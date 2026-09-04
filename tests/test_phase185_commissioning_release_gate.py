#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "d3" / "production"))

import phase184_campaign_evidence as p184
import phase185_commissioning_evidence as p185
import phase185_machine_batch_submit as batch
import phase185_safe_resume as wrapper


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CommissioningEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_root = self.root / "runs"
        self.evidence_root = self.root / "commissioning-evidence"
        self.run_root.mkdir()
        self.row = {
            "run_id": "C001",
            "branch": "SIDM2v",
            "group": "commissioning",
            "resolution_tier": "R0",
            "seed": "185001",
            "blind_analysis": "false",
        }
        self.blind = {**self.row, "run_id": "B001", "blind_analysis": "true"}
        self.run_dir = self.run_root / "C001"
        self.run_dir.mkdir()
        self.post = self.run_dir / "phase175_POST.json"
        self.post.write_text('{"status":"COMPLETE"}\n')
        self.log = self.run_dir / "gizmo.log"
        self.log.write_text("log\n")
        self.exe = self.root / "exe"
        self.exe.write_bytes(b"exe")
        self.att = self.root / "att.json"
        self.att.write_text("{}\n")
        self.info = {
            "post_path": self.post,
            "post": {"executable_sha256": sha(self.exe)},
            "run_dir": self.run_dir,
            "integrity": {"run_directory_sha256": "raw-digest"},
            "log": self.log,
            "log_sha256": sha(self.log),
            "ic": self.root / "ic.dat",
        }
        self.att_obj = {"evidence_executable_sha256": sha(self.exe)}
        self.summary = {column: "" for column in p184.RUN_COLUMNS}
        self.summary.update({
            "run_id": "C001", "branch": "SIDM2v", "group": "commissioning",
            "resolution_tier": "R0", "seed": "185001", "status": "COMPLETE",
            "final_time_Gyr": "80",
        })
        self.profiles = [{column: "" for column in p184.p181_profile.PROFILE_COLUMNS}]
        self.profiles[0]["run_id"] = "C001"
        self.collisions = [{column: "" for column in p184.p181_collision.OUTPUT_COLUMNS}]
        self.collisions[0]["run_id"] = "C001"
        self.detail = {"profile_80Gyr_snapshot_sha256": "snap80"}

    def tearDown(self):
        self.tmp.cleanup()

    def campaign_patch(self):
        return mock.patch.object(
            p185, "campaign_rows", return_value=([self.row, self.blind], [self.row], [self.blind])
        )

    def test_blind_row_is_refused_by_finalizer(self):
        with self.campaign_patch():
            with self.assertRaisesRegex(p185.CommissioningEvidenceError, "refusing per-run derived evidence for blind row"):
                p185.commissioning_row("B001")

    def test_commissioning_finalize_is_atomic_idempotent_and_hash_checked(self):
        with self.campaign_patch(), \
             mock.patch.object(p185, "current_raw", return_value=(self.row, self.att_obj, self.info)), \
             mock.patch.object(p185.p184, "collect_one", return_value=(self.summary, self.profiles, self.collisions, self.detail)):
            first = p185.finalize("C001", self.run_root, self.evidence_root, self.exe, self.att)
            self.assertEqual(first["status"], "PASS")
            edir = self.evidence_root / "C001"
            self.assertTrue((edir / p185.FINAL_RECORD).is_file())
            second = p185.finalize("C001", self.run_root, self.evidence_root, self.exe, self.att)
            self.assertEqual(second["status"], "ALREADY_FINALIZED")
            (edir / p185.PROFILES).write_text("corrupt\n")
            with self.assertRaisesRegex(p185.CommissioningEvidenceError, "artifact changed"):
                p185.verify_finalized(edir, self.run_root, "C001", self.exe, self.att)


