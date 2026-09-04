#!/usr/bin/env python3
"""Phase185 atomic evidence finalizer for the eight non-blind commissioning runs.

This deliberately refuses all 119 blind rows. The blind campaign remains raw until
Phase184 collects all 127 runs together, preserving the frozen blind-analysis
boundary while still allowing commissioning evidence to gate blind release.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_machine_batch_submit as p181_batch  # noqa: E402
import phase184_campaign_evidence as p184  # noqa: E402

PHASE = 185
FINAL_RECORD = "phase185_COMMISSIONED.json"
RUN_SUMMARY = "run_summary.csv"
PROFILES = "profiles.csv"
COLLISIONS = "collision_log_summary.csv"
ARTIFACT_NAMES = (RUN_SUMMARY, PROFILES, COLLISIONS)


class CommissioningEvidenceError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def campaign_rows() -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    rows, commissioning, blind = p181_batch.frozen_rows()
    if len(rows) != 127 or len(commissioning) != 8 or len(blind) != 119:
        raise CommissioningEvidenceError(
            f"frozen campaign cardinality changed total={len(rows)} commissioning={len(commissioning)} blind={len(blind)}"
        )
    return rows, commissioning, blind


def commissioning_row(run_id: str) -> Dict[str, str]:
    _, commissioning, blind = campaign_rows()
    blind_ids = {str(row["run_id"]) for row in blind}
    if run_id in blind_ids:
        raise CommissioningEvidenceError(
            f"{run_id}: refusing per-run derived evidence for blind row; Phase184 must open blind evidence only after all 127 runs complete"
        )
    hits = [row for row in commissioning if str(row["run_id"]) == run_id]
    if len(hits) != 1:
        raise CommissioningEvidenceError(f"{run_id}: not an exact frozen commissioning run")
    return hits[0]


def require_external(path: Path, run_root: Path, label: str) -> None:
    rows, _, _ = campaign_rows()
    try:
        p184._require_external_output(path, run_root, rows, label)
    except p184.CollectionError as exc:
        raise CommissioningEvidenceError(str(exc)) from exc


def write_csv(path: Path, columns: List[str], rows: List[Dict]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def current_raw(
    run_id: str,
    run_root: Path,
    executable: Path,
    machine_attestation: Path,
) -> Tuple[Dict[str, str], Dict, Dict]:
    row = commissioning_row(run_id)
    try:
        att = p181_batch.load_attested(machine_attestation, executable)
        info = p184.preflight_one(row, run_root.resolve(), att)
    except Exception as exc:
        raise CommissioningEvidenceError(f"{run_id}: raw commissioning preflight failed: {exc}") from exc
    return row, att, info


def verify_finalized(
    evidence_dir: Path,
    run_root: Path,
    run_id: str,
    executable: Path,
    machine_attestation: Path,
) -> Dict:
    evidence_dir = evidence_dir.resolve()
    run_root = run_root.resolve()
    executable = executable.resolve()
    machine_attestation = machine_attestation.resolve()
    require_external(evidence_dir, run_root, "commissioning evidence directory")
    row, att, info = current_raw(run_id, run_root, executable, machine_attestation)

    record_path = evidence_dir / FINAL_RECORD
    if not record_path.is_file():
        raise CommissioningEvidenceError(f"{run_id}: commissioning finalization record missing")
    try:
        record = json.loads(record_path.read_text())
    except Exception as exc:
        raise CommissioningEvidenceError(f"{run_id}: invalid commissioning finalization record: {exc}") from exc
    if record.get("phase") != PHASE or record.get("status") != "PASS" or record.get("run_id") != run_id:
        raise CommissioningEvidenceError(f"{run_id}: commissioning finalization identity/status mismatch")

    expected = {
        "manifest_sha256": p184.EXPECTED_MANIFEST_SHA256,
        "manifest_row": row,
        "machine_attestation_sha256": sha256_file(machine_attestation),
        "evidence_executable_sha256": att["evidence_executable_sha256"],
        "completion_record": info["post_path"].name,
        "completion_record_sha256": sha256_file(info["post_path"]),
        "raw_run_directory_sha256": info["integrity"]["run_directory_sha256"],
        "gizmo_log_sha256": info["log_sha256"],
    }
    bad = {key: {"observed": record.get(key), "expected": value} for key, value in expected.items() if record.get(key) != value}
    if bad:
        raise CommissioningEvidenceError(f"{run_id}: commissioning provenance changed: {bad}")

    artifacts = record.get("artifacts")
    if not isinstance(artifacts, dict):
        raise CommissioningEvidenceError(f"{run_id}: commissioning artifact hash map missing")
    for name in ARTIFACT_NAMES:
        path = evidence_dir / name
        if not path.is_file():
            raise CommissioningEvidenceError(f"{run_id}: commissioning artifact missing: {name}")
        observed = sha256_file(path)
        if artifacts.get(name) != observed:
            raise CommissioningEvidenceError(
                f"{run_id}: commissioning artifact changed: {name} {observed} != {artifacts.get(name)}"
            )
    return record


def finalize(
    run_id: str,
    run_root: Path,
    evidence_root: Path,
    executable: Path,
    machine_attestation: Path,
) -> Dict:
    run_root = run_root.resolve()
    evidence_root = evidence_root.resolve()
    executable = executable.resolve()
    machine_attestation = machine_attestation.resolve()
    evidence_dir = evidence_root / run_id
    require_external(evidence_dir, run_root, "commissioning evidence directory")

    if evidence_dir.exists():
        record = verify_finalized(evidence_dir, run_root, run_id, executable, machine_attestation)
        return {**record, "status": "ALREADY_FINALIZED", "evidence_dir": str(evidence_dir)}

    row, att, info = current_raw(run_id, run_root, executable, machine_attestation)
    try:
        summary, profiles, collisions, detail = p184.collect_one(row, info)
    except Exception as exc:
        raise CommissioningEvidenceError(f"{run_id}: commissioning evidence extraction failed: {exc}") from exc

    evidence_root.mkdir(parents=True, exist_ok=True)
    stage = evidence_root / f".{run_id}.phase185-staging-{os.getpid()}"
    require_external(stage, run_root, "commissioning evidence staging directory")
    if stage.exists():
        raise CommissioningEvidenceError(f"{run_id}: commissioning staging directory already exists: {stage}")
    stage.mkdir()
    try:
        write_csv(stage / RUN_SUMMARY, p184.RUN_COLUMNS, [summary])
        write_csv(stage / PROFILES, p184.p181_profile.PROFILE_COLUMNS, profiles)
        write_csv(stage / COLLISIONS, p184.p181_collision.OUTPUT_COLUMNS, collisions)
        artifacts = {name: sha256_file(stage / name) for name in ARTIFACT_NAMES}
        record = {
            "phase": PHASE,
            "status": "PASS",
            "kind": "nonblind_commissioning_evidence",
            "run_id": run_id,
            "manifest_sha256": p184.EXPECTED_MANIFEST_SHA256,
            "manifest_row": row,
            "machine_attestation_sha256": sha256_file(machine_attestation),
            "evidence_executable_sha256": att["evidence_executable_sha256"],
            "completion_record": info["post_path"].name,
            "completion_record_sha256": sha256_file(info["post_path"]),
            "raw_run_directory_sha256": info["integrity"]["run_directory_sha256"],
            "gizmo_log_sha256": info["log_sha256"],
            "profile_rows": len(profiles),
            "collision_rows": len(collisions),
            "profile_80Gyr_snapshot_sha256": detail.get("profile_80Gyr_snapshot_sha256"),
            "artifacts": artifacts,
            "blind_policy": "NONBLIND_COMMISSIONING_ONLY",
        }
        (stage / FINAL_RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        os.replace(stage, evidence_dir)
        return {**record, "evidence_dir": str(evidence_dir)}
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--run-root", required=True)
    p.add_argument("--evidence-root", required=True)
    p.add_argument("--executable", required=True)
    p.add_argument("--machine-attestation", required=True)
    p.add_argument("--verify-only", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        evidence_dir = Path(args.evidence_root).resolve() / args.run_id
        if args.verify_only:
            result = verify_finalized(
                evidence_dir,
                Path(args.run_root),
                args.run_id,
                Path(args.executable),
                Path(args.machine_attestation),
            )
            result = {**result, "status": "VERIFIED", "evidence_dir": str(evidence_dir)}
        else:
            result = finalize(
                args.run_id,
                Path(args.run_root),
                Path(args.evidence_root),
                Path(args.executable),
                Path(args.machine_attestation),
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (CommissioningEvidenceError, OSError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
