#!/usr/bin/env python3
"""Phase182 deterministic assembly of the complete 127-run evidence ledger.

This command is intentionally unavailable as a partial blind-analysis shortcut: it
requires finalized evidence for all 127 frozen runs before it emits campaign-level
run_summary.csv, profiles.csv, collision_log_summary.csv, or evaluates the already-
frozen Phase174 radial gates.
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
from typing import Dict, Iterable, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase172_time_contract as time_contract  # noqa: E402
import phase174_radial_convergence_validator as radial  # noqa: E402
import phase182_finalize_run as finalizer  # noqa: E402

PHASE = 182
CAMPAIGN_LEDGER = "phase182_CAMPAIGN_LEDGER.json"
RUN_SUMMARY = "run_summary.csv"
PROFILES = "profiles.csv"
COLLISIONS = "collision_log_summary.csv"
MANIFEST = "phase172_manifest.csv"
RADIAL_RESULT = "phase174_radial_result.json"


class AssembleError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def concatenate_csv(paths: Iterable[Path], destination: Path) -> int:
    fields = None
    total = 0
    with destination.open("w", newline="") as out:
        writer = None
        for path in paths:
            with path.open(newline="") as fh:
                reader = csv.DictReader(fh)
                current = list(reader.fieldnames or [])
                if not current:
                    raise AssembleError(f"CSV has no header: {path}")
                if fields is None:
                    fields = current
                    writer = csv.DictWriter(out, fieldnames=fields)
                    writer.writeheader()
                elif current != fields:
                    raise AssembleError(f"CSV schema drift in {path}: {current} != {fields}")
                assert writer is not None
                for row in reader:
                    writer.writerow(row)
                    total += 1
    if fields is None:
        raise AssembleError("no CSV inputs supplied")
    return total


def assemble(
    run_root: Path,
    evidence_root: Path,
    output_dir: Path,
    executable: Path,
    attestation: Path,
) -> Dict:
    run_root = run_root.resolve()
    evidence_root = evidence_root.resolve()
    output_dir = output_dir.resolve()
    executable = executable.resolve()
    attestation = attestation.resolve()
    if output_dir.exists():
        raise AssembleError(f"refusing to overwrite campaign output directory: {output_dir}")

    raw, rows = finalizer.frozen_campaign()
    if len(rows) != 127:
        raise AssembleError(f"campaign must contain exactly 127 rows, found {len(rows)}")

    finalized = []
    for row in rows:
        rid = row["run_id"]
        evidence_dir = evidence_root / rid
        record = finalizer.verify_finalized(
            evidence_dir, run_root, rid, executable, attestation
        )
        finalized.append({
            "run_id": rid,
            "evidence_dir": str(evidence_dir),
            "finalization_record_sha256": sha256_file(evidence_dir / finalizer.FINAL_RECORD),
            "raw_run_directory_sha256": record["raw_run_directory_sha256"],
            "artifacts": record["artifacts"],
        })

    tmp = output_dir.parent / f".{output_dir.name}.phase182.tmp.{os.getpid()}"
    if tmp.exists():
        raise AssembleError(f"refusing to reuse campaign temp directory: {tmp}")
    tmp.mkdir(parents=True)
    try:
        manifest_path = tmp / MANIFEST
        manifest_path.write_bytes(raw)
        run_summary_path = tmp / RUN_SUMMARY
        profiles_path = tmp / PROFILES
        collision_path = tmp / COLLISIONS

        run_rows = concatenate_csv(
            (evidence_root / r["run_id"] / finalizer.RUN_SUMMARY for r in rows),
            run_summary_path,
        )
        profile_rows = concatenate_csv(
            (evidence_root / r["run_id"] / finalizer.PROFILES for r in rows),
            profiles_path,
        )
        collision_rows = concatenate_csv(
            (evidence_root / r["run_id"] / finalizer.COLLISIONS for r in rows),
            collision_path,
        )
        if run_rows != 127:
            raise AssembleError(f"aggregate run_summary row count {run_rows} != 127")

        tc_checks: List[Dict] = []
        tc_ok, manifest_rows, manifest_sha = time_contract.validate_manifest(manifest_path, tc_checks)
        if tc_ok:
            tc_ok = time_contract.validate_outputs(
                manifest_rows, run_summary_path, profiles_path, collision_path, tc_checks
            )
        if not tc_ok:
            raise AssembleError(
                "assembled campaign violates Phase172 time/output contract: "
                + json.dumps([c for c in tc_checks if not c.get("passed")], sort_keys=True)
            )

        radial_ok, radial_checks = radial.validate(
            manifest_path, run_summary_path, profiles_path, collision_path
        )
        radial_result = {
            "phase": 174,
            "status": "PASS" if radial_ok else "FAIL",
            "claim_epoch_Gyr": float(radial.CLAIM_TIME_GYR),
            "radial_range_over_rs": [float(radial.RADIUS_MIN_OVER_RS), float(radial.RADIUS_MAX_OVER_RS)],
            "thresholds": {
                "sidm2v_resolution_profile_delta_max": radial.SIDM2V_RESOLUTION_MAX,
                "timestep_profile_delta_max": radial.TIMESTEP_MAX,
                "neighbor_profile_delta_max": radial.NEIGHBOR_MAX,
                "max_pair_dP_over_P": radial.PAIR_RESIDUAL_MAX,
                "max_pair_dK_over_K": radial.PAIR_RESIDUAL_MAX,
                "prob_clip_fraction_max": radial.PROB_CLIP_MAX,
            },
            "checks": radial_checks,
        }
        (tmp / RADIAL_RESULT).write_text(json.dumps(radial_result, indent=2, sort_keys=True) + "\n")

        artifacts = {
            name: sha256_file(tmp / name)
            for name in (MANIFEST, RUN_SUMMARY, PROFILES, COLLISIONS, RADIAL_RESULT)
        }
        ledger = {
            "phase": PHASE,
            "status": "PASS",
            "kind": "complete_127_run_evidence_ledger",
            "manifest_sha256": manifest_sha,
            "runs_required": 127,
            "runs_finalized": len(finalized),
            "run_summary_rows": run_rows,
            "profile_rows": profile_rows,
            "collision_rows": collision_rows,
            "phase172_time_output_contract": "PASS",
            "phase174_radial_validator_status": radial_result["status"],
            "note": "A Phase174 FAIL is a recorded scientific gate result, not an evidence-assembly failure.",
            "machine_attestation_sha256": sha256_file(attestation),
            "evidence_executable_sha256": sha256_file(executable),
            "artifacts": artifacts,
            "finalized_runs": finalized,
            "phase172_checks": tc_checks,
        }
        (tmp / CAMPAIGN_LEDGER).write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, output_dir)
        return {**ledger, "output_dir": str(output_dir)}
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", required=True)
    p.add_argument("--evidence-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--executable", required=True)
    p.add_argument("--machine-attestation", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        result = assemble(
            Path(args.run_root),
            Path(args.evidence_root),
            Path(args.output_dir),
            Path(args.executable),
            Path(args.machine_attestation),
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        AssembleError,
        finalizer.FinalizeError,
        finalizer.machine.EvidenceGateError,
        finalizer.p175.ResumeError,
        radial.ValidationError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
