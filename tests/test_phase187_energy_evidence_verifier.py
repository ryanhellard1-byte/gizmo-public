#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase187_energy_evidence_verifier.py"
spec = importlib.util.spec_from_file_location("p187v", MOD_PATH)
assert spec and spec.loader
p187v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p187v)


class Phase187EnergyBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_root = self.root / "runs"
        self.run_root.mkdir()
        self.ids = ["R001", "R002"]

        self.probe = self.root / "GIZMO_PHASE187_ENERGY_PROBE"
        self.probe.write_bytes(b"phase187-probe")
        self.probe_sha = p187v.sha256_file(self.probe)

        self.att = self.root / "probe_attestation.json"
        self.att_data = {
            "phase": 187,
            "status": "PASS",
            "kind": "analysis_only_gizmo_energy_probe_build",
            "canonical_source_required": True,
            "source_commit": p187v.p187e.CANONICAL_PHYSICS_SOURCE_COMMIT,
            "canonical_physics_source_commit": p187v.p187e.CANONICAL_PHYSICS_SOURCE_COMMIT,
            "probe_executable_sha256": self.probe_sha,
            "builder_sha256": p187v.sha256_file(Path(p187v.p187e.__file__)),
            "patch_contract_sha256": p187v.sha256_bytes(p187v.p187e.RUN_PATCH.encode()),
            "probe_config_sha256": p187v.sha256_bytes(p187v.p187e.PROBE_CONFIG.encode()),
            "physics_isolation": {
                "DM_SIDM_enabled": False,
                "COMPUTE_POTENTIAL_ENERGY_enabled": True,
                "explicit_global_state_population": True,
                "returns_before_find_timesteps": True,
                "production_executable_modified": False,
            },
        }
        self.att.write_text(json.dumps(self.att_data) + "\n")

        self.current = {
            "R001": self.source_record("R001", "1" * 64, "2" * 64, "a" * 64),
            "R002": self.source_record("R002", "3" * 64, "4" * 64, "b" * 64),
        }
        self.csv = self.root / "energy.csv"
        self.report = self.root / "energy_report.json"
        self.write_bundle()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def source_record(rid, snap0, snap1, source_sha):
        return {
            "run_id": rid,
            "energy_source_sha256": source_sha,
            "completion_record_sha256": "c" * 64,
            "params_sha256": "d" * 64,
            "ic_sha256": "e" * 64,
            "snapshots": [
                {"expected_time_Gyr": 0.0, "snapshot": f"/x/{rid}/ic", "snapshot_sha256": snap0},
                {"expected_time_Gyr": 10.0, "snapshot": f"/x/{rid}/snap10", "snapshot_sha256": snap1},
            ],
        }

    def run_report(self, rid):
        current = self.current[rid]
        etots = [-100.0, -99.0]
        drifts = [0.0, 0.01]
        samples = []
        for i, actual in enumerate(current["snapshots"]):
            samples.append({
                "expected_time_Gyr": actual["expected_time_Gyr"],
                "snapshot_sha256": actual["snapshot_sha256"],
                "probe_executable_sha256": self.probe_sha,
                "original_params_sha256": current["params_sha256"],
                "Etot": etots[i],
                "Ekin": 10.0,
                "Epot": etots[i] - 10.0,
                "Eint": 0.0,
            })
        return {
            "run_id": rid,
            "status": "PASS",
            "energy_drift_abs_max": 0.01,
            "energy_probe_sha256": self.probe_sha,
            "energy_source_sha256": current["energy_source_sha256"],
            "samples": samples,
            "drifts": drifts,
        }

    def write_bundle(self):
        with self.csv.open("w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=p187v.ENERGY_REQUIRED)
            wr.writeheader()
            for rid in self.ids:
                rr = self.run_report(rid)
                wr.writerow({k: rr[k] for k in p187v.ENERGY_REQUIRED})
        runs = [self.run_report(rid) for rid in self.ids]
        report = {
            "phase": 187,
            "status": "PASS",
            "kind": "gizmo_global_energy_evidence",
            "manifest_sha256": p187v.EXPECTED_MANIFEST_SHA256,
            "run_count": len(self.ids),
            "sample_count": 2 * len(self.ids),
            "probe_executable_sha256": self.probe_sha,
            "energy_evidence_sha256": p187v.sha256_file(self.csv),
            "runs": runs,
        }
        self.report.write_text(json.dumps(report) + "\n")

    def verify(self):
        with mock.patch.object(p187v, "EXPECTED_TOTAL", len(self.ids)), \
             mock.patch.object(p187v, "frozen_manifest_ids", return_value=self.ids), \
             mock.patch.object(p187v, "current_campaign_source", side_effect=lambda _root, rid: self.current[rid]):
            return p187v.verify(self.run_root, self.csv, self.report, self.att, self.probe)

    def test_valid_bundle_passes(self):
        result = self.verify()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["verified_source_hashes"])
        self.assertTrue(result["verified_sample_snapshot_hashes"])
        self.assertTrue(result["verified_sample_energy_arithmetic"])

    def test_dummy_source_hash_attack_fails_even_with_rehashed_csv(self):
        rows = list(csv.DictReader(self.csv.open()))
        rows[0]["energy_source_sha256"] = "f" * 64
        with self.csv.open("w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=p187v.ENERGY_REQUIRED)
            wr.writeheader()
            wr.writerows(rows)
        report = json.loads(self.report.read_text())
        report["energy_evidence_sha256"] = p187v.sha256_file(self.csv)
        report["runs"][0]["energy_source_sha256"] = "f" * 64
        self.report.write_text(json.dumps(report) + "\n")
        with self.assertRaises(p187v.EnergyEvidenceError):
            self.verify()

    def test_snapshot_hash_mismatch_fails(self):
        report = json.loads(self.report.read_text())
        report["runs"][0]["samples"][1]["snapshot_sha256"] = "9" * 64
        self.report.write_text(json.dumps(report) + "\n")
        with self.assertRaises(p187v.EnergyEvidenceError):
            self.verify()

    def test_noncanonical_probe_attestation_fails(self):
        att = dict(self.att_data)
        att["canonical_source_required"] = False
        self.att.write_text(json.dumps(att) + "\n")
        with self.assertRaises(p187v.EnergyEvidenceError):
            self.verify()


if __name__ == "__main__":
    unittest.main()