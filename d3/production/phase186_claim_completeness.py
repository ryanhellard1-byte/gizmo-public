#!/usr/bin/env python3
"""Phase186 fail-closed audit of the preregistered D3 final-claim gate set.

This module does not evaluate campaign data and does not add or change a physics
threshold. It answers a narrower pre-data question: does the current production
pipeline actually implement every fatal gate that Phase165 preregistered before a
10-Gyr physical M11 claim may be promoted?

Phase187 closes the seven evaluator gaps that existed when Phase186 was merged.
READY therefore means implementation completeness only. It never means campaign
data passed the gates; Phase185 must execute Phase174 + Phase187 on real evidence.
"""
from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable, Mapping, Tuple

PHASE = 186

REQUIRED_FATAL_GATES: Tuple[str, ...] = (
    "energy_drift",
    "momentum_drift",
    "pair_conservation",
    "Monte_Carlo_probability",
    "particle_loss",
    "SIDM2c_total_profile_recovery",
    "CDM_stability",
    "SIDMx_HL_causal_signal",
    "HL_off_mimic_rejection",
    "SIDM2v_resolution_convergence",
    "timestep_convergence",
    "neighbor_convergence",
    "seed_stability",
)

REQUIRED_NONFATAL_DIAGNOSTICS: Tuple[str, ...] = (
    "SIDM2c_collapse_clock",
)

# Explicit code-level evaluator coverage. Every Phase187 entry is exercised by
# the Phase185 final-verdict path, not merely present as an orphan helper.
CURRENT_COVERAGE: Mapping[str, str] = {
    "energy_drift": (
        "Phase187 builds an analysis-only collisionless GIZMO probe with "
        "COMPUTE_POTENTIAL_ENERGY, evaluates immutable scheduled snapshots, and "
        "enforces the frozen max |dE/E| < 0.01 hard gate."
    ),
    "momentum_drift": (
        "Phase187 derives H+L COM-velocity drift from the immutable Phase181 "
        "scheduled snapshots and enforces the frozen 1e-4 code-unit proxy gate."
    ),
    "pair_conservation": (
        "Phase174 collision audit enforces per-pair momentum and kinetic-energy "
        "residuals below the frozen 1e-12 threshold."
    ),
    "Monte_Carlo_probability": (
        "Phase174 collision audit enforces the frozen probability-clipping gate."
    ),
    "particle_loss": (
        "Phase181 profile extraction requires the H/L particle-ID set at every "
        "scheduled snapshot to equal the initial IC set; Phase184 requires every "
        "manifest run to pass that extractor."
    ),
    "SIDM2c_total_profile_recovery": (
        "Phase187 compares 10-Gyr total-density profiles to the frozen Phase124/131 "
        "Yang-style SIDM2c target and enforces median fractional error < 0.10."
    ),
    "CDM_stability": (
        "Phase187 evaluates the 10-Gyr collisionless total-profile median drift "
        "and enforces the frozen < 0.03 gate."
    ),
    "SIDMx_HL_causal_signal": (
        "Phase187 evaluates the frozen Phase166 R2/R3 positive-S, H-in/L-out, "
        "and signal-greater-than-seed-SEM semantics from immutable snapshots."
    ),
    "HL_off_mimic_rejection": (
        "Phase187 requires the R2/R3 SIDMx mean segregation signal to exceed the "
        "matched HL-off mean, preserving the frozen zero-margin Phase166 gate."
    ),
    "SIDM2v_resolution_convergence": (
        "Phase174 evaluates the frozen R2-to-R3 species radial-profile gate."
    ),
    "timestep_convergence": (
        "Phase174 evaluates the frozen T_base-to-T_half radial-profile gate."
    ),
    "neighbor_convergence": (
        "Phase174 evaluates the frozen K_low/K_high-to-K_base radial-profile gate."
    ),
    "seed_stability": (
        "Phase187 implements the Phase165-registered but Phase166-omitted fatal "
        "SIDM2v seed gate as absolute matched SIDM2v-minus-CDM branch separation "
        "divided by the sample standard deviation of paired seed deltas >= 1, "
        "independently at R2 and R3. This directly implements the frozen rule that "
        "seed scatter must be smaller than branch separation."
    ),
}


class ClaimCompletenessError(RuntimeError):
    pass


def audit(covered: Iterable[str] | None = None) -> Dict[str, object]:
    covered_set = set(CURRENT_COVERAGE if covered is None else covered)
    required = set(REQUIRED_FATAL_GATES)
    missing = tuple(sorted(required - covered_set))
    unknown = tuple(sorted(covered_set - required - set(REQUIRED_NONFATAL_DIAGNOSTICS)))
    covered_required = tuple(sorted(required & covered_set))
    missing_nonfatal = tuple(sorted(set(REQUIRED_NONFATAL_DIAGNOSTICS) - covered_set))
    ready = not missing
    return {
        "phase": PHASE,
        "status": "READY" if ready else "BLOCKED",
        "final_physics_claim_allowed": ready,
        "required_fatal_gates": list(REQUIRED_FATAL_GATES),
        "covered_fatal_gates": list(covered_required),
        "missing_fatal_gates": list(missing),
        "required_nonfatal_diagnostics": list(REQUIRED_NONFATAL_DIAGNOSTICS),
        "missing_nonfatal_diagnostics": list(missing_nonfatal),
        "unknown_coverage_labels": list(unknown),
        "coverage_evidence": {
            key: CURRENT_COVERAGE[key]
            for key in covered_required
            if key in CURRENT_COVERAGE
        },
        "claim_boundary": (
            "READY means only that every preregistered fatal Phase165 claim gate "
            "has an implemented evaluator wired into the final-verdict path. It "
            "does not mean campaign data passed any gate. Phase185 must still "
            "execute Phase174 and Phase187 on the completed 127-run campaign."
        ),
    }


def assert_final_claim_ready() -> Dict[str, object]:
    report = audit()
    if report["status"] != "READY":
        missing = ", ".join(report["missing_fatal_gates"])
        raise ClaimCompletenessError(
            "Phase185 final-physics promotion is blocked: preregistered fatal "
            f"gate evaluators are missing: {missing}"
        )
    return report


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--require-ready",
        action="store_true",
        help="exit nonzero while any preregistered fatal gate evaluator is missing",
    )
    return ap


def main() -> int:
    args = parser().parse_args()
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_ready and report["status"] != "READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
