#!/usr/bin/env python3
"""Phase180 target-machine launch packet for the frozen D3 campaign.

Phase180 adds no physics, no manifest rows, and no thresholds. It emits the
operator-side command packet needed to run the already-locked Phase176/179 stack
on an HPC target without confusing the latest operator checkout with the older
canonical physics source commit used for the attested production binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase176_machine_audit as p176  # noqa: E402
import phase179_machine_batch_submit as p179  # noqa: E402

PHASE = 180
DEFAULT_REPO = "https://github.com/ryanhellard1-byte/gizmo-public.git"
DEFAULT_PACKET = "phase180_target_machine_launch.sh"


class PacketError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def q(value: str | Path) -> str:
    return shlex.quote(str(value))


def run_text(cmd: List[str], cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def git_head(repo_root: Path) -> str | None:
    try:
        return run_text(["git", "rev-parse", "HEAD"], cwd=repo_root)
    except Exception:
        return None


def canonical_source_commit() -> str:
    return str(p176.EXPECTED["source_commit"])


def validate_slurm_options(options: Iterable[str]) -> List[str]:
    clean = []
    for option in options:
        option = option.strip()
        if not option.startswith("--") or "\n" in option or "\r" in option:
            raise PacketError(f"invalid --slurm-option value: {option!r}")
        clean.append(option)
    return clean


def packet_script(args) -> str:
    slurm_options = validate_slurm_options(args.slurm_option)
    canonical = canonical_source_commit()
    operator_tree = Path(args.operator_tree)
    source_tree = Path(args.canonical_source_tree)
    binary_dir = Path(args.binary_dir)
    attestation = Path(args.machine_attestation)
    ic_root = Path(args.ic_root)
    run_root = Path(args.run_root)
    batch_root = Path(args.batch_root)

    commissioning_stage = [
        "python3", str(operator_tree / "d3/production/phase179_machine_batch_submit.py"), "stage",
        "--phase", "commissioning",
        "--machine-attestation", str(attestation),
        "--executable", str(binary_dir / "GIZMO_D3_PROD"),
        "--ic-root", str(ic_root),
        "--run-root", str(run_root),
        "--batch-root", str(batch_root),
        "--mpi-prefix", args.run_mpi_prefix,
        "--mpi-tasks", str(args.mpi_tasks),
    ]
    for option in slurm_options:
        commissioning_stage.extend(["--slurm-option", option])
    if args.submit:
        commissioning_stage.append("--submit")

    verify_commissioning = [
        "python3", str(operator_tree / "d3/production/phase179_machine_batch_submit.py"), "verify-commissioning",
        "--run-root", str(run_root),
        "--machine-attestation", str(attestation),
        "--executable", str(binary_dir / "GIZMO_D3_PROD"),
        "--proof", str(batch_root / "commissioning/phase179_commissioning_proof.json"),
    ]

    blind_stage = [
        "python3", str(operator_tree / "d3/production/phase179_machine_batch_submit.py"), "stage",
        "--phase", "blind",
        "--machine-attestation", str(attestation),
        "--executable", str(binary_dir / "GIZMO_D3_PROD"),
        "--commissioning-proof", str(batch_root / "commissioning/phase179_commissioning_proof.json"),
        "--ic-root", str(ic_root),
        "--run-root", str(run_root),
        "--batch-root", str(batch_root),
        "--mpi-prefix", args.run_mpi_prefix,
        "--mpi-tasks", str(args.mpi_tasks),
    ]
    for option in slurm_options:
        blind_stage.extend(["--slurm-option", option])
    if args.submit:
        blind_stage.append("--submit")

    build_attest = [
        "python3", str(operator_tree / "d3/production/phase176_machine_audit.py"), "build-attest",
        "--source-tree", str(source_tree),
        "--jobs", str(args.build_jobs),
        "--mpi-prefix", args.build_mpi_prefix,
        "--binary-dir", str(binary_dir),
        "--output", str(attestation),
    ]
    if args.systype:
        build_attest.extend(["--systype", args.systype])

    preflight = [
        "python3", str(operator_tree / "d3/production/phase176_production_launcher.py"),
        "--machine-attestation", str(attestation),
        "preflight",
        "--executable", str(binary_dir / "GIZMO_D3_PROD"),
    ]

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f"REPO_URL={q(args.repo_url)}",
        f"OPERATOR_TREE={q(operator_tree)}",
        f"CANONICAL_SOURCE_TREE={q(source_tree)}",
        f"EXPECTED_CANONICAL_SOURCE_COMMIT={q(canonical)}",
        "",
        "echo '[Phase180] bootstrap operator checkout with latest production tools'",
        "if [ ! -d \"$OPERATOR_TREE/.git\" ]; then git clone \"$REPO_URL\" \"$OPERATOR_TREE\"; fi",
        "git -C \"$OPERATOR_TREE\" fetch origin",
        "git -C \"$OPERATOR_TREE\" checkout master",
        "git -C \"$OPERATOR_TREE\" pull --ff-only origin master",
        "OPERATOR_HEAD=$(git -C \"$OPERATOR_TREE\" rev-parse HEAD)",
        "",
        "echo '[Phase180] bootstrap canonical Phase176 physics source checkout'",
        "if [ ! -d \"$CANONICAL_SOURCE_TREE/.git\" ]; then git clone \"$REPO_URL\" \"$CANONICAL_SOURCE_TREE\"; fi",
        "git -C \"$CANONICAL_SOURCE_TREE\" fetch origin",
        "git -C \"$CANONICAL_SOURCE_TREE\" checkout \"$EXPECTED_CANONICAL_SOURCE_COMMIT\"",
        "test \"$(git -C \"$CANONICAL_SOURCE_TREE\" rev-parse HEAD)\" = \"$EXPECTED_CANONICAL_SOURCE_COMMIT\"",
        "git -C \"$CANONICAL_SOURCE_TREE\" diff --quiet",
        "git -C \"$CANONICAL_SOURCE_TREE\" diff --cached --quiet",
        "",
        "echo '[Phase180] build and attest production executable from canonical source'",
        shlex.join(build_attest),
        "",
        "echo '[Phase180] preflight attested production launcher'",
        shlex.join(preflight),
        "",
        "echo '[Phase180] stage commissioning jobs only'",
        shlex.join(commissioning_stage),
        "",
        "cat <<'PHASE180_NEXT'",
        "Phase180 commissioning jobs are staged. Submit/monitor them on the target scheduler.",
        "After all 8 R0 commissioning runs are COMPLETE, run:",
        shlex.join(verify_commissioning),
        "",
        "Then stage the 119 blind runs with:",
        shlex.join(blind_stage),
        "PHASE180_NEXT",
        "",
        "cat > phase180_operator_record.json <<PHASE180_JSON",
        json.dumps({
            "phase": PHASE,
            "status": "PACKET_RENDERED",
            "repo_url": args.repo_url,
            "canonical_source_commit": canonical,
            "operator_tree": str(operator_tree),
            "canonical_source_tree": str(source_tree),
            "binary_dir": str(binary_dir),
            "machine_attestation": str(attestation),
            "ic_root": str(ic_root),
            "run_root": str(run_root),
            "batch_root": str(batch_root),
            "build_jobs": args.build_jobs,
            "systype": args.systype,
            "build_mpi_prefix": args.build_mpi_prefix,
            "run_mpi_prefix": args.run_mpi_prefix,
            "mpi_tasks": args.mpi_tasks,
            "slurm_options": slurm_options,
            "submit": bool(args.submit),
        }, indent=2),
        "PHASE180_JSON",
        "python3 - <<'PY'",
        "import hashlib, pathlib",
        "p=pathlib.Path('phase180_operator_record.json')",
        "print('[Phase180] operator record SHA256', hashlib.sha256(p.read_bytes()).hexdigest())",
        "PY",
    ]
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    w = sub.add_parser("write-packet")
    w.add_argument("--repo-url", default=DEFAULT_REPO)
    w.add_argument("--operator-tree", required=True)
    w.add_argument("--canonical-source-tree", required=True)
    w.add_argument("--binary-dir", required=True)
    w.add_argument("--machine-attestation", required=True)
    w.add_argument("--ic-root", required=True)
    w.add_argument("--run-root", required=True)
    w.add_argument("--batch-root", required=True)
    w.add_argument("--systype", default=None)
    w.add_argument("--build-jobs", type=int, default=8)
    w.add_argument("--build-mpi-prefix", default="mpirun -np 2")
    w.add_argument("--run-mpi-prefix", default="srun")
    w.add_argument("--mpi-tasks", type=int, required=True)
    w.add_argument("--slurm-option", action="append", default=[])
    w.add_argument("--submit", action="store_true")
    w.add_argument("--output", default=DEFAULT_PACKET)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command != "write-packet":
            raise PacketError(f"unknown command {args.command}")
        if args.build_jobs <= 0 or args.mpi_tasks <= 0:
            raise PacketError("build jobs and MPI tasks must be positive")
        script = packet_script(args)
        out = Path(args.output)
        if out.exists():
            raise PacketError(f"refusing to overwrite existing packet: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(script)
        out.chmod(0o755)
        print(json.dumps({
            "phase": PHASE,
            "status": "PASS",
            "packet": str(out),
            "packet_sha256": sha256_text(script),
            "canonical_source_commit": canonical_source_commit(),
            "operator_checkout_head": git_head(HERE.parents[1]),
            "claim_boundary": "operator packet only; does not execute the 127-run halo campaign",
        }, indent=2))
        return 0
    except (PacketError, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
