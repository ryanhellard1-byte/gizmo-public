#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "d3" / "production"
MOD_PATH = PROD / "phase174_radial_convergence_validator.py"
spec = importlib.util.spec_from_file_location("phase174_radial_convergence_validator", MOD_PATH)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def manifest_row(run_id, group, branch="SIDM2v", tier="R2_double", seed="1",
                 timestep="T_base", kernel="K_base"):
    return {
        "run_id": run_id,
        "group": group,
        "branch": branch,
        "resolution_tier": tier,
        "seed": str(seed),
        "timestep_control": timestep,
        "kernel_control": kernel,
    }


def profile_rows(run_id, scale=1.0, radii=(0.03, 0.1, 1.0, 3.0), time=10.0):
    rows = []
    for species, base in (("H", 4.0), ("L", 2.0), ("total", 3.0)):
        for i, r in enumerate(radii):
            rho = base * (i + 1) * scale
            rows.append({
                "run_id": run_id,
                "time_Gyr": str(time),
                "r_mid_over_rs": str(r),
                "r_lo_over_rs": str(r * 0.9),
                "r_hi_over_rs": str(r * 1.1),
                "species": species,
                "rho": str(rho),
                "rho_initial": str(base * (i + 1)),
                "rho_rel": str(scale),
                "sigma2": "1",
                "beta": "0",
                "mass_enclosed": "1",
            })
    return rows


class Phase174RadialConvergenceTests(unittest.TestCase):
    def test_pair_delta_passes_below_ten_percent(self):
        ref = manifest_row("R3", "core_blind_production", tier="R3_gold")
        test = manifest_row("R2", "core_blind_production", tier="R2_double")
        profiles = profile_rows("R3", 1.0) + profile_rows("R2", 1.099)
        out = m.compare_profile_pair(profiles, ref, test)
        self.assertLess(out["max_fractional_delta"], 0.10)

    def test_exact_threshold_is_rejected(self):
        ref = manifest_row("BASE", "core_blind_production")
        test = manifest_row("HALF", "half_timestep_convergence", timestep="T_half")
        profiles = profile_rows("BASE", 1.0) + profile_rows("HALF", 1.05)
        checks = []
        ok = m.radial_gate("half", profiles, [(ref, test)], 0.05, checks)
        self.assertFalse(ok)
        self.assertFalse(checks[-1]["passed"])

    def test_single_bad_bin_cannot_be_averaged_away(self):
        ref = manifest_row("BASE", "core_blind_production")
        test = manifest_row("NGB", "neighbor_kernel_convergence", kernel="K_high")
        profiles = profile_rows("BASE", 1.0) + profile_rows("NGB", 1.0)
        for row in profiles:
            if row["run_id"] == "NGB" and row["species"] == "H" and row["r_mid_over_rs"] == "0.1":
                row["rho"] = str(float(row["rho"]) * 1.071)
        checks = []
        ok = m.radial_gate("neighbor", profiles, [(ref, test)], 0.07, checks)
        self.assertFalse(ok)
        self.assertGreater(checks[-1]["detail"]["worst"]["max_fractional_delta"], 0.07)

    def test_bin_mismatch_fails_closed(self):
        ref = manifest_row("A", "core_blind_production")
        test = manifest_row("B", "core_blind_production")
        profiles = profile_rows("A") + profile_rows("B", radii=(0.03, 0.1, 1.0))
        with self.assertRaises(m.ValidationError):
            m.compare_profile_pair(profiles, ref, test)

    def test_missing_species_fails_closed(self):
        ref = manifest_row("A", "core_blind_production")
        test = manifest_row("B", "core_blind_production")
        profiles = profile_rows("A") + [r for r in profile_rows("B") if r["species"] != "L"]
        with self.assertRaises(m.ValidationError):
            m.compare_profile_pair(profiles, ref, test)

    def test_nonpositive_density_fails_closed(self):
        rows = profile_rows("A")
        rows[0]["rho"] = "0"
        with self.assertRaises(m.ValidationError):
            m.select_claim_profile_rows(rows, "A")

    def test_outside_radial_range_is_not_used(self):
        ref = manifest_row("A", "core_blind_production")
        test = manifest_row("B", "core_blind_production")
        profiles = profile_rows("A") + profile_rows("B")
        for rid in ("A", "B"):
            profiles.extend(profile_rows(rid, scale=100.0, radii=(0.01, 4.0)))
        out = m.compare_profile_pair(profiles, ref, test)
        self.assertAlmostEqual(out["max_fractional_delta"], 0.0, places=12)

    def test_claim_epoch_is_ten_gyr_only(self):
        ref = manifest_row("A", "core_blind_production")
        test = manifest_row("B", "core_blind_production")
        profiles = profile_rows("A") + profile_rows("B")
        profiles += profile_rows("A", scale=1.0, time=80.0)
        profiles += profile_rows("B", scale=2.0, time=80.0)
        out = m.compare_profile_pair(profiles, ref, test)
        self.assertAlmostEqual(out["max_fractional_delta"], 0.0, places=12)

    def test_resolution_pairing_requires_same_seed(self):
        rows = [
            manifest_row("R2a", "core_blind_production", tier="R2_double", seed="11"),
            manifest_row("R3b", "core_blind_production", tier="R3_gold", seed="12"),
        ]
        with self.assertRaises(m.ValidationError):
            m.build_resolution_pairs(rows)

    def test_timestep_pair_uses_core_base_same_seed(self):
        rows = [
            manifest_row("BASE", "core_blind_production", seed="11", timestep="T_base"),
            manifest_row("HALF", "half_timestep_convergence", seed="11", timestep="T_half"),
        ]
        pairs = m.build_timestep_pairs(rows)
        self.assertEqual([(a["run_id"], b["run_id"]) for a, b in pairs], [("BASE", "HALF")])

    def test_neighbor_pair_uses_core_kbase_same_seed(self):
        rows = [
            manifest_row("BASE", "core_blind_production", seed="11", kernel="K_base"),
            manifest_row("LOW", "neighbor_kernel_convergence", seed="11", kernel="K_low"),
            manifest_row("HIGH", "neighbor_kernel_convergence", seed="11", kernel="K_high"),
        ]
        pairs = m.build_neighbor_pairs(rows)
        self.assertEqual(
            [(a["run_id"], b["run_id"]) for a, b in pairs],
            [("BASE", "LOW"), ("BASE", "HIGH")],
        )

    def test_collision_thresholds_are_strict(self):
        manifest = [manifest_row("A", "core_blind_production")]
        rows = [{
            "run_id": "A",
            "channel": "HL",
            "collision_count": "1",
            "mean_sigma_factor": "1",
            "mean_mu": "0",
            "max_pair_dP_over_P": str(m.PAIR_RESIDUAL_MAX),
            "max_pair_dK_over_K": "0",
            "prob_clip_fraction_max": "0",
        }]
        checks = []
        ok = m.validate_collision_summary(manifest, rows, checks)
        self.assertFalse(ok)
        gate = next(c for c in checks if c["gate"] == "collision_pair_momentum_residual")
        self.assertFalse(gate["passed"])

    def test_collision_bad_count_rejected(self):
        manifest = [manifest_row("A", "core_blind_production")]
        rows = [{
            "run_id": "A",
            "channel": "HL",
            "collision_count": "1.5",
            "mean_sigma_factor": "1",
            "mean_mu": "0",
            "max_pair_dP_over_P": "0",
            "max_pair_dK_over_K": "0",
            "prob_clip_fraction_max": "0",
        }]
        checks = []
        ok = m.validate_collision_summary(manifest, rows, checks)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
