#!/usr/bin/env python3
"""Two-mode Helmholtz/reciprocity diagnostic for the benchmark effective EOM.

For equations E_i[x]=0 to arise directly as Euler-Lagrange equations, the
linearized functional derivative (second variation) must obey an appropriate
reciprocity/symmetry condition. This toy discrete-frequency test checks the
cross-mode Jacobian for the benchmark scalar-amplitude EOM.

A failure here does not disprove modified inertia. It means the *simple
multiplicative effective EOM as written* cannot be assumed to come from an
action without additional cross-frequency reaction terms.
"""
from __future__ import annotations

import math

A_H = 1.19e-10
THETA0 = 7.0
Q = 1.0


def theta(y: float) -> float:
    return THETA0 / (1.0 + (THETA0 - 1.0) * y**Q)


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def eom(x1: float, x2: float, w1: float, w2: float):
    # Scalar positive-amplitude two-mode proxy. a_i = w_i^2 x_i in magnitude.
    a1 = w1*w1*x1
    a2 = w2*w2*x2
    A1 = a1 + theta(w2/w1)*a2
    A2 = a2 + theta(w1/w2)*a1
    E1 = a1 * mu(A1/A_H)
    E2 = a2 * mu(A2/A_H)
    return E1, E2


def jacobian(x1: float, x2: float, w1: float, w2: float):
    h1 = max(abs(x1)*1e-6, 1e-16)
    h2 = max(abs(x2)*1e-6, 1e-16)

    ep = eom(x1, x2+h2, w1, w2)
    em = eom(x1, x2-h2, w1, w2)
    dE1_dx2 = (ep[0]-em[0])/(2*h2)

    ep = eom(x1+h1, x2, w1, w2)
    em = eom(x1-h1, x2, w1, w2)
    dE2_dx1 = (ep[1]-em[1])/(2*h1)
    return dE1_dx2, dE2_dx1


def main():
    # Choose accelerations around a_H with a large frequency hierarchy.
    w1 = 1.0
    w2 = 1e-3
    a1 = 0.7*A_H
    a2 = 1.3*A_H
    x1 = a1/(w1*w1)
    x2 = a2/(w2*w2)

    j12, j21 = jacobian(x1, x2, w1, w2)
    scale = max(abs(j12), abs(j21), 1e-300)
    asym = abs(j12-j21)/scale

    print(f"theta(w2/w1)={theta(w2/w1):.6g}")
    print(f"theta(w1/w2)={theta(w1/w2):.6g}")
    print(f"dE1/dx2={j12:.6e}")
    print(f"dE2/dx1={j21:.6e}")
    print(f"relative reciprocity mismatch={asym:.6e}")

    if asym < 1e-3:
        print("RESULT: this toy point is accidentally near-reciprocal; broaden the test.")
    else:
        print("RESULT: benchmark effective EOM fails the two-mode reciprocity diagnostic.")
        print("ACTION CONSEQUENCE: an action completion must add cross-frequency terms or change the kernel construction.")


if __name__ == "__main__":
    main()
