#!/usr/bin/env python3
"""Generate a deterministic equal-mass H/L cloud for the Phase179 standard-SIDM audit gate.

This is a commissioning fixture, not an astrophysical halo.  It deliberately uses
Type 1 and Type 2 with equal macro-particle masses and the ordinary positive
GIZMO SIDM path so the repaired identical-label control can be audited without
weakening the frozen m_H/m_L=3 D3 sentinel contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

D3_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(D3_DIR))
from phase141_generate_m11_ic import recenter, write_gadget_format1  # noqa: E402


def sample_uniform_sphere(n: int, radius_kpc: float, rng: np.random.Generator) -> np.ndarray:
    r = radius_kpc * np.cbrt(rng.random(n))
    mu = 2.0 * rng.random(n) - 1.0
    phi = 2.0 * np.pi * rng.random(n)
    st = np.sqrt(np.maximum(0.0, 1.0 - mu * mu))
    return np.column_stack((r * st * np.cos(phi), r * st * np.sin(phi), r * mu))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-total", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=179001)
    ap.add_argument("--radius-kpc", type=float, default=1.0)
    ap.add_argument("--total-mass-msun", type=float, default=1.0e11)
    ap.add_argument("--stream-speed-kms", type=float, default=100.0)
    ap.add_argument("--dispersion-kms", type=float, default=100.0)
    ap.add_argument("--output", default="phase179_equal_label_cloud.dat")
    args = ap.parse_args()

    if args.n_total <= 0 or args.n_total % 2:
        raise SystemExit("n-total must be a positive even integer")
    if args.radius_kpc <= 0.0 or args.total_mass_msun <= 0.0:
        raise SystemExit("radius and total mass must be positive")

    rng = np.random.default_rng(args.seed)
    n = args.n_total // 2
    mass_each = args.total_mass_msun / args.n_total

    pos = np.vstack((
        sample_uniform_sphere(n, args.radius_kpc, rng),
        sample_uniform_sphere(n, args.radius_kpc, rng),
    ))
    v_h = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    v_l = rng.normal(0.0, args.dispersion_kms, size=(n, 3))
    v_h[:, 0] += args.stream_speed_kms
    v_l[:, 0] -= args.stream_speed_kms
    vel = np.vstack((v_h, v_l))

    ptype = np.r_[np.ones(n, dtype=np.int32), np.full(n, 2, dtype=np.int32)]
    mass = np.full(args.n_total, mass_each, dtype=float)
    ids = np.arange(1, args.n_total + 1, dtype=np.uint32)
    pos, vel = recenter(pos, vel, mass)

    out = Path(args.output)
    write_gadget_format1(out, pos, vel, ids, ptype, mass)
    meta = {
        "phase": 179,
        "purpose": "equal-label ordinary positive-SIDM audit/equivalence fixture; not halo physics",
        "n_total": args.n_total,
        "n_H": n,
        "n_L": n,
        "seed": args.seed,
        "radius_kpc": args.radius_kpc,
        "total_mass_msun": args.total_mass_msun,
        "mH_msun": mass_each,
        "mL_msun": mass_each,
        "mass_ratio": 1.0,
        "positive_cross_section_cm2_g": 1.125,
        "stream_speed_kms": args.stream_speed_kms,
        "dispersion_kms": args.dispersion_kms,
        "snapshot": str(out.resolve()),
        "snapshot_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "total_momentum_msun_km_s": np.sum(vel * mass[:, None], axis=0).tolist(),
    }
    Path(str(out) + ".json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
