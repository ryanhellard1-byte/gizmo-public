#!/usr/bin/env python3
"""Stress-test the Hellard spectral-dominance modified-inertia candidate.

Candidate two-mode reduction:
    D = a^2 / (a^2 + beta a_bg^2)
    mu_eff = 1 - D^p [1 - mu(a/a_H)]
    a * mu_eff = g_N

This script scans stellar mass, wide-binary separation, and Galactic background
acceleration. It is a phenomenological reduced model derived from the idea that
low-acceleration modification activates only when the mode's spectral power is
not dominated by a stronger background mode.

It does NOT constitute a fundamental relativistic completion or a full Bayesian
wide-binary likelihood.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.optimize import brentq

G = 6.67430e-11
M_SUN = 1.98847e30
AU = 1.495978707e11
A_H = 1.12e-10


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def dominance(a: float, a_bg: float, beta: float = 1.0) -> float:
    return a*a / (a*a + beta*a_bg*a_bg)


def mu_eff(a: float, a_bg: float, p: float = 2.0, beta: float = 1.0) -> float:
    d = dominance(a, a_bg, beta)
    return 1.0 - d**p * (1.0 - mu(a / A_H))


def solve_accel(g_n: float, a_bg: float, p: float = 2.0, beta: float = 1.0) -> float:
    def f(a: float) -> float:
        return a * mu_eff(a, a_bg, p, beta) - g_n

    lo = max(g_n, 1e-30)
    hi = max(50*A_H, 50*g_n, 50*a_bg)
    flo, fhi = f(lo), f(hi)
    for _ in range(20):
        if flo * fhi <= 0:
            break
        hi *= 2.0
        fhi = f(hi)
    else:
        raise RuntimeError("could not bracket acceleration root")
    return brentq(f, lo, hi, xtol=1e-18, rtol=1e-12, maxiter=100)


def circular_speed_boost(g_n: float, a_bg: float, p: float = 2.0, beta: float = 1.0) -> float:
    a = solve_accel(g_n, a_bg, p, beta)
    return math.sqrt(a / g_n) - 1.0


def stress_test(p: float = 2.0, beta: float = 1.0):
    masses = np.array([0.5, 0.75, 1.0, 1.5, 2.0]) * M_SUN
    separations = np.geomspace(3e3, 3e4, 30) * AU
    backgrounds = np.array([1.4, 1.7, 2.0]) * 1e-10

    worst = (-1.0, None)
    for mass in masses:
        for r in separations:
            g_n = G * mass / r**2
            for a_bg in backgrounds:
                boost = circular_speed_boost(g_n, a_bg, p, beta)
                if boost > worst[0]:
                    worst = (boost, (mass/M_SUN, r/AU/1000.0, a_bg))
    return worst


def solar_mass_peak(p: float = 2.0, beta: float = 1.0, a_bg: float = 1.7e-10):
    best = (-1.0, None)
    for sep_kau in np.geomspace(1.0, 50.0, 120):
        r = sep_kau * 1e3 * AU
        g_n = G * M_SUN / r**2
        a = solve_accel(g_n, a_bg, p, beta)
        boost = math.sqrt(a/g_n) - 1.0
        d = dominance(a, a_bg, beta)
        if boost > best[0]:
            best = (boost, (sep_kau, g_n/A_H, d))
    return best


def isolated_deep_check():
    # With a_bg=0, D=1 and the ordinary modified-inertia branch is recovered.
    g_n = 0.01 * A_H
    a = solve_accel(g_n, 0.0, p=2.0, beta=1.0)
    expected = math.sqrt(A_H * g_n)
    return a, expected, abs(a-expected)/expected


def main():
    p, beta = 2.0, 1.0
    worst_boost, where = stress_test(p, beta)
    peak_boost, peak_where = solar_mass_peak(p, beta)
    a, expected, rel = isolated_deep_check()

    print(f"benchmark p={p:g}, beta={beta:g}, a_H={A_H:.6e} m/s^2")
    print(f"wide-binary stress worst dv/v = {100*worst_boost:.3f}%")
    print(f"  at M={where[0]:.2f} Msun, sep={where[1]:.3f} kAU, a_bg={where[2]:.3e} m/s^2")
    print(f"solar-mass peak dv/v = {100*peak_boost:.3f}%")
    print(f"  at sep={peak_where[0]:.3f} kAU, gN/a_H={peak_where[1]:.3f}, D={peak_where[2]:.3f}")
    print(f"isolated deep-limit relative error vs sqrt(a_H gN) = {rel:.4%}")

    # Conservative research gates, not observational likelihood statements.
    if worst_boost >= 0.05:
        raise SystemExit("FAIL: benchmark exceeds 5% circular-speed wide-binary stress threshold")
    if rel >= 0.02:
        raise SystemExit("FAIL: isolated deep limit deviates by >=2% from sqrt(a_H gN)")

    print("spectral-dominance reduced-model gate: PASS")


if __name__ == "__main__":
    main()
