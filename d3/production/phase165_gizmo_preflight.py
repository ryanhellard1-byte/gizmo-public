#!/usr/bin/env python3
"""Fail-closed bridge from the frozen Phase165 manifest to live GIZMO D3 modes.

This script does not alter the frozen manifest. It proves that every registered
row is representable by the current live-GIZMO adapter while preserving the
physical D3 3:1 mass contract outside the explicit equal-label null control.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

MANIFEST_SHA256 = "08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3"
EXPECTED_ROWS = 127
EXPECTED_BLIND = 119
EXPECTED_GROUPS = {
    "core_blind_production": 48,
    "channel_ablation": 24,
    "neighbor_kernel_convergence": 18,
    "half_timestep_convergence": 12,
    "constant_SIDM2c_benchmark": 9,
    "R0_commissioning_not_for_claims": 8,
    "constant_SIDM2c_half_timestep": 2,
    "identical_label_null": 2,
    "zero_cross_section_null": 2,
    "permutation_reproducibility": 2,
}
BRANCH_TO_SENTINEL = {
    "CDM": 0,
    "SIDM2v": -1,
    "SIDMx": -2,
    "HL_off": -3,
    "HH_only": -4,
    "LL_only": -5,
    "HL_HH": -6,
    "HL_LL": -7,
    "SIDM2c_const": -8,
}
EXPECTED_RESOLUTION = {
    "R0_pilot": (100_000, 100_000, 0.060),
    "R1_base": (300_000, 300_000, 0.040),
    "R2_double": (600_000, 600_000, 0.028),
    "R3_gold": (1_200_000, 1_200_000, 0.020),
}
EXPECTED_ANALYSIS_TIMES = [0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_bool(x: str) -> bool:
    return x.strip().lower() in {"1", "true", "yes"}


def parse_times(x: str) -> list[float]:
    return [float(v) for v in x.split(",")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?", default="phase165_production_live_nbody_manifest.csv")
    ap.add_argument("--report", default=None)
    ap.add_argument("--require-production-ready", action="store_true")
    args = ap.parse_args()

    path = Path(args.manifest)
    if not path.is_file():
        raise SystemExit(f"FAIL: manifest missing: {path}")
    got_sha = sha256(path)
    if got_sha != MANIFEST_SHA256:
        raise SystemExit(f"FAIL: manifest SHA256 {got_sha} != frozen {MANIFEST_SHA256}")

    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"FAIL: {len(rows)} rows != frozen {EXPECTED_ROWS}")
    blind = sum(parse_bool(r["blind_analysis"]) for r in rows)
    if blind != EXPECTED_BLIND:
        raise SystemExit(f"FAIL: {blind} blind rows != frozen {EXPECTED_BLIND}")
    groups = Counter(r["group"] for r in rows)
    if dict(groups) != EXPECTED_GROUPS:
        raise SystemExit(f"FAIL: group counts changed: {dict(groups)}")

    adapters = []
    failures = []
    for r in rows:
        run_id = r["run_id"]
        group = r["group"]
        branch = r["branch"]
        tier = r["resolution_tier"]
        if tier not in EXPECTED_RESOLUTION:
            failures.append(f"{run_id}: unknown resolution tier {tier}")
            continue
        eh, el, eps = EXPECTED_RESOLUTION[tier]
        if int(r["N_H"]) != eh or int(r["N_L"]) != el or int(r["N_total"]) != eh + el:
            failures.append(f"{run_id}: particle counts do not match frozen {tier}")
        if abs(float(r["epsilon_kpc"]) - eps) > 1e-12:
            failures.append(f"{run_id}: epsilon does not match frozen {tier}")
        if abs(float(r["particle_mass_ratio_H_over_L"]) - 3.0) > 1e-12:
            failures.append(f"{run_id}: frozen reference mass ratio changed")
        if parse_times(r["analysis_times_Gyr"]) != EXPECTED_ANALYSIS_TIMES:
            failures.append(f"{run_id}: analysis-time list changed")
        if branch not in BRANCH_TO_SENTINEL:
            failures.append(f"{run_id}: no branch sentinel mapping for {branch}")
            continue

        sentinel = BRANCH_TO_SENTINEL[branch]
        state = "READY"
        requirement = "direct live-GIZMO branch mapping"
        effective_mass_ratio = 3.0
        permutation_seed = None

        if group == "zero_cross_section_null":
            sentinel = -9
            state = "READY_NULL"
            requirement = "frozen zero-scattering sentinel -9"
        elif group == "identical_label_null":
            sentinel = -10
            state = "READY_CONTROL"
            effective_mass_ratio = 1.0
            requirement = (
                "control-only equal-label mode -10: mH=mL, HL Rutherford only; "
                "physical modes retain mH/mL=3"
            )
        elif group == "permutation_reproducibility":
            state = "READY_PERMUTATION"
            permutation_seed = int(r["seed"]) + 10_000_000
            requirement = (
                "generate identical phase-space/ID mapping then deterministically permute "
                "within species using permutation_seed"
            )

        adapters.append({
            "run_id": run_id,
            "group": group,
            "branch": branch,
            "resolution_tier": tier,
            "sentinel": sentinel,
            "effective_mass_ratio": effective_mass_ratio,
            "permutation_seed": permutation_seed,
            "state": state,
            "requirement": requirement,
        })

    if failures:
        raise SystemExit("FAIL:\n" + "\n".join(failures))

    states = Counter(a["state"] for a in adapters)
    not_ready = [a for a in adapters if not a["state"].startswith("READY")]
    report = {
        "status": "PRODUCTION_ADAPTER_READY" if not not_ready else "PRODUCTION_ADAPTER_BLOCKED",
        "manifest_sha256": got_sha,
        "registered_runs": len(rows),
        "blind_runs": blind,
        "group_counts": dict(groups),
        "adapter_state_counts": dict(states),
        "blocked_run_ids": [a["run_id"] for a in not_ready],
        "sentinel_contract": BRANCH_TO_SENTINEL | {
            "zero_cross_section_null": -9,
            "identical_label_null": -10,
        },
        "control_contract": (
            "identical_label_null uses mH=mL and the same frozen HL Rutherford law; "
            "modes -1..-9 keep the physical mH/mL=3 fail-closed contract"
        ),
        "adapters": adapters,
    }
    out = json.dumps(report, indent=2, sort_keys=True)
    print(out)
    if args.report:
        Path(args.report).write_text(out + "\n")
    if args.require_production_ready and not_ready:
        raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
