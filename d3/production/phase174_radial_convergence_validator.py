#!/usr/bin/env python3
"""Phase 174 fail-closed radial convergence validator for the frozen Phase172 campaign.

This closes the gap left by Phase166: the old validator implemented only a scalar
SIDM2v R2/R3 proxy while the frozen acceptance gates explicitly required
species-resolved radial profile convergence.

Fatal inherited gates are evaluated at 10 Gyr, before production outputs are
inspected, with the original thresholds unchanged:

  R2 -> R3 SIDM2v species-profile delta < 10%
  T_base -> T_half SIDM2v species-profile delta < 5%
  K_low/K_high -> K_base SIDM2v species-profile delta < 7%

The radial domain is the frozen 0.03 <= r/r_s <= 3.0 interval.  "profile delta
max" is made operational as the maximum pointwise fractional density difference
over matched seed, species, and common radial bins.  The more refined/control
member is the denominator:

  resolution: |rho_R2/rho_R3 - 1|
  timestep:   |rho_Tbase/rho_Thalf - 1|
  neighbors:  |rho_Kvariant/rho_Kbase - 1|

No interpolation, averaging, fit, smoothing, or post-hoc tolerance is allowed.
All gate-participating runs must also pass the frozen collision-log conservation
and probability-clipping audit.

This validates supplied production tables.  It does not generate physics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase172_lock  # noqa: E402

EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"

GATE_TIME_GYR = 10.0
R_MIN_OVER_RS = 0.03
R_MAX_OVER_RS = 3.0
TIME_TOL = 1.0e-9
BIN_TOL = 1.0e-12

THRESHOLDS = {
    "sidm2v_resolution_profile_delta_max": 0.10,
    "timestep_profile_delta_max": 0.05,
    "neighbor_profile_delta_max": 0.07,
    "max_pair_dP_over_P": 1.0e-12,
    "max_pair_dK_over_K": 1.0e-12,
    "prob_clip_fraction_max": 0.005,
}

EXPECTED_ANALYSIS_TIMES_GYR = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0)
PROFILE_REQUIRED = (
    "run_id", "time_Gyr", "r_mid_over_rs", "r_lo_over_rs", "r_hi_over_rs",
    "species", "rho", "rho_initial", "rho_rel", "sigma2", "beta", "mass_enclosed",
)
COLLISION_REQUIRED = (
    "run_id", "channel", "collision_count", "mean_sigma_factor", "mean_mu",
    "max_pair_dP_over_P", "max_pair_dK_over_K", "prob_clip_fraction_max",
)
FULL_CHANNELS = ("HH", "LL", "HL")


class ValidationError(RuntimeError):
    pass


def _finite_float(value: str, label: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValidationError(f"{label}: not a float: {value!r}") from exc
    if not math.isfinite(out):
        raise ValidationError(f"{label}: non-finite value {out!r}")
    return out


def _read_csv(path: Path, required: Sequence[str]) -> List[Dict[str, str]]:
    if not path.is_file():
        raise ValidationError(f"missing required file: {path}")
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = tuple(reader.fieldnames or ())
        missing = [c for c in required if c not in fields]
        if missing:
            raise ValidationError(f"{path.name}: missing required columns: {missing}")
        rows = [dict(r) for r in reader]
    if not rows:
        raise ValidationError(f"{path.name}: empty table")
    return rows


def load_manifest(path: Path | None) -> Tuple[bytes, List[Dict[str, str]]]:
    if path is None:
        raw, rows = phase172_lock.load()
    else:
        if not path.is_file():
            raise ValidationError(f"manifest missing: {path}")
        raw = path.read_bytes()
        rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_MANIFEST_SHA256:
        raise ValidationError(
            f"Phase172 manifest SHA mismatch: {observed} != {EXPECTED_MANIFEST_SHA256}"
        )
    if len(rows) != 127 or len({r["run_id"] for r in rows}) != 127:
        raise ValidationError("Phase172 manifest row/ID contract changed")
    return raw, rows


def _unique(rows: Iterable[Dict[str, str]], label: str) -> Dict[str, str]:
    rows = list(rows)
    if len(rows) != 1:
        raise ValidationError(f"{label}: expected exactly one manifest row, found {len(rows)}")
    return rows[0]


def build_pairs(manifest: List[Dict[str, str]]) -> Dict[str, List[Tuple[Dict[str, str], Dict[str, str], str]]]:
    core = [r for r in manifest if r["group"] == "core_blind_production"]

    def core_row(branch: str, tier: str, seed: str) -> Dict[str, str]:
        return _unique(
            (r for r in core
             if r["branch"] == branch and r["resolution_tier"] == tier and r["seed"] == seed),
            f"core {branch} {tier} seed={seed}",
        )

    r2 = [r for r in core if r["branch"] == "SIDM2v" and r["resolution_tier"] == "R2_double"]
    r3 = [r for r in core if r["branch"] == "SIDM2v" and r["resolution_tier"] == "R3_gold"]
    if len(r2) != 4 or len(r3) != 4:
        raise ValidationError("frozen SIDM2v R2/R3 count changed")
    r2_seeds = {r["seed"] for r in r2}
    r3_seeds = {r["seed"] for r in r3}
    if r2_seeds != r3_seeds:
        raise ValidationError("SIDM2v R2/R3 seeds are no longer matched")
    resolution = [
        (core_row("SIDM2v", "R2_double", seed),
         core_row("SIDM2v", "R3_gold", seed),
         f"seed={seed}:R2/R3")
        for seed in sorted(r2_seeds)
    ]

    half = [
        r for r in manifest
        if r["group"] == "half_timestep_convergence"
        and r["branch"] == "SIDM2v"
        and r["timestep_control"] == "T_half"
    ]
    if len(half) != 3:
        raise ValidationError("frozen SIDM2v half-timestep count changed")
    timestep = [
        (core_row("SIDM2v", "R2_double", r["seed"]), r, f"seed={r['seed']}:Tbase/Thalf")
        for r in sorted(half, key=lambda x: x["seed"])
    ]

    neighbors = [
        r for r in manifest
        if r["group"] == "neighbor_kernel_convergence"
        and r["branch"] == "SIDM2v"
        and r["kernel_control"] in ("K_low", "K_high")
    ]
    lows = [r for r in neighbors if r["kernel_control"] == "K_low"]
    highs = [r for r in neighbors if r["kernel_control"] == "K_high"]
    if len(lows) != 3 or len(highs) != 3:
        raise ValidationError("frozen SIDM2v neighbor-control count changed")
    low_seeds = {r["seed"] for r in lows}
    high_seeds = {r["seed"] for r in highs}
    if low_seeds != high_seeds:
        raise ValidationError("K_low/K_high SIDM2v seeds are no longer matched")
    neighbor_pairs = []
    for variant in sorted(neighbors, key=lambda x: (x["seed"], x["kernel_control"])):
        base = core_row("SIDM2v", "R2_double", variant["seed"])
        neighbor_pairs.append(
            (variant, base, f"seed={variant['seed']}:{variant['kernel_control']}/Kbase")
        )

    return {
        "resolution": resolution,
        "timestep": timestep,
        "neighbor": neighbor_pairs,
    }


def _profile_index(rows: List[Dict[str, str]]) -> Dict[str, Dict[float, Dict[str, List[Tuple[float, float, float, float]]]]]:
    index: Dict[str, Dict[float, Dict[str, List[Tuple[float, float, float, float]]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    seen = set()
    for i, row in enumerate(rows, 2):
        rid = row["run_id"].strip()
        species = row["species"].strip().upper()
        if not rid:
            raise ValidationError(f"profiles.csv line {i}: empty run_id")
        if species not in ("H", "L", "TOTAL"):
            raise ValidationError(f"profiles.csv line {i}: unsupported species {row['species']!r}")
        if species == "TOTAL":
            continue

        t = _finite_float(row["time_Gyr"], f"profiles.csv line {i} time_Gyr")
        rmid = _finite_float(row["r_mid_over_rs"], f"profiles.csv line {i} r_mid_over_rs")
        rlo = _finite_float(row["r_lo_over_rs"], f"profiles.csv line {i} r_lo_over_rs")
        rhi = _finite_float(row["r_hi_over_rs"], f"profiles.csv line {i} r_hi_over_rs")
        rho = _finite_float(row["rho"], f"profiles.csv line {i} rho")
        _finite_float(row["rho_initial"], f"profiles.csv line {i} rho_initial")
        _finite_float(row["rho_rel"], f"profiles.csv line {i} rho_rel")
        _finite_float(row["sigma2"], f"profiles.csv line {i} sigma2")
        _finite_float(row["beta"], f"profiles.csv line {i} beta")
        _finite_float(row["mass_enclosed"], f"profiles.csv line {i} mass_enclosed")
        if not (rlo < rmid < rhi):
            raise ValidationError(f"profiles.csv line {i}: invalid radial bin [{rlo}, {rmid}, {rhi}]")
        if rho <= 0.0:
            raise ValidationError(f"profiles.csv line {i}: rho must be positive")
        key = (rid, t, species, rlo, rmid, rhi)
        if key in seen:
            raise ValidationError(f"profiles.csv line {i}: duplicate profile key {key}")
        seen.add(key)
        index[rid][t][species].append((rlo, rmid, rhi, rho))

    for rid in index:
        for t in index[rid]:
            for species in index[rid][t]:
                index[rid][t][species].sort(key=lambda x: (x[1], x[0], x[2]))
    return index


def _time_key(run: Dict[float, object], target: float, rid: str) -> float:
    hits = [t for t in run if abs(t - target) <= TIME_TOL]
    if len(hits) != 1:
        raise ValidationError(f"{rid}: expected exactly one profile time {target} Gyr, found {hits}")
    return hits[0]


def _validate_profile_time_completeness(
    pidx: Dict[str, Dict[float, Dict[str, List[Tuple[float, float, float, float]]]]],
    run_ids: Iterable[str],
) -> None:
    for rid in sorted(set(run_ids)):
        if rid not in pidx:
            raise ValidationError(f"{rid}: missing from profiles.csv")
        for target in EXPECTED_ANALYSIS_TIMES_GYR:
            t = _time_key(pidx[rid], target, rid)
            for species in ("H", "L"):
                if species not in pidx[rid][t] or not pidx[rid][t][species]:
                    raise ValidationError(f"{rid}: missing {species} profile at {target} Gyr")


def _common_domain_rows(
    pidx: Dict[str, Dict[float, Dict[str, List[Tuple[float, float, float, float]]]]],
    rid: str,
    time: float,
    species: str,
) -> List[Tuple[float, float, float, float]]:
    tk = _time_key(pidx[rid], time, rid)
    rows = [
        x for x in pidx[rid][tk][species]
        if R_MIN_OVER_RS - BIN_TOL <= x[1] <= R_MAX_OVER_RS + BIN_TOL
    ]
    if not rows:
        raise ValidationError(
            f"{rid}: no {species} radial bins in frozen domain "
            f"{R_MIN_OVER_RS}..{R_MAX_OVER_RS} r_s at {time} Gyr"
        )
    return rows


def _same_bin(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
    return all(math.isclose(a[i], b[i], rel_tol=0.0, abs_tol=BIN_TOL) for i in range(3))


def profile_pair_delta(
    pidx: Dict[str, Dict[float, Dict[str, List[Tuple[float, float, float, float]]]]],
    candidate_id: str,
    reference_id: str,
    time: float,
) -> Dict:
    max_delta = -1.0
    worst = None
    n_points = 0
    for species in ("H", "L"):
        a = _common_domain_rows(pidx, candidate_id, time, species)
        b = _common_domain_rows(pidx, reference_id, time, species)
        if len(a) != len(b):
            raise ValidationError(
                f"{candidate_id} vs {reference_id}: {species} radial-bin count mismatch "
                f"at {time} Gyr ({len(a)} != {len(b)}); interpolation is forbidden"
            )
        for xa, xb in zip(a, b):
            if not _same_bin(xa, xb):
                raise ValidationError(
                    f"{candidate_id} vs {reference_id}: non-identical {species} radial grids "
                    f"at {time} Gyr; interpolation is forbidden"
                )
            rho_candidate = xa[3]
            rho_reference = xb[3]
            delta = abs(rho_candidate / rho_reference - 1.0)
            n_points += 1
            if delta > max_delta:
                max_delta = delta
                worst = {
                    "species": species,
                    "r_lo_over_rs": xa[0],
                    "r_mid_over_rs": xa[1],
                    "r_hi_over_rs": xa[2],
                    "rho_candidate": rho_candidate,
                    "rho_reference": rho_reference,
                    "fractional_delta": delta,
                }
    if n_points == 0 or worst is None:
        raise ValidationError(f"{candidate_id} vs {reference_id}: no comparable profile points")
    return {"max_fractional_delta": max_delta, "points_compared": n_points, "worst": worst}


def evaluate_family(
    pidx,
    pairs: List[Tuple[Dict[str, str], Dict[str, str], str]],
    threshold: float,
    family_name: str,
) -> Dict:
    details = []
    overall = -1.0
    overall_worst = None
    for candidate, reference, label in pairs:
        result = profile_pair_delta(
            pidx, candidate["run_id"], reference["run_id"], GATE_TIME_GYR
        )
        detail = {
            "label": label,
            "candidate_run_id": candidate["run_id"],
            "reference_run_id": reference["run_id"],
            **result,
        }
        details.append(detail)
        if result["max_fractional_delta"] > overall:
            overall = result["max_fractional_delta"]
            overall_worst = detail
    passed = overall < threshold
    return {
        "gate": family_name,
        "passed": passed,
        "fatal": True,
        "time_Gyr": GATE_TIME_GYR,
        "radial_domain_r_over_rs": [R_MIN_OVER_RS, R_MAX_OVER_RS],
        "metric": "max abs(rho_candidate/rho_reference - 1) over matched seeds/species/common bins",
        "threshold": threshold,
        "observed_max": overall,
        "worst": overall_worst,
        "comparisons": details,
    }


def _collision_audit(rows: List[Dict[str, str]], required_run_ids: Iterable[str]) -> Dict:
    by_run: Dict[str, Dict[str, Dict]] = defaultdict(dict)
    for i, row in enumerate(rows, 2):
        rid = row["run_id"].strip()
        channel = row["channel"].strip().upper()
        if not rid:
            raise ValidationError(f"collision_log_summary.csv line {i}: empty run_id")
        if not channel:
            raise ValidationError(f"collision_log_summary.csv line {i}: empty channel")
        if channel in by_run[rid]:
            raise ValidationError(f"collision_log_summary.csv line {i}: duplicate {rid}/{channel}")
        count_f = _finite_float(row["collision_count"], f"collision line {i} collision_count")
        if count_f < 0 or abs(count_f - round(count_f)) > 1e-9:
            raise ValidationError(f"collision line {i}: collision_count must be a nonnegative integer")
        mean_sigma = _finite_float(row["mean_sigma_factor"], f"collision line {i} mean_sigma_factor")
        mean_mu = _finite_float(row["mean_mu"], f"collision line {i} mean_mu")
        dP = _finite_float(row["max_pair_dP_over_P"], f"collision line {i} max_pair_dP_over_P")
        dK = _finite_float(row["max_pair_dK_over_K"], f"collision line {i} max_pair_dK_over_K")
        clip = _finite_float(row["prob_clip_fraction_max"], f"collision line {i} prob_clip_fraction_max")
        if dP < 0 or dK < 0 or clip < 0:
            raise ValidationError(f"collision line {i}: audit residuals/fractions must be nonnegative")
        by_run[rid][channel] = {
            "collision_count": int(round(count_f)),
            "mean_sigma_factor": mean_sigma,
            "mean_mu": mean_mu,
            "max_pair_dP_over_P": dP,
            "max_pair_dK_over_K": dK,
            "prob_clip_fraction_max": clip,
        }

    maxima = {
        "max_pair_dP_over_P": 0.0,
        "max_pair_dK_over_K": 0.0,
        "prob_clip_fraction_max": 0.0,
    }
    checked_rows = 0
    for rid in sorted(set(required_run_ids)):
        if rid not in by_run:
            raise ValidationError(f"{rid}: missing from collision_log_summary.csv")
        missing = [ch for ch in FULL_CHANNELS if ch not in by_run[rid]]
        if missing:
            raise ValidationError(f"{rid}: missing SIDM2v collision channels {missing}")
        for ch in FULL_CHANNELS:
            rec = by_run[rid][ch]
            checked_rows += 1
            for key in maxima:
                maxima[key] = max(maxima[key], rec[key])

    passed = (
        maxima["max_pair_dP_over_P"] < THRESHOLDS["max_pair_dP_over_P"]
        and maxima["max_pair_dK_over_K"] < THRESHOLDS["max_pair_dK_over_K"]
        and maxima["prob_clip_fraction_max"] < THRESHOLDS["prob_clip_fraction_max"]
    )
    return {
        "gate": "collision_log_integrity_for_radial_gate_runs",
        "passed": passed,
        "fatal": True,
        "checked_rows": checked_rows,
        "required_channels_per_run": list(FULL_CHANNELS),
        "observed_max": maxima,
        "thresholds": {
            "max_pair_dP_over_P": THRESHOLDS["max_pair_dP_over_P"],
            "max_pair_dK_over_K": THRESHOLDS["max_pair_dK_over_K"],
            "prob_clip_fraction_max": THRESHOLDS["prob_clip_fraction_max"],
        },
    }


def _diagnostic_all_times(pidx, pairs_by_family) -> Dict:
    """Report inherited-metric trajectories at every Phase172 time without adding gates."""
    out = {}
    for family, pairs in pairs_by_family.items():
        family_out = {}
        for t in EXPECTED_ANALYSIS_TIMES_GYR:
            values = []
            for candidate, reference, label in pairs:
                result = profile_pair_delta(pidx, candidate["run_id"], reference["run_id"], t)
                values.append({
                    "label": label,
                    "candidate_run_id": candidate["run_id"],
                    "reference_run_id": reference["run_id"],
                    **result,
                })
            family_out[str(t)] = {
                "observed_max": max(x["max_fractional_delta"] for x in values),
                "comparisons": values,
            }
        out[family] = family_out
    return out


def validate(
    profiles_path: Path,
    collision_path: Path,
    manifest_path: Path | None = None,
    include_all_time_diagnostics: bool = True,
) -> Dict:
    raw, manifest = load_manifest(manifest_path)
    pairs = build_pairs(manifest)
    profile_rows = _read_csv(profiles_path, PROFILE_REQUIRED)
    collision_rows = _read_csv(collision_path, COLLISION_REQUIRED)
    pidx = _profile_index(profile_rows)

    participating_ids = {
        r["run_id"]
        for family in pairs.values()
        for pair in family
        for r in pair[:2]
    }
    _validate_profile_time_completeness(pidx, participating_ids)

    gates = [
        evaluate_family(
            pidx, pairs["resolution"],
            THRESHOLDS["sidm2v_resolution_profile_delta_max"],
            "SIDM2v_R2_R3_radial_convergence",
        ),
        evaluate_family(
            pidx, pairs["timestep"],
            THRESHOLDS["timestep_profile_delta_max"],
            "SIDM2v_half_timestep_radial_convergence",
        ),
        evaluate_family(
            pidx, pairs["neighbor"],
            THRESHOLDS["neighbor_profile_delta_max"],
            "SIDM2v_neighbor_radial_convergence",
        ),
        _collision_audit(collision_rows, participating_ids),
    ]
    ok = all(g["passed"] for g in gates)

    result = {
        "phase": 174,
        "status": "PASS" if ok else "FAIL",
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "gate_time_Gyr": GATE_TIME_GYR,
        "radial_domain_r_over_rs": [R_MIN_OVER_RS, R_MAX_OVER_RS],
        "profile_metric_contract": {
            "observable": "rho",
            "species": ["H", "L"],
            "reduction": "maximum pointwise fractional difference",
            "resolution_formula": "abs(rho_R2/rho_R3 - 1)",
            "timestep_formula": "abs(rho_Tbase/rho_Thalf - 1)",
            "neighbor_formula": "max(abs(rho_Klow/rho_Kbase - 1), abs(rho_Khigh/rho_Kbase - 1))",
            "radial_grid": "exact common bins required; interpolation forbidden",
            "seed_matching": "exact frozen manifest seed",
            "threshold_comparison": "strictly less than",
        },
        "thresholds": dict(THRESHOLDS),
        "gates": gates,
    }
    if include_all_time_diagnostics:
        result["all_time_diagnostics_nonfatal"] = _diagnostic_all_times(pidx, pairs)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", required=True, type=Path)
    ap.add_argument("--collision-log-summary", required=True, type=Path)
    ap.add_argument("--manifest", type=Path, default=None,
                    help="optional materialized Phase172 manifest; SHA must match frozen lock")
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--no-all-time-diagnostics", action="store_true")
    args = ap.parse_args()

    try:
        result = validate(
            args.profiles,
            args.collision_log_summary,
            args.manifest,
            include_all_time_diagnostics=not args.no_all_time_diagnostics,
        )
    except ValidationError as exc:
        result = {
            "phase": 174,
            "status": "FAIL",
            "fatal_error": str(exc),
            "manifest_sha256_expected": EXPECTED_MANIFEST_SHA256,
        }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.out_json:
        args.out_json.write_text(text + "\n")
    raise SystemExit(0 if result.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()
