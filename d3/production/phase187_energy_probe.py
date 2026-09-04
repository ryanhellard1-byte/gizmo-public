#!/usr/bin/env python3
"""Phase187 analysis-only GIZMO global-energy probe.

The frozen Phase176 production executable is never modified or re-used for
analysis.  Instead this tool exports a clean GIZMO source tree, deterministically
patches the temporary run.c so it returns immediately after the first statistics
pass, compiles collisionless gravity with COMPUTE_POTENTIAL_ENERGY, and hashes
all resulting provenance.

The probe therefore loads an immutable production snapshot, computes GIZMO's own
gravitational potential and global kinetic+potential energy, prints exactly one
machine-readable record, and exits before find_timesteps()/any kick/drift.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase174_batch_submit as p174  # noqa: E402
import phase181_profile_extract as p181  # noqa: E402

PHASE = 187
CANONICAL_PHYSICS_SOURCE_COMMIT = "dc93bca31b19135a1f8510e838f23abc850869fb"
EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
PROBE_EXECUTABLE_NAME = "GIZMO_PHASE187_ENERGY_PROBE"
PROBE_MARKER = "PHASE187_ENERGY_PROBE"
PROBE_CONFIG = "COMPUTE_POTENTIAL_ENERGY\n"

RUN_ANCHOR = "        compute_statistics();\t/* regular statistics outputs (like total energy) */\n"
RUN_PATCH = RUN_ANCHOR + (
    "\n"
    "        /* Phase187 analysis-only probe: emit one global-energy record and\n"
    "         * return before find_timesteps(), kicks, drift, or any evolution. */\n"
    "        if(ThisTask == 0)\n"
    "        {\n"
    "            printf(\"PHASE187_ENERGY_PROBE time=%.17g Etot=%.17g Ekin=%.17g Epot=%.17g Eint=%.17g\\n\",\n"
    "                   All.Time, SysState.EnergyTot, SysState.EnergyKin, SysState.EnergyPot, SysState.EnergyInt);\n"
    "            fflush(stdout);\n"
    "        }\n"
    "        return;\n"
)

ENERGY_COLUMNS = [
    "run_id", "energy_drift_abs_max", "energy_probe_sha256", "energy_source_sha256"
]


class ProbeError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_text(cmd: List[str], cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return p.stdout.strip()


def git_head(source_tree: Path) -> str:
    return run_text(["git", "-C", str(source_tree), "rev-parse", "HEAD"])


def clean_git(source_tree: Path) -> None:
    for cmd, label in (
        (["git", "-C", str(source_tree), "diff", "--quiet"], "tracked"),
        (["git", "-C", str(source_tree), "diff", "--cached", "--quiet"], "index"),
    ):
        if subprocess.run(cmd).returncode != 0:
            raise ProbeError(f"source tree has {label} modifications")


def export_source(source_tree: Path, dest: Path) -> None:
    if dest.exists():
        raise ProbeError(f"refusing to overwrite exported source: {dest}")
    dest.mkdir(parents=True)
    p1 = subprocess.Popen(["git", "-C", str(source_tree), "archive", "HEAD"], stdout=subprocess.PIPE)
    assert p1.stdout is not None
    p2 = subprocess.run(["tar", "-x", "-C", str(dest)], stdin=p1.stdout)
    p1.stdout.close()
    rc1 = p1.wait()
    if rc1 or p2.returncode:
        raise ProbeError("git archive export failed")


def patch_probe_tree(tree: Path) -> Dict[str, str]:
    run_c = tree / "run.c"
    if not run_c.is_file():
        raise ProbeError("exported source lacks run.c")
    text = run_c.read_text()
    if text.count(RUN_ANCHOR) != 1:
        raise ProbeError(f"run.c probe anchor count is {text.count(RUN_ANCHOR)}, expected 1")
    if PROBE_MARKER in text:
        raise ProbeError("run.c already contains Phase187 probe marker")
    original_sha = sha256_file(run_c)
    text = text.replace(RUN_ANCHOR, RUN_PATCH, 1)
    run_c.write_text(text)
    patched_sha = sha256_file(run_c)

    cfg = tree / "Config.phase187-energy.sh"
    cfg.write_text(PROBE_CONFIG)
    if "DM_SIDM" in cfg.read_text():
        raise ProbeError("analysis probe config must not enable DM_SIDM")
    return {
        "run_c_original_sha256": original_sha,
        "run_c_patched_sha256": patched_sha,
        "patch_contract_sha256": sha256_bytes(RUN_PATCH.encode()),
        "probe_config_sha256": sha256_file(cfg),
    }


def set_systype(tree: Path, systype: str | None) -> None:
    if not systype:
        return
    path = tree / "Makefile.systype"
    text = path.read_text()
    new, n = re.subn(r'^SYSTYPE="[^"]*"', f'SYSTYPE="{systype}"', text, count=1, flags=re.M)
    if n != 1:
        raise ProbeError("could not set Makefile.systype")
    path.write_text(new)


def build_probe(source_tree: Path, output_binary: Path, *, jobs: int = 2,
                systype: str | None = None, require_canonical: bool = True,
                work_dir: Path | None = None) -> Dict:
    source_tree = source_tree.resolve()
    if jobs <= 0:
        raise ProbeError("jobs must be positive")
    head = git_head(source_tree)
    clean_git(source_tree)
    if require_canonical and head != CANONICAL_PHYSICS_SOURCE_COMMIT:
        raise ProbeError(
            f"energy probe production build requires canonical physics source "
            f"{CANONICAL_PHYSICS_SOURCE_COMMIT}; observed {head}"
        )

    if work_dir is None:
        work_root = Path(tempfile.mkdtemp(prefix="phase187-energy-build-"))
        own_work = True
    else:
        work_root = work_dir.resolve()
        work_root.mkdir(parents=True, exist_ok=True)
        own_work = False
    tree = work_root / "source"
    export_source(source_tree, tree)
    patch = patch_probe_tree(tree)
    set_systype(tree, systype)
    shutil.copyfile(tree / "Config.phase187-energy.sh", tree / "Config.sh")

    try:
        subprocess.run(
            ["make", f"-j{jobs}", "CONFIG=Config.sh", f"EXEC={PROBE_EXECUTABLE_NAME}"],
            cwd=tree, check=True,
        )
        exe = tree / PROBE_EXECUTABLE_NAME
        if not exe.is_file():
            raise ProbeError("probe build produced no executable")
        output_binary = output_binary.resolve()
        output_binary.parent.mkdir(parents=True, exist_ok=True)
        if output_binary.exists():
            raise ProbeError(f"refusing to overwrite probe executable: {output_binary}")
        shutil.copy2(exe, output_binary)
        result = {
            "phase": PHASE,
            "status": "PASS",
            "kind": "analysis_only_gizmo_energy_probe_build",
            "source_commit": head,
            "canonical_source_required": bool(require_canonical),
            "canonical_physics_source_commit": CANONICAL_PHYSICS_SOURCE_COMMIT,
            "probe_executable": str(output_binary),
            "probe_executable_sha256": sha256_file(output_binary),
            "builder_sha256": sha256_file(Path(__file__)),
            "systype": systype,
            "jobs": jobs,
            **patch,
            "physics_isolation": {
                "DM_SIDM_enabled": False,
                "COMPUTE_POTENTIAL_ENERGY_enabled": True,
                "returns_after_first_compute_statistics": True,
                "find_timesteps_reached": False,
                "production_executable_modified": False,
            },
        }
        return result
    finally:
        if own_work:
            shutil.rmtree(work_root, ignore_errors=True)


def sanitize_params(original: Path, snapshot: Path, output_dir: Path, dest: Path) -> Dict[str, str]:
    lines = original.read_text().splitlines()
    replacements = {
        "InitCondFile": str(snapshot.resolve()),
        "OutputDir": str(output_dir.resolve()) + "/",
        "OutputListOn": "0",
        "TimeLimitCPU": "3600",
    }
    drop = {
        "DM_InteractionCrossSection",
        "DM_InteractionVelocityScale",
        "DM_DissipationFactor",
        "DM_KickPerCollision",
    }
    out: List[str] = []
    seen = set()
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("%") or stripped.startswith("#"):
            out.append(raw)
            continue
        parts = stripped.split(None, 1)
        key = parts[0]
        if key in drop:
            continue
        if key in replacements:
            out.append(f"{key:<28} {replacements[key]}")
            seen.add(key)
        else:
            out.append(raw)
    missing = set(replacements) - seen
    if missing:
        raise ProbeError(f"parameter file missing required keys: {sorted(missing)}")
    dest.write_text("\n".join(out) + "\n")
    return {"original_params_sha256": sha256_file(original), "probe_params_sha256": sha256_file(dest)}


def parse_probe_record(text: str) -> Dict[str, float]:
    hits = [line.strip() for line in text.splitlines() if line.startswith(PROBE_MARKER + " ")]
    if len(hits) != 1:
        raise ProbeError(f"expected exactly one {PROBE_MARKER} record, found {len(hits)}")
    parts = hits[0].split()[1:]
    vals: Dict[str, float] = {}
    for token in parts:
        if "=" not in token:
            raise ProbeError(f"malformed probe token {token!r}")
        k, v = token.split("=", 1)
        try:
            x = float(v)
        except ValueError as exc:
            raise ProbeError(f"non-numeric probe value {token!r}") from exc
        if not math_isfinite(x):
            raise ProbeError(f"non-finite probe value {token!r}")
        vals[k] = x
    required = {"time", "Etot", "Ekin", "Epot", "Eint"}
    if set(vals) != required:
        raise ProbeError(f"probe record keys {sorted(vals)} != {sorted(required)}")
    return vals


def math_isfinite(x: float) -> bool:
    return x == x and abs(x) != float("inf")


def run_probe_once(executable: Path, original_params: Path, snapshot: Path,
                   mpi_prefix: str = "") -> Dict:
    executable = executable.resolve()
    if not executable.is_file():
        raise ProbeError(f"probe executable missing: {executable}")
    if not snapshot.is_file():
        raise ProbeError(f"snapshot missing: {snapshot}")
    with tempfile.TemporaryDirectory(prefix="phase187-energy-run-") as td:
        tmp = Path(td)
        outdir = tmp / "out"; outdir.mkdir()
        params = tmp / "params.txt"
        pmeta = sanitize_params(original_params, snapshot, outdir, params)
        cmd = shlex.split(mpi_prefix) + [str(executable), str(params), "0"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode != 0 or re.search(r"MPI_ABORT|ENDRUN issued|Fatal error", text):
            raise ProbeError(f"energy probe failed for {snapshot}; rc={proc.returncode}")
        vals = parse_probe_record(text)
        return {
            **vals,
            "snapshot": str(snapshot.resolve()),
            "snapshot_sha256": sha256_file(snapshot),
            "probe_executable_sha256": sha256_file(executable),
            **pmeta,
        }


def completion_record(run_dir: Path, run_id: str) -> Tuple[Path, Dict]:
    post_path, post = p174.completion_record(run_dir)
    if post_path is None or post is None or post.get("status") != "COMPLETE":
        raise ProbeError(f"{run_id}: missing COMPLETE production record")
    if str(post.get("run_id")) != run_id:
        raise ProbeError(f"{run_id}: completion run_id mismatch")
    return post_path, post


def one_run(run_id: str, run_dir: Path, executable: Path, mpi_prefix: str = "") -> Dict:
    post_path, post = completion_record(run_dir, run_id)
    ic = Path(str(post.get("ic", "")))
    if not ic.is_file() or sha256_file(ic) != str(post.get("ic_sha256", "")):
        raise ProbeError(f"{run_id}: completion IC missing or SHA mismatch")
    params = run_dir / "params.txt"
    if not params.is_file():
        raise ProbeError(f"{run_id}: production params.txt missing")
    mapped = p181.map_required_times(ic, run_dir)
    values = []
    source_hash = hashlib.sha256()
    source_hash.update(post_path.read_bytes())
    source_hash.update(params.read_bytes())
    for expected_time, path, _snap in mapped:
        result = run_probe_once(executable, params, path, mpi_prefix)
        result["expected_time_Gyr"] = float(expected_time)
        values.append(result)
        source_hash.update(path.resolve().as_posix().encode() + b"\0")
        source_hash.update(bytes.fromhex(result["snapshot_sha256"]))
    e0 = float(values[0]["Etot"])
    if e0 == 0.0:
        raise ProbeError(f"{run_id}: zero initial total energy")
    drifts = [abs(float(x["Etot"]) / e0 - 1.0) for x in values]
    return {
        "run_id": run_id,
        "status": "PASS",
        "energy_drift_abs_max": max(drifts),
        "energy_probe_sha256": sha256_file(executable),
        "energy_source_sha256": source_hash.hexdigest(),
        "samples": values,
        "drifts": drifts,
    }


def frozen_rows() -> List[Dict[str, str]]:
    raw, rows = p174.p173.frozen_manifest()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_MANIFEST_SHA256 or len(rows) != 127:
        raise ProbeError("frozen manifest contract changed")
    return rows


def campaign(run_root: Path, executable: Path, output_csv: Path,
             report_json: Path, mpi_prefix: str = "") -> Dict:
    rows = frozen_rows()
    if output_csv.exists() or report_json.exists():
        raise ProbeError("refusing to overwrite Phase187 energy evidence")
    results = []
    for row in rows:
        rid = str(row["run_id"])
        results.append(one_run(rid, run_root / rid, executable, mpi_prefix))
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=ENERGY_COLUMNS)
        wr.writeheader()
        for r in results:
            wr.writerow({k: r[k] for k in ENERGY_COLUMNS})
    report = {
        "phase": PHASE,
        "status": "PASS",
        "kind": "gizmo_global_energy_evidence",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "run_count": len(results),
        "sample_count": sum(len(r["samples"]) for r in results),
        "probe_executable_sha256": sha256_file(executable),
        "energy_evidence_sha256": sha256_file(output_csv),
        "runs": results,
        "claim_boundary": (
            "This is analysis-only global-energy measurement on immutable production snapshots. "
            "It does not evolve the snapshots and does not replace production execution."
        ),
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("--source-tree", required=True)
    b.add_argument("--output-binary", required=True)
    b.add_argument("--attestation-json", required=True)
    b.add_argument("--jobs", type=int, default=2)
    b.add_argument("--systype")
    b.add_argument("--work-dir")
    b.add_argument("--allow-noncanonical-source", action="store_true",
                   help="CI compile test only; production evidence must not use this")
    o = sp.add_parser("one-run")
    o.add_argument("--run-id", required=True)
    o.add_argument("--run-dir", required=True)
    o.add_argument("--executable", required=True)
    o.add_argument("--mpi-prefix", default="")
    c = sp.add_parser("campaign")
    c.add_argument("--run-root", required=True)
    c.add_argument("--executable", required=True)
    c.add_argument("--output-csv", required=True)
    c.add_argument("--report-json", required=True)
    c.add_argument("--mpi-prefix", default="")
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        if args.cmd == "build":
            result = build_probe(
                Path(args.source_tree), Path(args.output_binary), jobs=args.jobs,
                systype=args.systype, require_canonical=not args.allow_noncanonical_source,
                work_dir=Path(args.work_dir) if args.work_dir else None,
            )
            att = Path(args.attestation_json)
            att.parent.mkdir(parents=True, exist_ok=True)
            if att.exists():
                raise ProbeError(f"refusing to overwrite attestation: {att}")
            att.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps({**result, "attestation_sha256": sha256_file(att)}, indent=2))
        elif args.cmd == "one-run":
            print(json.dumps(one_run(args.run_id, Path(args.run_dir), Path(args.executable), args.mpi_prefix), indent=2))
        else:
            result = campaign(Path(args.run_root), Path(args.executable), Path(args.output_csv),
                              Path(args.report_json), args.mpi_prefix)
            print(json.dumps({k: v for k, v in result.items() if k != "runs"}, indent=2))
        return 0
    except (ProbeError, p181.ProfileError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"phase": PHASE, "status": "ERROR", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
