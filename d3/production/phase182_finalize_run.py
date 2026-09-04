#!/usr/bin/env python3
"""Phase182 atomic finalization of one completed Phase181 production run.

Raw GIZMO outputs remain inside the Phase175-fingerprinted run directory. Derived
analysis is written to a separate evidence root so legitimate post-processing
cannot invalidate the raw-simulation integrity digest.

This stage introduces no new physics threshold. It only proves that one completed
run can be transformed deterministically into the three already-frozen evidence
artifacts: run_summary.csv, profiles.csv, and collision_log_summary.csv.
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
import phase172_lock as lock  # noqa: E402
import phase175_safe_resume as p175  # noqa: E402
import phase181_collision_summary as collision  # noqa: E402
import phase181_machine_evidence as machine  # noqa: E402
import phase181_profile_extract as profile  # noqa: E402

PHASE = 182
FINAL_RECORD = "phase182_FINALIZED.json"
RUN_SUMMARY = "run_summary.csv"
PROFILES = "profiles.csv"
COLLISIONS = "collision_log_summary.csv"
PROFILE_REPORT = "phase181_profile_report.json"
COLLISION_REPORT = "phase181_collision_report.json"
MANIFEST_COPY = "phase172_manifest.csv"
RUN_SUMMARY_COLUMNS = [
    "run_id", "branch", "group", "resolution_tier", "seed", "status", "final_time_Gyr",
    "executable_sha256", "machine_attestation_sha256", "raw_run_directory_sha256",
    "completion_record", "completion_record_sha256", "profiles_sha256",
    "collision_log_summary_sha256", "profile_rows", "collision_rows",
]
ARTIFACT_NAMES = (
    RUN_SUMMARY,
    PROFILES,
    COLLISIONS,
    PROFILE_REPORT,
    COLLISION_REPORT,
    MANIFEST_COPY,
)


class FinalizeError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def frozen_campaign() -> Tuple[bytes, List[Dict[str, str]]]:
    raw, rows = lock.load()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != machine.PHASE172_MANIFEST_SHA256:
        raise FinalizeError(
            f"Phase172 manifest SHA drift: {observed} != {machine.PHASE172_MANIFEST_SHA256}"
        )
    if len(rows) != 127:
        raise FinalizeError(f"Phase172 campaign cardinality drift: {len(rows)} != 127")
    for row in rows:
        p175.p173.validate_row(row)
    return raw, rows


def one_row(rows: List[Dict[str, str]], run_id: str) -> Dict[str, str]:
    hits = [r for r in rows if str(r.get("run_id")) == str(run_id)]
    if len(hits) != 1:
        raise FinalizeError(f"expected one frozen manifest row for {run_id}, found {len(hits)}")
    return hits[0]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def require_outside_raw_runs(
    candidate: Path,
    run_root: Path,
    rows: List[Dict[str, str]],
    label: str,
) -> None:
    """Reject a derived-output path nested in any frozen raw run directory."""
    candidate = candidate.resolve()
    run_root = run_root.resolve()
    for row in rows:
        raw_dir = run_root / str(row["run_id"])
        if is_within(candidate, raw_dir):
            raise FinalizeError(
                f"{label} must live outside every fingerprinted raw run directory; "
                f"candidate={candidate} raw_run_dir={raw_dir}"
            )


def verify_raw_completion(
    run_root: Path,
    run_id: str,
    executable: Path,
    attestation_path: Path,
    row: Dict[str, str],
) -> Dict:
    run_dir = run_root.resolve() / run_id
    if not run_dir.is_dir():
        raise FinalizeError(f"raw run directory missing: {run_dir}")
    provenance = machine.provenance_from_attestation(attestation_path, executable)
    pre = p175.verify_prelaunch(run_dir, row, executable, provenance)
    complete, post, source = p175.post_is_complete(run_dir)
    if not complete or post is None or source is None:
        raise FinalizeError(f"{run_id}: raw simulation is not COMPLETE")
    integrity = p175.verify_completion_integrity(run_dir, post, source)
    return {
        "run_dir": run_dir,
        "prelaunch": pre,
        "post": post,
        "completion_record": source,
        "completion_record_path": run_dir / source,
        "integrity": integrity,
        "provenance": provenance,
    }


def observed_final_time_gyr(profile_report: Dict) -> float:
    sources = profile_report.get("source_snapshots")
    if not isinstance(sources, list) or not sources:
        raise FinalizeError("profile report lacks source snapshots")
    final_path = Path(str(sources[-1].get("path", "")))
    if not final_path.is_file():
        raise FinalizeError(f"final source snapshot missing: {final_path}")
    snap = profile.read_gadget_format1(final_path)
    observed = float(snap.time_code) * profile.TIME_UNIT_GYR
    required = float(profile.EXPECTED_TIMES_GYR[-1])
    if abs(observed - required) > profile.TIME_TOL_GYR:
        raise FinalizeError(
            f"final snapshot time drift: observed={observed:.12g} required={required:.12g} Gyr"
        )
    return observed


def write_run_summary(path: Path, row: Dict[str, str], payload: Dict) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RUN_SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "run_id": row["run_id"],
            "branch": row["branch"],
            "group": row["group"],
            "resolution_tier": row["resolution_tier"],
            "seed": row["seed"],
            "status": "COMPLETE",
            "final_time_Gyr": f"{payload['final_time_Gyr']:.12g}",
            "executable_sha256": payload["executable_sha256"],
            "machine_attestation_sha256": payload["machine_attestation_sha256"],
            "raw_run_directory_sha256": payload["raw_run_directory_sha256"],
            "completion_record": payload["completion_record"],
            "completion_record_sha256": payload["completion_record_sha256"],
            "profiles_sha256": payload["profiles_sha256"],
            "collision_log_summary_sha256": payload["collision_log_summary_sha256"],
            "profile_rows": payload["profile_rows"],
            "collision_rows": payload["collision_rows"],
        })


def verify_finalized(
    evidence_dir: Path,
    run_root: Path,
    run_id: str,
    executable: Path,
    attestation_path: Path,
) -> Dict:
    raw, rows = frozen_campaign()
    require_outside_raw_runs(evidence_dir, run_root, rows, "derived evidence directory")
    row = one_row(rows, run_id)

    record_path = evidence_dir / FINAL_RECORD
    if not record_path.is_file():
        raise FinalizeError(f"finalization record missing: {record_path}")
    try:
        record = json.loads(record_path.read_text())
    except Exception as exc:
        raise FinalizeError(f"invalid finalization record: {exc}") from exc
    if record.get("phase") != PHASE or record.get("status") != "PASS" or record.get("run_id") != run_id:
        raise FinalizeError(f"{run_id}: finalization record identity/status mismatch")

    raw_state = verify_raw_completion(run_root, run_id, executable, attestation_path, row)
    expected = {
        "phase172_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "evidence_executable_sha256": sha256_file(executable),
        "machine_attestation_sha256": sha256_file(attestation_path),
        "raw_run_directory_sha256": raw_state["integrity"]["run_directory_sha256"],
        "completion_record": raw_state["completion_record"],
        "completion_record_sha256": sha256_file(raw_state["completion_record_path"]),
    }
    bad = {k: {"observed": record.get(k), "expected": v} for k, v in expected.items() if record.get(k) != v}
    if bad:
        raise FinalizeError(f"{run_id}: finalized provenance drift: {bad}")

    artifacts = record.get("artifacts")
    if not isinstance(artifacts, dict):
        raise FinalizeError(f"{run_id}: finalization record lacks artifact hashes")
    for name in ARTIFACT_NAMES:
        path = evidence_dir / name
        if not path.is_file():
            raise FinalizeError(f"{run_id}: finalized artifact missing: {name}")
        observed = sha256_file(path)
        expected_sha = artifacts.get(name)
        if observed != expected_sha:
            raise FinalizeError(f"{run_id}: finalized artifact changed: {name} {observed} != {expected_sha}")
    return record


def finalize(
    run_id: str,
    run_root: Path,
    evidence_root: Path,
    executable: Path,
    attestation_path: Path,
) -> Dict:
    run_root = run_root.resolve()
    evidence_root = evidence_root.resolve()
    executable = executable.resolve()
    attestation_path = attestation_path.resolve()
    evidence_dir = evidence_root / run_id

    raw, rows = frozen_campaign()
    require_outside_raw_runs(evidence_dir, run_root, rows, "derived evidence directory")
    row = one_row(rows, run_id)

    if evidence_dir.exists():
        record = verify_finalized(evidence_dir, run_root, run_id, executable, attestation_path)
        return {**record, "status": "ALREADY_FINALIZED", "evidence_dir": str(evidence_dir)}

    raw_state = verify_raw_completion(run_root, run_id, executable, attestation_path, row)
    run_dir = raw_state["run_dir"]
    pre = raw_state["prelaunch"]

    evidence_root.mkdir(parents=True, exist_ok=True)
    tmp = evidence_root / f".{run_id}.phase182.tmp.{os.getpid()}"
    require_outside_raw_runs(tmp, run_root, rows, "finalization temporary directory")
    if tmp.exists():
        raise FinalizeError(f"refusing to reuse finalization temp directory: {tmp}")
    tmp.mkdir()
    try:
        manifest_path = tmp / MANIFEST_COPY
        manifest_path.write_bytes(raw)

        profile.load_manifest(manifest_path, run_id)
        profile_rows, profile_report = profile.build_profiles(
            run_id, Path(str(pre["ic"])), run_dir
        )
        profiles_path = tmp / PROFILES
        profile.write_profiles(profiles_path, profile_rows)
        (tmp / PROFILE_REPORT).write_text(json.dumps(profile_report, indent=2, sort_keys=True) + "\n")

        _, manifest_rows = collision.load_manifest(manifest_path)
        collision_row = collision.find_manifest_row(manifest_rows, run_id)
        collision_rows, collision_report = collision.summarize(collision_row, run_dir / "gizmo.log")
        collisions_path = tmp / COLLISIONS
        collision.write_csv(collisions_path, collision_rows)
        (tmp / COLLISION_REPORT).write_text(json.dumps(collision_report, indent=2, sort_keys=True) + "\n")

        final_time = observed_final_time_gyr(profile_report)
        att_sha = sha256_file(attestation_path)
        exe_sha = sha256_file(executable)
        if exe_sha != raw_state["post"].get("executable_sha256"):
            raise FinalizeError("completed run executable SHA no longer matches evidence executable")
        payload = {
            "final_time_Gyr": final_time,
            "executable_sha256": exe_sha,
            "machine_attestation_sha256": att_sha,
            "raw_run_directory_sha256": raw_state["integrity"]["run_directory_sha256"],
            "completion_record": raw_state["completion_record"],
            "completion_record_sha256": sha256_file(raw_state["completion_record_path"]),
            "profiles_sha256": sha256_file(profiles_path),
            "collision_log_summary_sha256": sha256_file(collisions_path),
            "profile_rows": len(profile_rows),
            "collision_rows": len(collision_rows),
        }
        write_run_summary(tmp / RUN_SUMMARY, row, payload)

        artifacts = {name: sha256_file(tmp / name) for name in ARTIFACT_NAMES}
        record = {
            "phase": PHASE,
            "status": "PASS",
            "kind": "atomic_external_per_run_evidence_finalization",
            "run_id": run_id,
            "phase172_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            "evidence_executable_sha256": exe_sha,
            "machine_attestation_sha256": att_sha,
            "raw_run_directory": str(run_dir),
            "raw_run_directory_sha256": raw_state["integrity"]["run_directory_sha256"],
            "completion_record": raw_state["completion_record"],
            "completion_record_sha256": payload["completion_record_sha256"],
            "final_time_Gyr": final_time,
            "profile_rows": len(profile_rows),
            "collision_rows": len(collision_rows),
            "artifacts": artifacts,
        }
        (tmp / FINAL_RECORD).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, evidence_dir)
        return {**record, "evidence_dir": str(evidence_dir)}
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
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
    except (
        FinalizeError,
        machine.EvidenceGateError,
        p175.ResumeError,
        p175.p173.LaunchError,
        profile.ProfileError,
        collision.EvidenceError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
