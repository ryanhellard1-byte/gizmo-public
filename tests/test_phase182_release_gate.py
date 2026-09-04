import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "d3" / "production"))

import phase182_machine_batch_submit as batch
import phase182_finalize_run as finalizer


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.run_root = self.root / "runs"
        self.evidence_root = self.root / "evidence"
        self.run_root.mkdir()
        self.evidence_root.mkdir()
        self.exe = self.root / "exe"
        self.att = self.root / "att.json"
        self.exe.write_bytes(b"evidence-exe")
        self.att.write_bytes(b"machine-attestation")
        self.exe_sha = sha(self.exe)
        self.commissioning = [{"run_id": f"RID{i}"} for i in range(8)]
        self.current = {}
        records = []
        for i, row in enumerate(self.commissioning):
            rid = row["run_id"]
            edir = self.evidence_root / rid
            edir.mkdir()
            record_path = edir / finalizer.FINAL_RECORD
            record_path.write_text(json.dumps({"run_id": rid, "version": 1}) + "\n")
            current = {
                "raw_run_directory_sha256": f"raw-{i}",
                "artifacts": {"profiles.csv": f"profile-{i}"},
            }
            self.current[rid] = current
            records.append({
                "run_id": rid,
                "finalization_record_sha256": sha(record_path),
                "raw_run_directory_sha256": current["raw_run_directory_sha256"],
                "artifacts": current["artifacts"],
            })
        self.proof = {
            "phase": 182,
            "status": "PASS",
            "manifest_sha256": batch.p181.p174.EXPECTED_MANIFEST_SHA256,
            "commissioning_runs": 8,
            "complete_runs": 8,
            "finalized_runs": 8,
            "run_ids": [r["run_id"] for r in self.commissioning],
            "machine_attestation_sha256": sha(self.att),
            "evidence_executable_sha256": self.exe_sha,
            "finalization_records": records,
        }
        self.proof_path = self.root / "proof.json"
        self.proof_path.write_text(json.dumps(self.proof))
        self.att_obj = {"evidence_executable_sha256": self.exe_sha}

    def tearDown(self):
        self.td.cleanup()

    def verify_current(self, evidence_dir, run_root, rid, executable, machine_attestation):
        return self.current[rid]

    def test_blind_unlock_reverifies_all_current_finalizations(self):
        with mock.patch.object(batch.finalizer, "verify_finalized", side_effect=self.verify_current) as verify:
            result = batch.load_commissioning_proof(
                self.proof_path,
                self.commissioning,
                self.att_obj,
                self.att,
                self.exe,
                self.run_root,
                self.evidence_root,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(verify.call_count, 8)

    def test_stale_pass_proof_cannot_unlock_after_record_change(self):
        changed = self.evidence_root / "RID3" / finalizer.FINAL_RECORD
        changed.write_text(json.dumps({"run_id": "RID3", "version": 2}) + "\n")
        with mock.patch.object(batch.finalizer, "verify_finalized", side_effect=self.verify_current):
            with self.assertRaises(batch.BatchError):
                batch.load_commissioning_proof(
                    self.proof_path,
                    self.commissioning,
                    self.att_obj,
                    self.att,
                    self.exe,
                    self.run_root,
                    self.evidence_root,
                )

    def test_current_artifact_corruption_blocks_blind_unlock(self):
        def fail_one(evidence_dir, run_root, rid, executable, machine_attestation):
            if rid == "RID5":
                raise finalizer.FinalizeError("artifact hash mismatch")
            return self.current[rid]

        with mock.patch.object(batch.finalizer, "verify_finalized", side_effect=fail_one):
            with self.assertRaises(finalizer.FinalizeError):
                batch.load_commissioning_proof(
                    self.proof_path,
                    self.commissioning,
                    self.att_obj,
                    self.att,
                    self.exe,
                    self.run_root,
                    self.evidence_root,
                )


if __name__ == "__main__":
    unittest.main()
