#!/usr/bin/env python3
"""
Phase166 blind gate validator for the Phase165 D3 production live-N-body manifest.

This validates output tables. It does NOT generate physics. If you feed it mock
data, it validates the lock, not the universe. Apparently that needs saying.
"""
import argparse, json, hashlib, sys
from pathlib import Path
import pandas as pd
import numpy as np
import math

THRESHOLDS = {
    "final_time_min_Gyr": 10.0,
    "energy_drift_abs_max": 0.01,
    "energy_drift_median_preferred": 0.003,
    "momentum_drift_abs_max": 1e-4,
    "max_pair_dP_over_P": 1e-12,
    "max_pair_dK_over_K": 1e-12,
    "prob_clip_fraction_max": 0.005,
    "particle_loss_untracked": 0,
    "cdm_profile_median_drift_10Gyr": 0.03,
    "sidm2c_profile_median_error_10Gyr": 0.10,
    "sidm2c_collapse_clock_error_frac": 0.15,
    "sidmx_min_positive_deltaS_R2_R3": 0.0,
    "hl_off_mimic_margin": 0.0,
    "sidm2v_resolution_profile_delta_max": 0.10,
    "timestep_profile_delta_max": 0.05,
    "neighbor_profile_delta_max": 0.07,
    "seed_branch_separation_min_sigma": 1.0
}

REQUIRED_COLUMNS = [
    "run_id","branch","group","resolution_tier","seed","status",
    "executable_sha256","analysis_sha256","output_sha256","final_time_Gyr",
    "energy_drift_abs_max","momentum_drift_abs_max","max_pair_dP_over_P",
    "max_pair_dK_over_K","prob_clip_fraction_max","particle_loss_untracked",
    "cdm_profile_median_drift_10Gyr","sidm2c_profile_median_error_10Gyr",
    "sidm2c_collapse_clock_error_frac","S_inner_10Gyr","O_overlap_10Gyr",
    "H_in_L_out_score","notes"
]

def sem(x):
    x = pd.Series(x).dropna()
    if len(x) <= 1:
        return float("inf")
    return float(x.std(ddof=1) / math.sqrt(len(x)))

def add(checks, name, passed, detail, fatal=True):
    checks.append({"gate": name, "passed": bool(passed), "fatal": bool(fatal), "detail": detail})
    return bool(passed) or not fatal

