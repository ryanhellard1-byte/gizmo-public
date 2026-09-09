#!/usr/bin/env python3
"""Exact two-mode Euler-equation test for the Hellard spectral-dominance action.

Spectral action density:
    S_kin = (m/2) ∫ dω/(2π ω^2) F(P_ω, B_ω)

with
    P_ω = |a_ω|^2,
    D = P/(P + beta B),
    F_P = 1 - D^p [1 - mu(sqrt(P))],
    mu(x) = x/sqrt(1+x^2).

B is a smooth slow-background spectral-power functional. In the two-mode
reduction, variation of B generates the reciprocal cross term explicitly.
The action therefore satisfies variational reciprocity by construction.

This is a nonrelativistic two-mode research model, not a complete theory of gravity.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

G = 6.67430e-11
M_SUN = 1.98847e30
AU = 1.495978707e11
YEAR = 365.25 * 86400.0
A_H = 1.12e-10
A_EXT = 1.7e-10
P_GAL = 220e6 * YEAR
P_EXP = 2.0
BETA = 1.0


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def wslow(y: float, n: int = 4) -> float:
    return 1.0 / (1.0 + y**n)


def f_p(P: float, B: float) -> float:
    if P <= 0:
        return 1.0
    D = P / (P + BETA*B) if P + BETA*B > 0 else 1.0
    return 1.0 - D**P_EXP * (1.0 - mu(math.sqrt(P)))


def f_b(P: float, B: float) -> float:
    if P <= 0:
        return 0.0

    def integrand(u: float) -> float:
        if u <= 0:
            return 0.0
        q = 1.0 - mu(math.sqrt(u))
        return P_EXP*BETA*(u**P_EXP)*q / ((u + BETA*B)**(P_EXP + 1.0))

    return quad(integrand, 0.0, P, epsabs=1e-9, epsrel=2e-8, limit=80)[0]


def internal_inertia_coeff(x_i: float, x_e: float, w_i: float, w_e: float) -> float:
    P_i, P_e = x_i*x_i, x_e*x_e
    B_i = wslow(w_e/w_i) * P_e
    B_e = wslow(w_i/w_e) * P_i
    return (
        f_p(P_i, B_i)
        + (w_i*w_i/(w_e*w_e)) * wslow(w_i/w_e) * f_b(P_e, B_e)
    )


def solve_binary(g_n: float, mass: float = M_SUN, a_bg: float = A_EXT):
    r = math.sqrt(G*mass/g_n)
    w_i = math.sqrt(G*mass/r**3)
    w_e = 2.0*math.pi/P_GAL
    x_e = a_bg/A_H
    g = g_n/A_H

    def equation(x_i: float) -> float:
        return x_i*internal_inertia_coeff(x_i, x_e, w_i, w_e) - g

    # The physical branch is continuous from the Newtonian root.  Bracket it
    # directly instead of evaluating a 300-point logarithmic scan at every
    # stress-grid point.  This changes only the numerical root finder.
    lo = max(1e-10, 1e-4*g)
    hi = max(10.0, 4.0*g + 10.0)
    flo, fhi = equation(lo), equation(hi)
    for _ in range(16):
        if flo*fhi <= 0:
            break
        hi *= 2.0
        fhi = equation(hi)
    else:
        raise RuntimeError("no positive binary acceleration bracket")

    x_i = brentq(equation, lo, hi, xtol=1e-11, rtol=2e-10, maxiter=80)
    c = internal_inertia_coeff(x_i, x_e, w_i, w_e)
    return x_i*A_H, c


def stress_grid():
    high = (-1e9, None)
    low = (1e9, None)
    for mass_factor in [0.5, 1.0, 2.0]:
        mass = mass_factor*M_SUN
        for a_bg in [1.4e-10, 1.7e-10, 2.0e-10]:
            for sep_kau in np.geomspace(3.0, 30.0, 24):
                r = sep_kau*1e3*AU
                g_n = G*mass/r**2
                a, c = solve_binary(g_n, mass, a_bg)
                dv = math.sqrt(a/g_n) - 1.0
                item = (mass_factor, a_bg, sep_kau, c, a/g_n)
                if dv > high[0]:
                    high = (dv, item)
                if dv < low[0]:
                    low = (dv, item)
    return high, low


def main():
    print("Hellard spectral-dominance exact two-mode action")
    print(f"a_H={A_H:.6e} m/s^2, p={P_EXP:g}, beta={BETA:g}")
    for sep_kau in [1, 3, 5, 7, 10, 15, 20, 30]:
        r = sep_kau*1e3*AU
        g_n = G*M_SUN/r**2
        a, c = solve_binary(g_n)
        dv = math.sqrt(a/g_n)-1.0
        print(f"{sep_kau:>2} kAU: coeff={c:.6f}, a/gN={a/g_n:.6f}, dv/v={100*dv:+.3f}%")

    high, low = stress_grid()
    print(f"stress max dv/v={100*high[0]:+.3f}% at M={high[1][0]:.2f} Msun, bg={high[1][1]:.2e}, sep={high[1][2]:.3f} kAU")
    print(f"stress min dv/v={100*low[0]:+.3f}% at M={low[1][0]:.2f} Msun, bg={low[1][1]:.2e}, sep={low[1][2]:.3f} kAU")

    if high[0] >= 0.05:
        raise SystemExit("FAIL: action-derived positive wide-binary deviation exceeds +5%")
    if low[0] <= -0.05:
        raise SystemExit("FAIL: action-derived negative wide-binary deviation exceeds -5%")
    print("exact two-mode spectral-action gate: PASS")


if __name__ == "__main__":
    main()
