#!/usr/bin/env python3
"""Build the Phase187 scalar claim-evidence table from frozen campaign artifacts.

No production trajectory is changed.  This analysis consumes:
- the frozen Phase172 manifest;
- Phase184 run_summary.csv and profiles.csv;
- the immutable Phase175/181 run directories and their scheduled snapshots;
- a provenance-hashed global-energy evidence table produced by the separate
  Phase187 GIZMO energy probe.

Everything except global gravitational energy is derived directly here from the
frozen snapshots/profiles.  The metric definitions are fixed before campaign
results are opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase174_batch_submit as p174  # noqa: E402
import phase181_profile_extract as p181  # noqa: E402
import phase187_fatal_gate_validator as p187  # noqa: E402

PHASE = 187
EXPECTED_MANIFEST_SHA256 = p187.EXPECTED_MANIFEST_SHA256
CLAIM_TIME_GYR = 10.0
R_S_KPC = 9.1
RHO_S0 = 6.89e6
INNER_OVER_RS = 0.33
PROFILE_RMIN_OVER_RS = 0.03
PROFILE_RMAX_OVER_RS = 5.0
TIME_TOL = 1.0e-8

# Published/frozen 10-Gyr constant-SIDM2c target parameters retained from the
# Phase124/131 benchmark chain.
YANG = {
    "rho_s_over_rhos0": 0.033856404996,
    "rs_over_rs0": 2.80218707664,
    "rc_over_rs0": 0.175435349703,
    "beta_shape": 2.46273475939,
    "gamma_shape": 1.95371506117,
}

ENERGY_REQUIRED = (
    "run_id", "energy_drift_abs_max", "energy_probe_sha256", "energy_source_sha256"
)

OUTPUT_COLUMNS = list(p187.REQUIRED_COLUMNS)


class EvidenceError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open(newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def one_by(rows: Iterable[Dict[str, str]], **criteria: object) -> Dict[str, str]:
    hits = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in criteria.items())]
    if len(hits) != 1:
        raise EvidenceError(f"expected one row for {criteria}, found {len(hits)}")
    return hits[0]


def finite(value: object, label: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"invalid float {label}={value!r}") from exc
    if not math.isfinite(x):
        raise EvidenceError(f"non-finite float {label}={value!r}")
    return x


def frozen_manifest() -> Tuple[bytes, List[Dict[str, str]]]:
    raw, rows = p174.p173.frozen_manifest()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_MANIFEST_SHA256:
        raise EvidenceError(f"embedded Phase172 manifest SHA mismatch: {sha}")
    if len(rows) != 127:
        raise EvidenceError(f"expected 127 manifest rows, found {len(rows)}")
    return raw, rows


def yang_sidm2c_rho_over_rhos0(r_over_rs0: float) -> float:
    """Frozen Phase124/131 Yang-style 10-Gyr SIDM2c profile."""
    r = finite(r_over_rs0, "r_over_rs0")
    if r <= 0.0:
        raise EvidenceError("Yang profile radius must be positive")
    rho_s = YANG["rho_s_over_rhos0"]
    rs = YANG["rs_over_rs0"]
    rc = YANG["rc_over_rs0"]
    beta = YANG["beta_shape"]
    gamma = YANG["gamma_shape"]
    x = r / rs
    core = rc / rs
    return rho_s / (((x**4 + core**4) ** (gamma / 4.0)) *
                    ((1.0 + x**beta) ** ((3.0 - gamma) / beta)))


def _profile_rows_at(profiles: List[Dict[str, str]], run_id: str, time_gyr: float,
                     species: str) -> List[Dict[str, str]]:
    rows = []
    for r in profiles:
        if str(r.get("run_id")) != str(run_id):
            continue
        if str(r.get("species", "")).lower() != species.lower():
            continue
        if abs(finite(r.get("time_Gyr"), "time_Gyr") - time_gyr) > TIME_TOL:
            continue
        rmid = finite(r.get("r_mid_over_rs"), "r_mid_over_rs")
        if PROFILE_RMIN_OVER_RS <= rmid <= PROFILE_RMAX_OVER_RS:
            rows.append(r)
    rows.sort(key=lambda r: finite(r["r_mid_over_rs"], "r_mid_over_rs"))
    if not rows:
        raise EvidenceError(f"{run_id}: missing {species} profile at {time_gyr} Gyr")
    return rows


def cdm_profile_median_drift(profiles: List[Dict[str, str]], run_id: str) -> float:
    rows = _profile_rows_at(profiles, run_id, CLAIM_TIME_GYR, "total")
    vals = []
    for r in rows:
        rel = finite(r["rho_rel"], f"{run_id}:rho_rel")
        vals.append(abs(rel - 1.0))
    return float(np.median(np.asarray(vals, dtype=float)))


def sidm2c_profile_median_error(profiles: List[Dict[str, str]], run_id: str) -> float:
    rows = _profile_rows_at(profiles, run_id, CLAIM_TIME_GYR, "total")
    vals = []
    for r in rows:
        rr = finite(r["r_mid_over_rs"], f"{run_id}:r_mid_over_rs")
        observed = finite(r["rho"], f"{run_id}:rho") / RHO_S0
        target = yang_sidm2c_rho_over_rhos0(rr)
        if observed <= 0.0 or target <= 0.0:
            raise EvidenceError(f"{run_id}: non-positive SIDM2c observed/target density")
        vals.append(abs(observed / target - 1.0))
    return float(np.median(np.asarray(vals, dtype=float)))


def _r_fraction(snap: p181.Snapshot, ptype: int, fraction: float) -> float:
    x, _ = p181.centered(snap)
    mask = snap.ptype == ptype
    r = np.linalg.norm(x[mask], axis=1)
    m = snap.mass[mask]
    if len(r) == 0 or not (0.0 < fraction < 1.0):
        raise EvidenceError("invalid radius-fraction request")
    order = np.argsort(r, kind="mergesort")
    cs = np.cumsum(m[order])
    target = fraction * float(cs[-1])
    idx = int(np.searchsorted(cs, target, side="left"))
    return float(r[order[min(idx, len(order)-1)]])


def _particle_metrics(snap: p181.Snapshot) -> Dict[str, float]:
    x, _ = p181.centered(snap)
    r = np.linalg.norm(x, axis=1)
    h = snap.ptype == 1
    l = snap.ptype == 2
    if not np.any(h) or not np.any(l):
        raise EvidenceError("snapshot lacks H or L particles")

    # Historical Phase157/158 metric family used an eighth-power smooth inner
    # weight.  Production maps its scale to the already-frozen M11 inner region
    # r <= 0.33 r_s from the Phase134/135 chain.
    inner_kpc = INNER_OVER_RS * R_S_KPC
    w = 1.0 / (1.0 + (r / inner_kpc) ** 8)
    mh = float(np.median(snap.mass[h])); ml = float(np.median(snap.mass[l]))
    hin = float(np.sum(snap.mass[h] * w[h]))
    lin = float(np.sum(snap.mass[l] * w[l]))
    inner_ratio = (hin + 0.5 * mh) / max(lin + 0.5 * ml, 1.0e-300)

    # Shellwise Bhattacharyya-style H/L mass overlap, matching the historical
    # metric family but using the Phase181 48-bin M11 shell contract.
    edges = p181.EDGES_OVER_RS * R_S_KPC
    hh, _ = np.histogram(r[h], bins=edges, weights=snap.mass[h])
    ll, _ = np.histogram(r[l], bins=edges, weights=snap.mass[l])
    overlap = float(np.sum(np.sqrt(np.maximum(hh * ll, 0.0))))

    return {
        "inner_ratio": inner_ratio,
        "overlap": overlap,
        "r10_H": _r_fraction(snap, 1, 0.10),
        "r10_L": _r_fraction(snap, 2, 0.10),
    }


def scalar_particle_evidence(ic: Path, run_dir: Path) -> Dict[str, float]:
    mapped = p181.map_required_times(ic, run_dir)
    initial = mapped[0][2]
    hits = [s for t, _p, s in mapped if abs(float(t) - CLAIM_TIME_GYR) <= TIME_TOL]
    if len(hits) != 1:
        raise EvidenceError(f"{run_dir.name}: expected one 10-Gyr snapshot, found {len(hits)}")
    now = hits[0]
    base = _particle_metrics(initial)
    cur = _particle_metrics(now)
    if base["inner_ratio"] <= 0.0 or base["overlap"] <= 0.0 or cur["overlap"] <= 0.0:
        raise EvidenceError(f"{run_dir.name}: invalid positive baseline for S/O")
    s_inner = math.log(cur["inner_ratio"] / base["inner_ratio"])
    o_overlap = math.log(cur["overlap"] / base["overlap"])
    # Positive means H moved inward while L moved outward, the original Phase166
    # directional semantics.  Log ratios make the two directions dimensionless.
    direction = math.log(cur["r10_L"] / base["r10_L"]) - math.log(cur["r10_H"] / base["r10_H"])

    mt = float(initial.mass.sum())
    vcm0 = np.sum(initial.vel * initial.mass[:, None], axis=0) / mt
    max_dv = 0.0
    for _t, _p, snap in mapped:
        mts = float(snap.mass.sum())
        vcm = np.sum(snap.vel * snap.mass[:, None], axis=0) / mts
        max_dv = max(max_dv, float(np.linalg.norm(vcm - vcm0)))
    return {
        "S_inner_10Gyr": s_inner,
        "O_overlap_10Gyr": o_overlap,
        "H_in_L_out_score": direction,
        "momentum_drift_abs_max": max_dv,
    }


def load_energy(path: Path, manifest_ids: set[str]) -> Dict[str, Dict[str, str]]:
    fields, rows = read_csv(path)
    missing = [c for c in ENERGY_REQUIRED if c not in fields]
    if missing:
        raise EvidenceError(f"energy evidence missing columns: {missing}")
    out = {}
    for r in rows:
        rid = str(r["run_id"])
        if rid in out:
            raise EvidenceError(f"duplicate energy evidence for {rid}")
        if rid not in manifest_ids:
            raise EvidenceError(f"energy evidence contains unknown run_id {rid}")
        drift = finite(r["energy_drift_abs_max"], f"{rid}:energy_drift_abs_max")
        if drift < 0.0:
            raise EvidenceError(f"{rid}: negative energy drift")
        for k in ("energy_probe_sha256", "energy_source_sha256"):
            if len(str(r[k]).strip()) < 32:
                raise EvidenceError(f"{rid}: missing {k}")
        out[rid] = r
    if set(out) != manifest_ids:
        raise EvidenceError(f"energy evidence coverage mismatch: missing={sorted(manifest_ids-set(out))[:10]}")
    return out


def completion_ic(run_dir: Path, run_id: str) -> Path:
    post_path, post = p174.completion_record(run_dir)
    if post_path is None or post is None or post.get("status") != "COMPLETE":
        raise EvidenceError(f"{run_id}: missing COMPLETE production record")
    if str(post.get("run_id")) != run_id:
        raise EvidenceError(f"{run_id}: completion record run_id mismatch")
    ic = Path(str(post.get("ic", "")))
    if not ic.is_file():
        raise EvidenceError(f"{run_id}: completion IC missing: {ic}")
    expected = str(post.get("ic_sha256", ""))
    observed = sha256_file(ic)
    if not expected or observed != expected:
        raise EvidenceError(f"{run_id}: completion IC SHA mismatch")
    return ic


def build(manifest_path: Path, run_summary_path: Path, profiles_path: Path,
          run_root: Path, energy_evidence_path: Path, output_path: Path) -> Dict:
    raw, manifest = frozen_manifest()
    if sha256_file(manifest_path) != EXPECTED_MANIFEST_SHA256 or manifest_path.read_bytes() != raw:
        raise EvidenceError("materialized manifest is not the exact frozen Phase172 bytes")

    run_fields, run_rows = read_csv(run_summary_path)
    prof_fields, profiles = read_csv(profiles_path)
    manifest_ids = {str(r["run_id"]) for r in manifest}
    run_by_id = {str(r["run_id"]): r for r in run_rows}
    if set(run_by_id) != manifest_ids:
        raise EvidenceError("Phase184 run_summary coverage does not equal frozen manifest")
    required_prof = set(p181.PROFILE_COLUMNS)
    if not required_prof <= set(prof_fields):
        raise EvidenceError(f"profiles.csv missing Phase181 columns: {sorted(required_prof-set(prof_fields))}")
    energy = load_energy(energy_evidence_path, manifest_ids)

    analysis_sha = sha256_file(Path(__file__))
    source_hash = hashlib.sha256()
    source_hash.update(manifest_path.read_bytes())
    source_hash.update(run_summary_path.read_bytes())
    source_hash.update(profiles_path.read_bytes())
    source_hash.update(energy_evidence_path.read_bytes())
    source_evidence_sha = source_hash.hexdigest()

    rows_out: List[Dict[str, object]] = []
    for m in manifest:
        rid = str(m["run_id"])
        rs = run_by_id[rid]
        for col in ("branch", "group", "resolution_tier", "seed"):
            if str(rs.get(col)) != str(m.get(col)):
                raise EvidenceError(f"{rid}: run_summary metadata mismatch for {col}")
        if str(rs.get("status")) != "COMPLETE":
            raise EvidenceError(f"{rid}: run_summary is not COMPLETE")

        run_dir = run_root / rid
        ic = completion_ic(run_dir, rid)
        particle = scalar_particle_evidence(ic, run_dir)
        cdm_metric = ""
        c2_metric = ""
        c2_clock = ""
        if m["branch"] == "CDM":
            cdm_metric = f"{cdm_profile_median_drift(profiles, rid):.17g}"
        if m["branch"] == "SIDM2c_const":
            c2_metric = f"{sidm2c_profile_median_error(profiles, rid):.17g}"
            # The collapse-clock diagnostic remains explicitly non-fatal.  No
            # profile-only proxy is manufactured here; blank is preserved.
            c2_clock = ""

        rows_out.append({
            "run_id": rid,
            "branch": m["branch"],
            "group": m["group"],
            "resolution_tier": m["resolution_tier"],
            "seed": m["seed"],
            "status": "COMPLETE",
            "energy_drift_abs_max": f"{finite(energy[rid]['energy_drift_abs_max'], rid+':energy'):.17g}",
            "momentum_drift_abs_max": f"{particle['momentum_drift_abs_max']:.17g}",
            "cdm_profile_median_drift_10Gyr": cdm_metric,
            "sidm2c_profile_median_error_10Gyr": c2_metric,
            "sidm2c_collapse_clock_error_frac": c2_clock,
            "S_inner_10Gyr": f"{particle['S_inner_10Gyr']:.17g}",
            "O_overlap_10Gyr": f"{particle['O_overlap_10Gyr']:.17g}",
            "H_in_L_out_score": f"{particle['H_in_L_out_score']:.17g}",
            "analysis_sha256": analysis_sha,
            "source_evidence_sha256": source_evidence_sha,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise EvidenceError(f"refusing to overwrite scalar evidence: {output_path}")
    with output_path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        wr.writeheader(); wr.writerows(rows_out)

    # Evaluate immediately so the builder cannot emit a structurally malformed
    # table and call that success.
    ok, checks = p187.validate(manifest_path, output_path)
    report = {
        "phase": PHASE,
        "status": "PASS" if ok else "FAIL",
        "kind": "phase187_scalar_evidence",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "run_count": len(rows_out),
        "analysis_sha256": analysis_sha,
        "source_evidence_sha256": source_evidence_sha,
        "scalar_evidence_sha256": sha256_file(output_path),
        "metric_contract": {
            "S_inner": "log of smooth H/L inner-mass ratio relative to the same IC; w=1/(1+(r/(0.33*r_s))^8)",
            "O_overlap": "log shellwise H/L Bhattacharyya mass overlap relative to the same IC",
            "H_in_L_out_score": "log(r10_L/r10_L0)-log(r10_H/r10_H0)",
            "CDM_profile_drift": "median over 0.03<=r/r_s<=5 of abs(rho_total(10Gyr)/rho_total(0)-1)",
            "SIDM2c_profile_error": "median over 0.03<=r/r_s<=5 of abs(rho_total/Yang10Gyr-1)",
            "momentum_drift": "max scheduled-time norm of H+L COM velocity minus its IC value, in snapshot velocity units",
            "energy_drift": "supplied only by the provenance-hashed Phase187 GIZMO global-energy probe",
        },
        "validator_checks": checks,
        "claim_boundary": (
            "This builder derives preregistered scalar claim evidence without changing production trajectories. "
            "Its PASS is not a final physics PASS unless Phase174 and Phase187 fatal validators both pass."
        ),
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-summary", required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--run-root", required=True)
    ap.add_argument("--energy-evidence", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report-json")
    args = ap.parse_args()
    try:
        rep = build(Path(args.manifest), Path(args.run_summary), Path(args.profiles),
                    Path(args.run_root), Path(args.energy_evidence), Path(args.output))
        text = json.dumps(rep, indent=2, sort_keys=True)
        print(text)
        if args.report_json:
            Path(args.report_json).write_text(text + "\n")
        return 0 if rep["status"] == "PASS" else 1
    except (EvidenceError, p181.ProfileError, p187.FatalGateError, OSError, ValueError) as exc:
        print(json.dumps({"phase": PHASE, "status": "ERROR", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
