from __future__ import annotations

import math


def pitch_after_compression(
    pitch_start: float,
    convergence_start: float,
    convergence_end: float,
    length_ratio: float = 1.0,
) -> float:
    """Ideal-MHD cylindrical flux-freezing estimate.

    For deformation F=diag(a,a,c), J=a^2 c:
      B_theta ~ 1/(a c)
      B_z     ~ 1/a^2
      pitch = B_theta/B_z ~ a/c

    With convergence C proportional to 1/R, a2/a1=C1/C2, so
      p2 = p1 * (C1/C2) / (L2/L1).

    This ignores resistive diffusion, Hall/Nernst transport, current evolution,
    and the fact that DSP drive fields are not simply frozen into the fuel.
    """
    if pitch_start < 0:
        raise ValueError("pitch_start must be nonnegative")
    if convergence_start <= 0 or convergence_end <= 0:
        raise ValueError("convergences must be positive")
    if length_ratio <= 0:
        raise ValueError("length_ratio must be positive")
    return pitch_start * (convergence_start / convergence_end) / length_ratio


def required_start_convergence(
    pitch_start: float,
    target_pitch_end: float,
    convergence_end: float,
    length_ratio: float = 1.0,
) -> float:
    if pitch_start <= 0 or target_pitch_end < 0 or convergence_end <= 0 or length_ratio <= 0:
        raise ValueError("invalid inputs")
    return target_pitch_end * convergence_end * length_ratio / pitch_start


def pitch_angle_deg(pitch: float) -> float:
    return math.degrees(math.atan(pitch))


if __name__ == "__main__":
    p0 = 1.2
    c0 = 25.625
    c1 = 30.0
    p1 = pitch_after_compression(p0, c0, c1)
    print({
        "pitch_start": p0,
        "C_start": c0,
        "C_end": c1,
        "pitch_end": p1,
        "theta_end_deg": pitch_angle_deg(p1),
    })
