#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase185_final_verdict.py"
spec = importlib.util.spec_from_file_location("p185", MOD_PATH)
assert spec and spec.loader
p185 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p185)


class Phase185FinalVerdictTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_root = self.root / "runs"
        self.run_root.mkdir()
        self.att = self.root / "att.json"
        self.att.write_text('{"status":"PASS"}\n')
        self.exe = self.root / "GIZMO"
        self.exe.write_bytes(b"exe")
        self.final = self.root / "final"

    def tearDown(self):
        self.tmp.cleanup()

    def ready_guard(self):
        return mock.patch.object(
            p185.p186,
            "assert_final_claim_ready",
            return_value={"phase": 186, "status": "READY", "final_physics_claim_allowed": True},
        )

    def fake_collect(self, run_root, output_dir, machine_attestation, executable):
        output_dir.mkdir(parents=True)
        rows = ["run_id,status,energy_drift_abs_max,momentum_drift_abs_max"]
        for i in range(p185.EXPECTED_TOTAL):
            rows.append(f"R{i+1:03d},COMPLETE,0.001,0.00001")
        (output_dir / "run_summary.csv").write_text("\n".join(rows) + "\n")
        (output_dir / "profiles.csv").write_text("run_id,time_Gyr\nR001,80\n")
        (output_dir / "collision_log_summary.csv").write_text("run_id,channel\nR001,HL\n")
        report = {
            "phase": 184,
            "status": "PASS",
            "manifest_sha256": p185.EXPECTED_MANIFEST_SHA256,
            "run_count": p185.EXPECTED_TOTAL,
        }
        (output_dir / "phase184_collection_report.json").write_text(json.dumps(report) + "\n")
        return report

    def fake_manifest(self):
        return b"run_id\nR001\n", [{} for _ in range(p185.EXPECTED_TOTAL)]

    def test_incomplete_claim_contract_blocks_before_reading_campaign(self):
        with mock.patch.object(
            p185.p186,
            "assert_final_claim_ready",
            side_effect=p185.p186.ClaimCompletenessError("missing gates"),
        ), mock.patch.object(p185.p184, "collect_campaign") as collect:
            with self.assertRaises(p185.p186.ClaimCompletenessError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)
        collect.assert_not_called()
        self.assertFalse(self.final.exists())
        self.assertFalse(any(self.root.glob(".final.phase185-staging-*")))

    def test_pass_requires_radial_and_runtime_gates(self):
        with self.ready_guard(), \
             mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect), \
             mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest), \
             mock.patch.object(p185.p174, "validate", return_value=(True, [{"gate":"radial","passed":True}])):
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["phase174_status"], "PASS")
        self.assertEqual(report["phase187_status"], "PASS")
        self.assertEqual(report["phase186_claim_completeness"]["status"], "READY")
        self.assertTrue((self.final / "phase185_final_verdict.json").is_file())
        self.assertTrue((self.final / "phase174_physics_verdict.json").is_file())
        self.assertTrue((self.final / "phase187_runtime_verdict.json").is_file())
        self.assertTrue((self.final / "evidence" / "run_summary.csv").is_file())

    def test_phase174_fail_is_preserved_not_deleted(self):
        with self.ready_guard(), \
             mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect), \
             mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest), \
             mock.patch.object(p185.p174, "validate", return_value=(False, [{"gate":"radial","passed":False}])):
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)
        self.assertEqual(report["status"], "FAIL")
        verdict = json.loads((self.final / "phase174_physics_verdict.json").read_text())
        self.assertEqual(verdict["status"], "FAIL")
        self.assertTrue((self.final / "phase187_runtime_verdict.json").is_file())
        self.assertTrue((self.final / "evidence" / "profiles.csv").is_file())

    def test_phase187_runtime_fail_is_preserved_not_deleted(self):
        with self.ready_guard(), \
             mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect), \
             mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest), \
             mock.patch.object(p185.p174, "validate", return_value=(True, [{"gate":"radial","passed":True}])), \
             mock.patch.object(
                 p185.p187,
                 "validate_run_metrics",
                 return_value=(False, [{"gate":"energy_drift_hard_gate","passed":False,"fatal":True}]),
             ):
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["phase174_status"], "PASS")
        self.assertEqual(report["phase187_status"], "FAIL")
        verdict = json.loads((self.final / "phase187_runtime_verdict.json").read_text())
        self.assertEqual(verdict["status"], "FAIL")

    def test_evidence_error_leaves_no_final_directory(self):
        with self.ready_guard(), mock.patch.object(
            p185.p184, "collect_campaign", side_effect=p185.p184.CollectionError("bad evidence")
        ):
            with self.assertRaises(p185.p184.CollectionError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)
        self.assertFalse(self.final.exists())
        self.assertFalse(any(self.root.glob(".final.phase185-staging-*")))

    def test_refuses_existing_final_directory(self):
        self.final.mkdir()
        with self.ready_guard():
            with self.assertRaises(p185.VerdictError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe)


if __name__ == "__main__":
    unittest.main()
