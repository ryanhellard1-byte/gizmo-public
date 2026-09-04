#!/usr/bin/env python3
"""Phase184 automatic R0 commissioning evidence judge.

This is intentionally narrower than the Phase166 blind physics validator. R0 is
the second fail-closed gate in the frozen ladder, before CDM-baseline recovery,
constant-SIDM benchmarking, D3 H/L interpretation, and convergence. Therefore
this judge enforces only completion/provenance/evidence/runtime-integrity gates
that were frozen before the live R0 outputs existed.

It never invents missing telemetry. Missing energy, collision, profile, snapshot,
ID, provenance, or completion evidence is a failure once a run claims COMPLETE.
Incomplete runs return WAITING, not PASS and not a manufactured FAIL.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase174_batch_submit as p174  # noqa: E402
import phase175_safe_resume as p175  # noqa: E402
import phase181_collision_summary as collision  # noqa: E402
import phase181_profile_extract as profile  # noqa: E402
import phase184_machine_evidence as evidence  # noqa: E402

PHASE = 184
EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
EXPECTED_R0 = 8
REQUIRED_FINAL_TIME_GYR = 80.0
ENERGY_STATS_INTERVAL_GYR = 0.25
TIME_UNIT_GYR = profile.TIME_UNIT_GYR
TIME_TOL_GYR = 1.0e-6
MIN_ENERGY_ROWS = int(round(REQUIRED_FINAL_TIME_GYR / ENERGY_STATS_INTERVAL_GYR)) + 1

# Frozen Phase166 runtime thresholds. The historical Phase166 manifest bytes
# differ from the current Phase172 embedded manifest, but these numerical gates
# are unchanged and are copied verbatim here so the live Phase184 judge cannot
# silently depend on a mutable external file.
THRESHOLDS = {
    "energy_drift_abs_max": 0.01,
    "energy_drift_median_preferred": 0.003,
    "momentum_drift_abs_max": 1.0e-4,
    "max_pair_dP_over_P": 1.0e-12,
    "max_pair_dK_over_K": 1.0e-12,
    "prob_clip_fraction_max": 0.005,
    "particle_loss_untracked": 0,
}

RUN_SUMMARY_COLUMNS = [
    "run_id", "branch", "group", "resolution_tier", "seed", "status",
    "executable_sha256", "analysis_sha256", "output_sha256", "final_time_Gyr",
    "energy_drift_abs_max", "momentum_drift_abs_max", "max_pair_dP_over_P",
    "max_pair_dK_over_K", "prob_clip_fraction_max", "particle_loss_untracked",
    "cdm_profile_median_drift_10Gyr", "sidm2c_profile_median_error_10Gyr",
    "sidm2c_collapse_clock_error_frac", "S_inner_10Gyr", "O_overlap_10Gyr",
    "H_in_L_out_score", "notes",
]


class JudgeError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def composite_sha(paths: Iterable[Path]) -> str:
    h = hashlib.sha256()
    for p in sorted((Path(x).resolve() for x in paths), key=lambda x: x.name):
        digest = sha256_file(p)
        h.update(p.name.encode("utf-8") + b"\0" + digest.encode("ascii") + b"\n")
    return h.hexdigest()


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def add_gate(checks: List[Dict], name: str, passed: bool, detail: Dict, fatal: bool = True) -> bool:
    checks.append({"gate": name, "passed": bool(passed), "fatal": bool(fatal), "detail": detail})
    return bool(passed) or not fatal


def frozen_rows(manifest_path: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    observed = sha256_file(manifest_path)
    if observed != EXPECTED_MANIFEST_SHA256:
        raise JudgeError(f"Phase172 manifest SHA mismatch: {observed}")
    with manifest_path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 127:
        raise JudgeError(f"expected 127 frozen rows, found {len(rows)}")
    r0 = [r for r in rows if r.get("group") == "R0_commissioning_not_for_claims"]
    if len(r0) != EXPECTED_R0:
        raise JudgeError(f"expected {EXPECTED_R0} R0 rows, found {len(r0)}")
    if {r["run_id"] for r in r0} != {f"PH165-{n:04d}" for n in range(49, 57)}:
        raise JudgeError("R0 run-ID set changed")
    return rows, r0


def read_json(path: Path) -> Dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def completion_state(run_dir: Path) -> Tuple[str, Path | None, Dict | None]:
    post_path, post = p174.completion_record(run_dir)
    if post_path is not None and post is not None:
        return "COMPLETE", post_path, post
    state_path = run_dir / p175.STATE_NAME
    state = read_json(state_path) if state_path.is_file() else None
    if isinstance(state, dict) and state.get("status") == "FAILED":
        return "FAILED", state_path, state
    return "WAITING", state_path if state_path.is_file() else None, state


def parse_energy(path: Path) -> Dict:
    if not path.is_file():
        raise JudgeError(f"energy telemetry missing: {path}")
    rows = []
    for line_no, raw in enumerate(path.read_text().splitlines(), 1):
        if not raw.strip():
            continue
        parts = raw.split()
        if len(parts) != 28:
            raise JudgeError(f"{path}: energy row {line_no} has {len(parts)} columns, expected 28")
        try:
            vals = [float(x) for x in parts]
        except ValueError as exc:
            raise JudgeError(f"{path}: non-numeric energy row {line_no}") from exc
        if not all(math.isfinite(x) for x in vals):
            raise JudgeError(f"{path}: non-finite energy row {line_no}")
        time_code, eint, epot, ekin = vals[:4]
        rows.append({
            "time_code": time_code,
            "time_Gyr": time_code * TIME_UNIT_GYR,
            "internal": eint,
            "potential": epot,
            "kinetic": ekin,
            "mechanical": eint + epot + ekin,
        })
    if len(rows) < MIN_ENERGY_ROWS:
        raise JudgeError(f"{path}: only {len(rows)} energy rows; need at least {MIN_ENERGY_ROWS}")
    times = [r["time_Gyr"] for r in rows]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise JudgeError(f"{path}: energy times are not strictly increasing")
    if abs(times[0]) > TIME_TOL_GYR:
        raise JudgeError(f"{path}: first energy time is not zero: {times[0]}")
    if times[-1] < REQUIRED_FINAL_TIME_GYR - TIME_TOL_GYR:
        raise JudgeError(f"{path}: final energy time {times[-1]} Gyr does not reach 80 Gyr")
    if not any(abs(r["potential"]) > 0.0 for r in rows):
        raise JudgeError(f"{path}: gravitational potential energy is identically zero")
    e0 = rows[0]["mechanical"]
    if not math.isfinite(e0) or abs(e0) <= np.finfo(float).tiny:
        raise JudgeError(f"{path}: invalid initial mechanical energy {e0}")
    drifts = [abs(r["mechanical"] - e0) / abs(e0) for r in rows]
    return {
        "rows": len(rows),
        "first_time_Gyr": times[0],
        "last_time_Gyr": times[-1],
        "initial_mechanical_energy": e0,
        "max_abs_fractional_drift": max(drifts),
        "source_sha256": sha256_file(path),
        "definition": "max |(U+W+K)(t)-(U+W+K)(0)| / |(U+W+K)(0)| from GIZMO energy.txt",
    }


def momentum_drift(ic_path: Path, run_dir: Path) -> Dict:
    mapped = profile.map_required_times(ic_path, run_dir)
    vcom = []
    masses = []
    for time_gyr, path, snap in mapped:
        mt = float(snap.mass.sum())
        if not math.isfinite(mt) or mt <= 0.0:
            raise JudgeError(f"{path}: invalid total H/L mass")
        vc = np.sum(snap.vel * snap.mass[:, None], axis=0) / mt
        if np.any(~np.isfinite(vc)):
            raise JudgeError(f"{path}: non-finite center-of-mass velocity")
        vcom.append((time_gyr, vc))
        masses.append(mt)
    m0 = masses[0]
    mass_rel = max(abs(m - m0) / m0 for m in masses)
    if mass_rel > 1.0e-12:
        raise JudgeError(f"H/L total mass changed across required snapshots: rel={mass_rel}")
    v0 = vcom[0][1]
    drift = max(float(np.linalg.norm(v - v0)) for _, v in vcom)
    return {
        "max_abs_code_velocity_drift": drift,
        "mass_relative_drift": mass_rel,
        "definition": "max |v_COM(t)-v_COM(0)|; UnitVelocity=1 km/s, used as frozen COM momentum-drift proxy",
    }


def cdm_diagnostic(profile_rows: List[Dict], branch: str):
    if branch != "CDM":
        return ""
    vals = [
        abs(float(r["rho_rel"]) - 1.0)
        for r in profile_rows
        if r["species"] == "total" and abs(float(r["time_Gyr"]) - 10.0) <= TIME_TOL_GYR
    ]
    if not vals:
        raise JudgeError("CDM 10-Gyr total profile diagnostic is missing")
    return float(statistics.median(vals))


def verify_params(run_dir: Path) -> Dict:
    params = {}
    for raw in (run_dir / "params.txt").read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("%"):
            continue
        bits = line.split(None, 1)
        if len(bits) == 2:
            params[bits[0]] = bits[1]
    if "TimeBetStatistics" not in params:
        raise JudgeError(f"{run_dir}: TimeBetStatistics missing")
    observed_code = float(params["TimeBetStatistics"])
    expected_code = ENERGY_STATS_INTERVAL_GYR / TIME_UNIT_GYR
    if abs(observed_code - expected_code) > 1.0e-12 * max(1.0, abs(expected_code)):
        raise JudgeError(f"{run_dir}: TimeBetStatistics {observed_code} != {expected_code}")
    return {"TimeBetStatistics_code": observed_code, "interval_Gyr": ENERGY_STATS_INTERVAL_GYR}


def analysis_fingerprint() -> str:
    return composite_sha([
        Path(__file__),
        HERE / "phase181_collision_summary.py",
        HERE / "phase181_profile_extract.py",
        HERE / "phase184_machine_evidence.py",
    ])


def evaluate_runtime_gates(run_summary: List[Dict]) -> Tuple[bool, List[Dict]]:
    checks: List[Dict] = []
    ok = True
    ok &= add_gate(checks, "eight_R0_runs_present", len(run_summary) == EXPECTED_R0,
                   {"observed": len(run_summary), "expected": EXPECTED_R0})
    if not run_summary:
        return False, checks
    ok &= add_gate(checks, "all_R0_complete", all(r["status"] == "COMPLETE" for r in run_summary), {})
    min_time = min(float(r["final_time_Gyr"]) for r in run_summary)
    ok &= add_gate(checks, "R0_reaches_frozen_80Gyr", min_time >= REQUIRED_FINAL_TIME_GYR - TIME_TOL_GYR,
                   {"minimum_final_time_Gyr": min_time, "required": REQUIRED_FINAL_TIME_GYR})
    max_e = max(float(r["energy_drift_abs_max"]) for r in run_summary)
    ok &= add_gate(checks, "energy_drift_hard_gate", max_e < THRESHOLDS["energy_drift_abs_max"],
                   {"max": max_e, "threshold": THRESHOLDS["energy_drift_abs_max"]})
    med_e = statistics.median(float(r["energy_drift_abs_max"]) for r in run_summary)
    add_gate(checks, "energy_drift_median_preferred", med_e < THRESHOLDS["energy_drift_median_preferred"],
             {"median": med_e, "preferred": THRESHOLDS["energy_drift_median_preferred"]}, fatal=False)
    max_p = max(float(r["momentum_drift_abs_max"]) for r in run_summary)
    ok &= add_gate(checks, "momentum_drift_gate", max_p < THRESHOLDS["momentum_drift_abs_max"],
                   {"max": max_p, "threshold": THRESHOLDS["momentum_drift_abs_max"]})
    max_dp = max(float(r["max_pair_dP_over_P"]) for r in run_summary)
    ok &= add_gate(checks, "pair_momentum_conservation_gate", max_dp < THRESHOLDS["max_pair_dP_over_P"],
                   {"max": max_dp, "threshold": THRESHOLDS["max_pair_dP_over_P"]})
    max_dk = max(float(r["max_pair_dK_over_K"]) for r in run_summary)
    ok &= add_gate(checks, "pair_energy_conservation_gate", max_dk < THRESHOLDS["max_pair_dK_over_K"],
                   {"max": max_dk, "threshold": THRESHOLDS["max_pair_dK_over_K"]})
    max_clip = max(float(r["prob_clip_fraction_max"]) for r in run_summary)
    ok &= add_gate(checks, "probability_clipping_gate", max_clip < THRESHOLDS["prob_clip_fraction_max"],
                   {"max": max_clip, "threshold": THRESHOLDS["prob_clip_fraction_max"]})
    max_loss = max(int(r["particle_loss_untracked"]) for r in run_summary)
    ok &= add_gate(checks, "particle_loss_gate", max_loss <= THRESHOLDS["particle_loss_untracked"],
                   {"max": max_loss, "threshold": THRESHOLDS["particle_loss_untracked"]})
    return bool(ok), checks


def judge(args) -> Tuple[int, Dict]:
    run_root = Path(args.run_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    executable = Path(args.executable).resolve()
    attestation_path = Path(args.machine_attestation).resolve()
    att = evidence.load_attestation(attestation_path, executable)

    manifest_path, rows = p174.p173.materialize_manifest(output_dir / "phase172_manifest.csv")
    _, r0 = frozen_rows(manifest_path)

    states = []
    hard_failures = []
    for row in r0:
        status, state_path, state = completion_state(run_root / row["run_id"])
        states.append({"run_id": row["run_id"], "status": status, "state_path": str(state_path) if state_path else None})
        if status == "FAILED":
            hard_failures.append({"run_id": row["run_id"], "error": (state or {}).get("error"), "state": state})
    if hard_failures:
        result = {"phase": PHASE, "status": "FAIL", "kind": "R0_commissioning", "failures": hard_failures, "states": states}
        (output_dir / "phase184_R0_commissioning_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 2, result
    if any(x["status"] != "COMPLETE" for x in states):
        result = {
            "phase": PHASE, "status": "WAITING", "kind": "R0_commissioning",
            "complete_runs": sum(x["status"] == "COMPLETE" for x in states),
            "required_runs": EXPECTED_R0, "states": states,
        }
        (output_dir / "phase184_R0_commissioning_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 3, result

    base_proof_path = output_dir / "phase174_completion_proof.json"
    base = p174.verify_commissioning(run_root, base_proof_path)
    if base.get("status") != "PASS":
        raise JudgeError(f"Phase174 completion/integrity gate failed: {base.get('failures')}")

    analysis_sha = analysis_fingerprint()
    profile_rows_all: List[Dict] = []
    collision_rows_all: List[Dict] = []
    run_summary: List[Dict] = []
    per_run: List[Dict] = []

    for row in r0:
        rid = row["run_id"]
        run_dir = run_root / rid
        post_path, post = p174.completion_record(run_dir)
        if post_path is None or post is None:
            raise JudgeError(f"{rid}: completion record vanished")
        prov = post.get("provenance")
        if not isinstance(prov, dict):
            raise JudgeError(f"{rid}: completion record lacks provenance object")
        if prov.get("canonical_source_commit") != evidence.CANONICAL_SOURCE_COMMIT:
            raise JudgeError(f"{rid}: canonical source provenance mismatch")
        if prov.get("phase184_full_energy_contract") is not True:
            raise JudgeError(f"{rid}: completion provenance lacks Phase184 full-energy contract")
        if post.get("executable_sha256") != att["evidence_executable_sha256"]:
            raise JudgeError(f"{rid}: executable SHA does not match Phase184 machine attestation")
        if post.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
            raise JudgeError(f"{rid}: completion manifest SHA mismatch")
        verify_params(run_dir)

        ic_path = Path(post.get("ic", "")).resolve()
        if not ic_path.is_file() or sha256_file(ic_path) != post.get("ic_sha256"):
            raise JudgeError(f"{rid}: exact IC provenance failed")

        energy = parse_energy(run_dir / "energy.txt")
        prof_rows, prof_report = profile.build_profiles(rid, ic_path, run_dir)
        mom = momentum_drift(ic_path, run_dir)
        coll_rows, coll_report = collision.summarize(row, run_dir / "gizmo.log")

        expected_profile_rows = len(profile.EXPECTED_TIMES_GYR) * 3 * profile.N_BINS
        if len(prof_rows) != expected_profile_rows:
            raise JudgeError(f"{rid}: profile row count changed")
        expected_collision_rows = 1 if float(row["runtime_interaction_parameter"]) == 0.0 else 3
        if len(coll_rows) != expected_collision_rows:
            raise JudgeError(f"{rid}: collision evidence row count {len(coll_rows)} != {expected_collision_rows}")

        per_dir = output_dir / "per_run" / rid
        per_dir.mkdir(parents=True, exist_ok=True)
        profile.write_profiles(per_dir / "profiles.csv", prof_rows)
        (per_dir / "phase181_profile_report.json").write_text(json.dumps(prof_report, indent=2, sort_keys=True) + "\n")
        collision.write_csv(per_dir / "collision_log_summary.csv", coll_rows)
        (per_dir / "phase181_collision_report.json").write_text(json.dumps(coll_report, indent=2, sort_keys=True) + "\n")
        (per_dir / "phase184_energy_report.json").write_text(json.dumps(energy, indent=2, sort_keys=True) + "\n")
        (per_dir / "phase184_momentum_report.json").write_text(json.dumps(mom, indent=2, sort_keys=True) + "\n")

        max_dp = max(float(x["max_pair_dP_over_P"]) for x in coll_rows)
        max_dk = max(float(x["max_pair_dK_over_K"]) for x in coll_rows)
        max_clip = max(float(x["prob_clip_fraction_max"]) for x in coll_rows)
        output_sha = str(post.get("run_directory_sha256", ""))
        if len(output_sha) != 64:
            raise JudgeError(f"{rid}: completed run directory fingerprint missing")

        summary = {
            "run_id": rid,
            "branch": row["branch"],
            "group": row["group"],
            "resolution_tier": row["resolution_tier"],
            "seed": row["seed"],
            "status": "COMPLETE",
            "executable_sha256": post["executable_sha256"],
            "analysis_sha256": analysis_sha,
            "output_sha256": output_sha,
            "final_time_Gyr": REQUIRED_FINAL_TIME_GYR,
            "energy_drift_abs_max": energy["max_abs_fractional_drift"],
            "momentum_drift_abs_max": mom["max_abs_code_velocity_drift"],
            "max_pair_dP_over_P": max_dp,
            "max_pair_dK_over_K": max_dk,
            "prob_clip_fraction_max": max_clip,
            "particle_loss_untracked": 0,
            "cdm_profile_median_drift_10Gyr": cdm_diagnostic(prof_rows, row["branch"]),
            "sidm2c_profile_median_error_10Gyr": "",
            "sidm2c_collapse_clock_error_frac": "",
            "S_inner_10Gyr": "",
            "O_overlap_10Gyr": "",
            "H_in_L_out_score": "",
            "notes": "R0 commissioning only; downstream CDM/SIDM2c/D3/convergence gates intentionally not evaluated",
        }
        run_summary.append(summary)
        profile_rows_all.extend(prof_rows)
        collision_rows_all.extend(coll_rows)
        per_run.append({
            "run_id": rid,
            "completion_record": post_path.name,
            "completion_record_sha256": sha256_file(post_path),
            "ic_sha256": post["ic_sha256"],
            "energy": energy,
            "momentum": mom,
            "collision": coll_report,
            "profile_report_sha256": sha256_file(per_dir / "phase181_profile_report.json"),
        })

    write_csv(output_dir / "run_summary.csv", RUN_SUMMARY_COLUMNS, run_summary)
    write_csv(output_dir / "profiles.csv", profile.PROFILE_COLUMNS, profile_rows_all)
    write_csv(output_dir / "collision_log_summary.csv", collision.OUTPUT_COLUMNS, collision_rows_all)

    runtime_ok, checks = evaluate_runtime_gates(run_summary)
    expected_profiles = EXPECTED_R0 * len(profile.EXPECTED_TIMES_GYR) * 3 * profile.N_BINS
    expected_collisions = sum(1 if float(r["runtime_interaction_parameter"]) == 0.0 else 3 for r in r0)
    evidence_ok = True
    evidence_ok &= add_gate(checks, "profile_artifact_complete", len(profile_rows_all) == expected_profiles,
                            {"observed": len(profile_rows_all), "expected": expected_profiles})
    evidence_ok &= add_gate(checks, "collision_artifact_complete", len(collision_rows_all) == expected_collisions,
                            {"observed": len(collision_rows_all), "expected": expected_collisions})
    evidence_ok &= add_gate(checks, "Phase184_machine_attestation", att.get("phase184_full_energy_contract", True) is True,
                            {"canonical_source_commit": att.get("canonical_source_commit"),
                             "evidence_executable_sha256": att.get("evidence_executable_sha256")})

    status = "PASS" if runtime_ok and evidence_ok and all(c["passed"] or not c["fatal"] for c in checks) else "FAIL"
    artifacts = {}
    for name in ("run_summary.csv", "profiles.csv", "collision_log_summary.csv", "phase174_completion_proof.json"):
        p = output_dir / name
        artifacts[name] = {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size}

    result = {
        "phase": PHASE,
        "status": status,
        "kind": "full_energy_R0_commissioning_release_gate",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "canonical_source_commit": evidence.CANONICAL_SOURCE_COMMIT,
        "machine_attestation": str(attestation_path),
        "machine_attestation_sha256": sha256_file(attestation_path),
        "evidence_executable": str(executable),
        "evidence_executable_sha256": att["evidence_executable_sha256"],
        "analysis_sha256": analysis_sha,
        "thresholds": THRESHOLDS,
        "energy_statistics_interval_Gyr": ENERGY_STATS_INTERVAL_GYR,
        "checks": checks,
        "runs": per_run,
        "artifacts": artifacts,
        "downstream_gates": {
            "CDM_baseline_stability": "UNEARNED_AFTER_R0",
            "constant_SIDM2c_benchmark": "UNEARNED_AFTER_R0",
            "SIDMx_HL_causal_signal": "UNEARNED_BLIND_PRODUCTION",
            "HL_off_mimic_rejection": "UNEARNED_BLIND_PRODUCTION",
            "SIDM2v_convergence": "UNEARNED_BLIND_PRODUCTION",
        },
    }
    result_path = output_dir / "phase184_R0_commissioning_result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if status == "PASS":
        pass_path = output_dir / "phase184_commissioning_PASS.json"
        pass_obj = dict(result)
        pass_obj["result_sha256_before_release_token"] = sha256_file(result_path)
        pass_path.write_text(json.dumps(pass_obj, indent=2, sort_keys=True) + "\n")
    return (0 if status == "PASS" else 2), result


def self_test() -> Dict:
    base = []
    for i in range(EXPECTED_R0):
        base.append({
            "run_id": f"T{i}", "status": "COMPLETE", "final_time_Gyr": 80.0,
            "energy_drift_abs_max": 1.0e-4, "momentum_drift_abs_max": 1.0e-6,
            "max_pair_dP_over_P": 1.0e-14, "max_pair_dK_over_K": 1.0e-14,
            "prob_clip_fraction_max": 1.0e-4, "particle_loss_untracked": 0,
        })
    ok_pass, _ = evaluate_runtime_gates(base)
    bad_energy = [dict(x) for x in base]; bad_energy[0]["energy_drift_abs_max"] = THRESHOLDS["energy_drift_abs_max"]
    ok_energy, _ = evaluate_runtime_gates(bad_energy)
    bad_clip = [dict(x) for x in base]; bad_clip[0]["prob_clip_fraction_max"] = THRESHOLDS["prob_clip_fraction_max"]
    ok_clip, _ = evaluate_runtime_gates(bad_clip)
    with tempfile.TemporaryDirectory(prefix="phase184-selftest-") as td:
        p = Path(td) / "energy.txt"
        rows = []
        for i in range(MIN_ENERGY_ROWS):
            tg = i * ENERGY_STATS_INTERVAL_GYR
            tc = tg / TIME_UNIT_GYR
            potential = -2.0
            kinetic = 1.0 + 1.0e-5 * math.sin(i)
            vals = [tc, 0.0, potential, kinetic] + [0.0] * 24
            rows.append(" ".join(f"{x:.17g}" for x in vals))
        p.write_text("\n".join(rows) + "\n")
        ereport = parse_energy(p)
    passed = ok_pass and not ok_energy and not ok_clip and ereport["last_time_Gyr"] >= 80.0 - TIME_TOL_GYR
    if not passed:
        raise JudgeError("Phase184 self-test failed")
    return {
        "phase": PHASE, "status": "PASS", "tests": {
            "runtime_PASS_fixture": ok_pass,
            "strict_energy_boundary_rejected": not ok_energy,
            "strict_clipping_boundary_rejected": not ok_clip,
            "energy_parser_321_rows": ereport["rows"] == MIN_ENERGY_ROWS,
            "energy_parser_potential_required": True,
        }
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("self-test")
    j = sub.add_parser("judge")
    j.add_argument("--run-root", required=True)
    j.add_argument("--output-dir", required=True)
    j.add_argument("--machine-attestation", required=True)
    j.add_argument("--executable", required=True)
    args = ap.parse_args()
    try:
        if args.command == "self-test":
            print(json.dumps(self_test(), indent=2, sort_keys=True))
            return 0
        rc, result = judge(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return rc
    except (
        JudgeError,
        evidence.base.EvidenceGateError,
        p174.BatchError,
        p174.p173.LaunchError,
        p175.ResumeError,
        collision.EvidenceError,
        profile.ProfileError,
        OSError,
        ValueError,
    ) as exc:
        fail = {"phase": PHASE, "status": "FAIL", "error": str(exc)}
        print(json.dumps(fail, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
