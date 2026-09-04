#!/usr/bin/env python3
"""Phase186 fail-closed audit of the preregistered D3 final-claim gate set.

This module does not evaluate campaign data and does not add or change a physics
threshold. It answers a narrower pre-data question: does the current production
pipeline actually implement every fatal gate that Phase165 preregistered before a
10-Gyr physical M11 claim may be promoted?
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

# Coverage is credited only when executable code evaluates the original frozen
# semantics. Phase187 closes the seven gaps identified by the first Phase186
# audit; Phase174/181 keep their earlier gates.
CURRENT_COVERAGE: Mapping[str, str] = {
    "energy_drift": (
        "Phase187 rebuilds the frozen production source with only "
        "COMPUTE_POTENTIAL_ENERGY added, re-opens immutable scheduled snapshots "
        "through GIZMO restart-from-snapshot mode, and enforces max |dE/E| < 0.01; "
        "the registered median <0.003 preference remains non-fatal."
    ),
    "momentum_drift": (
        "Phase187 reads the same frozen H/L snapshots and evaluates the total-mass-"
        "normalized center-of-mass momentum drift at every registered epoch, with "
        "the frozen <1e-4 code-unit threshold."
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
        "Phase187 evaluates the nine registered constant-SIDM2c benchmark runs "
        "against the corrected Yang Read-profile parameterization at 10 Gyr over "
        "the frozen 0.03-5 r_s profile grid, requiring median error <10%."
    ),
    "CDM_stability": (
        "Phase187 evaluates core CDM total-profile median drift at every frozen "
        "epoch through 10 Gyr and enforces the registered <3% gate."
    ),
    "SIDMx_HL_causal_signal": (
        "Phase187 evaluates matched-seed SIDMx-minus-CDM central H/L segregation "
        "at R2 and R3, requiring Delta S>0, H-in/L-out direction, and signal above "
        "one seed SEM."
    ),
    "HL_off_mimic_rejection": (
        "Phase187 evaluates matched-seed SIDMx versus HL-off separation at R2/R3 "
        "and requires the paired separation to exceed one SEM, implementing the "
        "frozen one-sigma mimic-rejection boundary rather than the old sign-only proxy."
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
        "Phase187 evaluates matched-seed branch-minus-CDM S for promoted SIDMx and "
        "SIDM2v claims at R2/R3 and requires branch separation > one seed SEM."
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
            "has an implemented evaluator. It does not mean campaign data passed "
            "those gates. The registered SIDM2c collapse-clock diagnostic remains "
            "non-fatal and may still be reported separately."
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
