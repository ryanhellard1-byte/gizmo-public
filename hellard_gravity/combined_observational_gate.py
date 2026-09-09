#!/usr/bin/env python3
"""Combined observational gate for the Hellard modified-inertia benchmark.

This deliberately uses ONE universal kernel:
    theta(y) = theta0 / [1 + (theta0 - 1) y^q]
with y = omega_ext/omega_int.

Galaxy circular modes are normalized by theta(1)=1. The wide-binary layer is
currently a literature-level exclusion gate rather than a raw Gaia likelihood:
Cookson et al. (MNRAS 547, 2026) find no ~20% MOND boost in a high-purity
Gaia DR3 sample at 1-30 kAU. We therefore require the benchmark's local EFE
proxy to remain below 2% across representative 10-100 kyr internal periods.

This is intentionally conservative and must be replaced by the raw catalogue
likelihood when those data are ingested.
"""
from __future__ import annotations

import math

A_H = 1.19e-10
A_EXT = 1.7e-10
P_GAL_YR = 220e6
THETA0 = 7.0
Q = 1.0


def theta(y: float, theta0: float = THETA0, q: float = Q) -> float:
    return theta0 / (1.0 + (theta0 - 1.0) * y**q)


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def external_field_proxy(period_yr: float, theta0=THETA0, q=Q) -> float:
    y = period_yr / P_GAL_YR
    x = theta(y, theta0, q) * A_EXT / A_H
    return 1.0 / mu(x) - 1.0


def check_kernel(theta0=THETA0, q=Q):
    if abs(theta(1.0, theta0, q) - 1.0) > 1e-12:
        raise AssertionError("theta(1) must equal 1 to preserve isolated circular-galaxy normalization")

    periods = {
        "Earth": 1.0,
        "Saturn": 29.457,
        "Neptune": 164.8,
        "WB_10kyr": 1e4,
        "WB_100kyr": 1e5,
    }
    boosts = {name: external_field_proxy(p, theta0, q) for name, p in periods.items()}

    if max(boosts[k] for k in ("Earth", "Saturn", "Neptune")) >= 0.005:
        raise AssertionError(f"planetary proxy exceeds 0.5%: {boosts}")
    if max(boosts[k] for k in ("WB_10kyr", "WB_100kyr")) >= 0.02:
        raise AssertionError(f"wide-binary proxy exceeds 2%: {boosts}")
    return boosts


def main():
    boosts = check_kernel()
    print(f"universal kernel theta0={THETA0:g}, q={Q:g}")
    for key, value in boosts.items():
        print(f"{key:12s}: proxy boost={100*value:.4f}%")
    print("combined proxy gate: PASS")


if __name__ == "__main__":
    main()
