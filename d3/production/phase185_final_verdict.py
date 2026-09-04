#!/usr/bin/env python3
"""Phase185 atomic campaign-verdict packager for the frozen D3 campaign.

Phase185 assembles the already-frozen Phase184 evidence and evaluates the
already-frozen Phase174 radial/collision gates.  Phase186 now guards the claim
boundary: this packager must not be promoted as a *final physics* verdict until
every preregistered fatal Phase165 gate has an implemented evaluator.

A valid physics FAIL remains a scientific result.  Incomplete/corrupt evidence,
or an incomplete preregistered claim-gate implementation, fails closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import phase174_radial_convergence_validator as p174  # noqa: E402
import phase184_campaign_evidence as p184  # noqa: E402
import phase186_claim_completeness as p186  # noqa: E402

PHASE = 185
EXPECTED_TOTAL = p184.EXPECTED_TOTAL
EXPECTED_MANIFEST_SHA256 = p184.EXPECTED_MANIFEST_SHA256


class VerdictError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def _refuse_existing(final_dir: Path) -> None:
    if final_dir.exists():
        raise VerdictError(f"refusing to overwrite existing final verdict directory: {final_dir}")


def physics_result(ok: bool, checks: List[Dict]) -> Dict:
    return {
        "phase": 174,
        "status": "PASS" if ok else "FAIL",
        "scope": "registered_radial_convergence_and_collision_gates_only",
        "claim_epoch_Gyr": float(p174.CLAIM_TIME_GYR),
        "radial_range_over_rs": [float(p174.RADIUS_MIN_OVER_RS), float(p174.RADIUS_MAX_OVER_RS)],
        "thresholds": {
            "sidm2v_resolution_profile_delta_max": p174.SIDM2V_RESOLUTION_MAX,
            "timestep_profile_delta_max": p174.TIMESTEP_MAX,
            "neighbor_profile_delta_max": p174.NEIGHBOR_MAX,
            "max_pair_dP_over_P": p174.PAIR_RESIDUAL_MAX,
            "max_pair_dK_over_K": p174.PAIR_RESIDUAL_MAX,
            "prob_clip_fraction_max": p174.PROB_CLIP_MAX,
        },
        "checks": checks,
    }


def finalize_campaign(
    run_root: Path,
    final_dir: Path,
    machine_attestation: Path,
    executable: Path,
) -> Dict:
    # This is deliberately before touching the destination or reading campaign
    # outputs.  Phase186 is a pre-data claim-contract check, not a data-dependent
    # physics gate.  Today it blocks because seven preregistered fatal evaluators
    # are still absent from the production verdict path.
    claim_completeness = p186.assert_final_claim_ready()

    _refuse_existing(final_dir)
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = final_dir.parent / f".{final_dir.name}.phase185-staging-{os.getpid()}"
    if stage.exists():
        raise VerdictError(f"staging directory already exists: {stage}")
    stage.mkdir()

    try:
        evidence_dir = stage / "evidence"
        evidence_report = p184.collect_campaign(
            run_root, evidence_dir, machine_attestation, executable
        )
        if evidence_report.get("status") != "PASS":
            raise VerdictError("Phase184 evidence collector did not return PASS")
        if int(evidence_report.get("run_count", -1)) != EXPECTED_TOTAL:
            raise VerdictError(
                f"Phase184 evidence run count mismatch: {evidence_report.get('run_count')}"
            )
        if evidence_report.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
            raise VerdictError("Phase184 evidence manifest SHA mismatch")

        raw_manifest, manifest_rows = p184.frozen_manifest()
        if len(manifest_rows) != EXPECTED_TOTAL:
            raise VerdictError("embedded manifest cardinality changed during finalization")
        manifest_path = stage / "phase172_manifest.csv"
        manifest_path.write_bytes(raw_manifest)

        run_summary = evidence_dir / "run_summary.csv"
        profiles = evidence_dir / "profiles.csv"
        collisions = evidence_dir / "collision_log_summary.csv"
        ok, checks = p174.validate(manifest_path, run_summary, profiles, collisions)
        verdict = physics_result(bool(ok), checks)
        verdict_path = stage / "phase174_physics_verdict.json"
        verdict_path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")

        package_files = {
            "phase172_manifest.csv": manifest_path,
            "evidence/run_summary.csv": run_summary,
            "evidence/profiles.csv": profiles,
            "evidence/collision_log_summary.csv": collisions,
            "evidence/phase184_collection_report.json": evidence_dir / "phase184_collection_report.json",
            "phase174_physics_verdict.json": verdict_path,
        }
        missing = [name for name, path in package_files.items() if not path.is_file()]
        if missing:
            raise VerdictError(f"final verdict package missing files: {missing}")

        report = {
            "phase": PHASE,
            "status": verdict["status"],
            "kind": "atomic_campaign_verdict",
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "run_count": EXPECTED_TOTAL,
            "run_root": str(run_root.resolve()),
            "machine_attestation": str(machine_attestation.resolve()),
            "machine_attestation_sha256": sha256_file(machine_attestation),
            "executable": str(executable.resolve()),
            "executable_sha256": sha256_file(executable),
            "phase184_status": evidence_report["status"],
            "phase174_status": verdict["status"],
            "phase186_claim_completeness": claim_completeness,
            "files": {
                name: {"sha256": sha256_file(path)} for name, path in package_files.items()
            },
            "claim_boundary": (
                "PASS means the completed 127-run/80-Gyr campaign satisfied the frozen "
                "Phase172 evidence contract and Phase174 convergence/collision gates, and "
                "Phase186 verified that every preregistered fatal Phase165 claim gate has "
                "an implemented evaluator. It does not by itself establish dark-matter "
                "discovery, observational uniqueness, or external reproduction."
            ),
        }
        report_path = stage / "phase185_final_verdict.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        report["files"]["phase185_final_verdict.json"] = {
            "sha256": sha256_file(report_path)
        }

        # Rewrite once so the report contains the hash of every other immutable artifact.
        # It intentionally cannot self-hash its own final bytes without recursion.
        report["files"]["phase185_final_verdict.json"] = {
            "sha256": None,
            "note": "self-hash intentionally omitted to avoid recursive content",
        }
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        stage.replace(final_dir)
        return report
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--final-dir", required=True)
    ap.add_argument("--machine-attestation", required=True)
    ap.add_argument("--executable", required=True)
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        report = finalize_campaign(
            Path(args.run_root),
            Path(args.final_dir),
            Path(args.machine_attestation),
            Path(args.executable),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    except (
        VerdictError,
        p186.ClaimCompletenessError,
        p184.CollectionError,
        p174.ValidationError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "ERROR", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
