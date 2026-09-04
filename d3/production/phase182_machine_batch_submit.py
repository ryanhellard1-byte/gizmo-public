#!/usr/bin/env python3
"""Phase182 scheduler: attested Phase181 execution plus automatic external evidence.

The original 8 non-blind commissioning jobs remain the release gate. Phase182
strengthens that gate by requiring every commissioning run to be both raw-COMPLETE
and atomically FINALIZED before the 119 blind jobs can be staged or submitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_machine_batch_submit as p181  # noqa: E402
import phase182_finalize_run as finalizer  # noqa: E402

PHASE = 182
EXPECTED_TOTAL = 127
EXPECTED_COMMISSIONING = 8
EXPECTED_BLIND = 119


class BatchError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def truthy(value: str) -> bool:
    return str(value).strip().lower() == "true"


def frozen_rows():
    rows, commissioning, blind = p181.frozen_rows()
    if len(rows) != EXPECTED_TOTAL or len(commissioning) != EXPECTED_COMMISSIONING or len(blind) != EXPECTED_BLIND:
        raise BatchError(
            f"frozen campaign cardinality changed total={len(rows)} commissioning={len(commissioning)} blind={len(blind)}"
        )
    return rows, commissioning, blind


def verify_commissioning(
    run_root: Path,
    evidence_root: Path,
    proof_path: Path,
    machine_attestation: Path,
    executable: Path,
) -> Dict:
    att = p181.load_attested(machine_attestation, executable)
    phase181_tmp = proof_path.with_suffix(proof_path.suffix + ".phase181.tmp")
    base = p181.verify_commissioning(run_root, phase181_tmp, machine_attestation, executable)
    try:
        if phase181_tmp.exists():
            phase181_tmp.unlink()
    except OSError:
        pass

    failures = list(base.get("failures", []))
    _, commissioning, _ = frozen_rows()
    finalized = []
    for row in commissioning:
        rid = row["run_id"]
        try:
            record = finalizer.verify_finalized(
                evidence_root.resolve() / rid,
                run_root,
                rid,
                executable,
                machine_attestation,
            )
            record_path = evidence_root.resolve() / rid / finalizer.FINAL_RECORD
            finalized.append({
                "run_id": rid,
                "finalization_record": str(record_path),
                "finalization_record_sha256": sha256_file(record_path),
                "raw_run_directory_sha256": record["raw_run_directory_sha256"],
                "artifacts": record["artifacts"],
            })
        except Exception as exc:
            failures.append(f"{rid}: Phase182 finalization verification failed: {exc}")

    expected_ids = {r["run_id"] for r in commissioning}
    finalized_ids = {r["run_id"] for r in finalized}
    status = (
        "PASS"
        if base.get("status") == "PASS"
        and not failures
        and finalized_ids == expected_ids
        else "FAIL"
    )
    proof = dict(base)
    proof.update({
        "phase": PHASE,
        "kind": "phase182_complete_and_finalized_commissioning_release_gate",
        "base_phase181_status": base.get("status"),
        "status": status,
        "evidence_root": str(evidence_root.resolve()),
        "machine_attestation": str(machine_attestation.resolve()),
        "machine_attestation_sha256": sha256_file(machine_attestation),
        "evidence_executable": str(executable.resolve()),
        "evidence_executable_sha256": att["evidence_executable_sha256"],
        "finalized_runs": len(finalized),
        "finalization_records": finalized,
        "failures": failures,
    })
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    return proof


def load_commissioning_proof(
    path: Path,
    commissioning: List[Dict[str, str]],
    attestation: Dict,
    machine_attestation: Path,
    executable: Path,
) -> Dict:
    if not path.is_file():
        raise BatchError(f"commissioning proof missing: {path}")
    proof = json.loads(path.read_text())
    expected_ids = {r["run_id"] for r in commissioning}
    if proof.get("phase") != PHASE or proof.get("status") != "PASS":
        raise BatchError("commissioning proof is not a Phase182 PASS proof")
    if proof.get("manifest_sha256") != p181.p174.EXPECTED_MANIFEST_SHA256:
        raise BatchError("commissioning proof manifest SHA mismatch")
    if proof.get("commissioning_runs") != EXPECTED_COMMISSIONING or proof.get("complete_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("commissioning proof raw completion count mismatch")
    if proof.get("finalized_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("commissioning proof finalized-run count mismatch")
    if set(proof.get("run_ids", [])) != expected_ids:
        raise BatchError("commissioning proof run IDs mismatch")
    records = proof.get("finalization_records")
    if not isinstance(records, list) or {r.get("run_id") for r in records} != expected_ids:
        raise BatchError("commissioning proof finalization record IDs mismatch")
    if proof.get("machine_attestation_sha256") != sha256_file(machine_attestation):
        raise BatchError("commissioning proof machine-attestation SHA mismatch")
    if proof.get("evidence_executable_sha256") != attestation["evidence_executable_sha256"]:
        raise BatchError("commissioning proof evidence executable SHA mismatch")
    if sha256_file(executable) != attestation["evidence_executable_sha256"]:
        raise BatchError("current evidence executable no longer matches attestation")
    return proof


def write_job(path: Path, row: Dict[str, str], args, slurm_options: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dispatcher = HERE / "phase182_safe_resume.py"
    if not dispatcher.is_file():
        raise BatchError("Phase182 dispatcher missing")
    command = [
        sys.executable,
        str(dispatcher),
        "--machine-attestation", str(Path(args.machine_attestation).resolve()),
        "--evidence-root", str(Path(args.evidence_root).resolve()),
        "dispatch",
        "--run-id", row["run_id"],
        "--executable", str(Path(args.executable).resolve()),
        "--ic-root", str(Path(args.ic_root).resolve()),
        "--run-root", str(Path(args.run_root).resolve()),
        "--mpi-prefix", args.mpi_prefix,
    ]
    if args.mpi_tasks is not None:
        command.extend(["--mpi-tasks", str(args.mpi_tasks)])
    if args.no_generate_ic:
        command.append("--no-generate-ic")
    command.extend(["--max-mem-mb", str(args.max_mem_mb), "--time-limit-cpu", str(args.time_limit_cpu)])

    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name=d3-{row['run_id']}",
        f"#SBATCH --output={path.parent / 'slurm-%j.out'}",
        f"#SBATCH --error={path.parent / 'slurm-%j.err'}",
    ]
    lines.extend(f"#SBATCH {option}" for option in slurm_options)
    lines.extend([
        "set -euo pipefail",
        f"test -r {shlex.quote(str(Path(args.machine_attestation).resolve()))}",
        f"test -x {shlex.quote(str(Path(args.executable).resolve()))}",
        f"mkdir -p {shlex.quote(str(Path(args.evidence_root).resolve()))}",
        shlex.join(command),
    ])
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)


def stage_or_submit(args) -> Dict:
    _, commissioning, blind = frozen_rows()
    executable = Path(args.executable).resolve()
    machine_attestation = Path(args.machine_attestation).resolve()
    att = p181.load_attested(machine_attestation, executable)
    selected = commissioning if args.phase == "commissioning" else blind
    if args.phase == "blind":
        if not args.commissioning_proof:
            raise BatchError("blind phase requires --commissioning-proof")
        load_commissioning_proof(
            Path(args.commissioning_proof), commissioning, att, machine_attestation, executable
        )

    options = p181.validate_slurm_options(args.slurm_option, args.submit)
    batch_root = Path(args.batch_root).resolve()
    jobs_dir = batch_root / args.phase / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for row in selected:
        job = jobs_dir / f"{row['run_id']}.slurm"
        if job.exists():
            raise BatchError(f"refusing to overwrite scheduler job: {job}")
        write_job(job, row, args, options)
        entry = {
            "run_id": row["run_id"],
            "group": row["group"],
            "branch": row["branch"],
            "resolution_tier": row["resolution_tier"],
            "N_total": int(row["N_total"]),
            "seed": int(row["seed"]),
            "blind_analysis": truthy(row["blind_analysis"]),
            "job_script": str(job),
            "job_sha256": sha256_file(job),
            "submitted": False,
        }
        if args.submit:
            p = subprocess.run([args.sbatch, str(job)], check=True, capture_output=True, text=True)
            entry["submitted"] = True
            entry["submission_stdout"] = p.stdout.strip()
        entries.append(entry)

    report = {
        "phase": PHASE,
        "status": "SUBMITTED" if args.submit else "STAGED",
        "campaign_phase": args.phase,
        "manifest_sha256": p181.p174.EXPECTED_MANIFEST_SHA256,
        "selected_runs": len(entries),
        "blind_selected": sum(e["blind_analysis"] for e in entries),
        "commissioning_selected": sum(not e["blind_analysis"] for e in entries),
        "machine_attestation": str(machine_attestation),
        "machine_attestation_sha256": sha256_file(machine_attestation),
        "evidence_executable": str(executable),
        "evidence_executable_sha256": att["evidence_executable_sha256"],
        "evidence_root": str(Path(args.evidence_root).resolve()),
        "dispatcher": str((HERE / "phase182_safe_resume.py").resolve()),
        "dispatcher_sha256": sha256_file(HERE / "phase182_safe_resume.py"),
        "finalizer_sha256": sha256_file(HERE / "phase182_finalize_run.py"),
        "mpi_prefix": args.mpi_prefix,
        "mpi_tasks": args.mpi_tasks,
        "slurm_options": options,
        "entries": entries,
    }
    report_path = batch_root / args.phase / "phase182_batch_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify-commissioning")
    v.add_argument("--run-root", required=True)
    v.add_argument("--evidence-root", required=True)
    v.add_argument("--proof", required=True)
    v.add_argument("--machine-attestation", required=True)
    v.add_argument("--executable", required=True)
    s = sub.add_parser("stage")
    s.add_argument("--phase", choices=["commissioning", "blind"], required=True)
    s.add_argument("--machine-attestation", required=True)
    s.add_argument("--executable", required=True)
    s.add_argument("--ic-root", required=True)
    s.add_argument("--run-root", required=True)
    s.add_argument("--evidence-root", required=True)
    s.add_argument("--batch-root", required=True)
    s.add_argument("--mpi-prefix", default="srun")
    s.add_argument("--mpi-tasks", type=int, default=None)
    s.add_argument("--max-mem-mb", type=int, default=3500)
    s.add_argument("--time-limit-cpu", type=int, default=170000)
    s.add_argument("--no-generate-ic", action="store_true")
    s.add_argument("--slurm-option", action="append", default=[])
    s.add_argument("--commissioning-proof")
    s.add_argument("--submit", action="store_true")
    s.add_argument("--sbatch", default="sbatch")
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "verify-commissioning":
            result = verify_commissioning(
                Path(args.run_root),
                Path(args.evidence_root),
                Path(args.proof),
                Path(args.machine_attestation),
                Path(args.executable),
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 2
        result = stage_or_submit(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        BatchError,
        p181.BatchError,
        finalizer.FinalizeError,
        finalizer.machine.EvidenceGateError,
        p181.p174.BatchError,
        p181.p174.p173.LaunchError,
        p181.p174.p175.ResumeError,
        subprocess.CalledProcessError,
        ValueError,
        OSError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
