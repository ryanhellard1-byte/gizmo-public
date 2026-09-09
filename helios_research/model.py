from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PlasmaState:
    chi_e: float
    chi_alpha: float
    w_alpha: float

    def validate(self) -> None:
        if self.chi_e < 0 or self.chi_alpha < 0:
            raise ValueError("Hall parameters must be nonnegative")
        if not 0 <= self.w_alpha <= 1:
            raise ValueError("w_alpha must be in [0,1]")


def transport_factor(theta_rad: float, chi: float) -> float:
    """Classical anisotropic transport projection.

    F=1 is unsuppressed transport along the burn-front normal.
    This is a reduced-order proxy, not a kinetic transport solver.
    """
    if chi < 0:
        raise ValueError("chi must be nonnegative")
    c2 = math.cos(theta_rad) ** 2
    s2 = math.sin(theta_rad) ** 2
    return c2 + s2 / (1.0 + chi * chi)


def magnetization_factor(chi: float) -> float:
    if chi < 0:
        raise ValueError("chi must be nonnegative")
    return chi * chi / (1.0 + chi * chi)


def burn_transport_score(theta_rad: float, state: PlasmaState) -> float:
    """Balance hotspot electron insulation against reservoir transfer."""
    state.validate()
    fe = transport_factor(theta_rad, state.chi_e)
    fa = transport_factor(theta_rad, state.chi_alpha)
    insulation = 1.0 - fe
    transfer = state.w_alpha * fa + (1.0 - state.w_alpha) * fe
    return insulation * transfer


def hellard_optimum_angle_rad(state: PlasmaState) -> float:
    """Analytic optimum for the reduced burn-transport objective."""
    state.validate()
    ae = magnetization_factor(state.chi_e)
    aa = magnetization_factor(state.chi_alpha)
    b = state.w_alpha * aa + (1.0 - state.w_alpha) * ae
    if b <= 0:
        return math.pi / 2
    s2 = min(1.0, 1.0 / (2.0 * b))
    return math.asin(math.sqrt(s2))


def hellard_optimum_angle_deg(state: PlasmaState) -> float:
    return math.degrees(hellard_optimum_angle_rad(state))


def helical_pitch_ratio(state: PlasmaState) -> float:
    """Return B_theta/B_z for the angle convention used by this model."""
    return math.tan(hellard_optimum_angle_rad(state))


def liner_kinetic_energy_mj(mass_g: float, velocity_kms: float) -> float:
    if mass_g < 0 or velocity_kms < 0:
        raise ValueError("mass and velocity must be nonnegative")
    m = mass_g * 1e-3
    v = velocity_kms * 1e3
    return 0.5 * m * v * v / 1e6


def required_driver_energy_mj(useful_target_mj: float, coupling: float) -> float:
    if useful_target_mj < 0:
        raise ValueError("useful_target_mj must be nonnegative")
    if not 0 < coupling <= 1:
        raise ValueError("coupling must be in (0,1]")
    return useful_target_mj / coupling


def target_gain(fusion_yield_mj: float, driver_energy_mj: float) -> float:
    if fusion_yield_mj < 0 or driver_energy_mj <= 0:
        raise ValueError("invalid energies")
    return fusion_yield_mj / driver_energy_mj


def shots_per_module(days: float, aggregate_hz: float, modules: int) -> float:
    if days < 0 or aggregate_hz < 0 or modules <= 0:
        raise ValueError("invalid campaign inputs")
    return days * 86400.0 * aggregate_hz / modules
