"""Reduced-order Hellard fusion-propulsion closure criterion.

Research/systems-analysis code only. This is not a radiation-MHD, PIC,
neutron-transport, or hardware design solver.
"""

from __future__ import annotations


def recoverable_fraction(neutron_fraction: float, neutron_recovery: float) -> float:
    """Fraction of fusion energy remaining available to the nozzle."""
    return 1.0 - neutron_fraction * (1.0 - neutron_recovery)


def hellard_number(
    nozzle_efficiency: float,
    neutron_fraction: float,
    neutron_recovery: float,
    mission_min_efficiency: float,
) -> float:
    """Dimensionless propulsion-energy closure number H."""
    if mission_min_efficiency <= 0.0:
        raise ValueError("mission_min_efficiency must be positive")
    return (
        nozzle_efficiency
        * recoverable_fraction(neutron_fraction, neutron_recovery)
        / mission_min_efficiency
    )


def minimum_neutron_recovery(
    nozzle_efficiency: float,
    neutron_fraction: float,
    mission_min_efficiency: float,
) -> float:
    """Neutron-recovery fraction required for H=1."""
    if neutron_fraction <= 0.0:
        return 0.0 if nozzle_efficiency >= mission_min_efficiency else float("inf")
    return 1.0 - (1.0 - mission_min_efficiency / nozzle_efficiency) / neutron_fraction


def maximum_neutron_fraction(
    nozzle_efficiency: float,
    neutron_recovery: float,
    mission_min_efficiency: float,
) -> float:
    """Largest neutron-energy fraction allowed at H=1."""
    if neutron_recovery >= 1.0:
        return 1.0
    return (1.0 - mission_min_efficiency / nozzle_efficiency) / (1.0 - neutron_recovery)


if __name__ == "__main__":
    # HELIOS examples using archived 30-day mission thresholds.
    cases = [
        ("DT historical", 0.80, 0.8006, 0.30, 0.676),
        ("DT high capture", 0.80, 0.8006, 0.81, 0.676),
        ("Cat-DD R19", 0.88, 0.383, 0.30, 0.614),
    ]
    for name, noz, fn, cn, req in cases:
        h = hellard_number(noz, fn, cn, req)
        print(f"{name}: H={h:.4f} {'PASS' if h >= 1 else 'FAIL'}")
