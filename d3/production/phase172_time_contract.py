#!/usr/bin/env python3
"""Phase 172 production time/output contract.

This is a fail-closed contract gate, not a physics result. It validates that the
frozen production manifest requests the full 80 Gyr campaign and, when output
artifacts are supplied, that every run actually reached the manifest endpoint
and contains profile samples at every preregistered analysis time.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

EXPECTED_ANALYSIS_TIMES_GYR = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0)
TIME_TOL_GYR = 1.0e-6
EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"

RUN_REQUIRED = {
    "run_id", "branch", "group", "resolution_tier", "seed", "status", "final_time_Gyr"
}
PROFILE_REQUIRED = {
    "run_id", "time_Gyr", "r_mid_over_rs", "r_lo_over_rs", "r_hi_over_rs",
    "species", "rho", "rho_initial", "rho_rel", "sigma2", "beta", "mass_enclosed"
}
COLLISION_REQUIRED = {
    "run_id", "channel", "collision_count", "mean_sigma_factor", "mean_mu",
    "max_pair_dP_over_P", "max_pair_dK_over_K", "prob_clip_fraction_max"
}


def parse_times(text: str) -> tuple[float, ...]:
    vals = tuple(float(x.strip()) for x in str(text).split(",") if x.strip())
    if not vals:
        raise ValueError("empty analysis_times_Gyr")
    return vals


def close(a: float, b: float, tol: float = TIME_TOL_GYR) -> bool:
    return math.isfinite(a) and abs(a - b) <= tol


def add(checks, name, passed, detail):
    checks.append({"gate": name, "passed": bool(passed), "detail": detail})
    return bool(passed)


def load_csv(path: Path):
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def validate_manifest(path: Path, checks):
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    fields, rows = load_csv(path)
    ok = True

    ok &= add(checks, "manifest_sha256_frozen", sha == EXPECTED_MANIFEST_SHA256,
              {"observed": sha, "expected": EXPECTED_MANIFEST_SHA256})
    ok &= add(checks, "manifest_has_analysis_times_Gyr", "analysis_times_Gyr" in fields, {})
    if "analysis_times_Gyr" not in fields:
        return False, rows, sha

    bad = []
    for r in rows:
        try:
            times = parse_times(r["analysis_times_Gyr"])
        except Exception as exc:
            bad.append({"run_id": r.get("run_id"), "error": str(exc)})
            continue
        exact = len(times) == len(EXPECTED_ANALYSIS_TIMES_GYR) and all(
            close(a, b) for a, b in zip(times, EXPECTED_ANALYSIS_TIMES_GYR)
        )
        monotonic = all(b > a for a, b in zip(times, times[1:]))
        if not exact or not monotonic or not close(times[-1], 80.0):
            bad.append({"run_id": r.get("run_id"), "times": list(times)})
    ok &= add(checks, "every_run_uses_frozen_0_to_80Gyr_schedule", not bad,
              {"bad_count": len(bad), "bad_sample": bad[:5],
               "required": list(EXPECTED_ANALYSIS_TIMES_GYR)})
    return ok, rows, sha


def validate_outputs(manifest_rows, run_path: Path, profile_path: Path, collision_path: Path, checks):
    ok = True
    run_fields, run_rows = load_csv(run_path)
    profile_fields, profile_rows = load_csv(profile_path)
    collision_fields, collision_rows = load_csv(collision_path)

    missing_run = sorted(RUN_REQUIRED - set(run_fields))
    missing_prof = sorted(PROFILE_REQUIRED - set(profile_fields))
    missing_col = sorted(COLLISION_REQUIRED - set(collision_fields))
    ok &= add(checks, "run_summary_schema", not missing_run, {"missing": missing_run})
    ok &= add(checks, "profiles_schema", not missing_prof, {"missing": missing_prof})
    ok &= add(checks, "collision_summary_schema", not missing_col, {"missing": missing_col})
    if missing_run or missing_prof or missing_col:
        return False

    man = {str(r["run_id"]): r for r in manifest_rows}
    out = {str(r["run_id"]): r for r in run_rows}
    ok &= add(checks, "one_run_summary_row_per_run", len(out) == len(run_rows),
              {"rows": len(run_rows), "unique_run_ids": len(out)})
    ok &= add(checks, "run_summary_exact_manifest_ids", set(out) == set(man),
              {"missing": sorted(set(man) - set(out))[:10], "extra": sorted(set(out) - set(man))[:10]})

    incomplete = []
    short = []
    for rid, mr in man.items():
        rr = out.get(rid)
        if rr is None:
            continue
        if str(rr["status"]).strip().upper() != "COMPLETE":
            incomplete.append(rid)
        required_final = max(parse_times(mr["analysis_times_Gyr"]))
        try:
            got_final = float(rr["final_time_Gyr"])
        except Exception:
            got_final = float("nan")
        if not math.isfinite(got_final) or got_final + TIME_TOL_GYR < required_final:
            short.append({"run_id": rid, "observed": got_final, "required": required_final})
    ok &= add(checks, "all_runs_complete", not incomplete,
              {"bad_count": len(incomplete), "bad_sample": incomplete[:10]})
    ok &= add(checks, "every_run_reaches_manifest_endpoint_80Gyr", not short,
              {"bad_count": len(short), "bad_sample": short[:10]})

    profile_times = defaultdict(list)
    profile_species = defaultdict(set)
    for r in profile_rows:
        rid = str(r["run_id"])
        try:
            t = float(r["time_Gyr"])
        except Exception:
            continue
        profile_times[rid].append(t)
        profile_species[(rid, t)].add(str(r["species"]).strip().lower())

    missing_times = []
    missing_species = []
    required_species = {"h", "l", "total"}
    for rid, mr in man.items():
        observed = profile_times.get(rid, [])
        for req in parse_times(mr["analysis_times_Gyr"]):
            matches = [t for t in observed if close(t, req)]
            if not matches:
                missing_times.append({"run_id": rid, "time_Gyr": req})
                continue
            t0 = min(matches, key=lambda t: abs(t - req))
            species = profile_species[(rid, t0)]
            if not required_species <= species:
                missing_species.append({"run_id": rid, "time_Gyr": req,
                                        "observed": sorted(species),
                                        "required": sorted(required_species)})
    ok &= add(checks, "profiles_cover_every_preregistered_time_including_55.28_and_80Gyr",
              not missing_times,
              {"bad_count": len(missing_times), "bad_sample": missing_times[:10]})
    ok &= add(checks, "profiles_have_H_L_total_at_every_required_time", not missing_species,
              {"bad_count": len(missing_species), "bad_sample": missing_species[:10]})

    collision_ids = {str(r["run_id"]) for r in collision_rows}
    ok &= add(checks, "collision_summary_represents_every_manifest_run",
              set(man) <= collision_ids,
              {"missing": sorted(set(man) - collision_ids)[:10],
               "missing_count": len(set(man) - collision_ids)})
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-summary")
    ap.add_argument("--profiles")
    ap.add_argument("--collision-summary")
    ap.add_argument("--manifest-only", action="store_true")
    ap.add_argument("--out-json")
    args = ap.parse_args()

    checks = []
    manifest_path = Path(args.manifest)
    ok, rows, sha = validate_manifest(manifest_path, checks)

    supplied = [args.run_summary, args.profiles, args.collision_summary]
    if args.manifest_only:
        if any(supplied):
            ok &= add(checks, "manifest_only_has_no_output_args", False,
                      {"detail": "remove output arguments when using --manifest-only"})
    else:
        if not all(supplied):
            ok &= add(checks, "all_output_artifacts_required", False,
                      {"required": ["--run-summary", "--profiles", "--collision-summary"]})
        elif ok:
            ok &= validate_outputs(rows, Path(args.run_summary), Path(args.profiles),
                                   Path(args.collision_summary), checks)

    result = {"status": "PASS" if ok else "FAIL", "manifest_sha256": sha, "checks": checks}
    text = json.dumps(result, indent=2)
    print(text)
    if args.out_json:
        Path(args.out_json).write_text(text + "\n")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
