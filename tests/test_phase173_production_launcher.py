#!/usr/bin/env python3
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "d3" / "production"
MOD_PATH = PROD / "phase173_production_launcher.py"
spec = importlib.util.spec_from_file_location("phase173_production_launcher", MOD_PATH)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class Phase173ProductionLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prov = m.load_provenance(PROD / "phase173_provenance_master_6353.json")
        cls.raw, cls.rows = m.frozen_manifest()

    def test_provenance_is_current_green_master(self):
        self.assertEqual(self.prov["physics_source_commit"], m.EXPECTED_PHYSICS_SOURCE_COMMIT)
        self.assertEqual(self.prov["workflow_run_id"], 33845004328)
        self.assertEqual(self.prov["artifact_id"], 9926223195)
        self.assertEqual(self.prov["executable_sha256"], m.EXPECTED_EXECUTABLE_SHA256)
        self.assertEqual(self.prov["required_final_time_Gyr"], 80.0)

    def test_manifest_is_frozen_127_119(self):
        self.assertEqual(len(self.rows), 127)
        self.assertEqual(sum(r["blind_analysis"] == "True" for r in self.rows), 119)
        with tempfile.TemporaryDirectory() as td:
            p, rows = m.materialize_manifest(Path(td) / "phase172.csv")
            self.assertEqual(m.sha256_file(p), m.EXPECTED_MANIFEST_SHA256)
            self.assertEqual(len(rows), 127)

    def test_every_row_passes_launcher_contract(self):
        for row in self.rows:
            m.validate_row(row)
            self.assertAlmostEqual(m.parse_times(row)[-1], 80.0, places=12)

    def test_r0_has_exactly_eight_rows(self):
        r0 = [r for r in self.rows if r["group"] == "R0_commissioning_not_for_claims"]
        self.assertEqual(len(r0), 8)
        self.assertEqual({r["branch"] for r in r0}, {"CDM", "SIDMx", "HL_off", "SIDM2v"})

    def test_identical_label_control_is_repaired(self):
        rows = [r for r in self.rows if r["group"] == "identical_label_null"]
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual(float(r["ic_mass_ratio"]), 1.0)
            self.assertEqual(r["runtime_contract"], "standard_constant_identical_labels")
            self.assertEqual(float(r["runtime_interaction_parameter"]), 1.125)
            m.validate_row(r)

    def test_permutation_control_is_frozen(self):
        rows = [r for r in self.rows if r["group"] == "permutation_reproducibility"]
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual(r["ic_order"], "shuffled_within_species")
            p = m.expected_ic_path(Path("/ic"), r)
            self.assertIn("shuffled_within_species", p.name)
            m.validate_row(r)

    def test_wrong_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "GIZMO_D3"
            fake.write_bytes(b"definitely not the production binary")
            with self.assertRaises(m.LaunchError):
                m.verify_executable(fake, self.prov)

    def test_plan_preserves_80gyr_and_runtime(self):
        i, row = m.find_row(self.rows, "PH165-0001")
        p = m.plan(row, i, Path("/ic"))
        self.assertEqual(p["required_final_time_Gyr"], 80.0)
        self.assertEqual(p["runtime_interaction_parameter"], float(row["runtime_interaction_parameter"]))
        self.assertEqual(p["N_total"], int(row["N_total"]))


if __name__ == "__main__":
    unittest.main()
