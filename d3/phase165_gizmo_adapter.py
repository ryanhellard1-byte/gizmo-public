#!/usr/bin/env python3
"""
Fail-closed native GIZMO adapter for the frozen Phase165 D3/SIDMx production manifest.

This adapter translates one frozen manifest row into the parameter-file interface
GIZMO actually accepts. It does not invent generic --branch/--channels flags.

Supported physics rows map directly to frozen D3 runtime sentinels:
  CDM          ->  0
  SIDM2v       -> -1  (HH+LL+HL)
  SIDMx        -> -2  (HL)
  HL_off       -> -3  (HH+LL)
  HH_only      -> -4
  LL_only      -> -5
  HL_HH        -> -6
  HL_LL        -> -7
  SIDM2c_const -> -8  (constant/isotropic benchmark)
  zero-cross-section null -> -9

Two diagnostic groups remain deliberately blocked because the Phase165 manifest
describes executor-side transformations that are not frozen in the current GIZMO
source:
  - identical_label_null
  - permutation_reproducibility

Blocking them is intentional. A production adapter must not guess hidden physics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

FROZEN_MANIFEST_SHA256 = "08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3"

UNIT_LENGTH_CM = 3.085678e21
UNIT_VELOCITY_CM_S = 1.0e5
SECONDS_PER_GYR = 365.25 * 24.0 * 3600.0 * 1.0e9
CODE_TIME_GYR = (UNIT_LENGTH_CM / UNIT_VELOCITY_CM_S) / SECONDS_PER_GYR

BRANCH_TO_MODE = {
    "CDM": 0,
    "SIDM2v": 1,
    "SIDMx": 2,
    "HL_off": 3,
    "HH_only": 4,
    "LL_only": 5,
    "HL_HH": 6,
    "HL_LL": 7,
    "SIDM2c_const": 8,
}

BLOCKED_SPECIAL_GROUPS = {
    "identical_label_null": (
        "Phase165 requires mH=mL plus duplicated executor cross sections, "
        "but current D3 GIZMO enforces mH/mL=3 and has no frozen identity-null mode."
    ),
    "permutation_reproducibility": (
        "Phase165 requires a particle-order permutation of the same physical realization, "
        "but the manifest does not freeze how its distinct seed values map to base-IC versus shuffle RNG."
    ),
}

ZERO_NULL_GROUP = "zero_cross_section_null"


class AdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class Compatibility:
    supported: bool
    mode: int | None
    sentinel: float | None
    reason: str


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()


def load_manifest(path: Path, expected_sha: str = FROZEN_MANIFEST_SHA256) -> List[Dict[str, str]]:
    observed = manifest_sha256(path)
    if observed != expected_sha:
        raise AdapterError(f"manifest SHA256 mismatch: {observed} != {expected_sha}")
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 127:
        raise AdapterError(f"frozen Phase165 manifest must contain 127 rows, observed {len(rows)}")
    ids = [r["run_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise AdapterError("duplicate run_id in Phase165 manifest")
    return rows


def compatibility_for_row(row: Dict[str, str]) -> Compatibility:
    group = row["group"]
    branch = row["branch"]

    if group in BLOCKED_SPECIAL_GROUPS:
        return Compatibility(False, None, None, BLOCKED_SPECIAL_GROUPS[group])

    if group == ZERO_NULL_GROUP:
        return Compatibility(True, 9, -9.0, "native D3 null mode")

    if branch not in BRANCH_TO_MODE:
        return Compatibility(False, None, None, f"unknown frozen branch {branch!r}")

    mode = BRANCH_TO_MODE[branch]
    sentinel = 0.0 if mode == 0 else -float(mode)
    return Compatibility(True, mode, sentinel, "direct frozen branch mapping")


def _as_int(row: Dict[str, str], key: str) -> int:
    try:
        return int(float(row[key]))
    except Exception as exc:
        raise AdapterError(f"{row.get('run_id','?')}: invalid integer {key}={row.get(key)!r}") from exc


def _as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row[key])
    except Exception as exc:
        raise AdapterError(f"{row.get('run_id','?')}: invalid float {key}={row.get(key)!r}") from exc


def validate_row_contract(row: Dict[str, str]) -> None:
    rid = row["run_id"]
    nh = _as_int(row, "N_H")
    nl = _as_int(row, "N_L")
    nt = _as_int(row, "N_total")
    ratio = _as_float(row, "particle_mass_ratio_H_over_L")
    eps = _as_float(row, "epsilon_kpc")
    neighbors = _as_int(row, "neighbors")
    max_dt = _as_float(row, "max_dt_Gyr")

    if nh <= 0 or nl <= 0 or nh != nl:
        raise AdapterError(f"{rid}: required N_H=N_L>0, got {nh}, {nl}")
    if nt != nh + nl:
        raise AdapterError(f"{rid}: N_total={nt} does not equal N_H+N_L={nh+nl}")
    if abs(ratio - 3.0) > 1e-12:
        raise AdapterError(f"{rid}: frozen manifest mass ratio must be 3, got {ratio}")
    if eps <= 0:
        raise AdapterError(f"{rid}: epsilon_kpc must be positive")
    if neighbors not in (48, 64, 96):
        raise AdapterError(f"{rid}: unexpected frozen neighbor count {neighbors}")
    if max_dt <= 0:
        raise AdapterError(f"{rid}: max_dt_Gyr must be positive")

    times = parse_analysis_times(row["analysis_times_Gyr"])
    required = {0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0}
    if set(times) != required:
        raise AdapterError(f"{rid}: analysis time lock changed: {times}")

    comp = compatibility_for_row(row)
    if not comp.supported:
        return

    expected_channels = {
        0: "none",
        1: "HH+LL+HL",
        2: "HL",
        3: "HH+LL",
        4: "HH",
        5: "LL",
        6: "HL+HH",
        7: "HL+LL",
        8: "constant_SIDM2c_surrogate",
        9: "HH+LL+HL",
    }[comp.mode]
    if row["channels"] != expected_channels:
        raise AdapterError(
            f"{rid}: channel lock mismatch for mode {comp.mode}: "
            f"manifest={row['channels']!r}, expected={expected_channels!r}"
        )


def parse_analysis_times(value: str) -> List[float]:
    try:
        vals = [float(x.strip()) for x in value.split(",") if x.strip()]
    except Exception as exc:
        raise AdapterError(f"invalid analysis_times_Gyr={value!r}") from exc
    if not vals or vals != sorted(vals) or len(vals) != len(set(vals)):
        raise AdapterError(f"analysis times must be non-empty, sorted and unique: {value!r}")
    return vals


def gyr_to_code_time(gyr: float) -> float:
    return gyr / CODE_TIME_GYR


def render_output_times(row: Dict[str, str]) -> str:
    times = parse_analysis_times(row["analysis_times_Gyr"])
    return "\n".join(f"{gyr_to_code_time(t):.17g}" for t in times) + "\n"


def render_params(
    row: Dict[str, str],
    ic_path: Path,
    output_dir: Path,
    output_list_path: Path,
    *,
    time_limit_cpu: int = 172800,
) -> str:
    validate_row_contract(row)
    comp = compatibility_for_row(row)
    if not comp.supported:
        raise AdapterError(f"{row['run_id']}: unsupported special row: {comp.reason}")

    times = parse_analysis_times(row["analysis_times_Gyr"])
    time_max = gyr_to_code_time(max(times))
    max_dt = gyr_to_code_time(_as_float(row, "max_dt_Gyr"))
    eps = _as_float(row, "epsilon_kpc")
    neighbors = _as_int(row, "neighbors")

    return f"""% Phase165 native-GIZMO production parameters.
