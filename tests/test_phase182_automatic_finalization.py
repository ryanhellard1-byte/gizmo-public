import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "d3" / "production"))

import phase181_collision_summary as collision
import phase181_profile_extract as profile
import phase182_campaign_assemble as assemble
import phase182_finalize_run as finalizer
import phase182_machine_batch_submit as batch
import phase182_safe_resume as wrapper


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FinalizerTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.run_root = self.root / "runs"
        self.evidence_root = self.root / "evidence"
        self.rid = "PH182-TEST"
        self.run_dir = self.run_root / self.rid
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "raw.bin").write_bytes(b"immutable-raw")
        (self.run_dir / "gizmo.log").write_text("Final time=1 reached. Simulation ends.\n")
        self.exe = self.root / "GIZMO_D3_EVIDENCE"
        self.exe.write_bytes(b"exe")
        self.att = self.root / "attestation.json"
        self.att.write_text("{}\n")
        self.row = {
            "run_id": self.rid,
            "branch": "SIDM2v",
            "group": "commissioning",
            "resolution_tier": "R0",
            "seed": "182001",
        }
        self.pre = {"ic": str(self.root / "ic.dat")}
        Path(self.pre["ic"]).write_bytes(b"ic")
        self.raw_digest = "a" * 64
        self.raw_state = {
            "run_dir": self.run_dir,
            "prelaunch": self.pre,
            "post": {"executable_sha256": sha(self.exe)},
            "completion_record": "phase175_POST.json",
            "completion_record_path": self.run_dir / "phase175_POST.json",
            "integrity": {"run_directory_sha256": self.raw_digest},
            "provenance": {},
        }
        self.raw_state["completion_record_path"].write_text('{"status":"COMPLETE"}\n')
        self.profile_rows = [{k: "1" for k in profile.PROFILE_COLUMNS}]
        self.profile_rows[0].update({"run_id": self.rid, "species": "H"})
        self.profile_report = {
            "status": "PASS",
            "run_id": self.rid,
            "source_snapshots": [{"path": str(self.root / "snapshot_final")}],
        }
        self.collision_rows = [{k: "0" for k in collision.OUTPUT_COLUMNS}]
        self.collision_rows[0].update({"run_id": self.rid, "channel": "NONE"})
        self.collision_report = {"status": "PASS", "run_id": self.rid}

    def tearDown(self):
        self.td.cleanup()

    def patches(self):
        return (
            mock.patch.object(finalizer, "frozen_campaign", return_value=(b"manifest", [self.row])),
            mock.patch.object(finalizer, "verify_raw_completion", return_value=self.raw_state),
            mock.patch.object(finalizer.profile, "load_manifest", return_value=self.row),
            mock.patch.object(finalizer.profile, "build_profiles", return_value=(self.profile_rows, self.profile_report)),
            mock.patch.object(finalizer.collision, "load_manifest", return_value=([], [self.row])),
            mock.patch.object(finalizer.collision, "find_manifest_row", return_value=self.row),
            mock.patch.object(finalizer.collision, "summarize", return_value=(self.collision_rows, self.collision_report)),
            mock.patch.object(finalizer, "observed_final_time_gyr", return_value=80.0),
        )

    def test_finalize_is_external_atomic_and_idempotent(self):
        raw_before = {p.name: sha(p) for p in self.run_dir.iterdir() if p.is_file()}
        patches = self.patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
            result = finalizer.finalize(
                self.rid, self.run_root, self.evidence_root, self.exe, self.att
            )
            self.assertEqual(result["status"], "PASS")
            evidence_dir = self.evidence_root / self.rid
            self.assertTrue((evidence_dir / finalizer.FINAL_RECORD).is_file())
            raw_after = {p.name: sha(p) for p in self.run_dir.iterdir() if p.is_file()}
            self.assertEqual(raw_before, raw_after)

            second = finalizer.finalize(
                self.rid, self.run_root, self.evidence_root, self.exe, self.att
            )
            self.assertEqual(second["status"], "ALREADY_FINALIZED")

            (evidence_dir / finalizer.PROFILES).write_text("corrupt\n")
            with self.assertRaises(finalizer.FinalizeError):
                finalizer.verify_finalized(
                    evidence_dir, self.run_root, self.rid, self.exe, self.att
                )

    def test_refuses_evidence_inside_own_raw_run_directory(self):
        with mock.patch.object(finalizer, "frozen_campaign", return_value=(b"manifest", [self.row])):
            with self.assertRaises(finalizer.FinalizeError):
                finalizer.finalize(
                    self.rid, self.run_root, self.run_root, self.exe, self.att
                )

    def test_refuses_evidence_inside_different_raw_run_directory(self):
        other = {**self.row, "run_id": "PH182-OTHER"}
        other_dir = self.run_root / other["run_id"]
        other_dir.mkdir(parents=True)
        bad_evidence_root = other_dir / "derived"
        with mock.patch.object(finalizer, "frozen_campaign", return_value=(b"manifest", [self.row, other])):
            with self.assertRaisesRegex(finalizer.FinalizeError, "outside every fingerprinted raw run"):
                finalizer.finalize(
                    self.rid, self.run_root, bad_evidence_root, self.exe, self.att
                )


