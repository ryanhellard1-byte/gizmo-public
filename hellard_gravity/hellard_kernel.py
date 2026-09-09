"""Benchmark Hellard modified-inertia helpers.

This module implements only the current effective toy model.  It does not
claim a fundamental relativistic completion.
"""

from __future__ import annotations

import math

A_H = 1.19e-10  # m / s^2
THETA0 = 7.0
Q = 1.0


def mu(x: float) -> float:
    """Interpolation function mu(x)=x/sqrt(1+x^2)."""
    if x < 0:
        raise ValueError("x must be non-negative")
    return x / math.sqrt(1.0 + x * x)


def theta(y: float, theta0: float = THETA0, q: float = Q) -> float:
    """Universal benchmark frequency-ratio kernel.

    y = omega_external / omega_internal.
    theta(0)=theta0, theta(1)=1, theta(infinity)=0.
    """
    if y < 0:
        raise ValueError("frequency ratio y must be non-negative")
    if theta0 <= 1:
        raise ValueError("theta0 must be > 1")
    if q <= 0:
        raise ValueError("q must be > 0")
    return theta0 / (1.0 + (theta0 - 1.0) * y**q)


def deep_mond_acceleration(g_newton: float, a_h: float = A_H) -> float:
    """Deep isolated circular-orbit limit, sqrt(a_H g_N)."""
    if g_newton < 0:
        raise ValueError("g_newton must be non-negative")
    return math.sqrt(a_h * g_newton)


def circular_speed_fourth_power(mass_kg: float, G: float = 6.67430e-11, a_h: float = A_H) -> float:
    """BTFR prediction v^4 = G M a_H."""
    if mass_kg < 0:
        raise ValueError("mass_kg must be non-negative")
    return G * mass_kg * a_h


def external_mode_inertia_argument(
    a_internal: float,
    a_external: float,
    omega_external_over_internal: float,
    *,
    a_h: float = A_H,
    theta0: float = THETA0,
    q: float = Q,
) -> float:
    """Dimensionless benchmark inertia argument for a fast internal mode.

    The present mode-separable approximation treats amplitudes scalarly:
        A_eff = a_internal + theta(y) a_external.
    """
    if min(a_internal, a_external) < 0:
        raise ValueError("accelerations must be non-negative")
    return (
        a_internal
        + theta(omega_external_over_internal, theta0=theta0, q=q) * a_external
    ) / a_h


def fractional_inertial_anomaly(argument: float) -> float:
    """Fractional acceleration correction implied by a*mu = a_N."""
    m = mu(argument)
    if m == 0:
        return math.inf
    return 1.0 / m - 1.0