% Generated fail-closed from frozen manifest row {row['run_id']}.
InitCondFile                {ic_path}
OutputDir                   {output_dir}
ICFormat                    1
SnapFormat                  1
SnapshotFileBase            snapshot
RestartFile                 restart
OutputListOn                1
OutputListFilename          {output_list_path}
NumFilesPerSnapshot         1
NumFilesWrittenInParallel   1

TimeLimitCPU                {int(time_limit_cpu)}
CpuTimeBetRestartFile       7200
PartAllocFactor             4.0
BufferSize                  64

TimeBegin                    0.0
TimeMax                      {time_max:.17g}
MaxSizeTimestep              {max_dt:.17g}
MinSizeTimestep              1.0e-12

UnitLength_in_cm             {UNIT_LENGTH_CM:.7e}
UnitMass_in_g                1.989e33
UnitVelocity_in_cm_per_s     {UNIT_VELOCITY_CM_S:.7e}
GravityConstantInternal      0

ComovingIntegrationOn        0
BoxSize                      2000.0
Omega_Matter                 0
Omega_Lambda                 0
Omega_Baryon                 0
HubbleParam                  1.0

AGS_DesNumNgb                {neighbors}
TreeRebuild_ActiveFraction   0.01
Softening_Type0              {eps:.17g}
Softening_Type1              {eps:.17g}
Softening_Type2              {eps:.17g}
Softening_Type3              {eps:.17g}
Softening_Type4              {eps:.17g}
Softening_Type5              {eps:.17g}

