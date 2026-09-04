#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase187_runtime_invariants.py"
spec = importlib.util.spec_from_file_location("p187", MOD_PATH)
assert spec and spec.loader
p187 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p187)


class Phase187RuntimeInvariantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_energy(self, rows):
        path = self.root / "energy.txt"
        a = np.zeros((len(rows), p187.ENERGY_COLUMNS), dtype=float)
        for i, (time_gyr, eint, epot, ekin) in enumerate(rows):
            a[i, 0] = time_gyr / p187.TIME_UNIT_GYR
            a[i, 1] = eint
            a[i, 2] = epot
            a[i, 3] = ekin
        np.savetxt(path, a, fmt="%.17g")
        return path

    def snapshot(self, vcom):
        masses = np.array([3.0, 1.0], dtype=float)
        # Equal particle velocities make the requested COM velocity exact and
        # keep this unit test about the frozen invariant definition only.
        vel = np.tile(np.asarray(vcom, dtype=float), (2, 1))
        return p187.p181.Snapshot(
            0.0,
            np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float),
            vel,
            masses,
            np.array([1, 2], dtype=np.int8),
            np.array([1, 2], dtype=np.uint64),
        )

    def mapped(self, final_vcom=(0.0, 0.0, 0.0)):
        out = []
        n = len(p187.p181.EXPECTED_TIMES_GYR)
        for i, t in enumerate(p187.p181.EXPECTED_TIMES_GYR):
            path = self.root / f"snap_{i:03d}"
            path.write_bytes(f"snapshot-{i}".encode())
            frac = i / (n - 1)
            v = np.asarray(final_vcom, dtype=float) * frac
            out.append((float(t), path, self.snapshot(v)))
        return out

    def test_energy_drift_uses_gizmo_total_energy_columns(self):
        path = self.write_energy([
            (0.0, 0.0, -100.0, 50.0),
            (40.0, 0.0, -99.9, 50.0),
            (80.0, 0.0, -99.75, 50.0),
        ])
        result = p187.energy_drift(path)
        self.assertAlmostEqual(result["energy_initial"], -50.0)
        self.assertAlmostEqual(result["energy_final"], -49.75)
        self.assertAlmostEqual(result["energy_drift_abs_max"], 0.005)
        self.assertEqual(result["energy_statistics_rows"], 3)

    def test_energy_drift_rejects_wrong_column_contract(self):
        path = self.root / "energy.txt"
        np.savetxt(path, np.zeros((2, p187.ENERGY_COLUMNS - 1)))
        with self.assertRaises(p187.RuntimeInvariantError):
            p187.energy_drift(path)

    def test_energy_drift_requires_zero_time_baseline(self):
        path = self.write_energy([
            (0.25, 0.0, -100.0, 50.0),
            (80.0, 0.0, -100.0, 50.0),
        ])
        with self.assertRaises(p187.RuntimeInvariantError):
            p187.energy_drift(path)

    def test_energy_drift_requires_end_of_campaign_coverage(self):
        path = self.write_energy([
            (0.0, 0.0, -100.0, 50.0),
            (55.28, 0.0, -100.0, 50.0),
        ])
        with self.assertRaises(p187.RuntimeInvariantError):
            p187.energy_drift(path)

    def test_momentum_proxy_is_mass_weighted_com_velocity_drift(self):
        mapped = self.mapped(final_vcom=(6.0e-5, -8.0e-5, 0.0))
        result = p187.momentum_drift_from_mapped(mapped)
        self.assertAlmostEqual(result["momentum_drift_abs_max"], 1.0e-4)
        self.assertEqual(len(result["momentum_samples"]), 11)
        self.assertEqual(
            result["momentum_proxy_definition"],
            "max ||v_COM(t)-v_COM(0)|| for H+L, code velocity units",
        )

    def test_campaign_hard_gates_are_strict(self):
        ok, checks = p187.validate_run_metrics([
            {"energy_drift_abs_max": 0.009, "momentum_drift_abs_max": 9.0e-5},
            {"energy_drift_abs_max": 0.002, "momentum_drift_abs_max": 1.0e-5},
        ])
        self.assertTrue(ok)
        self.assertTrue(next(c for c in checks if c["gate"] == "energy_drift_hard_gate")["passed"])
        self.assertTrue(next(c for c in checks if c["gate"] == "momentum_drift_gate")["passed"])

        ok, checks = p187.validate_run_metrics([
            {"energy_drift_abs_max": 0.01, "momentum_drift_abs_max": 1.0e-5},
        ])
        self.assertFalse(ok)
        self.assertFalse(next(c for c in checks if c["gate"] == "energy_drift_hard_gate")["passed"])

        ok, checks = p187.validate_run_metrics([
            {"energy_drift_abs_max": 0.001, "momentum_drift_abs_max": 1.0e-4},
        ])
        self.assertFalse(ok)
        self.assertFalse(next(c for c in checks if c["gate"] == "momentum_drift_gate")["passed"])

    def test_preferred_energy_median_is_nonfatal(self):
        ok, checks = p187.validate_run_metrics([
            {"energy_drift_abs_max": 0.004, "momentum_drift_abs_max": 1.0e-5},
            {"energy_drift_abs_max": 0.004, "momentum_drift_abs_max": 1.0e-5},
        ])
        self.assertTrue(ok)
        preferred = next(c for c in checks if c["gate"] == "energy_drift_median_preferred")
        self.assertFalse(preferred["passed"])
        self.assertFalse(preferred["fatal"])


if __name__ == "__main__":
    unittest.main()
