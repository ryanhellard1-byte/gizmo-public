#!/usr/bin/env python3
"""Canonical Phase174 full blind-physics validator.

The Phase172 validator remains responsible for the campaign-wide runtime,
benchmark, causal-signal, null-control, and fingerprint gates. Its original
radial convergence implementation is retained only as a diagnostic because it
averaged resolution seeds before comparison.

Phase174 supersedes those four legacy radial gates with exact matched-seed,
species-resolved, common-bin profile gates from
phase174_radial_convergence_validator.py.

Synthetic fixtures validate this program only. They are never physics evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import phase172_blind_physics_validator as legacy  # noqa: E402
import phase174_radial_convergence_validator as radial174  # noqa: E402


SUPERSEDED_LEGACY_RADIAL_GATES = {
    "SIDM2v_R2_R3_profile_convergence",
    "SIDM2v_half_timestep_profile_convergence",
    "SIDM2v_K_low_profile_convergence",
    "SIDM2v_K_high_profile_convergence",
}


def _legacy_without_superseded_radial(checks):
    out = []
    for check in checks:
        item = dict(check)
        if item.get("gate") in SUPERSEDED_LEGACY_RADIAL_GATES:
            item["fatal"] = False
            item["superseded_by"] = "Phase174 matched-seed radial convergence gate"
        out.append(item)
    ok = all(bool(c.get("passed")) or not bool(c.get("fatal", True)) for c in out)
    return ok, out


def validate_detailed(manifest, run_summary, profiles, collision_summary):
    _legacy_ok_original, legacy_checks = legacy.validate(
        manifest, run_summary, profiles, collision_summary
    )
    legacy_ok, checks = _legacy_without_superseded_radial(legacy_checks)

    radial_result = None
    radial_ok = False
    try:
        radial_result = radial174.validate(
            Path(profiles),
            Path(collision_summary),
            Path(manifest),
            include_all_time_diagnostics=False,
        )
        radial_ok = radial_result.get("status") == "PASS"
        for gate in radial_result.get("gates", []):
            item = dict(gate)
            item["gate"] = "Phase174_" + str(item["gate"])
            checks.append(item)
    except radial174.ValidationError as exc:
        checks.append({
            "gate": "Phase174_radial_validator_structural_integrity",
            "passed": False,
            "fatal": True,
            "detail": {"error": str(exc)},
        })

    ok = legacy_ok and radial_ok
    detail = {
        "status": "PASS" if ok else "FAIL",
        "legacy_radial_gates_superseded": sorted(SUPERSEDED_LEGACY_RADIAL_GATES),
        "phase174_profile_metric_contract": (
            radial_result.get("profile_metric_contract") if radial_result else None
        ),
        "phase174_thresholds": (
            radial_result.get("thresholds") if radial_result else dict(radial174.THRESHOLDS)
        ),
        "checks": checks,
    }
    return ok, checks, detail


def validate(manifest, run_summary, profiles, collision_summary):
    """Compatibility API used by phase172_validator_selftest.py."""
    ok, checks, _ = validate_detailed(
        manifest, run_summary, profiles, collision_summary
    )
    return ok, checks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-summary", required=True)
    p.add_argument("--profiles", required=True)
    p.add_argument("--collision-summary", required=True)
    p.add_argument("--out-json")
    a = p.parse_args()

    ok, _checks, result = validate_detailed(
        a.manifest, a.run_summary, a.profiles, a.collision_summary
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if a.out_json:
        Path(a.out_json).write_text(text + "\n")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
