from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NonIdealSelfSteering:
    p0: float
    C0: float
    n_eff: float = 1.0
    L_over_L0: float = 1.0

    def pitch(self, C: float) -> float:
        if min(self.p0, self.C0, C, self.L_over_L0) <= 0:
            raise ValueError("all scale parameters must be positive")
        return self.p0 * (C / self.C0) ** (-self.n_eff) / self.L_over_L0


def required_effective_exponent(p0: float, p1: float, C0: float, C1: float, L1_over_L0: float = 1.0) -> float:
    """Solve the generalized pitch law for n_eff.

    p1/p0 = (C1/C0)^(-n_eff) / (L1/L0)
    n_eff=1 corresponds to ideal fixed-length cylindrical flux freezing.

    n_eff packages differential Hall/Nernst/resistive transport into one
    measurable effective exponent. It is a reduced model, not a closure for
    those transport terms.
    """
    if min(p0, p1, C0, C1, L1_over_L0) <= 0 or C1 == C0:
        raise ValueError("invalid endpoint values")
    return -math.log((p1 / p0) * L1_over_L0) / math.log(C1 / C0)


def self_steering_residual(p_natural: float, p_transport_optimum: float) -> float:
    return (p_natural - p_transport_optimum) / p_transport_optimum


if __name__ == "__main__":
    # HR52 representative endpoint match
    p0, C0 = 1.20, 25.5
    p1, C1 = 1.025, 30.0
    n = required_effective_exponent(p0, p1, C0, C1)
    model = NonIdealSelfSteering(p0=p0, C0=C0, n_eff=n)
    print({
        "required_n_eff": n,
        "predicted_end_pitch": model.pitch(C1),
        "ideal_reference_n_eff": 1.0,
    })
