#!/usr/bin/env python3
"""Causal, scale-free continuum memory representation for Hellard research.

For each relaxation rate lambda>0 define a causal low-pass memory
    dm_lambda/dt + lambda m_lambda = lambda a(t).
For a harmonic a=A exp(i omega t),
    m/A = lambda/(lambda+i omega).
The logarithmic scale derivative
    q_lambda = d m_lambda / d ln(lambda)
has transfer
    q/A = i omega lambda/(lambda+i omega)^2.
Its scale-energy density is localized around lambda~omega and obeys
    2 int_0^infty |q_lambda|^2 d ln lambda = |A|^2.
No preferred time scale appears because lambda is integrated with d ln lambda.
"""
from __future__ import annotations

import math


def band_power_density(lam: float, omega: float, amp: float = 1.0) -> float:
    """Return 2 |q_lambda|^2 per d ln(lambda)."""
    return 2.0 * amp * amp * (omega * omega * lam * lam) / ((lam * lam + omega * omega) ** 2)


def cumulative_slow_power(lam: float, omega: float, amp: float = 1.0) -> float:
    """Analytic integral of the band-power density from 0 to lam."""
    return amp * amp * lam * lam / (lam * lam + omega * omega)


def total_power_numeric(omega: float, amp: float = 1.0, decades: float = 12.0, n: int = 200000) -> float:
    """Trapezoid integration over log(lambda) for a convergence check."""
    lo = math.log(omega) - decades * math.log(10.0)
    hi = math.log(omega) + decades * math.log(10.0)
    h = (hi - lo) / (n - 1)
    total = 0.0
    prev = band_power_density(math.exp(lo), omega, amp)
    for i in range(1, n):
        x = lo + i * h
        cur = band_power_density(math.exp(x), omega, amp)
        total += 0.5 * (prev + cur) * h
        prev = cur
    return total


def main() -> None:
    # Scale invariance checks over many absolute frequencies.
    for omega in (1e-9, 1e-3, 1.0, 1e3, 1e9):
        total = total_power_numeric(omega, amp=1.7, decades=8.0, n=40000)
        expected = 1.7 ** 2
        rel = abs(total - expected) / expected
        print(f"omega={omega:.1e}: recovered={total:.12f}, expected={expected:.12f}, relerr={rel:.3e}")
        if rel > 1e-6:
            raise SystemExit("FAIL: continuum memory power identity did not converge")

    # The bandpower peaks exactly at lambda=omega.
    omega = 3.7
    center = band_power_density(omega, omega)
    left = band_power_density(omega / 2.0, omega)
    right = band_power_density(2.0 * omega, omega)
    print(f"peak test: left={left:.6f}, center={center:.6f}, right={right:.6f}")
    if not (center > left and center > right):
        raise SystemExit("FAIL: bandpower is not centered near lambda=omega")

    # Half the power lies below lambda=omega.
    half = cumulative_slow_power(omega, omega)
    print(f"cumulative at lambda=omega: {half:.12f}")
    if abs(half - 0.5) > 1e-12:
        raise SystemExit("FAIL: analytic cumulative-power identity")

    print("PASS: causal scale-free continuum memory representation identities")


if __name__ == "__main__":
    main()
