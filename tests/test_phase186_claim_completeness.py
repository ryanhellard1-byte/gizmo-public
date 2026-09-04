#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase186_claim_completeness.py"
spec = importlib.util.spec_from_file_location("p186", MOD_PATH)
assert spec and spec.loader
p186 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p186)


class Phase186ClaimCompletenessTests(unittest.TestCase):
    def test_current_pipeline_has_all_13_fatal_evaluator_families(self):
        report = p186.audit()
        self.assertEqual(report["status"], "READY")
        self.assertTrue(report["final_physics_claim_allowed"])
        self.assertEqual(report["missing_fatal_gates"], [])
        self.assertEqual(set(report["covered_fatal_gates"]), set(p186.REQUIRED_FATAL_GATES))
        self.assertEqual(len(report["covered_fatal_gates"]), 13)

    def test_phase187_closes_the_exact_previous_missing_set(self):
        previous = {
            "energy_drift",
            "momentum_drift",
            "SIDM2c_total_profile_recovery",
            "CDM_stability",
            "SIDMx_HL_causal_signal",
            "HL_off_mimic_rejection",
            "seed_stability",
        }
        for gate in previous:
            self.assertIn(gate, p186.CURRENT_COVERAGE)
            self.assertIn("Phase187", p186.CURRENT_COVERAGE[gate])

    def test_nonfatal_collapse_clock_is_reported_but_not_a_ready_condition(self):
        report = p186.audit()
        self.assertEqual(report["status"], "READY")
        self.assertIn("SIDM2c_collapse_clock", report["missing_nonfatal_diagnostics"])

    def test_missing_any_fatal_gate_still_blocks(self):
        covered = set(p186.REQUIRED_FATAL_GATES)
        covered.remove("energy_drift")
        report = p186.audit(covered)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["final_physics_claim_allowed"])
        self.assertEqual(report["missing_fatal_gates"], ["energy_drift"])

    def test_assert_final_claim_ready_now_passes_implementation_only(self):
        report = p186.assert_final_claim_ready()
        self.assertEqual(report["status"], "READY")
        self.assertIn("does not mean campaign data passed", report["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
