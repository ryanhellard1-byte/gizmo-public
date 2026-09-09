#!/usr/bin/env python3
"""Explore a reciprocal two-frequency Hellard kernel.

We symmetrize the previous directional kernel theta(y)=7/(1+6y) via
    K(y)=sqrt(theta(y) theta(1/y))
so K(y)=K(1/y), as required for a Hermitian quadratic cross-frequency kernel.

This script quantifies how much cross-talk survives for hierarchical frequency ratios.
The purpose is diagnostic: the diagonal nonlinear inertia term must carry the galaxy
RAR/BTFR branch; the symmetric off-diagonal kernel should remain perturbative.
"""
from __future__ import annotations
import math


def theta(y: float) -> float:
    return 7.0 / (1.0 + 6.0*y)


def K(y: float) -> float:
    if y <= 0:
        raise ValueError("frequency ratio must be positive")
    return math.sqrt(theta(y) * theta(1.0/y))


def main():
    ratios = [1.0, 1e1, 1e2, 1e3, 1e4, 1e6, 1e8]
    print("ratio, K(ratio), reciprocity_error")
    for r in ratios:
        kr = K(r)
        err = abs(kr-K(1.0/r))
        print(f"{r:.1e}, {kr:.8e}, {err:.3e}")
        if err > 1e-14:
            raise SystemExit("FAIL: reciprocal kernel symmetry broken")

    # Cross-talk should be strongly reduced for large mode hierarchy.
    if K(1e3) >= 0.1:
        raise SystemExit("FAIL: 1e3 frequency hierarchy cross-talk is too large")
    if K(1e6) >= 0.01:
        raise SystemExit("FAIL: 1e6 frequency hierarchy cross-talk is too large")

    print("symmetric-kernel hierarchy gate: PASS")


if __name__ == "__main__":
    main()
