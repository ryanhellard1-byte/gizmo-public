#!/usr/bin/env python3
"""Deterministic dense equal-mass two-label cloud for Phase181 standard-SIDM audit CI.

This is a software/equivalence fixture, not an astrophysical halo.  It exercises
the ordinary positive DM_InteractionCrossSection path with type-1/type-2 labels
and m1=m2, which is the Phase172 identical-label control contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from generate_d3_collision_cloud import sample_uniform_sphere
from phase141_generate_m11_ic import recenter, write_gadget_format1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-total", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=181001)
    ap.add_argument("--radius-kpc", type=float, default=1.0)
    ap.add_argument("--total-mass-msun", type=float, default=1.0e11)
    ap.add_argument("--stream-speed-kms", type=float, default=100.0)
    ap.add_argument("--dispersion-kms", type=float, default=100.0)
    ap.add_argument("--output", default="phase181_equal_collision_cloud.dat")
    args = ap.parse_args()

    if args.n_total <= 0 or args.n_total % 2:
        raise SystemExit("n-total must be a positive even integer")
    if args.radius_kpc <= 0 or args.total_mass_msun <= 0:
        raise SystemExit("radius and total mass must be positive")

    rng = np.random.default_rng(args.seed)
    n = args.n_total // 2
    mass_each = args.total_mass_msun / args.n_total

    p1 = sample_uniform_sphere(n, args.radius_kpc, rng)
    p2 = sample_uniform_sphere(n, args.radius_kpc, rng)
    pos = np.vstack((p1, p2))

    v1 = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    v2 = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    v1[:, 0] += args.stream_speed_kms
    v2[:, 0] -= args.stream_speed_kms
    vel = np.vstack((v1, v2))

    ptype = np.r_[np.ones(n, dtype=np.int32), np.full(n, 2, dtype=np.int32)]
    mass = np.full(args.n_total, mass_each, dtype=float)
    ids = np.arange(1, args.n_total + 1, dtype=np.uint32)
    pos, vel = recenter(pos, vel, mass)

    out = Path(args.output)
    write_gadget_format1(out, pos, vel, ids, ptype, mass)
    meta = {
        "generator": "phase181_generate_equal_collision_cloud.py",
        "purpose": "positive-SIDM audit/equivalence fixture; not an astrophysical halo",
        "n_total": args.n_total,
        "n_type1": n,
        "n_type2": n,
        "seed": args.seed,
        "mass_ratio": 1.0,
        "radius_kpc": args.radius_kpc,
        "total_mass_msun": args.total_mass_msun,
        "mass_each_msun": mass_each,
        "mean_relative_stream_kms": 2.0 * args.stream_speed_kms,
        "dispersion_kms": args.dispersion_kms,
        "snapshot": str(out.resolve()),
        "snapshot_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "total_momentum_msun_km_s": np.sum(vel * mass[:, None], axis=0).tolist(),
    }
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
