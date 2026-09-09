#!/usr/bin/env python3
"""Stationary quartic-action diagnostic for Hellard modified inertia.

Goal
----
Construct the simplest frequency-conserving environmental correction that:
1. is compatible with time-translation invariance,
2. is reciprocal/Hermitian in the frequency hierarchy,
3. leaves the isolated single-mode circular branch untouched,
4. suppresses high-acceleration planetary cross-reaction strongly enough for Cassini.

This is a reduced two-mode diagnostic, not yet a full relativistic or continuous-spectrum theory.
"""
from __future__ import annotations

import math

A_H = 1.12e-10
A_EXT = 1.70e-10
P_GAL_YR = 2.20e8
AU = 1.495978707e11
EPSILON = 1.0  # natural O(1) benchmark; dimensionless


def mu(s: float) -> float:
    return s / math.sqrt(1.0 + s*s)


def psi(s: float) -> float:
    """Bounded primitive of 1-mu(s), normalized by Psi(0)=0.

    Psi'(s)=1-mu(s), and Psi(s)->1 for s->infinity.
    """
    return 1.0 + s - math.sqrt(1.0 + s*s)


def theta_asym(y: float) -> float:
    return 7.0 / (1.0 + 6.0*y)


def k_sym(y: float) -> float:
    """Hermitian frequency-ratio kernel K(y)=K(1/y)."""
    return math.sqrt(theta_asym(y) * theta_asym(1.0/y))


def cross_accel_on_internal(a_int: float, p_int_yr: float, epsilon: float = EPSILON) -> float:
    """Leading reduced-action cross correction on a fast internal mode.

    Reduced quartic interaction:
        L_x ~ m eps a_H^2/(w_i^2+w_e^2) K(w_e/w_i) Psi(s_i) Psi(s_e)

    Variation wrt internal amplitude gives, in acceleration units,
        delta a_i = eps a_H [w_i^2/(w_i^2+w_e^2)] K(y)
                    [1-mu(s_i)] Psi(s_e)

    where y=w_e/w_i=P_i/P_e.
    """
    y = p_int_yr / P_GAL_YR
    freq_factor = 1.0 / (1.0 + y*y)
    s_int = a_int / A_H
    s_ext = A_EXT / A_H
    return (
        epsilon
        * A_H
        * freq_factor
        * k_sym(y)
        * (1.0 - mu(s_int))
        * psi(s_ext)
    )


def main() -> None:
    systems = [
        ("Earth", 1.0, 5.93e-3, 1.0),
        ("Saturn", 29.457, 6.57e-5, 9.58),
        ("Neptune", 164.8, 6.55e-6, 30.07),
    ]

    print("stationary quartic reciprocal-action diagnostic")
    print(f"a_H={A_H:.6e} m/s^2, epsilon={EPSILON:g}")
    print(f"Psi(a_ext/a_H)={psi(A_EXT/A_H):.6f}")

    worst_q = 0.0
    for name, period, a_int, radius_au in systems:
        y = period/P_GAL_YR
        da = cross_accel_on_internal(a_int, period)
        q_proxy = abs(da)/(radius_au*AU)
        worst_q = max(worst_q, q_proxy)
        print(
            f"{name:8s}: y={y:.3e} Ksym={k_sym(y):.3e} "
            f"1-mu={1-mu(a_int/A_H):.3e} delta_a={da:.3e} m/s^2 "
            f"|delta_a|/r={q_proxy:.3e} s^-2"
        )

    # Cassini quadrupole central scale is O(1e-27 s^-2). This deliberately crude
    # proxy treats the entire cross acceleration as anisotropic, so it is conservative.
    cassini_scale = 5.2e-27
    if worst_q >= cassini_scale:
        raise SystemExit(
            f"FAIL: conservative quartic-action anisotropy proxy {worst_q:.3e} "
            f"exceeds comparison scale {cassini_scale:.3e} s^-2"
        )

    # Structural checks.
    for y in (1e-9, 1e-6, 1e-3, 1.0, 1e3, 1e6, 1e9):
        if not math.isclose(k_sym(y), k_sym(1/y), rel_tol=1e-12, abs_tol=1e-15):
            raise SystemExit("FAIL: symmetric kernel reciprocity broken")

    if not math.isclose(psi(0.0), 0.0, abs_tol=1e-15):
        raise SystemExit("FAIL: Psi(0) normalization")
    if abs(psi(1e8)-1.0) > 1e-7:
        raise SystemExit("FAIL: bounded Psi high-acceleration limit")

    print(f"worst conservative Q2-like proxy={worst_q:.3e} s^-2")
    print("stationary quartic reciprocal-action gate: PASS")
    print("CAVEAT: this is a reduced two-mode action diagnostic, not an exact Cassini ephemeris likelihood.")


if __name__ == "__main__":
    main()
