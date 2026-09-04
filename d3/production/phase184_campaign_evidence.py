#!/usr/bin/env python3
"""Phase184 fail-closed campaign evidence collector.

Reads the immutable Phase175/181 production run directories and writes the three
campaign-level artifacts consumed by the frozen Phase172/174 validation stack:
run_summary.csv, profiles.csv, and collision_log_summary.csv.

The collector never writes into a completed GIZMO run directory. That preserves
the Phase175 completion-directory fingerprints. All outputs are staged in a
sibling temporary evidence directory, structurally validated against the embedded
frozen Phase172 manifest, and atomically promoted as one directory only after
every manifest run passes.
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
from typing import Dict, Iterable, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import phase172_time_contract as p172_time  # noqa: E402
import phase174_batch_submit as p174  # noqa: E402
import phase175_safe_resume as p175  # noqa: E402
import phase181_collision_summary as p181_collision  # noqa: E402
import phase181_machine_batch_submit as p181_batch  # noqa: E402
import phase181_profile_extract as p181_profile  # noqa: E402

PHASE = 184
EXPECTED_MANIFEST_SHA256 = p174.EXPECTED_MANIFEST_SHA256
EXPECTED_TOTAL = p174.EXPECTED_TOTAL
EXPECTED_FINAL_TIME_GYR = 80.0
RUN_COLUMNS = [
    "run_id", "branch", "group", "resolution_tier", "seed", "status",
    "final_time_Gyr", "completion_record", "completion_record_sha256",
    "run_directory_sha256", "executable_sha256", "ic_sha256",
    "gizmo_log_sha256", "profile_rows", "profile_80Gyr_snapshot_sha256",
    "collision_rows", "collision_source_log_sha256",
]


class CollectionError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def frozen_manifest() -> Tuple[bytes, List[Dict[str, str]]]:
    raw, rows = p174.p173.frozen_manifest()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_MANIFEST_SHA256:
        raise CollectionError(
            f"embedded Phase172 manifest SHA mismatch: {observed} != {EXPECTED_MANIFEST_SHA256}"
        )
    if len(rows) != EXPECTED_TOTAL:
        raise CollectionError(f"expected {EXPECTED_TOTAL} manifest rows, found {len(rows)}")
    ids = [str(r["run_id"]) for r in rows]
    if len(ids) != len(set(ids)):
        raise CollectionError("duplicate run_id in frozen manifest")
    for row in rows:
        p174.p173.validate_row(row)
    return raw, rows


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _require_external_output(output: Path, run_root: Path, rows: Iterable[Dict[str, str]], label: str) -> None:
    output = output.resolve()
    run_root = run_root.resolve()
    for row in rows:
        raw_dir = run_root / str(row["run_id"])
        if _is_within(output, raw_dir):
            raise CollectionError(
                f"{label} must live outside every fingerprinted raw run directory; "
                f"candidate={output} raw_run_dir={raw_dir}"
            )


def preflight_one(row: Dict[str, str], run_root: Path, attestation: Dict) -> Dict:
    run_id = str(row["run_id"])
    run_dir = run_root / run_id
    if not run_dir.is_dir():
        raise CollectionError(f"{run_id}: run directory missing: {run_dir}")

    post_path, post = p174.completion_record(run_dir)
    if post_path is None or post is None:
        raise CollectionError(f"{run_id}: no COMPLETE Phase175/Phase173 completion record")
    if post.get("run_id") != run_id:
        raise CollectionError(f"{run_id}: completion run_id mismatch")
    if post.get("status") != "COMPLETE":
        raise CollectionError(f"{run_id}: completion status is not COMPLETE")
    if post.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise CollectionError(f"{run_id}: completion manifest SHA mismatch")
    if post.get("manifest_row") != row:
        raise CollectionError(f"{run_id}: completion manifest row mismatch")
    if not post.get("completion_marker") or post.get("fatal_marker"):
        raise CollectionError(f"{run_id}: completion/fatal marker gate failed")

    try:
        required = int(post.get("required_snapshot_count", -1))
        observed = int(post.get("snapshot_count", -1))
    except Exception as exc:
        raise CollectionError(f"{run_id}: invalid snapshot-count evidence") from exc
    if required < 10 or observed < required:
        raise CollectionError(f"{run_id}: snapshots {observed}/{required}")

    try:
        p181_batch.verify_evidence_completion(post, attestation)
    except Exception as exc:
        raise CollectionError(f"{run_id}: Phase181 evidence provenance failed: {exc}") from exc

    try:
        integrity = p175.verify_completion_integrity(run_dir, post, post_path.name)
    except Exception as exc:
        raise CollectionError(f"{run_id}: completion-directory fingerprint failed: {exc}") from exc

    ic = Path(str(post.get("ic", "")))
    expected_ic_sha = str(post.get("ic_sha256", ""))
    if not ic.is_file() or not expected_ic_sha:
        raise CollectionError(f"{run_id}: IC path/hash missing from completion evidence")
    observed_ic_sha = sha256_file(ic)
    if observed_ic_sha != expected_ic_sha:
        raise CollectionError(f"{run_id}: IC SHA changed: {observed_ic_sha} != {expected_ic_sha}")

    log = run_dir / "gizmo.log"
    if not log.is_file():
        raise CollectionError(f"{run_id}: gizmo.log missing")
    log_sha = sha256_file(log)

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "post_path": post_path,
        "post": post,
        "integrity": integrity,
        "ic": ic,
        "log": log,
        "log_sha256": log_sha,
    }


def preflight_all(rows: Iterable[Dict[str, str]], run_root: Path, attestation: Dict) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for row in rows:
        info = preflight_one(row, run_root, attestation)
        out[info["run_id"]] = info
    return out


def collect_one(row: Dict[str, str], info: Dict) -> Tuple[Dict[str, object], List[Dict[str, object]], List[Dict[str, object]], Dict]:
    run_id = str(row["run_id"])
    profile_rows, profile_report = p181_profile.build_profiles(run_id, Path(info["ic"]), Path(info["run_dir"]))
    if profile_report.get("status") != "PASS" or profile_report.get("run_id") != run_id:
        raise CollectionError(f"{run_id}: invalid Phase181 profile report")

    source = list(profile_report.get("source_snapshots", []))
    final_sources = [
        x for x in source
        if abs(float(x.get("time_Gyr", -1.0)) - EXPECTED_FINAL_TIME_GYR) <= p181_profile.TIME_TOL_GYR
    ]
    if len(final_sources) != 1:
        raise CollectionError(f"{run_id}: expected exactly one verified 80-Gyr profile source, found {len(final_sources)}")
    final_snapshot_sha = str(final_sources[0].get("sha256", ""))
    if not final_snapshot_sha:
        raise CollectionError(f"{run_id}: 80-Gyr source snapshot lacks SHA256")

    collision_rows, collision_report = p181_collision.summarize(row, Path(info["log"]))
    if collision_report.get("status") != "PASS" or collision_report.get("run_id") != run_id:
        raise CollectionError(f"{run_id}: invalid Phase181 collision report")
    collision_log_sha = str(collision_report.get("source_log_sha256", info["log_sha256"]))
    if collision_log_sha != info["log_sha256"]:
        raise CollectionError(
            f"{run_id}: collision extractor log SHA mismatch: {collision_log_sha} != {info['log_sha256']}"
        )

    post = info["post"]
    post_path = info["post_path"]
    summary = {
        "run_id": run_id,
        "branch": row["branch"],
        "group": row["group"],
        "resolution_tier": row["resolution_tier"],
        "seed": row["seed"],
        "status": "COMPLETE",
        "final_time_Gyr": f"{EXPECTED_FINAL_TIME_GYR:.17g}",
        "completion_record": post_path.name,
        "completion_record_sha256": sha256_file(post_path),
        "run_directory_sha256": info["integrity"]["run_directory_sha256"],
        "executable_sha256": post.get("executable_sha256", ""),
        "ic_sha256": post.get("ic_sha256", ""),
        "gizmo_log_sha256": info["log_sha256"],
        "profile_rows": len(profile_rows),
        "profile_80Gyr_snapshot_sha256": final_snapshot_sha,
        "collision_rows": len(collision_rows),
        "collision_source_log_sha256": collision_log_sha,
    }
    detail = {
        "run_id": run_id,
        "completion_record": post_path.name,
        "run_directory_sha256": info["integrity"]["run_directory_sha256"],
        "profile_rows": len(profile_rows),
        "collision_rows": len(collision_rows),
        "profile_80Gyr_snapshot_sha256": final_snapshot_sha,
        "gizmo_log_sha256": info["log_sha256"],
    }
    return summary, profile_rows, collision_rows, detail


def _open_writer(path: Path, columns: List[str]):
    fh = path.open("w", newline="")
    writer = csv.DictWriter(fh, fieldnames=columns)
    writer.writeheader()
    return fh, writer


def _refuse_existing(output_dir: Path) -> None:
    if output_dir.exists():
        raise CollectionError(f"refusing to overwrite existing campaign evidence directory: {output_dir}")


def collect_campaign(run_root: Path, output_dir: Path, machine_attestation: Path, executable: Path) -> Dict:
    run_root = run_root.resolve()
    output_dir = output_dir.resolve()
    machine_attestation = machine_attestation.resolve()
    executable = executable.resolve()

    raw_manifest, rows = frozen_manifest()
    _require_external_output(output_dir, run_root, rows, "campaign evidence directory")
    _refuse_existing(output_dir)
    try:
        attestation = p181_batch.load_attested(machine_attestation, executable)
    except Exception as exc:
        raise CollectionError(f"Phase181 machine attestation failed: {exc}") from exc

    preflight = preflight_all(rows, run_root, attestation)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = output_dir.parent / f".{output_dir.name}.phase184-staging-{os.getpid()}"
    _require_external_output(stage, run_root, rows, "campaign evidence staging directory")
    if stage.exists():
        raise CollectionError(f"staging directory already exists: {stage}")
    stage.mkdir()

    manifest_path = stage / "phase172_manifest.csv"
    run_path = stage / "run_summary.csv"
    profile_path = stage / "profiles.csv"
    collision_path = stage / "collision_log_summary.csv"
    manifest_path.write_bytes(raw_manifest)

    run_fh = profile_fh = collision_fh = None
    details: List[Dict] = []
    total_profiles = 0
    total_collisions = 0
    try:
        run_fh, run_writer = _open_writer(run_path, RUN_COLUMNS)
        profile_fh, profile_writer = _open_writer(profile_path, p181_profile.PROFILE_COLUMNS)
        collision_fh, collision_writer = _open_writer(collision_path, p181_collision.OUTPUT_COLUMNS)

        for row in rows:
            run_id = str(row["run_id"])
            summary, profiles, collisions, detail = collect_one(row, preflight[run_id])
            run_writer.writerow(summary)
            profile_writer.writerows(profiles)
            collision_writer.writerows(collisions)
            total_profiles += len(profiles)
            total_collisions += len(collisions)
            details.append(detail)

        run_fh.close(); run_fh = None
        profile_fh.close(); profile_fh = None
        collision_fh.close(); collision_fh = None

        checks: List[Dict] = []
        manifest_ok, manifest_rows, _ = p172_time.validate_manifest(manifest_path, checks)
        contract_ok = bool(manifest_ok) and p172_time.validate_outputs(
            manifest_rows, run_path, profile_path, collision_path, checks
        )
        if not contract_ok:
            failed = [c for c in checks if not c.get("passed")]
            raise CollectionError(f"Phase172 output contract rejected assembled evidence: {failed[:5]}")

        report = {
            "phase": PHASE,
            "status": "PASS",
            "kind": "campaign_evidence_collection",
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "run_count": len(rows),
            "profile_rows": total_profiles,
            "collision_rows": total_collisions,
            "run_root": str(run_root),
            "machine_attestation": str(machine_attestation),
            "machine_attestation_sha256": sha256_file(machine_attestation),
            "executable": str(executable),
            "executable_sha256": sha256_file(executable),
            "outputs": {
                "run_summary.csv": {"sha256": sha256_file(run_path)},
                "profiles.csv": {"sha256": sha256_file(profile_path)},
                "collision_log_summary.csv": {"sha256": sha256_file(collision_path)},
            },
            "phase172_contract_checks": checks,
            "runs": details,
            "claim_boundary": (
                "PASS proves complete, provenance-locked campaign evidence assembly only. "
                "The Phase174 radial/convergence validator must still be run on these artifacts "
                "to obtain the frozen physics verdict."
            ),
        }
        report_path = stage / "phase184_collection_report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        manifest_path.unlink()
        os.replace(stage, output_dir)
        return report
    except Exception:
        for fh in (run_fh, profile_fh, collision_fh):
            if fh is not None:
                try:
                    fh.close()
                except Exception:
                    pass
        shutil.rmtree(stage, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--machine-attestation", required=True)
    ap.add_argument("--executable", required=True)
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        report = collect_campaign(
            Path(args.run_root), Path(args.output_dir), Path(args.machine_attestation), Path(args.executable)
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (
        CollectionError,
        p174.BatchError,
        p175.ResumeError,
        p181_batch.BatchError,
        p181_collision.EvidenceError,
        p181_profile.ProfileError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
