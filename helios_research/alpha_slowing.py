from __future__ import annotations

import math

Q_ALPHA = 2 * 1.602176634e-19
M_ALPHA = 6.6446573357e-27
OMEGA_ALPHA_PER_T = Q_ALPHA / M_ALPHA


def alpha_electron_drag_time_ps(T_keV: float, rho_gcc: float, coulomb_log: float) -> float:
    """Approximate characteristic alpha-electron slowing time.

    t_alphae [ps] ~= 42 T_e^(3/2)/(rho lnLambda).

    This is a reduced-order ICF scaling, not a full kinetic/Fokker-Planck solver.
    """
    if T_keV <= 0 or rho_gcc <= 0 or coulomb_log <= 0:
        raise ValueError("T_keV, rho_gcc, and coulomb_log must be positive")
    return 42.0 * T_keV ** 1.5 / (rho_gcc * coulomb_log)


def chi_alpha_from_drag_time(
    B_T: float,
    T_keV: float,
    rho_gcc: float,
    coulomb_log: float,
    hydro_factor: float = 1.0,
) -> float:
    if B_T < 0 or hydro_factor <= 0:
        raise ValueError("B_T must be nonnegative and hydro_factor positive")
    tau_s = alpha_electron_drag_time_ps(T_keV, rho_gcc, coulomb_log) * hydro_factor * 1e-12
    return OMEGA_ALPHA_PER_T * B_T * tau_s


def strong_electron_pitch(chi_alpha: float, w_alpha: float = 0.5) -> tuple[float, float]:
    """Return (theta_deg, Btheta/Bz) in the chi_e >> 1 limit."""
    if chi_alpha < 0 or not 0 <= w_alpha <= 1:
        raise ValueError("invalid chi_alpha or w_alpha")
    aa = chi_alpha * chi_alpha / (1.0 + chi_alpha * chi_alpha)
    b = 1.0 - w_alpha + w_alpha * aa
    if b < 0.5:
        theta = math.pi / 2
    else:
        theta = math.asin(math.sqrt(1.0 / (2.0 * b)))
    return math.degrees(theta), math.tan(theta)


if __name__ == "__main__":
    rho = 2.1
    T = 10.0
    lnL = 6.0
    for B in (300, 500, 800, 1200, 1500):
        chi = chi_alpha_from_drag_time(B, T, rho, lnL)
        theta, pitch = strong_electron_pitch(chi)
        print(B, chi, theta, pitch)