DM_InteractionCrossSection   {comp.sentinel:.17g}
DM_InteractionVelocityScale  0
DM_DissipationFactor         0
DM_KickPerCollision          0
"""


def find_row(rows: Iterable[Dict[str, str]], run_id: str) -> Dict[str, str]:
    matches = [r for r in rows if r["run_id"] == run_id]
    if len(matches) != 1:
        raise AdapterError(f"expected exactly one row for {run_id}, found {len(matches)}")
    return matches[0]


def expected_ic_paths(ic_cache: Path, row: Dict[str, str], taper: float) -> Tuple[Path, Path]:
    nt = _as_int(row, "N_total")
    seed = _as_int(row, "seed")
    taper_tag = str(taper).replace(".", "p")
    stem = f"M11_N{nt}_seed{seed}_taper{taper_tag}"
    data = ic_cache / f"{stem}.dat"
    return data, Path(str(data) + ".json")


def verify_ic_metadata(meta_path: Path, row: Dict[str, str], snapshot_path: Path, taper: float) -> Dict:
    meta = json.loads(meta_path.read_text())
    rid = row["run_id"]
    checks = {
        "n_total": _as_int(row, "N_total"),
        "n_H": _as_int(row, "N_H"),
        "n_L": _as_int(row, "N_L"),
        "seed": _as_int(row, "seed"),
    }
    for key, expected in checks.items():
        if int(meta.get(key, -1)) != expected:
            raise AdapterError(f"{rid}: IC metadata {key}={meta.get(key)!r} != {expected!r}")
    if abs(float(meta.get("mass_ratio", -1.0)) - 3.0) > 1e-12:
        raise AdapterError(f"{rid}: IC mass ratio is not 3")
    if abs(float(meta.get("taper_rd_over_r200", -1.0)) - taper) > 1e-12:
        raise AdapterError(f"{rid}: IC taper mismatch")
    observed = sha256_file(snapshot_path)
    if meta.get("snapshot_sha256") != observed:
        raise AdapterError(f"{rid}: IC snapshot SHA mismatch")
    return meta


def ensure_ic(
    row: Dict[str, str],
    generator: Path,
    ic_cache: Path,
    taper: float,
) -> Tuple[Path, Dict]:
    comp = compatibility_for_row(row)
    if not comp.supported:
        raise AdapterError(f"{row['run_id']}: cannot generate IC for blocked special row: {comp.reason}")

    ic_cache.mkdir(parents=True, exist_ok=True)
    data_path, meta_path = expected_ic_paths(ic_cache, row, taper)

    if data_path.exists() or meta_path.exists():
        if not (data_path.exists() and meta_path.exists()):
            raise AdapterError(f"{row['run_id']}: incomplete cached IC pair at {data_path}")
        return data_path, verify_ic_metadata(meta_path, row, data_path, taper)

    cmd = [
        sys.executable,
        str(generator),
        "--n-total", str(_as_int(row, "N_total")),
        "--seed", str(_as_int(row, "seed")),
        "--taper", str(taper),
        "--output", str(data_path),
    ]
    subprocess.run(cmd, check=True)
    if not data_path.exists() or not meta_path.exists():
        raise AdapterError(f"{row['run_id']}: IC generator did not produce expected data+metadata")
    return data_path, verify_ic_metadata(meta_path, row, data_path, taper)


def load_provenance(path: Path) -> Dict:
    obj = json.loads(path.read_text())
    if obj.get("manifest_sha256") != FROZEN_MANIFEST_SHA256:
        raise AdapterError("provenance manifest hash does not match frozen Phase165 hash")
    exe_sha = str(obj.get("executable_sha256", ""))
    if len(exe_sha) != 64:
        raise AdapterError("provenance executable_sha256 is missing/invalid")
    return obj


def build_command(executable: Path, params: Path, mpi_prefix: str) -> List[str]:
    prefix = shlex.split(mpi_prefix) if mpi_prefix.strip() else []
    return prefix + [str(executable), str(params), "0"]


def directory_digest(root: Path, exclude_names: set[str] | None = None) -> Tuple[str, List[Dict]]:
    exclude_names = exclude_names or set()
    entries = []
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name not in exclude_names):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        size = path.stat().st_size
        entries.append({"path": rel, "size": size, "sha256": digest})
        h.update(rel.encode("utf-8") + b"\0")
        h.update(str(size).encode("ascii") + b"\0")
        h.update(digest.encode("ascii") + b"\n")
    return h.hexdigest(), entries


def preflight_report(rows: List[Dict[str, str]]) -> Dict:
    supported = []
    blocked = []
    modes: Dict[str, int] = {}
    for row in rows:
        validate_row_contract(row)
        comp = compatibility_for_row(row)
        if comp.supported:
            supported.append(row["run_id"])
            key = str(comp.mode)
            modes[key] = modes.get(key, 0) + 1
        else:
            blocked.append({
                "run_id": row["run_id"],
                "group": row["group"],
                "branch": row["branch"],
                "reason": comp.reason,
            })
    return {
        "status": "PASS_WITH_FROZEN_SPECIAL_BLOCKS" if len(blocked) == 4 else "FAIL",
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "total_rows": len(rows),
        "supported_rows": len(supported),
        "blocked_rows": len(blocked),
        "mode_counts": modes,
        "blocked": blocked,
    }


def plan_row(row: Dict[str, str], ic_cache: Path, taper: float) -> Dict:
    validate_row_contract(row)
    comp = compatibility_for_row(row)
    ic_path, meta_path = expected_ic_paths(ic_cache, row, taper)
    return {
        "run_id": row["run_id"],
        "group": row["group"],
        "branch": row["branch"],
        "supported": comp.supported,
        "reason": comp.reason,
        "mode": comp.mode,
        "sentinel": comp.sentinel,
        "N_total": _as_int(row, "N_total"),
        "seed": _as_int(row, "seed"),
        "epsilon_kpc": _as_float(row, "epsilon_kpc"),
        "neighbors": _as_int(row, "neighbors"),
        "max_dt_Gyr": _as_float(row, "max_dt_Gyr"),
        "analysis_times_Gyr": parse_analysis_times(row["analysis_times_Gyr"]),
        "TimeMax_code": gyr_to_code_time(max(parse_analysis_times(row["analysis_times_Gyr"]))),
        "MaxSizeTimestep_code": gyr_to_code_time(_as_float(row, "max_dt_Gyr")),
        "planned_ic": str(ic_path),
        "planned_ic_metadata": str(meta_path),
    }


def prepare_run(args, row: Dict[str, str], provenance: Dict) -> Tuple[Path, List[str], Dict]:
    comp = compatibility_for_row(row)
    if not comp.supported:
        raise AdapterError(f"{row['run_id']}: blocked: {comp.reason}")

    executable = Path(args.executable).resolve()
    if not executable.is_file():
        raise AdapterError(f"executable missing: {executable}")
    observed_exe = sha256_file(executable)
    expected_exe = provenance["executable_sha256"]
    if observed_exe != expected_exe:
        raise AdapterError(f"executable SHA mismatch: {observed_exe} != {expected_exe}")

    generator = Path(args.generator).resolve()
    if not generator.is_file():
        raise AdapterError(f"M11 generator missing: {generator}")

    output_root = Path(args.output_root).resolve()
    ic_cache = Path(args.ic_cache).resolve()
    run_dir = output_root / row["run_id"]
    if run_dir.exists():
        raise AdapterError(f"run directory already exists; refusing overwrite: {run_dir}")
    run_dir.mkdir(parents=True)

    ic_path, ic_meta = ensure_ic(row, generator, ic_cache, args.taper)
    output_dir = run_dir / "gizmo_output"
    output_dir.mkdir()

    output_list = run_dir / "output_times.txt"
    output_list.write_text(render_output_times(row))

    params = run_dir / "params.txt"
    params.write_text(render_params(
        row, ic_path.resolve(), output_dir.resolve(), output_list.resolve(),
        time_limit_cpu=args.time_limit_cpu,
    ))

    command = build_command(executable, params, args.mpi_prefix)
    pre = {
        "status": "PREPARED",
        "run": row,
        "compatibility": {
            "mode": comp.mode,
            "sentinel": comp.sentinel,
            "reason": comp.reason,
        },
        "manifest_sha256": FROZEN_MANIFEST_SHA256,
        "provenance": provenance,
        "executable": str(executable),
        "executable_sha256": observed_exe,
        "generator": str(generator),
        "generator_sha256": sha256_file(generator),
        "ic": str(ic_path.resolve()),
        "ic_sha256": ic_meta["snapshot_sha256"],
        "params": str(params.resolve()),
        "params_sha256": sha256_file(params),
        "output_list": str(output_list.resolve()),
        "output_list_sha256": sha256_file(output_list),
        "command": command,
        "code_time_Gyr": CODE_TIME_GYR,
    }
    (run_dir / "run_metadata_PRELAUNCH.json").write_text(json.dumps(pre, indent=2) + "\n")
    (run_dir / "command_PRELAUNCH.txt").write_text(shlex.join(command) + "\n")
    return run_dir, command, pre


def execute_run(run_dir: Path, command: List[str], pre: Dict) -> int:
    log_path = run_dir / "gizmo.log"
    started = time.time()
    with log_path.open("w") as log:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        rc = proc.wait()

    post = dict(pre)
    post["status"] = "COMPLETE" if rc == 0 else "FAILED"
    post["returncode"] = rc
    post["wall_seconds"] = time.time() - started

    digest, entries = directory_digest(run_dir, exclude_names={"run_metadata_POST.json"})
    post["run_output_sha256"] = digest
    post["file_hashes"] = entries
    (run_dir / "run_metadata_POST.json").write_text(json.dumps(post, indent=2) + "\n")
    return rc


def build_parser() -> argparse.ArgumentParser:
    repo_default = Path(__file__).resolve().parent
    prod = repo_default / "production"
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(prod / "phase165_production_live_nbody_manifest.csv"))
    ap.add_argument("--expected-manifest-sha", default=FROZEN_MANIFEST_SHA256)

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("preflight")

    pplan = sub.add_parser("plan")
    pplan.add_argument("--run-id", required=True)
    pplan.add_argument("--ic-cache", default="./phase165_ic_cache")
    pplan.add_argument("--taper", type=float, default=0.05, choices=[0.03, 0.05, 0.10])

    for name in ("prepare", "run"):
        p = sub.add_parser(name)
        p.add_argument("--run-id", required=True)
        p.add_argument("--provenance", default=str(prod / "provenance_master_a5e7.json"))
        p.add_argument("--executable", required=True)
        p.add_argument("--generator", default=str(repo_default / "phase141_generate_m11_ic.py"))
        p.add_argument("--output-root", required=True)
        p.add_argument("--ic-cache", required=True)
        p.add_argument("--taper", type=float, default=0.05, choices=[0.03, 0.05, 0.10])
        p.add_argument("--mpi-prefix", default="")
        p.add_argument("--time-limit-cpu", type=int, default=172800)

    return ap


def main() -> int:
    args = build_parser().parse_args()
    try:
        manifest = Path(args.manifest)
        rows = load_manifest(manifest, args.expected_manifest_sha)

        if args.cmd == "preflight":
            report = preflight_report(rows)
            print(json.dumps(report, indent=2))
            return 0 if report["status"] == "PASS_WITH_FROZEN_SPECIAL_BLOCKS" else 1

        row = find_row(rows, args.run_id)
        if args.cmd == "plan":
            print(json.dumps(plan_row(row, Path(args.ic_cache), args.taper), indent=2))
            return 0

        provenance = load_provenance(Path(args.provenance))
        run_dir, command, pre = prepare_run(args, row, provenance)
        print(json.dumps({
            "status": "PREPARED",
            "run_dir": str(run_dir),
            "command": command,
            "executable_sha256": pre["executable_sha256"],
            "ic_sha256": pre["ic_sha256"],
            "params_sha256": pre["params_sha256"],
        }, indent=2))

        if args.cmd == "prepare":
            return 0
        return execute_run(run_dir, command, pre)

    except AdapterError as exc:
        print(f"PHASE165 GIZMO ADAPTER FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
