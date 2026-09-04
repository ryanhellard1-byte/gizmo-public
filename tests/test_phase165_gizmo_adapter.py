#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "phase165_gizmo_adapter.py"
MANIFEST_PATH = ROOT / "d3" / "production" / "phase165_production_live_nbody_manifest.csv"

spec = importlib.util.spec_from_file_location("phase165_gizmo_adapter", MOD_PATH)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class Phase165GizmoAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = m.load_manifest(MANIFEST_PATH)

    def row(self, run_id):
        return m.find_row(self.rows, run_id)

    def test_manifest_frozen(self):
        self.assertEqual(len(self.rows), 127)
        self.assertEqual(m.manifest_sha256(MANIFEST_PATH), m.FROZEN_MANIFEST_SHA256)
        self.assertEqual(len(MANIFEST_PATH.read_bytes()), 24374)

    def test_compatibility_count_is_frozen(self):
        report = m.preflight_report(self.rows)
        self.assertEqual(report["status"], "PASS_WITH_FROZEN_SPECIAL_BLOCKS")
        self.assertEqual(report["supported_rows"], 123)
        self.assertEqual(report["blocked_rows"], 4)
        self.assertEqual(
            {x["run_id"] for x in report["blocked"]},
            {"PH165-0122", "PH165-0123", "PH165-0126", "PH165-0127"},
        )

    def test_native_branch_map(self):
        expected = {
            "CDM": 0,
            "SIDM2v": 1,
            "SIDMx": 2,
            "HL_off": 3,
            "HH_only": 4,
            "LL_only": 5,
            "HL_HH": 6,
            "HL_LL": 7,
            "SIDM2c_const": 8,
        }
        seen = {}
        for row in self.rows:
            if row["group"] in m.BLOCKED_SPECIAL_GROUPS or row["group"] == m.ZERO_NULL_GROUP:
                continue
            seen.setdefault(row["branch"], m.compatibility_for_row(row).mode)
        self.assertEqual(seen, expected)

    def test_zero_cross_section_uses_mode9(self):
        row = self.row("PH165-0124")
        comp = m.compatibility_for_row(row)
        self.assertTrue(comp.supported)
        self.assertEqual(comp.mode, 9)
        self.assertEqual(comp.sentinel, -9.0)

    def test_r0_render_is_native_gizmo(self):
        row = self.row("PH165-0049")
        text = m.render_params(
            row,
            Path("/tmp/ic.dat"),
            Path("/tmp/out"),
            Path("/tmp/output_times.txt"),
        )
        self.assertIn("DM_InteractionCrossSection   0", text)
        self.assertIn("OutputListOn                1", text)
        self.assertIn("AGS_DesNumNgb                64", text)
        self.assertIn("Softening_Type1              0.059999999999999998", text)
        self.assertNotIn("--branch", text)
        self.assertNotIn("--channels", text)

    def test_80_gyr_time_conversion(self):
        row = self.row("PH165-0049")
        plan = m.plan_row(row, Path("/tmp/ic"), 0.05)
        self.assertAlmostEqual(plan["TimeMax_code"] * m.CODE_TIME_GYR, 80.0, places=12)
        self.assertAlmostEqual(
            plan["MaxSizeTimestep_code"] * m.CODE_TIME_GYR,
            float(row["max_dt_Gyr"]),
            places=15,
        )

    def test_blocked_identity_null_fails_render(self):
        row = self.row("PH165-0122")
        with self.assertRaises(m.AdapterError):
            m.render_params(row, Path("/tmp/ic"), Path("/tmp/out"), Path("/tmp/times"))


if __name__ == "__main__":
    unittest.main()
