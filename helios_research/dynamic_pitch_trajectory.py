from __future__ import annotations

import math
from dataclasses import dataclass


OMEGA_ALPHA_PER_T = 4.822450739158287e7  # rad/s/T for a 3.5-MeV alpha gyrofrequency coefficient


@dataclass(frozen=True)
class BurnTrajectoryInput:
    duration_ns: float
    T0_keV: float
    Tpeak_keV: float
    rho0_gcc: float
    rhopeak_gcc: float
    B0_T: float
    Bpeak_T: float
    ln_lambda: float = 6.0
    hydro_factor: float = 1.0
    chi_e: float = 50.0
    w_alpha: float = 0.5


def slowing_time_ps(T_keV: float, rho_gcc: float, ln_lambda: float = 6.0, hydro_factor: float = 1.0) -> float:
    """Approximate alpha-electron slowing time proxy.

    Uses t_ps ~= 42*T_keV^(3/2)/(rho_gcc*lnLambda), multiplied by a hydrodynamic correction bracket.
    This is a surrogate, not a Fokker-Planck solver.
    """
    return hydro_factor * 42.0 * (T_keV ** 1.5) / (rho_gcc * ln_lambda)


def chi_alpha(B_T: float, t_ps: float) -> float:
    return OMEGA_ALPHA_PER_T * B_T * t_ps * 1e-12


def optimum_pitch(chi_alpha_value: float, chi_e: float = 50.0, w_alpha: float = 0.5) -> tuple[float, float]:
    ae = chi_e * chi_e / (1.0 + chi_e * chi_e)
    aa = chi_alpha_value * chi_alpha_value / (1.0 + chi_alpha_value * chi_alpha_value)
    c = w_alpha * aa + (1.0 - w_alpha) * ae
    s2 = 1.0 if c < 0.5 else 1.0 / (2.0 * c)
    theta = math.degrees(math.asin(math.sqrt(s2)))
    return theta, math.tan(math.radians(theta))


def trajectory(inp: BurnTrajectoryInput, steps: int = 101) -> list[dict[str, float]]:
    rows = []
    for i in range(steps):
        x = i / (steps - 1)
        T = inp.T0_keV + (inp.Tpeak_keV - inp.T0_keV) * (math.sin(math.pi * x / 2.0) ** 1.5)
        rho = inp.rho0_gcc + (inp.rhopeak_gcc - inp.rho0_gcc) * (math.sin(math.pi * x / 2.0) ** 1.1)
        B = inp.B0_T + (inp.Bpeak_T - inp.B0_T) * math.sin(math.pi * x / 2.0)
        tstop = slowing_time_ps(T, rho, inp.ln_lambda, inp.hydro_factor)
        chia = chi_alpha(B, tstop)
        theta, pitch = optimum_pitch(chia, inp.chi_e, inp.w_alpha)
        rows.append({
            "t_ns": x * inp.duration_ns,
            "T_keV": T,
            "rho_gcc": rho,
            "B_T": B,
            "tstop_ps": tstop,
            "chi_alpha": chia,
            "theta_deg": theta,
            "Btheta_over_Bz": pitch,
        })
    return rows


if __name__ == "__main__":
    case = BurnTrajectoryInput(
        duration_ns=3.0,
        T0_keV=8.0,
        Tpeak_keV=12.0,
        rho0_gcc=1.5,
        rhopeak_gcc=2.5,
        B0_T=300.0,
        Bpeak_T=800.0,
    )
    rows = trajectory(case)
    for idx in [0, 25, 50, 75, 100]:
        print(rows[idx])
