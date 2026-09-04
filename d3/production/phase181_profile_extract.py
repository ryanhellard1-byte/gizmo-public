#!/usr/bin/env python3
"""Phase181 deterministic GADGET-format1 radial-profile extractor.

This freezes the production analysis map before the 80-Gyr campaign is opened.
It introduces no acceptance thresholds. It only turns the Phase172 IC and
snapshots into the already-required profiles.csv schema consumed by Phase174.

Frozen analysis choices:
- types 1/2 are H/L;
- r_s = 9.1 kpc;
- 48 logarithmic shell edges over 0.03 <= r/r_s <= 5;
- center and bulk velocity are the mass-weighted H+L COM for each snapshot;
- rho = shell mass / shell volume;
- rho_initial is the same species/shell in the time-zero IC;
- rho_rel = rho/rho_initial;
- sigma2 is the mass-weighted 1-D velocity dispersion squared, i.e. one third
  of the trace of the shell velocity-dispersion tensor;
- beta = 1 - sigma_t^2/(2 sigma_r^2), using shell-mean-subtracted velocities;
- mass_enclosed is the species mass at r <= r_hi, including material interior to
  the first reported shell edge;
- no interpolation, smoothing, adaptive bins, fitted centers, or data-dependent
  choices are allowed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

PHASE = 181
EXPECTED_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
TIME_UNIT_GYR = 0.9777923542981722
EXPECTED_TIMES_GYR = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0)
TIME_TOL_GYR = 1.0e-6
R_S_KPC = 9.1
N_BINS = 48
RMIN_OVER_RS = 0.03
RMAX_OVER_RS = 5.0
EDGES_OVER_RS = np.geomspace(RMIN_OVER_RS, RMAX_OVER_RS, N_BINS + 1)
PROFILE_COLUMNS = [
    "run_id", "time_Gyr", "r_mid_over_rs", "r_lo_over_rs", "r_hi_over_rs",
    "species", "rho", "rho_initial", "rho_rel", "sigma2", "beta", "mass_enclosed",
]


class ProfileError(RuntimeError):
    pass


@dataclass
class Snapshot:
    time_code: float
    pos: np.ndarray
    vel: np.ndarray
    mass: np.ndarray
    ptype: np.ndarray
    ids: np.ndarray


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_record(fh, path: Path) -> bytes | None:
    prefix = fh.read(4)
    if not prefix:
        return None
    if len(prefix) != 4:
        raise ProfileError(f"{path}: truncated record prefix")
    n = struct.unpack("<I", prefix)[0]
    payload = fh.read(n)
    suffix = fh.read(4)
    if len(payload) != n or len(suffix) != 4 or struct.unpack("<I", suffix)[0] != n:
        raise ProfileError(f"{path}: malformed GADGET record")
    return payload


def decode_float_record(payload: bytes, n_values: int, label: str, path: Path) -> np.ndarray:
    if len(payload) == 4 * n_values:
        return np.frombuffer(payload, dtype="<f4").astype(np.float64)
    if len(payload) == 8 * n_values:
        return np.frombuffer(payload, dtype="<f8").astype(np.float64)
    raise ProfileError(f"{path}: {label} record has {len(payload)} bytes, expected {4*n_values} or {8*n_values}")


def decode_id_record(payload: bytes, n_values: int, path: Path) -> np.ndarray:
    if len(payload) == 4 * n_values:
        return np.frombuffer(payload, dtype="<u4").astype(np.uint64)
    if len(payload) == 8 * n_values:
        return np.frombuffer(payload, dtype="<u8").astype(np.uint64)
    raise ProfileError(f"{path}: ID record width is unsupported")


def read_gadget_format1(path: Path) -> Snapshot:
    with path.open("rb") as fh:
        header = read_record(fh, path)
        if header is None or len(header) != 256:
            raise ProfileError(f"{path}: expected 256-byte GADGET header")
        npart = np.array(struct.unpack_from("<6I", header, 0), dtype=np.int64)
        mass_table = np.array(struct.unpack_from("<6d", header, 24), dtype=np.float64)
        time_code = float(struct.unpack_from("<d", header, 72)[0])
        n_total = int(npart.sum())
        if n_total <= 0:
            raise ProfileError(f"{path}: empty snapshot")
        pos_rec = read_record(fh, path)
        vel_rec = read_record(fh, path)
        id_rec = read_record(fh, path)
        if pos_rec is None or vel_rec is None or id_rec is None:
            raise ProfileError(f"{path}: missing position/velocity/ID record")
        pos = decode_float_record(pos_rec, 3 * n_total, "position", path).reshape(n_total, 3)
        vel = decode_float_record(vel_rec, 3 * n_total, "velocity", path).reshape(n_total, 3)
        ids = decode_id_record(id_rec, n_total, path)

        ptype = np.concatenate([
            np.full(int(npart[t]), t, dtype=np.int8) for t in range(6) if npart[t] > 0
        ])
        mass = np.empty(n_total, dtype=np.float64)
        variable_count = int(sum(npart[t] for t in range(6) if npart[t] > 0 and mass_table[t] == 0.0))
        if variable_count:
            mass_rec = read_record(fh, path)
            if mass_rec is None:
                raise ProfileError(f"{path}: snapshot truncated before required mass record")
            variable = decode_float_record(mass_rec, variable_count, "mass", path)
        else:
            variable = np.empty(0, dtype=np.float64)
        cursor = 0
        var_cursor = 0
        for t in range(6):
            count = int(npart[t])
            if not count:
                continue
            if mass_table[t] != 0.0:
                mass[cursor:cursor + count] = mass_table[t]
            else:
                stop = var_cursor + count
                if stop > len(variable):
                    raise ProfileError(f"{path}: variable-mass record is truncated")
                mass[cursor:cursor + count] = variable[var_cursor:stop]
                var_cursor = stop
            cursor += count
        if var_cursor != variable_count:
            raise ProfileError(f"{path}: variable-mass record accounting mismatch")

    keep = (ptype == 1) | (ptype == 2)
    if not np.any(ptype == 1) or not np.any(ptype == 2):
        raise ProfileError(f"{path}: both type-1 H and type-2 L particles are required")
    if np.any(~np.isfinite(pos[keep])) or np.any(~np.isfinite(vel[keep])) or np.any(~np.isfinite(mass[keep])):
        raise ProfileError(f"{path}: non-finite H/L particle data")
    if np.any(mass[keep] <= 0):
        raise ProfileError(f"{path}: non-positive H/L particle mass")
    if len(np.unique(ids[keep])) != int(keep.sum()):
        raise ProfileError(f"{path}: duplicate H/L particle IDs")
    return Snapshot(time_code, pos[keep], vel[keep], mass[keep], ptype[keep], ids[keep])


def centered(s: Snapshot) -> Tuple[np.ndarray, np.ndarray]:
    mt = float(s.mass.sum())
    center = np.sum(s.pos * s.mass[:, None], axis=0) / mt
    bulk = np.sum(s.vel * s.mass[:, None], axis=0) / mt
    return s.pos - center, s.vel - bulk


def profile_species(s: Snapshot, species: str) -> List[Dict[str, float]]:
    x, v = centered(s)
    if species == "H":
        mask = s.ptype == 1
    elif species == "L":
        mask = s.ptype == 2
    elif species == "total":
        mask = np.ones(len(s.mass), dtype=bool)
    else:
        raise ProfileError(f"unknown species {species}")

    x = x[mask]
    v = v[mask]
    m = s.mass[mask]
    r = np.linalg.norm(x, axis=1)
    edges = EDGES_OVER_RS * R_S_KPC
    shell_index = np.searchsorted(edges, r, side="right") - 1
    out = []
    for b in range(N_BINS):
        lo, hi = float(edges[b]), float(edges[b + 1])
        in_shell = shell_index == b
        shell_mass = float(m[in_shell].sum())
        volume = 4.0 * math.pi * (hi**3 - lo**3) / 3.0
        rho = shell_mass / volume
        enclosed = float(m[r <= hi].sum())
        sigma2 = float("nan")
        beta = float("nan")
        if np.any(in_shell):
            ms = m[in_shell]
            vs = v[in_shell]
            xs = x[in_shell]
            ws = ms / ms.sum()
            mean_v = np.sum(vs * ws[:, None], axis=0)
            dv = vs - mean_v
            sig3 = float(np.sum(ws * np.sum(dv * dv, axis=1)))
            sigma2 = sig3 / 3.0
            rs = np.linalg.norm(xs, axis=1)
            if np.any(rs <= 0.0):
                raise ProfileError("particle at exact analysis center makes radial anisotropy undefined")
            er = xs / rs[:, None]
            vr = np.sum(dv * er, axis=1)
            sig_r2 = float(np.sum(ws * vr * vr))
            sig_t2 = max(0.0, sig3 - sig_r2)
            if sig_r2 > 0.0:
                beta = 1.0 - sig_t2 / (2.0 * sig_r2)
        out.append({
            "r_lo_over_rs": float(EDGES_OVER_RS[b]),
            "r_hi_over_rs": float(EDGES_OVER_RS[b + 1]),
            "r_mid_over_rs": float(math.sqrt(EDGES_OVER_RS[b] * EDGES_OVER_RS[b + 1])),
            "rho": rho,
            "sigma2": sigma2,
            "beta": beta,
            "mass_enclosed": enclosed,
            "shell_particles": int(in_shell.sum()),
        })
    return out


def load_manifest(path: Path, run_id: str) -> Dict[str, str]:
    observed = sha256_file(path)
    if observed != EXPECTED_MANIFEST_SHA256:
        raise ProfileError(f"frozen manifest SHA mismatch: {observed}")
    with path.open(newline="") as fh:
        hits = [r for r in csv.DictReader(fh) if str(r.get("run_id")) == str(run_id)]
    if len(hits) != 1:
        raise ProfileError(f"expected one manifest row for {run_id}, found {len(hits)}")
    times = tuple(float(x.strip()) for x in hits[0]["analysis_times_Gyr"].split(",") if x.strip())
    if len(times) != len(EXPECTED_TIMES_GYR) or any(abs(a-b) > 1e-9 for a,b in zip(times,EXPECTED_TIMES_GYR)):
        raise ProfileError(f"{run_id}: analysis-time contract changed")
    return hits[0]


def discover_snapshots(run_dir: Path) -> List[Tuple[float, Path, Snapshot]]:
    found = []
    for path in sorted(p for p in run_dir.glob("snapshot*") if p.is_file()):
        snap = read_gadget_format1(path)
        time_gyr = snap.time_code * TIME_UNIT_GYR
        found.append((time_gyr, path, snap))
    return found


def map_required_times(ic: Path, run_dir: Path) -> List[Tuple[float, Path, Snapshot]]:
    mapped = [(0.0, ic, read_gadget_format1(ic))]
    candidates = discover_snapshots(run_dir)
    for req in EXPECTED_TIMES_GYR[1:]:
        hits = [(abs(t-req), p, s, t) for t,p,s in candidates if abs(t-req) <= TIME_TOL_GYR]
        if len(hits) != 1:
            raise ProfileError(f"required snapshot time {req} Gyr has {len(hits)} matches")
        _, path, snap, observed = hits[0]
        mapped.append((req, path, snap))
    if len({str(p.resolve()) for _, p, _ in mapped[1:]}) != len(EXPECTED_TIMES_GYR) - 1:
        raise ProfileError("one snapshot matched more than one required output time")
    return mapped


def build_profiles(run_id: str, ic: Path, run_dir: Path) -> Tuple[List[Dict[str, object]], Dict]:
    mapped = map_required_times(ic, run_dir)
    initial_snap = mapped[0][2]
    initial = {sp: profile_species(initial_snap, sp) for sp in ("H", "L", "total")}
    initial_ids = set(int(x) for x in initial_snap.ids)
    rows: List[Dict[str, object]] = []
    source = []

    for time_gyr, path, snap in mapped:
        ids = set(int(x) for x in snap.ids)
        if ids != initial_ids:
            raise ProfileError(f"{run_id}: H/L particle ID set changed at {time_gyr} Gyr")
        source.append({"time_Gyr": time_gyr, "path": str(path.resolve()), "sha256": sha256_file(path)})
        for sp in ("H", "L", "total"):
            now = profile_species(snap, sp)
            base = initial[sp]
            for cur, ini in zip(now, base):
                rho0 = float(ini["rho"])
                rho = float(cur["rho"])
                if rho0 <= 0.0:
                    raise ProfileError(
                        f"{run_id}: zero initial density for {sp} bin {cur['r_mid_over_rs']}; frozen rho_rel undefined"
                    )
                if rho <= 0.0:
                    raise ProfileError(
                        f"{run_id}: non-positive density for {sp} at {time_gyr} Gyr bin {cur['r_mid_over_rs']}"
                    )
                sigma2 = float(cur["sigma2"])
                beta = float(cur["beta"])
                if not math.isfinite(sigma2) or not math.isfinite(beta):
                    raise ProfileError(
                        f"{run_id}: insufficient shell kinematics for {sp} at {time_gyr} Gyr bin {cur['r_mid_over_rs']}"
                    )
                rows.append({
                    "run_id": run_id,
                    "time_Gyr": time_gyr,
                    "r_mid_over_rs": cur["r_mid_over_rs"],
                    "r_lo_over_rs": cur["r_lo_over_rs"],
                    "r_hi_over_rs": cur["r_hi_over_rs"],
                    "species": sp,
                    "rho": rho,
                    "rho_initial": rho0,
                    "rho_rel": rho / rho0,
                    "sigma2": sigma2,
                    "beta": beta,
                    "mass_enclosed": cur["mass_enclosed"],
                })

    expected_rows = len(EXPECTED_TIMES_GYR) * 3 * N_BINS
    if len(rows) != expected_rows:
        raise ProfileError(f"{run_id}: profile row count {len(rows)} != {expected_rows}")
    report = {
        "phase": PHASE,
        "status": "PASS",
        "run_id": run_id,
        "analysis_times_Gyr": list(EXPECTED_TIMES_GYR),
        "r_s_kpc": R_S_KPC,
        "radial_bins": N_BINS,
        "radial_range_over_rs": [RMIN_OVER_RS, RMAX_OVER_RS],
        "profile_rows": len(rows),
        "source_snapshots": source,
        "definitions": {
            "center": "mass-weighted H+L center of mass independently at each epoch",
            "bulk_velocity": "mass-weighted H+L bulk velocity independently at each epoch",
            "rho": "shell mass / spherical shell volume",
            "rho_initial": "same species and fixed shell in time-zero IC",
            "sigma2": "mass-weighted one-dimensional velocity dispersion squared: trace(cov_v)/3",
            "beta": "1 - sigma_t^2/(2 sigma_r^2) from shell-mean-subtracted velocities",
            "mass_enclosed": "species mass with centered radius <= shell outer edge",
        },
    }
    return rows, report


def write_profiles(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PROFILE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--ic", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report-json")
    args = ap.parse_args()
    try:
        load_manifest(Path(args.manifest), args.run_id)
        rows, report = build_profiles(args.run_id, Path(args.ic), Path(args.run_dir))
        write_profiles(Path(args.output), rows)
        if args.report_json:
            Path(args.report_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (ProfileError, OSError, ValueError, struct.error) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())