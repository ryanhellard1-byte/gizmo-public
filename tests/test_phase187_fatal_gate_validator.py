#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase187_fatal_gate_validator.py"
spec = importlib.util.spec_from_file_location("p187", MOD_PATH)
p187 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(p187)

MAN_FIELDS = ["run_id", "branch", "group", "resolution_tier", "seed"]
EV_FIELDS = list(p187.REQUIRED_COLUMNS)


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)


def fixtures(tmp: Path):
    manifest = []
    evidence = []
    rid = 0
    for tier in ("R2_double", "R3_gold"):
        for seed_i, seed in enumerate((101, 102, 103, 104)):
            for branch in ("CDM", "SIDMx", "HL_off", "SIDM2v"):
                rid += 1
                run_id = f"T{rid:03d}"
                m = {
                    "run_id": run_id,
                    "branch": branch,
                    "group": "core_blind_production",
                    "resolution_tier": tier,
                    "seed": str(seed),
                }
                manifest.append(m)
                base = 0.002 * seed_i
                sval = {
                    "CDM": base,
                    "SIDMx": 0.20 + base,
                    "HL_off": 0.05 + base,
                    "SIDM2v": 0.15 + base + (0.001 if tier == "R3_gold" else 0.0),
                }[branch]
                evidence.append({
                    **m,
                    "status": "COMPLETE",
                    "energy_drift_abs_max": "0.001",
                    "momentum_drift_abs_max": "0.00001",
                    "cdm_profile_median_drift_10Gyr": "0.01" if branch == "CDM" else "",
                    "sidm2c_profile_median_error_10Gyr": "",
                    "sidm2c_collapse_clock_error_frac": "",
                    "S_inner_10Gyr": str(sval),
                    "O_overlap_10Gyr": "-0.02",
                    "H_in_L_out_score": "0.1" if branch == "SIDMx" else "0.0",
                    "analysis_sha256": "a" * 64,
                    "source_evidence_sha256": "b" * 64,
                })

    # Explicit non-claim commissioning CDM row. Its deliberately terrible
    # profile metric must not contaminate the claim-bearing CDM stability gate.
    rid += 1
    m = {
        "run_id": f"T{rid:03d}",
        "branch": "CDM",
        "group": "R0_commissioning_not_for_claims",
        "resolution_tier": "R0_pilot",
        "seed": "1",
    }
    manifest.append(m)
    evidence.append({
        **m,
        "status": "COMPLETE",
        "energy_drift_abs_max": "0.001",
        "momentum_drift_abs_max": "0.00001",
        "cdm_profile_median_drift_10Gyr": "0.99",
        "sidm2c_profile_median_error_10Gyr": "",
        "sidm2c_collapse_clock_error_frac": "",
        "S_inner_10Gyr": "0.0",
        "O_overlap_10Gyr": "0.0",
        "H_in_L_out_score": "0.0",
        "analysis_sha256": "a" * 64,
        "source_evidence_sha256": "b" * 64,
    })

    rid += 1
    m = {
        "run_id": f"T{rid:03d}",
        "branch": "SIDM2c_const",
        "group": "constant_SIDM2c_benchmark",
        "resolution_tier": "R2_double",
        "seed": "301",
    }
    manifest.append(m)
    evidence.append({
        **m,
        "status": "COMPLETE",
        "energy_drift_abs_max": "0.001",
        "momentum_drift_abs_max": "0.00001",
        "cdm_profile_median_drift_10Gyr": "",
        "sidm2c_profile_median_error_10Gyr": "0.05",
        "sidm2c_collapse_clock_error_frac": "0.10",
        "S_inner_10Gyr": "0.0",
        "O_overlap_10Gyr": "0.0",
        "H_in_L_out_score": "0.0",
        "analysis_sha256": "a" * 64,
        "source_evidence_sha256": "b" * 64,
    })

    man_path = tmp / "manifest.csv"
    ev_path = tmp / "scalar.csv"
    write_csv(man_path, MAN_FIELDS, manifest)
    write_csv(ev_path, EV_FIELDS, evidence)
    man_sha = hashlib.sha256(man_path.read_bytes()).hexdigest()
    return man_path, ev_path, man_sha, manifest, evidence


