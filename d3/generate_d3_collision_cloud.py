#!/usr/bin/env python3
"""Generate a dense deterministic two-species commissioning cloud.

This is not an astrophysical halo model.  It is a live-engine collision-rate test:
- equal H/L particle counts;
- m_H/m_L = 3 exactly;
- both species occupy the same compact sphere;
- counter-streaming velocities give a controlled O(400 km/s) H-L relative speed.

The frozen D3 cross sections remain untouched.  Density, not sigma/m, is raised so
CI sees enough stochastic events to validate the real GIZMO acceptance/kick path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from phase141_generate_m11_ic import recenter, write_gadget_format1


def sample_uniform_sphere(n: int, radius_kpc: float, rng: np.random.Generator) -> np.ndarray:
    r = radius_kpc * np.cbrt(rng.random(n))
    mu = 2.0 * rng.random(n) - 1.0
    phi = 2.0 * np.pi * rng.random(n)
    st = np.sqrt(np.maximum(0.0, 1.0 - mu * mu))
    return np.column_stack((r * st * np.cos(phi), r * st * np.sin(phi), r * mu))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-total", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=177001)
    ap.add_argument("--radius-kpc", type=float, default=1.0)
    ap.add_argument("--total-mass-msun", type=float, default=1.0e10)
    ap.add_argument("--stream-speed-kms", type=float, default=100.0,
                    help="H stream is +v; L stream is -3v, so COM is zero before jitter")
    ap.add_argument("--dispersion-kms", type=float, default=5.0)
    ap.add_argument("--output", default="D3_collision_cloud.dat")
    args = ap.parse_args()

    if args.n_total <= 0 or args.n_total % 2:
        raise SystemExit("n-total must be a positive even integer")
    if args.radius_kpc <= 0 or args.total_mass_msun <= 0:
        raise SystemExit("radius and total mass must be positive")

    rng = np.random.default_rng(args.seed)
    n = args.n_total // 2
    mL = args.total_mass_msun / (4.0 * n)
    mH = 3.0 * mL

    pH = sample_uniform_sphere(n, args.radius_kpc, rng)
    pL = sample_uniform_sphere(n, args.radius_kpc, rng)
    pos = np.vstack((pH, pL))

    vH = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    vL = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    vH[:, 0] += args.stream_speed_kms
    vL[:, 0] -= 3.0 * args.stream_speed_kms
    vel = np.vstack((vH, vL))

    ptype = np.r_[np.ones(n, dtype=np.int32), np.full(n, 2, dtype=np.int32)]
    mass = np.r_[np.full(n, mH), np.full(n, mL)]
    ids = np.arange(1, args.n_total + 1, dtype=np.uint32)
    pos, vel = recenter(pos, vel, mass)

    out = Path(args.output)
    write_gadget_format1(out, pos, vel, ids, ptype, mass)
    meta = {
        "generator": "generate_d3_collision_cloud.py",
        "purpose": "live D3 collision commissioning; not an astrophysical halo",
        "n_total": args.n_total,
        "n_H": n,
        "n_L": n,
        "seed": args.seed,
        "radius_kpc": args.radius_kpc,
        "total_mass_msun": args.total_mass_msun,
        "mH_msun": mH,
        "mL_msun": mL,
        "mass_ratio": mH / mL,
        "mean_relative_stream_kms": 4.0 * args.stream_speed_kms,
        "dispersion_kms": args.dispersion_kms,
        "snapshot": str(out.resolve()),
        "snapshot_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "total_momentum_msun_km_s": np.sum(vel * mass[:, None], axis=0).tolist(),
    }
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
