"""Deterministic falsification tests for the current Hellard benchmark."""

from __future__ import annotations

import math

from hellard_kernel import (
    A_H,
    circular_speed_fourth_power,
    deep_mond_acceleration,
    external_mode_inertia_argument,
    fractional_inertial_anomaly,
    theta,
)

YEAR = 365.25 * 24 * 3600
P_GAL = 220e6 * YEAR
A_EXT = 1.7e-10
AU = 1.495978707e11

SYSTEMS = {
    "Mercury": (0.2408467 * YEAR, 3.95e-2, 0.387 * AU),
    "Earth": (1.0 * YEAR, 5.93e-3, 1.0 * AU),
    "Saturn": (29.457 * YEAR, 6.57e-5, 9.58 * AU),
    "Neptune": (164.8 * YEAR, 6.55e-6, 30.07 * AU),
}


def test_kernel_limits() -> None:
    assert abs(theta(1.0) - 1.0) < 1e-15
    assert abs(theta(0.0) - 7.0) < 1e-15
    assert theta(1e12) < 1e-10


def test_btfr_identity() -> None:
    G = 6.67430e-11
    m = 6.0e10 * 1.98847e30
    assert math.isclose(circular_speed_fourth_power(m), G * m * A_H, rel_tol=1e-15)


def test_deep_limit() -> None:
    g_n = 1e-13
    expected = math.sqrt(A_H * g_n)
    assert math.isclose(deep_mond_acceleration(g_n), expected, rel_tol=1e-15)


def test_solar_system_anomalies() -> None:
    # This is a benchmark mode-separable proxy, not an exact planetary ephemeris test.
    limits = {
        "Mercury": 1e-14,
        "Earth": 1e-14,
        "Saturn": 1e-10,
        "Neptune": 1e-8,
    }
    for name, (period, a_internal, _radius) in SYSTEMS.items():
        y = (2 * math.pi / P_GAL) / (2 * math.pi / period)
        argument = external_mode_inertia_argument(a_internal, A_EXT, y)
        anomaly = fractional_inertial_anomaly(argument)
        assert anomaly < limits[name], (name, anomaly, limits[name])


def report() -> None:
    print(f"Hellard benchmark a_H = {A_H:.4e} m/s^2")
    print("kernel theta(y) = 7/(1+6y)")
    print("\nSolar-system benchmark:")
    for name, (period, a_internal, radius) in SYSTEMS.items():
        y = period / P_GAL
        th = theta(y)
        argument = external_mode_inertia_argument(a_internal, A_EXT, y)
        anomaly = fractional_inertial_anomaly(argument)
        a_anom = anomaly * a_internal
        q_worst = a_anom / radius
        print(
            f"{name:8s} y={y:.3e} theta={th:.6f} "
            f"frac={anomaly:.3e} worst_Q~{q_worst:.3e} s^-2"
        )
    print("\nLeading mode-separable angular quadrupole: Q2_H = 0 by construction at first order.")
    print("This does not replace a full ephemeris/Cassini likelihood calculation.")


if __name__ == "__main__":
    test_kernel_limits()
    test_btfr_identity()
    test_deep_limit()
    test_solar_system_anomalies()
    report()
