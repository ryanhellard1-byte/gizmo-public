#!/usr/bin/env python3
"""Phase175 fail-closed fresh/continue dispatcher for long Phase172 production runs.

Phase173 proves that a fresh launch is tied to the frozen manifest, exact GIZMO
binary, IC, and rendered parameters. Phase175 preserves that contract across
scheduler/CPU-time interruptions.

Fresh dispatch:
  - delegates preparation to Phase173;
  - executes GIZMO with RestartFlag=0;
  - classifies a clean time-limit/stop return with a valid restart set as
    PAUSED_RESTARTABLE rather than a physics failure.

Resume dispatch:
  - never regenerates an IC or re-renders parameters;
  - re-verifies the Phase173 prelaunch fingerprints and exact executable;
  - requires a prior PAUSED_RESTARTABLE authorization record;
  - requires the exact cryptographic checkpoint set recorded at that pause;
  - requires the same MPI task topology;
  - executes GIZMO with RestartFlag=1;
  - appends the log and writes an immutable attempt trail.

A changed experiment or unrecorded crash cannot be resumed automatically under
the same run directory.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase173_production_launcher as p173  # noqa: E402

PHASE = 175
STATE_NAME = "phase175_POST.json"
ATTEMPTS_NAME = "phase175_attempts.jsonl"
LOCK_NAME = ".phase175.lock"
GIZMO_RESTART_PATH_BUFFER_BYTES = 200


class ResumeError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> Dict:
    try:
        obj = json.loads(path.read_text())
    except Exception as exc:
        raise ResumeError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ResumeError(f"expected JSON object: {path}")
    return obj


def parse_prefix_tasks(prefix: str) -> int | None:
    tokens = shlex.split(prefix) if prefix.strip() else []
    for i, tok in enumerate(tokens):
        if tok in {"-n", "-np", "--ntasks"} and i + 1 < len(tokens):
            try:
                n = int(tokens[i + 1])
                return n if n > 0 else None
            except ValueError:
                return None
        for key in ("--ntasks=", "-np=", "-n="):
            if tok.startswith(key):
                try:
                    n = int(tok[len(key):])
                    return n if n > 0 else None
                except ValueError:
                    return None
    return None


def _positive_int(value: str, label: str) -> int:
    try:
        n = int(value)
    except ValueError as exc:
        raise ResumeError(f"invalid {label}={value!r}") from exc
    if n <= 0:
        raise ResumeError(f"invalid {label}={value!r}")
    return n


def resolve_mpi_tasks(explicit: int | None, mpi_prefix: str, env=None) -> int:
    """Resolve one MPI topology and reject contradictory sources."""
    env = os.environ if env is None else env
    slurm_text = str(env.get("SLURM_NTASKS", "")).strip()
    slurm = _positive_int(slurm_text, "SLURM_NTASKS") if slurm_text else None
    parsed = parse_prefix_tasks(mpi_prefix)

    if explicit is not None:
        if explicit <= 0:
            raise ResumeError("--mpi-tasks must be positive")
        if slurm is not None and slurm != explicit:
            raise ResumeError(
                f"MPI topology conflict: --mpi-tasks={explicit} but SLURM_NTASKS={slurm}"
            )
        if parsed is not None and parsed != explicit:
            raise ResumeError(
                f"MPI topology conflict: --mpi-tasks={explicit} but --mpi-prefix encodes {parsed}"
            )
        return explicit

    if slurm is not None:
        if parsed is not None and parsed != slurm:
            raise ResumeError(
                f"MPI topology conflict: SLURM_NTASKS={slurm} but --mpi-prefix encodes {parsed}"
            )
        return slurm
    if parsed is not None:
        return parsed
    if not mpi_prefix.strip():
        return 1
    raise ResumeError(
        "cannot prove MPI task count from --mpi-prefix; pass --mpi-tasks or provide SLURM_NTASKS"
    )


def read_params(path: Path) -> Dict[str, str]:
    return p173.read_params(path)


def validate_restart_path_capacity_values(output_dir: str, base: str, mpi_tasks: int) -> Dict:
    if mpi_tasks <= 0:
        raise ResumeError("MPI task count must be positive for restart path validation")
    if not output_dir:
        raise ResumeError("OutputDir missing while validating restart path capacity")
    if not base or "/" in base or "\\" in base:
        raise ResumeError(f"unsafe/invalid RestartFile={base!r}")
    candidate = f"{output_dir}/restartfiles/{base}.{mpi_tasks - 1}.bak2"
    encoded_bytes = len(os.fsencode(candidate))
    if encoded_bytes >= GIZMO_RESTART_PATH_BUFFER_BYTES:
        raise ResumeError(
            "GIZMO restart path would overflow restart.c's 200-byte buffer: "
            f"{encoded_bytes} bytes for {candidate!r}"
        )
    return {
        "longest_restart_path": candidate,
        "longest_restart_path_bytes": encoded_bytes,
        "buffer_bytes": GIZMO_RESTART_PATH_BUFFER_BYTES,
    }


def validate_restart_path_capacity(run_dir: Path, mpi_tasks: int) -> Dict:
    params = read_params(run_dir / "params.txt")
    return validate_restart_path_capacity_values(
        params.get("OutputDir", ""), params.get("RestartFile", "").strip(), mpi_tasks
    )


def critical_paths(run_dir: Path, pre: Dict) -> Dict[str, Path]:
    return {
        "params_sha256": run_dir / "params.txt",
        "output_times_sha256": run_dir / "output_times.txt",
        "render_metadata_sha256": run_dir / "render_metadata.json",
        "ic_sha256": Path(str(pre.get("ic", ""))),
    }


def verify_prelaunch(
    run_dir: Path,
    row: Dict[str, str],
    executable: Path,
    provenance: Dict,
) -> Dict:
    pre_path = run_dir / "phase173_PRELAUNCH.json"
    if not pre_path.is_file():
        raise ResumeError(f"{row['run_id']}: missing Phase173 prelaunch record")
    pre = load_json(pre_path)

    if pre.get("run_id") != row["run_id"]:
        raise ResumeError("prelaunch run_id mismatch")
    if pre.get("manifest_row") != row:
        raise ResumeError("prelaunch manifest row mismatch")
    if pre.get("manifest_sha256") != p173.EXPECTED_MANIFEST_SHA256:
        raise ResumeError("prelaunch manifest SHA mismatch")
    if pre.get("provenance") != provenance:
        raise ResumeError("prelaunch production provenance mismatch")

    observed_exe = p173.verify_executable(executable, provenance)
    if pre.get("executable_sha256") != observed_exe:
        raise ResumeError("prelaunch executable SHA mismatch")

    for key, path in critical_paths(run_dir, pre).items():
        if not path.is_file():
            raise ResumeError(f"critical resume input missing for {key}: {path}")
        observed = sha256_file(path)
        if pre.get(key) != observed:
            raise ResumeError(
                f"critical resume fingerprint changed for {key}: {observed} != {pre.get(key)}"
            )

    ic_path = Path(pre["ic"]).resolve()
    render_hashes = p173.verify_render(run_dir, row, ic_path)
    for key, value in render_hashes.items():
        if pre.get(key) != value:
            raise ResumeError(f"independent render hash mismatch for {key}")

    params = read_params(run_dir / "params.txt")
    output_dir = Path(params.get("OutputDir", "")).resolve()
    if output_dir != run_dir.resolve():
        raise ResumeError(f"OutputDir drift: {output_dir} != {run_dir.resolve()}")
    restart_base = params.get("RestartFile", "").strip()
    if not restart_base or "/" in restart_base or "\\" in restart_base:
        raise ResumeError(f"unsafe/invalid RestartFile={restart_base!r}")
    return pre


def post_is_complete(run_dir: Path) -> Tuple[bool, Dict | None, str | None]:
    for filename in (STATE_NAME, "phase173_POST.json"):
        path = run_dir / filename
        if not path.is_file():
            continue
        obj = load_json(path)
        if obj.get("status") == "COMPLETE":
            return True, obj, filename
    return False, None, None


def verify_completion_integrity(run_dir: Path, record: Dict, source: str) -> Dict:
    """Re-hash a completed run before trusting ALREADY_COMPLETE or releasing blind jobs."""
    if record.get("status") != "COMPLETE":
        raise ResumeError("completion-integrity check requires a COMPLETE record")
    expected_digest = record.get("run_directory_sha256")
    expected_files = record.get("file_hashes")
    if not expected_digest or not isinstance(expected_files, list):
        raise ResumeError(f"{source}: completed record lacks directory fingerprints")

    if source == STATE_NAME:
        exclude = {STATE_NAME, LOCK_NAME, ATTEMPTS_NAME}
    elif source == "phase173_POST.json":
        exclude = {"phase173_POST.json", STATE_NAME, LOCK_NAME, ATTEMPTS_NAME}
    else:
        raise ResumeError(f"unknown completion record source: {source}")

    observed_digest, observed_files = p173.directory_digest(run_dir, exclude=exclude)
    if observed_digest != expected_digest or observed_files != expected_files:
        raise ResumeError(
            f"completed run directory changed after fingerprint freeze: {observed_digest} != {expected_digest}"
        )
    return {
        "run_directory_sha256": observed_digest,
        "file_count": len(observed_files),
        "completion_record": source,
    }


def prior_fatal_failure(run_dir: Path) -> str | None:
    for filename in (STATE_NAME, "phase173_POST.json"):
        path = run_dir / filename
        if not path.is_file():
            continue
        obj = load_json(path)
        if obj.get("fatal_marker"):
            return f"{filename} records a fatal GIZMO marker"
    return None


def restart_indices(restart_dir: Path, base: str) -> Tuple[set[int], set[int], List[str]]:
    regular, backup, strange = set(), set(), []
    if not restart_dir.is_dir():
        return regular, backup, strange
    pattern = re.compile(rf"^{re.escape(base)}\.(\d+)(\.bak)?$")
    for path in restart_dir.iterdir():
        if not path.is_file():
            continue
        m = pattern.match(path.name)
        if not m:
            if path.name.startswith(base + ".") and not path.name.endswith(".bak2"):
                strange.append(path.name)
            continue
        idx = int(m.group(1))
        (backup if m.group(2) else regular).add(idx)
    return regular, backup, sorted(strange)


def validate_restart_set(run_dir: Path, mpi_tasks: int) -> Dict:
    params = read_params(run_dir / "params.txt")
    base = params.get("RestartFile", "").strip()
    path_capacity = validate_restart_path_capacity_values(
        params.get("OutputDir", ""), base, mpi_tasks
    )
    restart_dir = run_dir / "restartfiles"
    expected = set(range(mpi_tasks))
    regular, backup, strange = restart_indices(restart_dir, base)
    if strange:
        raise ResumeError(f"unexpected restart-like files: {strange[:10]}")

    extra_regular = regular - expected
    extra_backup = backup - expected
    if extra_regular or extra_backup:
        raise ResumeError(
            f"restart topology contains task indices outside current MPI size={mpi_tasks}: "
            f"regular={sorted(extra_regular)} backup={sorted(extra_backup)}"
        )

    def complete(indices: set[int], suffix: str) -> Tuple[bool, List[Dict]]:
        if indices != expected:
            return False, []
        records = []
        for i in range(mpi_tasks):
            path = restart_dir / f"{base}.{i}{suffix}"
            size = path.stat().st_size if path.is_file() else 0
            if size <= 0:
                return False, []
            records.append({
                "name": path.name,
                "path": str(path),
                "size": size,
                "sha256": sha256_file(path),
                "mtime_ns": path.stat().st_mtime_ns,
            })
        return True, records

    reg_ok, reg_records = complete(regular, "")
    bak_ok, bak_records = complete(backup, ".bak")
    if not reg_ok and not bak_ok:
        raise ResumeError(
            f"no complete restart set for MPI tasks={mpi_tasks}; "
            f"regular_indices={sorted(regular)} backup_indices={sorted(backup)}"
        )
    chosen = "regular" if reg_ok else "backup"
    records = reg_records if reg_ok else bak_records
    return {
        "mpi_tasks": mpi_tasks,
        "restart_base": base,
        "restart_dir": str(restart_dir),
        "chosen_set": chosen,
        "regular_complete": reg_ok,
        "backup_complete": bak_ok,
        "path_capacity": path_capacity,
        "files": records,
    }


def restart_identity(info: Dict) -> Dict:
    try:
        files = [
            {"name": x["name"], "size": int(x["size"]), "sha256": x["sha256"]}
            for x in info["files"]
        ]
        return {
            "mpi_tasks": int(info["mpi_tasks"]),
            "restart_base": info["restart_base"],
            "chosen_set": info["chosen_set"],
            "files": files,
        }
    except Exception as exc:
        raise ResumeError(f"invalid recorded restart fingerprint: {exc}") from exc


def authorize_resume(run_dir: Path, mpi_tasks: int) -> Dict:
    """Allow continuation only from the exact checkpoint set recorded by a clean pause."""
    state_path = run_dir / STATE_NAME
    if not state_path.is_file():
        legacy = run_dir / "phase173_POST.json"
        if legacy.is_file():
            legacy_state = load_json(legacy)
            raise ResumeError(
                "automatic restart requires a Phase175 PAUSED_RESTARTABLE record; "
                f"legacy Phase173 status={legacy_state.get('status')!r} is not authorization"
            )
        raise ResumeError("automatic restart requires a Phase175 PAUSED_RESTARTABLE record")

    state = load_json(state_path)
    if state.get("status") != "PAUSED_RESTARTABLE":
        raise ResumeError(
            "automatic restart refused: last Phase175 status is "
            f"{state.get('status')!r}, not 'PAUSED_RESTARTABLE'"
        )
    try:
        recorded_tasks = int(state.get("mpi_tasks"))
    except Exception as exc:
        raise ResumeError("paused state has invalid/missing mpi_tasks") from exc
    if recorded_tasks != mpi_tasks:
        raise ResumeError(
            f"MPI topology changed since pause: recorded={recorded_tasks} current={mpi_tasks}"
        )
    recorded = state.get("restart_after")
    if not isinstance(recorded, dict):
        raise ResumeError("paused state lacks recorded restart_after fingerprint")
    current = validate_restart_set(run_dir, mpi_tasks)
    if restart_identity(current) != restart_identity(recorded):
        raise ResumeError("restart checkpoint bytes/topology changed since PAUSED_RESTARTABLE freeze")
    return current


@contextmanager
def run_lock(run_dir: Path):
    lock_path = run_dir / LOCK_NAME
    fd = lock_path.open("a+")
    try:
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ResumeError(
                f"run directory is already locked by another Phase175 process: {run_dir}"
            ) from exc
        fd.seek(0)
        fd.truncate()
        fd.write(json.dumps({
            "phase": PHASE,
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "locked_unix": time.time(),
        }) + "\n")
        fd.flush()
        yield
    finally:
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        finally:
            fd.close()


def attempt_number(run_dir: Path) -> int:
    path = run_dir / ATTEMPTS_NAME
    if not path.is_file():
        return 1
    begins = 0
    with path.open() as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                raise ResumeError(
                    f"invalid attempt audit JSON at {path}:{line_no}: {exc}"
                ) from exc
            if obj.get("event") == "BEGIN":
                begins += 1
    return begins + 1


def append_attempt(run_dir: Path, record: Dict) -> None:
    with (run_dir / ATTEMPTS_NAME).open("a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def launch_command(executable: Path, params: Path, mpi_prefix: str, restart_flag: int) -> List[str]:
    prefix = shlex.split(mpi_prefix) if mpi_prefix.strip() else []
    return prefix + [str(executable.resolve()), str(params.resolve()), str(restart_flag)]


def count_snapshots(run_dir: Path) -> int:
    return len([p for p in run_dir.glob("snapshot*") if p.is_file()])


def write_state(run_dir: Path, state: Dict) -> None:
    (run_dir / STATE_NAME).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def execute_attempt(
    run_dir: Path,
    row: Dict[str, str],
    executable: Path,
    pre: Dict,
    mpi_prefix: str,
    mpi_tasks: int,
    restart_flag: int,
) -> int:
    if restart_flag not in (0, 1):
        raise ResumeError(f"unsupported restart flag {restart_flag}")
    path_capacity = validate_restart_path_capacity(run_dir, mpi_tasks)
    restart_before = validate_restart_set(run_dir, mpi_tasks) if restart_flag == 1 else None

    params = run_dir / "params.txt"
    command = launch_command(executable, params, mpi_prefix, restart_flag)
    attempt = attempt_number(run_dir)
    started = time.time()
    log_path = run_dir / "gizmo.log"
    log_mode = "w" if restart_flag == 0 and not log_path.exists() else "a"

    begin = {
        "phase": PHASE,
        "event": "BEGIN",
        "attempt": attempt,
        "run_id": row["run_id"],
        "restart_flag": restart_flag,
        "mpi_tasks": mpi_tasks,
        "command": command,
        "started_unix": started,
        "restart_before": restart_before,
        "restart_path_capacity": path_capacity,
    }
    append_attempt(run_dir, begin)

    with log_path.open(log_mode) as log:
        if log_mode == "a":
            log.write(f"\n===== PHASE175 ATTEMPT {attempt} RESTART_FLAG={restart_flag} =====\n")
        log.flush()
        start_offset = log.tell()
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                log.write(line)
            proc.stdout.close()
            rc = proc.wait()
        log.flush()

    with log_path.open(errors="replace") as fh:
        fh.seek(start_offset)
        attempt_text = fh.read()
    completed = bool(re.search(r"Final time=.*reached\. Simulation ends\.", attempt_text))
    fatal_marker = (
        "MPI_ABORT" in attempt_text
        or "ENDRUN issued" in attempt_text
        or "Fatal error" in attempt_text
    )
    snapshots = count_snapshots(run_dir)
    required_snapshots = len([t for t in p173.parse_times(row) if t > 0])

    restart_after = None
    restart_error = None
    try:
        restart_after = validate_restart_set(run_dir, mpi_tasks)
    except ResumeError as exc:
        restart_error = str(exc)

    if rc == 0 and completed and not fatal_marker and snapshots >= required_snapshots:
        status = "COMPLETE"
    elif rc == 0 and not completed and not fatal_marker and restart_after is not None:
        status = "PAUSED_RESTARTABLE"
    else:
        status = "FAILED"

    state = {
        "phase": PHASE,
        "status": status,
        "run_id": row["run_id"],
        "manifest_row": row,
        "manifest_sha256": p173.EXPECTED_MANIFEST_SHA256,
        "provenance": pre.get("provenance"),
        "executable_sha256": pre.get("executable_sha256"),
        "ic": pre.get("ic"),
        "ic_sha256": pre.get("ic_sha256"),
        "params_sha256": pre.get("params_sha256"),
        "output_times_sha256": pre.get("output_times_sha256"),
        "render_metadata_sha256": pre.get("render_metadata_sha256"),
        "attempt": attempt,
        "restart_flag": restart_flag,
        "mpi_tasks": mpi_tasks,
        "command": command,
        "returncode": rc,
        "completion_marker": completed,
        "fatal_marker": fatal_marker,
        "snapshot_count": snapshots,
        "required_snapshot_count": required_snapshots,
        "restart_after": restart_after,
        "restart_error": restart_error,
        "restart_path_capacity": path_capacity,
        "wall_seconds": time.time() - started,
    }
    if status == "COMPLETE":
        digest, files = p173.directory_digest(
            run_dir, exclude={STATE_NAME, LOCK_NAME, ATTEMPTS_NAME}
        )
        state["run_directory_sha256"] = digest
        state["file_hashes"] = files
    write_state(run_dir, state)
    append_attempt(run_dir, {
        "phase": PHASE,
        "event": "END",
        "attempt": attempt,
        "run_id": row["run_id"],
        "status": status,
        "returncode": rc,
        "completion_marker": completed,
        "fatal_marker": fatal_marker,
        "snapshot_count": snapshots,
        "ended_unix": time.time(),
        "restart_after": restart_after,
        "restart_error": restart_error,
    })

    if status in {"COMPLETE", "PAUSED_RESTARTABLE"}:
        return 0
    return rc if rc else 3


def load_campaign():
    provenance = p173.load_provenance(HERE / "phase173_provenance_master_6353.json")
    state_root = Path(".phase175")
    manifest_path, rows = p173.materialize_manifest(state_root / "phase172_manifest.csv")
    for row in rows:
        p173.validate_row(row)
    return provenance, manifest_path, rows


def fresh_prepare(args, provenance, manifest_path, rows):
    ns = SimpleNamespace(
        run_id=args.run_id,
        executable=args.executable,
        ic_root=args.ic_root,
        run_root=args.run_root,
        mpi_prefix=args.mpi_prefix,
        max_mem_mb=args.max_mem_mb,
        time_limit_cpu=args.time_limit_cpu,
        no_generate_ic=args.no_generate_ic,
    )
    return p173.prepare(ns, provenance, rows, manifest_path)


def dispatch(args) -> int:
    provenance, manifest_path, rows = load_campaign()
    _, row = p173.find_row(rows, args.run_id)
    run_root = Path(args.run_root).resolve()
    run_dir = run_root / row["run_id"]
    executable = Path(args.executable).resolve()
    mpi_tasks = resolve_mpi_tasks(args.mpi_tasks, args.mpi_prefix)

    if not run_dir.exists():
        validate_restart_path_capacity_values(
            str(run_dir.resolve()) + "/", "restart", mpi_tasks
        )
        run_dir, row, _, pre = fresh_prepare(args, provenance, manifest_path, rows)
        with run_lock(run_dir):
            return execute_attempt(
                run_dir, row, executable, pre, args.mpi_prefix, mpi_tasks, 0
            )

    if not run_dir.is_dir():
        raise ResumeError(f"run path exists but is not a directory: {run_dir}")

    with run_lock(run_dir):
        complete, post, source = post_is_complete(run_dir)
        pre = verify_prelaunch(run_dir, row, executable, provenance)
        if complete:
            assert post is not None and source is not None
            integrity = verify_completion_integrity(run_dir, post, source)
            print(json.dumps({
                "phase": PHASE,
                "status": "ALREADY_COMPLETE",
                "run_id": row["run_id"],
                "completion_record": source,
                "snapshot_count": post.get("snapshot_count"),
                "completion_integrity": integrity,
            }, indent=2))
            return 0
        fatal = prior_fatal_failure(run_dir)
        if fatal:
            raise ResumeError(f"refusing automatic resume after recorded fatal failure: {fatal}")
        authorize_resume(run_dir, mpi_tasks)
        return execute_attempt(
            run_dir, row, executable, pre, args.mpi_prefix, mpi_tasks, 1
        )


def inspect(args) -> int:
    provenance, _, rows = load_campaign()
    _, row = p173.find_row(rows, args.run_id)
    run_dir = Path(args.run_root).resolve() / row["run_id"]
    if not run_dir.is_dir():
        raise ResumeError(f"run directory missing: {run_dir}")
    executable = Path(args.executable).resolve()
    pre = verify_prelaunch(run_dir, row, executable, provenance)
    complete, post, source = post_is_complete(run_dir)
    result = {
        "phase": PHASE,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "run_id": row["run_id"],
        "completion_record": source,
        "critical_fingerprints_verified": True,
        "executable_sha256": pre["executable_sha256"],
    }
    if complete:
        assert post is not None and source is not None
        result["completion_integrity"] = verify_completion_integrity(run_dir, post, source)
    else:
        mpi_tasks = resolve_mpi_tasks(args.mpi_tasks, args.mpi_prefix)
        result["restart"] = authorize_resume(run_dir, mpi_tasks)
        result["status"] = "PAUSED_RESTARTABLE"
    print(json.dumps(result, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("dispatch", "inspect"):
        x = sub.add_parser(name)
        x.add_argument("--run-id", required=True)
        x.add_argument("--executable", required=True)
        x.add_argument("--run-root", required=True)
        x.add_argument("--mpi-prefix", default="")
        x.add_argument("--mpi-tasks", type=int, default=None)
        if name == "dispatch":
            x.add_argument("--ic-root", required=True)
            x.add_argument("--max-mem-mb", type=int, default=3500)
            x.add_argument("--time-limit-cpu", type=int, default=170000)
            x.add_argument("--no-generate-ic", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return dispatch(args) if args.command == "dispatch" else inspect(args)
    except (
        ResumeError,
        p173.LaunchError,
        subprocess.CalledProcessError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({
            "phase": PHASE,
            "status": "FAIL",
            "error": str(exc),
        }, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
