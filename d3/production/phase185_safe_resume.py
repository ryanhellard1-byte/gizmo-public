#!/usr/bin/env python3
"""Phase185 production dispatcher with a commissioning-only evidence boundary.

All simulation execution remains delegated to the Phase181-attested Phase175
safe-resume path. Completed non-blind commissioning runs are finalized into
external evidence. Blind runs are explicitly forbidden from producing Phase185
per-run derived evidence; they remain raw until the all-127 Phase184 collector.
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
import phase181_machine_batch_submit as p181_batch  # noqa: E402
import phase185_commissioning_evidence as p185  # noqa: E402

PHASE = 185


class DispatchError(RuntimeError):
    pass


def row_class(run_id: str) -> str:
    _, commissioning, blind = p181_batch.frozen_rows()
    if run_id in {str(r["run_id"]) for r in commissioning}:
        return "commissioning"
    if run_id in {str(r["run_id"]) for r in blind}:
        return "blind"
    raise DispatchError(f"{run_id}: not present exactly once in frozen campaign")


def phase181_command(args) -> list[str]:
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
        raise DispatchError(f"invalid Phase175 state after dispatcher success: {exc}") from exc
    status = str(obj.get("status", ""))
    if status != "PAUSED_RESTARTABLE":
        raise DispatchError(f"unexpected raw status after successful dispatcher call: {status!r}")
    return status


def blind_evidence_path(args) -> Path:
    return Path(args.evidence_root).resolve() / args.run_id


def enforce_blind_raw_only(args) -> None:
    path = blind_evidence_path(args)
    if path.exists():
        raise DispatchError(
            f"{args.run_id}: blind per-run evidence exists at {path}; blind rows must remain raw until Phase184 all-127 collection"
        )


def handle_success(args) -> int:
    kind = row_class(args.run_id)
    run_dir = Path(args.run_root).resolve() / args.run_id
    status = raw_status(run_dir)

    if kind == "blind":
        enforce_blind_raw_only(args)
        print(json.dumps({
            "phase": PHASE,
            "status": status,
            "run_id": args.run_id,
            "campaign_class": "blind",
            "derived_evidence": "FORBIDDEN_UNTIL_PHASE184_ALL_127",
        }, indent=2))
        return 0

    if status == "PAUSED_RESTARTABLE":
        print(json.dumps({
            "phase": PHASE,
            "status": status,
            "run_id": args.run_id,
            "campaign_class": "commissioning",
            "derived_evidence": "DEFERRED_UNTIL_COMPLETE",
        }, indent=2))
        return 0

    evidence_dir = Path(args.evidence_root).resolve() / args.run_id
    if args.command == "inspect":
        record = p185.verify_finalized(
            evidence_dir,
            Path(args.run_root),
            args.run_id,
            Path(args.executable),
            Path(args.machine_attestation),
        )
        final_status = "COMPLETE_COMMISSIONING_EVIDENCE_VERIFIED"
    else:
        record = p185.finalize(
            args.run_id,
            Path(args.run_root),
            Path(args.evidence_root),
            Path(args.executable),
            Path(args.machine_attestation),
        )
        final_status = "COMPLETE_COMMISSIONING_FINALIZED"
    print(json.dumps({
        "phase": PHASE,
        "status": final_status,
        "run_id": args.run_id,
        "campaign_class": "commissioning",
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
        rc = subprocess.run(phase181_command(args), check=False).returncode
        if rc != 0:
            return rc
        return handle_success(args)
    except (
        DispatchError,
        p185.CommissioningEvidenceError,
        p181_batch.BatchError,
        p175.ResumeError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
