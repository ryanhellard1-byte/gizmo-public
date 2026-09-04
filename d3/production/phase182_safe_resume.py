#!/usr/bin/env python3
"""Phase182 production wrapper: Phase181 attested safe resume plus automatic finalization.

A scheduler attempt may end in either PAUSED_RESTARTABLE or COMPLETE. Pauses are
left resumable with no derived evidence. A COMPLETE run is immediately finalized
into a separate evidence root by phase182_finalize_run.py.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase175_safe_resume as p175  # noqa: E402
import phase182_finalize_run as finalizer  # noqa: E402

PHASE = 182


class DispatchError(RuntimeError):
    pass


def raw_command(args) -> list[str]:
    cmd = [
        sys.executable,
        str(HERE / "phase181_safe_resume.py"),
        "--machine-attestation", str(Path(args.machine_attestation).resolve()),
        args.command,
        "--run-id", args.run_id,
        "--executable", str(Path(args.executable).resolve()),
        "--run-root", str(Path(args.run_root).resolve()),
        "--mpi-prefix", args.mpi_prefix,
    ]
    if args.mpi_tasks is not None:
        cmd.extend(["--mpi-tasks", str(args.mpi_tasks)])
    if args.command == "dispatch":
        cmd.extend([
            "--ic-root", str(Path(args.ic_root).resolve()),
            "--max-mem-mb", str(args.max_mem_mb),
            "--time-limit-cpu", str(args.time_limit_cpu),
        ])
        if args.no_generate_ic:
            cmd.append("--no-generate-ic")
    return cmd


def raw_status(run_dir: Path) -> str:
    complete, _, _ = p175.post_is_complete(run_dir)
    if complete:
        return "COMPLETE"
    state = run_dir / p175.STATE_NAME
    if not state.is_file():
        raise DispatchError(f"raw dispatcher returned success but Phase175 state is missing: {state}")
    try:
        obj = json.loads(state.read_text())
    except Exception as exc:
        raise DispatchError(f"invalid Phase175 state after dispatch: {exc}") from exc
    return str(obj.get("status", ""))


def dispatch(args) -> int:
    rc = subprocess.run(raw_command(args), check=False).returncode
    if rc != 0:
        return rc
    run_dir = Path(args.run_root).resolve() / args.run_id
    status = raw_status(run_dir)
    if status == "PAUSED_RESTARTABLE":
        print(json.dumps({
            "phase": PHASE,
            "status": "PAUSED_RESTARTABLE",
            "run_id": args.run_id,
            "finalization": "DEFERRED_UNTIL_COMPLETE",
        }, indent=2))
        return 0
    if status != "COMPLETE":
        raise DispatchError(f"unexpected raw run status after successful dispatch: {status!r}")
    result = finalizer.finalize(
        args.run_id,
        Path(args.run_root),
        Path(args.evidence_root),
        Path(args.executable),
        Path(args.machine_attestation),
    )
    print(json.dumps({
        "phase": PHASE,
        "status": "COMPLETE_FINALIZED",
        "run_id": args.run_id,
        "raw_status": status,
        "finalization_status": result.get("status"),
        "evidence_dir": result.get("evidence_dir"),
    }, indent=2))
    return 0


def inspect(args) -> int:
    rc = subprocess.run(raw_command(args), check=False).returncode
    if rc != 0:
        return rc
    run_dir = Path(args.run_root).resolve() / args.run_id
    status = raw_status(run_dir)
    if status == "PAUSED_RESTARTABLE":
        print(json.dumps({
            "phase": PHASE,
            "status": "PAUSED_RESTARTABLE",
            "run_id": args.run_id,
            "evidence_status": "NOT_EXPECTED_BEFORE_COMPLETION",
        }, indent=2))
        return 0
    if status != "COMPLETE":
        raise DispatchError(f"unexpected raw inspect status: {status!r}")
    evidence_dir = Path(args.evidence_root).resolve() / args.run_id
    record = finalizer.verify_finalized(
        evidence_dir,
        Path(args.run_root),
        args.run_id,
        Path(args.executable),
        Path(args.machine_attestation),
    )
    print(json.dumps({
        "phase": PHASE,
        "status": "COMPLETE_FINALIZED_VERIFIED",
        "run_id": args.run_id,
        "raw_status": status,
        "evidence_status": record.get("status"),
        "evidence_dir": str(evidence_dir),
    }, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--machine-attestation", required=True)
    p.add_argument("--evidence-root", required=True)
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
        DispatchError,
        finalizer.FinalizeError,
        finalizer.machine.EvidenceGateError,
        p175.ResumeError,
        p175.p173.LaunchError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