def validate(manifest_path, run_summary_path, expected_manifest_sha=None):
    checks = []
    ok = True

    manifest_path = Path(manifest_path)
    run_summary_path = Path(run_summary_path)
    manifest = pd.read_csv(manifest_path)
    out = pd.read_csv(run_summary_path)

    sha = hashlib.sha256(manifest_path.read_text().encode("utf-8")).hexdigest()
    if expected_manifest_sha:
        ok &= add(checks, "manifest_sha256_matches_expected", sha == expected_manifest_sha,
                  {"observed": sha, "expected": expected_manifest_sha})

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    ok &= add(checks, "required_columns_present", len(missing_cols) == 0, {"missing": missing_cols})

    if missing_cols:
        return False, checks

    man_ids = set(manifest.run_id.astype(str))
    out_ids = set(out.run_id.astype(str))
    ok &= add(checks, "all_manifest_runs_present", man_ids <= out_ids,
              {"missing_count": len(man_ids - out_ids), "missing_sample": sorted(list(man_ids - out_ids))[:10]})
    ok &= add(checks, "no_extra_run_ids", out_ids <= man_ids,
              {"extra_count": len(out_ids - man_ids), "extra_sample": sorted(list(out_ids - man_ids))[:10]})
    ok &= add(checks, "one_row_per_run_id", out.run_id.nunique() == len(out),
              {"rows": len(out), "unique_run_id": int(out.run_id.nunique())})

    merged = manifest.merge(out, on="run_id", suffixes=("_manifest","_out"), how="inner")
    mismatch = []
    for col in ["branch","group","resolution_tier","seed"]:
        bad = merged[merged[f"{col}_manifest"].astype(str) != merged[f"{col}_out"].astype(str)]
        if len(bad):
            mismatch.append({"column": col, "count": int(len(bad))})
    ok &= add(checks, "manifest_metadata_matches_outputs", len(mismatch) == 0, {"mismatch": mismatch})

    complete = out.status.eq("COMPLETE").all()
    ok &= add(checks, "all_runs_complete", complete, {"non_complete": int((~out.status.eq("COMPLETE")).sum())})

    ok &= add(checks, "final_time_reaches_10Gyr", out.final_time_Gyr.min() >= THRESHOLDS["final_time_min_Gyr"],
              {"min_final_time_Gyr": float(out.final_time_Gyr.min())})
    ok &= add(checks, "energy_drift_hard_gate", out.energy_drift_abs_max.max() < THRESHOLDS["energy_drift_abs_max"],
              {"max": float(out.energy_drift_abs_max.max()), "threshold": THRESHOLDS["energy_drift_abs_max"]})
    add(checks, "energy_drift_median_preferred", out.energy_drift_abs_max.median() < THRESHOLDS["energy_drift_median_preferred"],
        {"median": float(out.energy_drift_abs_max.median()), "preferred": THRESHOLDS["energy_drift_median_preferred"]}, fatal=False)

    ok &= add(checks, "momentum_drift_gate", out.momentum_drift_abs_max.max() < THRESHOLDS["momentum_drift_abs_max"],
              {"max": float(out.momentum_drift_abs_max.max())})
    ok &= add(checks, "pair_momentum_conservation_gate", out.max_pair_dP_over_P.max() < THRESHOLDS["max_pair_dP_over_P"],
              {"max": float(out.max_pair_dP_over_P.max())})
    ok &= add(checks, "pair_energy_conservation_gate", out.max_pair_dK_over_K.max() < THRESHOLDS["max_pair_dK_over_K"],
              {"max": float(out.max_pair_dK_over_K.max())})
    ok &= add(checks, "probability_clipping_gate", out.prob_clip_fraction_max.max() < THRESHOLDS["prob_clip_fraction_max"],
              {"max": float(out.prob_clip_fraction_max.max())})
    ok &= add(checks, "particle_loss_gate", out.particle_loss_untracked.max() <= THRESHOLDS["particle_loss_untracked"],
              {"max": int(out.particle_loss_untracked.max())})

    cdm = out[out.branch == "CDM"]
    ok &= add(checks, "CDM_runs_present", len(cdm) > 0, {"count": int(len(cdm))})
    if len(cdm):
        vals = cdm.cdm_profile_median_drift_10Gyr.dropna()
        ok &= add(checks, "CDM_profile_stability", len(vals) > 0 and vals.max() < THRESHOLDS["cdm_profile_median_drift_10Gyr"],
                  {"max": float(vals.max()) if len(vals) else None, "threshold": THRESHOLDS["cdm_profile_median_drift_10Gyr"]})

    c2 = out[out.branch == "SIDM2c_const"]
    ok &= add(checks, "SIDM2c_benchmark_runs_present", len(c2) > 0, {"count": int(len(c2))})
    if len(c2):
        vals = c2.sidm2c_profile_median_error_10Gyr.dropna()
        ok &= add(checks, "SIDM2c_profile_recovery", len(vals) > 0 and vals.max() < THRESHOLDS["sidm2c_profile_median_error_10Gyr"],
                  {"max": float(vals.max()) if len(vals) else None, "threshold": THRESHOLDS["sidm2c_profile_median_error_10Gyr"]})
        clock = c2.sidm2c_collapse_clock_error_frac.dropna()
        add(checks, "SIDM2c_collapse_clock_preferred", len(clock) > 0 and clock.max() < THRESHOLDS["sidm2c_collapse_clock_error_frac"],
            {"max": float(clock.max()) if len(clock) else None, "preferred": THRESHOLDS["sidm2c_collapse_clock_error_frac"]}, fatal=False)

    core = merged[merged.group_manifest.eq("core_blind_production")].copy()
    sx = core[core.branch_manifest.eq("SIDMx")]
    hl = core[core.branch_manifest.eq("HL_off")]
    s2v = core[core.branch_manifest.eq("SIDM2v")]

    sx_r23 = sx[sx.resolution_tier_manifest.isin(["R2_double","R3_gold"])]
    ok &= add(checks, "SIDMx_R2_R3_runs_present", len(sx_r23) >= 8, {"count": int(len(sx_r23))})
    if len(sx_r23):
        ok &= add(checks, "SIDMx_positive_deltaS_R2_R3", sx_r23.S_inner_10Gyr.mean() > THRESHOLDS["sidmx_min_positive_deltaS_R2_R3"],
                  {"mean": float(sx_r23.S_inner_10Gyr.mean())})
        ok &= add(checks, "SIDMx_H_in_L_out_R2_R3", sx_r23.H_in_L_out_score.mean() > 0,
                  {"mean": float(sx_r23.H_in_L_out_score.mean())})
        sx_sem = sem(sx_r23.S_inner_10Gyr)
        ok &= add(checks, "SIDMx_signal_beats_seed_noise", abs(sx_r23.S_inner_10Gyr.mean()) > sx_sem,
                  {"mean": float(sx_r23.S_inner_10Gyr.mean()), "sem": sx_sem})

    hl_r23 = hl[hl.resolution_tier_manifest.isin(["R2_double","R3_gold"])]
    if len(sx_r23) and len(hl_r23):
        sep = float(sx_r23.S_inner_10Gyr.mean() - hl_r23.S_inner_10Gyr.mean())
        ok &= add(checks, "HL_off_mimic_rejection", sep > THRESHOLDS["hl_off_mimic_margin"],
                  {"SIDMx_mean": float(sx_r23.S_inner_10Gyr.mean()), "HL_off_mean": float(hl_r23.S_inner_10Gyr.mean()), "separation": sep})

    s2v_r2 = s2v[s2v.resolution_tier_manifest.eq("R2_double")].S_inner_10Gyr
    s2v_r3 = s2v[s2v.resolution_tier_manifest.eq("R3_gold")].S_inner_10Gyr
    if len(s2v_r2) and len(s2v_r3):
        diff = abs(float(s2v_r3.mean() - s2v_r2.mean()))
        ok &= add(checks, "SIDM2v_R2_R3_scalar_convergence_proxy", diff < THRESHOLDS["sidm2v_resolution_profile_delta_max"],
                  {"R2_mean": float(s2v_r2.mean()), "R3_mean": float(s2v_r3.mean()), "abs_diff": diff,
                   "threshold": THRESHOLDS["sidm2v_resolution_profile_delta_max"]})

    ok &= add(checks, "executable_fingerprint_present", out.executable_sha256.astype(str).str.len().min() >= 32,
              {"unique_executable_hashes": int(out.executable_sha256.nunique())}, fatal=True)
    ok &= add(checks, "analysis_fingerprint_present", out.analysis_sha256.astype(str).str.len().min() >= 32,
              {"unique_analysis_hashes": int(out.analysis_sha256.nunique())}, fatal=True)
    ok &= add(checks, "output_fingerprint_present", out.output_sha256.astype(str).str.len().min() >= 32,
              {"unique_output_hashes": int(out.output_sha256.nunique())}, fatal=True)

    return ok, checks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-summary", required=True)
    ap.add_argument("--expected-manifest-sha", default=None)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    ok, checks = validate(args.manifest, args.run_summary, args.expected_manifest_sha)
    result = {"status": "PASS" if ok else "FAIL", "checks": checks}
    txt = json.dumps(result, indent=2)
    print(txt)
    if args.out_json:
        Path(args.out_json).write_text(txt + "\n")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
