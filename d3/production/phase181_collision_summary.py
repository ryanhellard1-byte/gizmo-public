#!/usr/bin/env python3
"""Phase181 fail-closed live-GIZMO collision evidence extractor.

The Phase172 output contract requires collision_log_summary.csv coverage for every
manifest run.  This tool converts the live SIDMx-D3 AUDIT stream into that frozen
schema without inventing unmeasured quantities.

Rules:
- DM_InteractionCrossSection == 0: collisionless control; no audit is required and
  one zero-valued NONE row is emitted.
- positive cross section: the ordinary upstream SIDM path must emit audit mode 10.
- negative D3 sentinel -1..-9: audit mode abs(sentinel) is required.
- HH/LL/HL collision counts are exact accepted-event sums.
- clipping fraction is the maximum, over synchronized integer times, of
  sum_task(p>0.2 evaluations) / sum_task(pair evaluations) for each channel.
- pair-conservation residuals are the maxima reported by the live engine.
- mean_sigma_factor and mean_mu remain blank because the current live telemetry
  does not define those observables.  Blank is preferable to fabricated physics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
CHANNELS = ("HH", "LL", "HL")
REQUIRED_AUDIT_KEYS = {
    "task", "ti", "mode",
    "max_momentum_residual", "max_energy_residual",
}
OUTPUT_COLUMNS = [
    "run_id", "channel", "collision_count", "mean_sigma_factor", "mean_mu",
    "max_pair_dP_over_P", "max_pair_dK_over_K", "prob_clip_fraction_max",
    "audit_mode", "pair_evaluations", "expected_sum_probability",
    "expected_sum_probability_squared", "pge1_count", "max_pair_probability",
    "audit_rows", "source_log_sha256",
]


class EvidenceError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_scalar(text: str):
    try:
        if any(c in text for c in ".eE"):
            return float(text)
        return int(text)
    except ValueError:
        return text


def load_manifest(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    observed = sha256_file(path)
    if observed != EXPECTED_MANIFEST_SHA256:
        raise EvidenceError(
            f"frozen Phase172 manifest SHA mismatch: {observed} != {EXPECTED_MANIFEST_SHA256}"
        )
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def find_manifest_row(rows: Iterable[Dict[str, str]], run_id: str) -> Dict[str, str]:
    hits = [r for r in rows if str(r.get("run_id")) == str(run_id)]
    if len(hits) != 1:
        raise EvidenceError(f"expected exactly one manifest row for {run_id}, found {len(hits)}")
    return hits[0]


def expected_audit_mode(row: Dict[str, str]) -> int:
    try:
        x = float(row["runtime_interaction_parameter"])
    except Exception as exc:
        raise EvidenceError("manifest runtime_interaction_parameter is missing/invalid") from exc
    if not math.isfinite(x):
        raise EvidenceError("manifest runtime_interaction_parameter is non-finite")
    if x == 0.0:
        return 0
    if x > 0.0:
        return 10
    mode = int(round(-x))
    if mode < 1 or mode > 9 or abs(x + mode) > 1.0e-10:
        raise EvidenceError(f"invalid frozen D3 sentinel {x}")
    return mode


def parse_audit_rows(log_path: Path) -> List[Dict]:
    rows: List[Dict] = []
    for line_no, line in enumerate(log_path.read_text(errors="replace").splitlines(), 1):
        marker = line.find("SIDMx-D3 AUDIT ")
        if marker < 0:
            continue
        payload = line[marker + len("SIDMx-D3 AUDIT "):]
        row = {k: parse_scalar(v) for k, v in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", payload)}
        missing = sorted(REQUIRED_AUDIT_KEYS - set(row))
        if missing:
            raise EvidenceError(f"audit line {line_no} missing keys {missing}")
        row["_line"] = line_no
        rows.append(row)
    return rows


def nonnegative_int(value, label: str) -> int:
    try:
        f = float(value)
    except Exception as exc:
        raise EvidenceError(f"invalid {label}={value!r}") from exc
    if not math.isfinite(f) or f < 0 or not f.is_integer():
        raise EvidenceError(f"{label} must be a nonnegative integer, got {value!r}")
    return int(f)


def finite_nonnegative(value, label: str) -> float:
    try:
        f = float(value)
    except Exception as exc:
        raise EvidenceError(f"invalid {label}={value!r}") from exc
    if not math.isfinite(f) or f < 0:
        raise EvidenceError(f"{label} must be finite and nonnegative, got {value!r}")
    return f


def collisionless_row(run_id: str, log_sha: str) -> Dict[str, object]:
    return {
        "run_id": run_id, "channel": "NONE", "collision_count": 0,
        "mean_sigma_factor": "", "mean_mu": "",
        "max_pair_dP_over_P": 0.0, "max_pair_dK_over_K": 0.0,
        "prob_clip_fraction_max": 0.0, "audit_mode": 0,
        "pair_evaluations": 0, "expected_sum_probability": 0.0,
        "expected_sum_probability_squared": 0.0, "pge1_count": 0,
        "max_pair_probability": 0.0, "audit_rows": 0,
        "source_log_sha256": log_sha,
    }


def summarize(row: Dict[str, str], log_path: Path) -> Tuple[List[Dict[str, object]], Dict]:
    run_id = str(row["run_id"])
    mode = expected_audit_mode(row)
    audit = parse_audit_rows(log_path)
    log_sha = sha256_file(log_path)

    if mode == 0:
        if audit:
            raise EvidenceError(f"{run_id}: collisionless control unexpectedly contains live audit rows")
        out = [collisionless_row(run_id, log_sha)]
        return out, {"run_id": run_id, "audit_mode": 0, "audit_rows": 0, "status": "PASS"}

    if not audit:
        raise EvidenceError(f"{run_id}: runtime requires audit mode {mode}, but no live audit rows were found")
    bad_modes = sorted({int(r["mode"]) for r in audit if int(r["mode"]) != mode})
    if bad_modes:
        raise EvidenceError(f"{run_id}: audit contains unexpected modes {bad_modes}; required {mode}")

    totals = {ch: defaultdict(float) for ch in CHANNELS}
    by_time = {ch: defaultdict(lambda: [0, 0]) for ch in CHANNELS}
    max_momentum = 0.0
    max_energy = 0.0

    for r in audit:
        ti = nonnegative_int(r["ti"], "ti")
        max_momentum = max(max_momentum, finite_nonnegative(r["max_momentum_residual"], "max_momentum_residual"))
        max_energy = max(max_energy, finite_nonnegative(r["max_energy_residual"], "max_energy_residual"))
        for ch in CHANNELS:
            pairs = nonnegative_int(r.get(f"pairs_{ch}", 0), f"pairs_{ch}")
            events = nonnegative_int(r.get(f"events_{ch}", 0), f"events_{ch}")
            pgt02 = nonnegative_int(r.get(f"pgt02_{ch}", 0), f"pgt02_{ch}")
            pge1 = nonnegative_int(r.get(f"pge1_{ch}", 0), f"pge1_{ch}")
            expected = finite_nonnegative(r.get(f"expected_{ch}", 0.0), f"expected_{ch}")
            expected2 = finite_nonnegative(r.get(f"expected2_{ch}", 0.0), f"expected2_{ch}")
            maxprob = finite_nonnegative(r.get(f"maxprob_{ch}", 0.0), f"maxprob_{ch}")
            if pgt02 > pairs or pge1 > pairs or events > pairs:
                raise EvidenceError(f"{run_id}: impossible {ch} audit counts at ti={ti}")
            if expected2 > expected * (1.0 + 1.0e-12):
                raise EvidenceError(f"{run_id}: sum(p^2) exceeds sum(p) for {ch} at ti={ti}")
            t = totals[ch]
            t["pairs"] += pairs
            t["events"] += events
            t["pgt02"] += pgt02
            t["pge1"] += pge1
            t["expected"] += expected
            t["expected2"] += expected2
            t["maxprob"] = max(t["maxprob"], maxprob)
            by_time[ch][ti][0] += pgt02
            by_time[ch][ti][1] += pairs

    if any(totals[ch]["pge1"] > 0 for ch in CHANNELS):
        bad = {ch: int(totals[ch]["pge1"]) for ch in CHANNELS if totals[ch]["pge1"] > 0}
        raise EvidenceError(f"{run_id}: p>=1 probability evaluations occurred: {bad}")

    out: List[Dict[str, object]] = []
    for ch in CHANNELS:
        t = totals[ch]
        fractions = [bad / pairs for bad, pairs in by_time[ch].values() if pairs > 0]
        clip_max = max(fractions, default=0.0)
        out.append({
            "run_id": run_id,
            "channel": ch,
            "collision_count": int(t["events"]),
            "mean_sigma_factor": "",
            "mean_mu": "",
            "max_pair_dP_over_P": max_momentum,
            "max_pair_dK_over_K": max_energy,
            "prob_clip_fraction_max": clip_max,
            "audit_mode": mode,
            "pair_evaluations": int(t["pairs"]),
            "expected_sum_probability": t["expected"],
            "expected_sum_probability_squared": t["expected2"],
            "pge1_count": int(t["pge1"]),
            "max_pair_probability": t["maxprob"],
            "audit_rows": len(audit),
            "source_log_sha256": log_sha,
        })

    report = {
        "status": "PASS",
        "run_id": run_id,
        "audit_mode": mode,
        "audit_rows": len(audit),
        "source_log_sha256": log_sha,
        "max_pair_dP_over_P": max_momentum,
        "max_pair_dK_over_K": max_energy,
        "channels": {
            r["channel"]: {
                "collision_count": r["collision_count"],
                "pair_evaluations": r["pair_evaluations"],
                "expected_sum_probability": r["expected_sum_probability"],
                "prob_clip_fraction_max": r["prob_clip_fraction_max"],
                "max_pair_probability": r["max_pair_probability"],
            }
            for r in out
        },
        "unmeasured_frozen_columns": ["mean_sigma_factor", "mean_mu"],
    }
    return out, report


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report-json")
    args = ap.parse_args()
    try:
        _, manifest = load_manifest(Path(args.manifest))
        row = find_manifest_row(manifest, args.run_id)
        rows, report = summarize(row, Path(args.log))
        write_csv(Path(args.output), rows)
        if args.report_json:
            Path(args.report_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (EvidenceError, OSError, ValueError) as exc:
        print(json.dumps({"phase": 181, "status": "FAIL", "error": str(exc)}, indent=2), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
