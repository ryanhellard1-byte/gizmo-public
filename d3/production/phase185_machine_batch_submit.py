#!/usr/bin/env python3
"""Phase185 machine-attested scheduler with a strict blind-analysis release gate.

Eight non-blind commissioning runs may materialize per-run derived evidence. The
119 blind runs may not. Blind staging requires a current Phase185 PASS proof and
re-verifies all eight commissioning finalizations at release time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_machine_batch_submit as p181  # noqa: E402
import phase185_commissioning_evidence as p185  # noqa: E402

PHASE = 185
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


def verify_blind_evidence_absent(evidence_root: Path, blind: List[Dict[str, str]]) -> None:
    leaked = [str((evidence_root.resolve() / row["run_id"])) for row in blind if (evidence_root.resolve() / row["run_id"]).exists()]
    if leaked:
        raise BatchError(
            "blind per-run derived evidence exists before Phase184 all-127 collection: " + ", ".join(leaked[:8])
        )


def verify_commissioning(
    run_root: Path,
    evidence_root: Path,
    proof_path: Path,
    machine_attestation: Path,
    executable: Path,
) -> Dict:
    att = p181.load_attested(machine_attestation, executable)
    temporary_base = proof_path.with_suffix(proof_path.suffix + ".phase181.tmp")
    base = p181.verify_commissioning(run_root, temporary_base, machine_attestation, executable)
    try:
        if temporary_base.exists():
            temporary_base.unlink()
    except OSError:
        pass

    failures = list(base.get("failures", []))
    _, commissioning, blind = frozen_rows()
    finalized = []
    for row in commissioning:
        rid = row["run_id"]
        try:
            record = p185.verify_finalized(
                evidence_root.resolve() / rid,
                run_root,
                rid,
                executable,
                machine_attestation,
            )
            record_path = evidence_root.resolve() / rid / p185.FINAL_RECORD
            finalized.append({
                "run_id": rid,
                "finalization_record": str(record_path),
                "finalization_record_sha256": sha256_file(record_path),
                "raw_run_directory_sha256": record["raw_run_directory_sha256"],
                "artifacts": record["artifacts"],
            })
        except Exception as exc:
            failures.append(f"{rid}: Phase185 commissioning evidence verification failed: {exc}")

    try:
        verify_blind_evidence_absent(evidence_root, blind)
    except BatchError as exc:
        failures.append(str(exc))

    expected_ids = {r["run_id"] for r in commissioning}
    finalized_ids = {r["run_id"] for r in finalized}
    proof = dict(base)
    proof.update({
        "phase": PHASE,
        "kind": "phase185_nonblind_commissioning_release_gate",
        "base_phase181_status": base.get("status"),
        "status": (
            "PASS"
            if base.get("status") == "PASS" and not failures and finalized_ids == expected_ids
            else "FAIL"
        ),
        "machine_attestation": str(machine_attestation.resolve()),
        "machine_attestation_sha256": sha256_file(machine_attestation),
        "evidence_executable": str(executable.resolve()),
        "evidence_executable_sha256": att["evidence_executable_sha256"],
        "evidence_root": str(evidence_root.resolve()),
        "finalized_commissioning_runs": len(finalized),
        "finalization_records": finalized,
        "blind_per_run_evidence": "ABSENT" if not any("blind per-run" in f for f in failures) else "VIOLATION",
        "blind_policy": "119 blind rows stay raw until Phase184 all-127 collection",
        "failures": failures,
    })
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    return proof


def load_commissioning_proof(
    path: Path,
    commissioning: List[Dict[str, str]],
    blind: List[Dict[str, str]],
    attestation: Dict,
    machine_attestation: Path,
    executable: Path,
    run_root: Path,
    evidence_root: Path,
) -> Dict:
    if not path.is_file():
        raise BatchError(f"commissioning proof missing: {path}")
    try:
        proof = json.loads(path.read_text())
    except Exception as exc:
        raise BatchError(f"invalid commissioning proof JSON: {exc}") from exc

    expected_ids = {r["run_id"] for r in commissioning}
    if proof.get("phase") != PHASE or proof.get("status") != "PASS":
        raise BatchError("commissioning proof is not a Phase185 PASS proof")
    if proof.get("manifest_sha256") != p181.p174.EXPECTED_MANIFEST_SHA256:
        raise BatchError("commissioning proof manifest SHA mismatch")
    if proof.get("commissioning_runs") != EXPECTED_COMMISSIONING or proof.get("complete_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("commissioning proof raw completion count mismatch")
    if proof.get("finalized_commissioning_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("commissioning proof finalized-run count mismatch")
    if set(proof.get("run_ids", [])) != expected_ids:
        raise BatchError("commissioning proof run IDs mismatch")
    if proof.get("machine_attestation_sha256") != sha256_file(machine_attestation):
        raise BatchError("commissioning proof machine-attestation SHA mismatch")
    if proof.get("evidence_executable_sha256") != attestation["evidence_executable_sha256"]:
        raise BatchError("commissioning proof evidence executable SHA mismatch")
    if sha256_file(executable) != attestation["evidence_executable_sha256"]:
        raise BatchError("current evidence executable no longer matches attestation")
    if proof.get("d3_equivalence_status") != "PASS" or proof.get("standard_equal_label_equivalence_status") != "PASS":
        raise BatchError("commissioning proof lacks both Phase181 equivalence PASS gates")
    records = proof.get("finalization_records")
    if not isinstance(records, list) or {r.get("run_id") for r in records} != expected_ids:
        raise BatchError("commissioning proof finalization record IDs mismatch")

    verify_blind_evidence_absent(evidence_root, blind)
    by_id = {str(record["run_id"]): record for record in records}
    for row in commissioning:
        rid = row["run_id"]
        frozen = by_id[rid]
        current = p185.verify_finalized(
            evidence_root.resolve() / rid,
            run_root,
            rid,
            executable,
            machine_attestation,
        )
        record_path = evidence_root.resolve() / rid / p185.FINAL_RECORD
        if sha256_file(record_path) != frozen.get("finalization_record_sha256"):
            raise BatchError(f"{rid}: commissioning finalization record changed since PASS proof")
        if current.get("raw_run_directory_sha256") != frozen.get("raw_run_directory_sha256"):
            raise BatchError(f"{rid}: commissioning raw run digest changed since PASS proof")
        if current.get("artifacts") != frozen.get("artifacts"):
            raise BatchError(f"{rid}: commissioning artifact hashes changed since PASS proof")
    return proof


def write_job(path: Path, row: Dict[str, str], args, slurm_options: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dispatcher = HERE / "phase185_safe_resume.py"
    if not dispatcher.is_file():
        raise BatchError("Phase185 safe-resume dispatcher missing")
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
        shlex.join(command),
    ])
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)


def stage_or_submit(args) -> Dict:
    _, commissioning, blind = frozen_rows()
    executable = Path(args.executable).resolve()
    machine_attestation = Path(args.machine_attestation).resolve()
    run_root = Path(args.run_root).resolve()
    evidence_root = Path(args.evidence_root).resolve()
    att = p181.load_attested(machine_attestation, executable)
    selected = commissioning if args.phase == "commissioning" else blind

    if args.phase == "blind":
        verify_blind_evidence_absent(evidence_root, blind)
        if not args.commissioning_proof:
            raise BatchError("blind phase requires --commissioning-proof")
        load_commissioning_proof(
            Path(args.commissioning_proof),
            commissioning,
            blind,
            att,
            machine_attestation,
            executable,
            run_root,
            evidence_root,
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
            proc = subprocess.run([args.sbatch, str(job)], check=True, capture_output=True, text=True)
            entry["submitted"] = True
            entry["submission_stdout"] = proc.stdout.strip()
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
        "commissioning_evidence_root": str(evidence_root),
        "blind_policy": "No per-run derived evidence for 119 blind rows; Phase184 opens all 127 together",
        "dispatcher": str((HERE / "phase185_safe_resume.py").resolve()),
        "dispatcher_sha256": sha256_file(HERE / "phase185_safe_resume.py"),
        "commissioning_finalizer_sha256": sha256_file(HERE / "phase185_commissioning_evidence.py"),
        "mpi_prefix": args.mpi_prefix,
        "mpi_tasks": args.mpi_tasks,
        "slurm_options": options,
        "entries": entries,
    }
    report_path = batch_root / args.phase / "phase185_batch_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify-commissioning")
    verify.add_argument("--run-root", required=True)
    verify.add_argument("--evidence-root", required=True)
    verify.add_argument("--proof", required=True)
    verify.add_argument("--machine-attestation", required=True)
    verify.add_argument("--executable", required=True)

    stage = sub.add_parser("stage")
    stage.add_argument("--phase", choices=["commissioning", "blind"], required=True)
    stage.add_argument("--machine-attestation", required=True)
    stage.add_argument("--executable", required=True)
    stage.add_argument("--ic-root", required=True)
    stage.add_argument("--run-root", required=True)
    stage.add_argument("--evidence-root", required=True)
    stage.add_argument("--batch-root", required=True)
    stage.add_argument("--mpi-prefix", default="srun")
    stage.add_argument("--mpi-tasks", type=int, default=None)
    stage.add_argument("--max-mem-mb", type=int, default=3500)
    stage.add_argument("--time-limit-cpu", type=int, default=170000)
    stage.add_argument("--no-generate-ic", action="store_true")
    stage.add_argument("--slurm-option", action="append", default=[])
    stage.add_argument("--commissioning-proof")
    stage.add_argument("--submit", action="store_true")
    stage.add_argument("--sbatch", default="sbatch")
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
        p185.CommissioningEvidenceError,
        p181.p174.BatchError,
        p181.p174.p173.LaunchError,
        p181.p174.p175.ResumeError,
        subprocess.CalledProcessError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
