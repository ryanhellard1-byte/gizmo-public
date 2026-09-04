#!/usr/bin/env python3
"""Phase 173 provenance-locked launcher for the frozen Phase172 production campaign.

This is the bridge from preregistered rows to actual GIZMO execution. It fails
closed on manifest provenance, executable provenance, IC identity, rendered
parameters, completion markers, and output snapshot count. It does not perform
or manufacture the downstream physics analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import phase172_lock  # noqa: E402

EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
EXPECTED_PHYSICS_SOURCE_COMMIT = "6353e4de5e627d926dec9114d36614340c376f67"
EXPECTED_EXECUTABLE_SHA256 = "e9f8167339ad6c3de0f10607b35f0b37d767a499f2ff17a5547e43cf04f7aceb"
EXPECTED_WORKFLOW_RUN_ID = 33845004328
EXPECTED_ARTIFACT_ID = 9926223195
EXPECTED_ARTIFACT_DIGEST = "sha256:41fc1d224c358afefb661f3075df09d254857d32cb6cc4dd60e7327c3624b9f8"
EXPECTED_FINAL_TIME_GYR = 80.0
TIME_UNIT_GYR = 0.9777923542981722
TIME_TOL = 1.0e-9


class LaunchError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def git_head(repo_root: Path = REPO_ROOT) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        return p.stdout.strip()
    except Exception:
        return None


def load_provenance(path: Path) -> Dict:
    obj = json.loads(path.read_text())
    expected = {
        "physics_source_commit": EXPECTED_PHYSICS_SOURCE_COMMIT,
        "workflow_run_id": EXPECTED_WORKFLOW_RUN_ID,
        "artifact_id": EXPECTED_ARTIFACT_ID,
        "artifact_digest": EXPECTED_ARTIFACT_DIGEST,
        "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "required_final_time_Gyr": EXPECTED_FINAL_TIME_GYR,
    }
    bad = {k: {"observed": obj.get(k), "expected": v}
           for k, v in expected.items() if obj.get(k) != v}
    if bad:
        raise LaunchError(f"provenance lock mismatch: {bad}")
    return obj


def frozen_manifest() -> Tuple[bytes, List[Dict[str, str]]]:
    raw, rows = phase172_lock.load()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_MANIFEST_SHA256:
        raise LaunchError(f"embedded Phase172 manifest SHA mismatch: {observed}")
    if len(rows) != 127:
        raise LaunchError(f"expected 127 Phase172 rows, observed {len(rows)}")
    if len({r["run_id"] for r in rows}) != len(rows):
        raise LaunchError("duplicate run_id in frozen Phase172 manifest")
    return raw, rows


def materialize_manifest(path: Path) -> Tuple[Path, List[Dict[str, str]]]:
    raw, rows = frozen_manifest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        observed = sha256_file(path)
        if observed != EXPECTED_MANIFEST_SHA256:
            raise LaunchError(f"existing manifest at {path} has wrong SHA: {observed}")
    else:
        path.write_bytes(raw)
    if sha256_file(path) != EXPECTED_MANIFEST_SHA256:
        raise LaunchError("materialized manifest SHA verification failed")
    return path, rows


def find_row(rows: Iterable[Dict[str, str]], run_id: str) -> Tuple[int, Dict[str, str]]:
    hits = [(i, r) for i, r in enumerate(rows) if r["run_id"] == run_id]
    if len(hits) != 1:
        raise LaunchError(f"expected exactly one manifest row for {run_id}, found {len(hits)}")
    return hits[0]


def parse_times(row: Dict[str, str]) -> Tuple[float, ...]:
    vals = tuple(float(x.strip()) for x in row["analysis_times_Gyr"].split(",") if x.strip())
    expected = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0)
    if len(vals) != len(expected) or any(abs(a-b) > TIME_TOL for a, b in zip(vals, expected)):
        raise LaunchError(f"{row['run_id']}: analysis-time contract changed: {vals}")
    return vals


def validate_row(row: Dict[str, str]) -> None:
    rid = row["run_id"]
    times = parse_times(row)
    if abs(times[-1] - EXPECTED_FINAL_TIME_GYR) > TIME_TOL:
        raise LaunchError(f"{rid}: final time is not 80 Gyr")
    nh, nl, nt = int(row["N_H"]), int(row["N_L"]), int(row["N_total"])
    if nh != nl or nt != nh + nl or nh <= 0:
        raise LaunchError(f"{rid}: invalid particle-count contract")
    expected_ratio = 1.0 if row["group"] == "identical_label_null" else 3.0
    if abs(float(row["ic_mass_ratio"]) - expected_ratio) > 1e-12:
        raise LaunchError(f"{rid}: IC mass-ratio contract mismatch")
    if row["group"] == "identical_label_null":
        if row["runtime_contract"] != "standard_constant_identical_labels":
            raise LaunchError(f"{rid}: identical-label runtime contract mismatch")
        if abs(float(row["runtime_interaction_parameter"]) - 1.125) > 1e-12:
            raise LaunchError(f"{rid}: identical-label cross section mismatch")
    elif row["group"] == "zero_cross_section_null":
        if row["runtime_contract"] != "d3_zero_cross_section":
            raise LaunchError(f"{rid}: zero-cross-section runtime contract mismatch")
        if abs(float(row["runtime_interaction_parameter"]) + 9.0) > 1e-12:
            raise LaunchError(f"{rid}: zero-cross-section sentinel mismatch")
    elif row["runtime_contract"] != "d3_frozen":
        raise LaunchError(f"{rid}: unexpected runtime contract {row['runtime_contract']!r}")
    if row["group"] == "permutation_reproducibility" and row["ic_order"] != "shuffled_within_species":
        raise LaunchError(f"{rid}: permutation control is not shuffled_within_species")


def expected_ic_path(ic_root: Path, row: Dict[str, str]) -> Path:
    n = int(row["N_total"])
    seed = int(row["seed"])
    ratio = float(row["ic_mass_ratio"])
    order = row["ic_order"]
    return ic_root / f"M11_N{n}_seed{seed}_mr{ratio:g}_{order}.dat"


def verify_ic(path: Path, row: Dict[str, str]) -> Dict:
    meta_path = Path(str(path) + ".json")
    if not path.is_file() or not meta_path.is_file():
        raise LaunchError(f"{row['run_id']}: IC or IC metadata missing: {path}")
    meta = json.loads(meta_path.read_text())
    expected = {
        "n_total": int(row["N_total"]),
        "n_H": int(row["N_H"]),
        "n_L": int(row["N_L"]),
        "seed": int(row["seed"]),
        "ic_order": row["ic_order"],
    }
    for key, value in expected.items():
        if meta.get(key) != value:
            raise LaunchError(f"{row['run_id']}: IC metadata {key}={meta.get(key)!r} != {value!r}")
    if abs(float(meta.get("mass_ratio", -1.0)) - float(row["ic_mass_ratio"])) > 1e-12:
        raise LaunchError(f"{row['run_id']}: IC mass ratio does not match manifest")
    observed = sha256_file(path)
    if meta.get("snapshot_sha256") != observed:
        raise LaunchError(f"{row['run_id']}: IC SHA mismatch")
    return meta


def ensure_ic(row: Dict[str, str], ic_root: Path, make_ic: Path, generate: bool) -> Tuple[Path, Dict]:
    target = expected_ic_path(ic_root, row)
    if target.exists() or Path(str(target)+".json").exists():
        return target, verify_ic(target, row)
    if not generate:
        raise LaunchError(f"{row['run_id']}: IC missing and generation disabled: {target}")
    ic_root.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, str(make_ic),
        "--n-total", row["N_total"],
        "--seed", row["seed"],
        "--mass-ratio", row["ic_mass_ratio"],
        "--order", row["ic_order"],
        "--output", str(target),
    ]
    subprocess.run(cmd, check=True)
    return target, verify_ic(target, row)


def verify_executable(executable: Path, provenance: Dict) -> str:
    if not executable.is_file():
        raise LaunchError(f"production executable missing: {executable}")
    observed = sha256_file(executable)
    expected = provenance["executable_sha256"]
    if observed != expected:
        raise LaunchError(f"production executable SHA mismatch: {observed} != {expected}")
    return observed


def read_params(path: Path) -> Dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            out[parts[0]] = parts[1].strip()
    return out


def verify_render(run_dir: Path, row: Dict[str, str], ic_path: Path) -> Dict:
    params_path = run_dir / "params.txt"
    outlist_path = run_dir / "output_times.txt"
    meta_path = run_dir / "render_metadata.json"
    for p in (params_path, outlist_path, meta_path):
        if not p.is_file():
            raise LaunchError(f"{row['run_id']}: renderer did not produce {p.name}")
    params = read_params(params_path)
    checks = {
        "DM_InteractionCrossSection": float(row["runtime_interaction_parameter"]),
        "AGS_DesNumNgb": float(row["neighbors"]),
        "Softening_Type1": float(row["epsilon_kpc"]),
        "MaxSizeTimestep": float(row["max_dt_Gyr"]) / TIME_UNIT_GYR,
        "TimeMax": EXPECTED_FINAL_TIME_GYR / TIME_UNIT_GYR,
    }
    for key, expected in checks.items():
        try:
            observed = float(params[key])
        except Exception as exc:
            raise LaunchError(f"{row['run_id']}: rendered parameter {key} missing/invalid") from exc
        if abs(observed - expected) > max(1e-12, 1e-11*abs(expected)):
            raise LaunchError(f"{row['run_id']}: rendered {key}={observed} != {expected}")
    if Path(params.get("InitCondFile", "")).resolve() != ic_path.resolve():
        raise LaunchError(f"{row['run_id']}: rendered InitCondFile does not match verified IC")
    output_times = [float(x) for x in outlist_path.read_text().split()]
    expected_times = [t/TIME_UNIT_GYR for t in parse_times(row) if t > 0]
    if len(output_times) != len(expected_times) or any(
        abs(a-b) > max(1e-12, 1e-11*abs(b)) for a, b in zip(output_times, expected_times)
    ):
        raise LaunchError(f"{row['run_id']}: rendered output-time list changed")
    return {
        "params_sha256": sha256_file(params_path),
        "output_times_sha256": sha256_file(outlist_path),
        "render_metadata_sha256": sha256_file(meta_path),
    }


def directory_digest(root: Path, exclude: set[str] | None = None) -> Tuple[str, List[Dict]]:
    exclude = exclude or set()
    items = []
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name not in exclude):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        size = path.stat().st_size
        items.append({"path": rel, "size": size, "sha256": digest})
        h.update(rel.encode()+b"\0"+str(size).encode()+b"\0"+digest.encode()+b"\n")
    return h.hexdigest(), items


def launcher_command(executable: Path, params: Path, mpi_prefix: str) -> List[str]:
    prefix = shlex.split(mpi_prefix) if mpi_prefix.strip() else []
    return prefix + [str(executable.resolve()), str(params.resolve()), "0"]


def prepare(args, provenance: Dict, rows: List[Dict[str, str]], manifest_path: Path):
    idx, row = find_row(rows, args.run_id)
    validate_row(row)
    executable = Path(args.executable).resolve()
    exe_sha = verify_executable(executable, provenance)
    make_ic = HERE / "phase172_make_ic.py"
    renderer = HERE / "phase172_render_run.py"
    if not make_ic.is_file() or not renderer.is_file():
        raise LaunchError("Phase172 IC generator or renderer is missing")

    ic_root = Path(args.ic_root).resolve()
    run_root = Path(args.run_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    run_dir = run_root / row["run_id"]
    if run_dir.exists():
        raise LaunchError(f"refusing to overwrite existing run directory: {run_dir}")

    ic_path, ic_meta = ensure_ic(row, ic_root, make_ic, not args.no_generate_ic)
    cmd_render = [
        sys.executable, str(renderer),
        "--manifest", str(manifest_path),
        "--row-index", str(idx),
        "--ic-root", str(ic_root),
        "--run-root", str(run_root),
        "--max-mem-mb", str(args.max_mem_mb),
        "--time-limit-cpu", str(args.time_limit_cpu),
    ]
    subprocess.run(cmd_render, check=True)
    render_hashes = verify_render(run_dir, row, ic_path)
    command = launcher_command(executable, run_dir/"params.txt", args.mpi_prefix)

    pre = {
        "phase": 173,
        "status": "PREPARED",
        "run_id": row["run_id"],
        "row_index": idx,
        "manifest_row": row,
        "manifest": str(manifest_path),
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "provenance": provenance,
        "production_executable": str(executable),
        "executable_sha256": exe_sha,
        "phase172_make_ic_sha256": sha256_file(make_ic),
        "phase172_render_run_sha256": sha256_file(renderer),
        "phase173_launcher_sha256": sha256_file(Path(__file__)),
        "checkout_head": git_head(),
        "ic": str(ic_path.resolve()),
        "ic_sha256": ic_meta["snapshot_sha256"],
        **render_hashes,
        "command": command,
        "required_final_time_Gyr": EXPECTED_FINAL_TIME_GYR,
    }
    (run_dir/"phase173_PRELAUNCH.json").write_text(json.dumps(pre, indent=2)+"\n")
    (run_dir/"command_PRELAUNCH.txt").write_text(shlex.join(command)+"\n")
    return run_dir, row, command, pre


def execute(run_dir: Path, row: Dict[str, str], command: List[str], pre: Dict) -> int:
    log_path = run_dir / "gizmo.log"
    started = time.time()
    with log_path.open("w") as log:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        rc = proc.wait()

    text = log_path.read_text(errors="replace")
    completed = bool(re.search(r"Final time=.*reached\. Simulation ends\.", text))
    fatal_marker = "MPI_ABORT" in text or "ENDRUN issued" in text
    snapshots = sorted(p.name for p in run_dir.glob("snapshot*"))
    required_snapshots = len([t for t in parse_times(row) if t > 0])

    post = dict(pre)
    post.update({
        "status": "COMPLETE" if rc == 0 and completed and not fatal_marker and len(snapshots) >= required_snapshots else "FAILED",
        "returncode": rc,
        "completion_marker": completed,
        "fatal_marker": fatal_marker,
        "snapshot_count": len(snapshots),
        "required_snapshot_count": required_snapshots,
        "wall_seconds": time.time()-started,
    })
    digest, files = directory_digest(run_dir, exclude={"phase173_POST.json"})
    post["run_directory_sha256"] = digest
    post["file_hashes"] = files
    (run_dir/"phase173_POST.json").write_text(json.dumps(post, indent=2)+"\n")
    return 0 if post["status"] == "COMPLETE" else (rc if rc else 3)


def plan(row: Dict[str, str], idx: int, ic_root: Path) -> Dict:
    validate_row(row)
    return {
        "run_id": row["run_id"],
        "row_index": idx,
        "group": row["group"],
        "branch": row["branch"],
        "resolution_tier": row["resolution_tier"],
        "N_total": int(row["N_total"]),
        "seed": int(row["seed"]),
        "ic_mass_ratio": float(row["ic_mass_ratio"]),
        "ic_order": row["ic_order"],
        "runtime_contract": row["runtime_contract"],
        "runtime_interaction_parameter": float(row["runtime_interaction_parameter"]),
        "epsilon_kpc": float(row["epsilon_kpc"]),
        "neighbors": int(row["neighbors"]),
        "max_dt_Gyr": float(row["max_dt_Gyr"]),
        "analysis_times_Gyr": list(parse_times(row)),
        "required_final_time_Gyr": EXPECTED_FINAL_TIME_GYR,
        "expected_ic": str(expected_ic_path(ic_root, row)),
    }


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--provenance", default=str(HERE/"phase173_provenance_master_6353.json"))
    sub = p.add_subparsers(dest="cmd", required=True)

    pre = sub.add_parser("preflight")
    pre.add_argument("--executable")

    rp = sub.add_parser("r0-plan")
    rp.add_argument("--ic-root", default="./phase172_ics")

    pl = sub.add_parser("plan")
    pl.add_argument("--run-id", required=True)
    pl.add_argument("--ic-root", default="./phase172_ics")

    for name in ("prepare", "run"):
        x = sub.add_parser(name)
        x.add_argument("--run-id", required=True)
        x.add_argument("--executable", required=True)
        x.add_argument("--ic-root", required=True)
        x.add_argument("--run-root", required=True)
        x.add_argument("--mpi-prefix", default="")
        x.add_argument("--max-mem-mb", type=int, default=3500)
        x.add_argument("--time-limit-cpu", type=int, default=170000)
        x.add_argument("--no-generate-ic", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        provenance = load_provenance(Path(args.provenance))
        state_root = Path(".phase173")
        manifest_path, rows = materialize_manifest(state_root/"phase172_manifest.csv")
        for row in rows:
            validate_row(row)

        if args.cmd == "preflight":
            result = {
                "status": "PASS",
                "phase": 173,
                "manifest_sha256": EXPECTED_MANIFEST_SHA256,
                "rows": len(rows),
                "blind_runs": sum(r["blind_analysis"] == "True" for r in rows),
                "required_final_time_Gyr": EXPECTED_FINAL_TIME_GYR,
                "physics_source_commit": provenance["physics_source_commit"],
                "workflow_run_id": provenance["workflow_run_id"],
                "artifact_id": provenance["artifact_id"],
                "artifact_digest": provenance["artifact_digest"],
                "expected_executable_sha256": provenance["executable_sha256"],
                "checkout_head": git_head(),
            }
            if args.executable:
                result["verified_executable_sha256"] = verify_executable(Path(args.executable), provenance)
            print(json.dumps(result, indent=2))
            return 0

        if args.cmd == "r0-plan":
            found = []
            for i, row in enumerate(rows):
                if row["group"] == "R0_commissioning_not_for_claims":
                    found.append(plan(row, i, Path(args.ic_root)))
            if len(found) != 8:
                raise LaunchError(f"expected 8 R0 commissioning rows, found {len(found)}")
            print(json.dumps({"status":"PASS","r0_runs":found}, indent=2))
            return 0

        idx, row = find_row(rows, args.run_id)
        if args.cmd == "plan":
            print(json.dumps(plan(row, idx, Path(args.ic_root)), indent=2))
            return 0

        run_dir, row, command, pre = prepare(args, provenance, rows, manifest_path)
        print(json.dumps({
            "status":"PREPARED", "run_dir":str(run_dir), "command":command,
            "executable_sha256":pre["executable_sha256"], "ic_sha256":pre["ic_sha256"],
            "params_sha256":pre["params_sha256"]
        }, indent=2))
        if args.cmd == "prepare":
            return 0
        return execute(run_dir, row, command, pre)
    except (LaunchError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f"PHASE173 PRODUCTION LAUNCHER FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
