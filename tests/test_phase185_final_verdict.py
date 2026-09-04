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
        self.energy = self.root / "phase187_energy.csv"
        self.energy.write_text("run_id,energy_drift_abs_max,energy_probe_sha256,energy_source_sha256\n")
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
        (output_dir / "run_summary.csv").write_text("run_id,status\nR001,COMPLETE\n")
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

    @staticmethod
    def fake_scalar_build(manifest, run_summary, profiles, run_root, energy, output):
        output.write_text("run_id,branch\nR001,CDM\n")
        return {"phase": 187, "status": "PASS", "kind": "phase187_scalar_evidence"}

    @staticmethod
    def fatal_pass(manifest, scalar):
        return {"phase": 187, "status": "PASS", "checks": [{"gate": "all-seven", "passed": True}]}

    def common_patches(self, radial_ok=True, fatal_status="PASS"):
        fatal = {"phase": 187, "status": fatal_status,
                 "checks": [{"gate": "all-seven", "passed": fatal_status == "PASS"}]}
        return (
            self.ready_guard(),
            mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect),
            mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest),
            mock.patch.object(p185.p174, "validate", return_value=(radial_ok, [{"gate":"radial","passed":radial_ok}])),
            mock.patch.object(p185.p187_scalar, "build", side_effect=self.fake_scalar_build),
            mock.patch.object(p185.p187, "report", return_value=fatal),
        )

    def test_incomplete_claim_contract_blocks_before_reading_campaign(self):
        with mock.patch.object(
            p185.p186,
            "assert_final_claim_ready",
            side_effect=p185.p186.ClaimCompletenessError("missing gates"),
        ), mock.patch.object(p185.p184, "collect_campaign") as collect:
            with self.assertRaises(p185.p186.ClaimCompletenessError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        collect.assert_not_called()
        self.assertFalse(self.final.exists())

    def test_missing_energy_evidence_blocks_before_campaign_collection(self):
        missing = self.root / "missing.csv"
        with self.ready_guard(), mock.patch.object(p185.p184, "collect_campaign") as collect:
            with self.assertRaises(p185.VerdictError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, missing)
        collect.assert_not_called()
        self.assertFalse(self.final.exists())

    def test_pass_requires_phase174_and_phase187_pass(self):
        patches = self.common_patches(radial_ok=True, fatal_status="PASS")
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["phase174_status"], "PASS")
        self.assertEqual(report["phase187_status"], "PASS")
        self.assertTrue(report["all_13_fatal_gate_families_evaluated"])
        self.assertTrue((self.final / "phase187_fatal_gate_verdict.json").is_file())
        self.assertTrue((self.final / "phase187_energy_evidence.csv").is_file())
        self.assertTrue((self.final / "phase185_final_verdict.json").is_file())

    def test_phase174_fail_is_preserved_as_physics_fail(self):
        patches = self.common_patches(radial_ok=False, fatal_status="PASS")
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["phase174_status"], "FAIL")
        self.assertEqual(report["phase187_status"], "PASS")

    def test_phase187_fail_is_preserved_as_physics_fail(self):
        patches = self.common_patches(radial_ok=True, fatal_status="FAIL")
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["phase174_status"], "PASS")
        self.assertEqual(report["phase187_status"], "FAIL")

    def test_scalar_builder_fail_matching_phase187_fail_is_preserved(self):
        def physics_fail_build(*args):
            output = args[-1]
            output.write_text("run_id,branch\nR001,CDM\n")
            return {"phase": 187, "status": "FAIL", "kind": "phase187_scalar_evidence"}
        with self.ready_guard(), \
             mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect), \
             mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest), \
             mock.patch.object(p185.p174, "validate", return_value=(True, [])), \
             mock.patch.object(p185.p187_scalar, "build", side_effect=physics_fail_build), \
             mock.patch.object(p185.p187, "report", return_value={"phase":187,"status":"FAIL","checks":[]}):
            report = p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["phase187_status"], "FAIL")
        self.assertTrue((self.final / "phase185_final_verdict.json").is_file())

    def test_scalar_builder_status_disagreement_fails_closed(self):
        def bad_build(*args):
            output = args[-1]
            output.write_text("run_id,branch\nR001,CDM\n")
            return {"phase": 187, "status": "FAIL"}
        with self.ready_guard(), \
             mock.patch.object(p185.p184, "collect_campaign", side_effect=self.fake_collect), \
             mock.patch.object(p185.p184, "frozen_manifest", side_effect=self.fake_manifest), \
             mock.patch.object(p185.p174, "validate", return_value=(True, [])), \
             mock.patch.object(p185.p187_scalar, "build", side_effect=bad_build), \
             mock.patch.object(p185.p187, "report", return_value={"phase":187,"status":"PASS","checks":[]}):
            with self.assertRaises(p185.VerdictError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertFalse(self.final.exists())

    def test_evidence_error_leaves_no_final_directory(self):
        with self.ready_guard(), mock.patch.object(
            p185.p184, "collect_campaign", side_effect=p185.p184.CollectionError("bad evidence")
        ):
            with self.assertRaises(p185.p184.CollectionError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)
        self.assertFalse(self.final.exists())
        self.assertFalse(any(self.root.glob(".final.phase185-staging-*")))

    def test_refuses_existing_final_directory(self):
        self.final.mkdir()
        with self.ready_guard():
            with self.assertRaises(p185.VerdictError):
                p185.finalize_campaign(self.run_root, self.final, self.att, self.exe, self.energy)


if __name__ == "__main__":
    unittest.main()