def run():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        man, ev, sha, manifest, evidence = fixtures(tmp)
        ok, checks = p187.validate(man, ev, expected_manifest_sha=sha)
        assert ok, [c for c in checks if c["fatal"] and not c["passed"]]
        assert next(c for c in checks if c["gate"] == "SIDM2v_seed_stability")["passed"]
        cdm_gate = next(c for c in checks if c["gate"] == "CDM_profile_stability")
        assert cdm_gate["passed"]
        assert "R0_commissioning_not_for_claims" in cdm_gate["detail"]["excluded_groups"]

        # Hard energy gate must fail closed.
        evidence_energy = [dict(r) for r in evidence]
        evidence_energy[0]["energy_drift_abs_max"] = "0.0100001"
        ev_energy = tmp / "scalar_energy_fail.csv"
        write_csv(ev_energy, EV_FIELDS, evidence_energy)
        ok_energy, checks_energy = p187.validate(man, ev_energy, expected_manifest_sha=sha)
        assert not ok_energy
        assert not next(c for c in checks_energy if c["gate"] == "energy_drift_hard_gate")["passed"]

        # P1 regression: R2 may not hide behind a large R3 signal. This fixture
        # makes R2 SIDMx negative in both S and the directional score while R3 is
        # extremely positive. The old pooled implementation could pass.
        evidence_tier = [dict(r) for r in evidence]
        for r in evidence_tier:
            if r["branch"] != "SIDMx" or r["group"] != "core_blind_production":
                continue
            if r["resolution_tier"] == "R2_double":
                r["S_inner_10Gyr"] = "-0.10"
                r["H_in_L_out_score"] = "-0.10"
            elif r["resolution_tier"] == "R3_gold":
                r["S_inner_10Gyr"] = "1.00"
                r["H_in_L_out_score"] = "1.00"
        ev_tier = tmp / "scalar_tier_pooling_attack.csv"
        write_csv(ev_tier, EV_FIELDS, evidence_tier)
        ok_tier, checks_tier = p187.validate(man, ev_tier, expected_manifest_sha=sha)
        assert not ok_tier
        assert not next(c for c in checks_tier if c["gate"] == "SIDMx_positive_deltaS_R2_R3")["passed"]
        assert not next(c for c in checks_tier if c["gate"] == "SIDMx_H_in_L_out_R2_R3")["passed"]

        # Kill the SIDM2v branch separation while leaving the rest intact.
        evidence_seed = [dict(r) for r in evidence]
        cdm_by_key = {
            (r["resolution_tier"], r["seed"]): r
            for r in evidence_seed
            if r["branch"] == "CDM" and r["group"] == "core_blind_production"
        }
        for r in evidence_seed:
            if r["branch"] == "SIDM2v" and r["group"] == "core_blind_production":
                r["S_inner_10Gyr"] = cdm_by_key[(r["resolution_tier"], r["seed"])]["S_inner_10Gyr"]
        ev_seed = tmp / "scalar_seed_fail.csv"
        write_csv(ev_seed, EV_FIELDS, evidence_seed)
        ok_seed, checks_seed = p187.validate(man, ev_seed, expected_manifest_sha=sha)
        assert not ok_seed
        seed_gate = next(c for c in checks_seed if c["gate"] == "SIDM2v_seed_stability")
        assert not seed_gate["passed"]
        assert all(not t["passed"] for t in seed_gate["detail"]["tiers"])

        # Regression for the Phase187 denominator repair. Four paired deltas
        # [0,0,2,2] have mean=1 and sample scatter~=1.1547, so separation is
        # smaller than seed scatter and MUST fail. The old SEM denominator
        # would have been ~=0.577 and would have incorrectly passed.
        evidence_noisy = [dict(r) for r in evidence]
        cdm_noisy = {
            (r["resolution_tier"], r["seed"]): r
            for r in evidence_noisy
            if r["branch"] == "CDM" and r["group"] == "core_blind_production"
        }
        delta_by_seed = {"101": 0.0, "102": 0.0, "103": 2.0, "104": 2.0}
        for r in evidence_noisy:
            if r["branch"] == "SIDM2v" and r["group"] == "core_blind_production":
                base = float(cdm_noisy[(r["resolution_tier"], r["seed"])]["S_inner_10Gyr"])
                r["S_inner_10Gyr"] = str(base + delta_by_seed[r["seed"]])
        ev_noisy = tmp / "scalar_seed_scatter_fail.csv"
        write_csv(ev_noisy, EV_FIELDS, evidence_noisy)
        ok_noisy, checks_noisy = p187.validate(man, ev_noisy, expected_manifest_sha=sha)
        assert not ok_noisy
        noisy_gate = next(c for c in checks_noisy if c["gate"] == "SIDM2v_seed_stability")
        assert not noisy_gate["passed"]
        for tier in noisy_gate["detail"]["tiers"]:
            assert tier["seed_scatter_std_delta_S"] > abs(tier["mean_delta_S"])
            assert tier["branch_separation_sigma"] < 1.0

        # Metadata or run-coverage tampering must also fail.
        evidence_missing = evidence[:-1]
        ev_missing = tmp / "scalar_missing.csv"
        write_csv(ev_missing, EV_FIELDS, evidence_missing)
        ok_missing, checks_missing = p187.validate(man, ev_missing, expected_manifest_sha=sha)
        assert not ok_missing
        assert not next(c for c in checks_missing if c["gate"] == "exact_manifest_run_coverage")["passed"]

    print("Phase187 fatal-gate validator regression: PASS")


if __name__ == "__main__":
    run()