class WrapperTests(unittest.TestCase):
    def args(self, root: Path):
        return SimpleNamespace(
            command="dispatch",
            machine_attestation=str(root / "att.json"),
            evidence_root=str(root / "evidence"),
            run_id="RID",
            executable=str(root / "exe"),
            run_root=str(root / "runs"),
            mpi_prefix="",
            mpi_tasks=1,
            ic_root=str(root / "ics"),
            max_mem_mb=3500,
            time_limit_cpu=170000,
            no_generate_ic=False,
        )

    def test_pause_does_not_finalize(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / "runs" / "RID"
            run_dir.mkdir(parents=True)
            (run_dir / "phase175_POST.json").write_text('{"status":"PAUSED_RESTARTABLE"}\n')
            args = self.args(root)
            with mock.patch.object(wrapper.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                 mock.patch.object(wrapper.p175, "post_is_complete", return_value=(False, None, None)), \
                 mock.patch.object(wrapper.finalizer, "finalize") as fin:
                self.assertEqual(wrapper.dispatch(args), 0)
                fin.assert_not_called()

    def test_complete_auto_finalizes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "runs" / "RID").mkdir(parents=True)
            args = self.args(root)
            with mock.patch.object(wrapper.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                 mock.patch.object(wrapper.p175, "post_is_complete", return_value=(True, {}, "phase175_POST.json")), \
                 mock.patch.object(wrapper.finalizer, "finalize", return_value={"status": "PASS", "evidence_dir": "/e/RID"}) as fin:
                self.assertEqual(wrapper.dispatch(args), 0)
                fin.assert_called_once()


class SchedulerAndAssemblerTests(unittest.TestCase):
    def test_scheduler_routes_jobs_through_phase182_wrapper(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            att = root / "att.json"
            exe = root / "exe"
            att.write_text("{}")
            exe.write_text("x")
            args = SimpleNamespace(
                machine_attestation=str(att),
                evidence_root=str(root / "evidence"),
                executable=str(exe),
                ic_root=str(root / "ics"),
                run_root=str(root / "runs"),
                mpi_prefix="srun",
                mpi_tasks=4,
                no_generate_ic=False,
                max_mem_mb=3500,
                time_limit_cpu=170000,
            )
            job = root / "job.slurm"
            batch.write_job(job, {"run_id": "RID"}, args, ["--nodes=1", "--ntasks=4"])
            text = job.read_text()
            self.assertIn("phase182_safe_resume.py", text)
            self.assertIn("--evidence-root", text)
            self.assertIn("--mpi-tasks 4", text)

    def test_csv_concatenation_rejects_schema_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a, b, out = root / "a.csv", root / "b.csv", root / "out.csv"
            a.write_text("x,y\n1,2\n")
            b.write_text("x,z\n3,4\n")
            with self.assertRaises(assemble.AssembleError):
                assemble.concatenate_csv([a, b], out)

    def test_campaign_assembly_refuses_less_than_127_frozen_rows(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(assemble.finalizer, "frozen_campaign", return_value=(b"x", [{"run_id": "RID"}])):
                with self.assertRaises(assemble.AssembleError):
                    assemble.assemble(
                        root / "runs", root / "evidence", root / "out", root / "exe", root / "att"
                    )

    def test_campaign_output_cannot_live_inside_any_raw_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_root = root / "runs"
            rows = [{"run_id": f"RID{i}"} for i in range(127)]
            bad_output = run_root / "RID73" / "campaign-ledger"
            with mock.patch.object(assemble.finalizer, "frozen_campaign", return_value=(b"x", rows)):
                with self.assertRaisesRegex(finalizer.FinalizeError, "outside every fingerprinted raw run"):
                    assemble.assemble(
                        run_root,
                        root / "evidence",
                        bad_output,
                        root / "exe",
                        root / "att",
                    )


if __name__ == "__main__":
    unittest.main()
