#!/usr/bin/env python3
"""Phase187 closure of the seven Phase186-missing fatal claim evaluators.

This module intentionally does not change the frozen Phase165/166 thresholds.
It consumes a one-row-per-run scalar evidence table plus the frozen Phase172
manifest and evaluates the original Phase166 semantics, with one repair:
Phase165 registered seed_stability but Phase166 never evaluated it.  Phase187
adds that missing fatal evaluator for the SIDM2v promoted finite-amplitude claim.

The scalar evidence table is analysis output, not a substitute for production
simulation data.  Mock inputs prove validator behavior only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

PHASE = 187
EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"

THRESHOLDS = {
    "energy_drift_abs_max": 0.01,
    "energy_drift_median_preferred": 0.003,
    "momentum_drift_abs_max": 1.0e-4,
    "cdm_profile_median_drift_10Gyr": 0.03,
    "sidm2c_profile_median_error_10Gyr": 0.10,
    "sidm2c_collapse_clock_error_frac": 0.15,
    "sidmx_min_positive_deltaS_R2_R3": 0.0,
    "hl_off_mimic_margin": 0.0,
    "seed_branch_separation_min_sigma": 1.0,
}

REQUIRED_COLUMNS = (
    "run_id", "branch", "group", "resolution_tier", "seed", "status",
    "energy_drift_abs_max", "momentum_drift_abs_max",
    "cdm_profile_median_drift_10Gyr", "sidm2c_profile_median_error_10Gyr",
    "sidm2c_collapse_clock_error_frac", "S_inner_10Gyr", "O_overlap_10Gyr",
    "H_in_L_out_score", "analysis_sha256", "source_evidence_sha256",
)

MISSING_GATE_FAMILIES = (
    "energy_drift",
    "momentum_drift",
    "SIDM2c_total_profile_recovery",
    "CDM_stability",
    "SIDMx_HL_causal_signal",
    "HL_off_mimic_rejection",
    "seed_stability",
)


class FatalGateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def finite(value: object, label: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise FatalGateError(f"invalid float {label}={value!r}") from exc
    if not math.isfinite(x):
        raise FatalGateError(f"non-finite float {label}={value!r}")
    return x


def optional_finite(value: object, label: str) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return finite(value, label)


def sem(values: Sequence[float]) -> float:
    vals = [float(x) for x in values if math.isfinite(float(x))]
    if len(vals) <= 1:
        return float("inf")
    return statistics.stdev(vals) / math.sqrt(len(vals))


def add(checks: List[Dict], gate: str, passed: bool, detail: Dict, fatal: bool = True) -> bool:
    checks.append({"gate": gate, "passed": bool(passed), "fatal": bool(fatal), "detail": detail})
    return bool(passed) or not fatal


def keyed(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in rows:
        rid = str(row.get("run_id", ""))
        if not rid:
            raise FatalGateError("blank run_id")
        if rid in out:
            raise FatalGateError(f"duplicate run_id {rid}")
        out[rid] = row
    return out


def _group(rows: Iterable[Dict[str, str]], *, branch: str | None = None,
           group: str | None = None, tiers: set[str] | None = None) -> List[Dict[str, str]]:
    out = []
    for r in rows:
        if branch is not None and str(r["branch"]) != branch:
            continue
        if group is not None and str(r["group"]) != group:
            continue
        if tiers is not None and str(r["resolution_tier"]) not in tiers:
            continue
        out.append(r)
    return out


def _vals(rows: Iterable[Dict[str, str]], column: str, allow_blank: bool = False) -> List[float]:
    vals = []
    for r in rows:
        v = optional_finite(r.get(column), f"{r.get('run_id')}:{column}")
        if v is None:
            if allow_blank:
                continue
            raise FatalGateError(f"{r.get('run_id')}: blank required metric {column}")
        vals.append(v)
    return vals


def _paired_branch_delta(rows: List[Dict[str, str]], tier: str,
                         branch: str, reference: str = "CDM") -> Dict:
    selected = [r for r in rows if r["group"] == "core_blind_production" and r["resolution_tier"] == tier]
    a = {str(r["seed"]): r for r in selected if r["branch"] == branch}
    b = {str(r["seed"]): r for r in selected if r["branch"] == reference}
    if not a or set(a) != set(b):
        raise FatalGateError(
            f"{tier}: paired seed mismatch {branch}={sorted(a)} {reference}={sorted(b)}"
        )
    deltas = []
    for seed in sorted(a):
        av = finite(a[seed]["S_inner_10Gyr"], f"{a[seed]['run_id']}:S_inner_10Gyr")
        bv = finite(b[seed]["S_inner_10Gyr"], f"{b[seed]['run_id']}:S_inner_10Gyr")
        deltas.append({"seed": int(seed), "delta_S": av - bv,
                       "branch_run_id": a[seed]["run_id"], "reference_run_id": b[seed]["run_id"]})
    nums = [d["delta_S"] for d in deltas]
    mean = statistics.fmean(nums)
    noise = sem(nums)
    sigma = abs(mean) / noise if math.isfinite(noise) and noise > 0 else (float("inf") if mean != 0 else 0.0)
    return {"tier": tier, "pairs": deltas, "mean_delta_S": mean, "sem_delta_S": noise,
            "branch_separation_sigma": sigma}


def validate(manifest_path: Path, scalar_evidence_path: Path,
             expected_manifest_sha: str = EXPECTED_MANIFEST_SHA256) -> Tuple[bool, List[Dict]]:
    checks: List[Dict] = []
    ok = True
    observed_sha = sha256_file(manifest_path)
    ok &= add(checks, "manifest_sha256_matches_frozen_phase172",
              observed_sha == expected_manifest_sha,
              {"observed": observed_sha, "expected": expected_manifest_sha})

    man_fields, manifest = read_csv(manifest_path)
    out_fields, out = read_csv(scalar_evidence_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in out_fields]
    ok &= add(checks, "phase187_required_columns_present", not missing, {"missing": missing})
    if missing:
        return False, checks

    man = keyed(manifest)
    ev = keyed(out)
    ok &= add(checks, "exact_manifest_run_coverage", set(man) == set(ev), {
        "missing": sorted(set(man) - set(ev))[:10],
        "extra": sorted(set(ev) - set(man))[:10],
        "manifest_count": len(man), "evidence_count": len(ev),
    })

    mismatch = []
    for rid in sorted(set(man) & set(ev)):
        for col in ("branch", "group", "resolution_tier", "seed"):
            if str(man[rid].get(col)) != str(ev[rid].get(col)):
                mismatch.append({"run_id": rid, "column": col,
                                 "manifest": man[rid].get(col), "evidence": ev[rid].get(col)})
    ok &= add(checks, "manifest_metadata_matches_scalar_evidence", not mismatch,
              {"mismatch_count": len(mismatch), "sample": mismatch[:10]})
    ok &= add(checks, "all_scalar_evidence_complete",
              all(str(r["status"]) == "COMPLETE" for r in out),
              {"non_complete": sum(str(r["status"]) != "COMPLETE" for r in out)})
    ok &= add(checks, "analysis_fingerprints_present",
              all(len(str(r["analysis_sha256"]).strip()) >= 32 and len(str(r["source_evidence_sha256"]).strip()) >= 32 for r in out),
              {"rows": len(out)})

    energy = _vals(out, "energy_drift_abs_max")
    max_energy = max(energy) if energy else float("inf")
    med_energy = statistics.median(energy) if energy else float("inf")
    ok &= add(checks, "energy_drift_hard_gate", max_energy < THRESHOLDS["energy_drift_abs_max"],
              {"max": max_energy, "threshold_strict_lt": THRESHOLDS["energy_drift_abs_max"]})
    add(checks, "energy_drift_median_preferred", med_energy < THRESHOLDS["energy_drift_median_preferred"],
        {"median": med_energy, "preferred_strict_lt": THRESHOLDS["energy_drift_median_preferred"]}, fatal=False)

    momentum = _vals(out, "momentum_drift_abs_max")
    max_momentum = max(momentum) if momentum else float("inf")
    ok &= add(checks, "momentum_drift_gate", max_momentum < THRESHOLDS["momentum_drift_abs_max"],
              {"max": max_momentum, "threshold_strict_lt": THRESHOLDS["momentum_drift_abs_max"]})

    cdm = _group(out, branch="CDM")
    cdm_vals = _vals(cdm, "cdm_profile_median_drift_10Gyr", allow_blank=True)
    ok &= add(checks, "CDM_runs_present", bool(cdm), {"count": len(cdm)})
    ok &= add(checks, "CDM_profile_stability",
              bool(cdm_vals) and max(cdm_vals) < THRESHOLDS["cdm_profile_median_drift_10Gyr"],
              {"max": max(cdm_vals) if cdm_vals else None,
               "threshold_strict_lt": THRESHOLDS["cdm_profile_median_drift_10Gyr"]})

    c2 = _group(out, branch="SIDM2c_const")
    c2_vals = _vals(c2, "sidm2c_profile_median_error_10Gyr", allow_blank=True)
    ok &= add(checks, "SIDM2c_benchmark_runs_present", bool(c2), {"count": len(c2)})
    ok &= add(checks, "SIDM2c_profile_recovery",
              bool(c2_vals) and max(c2_vals) < THRESHOLDS["sidm2c_profile_median_error_10Gyr"],
              {"max": max(c2_vals) if c2_vals else None,
               "threshold_strict_lt": THRESHOLDS["sidm2c_profile_median_error_10Gyr"]})
    clock = _vals(c2, "sidm2c_collapse_clock_error_frac", allow_blank=True)
    add(checks, "SIDM2c_collapse_clock_preferred",
        bool(clock) and max(clock) < THRESHOLDS["sidm2c_collapse_clock_error_frac"],
        {"max": max(clock) if clock else None,
         "preferred_strict_lt": THRESHOLDS["sidm2c_collapse_clock_error_frac"]}, fatal=False)

    r23 = {"R2_double", "R3_gold"}
    sx = _group(out, branch="SIDMx", group="core_blind_production", tiers=r23)
    hl = _group(out, branch="HL_off", group="core_blind_production", tiers=r23)
    ok &= add(checks, "SIDMx_R2_R3_runs_present", len(sx) >= 8, {"count": len(sx)})
    if sx:
        sx_s = _vals(sx, "S_inner_10Gyr")
        sx_dir = _vals(sx, "H_in_L_out_score")
        sx_mean = statistics.fmean(sx_s)
        sx_noise = sem(sx_s)
        ok &= add(checks, "SIDMx_positive_deltaS_R2_R3",
                  sx_mean > THRESHOLDS["sidmx_min_positive_deltaS_R2_R3"], {"mean": sx_mean})
        ok &= add(checks, "SIDMx_H_in_L_out_R2_R3", statistics.fmean(sx_dir) > 0.0,
                  {"mean": statistics.fmean(sx_dir)})
        ok &= add(checks, "SIDMx_signal_beats_seed_noise", abs(sx_mean) > sx_noise,
                  {"mean": sx_mean, "sem": sx_noise})
    else:
        ok = False

    if sx and hl:
        sx_mean = statistics.fmean(_vals(sx, "S_inner_10Gyr"))
        hl_mean = statistics.fmean(_vals(hl, "S_inner_10Gyr"))
        sep = sx_mean - hl_mean
        ok &= add(checks, "HL_off_mimic_rejection", sep > THRESHOLDS["hl_off_mimic_margin"],
                  {"SIDMx_mean": sx_mean, "HL_off_mean": hl_mean, "separation": sep,
                   "threshold_strict_gt": THRESHOLDS["hl_off_mimic_margin"]})
    else:
        ok &= add(checks, "HL_off_mimic_rejection", False,
                  {"error": "missing SIDMx or HL_off R2/R3 core evidence"})

    # Phase165 registered this fatal gate, but Phase166 never evaluated it.
    # Apply it to the promoted SIDM2v finite-amplitude claim using matched
    # core-production CDM controls, independently at R2 and R3.
    seed_details = []
    seed_pass = True
    for tier in ("R2_double", "R3_gold"):
        try:
            d = _paired_branch_delta(out, tier, "SIDM2v", "CDM")
            d["threshold_min_sigma"] = THRESHOLDS["seed_branch_separation_min_sigma"]
            d["passed"] = d["branch_separation_sigma"] >= THRESHOLDS["seed_branch_separation_min_sigma"]
            seed_pass &= bool(d["passed"])
            seed_details.append(d)
        except FatalGateError as exc:
            seed_pass = False
            seed_details.append({"tier": tier, "passed": False, "error": str(exc)})
    ok &= add(checks, "SIDM2v_seed_stability", seed_pass, {
        "definition": "abs(mean paired SIDM2v-minus-CDM S_inner_10Gyr) / SEM of paired deltas",
        "required_tiers": ["R2_double", "R3_gold"],
        "threshold_min_sigma": THRESHOLDS["seed_branch_separation_min_sigma"],
        "tiers": seed_details,
    })

    return bool(ok), checks


def report(manifest: Path, scalar_evidence: Path) -> Dict:
    ok, checks = validate(manifest, scalar_evidence)
    return {
        "phase": PHASE,
        "status": "PASS" if ok else "FAIL",
        "kind": "preregistered_fatal_gate_evaluation",
        "implemented_gate_families": list(MISSING_GATE_FAMILIES),
        "thresholds": THRESHOLDS,
        "manifest_sha256": sha256_file(manifest),
        "scalar_evidence_sha256": sha256_file(scalar_evidence),
        "checks": checks,
        "claim_boundary": (
            "PASS means the seven fatal Phase165 claim families missing at the Phase186 boundary "
            "passed on supplied campaign evidence. It does not replace Phase174 radial/collision "
            "gates and does not by itself establish a dark-matter discovery or observational uniqueness."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--scalar-evidence", required=True)
    ap.add_argument("--out-json")
    args = ap.parse_args()
    try:
        result = report(Path(args.manifest), Path(args.scalar_evidence))
        text = json.dumps(result, indent=2, sort_keys=True)
        print(text)
        if args.out_json:
            Path(args.out_json).write_text(text + "\n")
        return 0 if result["status"] == "PASS" else 1
    except (FatalGateError, OSError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "ERROR", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
