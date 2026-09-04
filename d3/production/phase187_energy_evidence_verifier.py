#!/usr/bin/env python3
"""Phase187 fail-closed binding for global-energy campaign evidence.

The energy CSV is not trusted on shape alone. This verifier binds it to:
- the exact Phase172 127-run manifest,
- a canonical-source Phase187 probe-build attestation,
- the actual probe executable bytes,
- the full Phase187 energy campaign report,
- and the current completion record, params, IC, and scheduled snapshot bytes
  for every production run.

This is provenance/evidence validation only. It does not alter trajectories.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import phase174_batch_submit as p174  # noqa: E402
import phase181_profile_extract as p181  # noqa: E402
import phase187_energy_probe as p187e  # noqa: E402

PHASE = 187
EXPECTED_TOTAL = 127
EXPECTED_MANIFEST_SHA256 = p187e.EXPECTED_MANIFEST_SHA256
ENERGY_REQUIRED = tuple(p187e.ENERGY_COLUMNS)


class EnergyEvidenceError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path, label: str) -> Dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise EnergyEvidenceError(f"invalid {label}: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EnergyEvidenceError(f"{label} must be a JSON object")
    return data


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def finite(value: object, label: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise EnergyEvidenceError(f"invalid float {label}={value!r}") from exc
    if not math.isfinite(x):
        raise EnergyEvidenceError(f"non-finite float {label}={value!r}")
    return x


def frozen_manifest_ids() -> List[str]:
    raw, rows = p174.p173.frozen_manifest()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_MANIFEST_SHA256:
        raise EnergyEvidenceError(f"frozen manifest SHA changed: {observed}")
    if len(rows) != EXPECTED_TOTAL:
        raise EnergyEvidenceError(f"expected {EXPECTED_TOTAL} manifest rows, found {len(rows)}")
    ids = [str(r["run_id"]) for r in rows]
    if len(set(ids)) != EXPECTED_TOTAL:
        raise EnergyEvidenceError("frozen manifest contains duplicate run_id")
    return ids


def current_campaign_source(run_root: Path, run_id: str) -> Dict:
    run_dir = run_root / run_id
    post_path, post = p187e.completion_record(run_dir, run_id)
    params = run_dir / "params.txt"
    if not params.is_file():
        raise EnergyEvidenceError(f"{run_id}: production params.txt missing")

    ic = Path(str(post.get("ic", "")))
    if not ic.is_file():
        raise EnergyEvidenceError(f"{run_id}: completion IC missing: {ic}")
    ic_sha = sha256_file(ic)
    if ic_sha != str(post.get("ic_sha256", "")):
        raise EnergyEvidenceError(f"{run_id}: completion IC SHA mismatch")

    try:
        mapped = p181.map_required_times(ic, run_dir)
    except p181.ProfileError as exc:
        raise EnergyEvidenceError(f"{run_id}: scheduled snapshot map failed: {exc}") from exc

    source_hash = hashlib.sha256(post_path.read_bytes() + params.read_bytes())
    snapshots = []
    for expected_time, path, _snap in mapped:
        path = path.resolve()
        observed = sha256_file(path)
        source_hash.update(path.as_posix().encode() + b"\0")
        source_hash.update(bytes.fromhex(observed))
        snapshots.append({
            "expected_time_Gyr": float(expected_time),
            "snapshot": str(path),
            "snapshot_sha256": observed,
        })

    return {
        "run_id": run_id,
        "energy_source_sha256": source_hash.hexdigest(),
        "completion_record_sha256": sha256_file(post_path),
        "params_sha256": sha256_file(params),
        "ic_sha256": ic_sha,
        "snapshots": snapshots,
    }


def _keyed(rows: List[Dict], label: str) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for row in rows:
        rid = str(row.get("run_id", ""))
        if not rid:
            raise EnergyEvidenceError(f"{label}: blank run_id")
        if rid in out:
            raise EnergyEvidenceError(f"{label}: duplicate run_id {rid}")
        out[rid] = row
    return out


def _same_float(a: object, b: object, label: str) -> bool:
    x = finite(a, label + ":a")
    y = finite(b, label + ":b")
    return math.isclose(x, y, rel_tol=1.0e-12, abs_tol=1.0e-15)


def verify(
    run_root: Path,
    energy_csv: Path,
    energy_report_json: Path,
    probe_attestation_json: Path,
    probe_executable: Path,
) -> Dict:
    for path, label in (
        (energy_csv, "energy CSV"),
        (energy_report_json, "energy report"),
        (probe_attestation_json, "probe attestation"),
        (probe_executable, "probe executable"),
    ):
        if not path.is_file():
            raise EnergyEvidenceError(f"missing {label}: {path}")

    manifest_ids = frozen_manifest_ids()
    manifest_set = set(manifest_ids)
    probe_sha = sha256_file(probe_executable)

    att = load_json(probe_attestation_json, "probe attestation")
    if att.get("phase") != PHASE or att.get("status") != "PASS":
        raise EnergyEvidenceError("probe attestation phase/status mismatch")
    if att.get("kind") != "analysis_only_gizmo_energy_probe_build":
        raise EnergyEvidenceError("probe attestation kind mismatch")
    if att.get("canonical_source_required") is not True:
        raise EnergyEvidenceError("production energy evidence requires canonical-source probe attestation")
    if att.get("source_commit") != p187e.CANONICAL_PHYSICS_SOURCE_COMMIT:
        raise EnergyEvidenceError("probe attestation source commit is not canonical physics source")
    if att.get("canonical_physics_source_commit") != p187e.CANONICAL_PHYSICS_SOURCE_COMMIT:
        raise EnergyEvidenceError("probe attestation canonical source field mismatch")
    if att.get("probe_executable_sha256") != probe_sha:
        raise EnergyEvidenceError("probe executable SHA does not match attestation")
    if att.get("builder_sha256") != sha256_file(Path(p187e.__file__)):
        raise EnergyEvidenceError("probe builder SHA does not match current Phase187 energy-probe code")
    if att.get("patch_contract_sha256") != sha256_bytes(p187e.RUN_PATCH.encode()):
        raise EnergyEvidenceError("probe patch contract SHA mismatch")
    if att.get("probe_config_sha256") != sha256_bytes(p187e.PROBE_CONFIG.encode()):
        raise EnergyEvidenceError("probe config SHA mismatch")
    iso = att.get("physics_isolation")
    expected_iso = {
        "DM_SIDM_enabled": False,
        "COMPUTE_POTENTIAL_ENERGY_enabled": True,
        "explicit_global_state_population": True,
        "returns_before_find_timesteps": True,
        "production_executable_modified": False,
    }
    if not isinstance(iso, dict) or any(iso.get(k) != v for k, v in expected_iso.items()):
        raise EnergyEvidenceError("probe physics-isolation attestation mismatch")

    report = load_json(energy_report_json, "energy campaign report")
    if report.get("phase") != PHASE or report.get("status") != "PASS":
        raise EnergyEvidenceError("energy report phase/status mismatch")
    if report.get("kind") != "gizmo_global_energy_evidence":
        raise EnergyEvidenceError("energy report kind mismatch")
    if report.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise EnergyEvidenceError("energy report manifest SHA mismatch")
    if int(report.get("run_count", -1)) != EXPECTED_TOTAL:
        raise EnergyEvidenceError("energy report run count mismatch")
    csv_sha = sha256_file(energy_csv)
    if report.get("energy_evidence_sha256") != csv_sha:
        raise EnergyEvidenceError("energy CSV SHA does not match campaign report")
    if report.get("probe_executable_sha256") != probe_sha:
        raise EnergyEvidenceError("energy report probe executable SHA mismatch")

    fields, csv_rows = read_csv(energy_csv)
    missing = [c for c in ENERGY_REQUIRED if c not in fields]
    if missing:
        raise EnergyEvidenceError(f"energy CSV missing columns: {missing}")
    csv_by_id = _keyed(csv_rows, "energy CSV")
    if set(csv_by_id) != manifest_set:
        raise EnergyEvidenceError(
            f"energy CSV run coverage mismatch: missing={sorted(manifest_set-set(csv_by_id))[:10]} "
            f"extra={sorted(set(csv_by_id)-manifest_set)[:10]}"
        )

    report_runs = report.get("runs")
    if not isinstance(report_runs, list):
        raise EnergyEvidenceError("energy report missing runs list")
    report_by_id = _keyed(report_runs, "energy report")
    if set(report_by_id) != manifest_set:
        raise EnergyEvidenceError("energy report run coverage does not equal frozen manifest")

    verified_runs = []
    for rid in manifest_ids:
        csv_row = csv_by_id[rid]
        rr = report_by_id[rid]
        if rr.get("status") != "PASS":
            raise EnergyEvidenceError(f"{rid}: energy report run status is not PASS")

        if str(csv_row["energy_probe_sha256"]) != probe_sha or rr.get("energy_probe_sha256") != probe_sha:
            raise EnergyEvidenceError(f"{rid}: probe executable SHA mismatch in energy evidence")

        current = current_campaign_source(run_root, rid)
        expected_source = current["energy_source_sha256"]
        if str(csv_row["energy_source_sha256"]) != expected_source:
            raise EnergyEvidenceError(f"{rid}: CSV energy source SHA does not match current campaign artifacts")
        if rr.get("energy_source_sha256") != expected_source:
            raise EnergyEvidenceError(f"{rid}: report energy source SHA does not match current campaign artifacts")

        csv_drift = finite(csv_row["energy_drift_abs_max"], f"{rid}:CSV drift")
        report_drift = finite(rr.get("energy_drift_abs_max"), f"{rid}:report drift")
        if csv_drift < 0.0 or not _same_float(csv_drift, report_drift, f"{rid}:drift"):
            raise EnergyEvidenceError(f"{rid}: CSV/report energy drift mismatch")

        samples = rr.get("samples")
        if not isinstance(samples, list) or len(samples) != len(current["snapshots"]):
            raise EnergyEvidenceError(f"{rid}: energy sample count mismatch")
        etots = []
        for i, (sample, actual) in enumerate(zip(samples, current["snapshots"])):
            if not isinstance(sample, dict):
                raise EnergyEvidenceError(f"{rid}: sample {i} is not an object")
            if sample.get("probe_executable_sha256") != probe_sha:
                raise EnergyEvidenceError(f"{rid}: sample {i} probe SHA mismatch")
            if sample.get("snapshot_sha256") != actual["snapshot_sha256"]:
                raise EnergyEvidenceError(f"{rid}: sample {i} snapshot SHA mismatch")
            if not _same_float(sample.get("expected_time_Gyr"), actual["expected_time_Gyr"], f"{rid}:sample time"):
                raise EnergyEvidenceError(f"{rid}: sample {i} scheduled time mismatch")
            if sample.get("original_params_sha256") != current["params_sha256"]:
                raise EnergyEvidenceError(f"{rid}: sample {i} production params SHA mismatch")
            etot = finite(sample.get("Etot"), f"{rid}:sample {i}:Etot")
            finite(sample.get("Ekin"), f"{rid}:sample {i}:Ekin")
            finite(sample.get("Epot"), f"{rid}:sample {i}:Epot")
            finite(sample.get("Eint"), f"{rid}:sample {i}:Eint")
            etots.append(etot)

        if not etots or etots[0] == 0.0:
            raise EnergyEvidenceError(f"{rid}: invalid initial total energy")
        derived_drifts = [abs(x / etots[0] - 1.0) for x in etots]
        derived_max = max(derived_drifts)
        if not _same_float(derived_max, report_drift, f"{rid}:derived drift"):
            raise EnergyEvidenceError(f"{rid}: reported drift does not match report sample energies")

        report_drifts = rr.get("drifts")
        if not isinstance(report_drifts, list) or len(report_drifts) != len(derived_drifts):
            raise EnergyEvidenceError(f"{rid}: report drift-vector length mismatch")
        for i, (got, exp) in enumerate(zip(report_drifts, derived_drifts)):
            if not _same_float(got, exp, f"{rid}:drift[{i}]"):
                raise EnergyEvidenceError(f"{rid}: report drift-vector mismatch at sample {i}")

        verified_runs.append({
            "run_id": rid,
            "energy_drift_abs_max": report_drift,
            "energy_source_sha256": expected_source,
        })

    return {
        "phase": PHASE,
        "status": "PASS",
        "kind": "phase187_energy_evidence_binding",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "run_count": EXPECTED_TOTAL,
        "probe_executable_sha256": probe_sha,
        "probe_attestation_sha256": sha256_file(probe_attestation_json),
        "energy_report_sha256": sha256_file(energy_report_json),
        "energy_evidence_sha256": csv_sha,
        "verified_source_hashes": True,
        "verified_sample_snapshot_hashes": True,
        "verified_sample_energy_arithmetic": True,
        "runs": verified_runs,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--energy-csv", required=True)
    ap.add_argument("--energy-report", required=True)
    ap.add_argument("--probe-attestation", required=True)
    ap.add_argument("--probe-executable", required=True)
    ap.add_argument("--out-json")
    args = ap.parse_args()
    try:
        result = verify(
            Path(args.run_root),
            Path(args.energy_csv),
            Path(args.energy_report),
            Path(args.probe_attestation),
            Path(args.probe_executable),
        )
        text = json.dumps(result, indent=2, sort_keys=True)
        print(text)
        if args.out_json:
            out = Path(args.out_json)
            if out.exists():
                raise EnergyEvidenceError(f"refusing to overwrite verifier report: {out}")
            out.write_text(text + "\n")
        return 0
    except (EnergyEvidenceError, OSError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "ERROR", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())