#!/usr/bin/env python3
"""Phase174 batch scheduler wrapper around the provenance-locked Phase173 launcher.

Phase174 adds no physics. It stages/submits the frozen campaign in two explicit
phases:
  1) exactly 8 non-claim R0 commissioning runs;
  2) exactly 119 blind runs, releasable only after a machine-readable
     commissioning PASS proof exists.

Each scheduler job delegates all IC, executable, parameter, completion, and
fingerprint checks to phase173_production_launcher.py.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase173_production_launcher as p173  # noqa: E402

EXPECTED_TOTAL = 127
EXPECTED_COMMISSIONING = 8
EXPECTED_BLIND = 119
EXPECTED_MANIFEST_SHA256 = p173.EXPECTED_MANIFEST_SHA256


class BatchError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def truthy(value: str) -> bool:
    return str(value).strip().lower() == "true"


def frozen_rows():
    raw, rows = p173.frozen_manifest()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_MANIFEST_SHA256:
        raise BatchError("Phase172 manifest hash changed")
    if len(rows) != EXPECTED_TOTAL:
        raise BatchError(f"expected {EXPECTED_TOTAL} rows, got {len(rows)}")
    for row in rows:
        p173.validate_row(row)
    commissioning = [r for r in rows if r["group"] == "R0_commissioning_not_for_claims"]
    blind = [r for r in rows if truthy(r["blind_analysis"])]
    nonblind = [r for r in rows if not truthy(r["blind_analysis"])]
    if len(commissioning) != EXPECTED_COMMISSIONING or len(nonblind) != EXPECTED_COMMISSIONING:
        raise BatchError(
            f"commissioning cardinality changed: group={len(commissioning)} nonblind={len(nonblind)}"
        )
    if {r["run_id"] for r in commissioning} != {r["run_id"] for r in nonblind}:
        raise BatchError("non-blind rows are no longer exactly the R0 commissioning set")
    if len(blind) != EXPECTED_BLIND:
        raise BatchError(f"blind cardinality changed: {len(blind)}")
    return rows, commissioning, blind


def validate_slurm_options(options: list[str], for_submit: bool) -> list[str]:
    clean = []
    for option in options:
        option = option.strip()
        if not option.startswith("--") or "\n" in option or "\r" in option:
            raise BatchError(f"invalid --slurm-option value: {option!r}")
        clean.append(option)
    if for_submit and not clean:
        raise BatchError("submission requires explicit --slurm-option resource settings")
    return clean


def write_job(path: Path, row: dict[str, str], args, slurm_options: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    launcher = HERE / "phase173_production_launcher.py"
    if not launcher.is_file():
        raise BatchError("Phase173 launcher missing")

    command = [
        sys.executable, str(launcher), "run",
        "--run-id", row["run_id"],
        "--executable", str(Path(args.executable).resolve()),
        "--ic-root", str(Path(args.ic_root).resolve()),
        "--run-root", str(Path(args.run_root).resolve()),
        "--mpi-prefix", args.mpi_prefix,
    ]
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name=d3-{row['run_id']}",
        f"#SBATCH --output={path.parent / 'slurm-%j.out'}",
        f"#SBATCH --error={path.parent / 'slurm-%j.err'}",
    ]
    lines.extend(f"#SBATCH {option}" for option in slurm_options)
    lines.extend([
        "set -euo pipefail",
        f"test -x {shlex.quote(str(Path(args.executable).resolve()))}",
        shlex.join(command),
    ])
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)


def verify_commissioning(run_root: Path, proof_path: Path) -> dict:
    _, commissioning, _ = frozen_rows()
    records = []
    failures = []
    for row in commissioning:
        run_id = row["run_id"]
        post_path = run_root / run_id / "phase173_POST.json"
        if not post_path.is_file():
            failures.append(f"{run_id}: missing phase173_POST.json")
            continue
        try:
            post = json.loads(post_path.read_text())
        except Exception as exc:
            failures.append(f"{run_id}: invalid phase173_POST.json: {exc}")
            continue
        if post.get("run_id") != run_id:
            failures.append(f"{run_id}: post run_id mismatch")
        if post.get("status") != "COMPLETE":
            failures.append(f"{run_id}: status={post.get('status')!r}")
        if post.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
            failures.append(f"{run_id}: manifest SHA mismatch")
        if post.get("manifest_row") != row:
            failures.append(f"{run_id}: manifest row mismatch")
        required = int(post.get("required_snapshot_count", -1))
        observed = int(post.get("snapshot_count", -1))
        if required < 10 or observed < required:
            failures.append(f"{run_id}: snapshots {observed}/{required}")
        if not post.get("completion_marker") or post.get("fatal_marker"):
            failures.append(f"{run_id}: GIZMO completion/fatal marker gate failed")
        records.append({
            "run_id": run_id,
            "post_sha256": sha256_file(post_path),
            "snapshot_count": observed,
            "required_snapshot_count": required,
            "status": post.get("status"),
        })

    proof = {
        "phase": 174,
        "kind": "commissioning_release_gate",
        "status": "PASS" if not failures and len(records) == EXPECTED_COMMISSIONING else "FAIL",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "commissioning_runs": EXPECTED_COMMISSIONING,
        "complete_runs": sum(r["status"] == "COMPLETE" for r in records),
        "run_ids": [r["run_id"] for r in records],
        "failures": failures,
        "records": records,
    }
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    return proof


def load_commissioning_proof(path: Path, commissioning: list[dict[str, str]]) -> dict:
    if not path.is_file():
        raise BatchError(f"commissioning proof missing: {path}")
    proof = json.loads(path.read_text())
    expected_ids = {r["run_id"] for r in commissioning}
    if proof.get("status") != "PASS":
        raise BatchError("commissioning proof is not PASS")
    if proof.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise BatchError("commissioning proof manifest SHA mismatch")
    if proof.get("commissioning_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("commissioning proof count mismatch")
    if proof.get("complete_runs") != EXPECTED_COMMISSIONING:
        raise BatchError("not all commissioning runs are COMPLETE")
    if set(proof.get("run_ids", [])) != expected_ids:
        raise BatchError("commissioning proof run IDs mismatch")
    return proof


def stage_or_submit(args) -> dict:
    _, commissioning, blind = frozen_rows()
    selected = commissioning if args.phase == "commissioning" else blind
    if args.phase == "blind":
        if not args.commissioning_proof:
            raise BatchError("blind phase requires --commissioning-proof")
        load_commissioning_proof(Path(args.commissioning_proof), commissioning)

    executable = Path(args.executable)
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise BatchError(f"executable missing/not executable: {executable}")
    # The Phase173 launcher will re-check the exact production SHA inside every job.

    options = validate_slurm_options(args.slurm_option, args.submit)
    batch_root = Path(args.batch_root).resolve()
    jobs_dir = batch_root / args.phase / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for row in selected:
        job = jobs_dir / f"{row['run_id']}.slurm"
        if job.exists():
            raise BatchError(f"refusing to overwrite existing scheduler job: {job}")
        write_job(job, row, args, options)
        entry = {
            "run_id": row["run_id"],
            "group": row["group"],
            "branch": row["branch"],
            "resolution_tier": row["resolution_tier"],
            "N_total": int(row["N_total"]),
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
        "phase": 174,
        "status": "SUBMITTED" if args.submit else "STAGED",
        "campaign_phase": args.phase,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "selected_runs": len(entries),
        "blind_selected": sum(e["blind_analysis"] for e in entries),
        "commissioning_selected": sum(not e["blind_analysis"] for e in entries),
        "phase173_executable_sha256": p173.EXPECTED_EXECUTABLE_SHA256,
        "phase173_workflow_run_id": p173.EXPECTED_WORKFLOW_RUN_ID,
        "slurm_options": options,
        "entries": entries,
    }
    report_path = batch_root / args.phase / "phase174_batch_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    v = sub.add_parser("verify-commissioning")
    v.add_argument("--run-root", required=True)
    v.add_argument("--proof", required=True)

    s = sub.add_parser("stage")
    s.add_argument("--phase", choices=["commissioning", "blind"], required=True)
    s.add_argument("--executable", required=True)
    s.add_argument("--ic-root", required=True)
    s.add_argument("--run-root", required=True)
    s.add_argument("--batch-root", required=True)
    s.add_argument("--mpi-prefix", default="srun")
    s.add_argument("--slurm-option", action="append", default=[])
    s.add_argument("--commissioning-proof", default=None)
    s.add_argument("--submit", action="store_true")
    s.add_argument("--sbatch", default="sbatch")

    args = ap.parse_args()
    try:
        if args.command == "verify-commissioning":
            result = verify_commissioning(Path(args.run_root), Path(args.proof))
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 2
        result = stage_or_submit(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (BatchError, p173.LaunchError, subprocess.CalledProcessError, ValueError, OSError) as exc:
        print(json.dumps({"phase": 174, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
