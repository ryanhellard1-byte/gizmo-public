#!/usr/bin/env python3
import importlib.util
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "d3" / "production"
MOD_PATH = PROD / "phase175_safe_resume.py"
spec = importlib.util.spec_from_file_location("phase175_safe_resume", MOD_PATH)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def row(run_id="R", times="0,0.25,0.5,1,2,5,10,20,40,55.28,80"):
    return {"run_id": run_id, "analysis_times_Gyr": times}


def write_minimal_params(run_dir: Path, base="restart", output_dir=None):
    params = run_dir / "params.txt"
    out = str(run_dir.resolve()) + "/" if output_dir is None else output_dir
    params.write_text(f"OutputDir {out}\nRestartFile {base}\n")
    return params


def make_restart_set(run_dir: Path, n: int, backup=False, base="restart"):
    rd = run_dir / "restartfiles"
    rd.mkdir(parents=True, exist_ok=True)
    suffix = ".bak" if backup else ""
    for i in range(n):
        (rd / f"{base}.{i}{suffix}").write_bytes(f"task-{i}".encode())


def fake_runner(path: Path):
    path.write_text("""#!/usr/bin/env python3
import pathlib, sys
params = pathlib.Path(sys.argv[1])
flag = int(sys.argv[2])
vals = {}
for line in params.read_text().splitlines():
    p=line.split(None,1)
    if len(p)==2: vals[p[0]]=p[1]
out=pathlib.Path(vals['OutputDir'])
if flag == 0:
    rd=out/'restartfiles'; rd.mkdir(exist_ok=True)
    (rd/'restart.0').write_bytes(b'restart-state')
    print('reaching time-limit. stopping.')
else:
    for i in range(10):
        (out/f'snapshot_{i:03d}').write_bytes(b'snap')
    rd=out/'restartfiles'; rd.mkdir(exist_ok=True)
    (rd/'restart.0').write_bytes(b'final-restart-state')
    print('Final time=81.817 reached. Simulation ends.')
""")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Phase175SafeResumeTests(unittest.TestCase):
    def test_resolve_mpi_tasks(self):
        self.assertEqual(m.resolve_mpi_tasks(8, "srun", {}), 8)
        self.assertEqual(m.resolve_mpi_tasks(None, "srun", {"SLURM_NTASKS": "64"}), 64)
        self.assertEqual(m.resolve_mpi_tasks(None, "mpirun -np 16", {}), 16)
        self.assertEqual(m.resolve_mpi_tasks(None, "", {}), 1)
        with self.assertRaises(m.ResumeError):
            m.resolve_mpi_tasks(None, "srun", {})
        with self.assertRaises(m.ResumeError):
            m.resolve_mpi_tasks(8, "srun", {"SLURM_NTASKS": "4"})
        with self.assertRaises(m.ResumeError):
            m.resolve_mpi_tasks(None, "mpirun -np 8", {"SLURM_NTASKS": "4"})
        with self.assertRaises(m.ResumeError):
            m.resolve_mpi_tasks(8, "mpirun -np 4", {})

    def test_restart_path_capacity_fails_before_c_buffer_overflow(self):
        safe = m.validate_restart_path_capacity_values("/tmp/d3/", "restart", 64)
        self.assertLess(safe["longest_restart_path_bytes"], m.GIZMO_RESTART_PATH_BUFFER_BYTES)
        too_long = "/tmp/" + ("x" * 190) + "/"
        with self.assertRaises(m.ResumeError):
            m.validate_restart_path_capacity_values(too_long, "restart", 64)

    def test_regular_restart_set_exact(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 4)
            result = m.validate_restart_set(run, 4)
            self.assertEqual(result["chosen_set"], "regular")
            self.assertEqual(len(result["files"]), 4)
            self.assertTrue(all(len(x["sha256"]) == 64 for x in result["files"]))

    def test_backup_only_restart_set_is_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 2, backup=True)
            result = m.validate_restart_set(run, 2)
            self.assertEqual(result["chosen_set"], "backup")

    def test_missing_restart_task_fails(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 3)
            with self.assertRaises(m.ResumeError):
                m.validate_restart_set(run, 4)

    def test_changed_mpi_size_fails_on_extra_task_file(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 4)
            with self.assertRaises(m.ResumeError):
                m.validate_restart_set(run, 2)

    def test_zero_length_restart_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 2)
            (run / "restartfiles" / "restart.1").write_bytes(b"")
            with self.assertRaises(m.ResumeError):
                m.validate_restart_set(run, 2)

    def test_strange_restart_like_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 1)
            (run / "restartfiles" / "restart.BAD").write_bytes(b"x")
            with self.assertRaises(m.ResumeError):
                m.validate_restart_set(run, 1)

    def test_complete_record_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / m.STATE_NAME).write_text(json.dumps({"status": "COMPLETE"}))
            complete, _, source = m.post_is_complete(run)
            self.assertTrue(complete)
            self.assertEqual(source, m.STATE_NAME)

    def test_fatal_previous_record_blocks_automatic_resume(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "phase173_POST.json").write_text(
                json.dumps({"status": "FAILED", "fatal_marker": True})
            )
            self.assertIsNotNone(m.prior_fatal_failure(run))

    def test_attempt_number_does_not_reuse_unpaired_begin(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / m.ATTEMPTS_NAME).write_text(
                json.dumps({"event": "BEGIN", "attempt": 1}) + "\n"
            )
            self.assertEqual(m.attempt_number(run), 2)

    def test_resume_requires_recorded_pause_and_exact_checkpoint_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 1)
            with self.assertRaises(m.ResumeError):
                m.authorize_resume(run, 1)

            restart = m.validate_restart_set(run, 1)
            state = {
                "status": "PAUSED_RESTARTABLE",
                "mpi_tasks": 1,
                "restart_after": restart,
            }
            (run / m.STATE_NAME).write_text(json.dumps(state))
            self.assertEqual(m.authorize_resume(run, 1)["chosen_set"], "regular")

            (run / "restartfiles" / "restart.0").write_bytes(b"changed-checkpoint")
            with self.assertRaises(m.ResumeError):
                m.authorize_resume(run, 1)

    def test_failed_state_never_authorizes_automatic_resume(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            write_minimal_params(run)
            make_restart_set(run, 1)
            restart = m.validate_restart_set(run, 1)
            (run / m.STATE_NAME).write_text(json.dumps({
                "status": "FAILED", "mpi_tasks": 1, "restart_after": restart,
            }))
            with self.assertRaises(m.ResumeError):
                m.authorize_resume(run, 1)

    def test_fresh_pause_then_resume_complete_and_detect_output_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "R"
            run.mkdir()
            write_minimal_params(run)
            (run / "output_times.txt").write_text("dummy\n")
            (run / "render_metadata.json").write_text("{}\n")
            exe = Path(td) / "fake_gizmo.py"
            fake_runner(exe)
            pre = {
                "provenance": {"test": True},
                "executable_sha256": m.sha256_file(exe),
                "ic": str(Path(td) / "ic.dat"),
                "ic_sha256": "x",
                "params_sha256": m.sha256_file(run / "params.txt"),
                "output_times_sha256": m.sha256_file(run / "output_times.txt"),
                "render_metadata_sha256": m.sha256_file(run / "render_metadata.json"),
            }
            r = row()

            rc0 = m.execute_attempt(run, r, exe, pre, "", 1, 0)
            self.assertEqual(rc0, 0)
            paused = json.loads((run / m.STATE_NAME).read_text())
            self.assertEqual(paused["status"], "PAUSED_RESTARTABLE")
            self.assertEqual(paused["restart_flag"], 0)
            self.assertTrue((run / "restartfiles" / "restart.0").is_file())
            m.authorize_resume(run, 1)

            rc1 = m.execute_attempt(run, r, exe, pre, "", 1, 1)
            self.assertEqual(rc1, 0)
            complete = json.loads((run / m.STATE_NAME).read_text())
            self.assertEqual(complete["status"], "COMPLETE")
            self.assertEqual(complete["restart_flag"], 1)
            self.assertEqual(complete["snapshot_count"], 10)
            self.assertEqual(
                m.verify_completion_integrity(run, complete, m.STATE_NAME)["file_count"],
                len(complete["file_hashes"]),
            )
            log = (run / "gizmo.log").read_text()
            self.assertIn("PHASE175 ATTEMPT 2 RESTART_FLAG=1", log)
            lines = [x for x in (run / m.ATTEMPTS_NAME).read_text().splitlines() if x.strip()]
            self.assertEqual(len(lines), 4)

            (run / "snapshot_005").write_bytes(b"tampered")
            with self.assertRaises(m.ResumeError):
                m.verify_completion_integrity(run, complete, m.STATE_NAME)

    def test_nonzero_resume_is_failed_even_if_old_restart_survives(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "R"
            run.mkdir()
            write_minimal_params(run)
            make_restart_set(run, 1)
            prior = m.validate_restart_set(run, 1)
            (run / m.STATE_NAME).write_text(json.dumps({
                "status": "PAUSED_RESTARTABLE", "mpi_tasks": 1, "restart_after": prior,
            }))
            exe = Path(td) / "bad.py"
            exe.write_text("#!/usr/bin/env python3\nimport sys\nprint('crash')\nsys.exit(7)\n")
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
            pre = {
                "provenance": {},
                "executable_sha256": m.sha256_file(exe),
                "ic": "x",
                "ic_sha256": "x",
                "params_sha256": m.sha256_file(run / "params.txt"),
                "output_times_sha256": "x",
                "render_metadata_sha256": "x",
            }
            m.authorize_resume(run, 1)
            rc = m.execute_attempt(run, row(), exe, pre, "", 1, 1)
            self.assertEqual(rc, 7)
            state = json.loads((run / m.STATE_NAME).read_text())
            self.assertEqual(state["status"], "FAILED")
            with self.assertRaises(m.ResumeError):
                m.authorize_resume(run, 1)

    def test_lock_is_kernel_released_not_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            with m.run_lock(run):
                self.assertTrue((run / m.LOCK_NAME).is_file())
            with m.run_lock(run):
                self.assertTrue((run / m.LOCK_NAME).is_file())


if __name__ == "__main__":
    unittest.main()
