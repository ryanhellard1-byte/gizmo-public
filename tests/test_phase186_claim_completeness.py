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
    def test_current_pipeline_is_blocked_on_exact_missing_gate_set(self):
        report = p186.audit()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["final_physics_claim_allowed"])
        self.assertEqual(
            set(report["missing_fatal_gates"]),
            {
                "SIDM2c_total_profile_recovery",
                "CDM_stability",
                "SIDMx_HL_causal_signal",
                "HL_off_mimic_rejection",
                "seed_stability",
            },
        )

    def test_existing_runtime_convergence_and_collision_gates_are_credited(self):
        report = p186.audit()
        self.assertEqual(
            set(report["covered_fatal_gates"]),
            {
                "energy_drift",
                "momentum_drift",
                "pair_conservation",
                "Monte_Carlo_probability",
                "particle_loss",
                "SIDM2v_resolution_convergence",
                "timestep_convergence",
                "neighbor_convergence",
            },
        )
        self.assertEqual(len(report["covered_fatal_gates"]), 8)
        self.assertEqual(len(report["missing_fatal_gates"]), 5)

    def test_nonfatal_collapse_clock_is_reported_but_not_a_ready_condition(self):
        covered = set(p186.REQUIRED_FATAL_GATES)
        report = p186.audit(covered)
        self.assertEqual(report["status"], "READY")
        self.assertIn("SIDM2c_collapse_clock", report["missing_nonfatal_diagnostics"])

    def test_ready_only_when_every_fatal_gate_has_an_evaluator(self):
        report = p186.audit(p186.REQUIRED_FATAL_GATES)
        self.assertEqual(report["status"], "READY")
        self.assertTrue(report["final_physics_claim_allowed"])
        self.assertEqual(report["missing_fatal_gates"], [])

    def test_assert_final_claim_ready_fails_closed_today(self):
        with self.assertRaises(p186.ClaimCompletenessError):
            p186.assert_final_claim_ready()


if __name__ == "__main__":
    unittest.main()