class BlindBoundaryWrapperTests(unittest.TestCase):
    def args(self, root: Path, run_id: str = "B001"):
        return SimpleNamespace(
            command="dispatch",
            machine_attestation=str(root / "att.json"),
            evidence_root=str(root / "evidence"),
            run_id=run_id,
            executable=str(root / "exe"),
            run_root=str(root / "runs"),
            mpi_prefix="",
            mpi_tasks=1,
            ic_root=str(root / "ics"),
            max_mem_mb=3500,
            time_limit_cpu=170000,
            no_generate_ic=False,
        )

    def test_completed_blind_run_never_calls_per_run_finalizer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runs" / "B001").mkdir(parents=True)
            args = self.args(root)
            with mock.patch.object(wrapper, "row_class", return_value="blind"), \
                 mock.patch.object(wrapper.p175, "post_is_complete", return_value=(True, {}, "phase175_POST.json")), \
                 mock.patch.object(wrapper.p185, "finalize") as finalize:
                self.assertEqual(wrapper.handle_success(args), 0)
                finalize.assert_not_called()
                self.assertFalse((root / "evidence" / "B001").exists())

    def test_existing_blind_per_run_evidence_is_a_hard_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runs" / "B001").mkdir(parents=True)
            (root / "evidence" / "B001").mkdir(parents=True)
            args = self.args(root)
            with mock.patch.object(wrapper, "row_class", return_value="blind"), \
                 mock.patch.object(wrapper.p175, "post_is_complete", return_value=(True, {}, "phase175_POST.json")):
                with self.assertRaisesRegex(wrapper.DispatchError, "blind per-run evidence exists"):
                    wrapper.handle_success(args)

    def test_completed_commissioning_run_is_finalized(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runs" / "C001").mkdir(parents=True)
            args = self.args(root, "C001")
            with mock.patch.object(wrapper, "row_class", return_value="commissioning"), \
                 mock.patch.object(wrapper.p175, "post_is_complete", return_value=(True, {}, "phase175_POST.json")), \
                 mock.patch.object(wrapper.p185, "finalize", return_value={"status": "PASS"}) as finalize:
                self.assertEqual(wrapper.handle_success(args), 0)
                finalize.assert_called_once()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_root = self.root / "runs"
        self.evidence_root = self.root / "evidence"
        self.run_root.mkdir()
        self.evidence_root.mkdir()
        self.exe = self.root / "exe"
        self.exe.write_bytes(b"exe")
        self.att = self.root / "att.json"
        self.att.write_bytes(b"att")
        self.exe_sha = sha(self.exe)
        self.commissioning = [{"run_id": f"C{i}"} for i in range(8)]
        self.blind = [{"run_id": f"B{i}"} for i in range(119)]
        self.current = {}
        records = []
        for i, row in enumerate(self.commissioning):
            rid = row["run_id"]
            edir = self.evidence_root / rid
            edir.mkdir()
            record_path = edir / p185.FINAL_RECORD
            record_path.write_text(json.dumps({"run_id": rid, "version": 1}) + "\n")
            current = {
                "raw_run_directory_sha256": f"raw-{i}",
                "artifacts": {"profiles.csv": f"profiles-{i}"},
            }
            self.current[rid] = current
            records.append({
                "run_id": rid,
                "finalization_record_sha256": sha(record_path),
                "raw_run_directory_sha256": current["raw_run_directory_sha256"],
                "artifacts": current["artifacts"],
            })
        self.proof = {
            "phase": 185,
            "status": "PASS",
            "manifest_sha256": batch.p181.p174.EXPECTED_MANIFEST_SHA256,
            "commissioning_runs": 8,
            "complete_runs": 8,
            "finalized_commissioning_runs": 8,
            "run_ids": [r["run_id"] for r in self.commissioning],
            "machine_attestation_sha256": sha(self.att),
            "evidence_executable_sha256": self.exe_sha,
            "d3_equivalence_status": "PASS",
            "standard_equal_label_equivalence_status": "PASS",
            "finalization_records": records,
        }
        self.proof_path = self.root / "proof.json"
        self.proof_path.write_text(json.dumps(self.proof))
        self.att_obj = {"evidence_executable_sha256": self.exe_sha}

    def tearDown(self):
        self.tmp.cleanup()

    def verify_current(self, evidence_dir, run_root, rid, executable, attestation):
        return self.current[rid]

    def test_blind_unlock_reverifies_all_eight_current_commissioning_records(self):
        with mock.patch.object(batch.p185, "verify_finalized", side_effect=self.verify_current) as verify:
            proof = batch.load_commissioning_proof(
                self.proof_path, self.commissioning, self.blind, self.att_obj,
                self.att, self.exe, self.run_root, self.evidence_root,
            )
            self.assertEqual(proof["status"], "PASS")
            self.assertEqual(verify.call_count, 8)

    def test_stale_pass_proof_is_rejected(self):
        changed = self.evidence_root / "C3" / p185.FINAL_RECORD
        changed.write_text(json.dumps({"run_id": "C3", "version": 2}) + "\n")
        with mock.patch.object(batch.p185, "verify_finalized", side_effect=self.verify_current):
            with self.assertRaisesRegex(batch.BatchError, "changed since PASS proof"):
                batch.load_commissioning_proof(
                    self.proof_path, self.commissioning, self.blind, self.att_obj,
                    self.att, self.exe, self.run_root, self.evidence_root,
                )

    def test_any_blind_per_run_evidence_blocks_release(self):
        (self.evidence_root / "B77").mkdir()
        with self.assertRaisesRegex(batch.BatchError, "blind per-run derived evidence exists"):
            batch.verify_blind_evidence_absent(self.evidence_root, self.blind)

    def test_scheduler_routes_through_phase185_wrapper(self):
        args = SimpleNamespace(
            machine_attestation=str(self.att), evidence_root=str(self.evidence_root),
            executable=str(self.exe), ic_root=str(self.root / "ics"), run_root=str(self.run_root),
            mpi_prefix="srun", mpi_tasks=4, no_generate_ic=False, max_mem_mb=3500,
            time_limit_cpu=170000,
        )
        job = self.root / "job.slurm"
        batch.write_job(job, {"run_id": "C0"}, args, ["--nodes=1", "--ntasks=4"])
        text = job.read_text()
        self.assertIn("phase185_safe_resume.py", text)
        self.assertIn("--evidence-root", text)
        self.assertIn("--mpi-tasks 4", text)


if __name__ == "__main__":
    unittest.main()
