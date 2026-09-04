#!/usr/bin/env python3
"""Self-tests for the Phase174 radial convergence validator."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import phase174_radial_convergence_validator as v


BINS = (
    (0.03, 0.05, 0.08, 1.00),
    (0.50, 1.00, 1.50, 0.25),
    (2.00, 2.50, 3.00, 0.08),
)


class Phase174ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = Path(__file__).resolve().with_name("phase172_manifest_for_test.csv")
        raw, rows = v.phase172_lock.load()
        self.manifest.write_bytes(raw)
        self.rows = rows
        self.addCleanup(self._cleanup_manifest)
        self.addCleanup(self.tmp.cleanup)

    def _cleanup_manifest(self):
        try:
            self.manifest.unlink()
        except FileNotFoundError:
            pass

    def _pairs_and_ids(self):
        pairs = v.build_pairs(self.rows)
        ids = {
            row["run_id"]
            for family in pairs.values()
            for pair in family
            for row in pair[:2]
        }
        by_id = {r["run_id"]: r for r in self.rows}
        return pairs, ids, by_id

    def _rho_multiplier(self, row):
        if row["group"] == "core_blind_production" and row["branch"] == "SIDM2v":
            if row["resolution_tier"] == "R3_gold":
                return 1.0
            if row["resolution_tier"] == "R2_double":
                return 1.08
        if row["group"] == "half_timestep_convergence" and row["branch"] == "SIDM2v":
            return 1.08 / 1.04
        if row["group"] == "neighbor_kernel_convergence" and row["branch"] == "SIDM2v":
            if row["kernel_control"] == "K_low":
                return 1.08 * 1.06
            if row["kernel_control"] == "K_high":
                return 1.08 * 0.95
        raise AssertionError(f"unhandled fixture row {row}")

    def _write_profiles(self, mutate=None):
        _, ids, by_id = self._pairs_and_ids()
        path = self.root / "profiles.csv"
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=v.PROFILE_REQUIRED)
            w.writeheader()
            for rid in sorted(ids):
                row = by_id[rid]
                mult = self._rho_multiplier(row)
                for t in v.EXPECTED_ANALYSIS_TIMES_GYR:
                    for species, sf in (("H", 1.0), ("L", 0.7)):
                        for rlo, rmid, rhi, rf in BINS:
                            rho0 = 100.0 * sf * rf
                            rec = {
                                "run_id": rid,
                                "time_Gyr": t,
                                "r_mid_over_rs": rmid,
                                "r_lo_over_rs": rlo,
                                "r_hi_over_rs": rhi,
                                "species": species,
                                "rho": rho0 * mult,
                                "rho_initial": rho0,
                                "rho_rel": mult,
                                "sigma2": 25.0,
                                "beta": 0.0,
                                "mass_enclosed": 1.0e9 * rf,
                            }
                            if mutate:
                                mutate(rec, row)
                            w.writerow(rec)
        return path

    def _write_collisions(self, mutate=None):
        _, ids, _ = self._pairs_and_ids()
        path = self.root / "collision_log_summary.csv"
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=v.COLLISION_REQUIRED)
            w.writeheader()
            for rid in sorted(ids):
                for ch in v.FULL_CHANNELS:
                    rec = {
                        "run_id": rid,
                        "channel": ch,
                        "collision_count": 100,
                        "mean_sigma_factor": 0.5,
                        "mean_mu": 0.0,
                        "max_pair_dP_over_P": 1.0e-15,
                        "max_pair_dK_over_K": 1.0e-15,
                        "prob_clip_fraction_max": 1.0e-4,
                    }
                    if mutate:
                        mutate(rec)
                    w.writerow(rec)
        return path

    def _validate(self, profiles, collisions):
        return v.validate(
            profiles,
            collisions,
            self.manifest,
            include_all_time_diagnostics=False,
        )

    def _gate(self, result, name):
        return next(g for g in result["gates"] if g["gate"] == name)

    def test_pass_fixture(self):
        result = self._validate(self._write_profiles(), self._write_collisions())
        self.assertEqual(result["status"], "PASS")
        self.assertAlmostEqual(
            self._gate(result, "SIDM2v_R2_R3_radial_convergence")["observed_max"],
            0.08,
            places=12,
        )
        self.assertAlmostEqual(
            self._gate(result, "SIDM2v_half_timestep_radial_convergence")["observed_max"],
            0.04,
            places=12,
        )
        self.assertAlmostEqual(
            self._gate(result, "SIDM2v_neighbor_radial_convergence")["observed_max"],
            0.06,
            places=12,
        )

    def test_resolution_fails_above_ten_percent(self):
        def mutate(rec, row):
            if (
                row["group"] == "core_blind_production"
                and row["branch"] == "SIDM2v"
                and row["resolution_tier"] == "R2_double"
                and row["seed"] == "165004"
                and float(rec["time_Gyr"]) == 10.0
                and rec["species"] == "H"
                and float(rec["r_mid_over_rs"]) == 1.0
            ):
                rec["rho"] = float(rec["rho_initial"]) * 1.101

        result = self._validate(self._write_profiles(mutate), self._write_collisions())
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(self._gate(result, "SIDM2v_R2_R3_radial_convergence")["passed"])

    def test_timestep_fails_above_five_percent(self):
        def mutate(rec, row):
            if (
                row["group"] == "half_timestep_convergence"
                and row["branch"] == "SIDM2v"
                and row["seed"] == "165001"
                and float(rec["time_Gyr"]) == 10.0
                and rec["species"] == "H"
                and float(rec["r_mid_over_rs"]) == 1.0
            ):
                rec["rho"] = float(rec["rho_initial"]) * 1.08 / 1.051

        result = self._validate(self._write_profiles(mutate), self._write_collisions())
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(self._gate(result, "SIDM2v_half_timestep_radial_convergence")["passed"])

    def test_neighbor_fails_above_seven_percent(self):
        def mutate(rec, row):
            if (
                row["group"] == "neighbor_kernel_convergence"
                and row["branch"] == "SIDM2v"
                and row["kernel_control"] == "K_low"
                and row["seed"] == "165001"
                and float(rec["time_Gyr"]) == 10.0
                and rec["species"] == "L"
                and float(rec["r_mid_over_rs"]) == 2.5
            ):
                rec["rho"] = float(rec["rho_initial"]) * 1.08 * 1.071

        result = self._validate(self._write_profiles(mutate), self._write_collisions())
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(self._gate(result, "SIDM2v_neighbor_radial_convergence")["passed"])

    def test_collision_integrity_is_fatal(self):
        target = {"done": False}

        def mutate(rec):
            if not target["done"]:
                rec["max_pair_dP_over_P"] = 1.1e-12
                target["done"] = True

        result = self._validate(self._write_profiles(), self._write_collisions(mutate))
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(
            self._gate(result, "collision_log_integrity_for_radial_gate_runs")["passed"]
        )

    def test_missing_common_bin_fails_closed(self):
        removed = {"done": False}

        def mutate(rec, row):
            if (
                not removed["done"]
                and row["group"] == "core_blind_production"
                and row["branch"] == "SIDM2v"
                and row["resolution_tier"] == "R3_gold"
                and row["seed"] == "165004"
                and float(rec["time_Gyr"]) == 10.0
                and rec["species"] == "H"
                and float(rec["r_mid_over_rs"]) == 1.0
            ):
                rec["r_mid_over_rs"] = 1.01
                removed["done"] = True

        profiles = self._write_profiles(mutate)
        collisions = self._write_collisions()
        with self.assertRaises(v.ValidationError):
            self._validate(profiles, collisions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
