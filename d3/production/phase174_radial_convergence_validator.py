#!/usr/bin/env python3
"""Phase 174 radial convergence and collision-audit validator.

This closes the profile-level validation gap left by the Phase166 scalar proxy.
It consumes the frozen Phase172 manifest plus the real run_summary.csv,
profiles.csv, and collision_log_summary.csv artifacts.

Physics thresholds are inherited unchanged from the frozen Phase165/166 gates:
- SIDM2v R2 -> R3 species density-profile change < 10%
- T_base -> T_half density-profile change < 5%
- K_low/K_high -> K_base density-profile change < 7%
over 0.03 <= r/r_s <= 3 at the frozen 10 Gyr claim epoch.
- per-pair momentum and kinetic-energy residuals < 1e-12
- collision-probability clipping fraction < 0.005

No interpolation, fit, smoothing, radial averaging, or post-output tolerance is
introduced. Every matched radial bin must satisfy the applicable threshold.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase172_time_contract as time_contract  # noqa: E402

EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"

CLAIM_TIME_GYR = Decimal("10")
RADIUS_MIN_OVER_RS = Decimal("0.03")
RADIUS_MAX_OVER_RS = Decimal("3")

SIDM2V_RESOLUTION_MAX = 0.10
TIMESTEP_MAX = 0.05
NEIGHBOR_MAX = 0.07
PAIR_RESIDUAL_MAX = 1.0e-12
PROB_CLIP_MAX = 0.005

REQUIRED_SPECIES = {"h", "l", "total"}

PROFILE_REQUIRED = {
    "run_id", "time_Gyr", "r_mid_over_rs", "r_lo_over_rs", "r_hi_over_rs",
    "species", "rho", "rho_initial", "rho_rel", "sigma2", "beta", "mass_enclosed",
}
COLLISION_REQUIRED = {
    "run_id", "channel", "collision_count", "mean_sigma_factor", "mean_mu",
    "max_pair_dP_over_P", "max_pair_dK_over_K", "prob_clip_fraction_max",
}


class ValidationError(RuntimeError):
    pass


def add(checks: List[Dict], name: str, passed: bool, detail: Dict, fatal: bool = True) -> bool:
    checks.append({
        "gate": name,
        "passed": bool(passed),
        "fatal": bool(fatal),
        "detail": detail,
    })
    return bool(passed) or not fatal


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def dec(value: str, label: str) -> Decimal:
    try:
        out = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"invalid decimal {label}={value!r}") from exc
    if not out.is_finite():
        raise ValidationError(f"non-finite decimal {label}={value!r}")
    return out


def finite_float(value: str, label: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"invalid float {label}={value!r}") from exc
    if not math.isfinite(out):
        raise ValidationError(f"non-finite float {label}={value!r}")
    return out


def profile_key(row: Dict[str, str]) -> Tuple[str, Decimal, Decimal, Decimal]:
    species = str(row["species"]).strip().lower()
    return (
        species,
        dec(row["r_lo_over_rs"], "r_lo_over_rs"),
        dec(row["r_mid_over_rs"], "r_mid_over_rs"),
        dec(row["r_hi_over_rs"], "r_hi_over_rs"),
    )


def select_claim_profile_rows(
    profiles: Iterable[Dict[str, str]], run_id: str
) -> Dict[Tuple[str, Decimal, Decimal, Decimal], float]:
    selected: Dict[Tuple[str, Decimal, Decimal, Decimal], float] = {}
    seen_species = set()
    for row in profiles:
        if str(row["run_id"]) != str(run_id):
            continue
        if dec(row["time_Gyr"], "time_Gyr") != CLAIM_TIME_GYR:
            continue
        rmid = dec(row["r_mid_over_rs"], "r_mid_over_rs")
        if rmid < RADIUS_MIN_OVER_RS or rmid > RADIUS_MAX_OVER_RS:
            continue
        key = profile_key(row)
        species = key[0]
        if species not in REQUIRED_SPECIES:
            continue
        rho = finite_float(row["rho"], "rho")
        if rho <= 0.0:
            raise ValidationError(f"{run_id}: non-positive rho at key={key}: {rho}")
        if key in selected:
            raise ValidationError(f"{run_id}: duplicate 10-Gyr radial profile key={key}")
        selected[key] = rho
        seen_species.add(species)

    if not selected:
        raise ValidationError(
            f"{run_id}: no profile rows at 10 Gyr in 0.03<=r/r_s<=3"
        )
    missing = REQUIRED_SPECIES - seen_species
    if missing:
        raise ValidationError(
            f"{run_id}: missing required species at 10 Gyr in radial gate: {sorted(missing)}"
        )
    return selected


def compare_profile_pair(
    profiles: List[Dict[str, str]],
    reference_run: Dict[str, str],
    test_run: Dict[str, str],
) -> Dict:
    ref = select_claim_profile_rows(profiles, reference_run["run_id"])
    test = select_claim_profile_rows(profiles, test_run["run_id"])
    if set(ref) != set(test):
        missing_test = sorted(str(k) for k in (set(ref) - set(test)))[:10]
        extra_test = sorted(str(k) for k in (set(test) - set(ref)))[:10]
        raise ValidationError(
            f"profile-bin mismatch reference={reference_run['run_id']} "
            f"test={test_run['run_id']} missing_test={missing_test} extra_test={extra_test}"
        )

    worst = None
    deltas = []
    for key in sorted(ref, key=str):
        ref_rho = ref[key]
        test_rho = test[key]
        delta = abs(test_rho / ref_rho - 1.0)
        deltas.append(delta)
        if worst is None or delta > worst["delta"]:
            species, rlo, rmid, rhi = key
            worst = {
                "delta": delta,
                "species": species,
                "r_lo_over_rs": float(rlo),
                "r_mid_over_rs": float(rmid),
                "r_hi_over_rs": float(rhi),
                "reference_rho": ref_rho,
                "test_rho": test_rho,
            }

    return {
        "reference_run_id": reference_run["run_id"],
        "test_run_id": test_run["run_id"],
        "branch": test_run["branch"],
        "seed": int(test_run["seed"]),
        "points": len(deltas),
        "max_fractional_delta": max(deltas),
        "worst": worst,
    }


def one_by(rows: Iterable[Dict[str, str]], **criteria: str) -> Dict[str, str]:
    hits = []
    for row in rows:
        if all(str(row.get(k)) == str(v) for k, v in criteria.items()):
            hits.append(row)
    if len(hits) != 1:
        raise ValidationError(f"expected one manifest row for {criteria}, found {len(hits)}")
    return hits[0]


def radial_gate(
    name: str,
    profiles: List[Dict[str, str]],
    pairs: List[Tuple[Dict[str, str], Dict[str, str]]],
    threshold: float,
    checks: List[Dict],
) -> bool:
    if not pairs:
        return add(checks, name, False, {"error": "no matched pairs", "threshold": threshold})

    results = []
    errors = []
    for reference, test in pairs:
        try:
            results.append(compare_profile_pair(profiles, reference, test))
        except ValidationError as exc:
            errors.append({
                "reference_run_id": reference.get("run_id"),
                "test_run_id": test.get("run_id"),
                "error": str(exc),
            })

    worst = max(results, key=lambda x: x["max_fractional_delta"]) if results else None
    passed = (
        not errors
        and bool(results)
        and all(r["max_fractional_delta"] < threshold for r in results)
    )
    return add(
        checks,
        name,
        passed,
        {
            "definition": "max over every matched seed/species/common radial bin of abs(rho_test/rho_reference - 1)",
            "claim_time_Gyr": float(CLAIM_TIME_GYR),
            "radial_range_over_rs": [float(RADIUS_MIN_OVER_RS), float(RADIUS_MAX_OVER_RS)],
            "threshold_strict_lt": threshold,
            "matched_pairs": len(pairs),
            "evaluated_pairs": len(results),
            "errors": errors[:10],
            "worst": worst,
            "all_pair_maxima": results,
        },
    )


def build_resolution_pairs(manifest: List[Dict[str, str]]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    r2 = [
        r for r in manifest
        if r["group"] == "core_blind_production"
        and r["branch"] == "SIDM2v"
        and r["resolution_tier"] == "R2_double"
    ]
    r3 = [
        r for r in manifest
        if r["group"] == "core_blind_production"
        and r["branch"] == "SIDM2v"
        and r["resolution_tier"] == "R3_gold"
    ]
    r2_by_seed = {str(r["seed"]): r for r in r2}
    r3_by_seed = {str(r["seed"]): r for r in r3}
    if len(r2_by_seed) != len(r2) or len(r3_by_seed) != len(r3):
        raise ValidationError("duplicate SIDM2v core seed within R2 or R3")
    if set(r2_by_seed) != set(r3_by_seed):
        raise ValidationError(
            f"SIDM2v R2/R3 seed mismatch: R2={sorted(r2_by_seed)} R3={sorted(r3_by_seed)}"
        )
    return [(r3_by_seed[s], r2_by_seed[s]) for s in sorted(r2_by_seed)]


def build_timestep_pairs(manifest: List[Dict[str, str]]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    half = [
        r for r in manifest
        if r["group"] == "half_timestep_convergence" and r["branch"] == "SIDM2v"
    ]
    pairs = []
    for test in half:
        ref = one_by(
            manifest,
            group="core_blind_production",
            branch="SIDM2v",
            resolution_tier=test["resolution_tier"],
            seed=test["seed"],
        )
        if str(ref.get("timestep_control")) != "T_base":
            raise ValidationError(f"{ref['run_id']}: timestep reference is not T_base")
        if str(test.get("timestep_control")) != "T_half":
            raise ValidationError(f"{test['run_id']}: timestep test is not T_half")
        pairs.append((ref, test))
    return pairs


def build_neighbor_pairs(manifest: List[Dict[str, str]]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    variants = [
        r for r in manifest
        if r["group"] == "neighbor_kernel_convergence" and r["branch"] == "SIDM2v"
    ]
    pairs = []
    for test in variants:
        if str(test.get("kernel_control")) not in {"K_low", "K_high"}:
            raise ValidationError(
                f"{test['run_id']}: neighbor test must be K_low or K_high, got {test.get('kernel_control')}"
            )
        ref = one_by(
            manifest,
            group="core_blind_production",
            branch="SIDM2v",
            resolution_tier=test["resolution_tier"],
            seed=test["seed"],
        )
        if str(ref.get("kernel_control")) != "K_base":
            raise ValidationError(f"{ref['run_id']}: neighbor reference is not K_base")
        pairs.append((ref, test))
    return pairs


def validate_collision_summary(
    manifest: List[Dict[str, str]],
    collision_rows: List[Dict[str, str]],
    checks: List[Dict],
) -> bool:
    ok = True
    manifest_ids = {str(r["run_id"]) for r in manifest}
    collision_ids = {str(r["run_id"]) for r in collision_rows}
    ok &= add(
        checks,
        "collision_summary_exact_manifest_coverage",
        manifest_ids <= collision_ids,
        {
            "missing_count": len(manifest_ids - collision_ids),
            "missing_sample": sorted(manifest_ids - collision_ids)[:10],
        },
    )

    bad_count = []
    dp_vals = []
    dk_vals = []
    clip_vals = []
    invalid = []
    for i, row in enumerate(collision_rows):
        try:
            rid = str(row["run_id"])
            if rid not in manifest_ids:
                invalid.append({"row": i, "run_id": rid, "error": "run_id not in manifest"})
                continue
            count_f = finite_float(row["collision_count"], "collision_count")
            if count_f < 0 or not count_f.is_integer():
                bad_count.append({"row": i, "run_id": rid, "collision_count": count_f})
            dp = finite_float(row["max_pair_dP_over_P"], "max_pair_dP_over_P")
            dk = finite_float(row["max_pair_dK_over_K"], "max_pair_dK_over_K")
            clip = finite_float(row["prob_clip_fraction_max"], "prob_clip_fraction_max")
            if dp < 0 or dk < 0 or clip < 0:
                invalid.append({"row": i, "run_id": rid, "error": "negative audit metric"})
                continue
            dp_vals.append((dp, rid, str(row["channel"])))
            dk_vals.append((dk, rid, str(row["channel"])))
            clip_vals.append((clip, rid, str(row["channel"])))
        except ValidationError as exc:
            invalid.append({"row": i, "run_id": row.get("run_id"), "error": str(exc)})

    ok &= add(
        checks,
        "collision_counts_nonnegative_integers",
        not bad_count,
        {"bad_count": len(bad_count), "bad_sample": bad_count[:10]},
    )
    ok &= add(
        checks,
        "collision_audit_values_finite_nonnegative",
        not invalid,
        {"bad_count": len(invalid), "bad_sample": invalid[:10]},
    )

    if dp_vals:
        worst_dp = max(dp_vals)
        ok &= add(
            checks,
            "collision_pair_momentum_residual",
            worst_dp[0] < PAIR_RESIDUAL_MAX,
            {
                "max": worst_dp[0], "run_id": worst_dp[1], "channel": worst_dp[2],
                "threshold_strict_lt": PAIR_RESIDUAL_MAX,
            },
        )
    else:
        ok &= add(checks, "collision_pair_momentum_residual", False, {"error": "no valid values"})

    if dk_vals:
        worst_dk = max(dk_vals)
        ok &= add(
            checks,
            "collision_pair_energy_residual",
            worst_dk[0] < PAIR_RESIDUAL_MAX,
            {
                "max": worst_dk[0], "run_id": worst_dk[1], "channel": worst_dk[2],
                "threshold_strict_lt": PAIR_RESIDUAL_MAX,
            },
        )
    else:
        ok &= add(checks, "collision_pair_energy_residual", False, {"error": "no valid values"})

    if clip_vals:
        worst_clip = max(clip_vals)
        ok &= add(
            checks,
            "collision_probability_clipping",
            worst_clip[0] < PROB_CLIP_MAX,
            {
                "max": worst_clip[0], "run_id": worst_clip[1], "channel": worst_clip[2],
                "threshold_strict_lt": PROB_CLIP_MAX,
            },
        )
    else:
        ok &= add(checks, "collision_probability_clipping", False, {"error": "no valid values"})

    return bool(ok)


def validate(
    manifest_path: Path,
    run_summary_path: Path,
    profiles_path: Path,
    collision_path: Path,
) -> Tuple[bool, List[Dict]]:
    checks: List[Dict] = []
    ok = True

    raw = manifest_path.read_bytes()
    observed_sha = hashlib.sha256(raw).hexdigest()
    ok &= add(
        checks,
        "phase172_manifest_sha256_frozen",
        observed_sha == EXPECTED_MANIFEST_SHA256,
        {"observed": observed_sha, "expected": EXPECTED_MANIFEST_SHA256},
    )

    tc_checks = []
    tc_ok, manifest, _ = time_contract.validate_manifest(manifest_path, tc_checks)
    if tc_ok:
        tc_ok = time_contract.validate_outputs(
            manifest, run_summary_path, profiles_path, collision_path, tc_checks
        )
    checks.extend({"gate": f"phase172::{c['gate']}", **{k: v for k, v in c.items() if k != "gate"}}
                  for c in tc_checks)
    ok &= bool(tc_ok)

    profile_fields, profiles = read_csv(profiles_path)
    collision_fields, collisions = read_csv(collision_path)
    missing_profile = sorted(PROFILE_REQUIRED - set(profile_fields))
    missing_collision = sorted(COLLISION_REQUIRED - set(collision_fields))
    ok &= add(checks, "profile_schema_for_radial_gates", not missing_profile, {"missing": missing_profile})
    ok &= add(checks, "collision_schema_for_physics_gates", not missing_collision, {"missing": missing_collision})
    if missing_profile or missing_collision or not manifest:
        return False, checks

    try:
        resolution_pairs = build_resolution_pairs(manifest)
        timestep_pairs = build_timestep_pairs(manifest)
        neighbor_pairs = build_neighbor_pairs(manifest)
    except ValidationError as exc:
        add(checks, "matched_seed_pairing_contract", False, {"error": str(exc)})
        return False, checks

    ok &= add(
        checks,
        "matched_seed_pairing_contract",
        bool(resolution_pairs) and bool(timestep_pairs) and bool(neighbor_pairs),
        {
            "resolution_pairs": [
                {"reference": a["run_id"], "test": b["run_id"], "seed": b["seed"]}
                for a, b in resolution_pairs
            ],
            "timestep_pairs": [
                {"reference": a["run_id"], "test": b["run_id"], "seed": b["seed"]}
                for a, b in timestep_pairs
            ],
            "neighbor_pairs": [
                {"reference": a["run_id"], "test": b["run_id"], "seed": b["seed"],
                 "kernel_control": b.get("kernel_control")}
                for a, b in neighbor_pairs
            ],
        },
    )

    ok &= radial_gate(
        "SIDM2v_R2_R3_radial_density_convergence",
        profiles, resolution_pairs, SIDM2V_RESOLUTION_MAX, checks,
    )
    ok &= radial_gate(
        "SIDM2v_half_timestep_radial_density_convergence",
        profiles, timestep_pairs, TIMESTEP_MAX, checks,
    )
    ok &= radial_gate(
        "SIDM2v_neighbor_radial_density_convergence",
        profiles, neighbor_pairs, NEIGHBOR_MAX, checks,
    )
    ok &= validate_collision_summary(manifest, collisions, checks)

    return bool(ok), checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-summary", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--collision-summary", required=True)
    ap.add_argument("--out-json")
    args = ap.parse_args()

    ok, checks = validate(
        Path(args.manifest),
        Path(args.run_summary),
        Path(args.profiles),
        Path(args.collision_summary),
    )
    result = {
        "status": "PASS" if ok else "FAIL",
        "phase": 174,
        "claim_epoch_Gyr": float(CLAIM_TIME_GYR),
        "radial_range_over_rs": [float(RADIUS_MIN_OVER_RS), float(RADIUS_MAX_OVER_RS)],
        "thresholds": {
            "sidm2v_resolution_profile_delta_max": SIDM2V_RESOLUTION_MAX,
            "timestep_profile_delta_max": TIMESTEP_MAX,
            "neighbor_profile_delta_max": NEIGHBOR_MAX,
            "max_pair_dP_over_P": PAIR_RESIDUAL_MAX,
            "max_pair_dK_over_K": PAIR_RESIDUAL_MAX,
            "prob_clip_fraction_max": PROB_CLIP_MAX,
        },
        "checks": checks,
    }
    text = json.dumps(result, indent=2)
    print(text)
    if args.out_json:
        Path(args.out_json).write_text(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
