#!/usr/bin/env python3
"""Phase179 fail-closed extractor from live GIZMO outputs to frozen evidence CSVs.

The analysis definitions in this file are frozen before any 80-Gyr production
outputs exist.  It produces the structural evidence consumed by Phase172 and
Phase174.  It does not decide the final blinded physical claim by itself.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import struct
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase172_render_run as render  # noqa: E402
import phase175_safe_resume as p175  # noqa: E402

R_S_KPC = 9.1
TIME_UNIT_GYR = render.TIME_UNIT_GYR
TIMES_GYR = render.EXPECTED_ANALYSIS_TIMES_GYR
TIME_TOL_GYR = 1.0e-6
N_BINS = 24
R_EDGES_OVER_RS = np.geomspace(0.02, 10.0, N_BINS + 1)
INNER_OVER_RS = 0.33
CONVERGENCE_LO = 0.03
CONVERGENCE_HI = 3.0
CHANNELS = ("HH", "LL", "HL")
AUDIT_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")

PROFILE_FIELDS = (
    "run_id", "time_Gyr", "r_mid_over_rs", "r_lo_over_rs", "r_hi_over_rs",
    "species", "rho", "rho_initial", "rho_rel", "sigma2", "beta", "mass_enclosed",
)
COLLISION_FIELDS = (
    "run_id", "channel", "collision_count", "mean_sigma_factor", "mean_mu",
    "max_pair_dP_over_P", "max_pair_dK_over_K", "prob_clip_fraction_max",
    "audit_mode", "evaluated_pairs", "expected_sum_probability",
    "expected_sum_probability_squared", "p_gt_0p2_count", "p_ge_1_count", "max_probability",
)
RUN_FIELDS = (
    "run_id", "branch", "group", "resolution_tier", "seed", "status",
    "executable_sha256", "analysis_sha256", "output_sha256", "final_time_Gyr",
    "energy_drift_abs_max", "momentum_drift_abs_max", "max_pair_dP_over_P",
    "max_pair_dK_over_K", "prob_clip_fraction_max", "particle_loss_untracked",
    "cdm_profile_median_drift_10Gyr", "sidm2c_profile_median_error_10Gyr",
    "sidm2c_collapse_clock_error_frac", "S_inner_10Gyr", "O_overlap_10Gyr",
    "H_in_L_out_score", "notes",
)


class EvidenceError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_fortran_records(path: Path) -> list[bytes]:
    data = path.read_bytes()
    records: list[bytes] = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise EvidenceError(f"truncated record prefix: {path}")
        n = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if n > len(data) - pos - 4:
            raise EvidenceError(f"impossible record length {n}: {path}")
        payload = data[pos:pos + n]
        pos += n
        m = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if m != n:
            raise EvidenceError(f"record marker mismatch {n}!={m}: {path}")
        records.append(payload)
    return records


def _float_record(payload: bytes, n: int, width: int, label: str) -> np.ndarray:
    if len(payload) == n * width * 4:
        return np.frombuffer(payload, dtype="<f4").astype(np.float64).reshape(n, width)
    if len(payload) == n * width * 8:
        return np.frombuffer(payload, dtype="<f8").astype(np.float64).reshape(n, width)
    raise EvidenceError(f"{label} record has {len(payload)} bytes for N={n}")


def read_snapshot(path: Path) -> dict:
    rec = read_fortran_records(path)
    if len(rec) < 4 or len(rec[0]) != 256:
        raise EvidenceError(f"not a supported Gadget format-1 snapshot: {path}")
    hdr = rec[0]
    counts = np.array(struct.unpack_from("<6I", hdr, 0), dtype=np.int64)
    mass_table = np.array(struct.unpack_from("<6d", hdr, 24), dtype=np.float64)
    time_code = float(struct.unpack_from("<d", hdr, 72)[0])
    n = int(counts.sum())
    if n <= 0:
        raise EvidenceError(f"empty snapshot: {path}")
    pos = _float_record(rec[1], n, 3, "positions")
    vel = _float_record(rec[2], n, 3, "velocities")

    if len(rec[3]) == 4 * n:
        ids = np.frombuffer(rec[3], dtype="<u4").astype(np.uint64)
    elif len(rec[3]) == 8 * n:
        ids = np.frombuffer(rec[3], dtype="<u8").astype(np.uint64)
    else:
        raise EvidenceError(f"ID record has {len(rec[3])} bytes for N={n}")
    if len(np.unique(ids)) != n:
        raise EvidenceError(f"duplicate particle IDs in {path}")

    ptype = np.repeat(np.arange(6, dtype=np.int8), counts)
    need_mass = [t for t in range(6) if counts[t] and mass_table[t] == 0.0]
    n_variable = int(sum(counts[t] for t in need_mass))
    mass = np.empty(n, dtype=np.float64)
    cursor = 0
    var = None
    if n_variable:
        if len(rec) < 5:
            raise EvidenceError(f"missing variable-mass record: {path}")
        payload = rec[4]
        if len(payload) == 4 * n_variable:
            var = np.frombuffer(payload, dtype="<f4").astype(np.float64)
        elif len(payload) == 8 * n_variable:
            var = np.frombuffer(payload, dtype="<f8").astype(np.float64)
        else:
            raise EvidenceError(f"mass record has {len(payload)} bytes, expected {4*n_variable} or {8*n_variable}")
    offset = 0
    for t in range(6):
        nt = int(counts[t])
        if not nt:
            continue
        sl = slice(offset, offset + nt)
        if mass_table[t] != 0.0:
            mass[sl] = mass_table[t]
        else:
            assert var is not None
            mass[sl] = var[cursor:cursor + nt]
            cursor += nt
        offset += nt
    if np.any(~np.isfinite(pos)) or np.any(~np.isfinite(vel)) or np.any(~np.isfinite(mass)) or np.any(mass <= 0):
        raise EvidenceError(f"non-finite/non-positive particle data: {path}")
    return {
        "path": path,
        "time_code": time_code,
        "time_Gyr": time_code * TIME_UNIT_GYR,
        "counts": counts,
        "pos": pos,
        "vel": vel,
        "ids": ids,
        "ptype": ptype,
        "mass": mass,
    }


def canonical_particles(snap: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(snap["ids"], kind="stable")
    return snap["ids"][order], snap["ptype"][order], snap["mass"][order]


def validate_particle_identity(base: dict, snap: dict) -> None:
    b_id, b_type, b_mass = canonical_particles(base)
    s_id, s_type, s_mass = canonical_particles(snap)
    if not np.array_equal(b_id, s_id):
        raise EvidenceError(f"particle ID set changed by t={snap['time_Gyr']:.9g} Gyr")
    if not np.array_equal(b_type, s_type):
        raise EvidenceError(f"particle species mapping changed by t={snap['time_Gyr']:.9g} Gyr")
    if not np.array_equal(b_mass, s_mass):
        raise EvidenceError(f"particle masses changed by t={snap['time_Gyr']:.9g} Gyr")


def weighted_mean(x: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(w * x) / np.sum(w))


def profile_components(pos: np.ndarray, vel: np.ndarray, mass: np.ndarray) -> dict[str, np.ndarray]:
    mt = float(mass.sum())
    center = np.sum(pos * mass[:, None], axis=0) / mt
    bulk = np.sum(vel * mass[:, None], axis=0) / mt
    x = pos - center
    v = vel - bulk
    r = np.linalg.norm(x, axis=1)
    rr = np.maximum(r, 1.0e-300)
    er = x / rr[:, None]
    phi = np.arctan2(x[:, 1], x[:, 0])
    rho_xy = np.hypot(x[:, 0], x[:, 1])
    costh = x[:, 2] / rr
    sinth = rho_xy / rr
    ephi = np.column_stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)))
    etheta = np.column_stack((costh * np.cos(phi), costh * np.sin(phi), -sinth))
    # At r=0 the angular basis is arbitrary; it contributes only to the first
    # shell and remains finite.  Use fixed Cartesian axes there.
    zero = r <= 1.0e-300
    if np.any(zero):
        er[zero] = np.array([1.0, 0.0, 0.0])
        etheta[zero] = np.array([0.0, 0.0, -1.0])
        ephi[zero] = np.array([0.0, 1.0, 0.0])
    vr = np.sum(v * er, axis=1)
    vt = np.sum(v * etheta, axis=1)
    vp = np.sum(v * ephi, axis=1)
    return {"center": center, "bulk": bulk, "r": r, "vr": vr, "vt": vt, "vp": vp}


def shell_profiles(snap: dict, run_id: str, time_Gyr: float, initial_rho: dict[str, np.ndarray] | None = None):
    comp = profile_components(snap["pos"], snap["vel"], snap["mass"])
    r_over = comp["r"] / R_S_KPC
    rows = []
    rho_by_species: dict[str, np.ndarray] = {}
    shell_mass_by_species: dict[str, np.ndarray] = {}
    vol = 4.0 * math.pi / 3.0 * ((R_EDGES_OVER_RS[1:] * R_S_KPC) ** 3 - (R_EDGES_OVER_RS[:-1] * R_S_KPC) ** 3)
    mids = np.sqrt(R_EDGES_OVER_RS[:-1] * R_EDGES_OVER_RS[1:])

    masks = {
        "H": snap["ptype"] == 1,
        "L": snap["ptype"] == 2,
        "total": np.isin(snap["ptype"], (1, 2)),
    }
    if not np.any(masks["H"]) or not np.any(masks["L"]):
        raise EvidenceError("snapshot is missing H or L particles")

    for species, smask in masks.items():
        rr = r_over[smask]
        mm = snap["mass"][smask]
        vr = comp["vr"][smask]
        vt = comp["vt"][smask]
        vp = comp["vp"][smask]
        shell_mass, _ = np.histogram(rr, bins=R_EDGES_OVER_RS, weights=mm)
        rho = shell_mass / vol
        rho_by_species[species] = rho
        shell_mass_by_species[species] = shell_mass
        enclosed = np.array([float(mm[rr <= edge].sum()) for edge in R_EDGES_OVER_RS[1:]])

        for b in range(N_BINS):
            take = (rr >= R_EDGES_OVER_RS[b]) & (rr < R_EDGES_OVER_RS[b + 1])
            if b == N_BINS - 1:
                take |= rr == R_EDGES_OVER_RS[b + 1]
            if np.any(take):
                w = mm[take]
                def variance(q):
                    mu = weighted_mean(q[take], w)
                    return weighted_mean((q[take] - mu) ** 2, w)
                sr2, st2, sp2 = variance(vr), variance(vt), variance(vp)
                sigma2 = (sr2 + st2 + sp2) / 3.0
                beta = 1.0 - (st2 + sp2) / (2.0 * sr2) if sr2 > 0.0 else float("nan")
            else:
                sigma2 = float("nan")
                beta = float("nan")
            initial = rho[b] if initial_rho is None else initial_rho[species][b]
            if initial <= 0.0:
                # Claim windows must never acquire an undefined ratio. Outer
                # empty bins are still rejected because a fixed common profile
                # grid is part of the preregistered evidence contract.
                raise EvidenceError(f"zero initial density: species={species} bin={b}")
            rows.append({
                "run_id": run_id,
                "time_Gyr": time_Gyr,
                "r_mid_over_rs": mids[b],
                "r_lo_over_rs": R_EDGES_OVER_RS[b],
                "r_hi_over_rs": R_EDGES_OVER_RS[b + 1],
                "species": species,
                "rho": rho[b],
                "rho_initial": initial,
                "rho_rel": rho[b] / initial,
                "sigma2": sigma2,
                "beta": beta,
                "mass_enclosed": enclosed[b],
            })
    return rows, rho_by_species, shell_mass_by_species, comp


def historical_metrics(base: dict, at10: dict, base_rho: dict[str, np.ndarray], rho10: dict[str, np.ndarray]) -> dict:
    def inner_ratio(snap: dict) -> float:
        comp = profile_components(snap["pos"], snap["vel"], snap["mass"])
        q = comp["r"] / R_S_KPC <= INNER_OVER_RS
        h = float(snap["mass"][q & (snap["ptype"] == 1)].sum())
        l = float(snap["mass"][q & (snap["ptype"] == 2)].sum())
        mh = float(np.median(snap["mass"][snap["ptype"] == 1]))
        ml = float(np.median(snap["mass"][snap["ptype"] == 2]))
        return (h + 0.5 * mh) / max(l + 0.5 * ml, 1.0e-300)

    vol = 4.0 * math.pi / 3.0 * ((R_EDGES_OVER_RS[1:] * R_S_KPC) ** 3 - (R_EDGES_OVER_RS[:-1] * R_S_KPC) ** 3)
    ov0 = float(np.sum(np.sqrt(np.maximum(base_rho["H"] * base_rho["L"], 0.0)) * vol))
    ov1 = float(np.sum(np.sqrt(np.maximum(rho10["H"] * rho10["L"], 0.0)) * vol))
    ratio0, ratio1 = inner_ratio(base), inner_ratio(at10)

    def r50(snap: dict, species_type: int) -> float:
        comp = profile_components(snap["pos"], snap["vel"], snap["mass"])
        mask = snap["ptype"] == species_type
        rr = comp["r"][mask]
        mm = snap["mass"][mask]
        order = np.argsort(rr)
        rr, mm = rr[order], mm[order]
        target = 0.5 * float(mm.sum())
        idx = int(np.searchsorted(np.cumsum(mm), target, side="left"))
        return float(rr[min(idx, len(rr) - 1)])

    h0, h1 = r50(base, 1), r50(at10, 1)
    l0, l1 = r50(base, 2), r50(at10, 2)
    h_in = math.log(max(h0, 1e-300) / max(h1, 1e-300))
    l_out = math.log(max(l1, 1e-300) / max(l0, 1e-300))
    return {
        "S_inner_10Gyr": math.log(max(ratio1, 1e-300) / max(ratio0, 1e-300)),
        "O_overlap_10Gyr": math.log(max(ov1, 1e-300) / max(ov0, 1e-300)),
        # Positive if and only if both H contracts and L expands.
        "H_in_L_out_score": min(h_in, l_out),
        "inner_ratio_0": ratio0,
        "inner_ratio_10": ratio1,
        "overlap_0": ov0,
        "overlap_10": ov1,
        "r50_H_0_kpc": h0,
        "r50_H_10_kpc": h1,
        "r50_L_0_kpc": l0,
        "r50_L_10_kpc": l1,
    }


def parse_value(text: str):
    try:
        return float(text) if any(c in text for c in ".eE") else int(text)
    except ValueError:
        return text


def expected_audit_mode(runtime_parameter: float) -> int:
    if runtime_parameter < 0.0:
        mode = int(round(-runtime_parameter))
        if mode < 1 or mode > 9 or abs(runtime_parameter + mode) > 1e-10:
            raise EvidenceError(f"invalid negative runtime interaction parameter {runtime_parameter}")
        return mode
    if runtime_parameter > 0.0:
        return 10
    return 0


def collision_summary(run_id: str, log: Path, runtime_parameter: float) -> tuple[list[dict], dict]:
    mode = expected_audit_mode(runtime_parameter)
    parsed = []
    if log.is_file():
        for line in log.read_text(errors="replace").splitlines():
            if not line.startswith("SIDMx-D3 AUDIT "):
                continue
            parsed.append({k: parse_value(v) for k, v in AUDIT_RE.findall(line)})

    if mode in set(range(1, 9)) | {10} and not parsed:
        raise EvidenceError(f"{run_id}: active mode {mode} has no live audit rows")
    if mode in (0, 9) and parsed and any(int(r.get("mode", -1)) != mode for r in parsed):
        raise EvidenceError(f"{run_id}: unexpected audit rows for null mode {mode}")
    if parsed and any(int(r.get("mode", -1)) != mode for r in parsed):
        got = sorted({int(r.get("mode", -1)) for r in parsed})
        raise EvidenceError(f"{run_id}: audit mode mismatch expected={mode} got={got}")

    seen = set()
    blocks = defaultdict(list)
    for r in parsed:
        key = (int(r.get("task", -1)), int(r.get("ti", -1)), int(r.get("mode", -1)))
        if key in seen:
            raise EvidenceError(f"{run_id}: duplicate audit task/time/mode block {key}")
        seen.add(key)
        blocks[(key[1], key[2])].append(r)

    totals = {ch: {"pairs": 0, "expected": 0.0, "expected2": 0.0, "events": 0,
                   "pgt02": 0, "pge1": 0, "maxprob": 0.0, "clipmax": 0.0}
              for ch in CHANNELS}
    max_dp = 0.0
    max_dk = 0.0
    for _, rows in sorted(blocks.items()):
        max_dp = max(max_dp, *(float(r.get("max_momentum_residual", 0.0)) for r in rows))
        max_dk = max(max_dk, *(float(r.get("max_energy_residual", 0.0)) for r in rows))
        for ch in CHANNELS:
            pairs = sum(int(r.get(f"pairs_{ch}", 0)) for r in rows)
            pgt = sum(int(r.get(f"pgt02_{ch}", 0)) for r in rows)
            totals[ch]["pairs"] += pairs
            totals[ch]["expected"] += sum(float(r.get(f"expected_{ch}", 0.0)) for r in rows)
            totals[ch]["expected2"] += sum(float(r.get(f"expected2_{ch}", 0.0)) for r in rows)
            totals[ch]["events"] += sum(int(r.get(f"events_{ch}", 0)) for r in rows)
            totals[ch]["pgt02"] += pgt
            totals[ch]["pge1"] += sum(int(r.get(f"pge1_{ch}", 0)) for r in rows)
            totals[ch]["maxprob"] = max(totals[ch]["maxprob"], *(float(r.get(f"maxprob_{ch}", 0.0)) for r in rows))
            if pairs:
                totals[ch]["clipmax"] = max(totals[ch]["clipmax"], pgt / pairs)

    if any(totals[ch]["pge1"] for ch in CHANNELS):
        raise EvidenceError(f"{run_id}: p>=1 probability evaluations occurred")

    out = []
    for ch in CHANNELS:
        d = totals[ch]
        out.append({
            "run_id": run_id,
            "channel": ch,
            "collision_count": d["events"],
            # The live engine does not emit historical mean_sigma_factor/mean_mu.
            # Preserve the frozen columns explicitly without manufacturing data.
            "mean_sigma_factor": "",
            "mean_mu": "",
            "max_pair_dP_over_P": max_dp,
            "max_pair_dK_over_K": max_dk,
            "prob_clip_fraction_max": d["clipmax"],
            "audit_mode": mode,
            "evaluated_pairs": d["pairs"],
            "expected_sum_probability": d["expected"],
            "expected_sum_probability_squared": d["expected2"],
            "p_gt_0p2_count": d["pgt02"],
            "p_ge_1_count": d["pge1"],
            "max_probability": d["maxprob"],
        })
    return out, {"mode": mode, "blocks": len(blocks), "max_pair_dP_over_P": max_dp,
                 "max_pair_dK_over_K": max_dk,
                 "prob_clip_fraction_max": max((totals[ch]["clipmax"] for ch in CHANNELS), default=0.0)}


def load_manifest_row(path: Path, run_id: str) -> dict[str, str]:
    with path.open(newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("run_id") == run_id]
    if len(rows) != 1:
        raise EvidenceError(f"manifest has {len(rows)} rows for {run_id}")
    row = rows[0]
    render.parse_frozen_times(row["analysis_times_Gyr"])
    return row


def collect_snapshots(run_dir: Path, row: dict[str, str]) -> dict[float, dict]:
    meta_path = run_dir / "render_metadata.json"
    if not meta_path.is_file():
        raise EvidenceError(f"missing render metadata: {meta_path}")
    meta = json.loads(meta_path.read_text())
    ic = Path(meta["ic"])
    if not ic.is_file():
        raise EvidenceError(f"missing IC: {ic}")
    base = read_snapshot(ic)
    if abs(base["time_Gyr"]) > TIME_TOL_GYR:
        raise EvidenceError(f"IC time is not zero: {base['time_Gyr']}")
    expected_n = int(row["N_total"])
    if len(base["ids"]) != expected_n:
        raise EvidenceError(f"IC particle count {len(base['ids'])} != manifest {expected_n}")

    found: dict[float, dict] = {0.0: base}
    unmatched = []
    for path in sorted(p for p in run_dir.glob("snapshot*") if p.is_file()):
        snap = read_snapshot(path)
        validate_particle_identity(base, snap)
        matches = [t for t in TIMES_GYR[1:] if abs(snap["time_Gyr"] - t) <= TIME_TOL_GYR]
        if len(matches) != 1:
            unmatched.append({"path": str(path), "time_Gyr": snap["time_Gyr"]})
            continue
        t = matches[0]
        if t in found:
            raise EvidenceError(f"duplicate snapshot for {t} Gyr")
        found[t] = snap
    if unmatched:
        raise EvidenceError(f"snapshots outside frozen schedule: {unmatched[:5]}")
    missing = [t for t in TIMES_GYR if t not in found]
    if missing:
        raise EvidenceError(f"missing frozen snapshot times: {missing}")
    return found


def verify_completion(run_dir: Path, row: dict[str, str]) -> tuple[dict, dict]:
    state_path = run_dir / p175.STATE_NAME
    if not state_path.is_file():
        raise EvidenceError(f"missing Phase175 completion state: {state_path}")
    state = json.loads(state_path.read_text())
    if state.get("status") != "COMPLETE":
        raise EvidenceError(f"run is not COMPLETE: {state.get('status')}")
    if state.get("run_id") != row["run_id"] or state.get("manifest_row") != row:
        raise EvidenceError("completion state does not match manifest row")
    try:
        integrity = p175.verify_completion_integrity(run_dir, state, state_path.name)
    except p175.ResumeError as exc:
        raise EvidenceError(f"completed-output integrity failed: {exc}") from exc
    return state, integrity


def csv_write(path: Path, fields, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def extract_one(manifest: Path, run_id: str, run_root: Path, out_dir: Path) -> dict:
    row = load_manifest_row(manifest, run_id)
    run_dir = run_root / run_id
    state, integrity = verify_completion(run_dir, row)
    snaps = collect_snapshots(run_dir, row)

    profile_rows: list[dict] = []
    profiles = {}
    first_rows, initial_rho, _, _ = shell_profiles(snaps[0.0], run_id, 0.0, None)
    profile_rows.extend(first_rows)
    profiles[0.0] = initial_rho
    for t in TIMES_GYR[1:]:
        rows_t, rho_t, _, _ = shell_profiles(snaps[t], run_id, t, initial_rho)
        profile_rows.extend(rows_t)
        profiles[t] = rho_t

    metrics = historical_metrics(snaps[0.0], snaps[10.0], profiles[0.0], profiles[10.0])
    collisions, collision_meta = collision_summary(run_id, run_dir / "gizmo.log",
                                                     float(row["runtime_interaction_parameter"]))

    mids = np.sqrt(R_EDGES_OVER_RS[:-1] * R_EDGES_OVER_RS[1:])
    claim = (mids >= CONVERGENCE_LO) & (mids <= CONVERGENCE_HI)
    cdm_drift = ""
    if row["branch"] == "CDM":
        rel = np.abs(profiles[10.0]["total"][claim] / profiles[0.0]["total"][claim] - 1.0)
        cdm_drift = float(np.median(rel))

    analysis_sha = sha256_file(Path(__file__))
    max_dp = collision_meta["max_pair_dP_over_P"]
    max_dk = collision_meta["max_pair_dK_over_K"]
    clip = collision_meta["prob_clip_fraction_max"]
    run_summary = {
        "run_id": run_id,
        "branch": row["branch"],
        "group": row["group"],
        "resolution_tier": row["resolution_tier"],
        "seed": row["seed"],
        "status": "COMPLETE",
        "executable_sha256": state.get("executable_sha256", ""),
        "analysis_sha256": analysis_sha,
        "output_sha256": integrity.get("run_directory_sha256", state.get("run_directory_sha256", "")),
        "final_time_Gyr": 80.0,
        "energy_drift_abs_max": "",
        "momentum_drift_abs_max": "",
        "max_pair_dP_over_P": max_dp,
        "max_pair_dK_over_K": max_dk,
        "prob_clip_fraction_max": clip,
        "particle_loss_untracked": 0,
        "cdm_profile_median_drift_10Gyr": cdm_drift,
        "sidm2c_profile_median_error_10Gyr": "",
        "sidm2c_collapse_clock_error_frac": "",
        "S_inner_10Gyr": metrics["S_inner_10Gyr"],
        "O_overlap_10Gyr": metrics["O_overlap_10Gyr"],
        "H_in_L_out_score": metrics["H_in_L_out_score"],
        "notes": "Phase179 structural extraction; energy and SIDM2c reference metrics require their separately frozen derivations",
    }

    dest = out_dir / run_id
    dest.mkdir(parents=True, exist_ok=False)
    csv_write(dest / "profiles.csv", PROFILE_FIELDS, profile_rows)
    csv_write(dest / "collision_log_summary.csv", COLLISION_FIELDS, collisions)
    csv_write(dest / "run_summary.csv", RUN_FIELDS, [run_summary])
    evidence = {
        "phase": 179,
        "status": "PASS",
        "run_id": run_id,
        "analysis_sha256": analysis_sha,
        "profile_definition": {
            "center": "total H+L mass-weighted center of mass independently at each epoch",
            "bulk_velocity": "total H+L mass-weighted velocity independently at each epoch",
            "r_s_kpc": R_S_KPC,
            "radial_edges_over_rs": R_EDGES_OVER_RS.tolist(),
            "sigma2": "mass-weighted (var(v_r)+var(v_theta)+var(v_phi))/3 in each shell",
            "beta": "1-(var(v_theta)+var(v_phi))/(2 var(v_r))",
            "mass_enclosed": "species mass at r <= shell upper edge",
        },
        "metric_definition": {
            "inner_radius_over_rs": INNER_OVER_RS,
            "S": "ln[(M_H(<0.33rs)+0.5mH)/(M_L(<0.33rs)+0.5mL)] relative to t=0",
            "overlap": "sum_bins sqrt(rho_H rho_L) shell_volume on fixed Phase179 grid",
            "O": "ln(overlap_10Gyr/overlap_0)",
            "H_in_L_out_score": "min[ln(r50_H(0)/r50_H(10)), ln(r50_L(10)/r50_L(0))]",
        },
        "historical_unavailable_columns": {
            "mean_sigma_factor": "not emitted by live engine; intentionally blank",
            "mean_mu": "not emitted by live engine; intentionally blank",
        },
        "collision_meta": collision_meta,
        "metrics_10Gyr": metrics,
        "files": {
            "profiles.csv": sha256_file(dest / "profiles.csv"),
            "collision_log_summary.csv": sha256_file(dest / "collision_log_summary.csv"),
            "run_summary.csv": sha256_file(dest / "run_summary.csv"),
        },
    }
    (dest / "phase179_evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return evidence


def combine(manifest: Path, fragments: Path, out_dir: Path) -> dict:
    with manifest.open(newline="") as fh:
        man_rows = list(csv.DictReader(fh))
    run_ids = [r["run_id"] for r in man_rows]
    all_profiles, all_collisions, all_runs = [], [], []
    for rid in run_ids:
        root = fragments / rid
        for name in ("profiles.csv", "collision_log_summary.csv", "run_summary.csv", "phase179_evidence.json"):
            if not (root / name).is_file():
                raise EvidenceError(f"missing fragment {rid}/{name}")
        with (root / "profiles.csv").open(newline="") as fh:
            all_profiles.extend(csv.DictReader(fh))
        with (root / "collision_log_summary.csv").open(newline="") as fh:
            all_collisions.extend(csv.DictReader(fh))
        with (root / "run_summary.csv").open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) != 1 or rows[0].get("run_id") != rid:
            raise EvidenceError(f"bad run-summary fragment for {rid}")
        all_runs.extend(rows)
    if len(all_runs) != len(run_ids) or {r["run_id"] for r in all_runs} != set(run_ids):
        raise EvidenceError("combined run IDs do not exactly match manifest")
    out_dir.mkdir(parents=True, exist_ok=False)
    csv_write(out_dir / "profiles.csv", PROFILE_FIELDS, all_profiles)
    csv_write(out_dir / "collision_log_summary.csv", COLLISION_FIELDS, all_collisions)
    csv_write(out_dir / "run_summary.csv", RUN_FIELDS, all_runs)
    result = {
        "phase": 179,
        "status": "PASS",
        "runs": len(all_runs),
        "profile_rows": len(all_profiles),
        "collision_rows": len(all_collisions),
        "analysis_sha256": sha256_file(Path(__file__)),
        "files": {name: sha256_file(out_dir / name) for name in
                  ("profiles.csv", "collision_log_summary.csv", "run_summary.csv")},
    }
    (out_dir / "phase179_combined_evidence.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def write_toy_snapshot(path: Path, pos, vel, ids, ptype, mass, time_code: float) -> None:
    order = np.argsort(ptype, kind="stable")
    pos = np.asarray(pos[order], dtype="<f4")
    vel = np.asarray(vel[order], dtype="<f4")
    ids = np.asarray(ids[order], dtype="<u4")
    ptype = np.asarray(ptype[order], dtype=np.int8)
    mass = np.asarray(mass[order], dtype="<f4")
    counts = np.array([(ptype == i).sum() for i in range(6)], dtype=np.uint32)
    header = bytearray(256)
    struct.pack_into("<6I", header, 0, *counts.tolist())
    struct.pack_into("<6d", header, 24, *([0.0] * 6))
    struct.pack_into("<d", header, 72, time_code)
    def record(fh, payload):
        fh.write(struct.pack("<I", len(payload))); fh.write(payload); fh.write(struct.pack("<I", len(payload)))
    with path.open("wb") as fh:
        record(fh, bytes(header)); record(fh, pos.tobytes()); record(fh, vel.tobytes()); record(fh, ids.tobytes()); record(fh, mass.tobytes())


def self_test() -> dict:
    rng = np.random.default_rng(179999)
    with tempfile.TemporaryDirectory(prefix="phase179-selftest-") as td:
        root = Path(td)
        n = 4000
        ptype = np.r_[np.ones(n // 2, dtype=np.int8), np.full(n // 2, 2, dtype=np.int8)]
        ids = np.arange(1, n + 1, dtype=np.uint32)
        mass = np.where(ptype == 1, 3.0, 1.0)
        # Log-uniform radii guarantee occupancy of every fixed radial shell.
        lr = rng.uniform(math.log(0.021 * R_S_KPC), math.log(9.9 * R_S_KPC), n)
        r = np.exp(lr)
        u = rng.normal(size=(n, 3)); u /= np.linalg.norm(u, axis=1)[:, None]
        pos = r[:, None] * u
        vel = rng.normal(0.0, 50.0, size=(n, 3))
        base_path = root / "base.dat"
        write_toy_snapshot(base_path, pos, vel, ids, ptype, mass, 0.0)
        base = read_snapshot(base_path)
        rows0, rho0, _, _ = shell_profiles(base, "TOY", 0.0)
        if len(rows0) != N_BINS * 3:
            raise EvidenceError("self-test profile cardinality")

        pos2 = pos.copy(); pos2[ptype == 1] *= 0.98; pos2[ptype == 2] *= 1.02
        s10_path = root / "s10.dat"
        write_toy_snapshot(s10_path, pos2, vel, ids, ptype, mass, 10.0 / TIME_UNIT_GYR)
        s10 = read_snapshot(s10_path); validate_particle_identity(base, s10)
        _, rho10, _, _ = shell_profiles(s10, "TOY", 10.0, rho0)
        met = historical_metrics(base, s10, rho0, rho10)
        if not met["H_in_L_out_score"] > 0.0:
            raise EvidenceError("self-test directional score did not detect H-in/L-out")

        log = root / "gizmo.log"
        log.write_text(
            "SIDMx-D3 AUDIT task=0 ti=1 mode=10 pairs_HH=100 pairs_LL=100 pairs_HL=200 "
            "expected_HH=1 expected_LL=1 expected_HL=2 expected2_HH=.01 expected2_LL=.01 expected2_HL=.02 "
            "events_HH=1 events_LL=1 events_HL=2 pgt02_HH=0 pgt02_LL=0 pgt02_HL=0 "
            "pge1_HH=0 pge1_LL=0 pge1_HL=0 maxprob_HH=.01 maxprob_LL=.01 maxprob_HL=.01 "
            "max_momentum_residual=1e-15 max_energy_residual=2e-15\n"
            "SIDMx-D3 AUDIT task=1 ti=1 mode=10 pairs_HH=100 pairs_LL=100 pairs_HL=200 "
            "expected_HH=1 expected_LL=1 expected_HL=2 expected2_HH=.01 expected2_LL=.01 expected2_HL=.02 "
            "events_HH=1 events_LL=1 events_HL=2 pgt02_HH=0 pgt02_LL=0 pgt02_HL=0 "
            "pge1_HH=0 pge1_LL=0 pge1_HL=0 maxprob_HH=.01 maxprob_LL=.01 maxprob_HL=.01 "
            "max_momentum_residual=1e-15 max_energy_residual=2e-15\n"
        )
        cols, meta = collision_summary("TOY", log, 1.125)
        if len(cols) != 3 or meta["mode"] != 10 or next(x for x in cols if x["channel"] == "HL")["evaluated_pairs"] != 400:
            raise EvidenceError("self-test MPI audit aggregation failed")

        # Adversarial record corruption must fail.
        bad = root / "bad.dat"; data = bytearray(base_path.read_bytes()); data[-4:] = struct.pack("<I", 7); bad.write_bytes(data)
        try:
            read_snapshot(bad)
        except EvidenceError:
            pass
        else:
            raise EvidenceError("corrupt record marker was accepted")

        # Identity mutation must fail.
        ids_bad = ids.copy(); ids_bad[-1] += 10000
        changed = root / "changed.dat"; write_toy_snapshot(changed, pos, vel, ids_bad, ptype, mass, 0.0)
        try:
            validate_particle_identity(base, read_snapshot(changed))
        except EvidenceError:
            pass
        else:
            raise EvidenceError("changed particle ID was accepted")

        # Missing live audit for a positive cross section must fail.
        empty = root / "empty.log"; empty.write_text("")
        try:
            collision_summary("TOY", empty, 1.125)
        except EvidenceError:
            pass
        else:
            raise EvidenceError("missing positive-SIDM audit was accepted")

        return {"phase": 179, "status": "PASS", "tests": [
            "format1 read", "fixed H/L/total profiles", "H-in/L-out sign",
            "MPI audit aggregation", "corrupt-record rejection", "ID-change rejection",
            "missing-positive-audit rejection",
        ]}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--manifest", required=True); r.add_argument("--run-id", required=True)
    r.add_argument("--run-root", required=True); r.add_argument("--out-dir", required=True)
    c = sub.add_parser("combine")
    c.add_argument("--manifest", required=True); c.add_argument("--fragments-root", required=True); c.add_argument("--out-dir", required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    try:
        if args.cmd == "run":
            result = extract_one(Path(args.manifest), args.run_id, Path(args.run_root), Path(args.out_dir))
        elif args.cmd == "combine":
            result = combine(Path(args.manifest), Path(args.fragments_root), Path(args.out_dir))
        else:
            result = self_test()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (EvidenceError, OSError, ValueError, KeyError, p175.ResumeError) as exc:
        print(json.dumps({"phase": 179, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
