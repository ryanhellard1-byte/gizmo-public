#!/usr/bin/env python3
"""Convex spectral-norm candidate for Hellard modified inertia.

Lead idea:
  Q_i = x_i^2 + beta * sum_j W(|omega_j/omega_i|) x_j^2,
  x_i = a_i / a_H,
  Phi'(Q) = mu(sqrt(Q)),  mu(z)=z/sqrt(1+z^2).

A closed primitive is
  Phi(Q) = sqrt(Q(1+Q)) - asinh(sqrt(Q)).

For Q>=0,
  Phi'(Q)  = sqrt(Q)/sqrt(1+Q) >= 0,
  Phi''(Q) = 1/[2 sqrt(Q) (1+Q)^(3/2)] > 0 (Q>0).

Hence Phi is increasing and convex. Since each Q_i is a nonnegative weighted
sum of squared amplitudes, Phi(Q_i) is convex in the amplitudes. Positive sums
of such terms remain convex. This gives a global convexity/stability guarantee
for the reduced discrete-mode kinetic functional, unlike the earlier ratio-gated
trial action.

This is still a nonrelativistic research candidate, not an established law.
"""
from __future__ import annotations

import math

A_H = 1.12e-10
BETA = 8.0
N_SLOW = 4


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def phi(Q: float) -> float:
    if Q < 0:
        raise ValueError("Q must be nonnegative")
    if Q == 0:
        return 0.0
    s = math.sqrt(Q)
    return math.sqrt(Q*(1.0+Q)) - math.asinh(s)


def phi_prime(Q: float) -> float:
    if Q <= 0:
        return 0.0
    return math.sqrt(Q) / math.sqrt(1.0 + Q)


def phi_second(Q: float) -> float:
    if Q <= 0:
        return math.inf
    return 1.0 / (2.0*math.sqrt(Q)*(1.0+Q)**1.5)


def slow_weight(y: float, n: int = N_SLOW) -> float:
    """Weights slower source modes strongly and faster modes weakly."""
    return 1.0 / (1.0 + y**n)


def Q_mode(x_i: float, omega_i: float, others, beta: float = BETA, n: int = N_SLOW) -> float:
    q = x_i*x_i
    for x_j, omega_j in others:
        q += beta * slow_weight(abs(omega_j/omega_i), n) * x_j*x_j
    return q


def isolated_inertia(x: float) -> float:
    """For an isolated mode, the action derivative gives mu(|x|)."""
    return phi_prime(x*x)


def self_test() -> None:
    for q in [1e-8, 1e-4, 1e-2, 1.0, 100.0]:
        assert phi_prime(q) >= 0.0
        assert phi_second(q) > 0.0
    for x in [0.01, 0.1, 1.0, 10.0]:
        assert abs(isolated_inertia(x)-mu(abs(x))) < 1e-12
    assert abs(slow_weight(1.0)-0.5) < 1e-15
    print("convex spectral-norm analytic checks: PASS")


if __name__ == "__main__":
    self_test()
