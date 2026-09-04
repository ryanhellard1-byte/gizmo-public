#!/usr/bin/env python3
"""Phase187 preregistered global runtime-invariant extractor.

This closes the two Phase165/166 runtime-summary fields that the old execution
lock named but never supplied an engine-specific producer for:

* energy_drift_abs_max: max |E(t)-E(0)|/|E(0)| from GIZMO energy.txt, where
  E = total internal + total gravitational potential + total kinetic energy;
* momentum_drift_abs_max: max change of H+L center-of-mass velocity relative
  to the time-zero IC over the frozen Phase172 snapshot times.

The latter is the explicit engine definition of the old schema's
"center-of-mass momentum drift proxy".  Both definitions are frozen before any
real 127-run production output is opened.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_profile_extract as p181  # noqa: E402

PHASE = 187
TIME_UNIT_GYR = p181.TIME_UNIT_GYR
EXPECTED_FINAL_TIME_GYR = 80.0
ENERGY_COLUMNS = 28
ENERGY_START_TOL_GYR = 1.0e-9
ENERGY_END_TOL_GYR = 0.01
ENERGY_DRIFT_HARD_MAX = 0.01
ENERGY_DRIFT_MEDIAN_PREFERRED = 0.003
MOMENTUM_DRIFT_HARD_MAX = 1.0e-4


class RuntimeInvariantError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return p181.sha256_file(path)


def _finite_matrix(path: Path) -> np.ndarray:
    try:
        a = np.loadtxt(path, dtype=np.float64, ndmin=2)
    except Exception as exc:
        raise RuntimeInvariantError(f"{path}: cannot parse GIZMO energy.txt") from exc
    if a.ndim != 2 or a.shape[0] < 2:
        raise RuntimeInvariantError(f"{path}: need at least two energy-statistics rows")
    if a.shape[1] != ENERGY_COLUMNS:
        raise RuntimeInvariantError(
            f"{path}: expected {ENERGY_COLUMNS} GIZMO energy columns, found {a.shape[1]}"
        )
    if np.any(~np.isfinite(a)):
        raise RuntimeInvariantError(f"{path}: non-finite energy diagnostic value")
    return a


def energy_drift(path: Path) -> Dict[str, object]:
    if not path.is_file():
        raise RuntimeInvariantError(f"GIZMO energy diagnostic missing: {path}")
    a = _finite_matrix(path)
    t_code = a[:, 0]
    if np.any(np.diff(t_code) <= 0.0):
        raise RuntimeInvariantError(f"{path}: energy-statistics times are not strictly increasing")
    t_gyr = t_code * TIME_UNIT_GYR
    if abs(float(t_gyr[0])) > ENERGY_START_TOL_GYR:
        raise RuntimeInvariantError(
            f"{path}: first energy statistic is {t_gyr[0]:.17g} Gyr, not time zero"
        )
    if float(t_gyr[-1]) < EXPECTED_FINAL_TIME_GYR - ENERGY_END_TOL_GYR:
        raise RuntimeInvariantError(
            f"{path}: final energy statistic {t_gyr[-1]:.9g} Gyr does not cover the 80-Gyr run"
        )

    # run.c writes columns 1/2/3 as total internal/potential/kinetic energy.
    e_total = a[:, 1] + a[:, 2] + a[:, 3]
    e0 = float(e_total[0])
    if not math.isfinite(e0) or abs(e0) <= np.finfo(np.float64).tiny:
        raise RuntimeInvariantError(f"{path}: zero/non-finite initial total energy")
    drift = np.abs((e_total - e0) / e0)
    if np.any(~np.isfinite(drift)):
        raise RuntimeInvariantError(f"{path}: non-finite relative energy drift")

    return {
        "energy_drift_abs_max": float(np.max(drift)),
        "energy_drift_abs_median_over_samples": float(np.median(drift)),
        "energy_initial": e0,
        "energy_final": float(e_total[-1]),
        "energy_statistics_rows": int(len(a)),
        "energy_statistics_first_time_Gyr": float(t_gyr[0]),
        "energy_statistics_last_time_Gyr": float(t_gyr[-1]),
        "energy_source": str(path.resolve()),
        "energy_source_sha256": sha256_file(path),
    }


def com_velocity(snapshot: p181.Snapshot) -> np.ndarray:
    mt = float(np.sum(snapshot.mass))
    if not math.isfinite(mt) or mt <= 0.0:
        raise RuntimeInvariantError("snapshot has non-positive/non-finite H+L total mass")
    v = np.sum(snapshot.vel * snapshot.mass[:, None], axis=0) / mt
    if np.any(~np.isfinite(v)):
        raise RuntimeInvariantError("snapshot has non-finite H+L COM velocity")
    return np.asarray(v, dtype=np.float64)


def momentum_drift_from_mapped(
    mapped: Sequence[Tuple[float, Path, p181.Snapshot]],
) -> Dict[str, object]:
    if len(mapped) != len(p181.EXPECTED_TIMES_GYR):
        raise RuntimeInvariantError(
            f"expected {len(p181.EXPECTED_TIMES_GYR)} frozen snapshots, found {len(mapped)}"
        )
    v0 = com_velocity(mapped[0][2])
    rows: List[Dict[str, object]] = []
    max_drift = 0.0
    for time_gyr, path, snap in mapped:
        v = com_velocity(snap)
        delta = float(np.linalg.norm(v - v0))
        if not math.isfinite(delta):
            raise RuntimeInvariantError("non-finite COM-velocity drift")
        max_drift = max(max_drift, delta)
        rows.append(
            {
                "time_Gyr": float(time_gyr),
                "com_velocity": [float(x) for x in v],
                "com_velocity_drift": delta,
                "snapshot": str(path.resolve()),
                "snapshot_sha256": sha256_file(path),
            }
        )
    return {
        "momentum_drift_abs_max": max_drift,
        "momentum_proxy_definition": "max ||v_COM(t)-v_COM(0)|| for H+L, code velocity units",
        "initial_com_velocity": [float(x) for x in v0],
        "momentum_samples": rows,
    }


def analyze_run(ic: Path, run_dir: Path) -> Dict[str, object]:
    mapped = p181.map_required_times(ic, run_dir)
    energy = energy_drift(run_dir / "energy.txt")
    momentum = momentum_drift_from_mapped(mapped)
    result: Dict[str, object] = {
        "phase": PHASE,
        "status": "PASS",
        **energy,
        **momentum,
        "thresholds": {
            "energy_drift_abs_max": ENERGY_DRIFT_HARD_MAX,
            "energy_drift_median_preferred": ENERGY_DRIFT_MEDIAN_PREFERRED,
            "momentum_drift_abs_max": MOMENTUM_DRIFT_HARD_MAX,
        },
        "claim_boundary": (
            "PASS means the two preregistered runtime invariants were measured from "
            "complete canonical evidence. Gate acceptance is evaluated separately."
        ),
    }
    return result


def validate_run_metrics(rows: Iterable[Dict[str, object]]) -> Tuple[bool, List[Dict[str, object]]]:
    rows = list(rows)
    if not rows:
        raise RuntimeInvariantError("no runtime-invariant rows supplied")
    energy = np.asarray([float(r["energy_drift_abs_max"]) for r in rows], dtype=float)
    momentum = np.asarray([float(r["momentum_drift_abs_max"]) for r in rows], dtype=float)
    if np.any(~np.isfinite(energy)) or np.any(~np.isfinite(momentum)):
        raise RuntimeInvariantError("non-finite campaign runtime invariant")
    checks = [
        {
            "gate": "energy_drift_hard_gate",
            "passed": bool(float(np.max(energy)) < ENERGY_DRIFT_HARD_MAX),
            "fatal": True,
            "detail": {"max": float(np.max(energy)), "threshold": ENERGY_DRIFT_HARD_MAX},
        },
        {
            "gate": "energy_drift_median_preferred",
            "passed": bool(float(np.median(energy)) < ENERGY_DRIFT_MEDIAN_PREFERRED),
            "fatal": False,
            "detail": {"median": float(np.median(energy)), "preferred": ENERGY_DRIFT_MEDIAN_PREFERRED},
        },
        {
            "gate": "momentum_drift_gate",
            "passed": bool(float(np.max(momentum)) < MOMENTUM_DRIFT_HARD_MAX),
            "fatal": True,
            "detail": {"max": float(np.max(momentum)), "threshold": MOMENTUM_DRIFT_HARD_MAX},
        },
    ]
    ok = all(c["passed"] or not c["fatal"] for c in checks)
    return bool(ok), checks


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ic", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--output")
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        result = analyze_run(Path(args.ic), Path(args.run_dir))
        text = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(text)
        print(text, end="")
        return 0
    except (RuntimeInvariantError, p181.ProfileError, OSError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
