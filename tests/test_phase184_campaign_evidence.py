#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase184_campaign_evidence.py"
spec = importlib.util.spec_from_file_location("p184", MOD_PATH)
assert spec and spec.loader
p184 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p184)


class Phase184CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_root = self.root / "runs"
        self.run_root.mkdir()
        self.row = {
            "run_id": "R001",
            "branch": "SIDM2v",
            "group": "core_blind_production",
            "resolution_tier": "R3_gold",
            "seed": "17",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def runtime_report(self):
        return {
            "phase": 187,
            "status": "PASS",
            "energy_drift_abs_max": 0.002,
            "momentum_drift_abs_max": 2.5e-5,
            "energy_statistics_rows": 321,
            "energy_source_sha256": "energysha",
        }

    def test_collect_one_builds_frozen_run_summary_without_mutating_run_dir(self):
        run_dir = self.run_root / "R001"
        run_dir.mkdir()
        post_path = run_dir / "phase175_POST.json"
        post_path.write_text("{}\n")
        log_path = run_dir / "gizmo.log"
        log_path.write_text("log\n")
        info = {
            "run_id": "R001",
            "run_dir": run_dir,
            "post_path": post_path,
            "post": {"executable_sha256": "exe", "ic_sha256": "ic"},
            "integrity": {"run_directory_sha256": "dirsha"},
            "ic": self.root / "ic.dat",
            "log": log_path,
            "log_sha256": p184.sha256_file(log_path),
        }
        profile_rows = [{"run_id": "R001"}]
        profile_report = {
            "status": "PASS",
            "run_id": "R001",
            "source_snapshots": [{"time_Gyr": 80.0, "sha256": "snap80"}],
        }
        collision_rows = [{"run_id": "R001", "channel": "HL"}]
        collision_report = {
            "status": "PASS",
            "run_id": "R001",
            "source_log_sha256": info["log_sha256"],
        }
        before = sorted(p.name for p in run_dir.iterdir())
        with mock.patch.object(
            p184.p181_profile, "build_profiles", return_value=(profile_rows, profile_report)
        ), mock.patch.object(
            p184.p181_collision, "summarize", return_value=(collision_rows, collision_report)
        ), mock.patch.object(
            p184.p187, "analyze_run", return_value=self.runtime_report()
        ):
            summary, profiles, collisions, detail = p184.collect_one(self.row, info)
        after = sorted(p.name for p in run_dir.iterdir())

        self.assertEqual(before, after)
        self.assertEqual(summary["status"], "COMPLETE")
        self.assertEqual(float(summary["final_time_Gyr"]), 80.0)
        self.assertEqual(summary["profile_80Gyr_snapshot_sha256"], "snap80")
        self.assertEqual(summary["collision_source_log_sha256"], info["log_sha256"])
        self.assertAlmostEqual(float(summary["energy_drift_abs_max"]), 0.002)
        self.assertAlmostEqual(float(summary["momentum_drift_abs_max"]), 2.5e-5)
        self.assertEqual(int(summary["energy_statistics_rows"]), 321)
        self.assertEqual(summary["energy_source_sha256"], "energysha")
        self.assertEqual(profiles, profile_rows)
        self.assertEqual(collisions, collision_rows)
        self.assertEqual(detail["run_directory_sha256"], "dirsha")
        self.assertAlmostEqual(detail["energy_drift_abs_max"], 0.002)

    def test_collect_one_rejects_missing_verified_80_gyr_source(self):
        run_dir = self.run_root / "R001"
        run_dir.mkdir()
        post_path = run_dir / "phase175_POST.json"
        post_path.write_text("{}\n")
        log_path = run_dir / "gizmo.log"
        log_path.write_text("log\n")
        info = {
            "run_id": "R001",
            "run_dir": run_dir,
            "post_path": post_path,
            "post": {},
            "integrity": {"run_directory_sha256": "dirsha"},
            "ic": self.root / "ic.dat",
            "log": log_path,
            "log_sha256": p184.sha256_file(log_path),
        }
        with mock.patch.object(
            p184.p181_profile,
            "build_profiles",
            return_value=([], {
                "status": "PASS",
                "run_id": "R001",
                "source_snapshots": [{"time_Gyr": 55.28, "sha256": "x"}],
            }),
        ):
            with self.assertRaises(p184.CollectionError):
                p184.collect_one(self.row, info)

    def test_collect_one_rejects_incomplete_runtime_invariant_report(self):
        run_dir = self.run_root / "R001"
        run_dir.mkdir()
        post_path = run_dir / "phase175_POST.json"
        post_path.write_text("{}\n")
        log_path = run_dir / "gizmo.log"
        log_path.write_text("log\n")
        info = {
            "run_id": "R001",
            "run_dir": run_dir,
            "post_path": post_path,
            "post": {},
            "integrity": {"run_directory_sha256": "dirsha"},
            "ic": self.root / "ic.dat",
            "log": log_path,
            "log_sha256": p184.sha256_file(log_path),
        }
        profile_report = {
            "status": "PASS", "run_id": "R001",
            "source_snapshots": [{"time_Gyr": 80.0, "sha256": "snap80"}],
        }
        collision_report = {
            "status": "PASS", "run_id": "R001",
            "source_log_sha256": info["log_sha256"],
        }
        with mock.patch.object(
            p184.p181_profile, "build_profiles", return_value=([], profile_report)
        ), mock.patch.object(
            p184.p181_collision, "summarize", return_value=([], collision_report)
        ), mock.patch.object(
            p184.p187, "analyze_run", return_value={"status": "FAIL"}
        ):
            with self.assertRaises(p184.CollectionError):
                p184.collect_one(self.row, info)

    def test_preflight_rejects_completion_identity_drift(self):
        run_dir = self.run_root / "R001"
        run_dir.mkdir()
        post_path = run_dir / "phase175_POST.json"
        post = {
            "run_id": "WRONG",
            "status": "COMPLETE",
            "manifest_sha256": p184.EXPECTED_MANIFEST_SHA256,
            "manifest_row": self.row,
            "completion_marker": True,
            "fatal_marker": False,
            "required_snapshot_count": 10,
            "snapshot_count": 10,
        }
        with mock.patch.object(p184.p174, "completion_record", return_value=(post_path, post)):
            with self.assertRaises(p184.CollectionError):
                p184.preflight_one(self.row, self.run_root, {})

    def test_refuses_to_overwrite_final_evidence(self):
        out = self.root / "evidence"
        out.mkdir()
        (out / "run_summary.csv").write_text("existing\n")
        with self.assertRaises(p184.CollectionError):
            p184._refuse_existing(out)


if __name__ == "__main__":
    unittest.main()
