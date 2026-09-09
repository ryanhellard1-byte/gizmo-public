from __future__ import annotations

import math
from dataclasses import dataclass

ALPHA_CHARGE_C = 2.0 * 1.602176634e-19
ALPHA_MASS_KG = 6.6446573357e-27
ALPHA_ENERGY_J = 3.5e6 * 1.602176634e-19
ALPHA_SPEED_M_S = math.sqrt(2.0 * ALPHA_ENERGY_J / ALPHA_MASS_KG)
ALPHA_OMEGA_PER_T = ALPHA_CHARGE_C / ALPHA_MASS_KG
DEFAULT_STOPPING_RHOR_KG_M2 = 0.077 * 10.0  # 0.077 g/cm^2


@dataclass(frozen=True)
class TargetState:
    convergence: float
    rhoR_g_cm2: float
    B_T: float
    initial_radius_m: float = 0.01


def compressed_radius_m(state: TargetState) -> float:
    return state.initial_radius_m / state.convergence


def density_kg_m3(state: TargetState) -> float:
    rhoR_si = state.rhoR_g_cm2 * 10.0
    return rhoR_si / compressed_radius_m(state)


def alpha_stopping_time_s(
    state: TargetState,
    stopping_rhoR_kg_m2: float = DEFAULT_STOPPING_RHOR_KG_M2,
) -> float:
    rho = density_kg_m3(state)
    stopping_length_m = stopping_rhoR_kg_m2 / rho
    return stopping_length_m / ALPHA_SPEED_M_S


def alpha_hall_proxy(
    state: TargetState,
    stopping_rhoR_kg_m2: float = DEFAULT_STOPPING_RHOR_KG_M2,
) -> float:
    return ALPHA_OMEGA_PER_T * state.B_T * alpha_stopping_time_s(
        state, stopping_rhoR_kg_m2
    )


def strong_electron_optimum_angle_deg(chi_alpha: float, w_alpha: float = 0.5) -> float:
    if chi_alpha < 0:
        raise ValueError("chi_alpha must be nonnegative")
    if not 0.0 <= w_alpha <= 1.0:
        raise ValueError("w_alpha must be in [0,1]")
    a_alpha = chi_alpha**2 / (1.0 + chi_alpha**2)
    b = 1.0 - w_alpha + w_alpha * a_alpha
    s2 = min(1.0, 1.0 / (2.0 * b))
    return math.degrees(math.asin(math.sqrt(s2)))


def predicted_pitch_ratio(state: TargetState, w_alpha: float = 0.5) -> float:
    chi = alpha_hall_proxy(state)
    theta = math.radians(strong_electron_optimum_angle_deg(chi, w_alpha))
    return math.tan(theta)


if __name__ == "__main__":
    examples = [
        TargetState(20, 0.07, 500),
        TargetState(30, 0.07, 800),
        TargetState(30, 0.05, 500),
    ]
    for state in examples:
        chi = alpha_hall_proxy(state)
        theta = strong_electron_optimum_angle_deg(chi)
        print(
            state,
            f"rho={density_kg_m3(state):.1f} kg/m^3",
            f"tau_stop={alpha_stopping_time_s(state)*1e12:.2f} ps",
            f"chi_alpha_proxy={chi:.3f}",
            f"theta*={theta:.2f} deg",
            f"Btheta/Bz={math.tan(math.radians(theta)):.3f}",
        )
