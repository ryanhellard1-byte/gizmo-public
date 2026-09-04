#!/usr/bin/env python3
"""Generate deterministic Phase165 M11 ICs from the validated Phase141 machinery.

Physical rows default to m_H/m_L=3. The hostile identical-label control must be
requested explicitly with --mass-ratio 1. Particle-order permutation preserves
particle IDs and phase-space states and changes only in-file ordering.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "d3" / "phase141_generate_m11_ic.py"
spec = importlib.util.spec_from_file_location("phase141_generate_m11_ic", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-total", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--taper", type=float, default=0.05, choices=[0.03, 0.05, 0.10])
    ap.add_argument("--mass-ratio", type=float, default=3.0, choices=[1.0, 3.0])
    ap.add_argument("--permute-within-species", action="store_true")
    ap.add_argument("--permutation-seed", type=int, default=None)
    ap.add_argument("--output", required=True)
    ap.add_argument("--metadata", default=None)
    args = ap.parse_args()

    if args.n_total % 2:
        raise SystemExit("n-total must be even")
    if args.permute_within_species and args.permutation_seed is None:
        raise SystemExit("--permute-within-species requires --permutation-seed")

    rng = np.random.default_rng(args.seed)
    halo = base.TruncatedNFW(args.taper)
    _, _, feval = base.build_df(halo)
    n = args.n_total // 2

    rH = base.sample_radii(halo, n, rng)
    rL = base.sample_radii(halo, n, rng)
    pH = base.sample_positions(rH, rng)
    pL = base.sample_positions(rL, rng)
    vH = base.sample_velocities(halo, feval, rH, rng)
    vL = base.sample_velocities(halo, feval, rL, rng)

    ratio = float(args.mass_ratio)
    mL = halo.Mtot / ((ratio + 1.0) * n)
    mH = ratio * mL
    pos = np.vstack([pH, pL])
    vel = np.vstack([vH, vL])
    ptype = np.r_[np.ones(n, dtype=np.int32), np.full(n, 2, dtype=np.int32)]
    mass = np.r_[np.full(n, mH), np.full(n, mL)]
    ids = np.arange(1, args.n_total + 1, dtype=np.uint32)
    pos, vel = base.recenter(pos, vel, mass)

    if args.permute_within_species:
        prng = np.random.default_rng(args.permutation_seed)
        h = np.arange(0, n)
        l = np.arange(n, 2*n)
        prng.shuffle(h)
        prng.shuffle(l)
        order = np.r_[h, l]
        pos = pos[order]
        vel = vel[order]
        ptype = ptype[order]
        mass = mass[order]
        ids = ids[order]

    base.write_gadget_format1(args.output, pos, vel, ids, ptype, mass)
    outpath = Path(args.output)
    meta = {
        "generator": "d3/production/generate_phase165_ic.py",
        "base_generator": "d3/phase141_generate_m11_ic.py",
        "n_total": args.n_total,
        "n_H": n,
        "n_L": n,
        "seed": args.seed,
        "M200_Msun": base.M200,
        "rho_s_Msun_kpc3": base.RHO_S,
        "r_s_kpc": base.R_S,
        "c200": base.C200,
        "r200_kpc": base.R200,
        "taper_rd_over_r200": args.taper,
        "Mtotal_tapered_Msun": halo.Mtot,
        "mH_num_Msun": mH,
        "mL_num_Msun": mL,
        "mass_ratio": mH/mL,
        "permuted_within_species": bool(args.permute_within_species),
        "permutation_seed": args.permutation_seed,
        "snapshot": str(outpath.resolve()),
        "snapshot_sha256": hashlib.sha256(outpath.read_bytes()).hexdigest(),
        "total_momentum_Msun_km_s": np.sum(vel*mass[:, None], axis=0).tolist(),
    }
    mpath = Path(args.metadata) if args.metadata else Path(str(outpath) + ".json")
    mpath.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
