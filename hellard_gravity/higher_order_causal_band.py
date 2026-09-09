#!/usr/bin/env python3
"""Higher-order causal scale band for suppressing fast internal contamination.

Given the causal continuum memory
    dot m_lambda + lambda m_lambda = lambda a(t),
define D = partial / partial ln(lambda) and
    b_lambda = (D^2-D) m_lambda.
For a harmonic a=A exp(i omega t), x=lambda/omega,
    b/A = -2 i x^2/(x+i)^3
and the normalized log-scale power kernel is
    K2(x)=4 x^4/(1+x^2)^3.
The low-x tail is 4 x^4, giving R^-4 suppression of a high-frequency
internal mode evaluated at a slow center-of-mass scale.
"""
from __future__ import annotations

import math


def k2(x: float) -> float:
    return 4.0 * x**4 / (1.0 + x*x)**3


def integrate_log_kernel(decades: float = 12.0, n: int = 200000) -> float:
    lo = -decades * math.log(10.0)
    hi = decades * math.log(10.0)
    h = (hi-lo)/(n-1)
    total=0.0
    prev=k2(math.exp(lo))
    for i in range(1,n):
        u=lo+i*h
        cur=k2(math.exp(u))
        total += 0.5*(prev+cur)*h
        prev=cur
    return total


def contamination_fraction(a_internal: float, a_com: float, freq_ratio: float) -> float:
    """Power contamination proxy at the COM scale from a faster internal mode."""
    return (a_internal/a_com)**2 * k2(1.0/freq_ratio)


def main() -> None:
    integ=integrate_log_kernel(decades=8.0,n=50000)
    print(f"K2 log-normalization={integ:.12f}")
    if abs(integ-1.0)>1e-7:
        raise SystemExit("FAIL: K2 is not normalized")

    for R in (10.0,1e2,1e3,1e6):
        exact=k2(1.0/R)
        asym=4.0/R**4
        print(f"R={R:.1e}: exact leakage={exact:.6e}, 4/R^4={asym:.6e}")
        if R>=100 and abs(exact/asym-1.0)>1e-3:
            raise SystemExit("FAIL: R^-4 asymptotic not reached")

    # Earth: annual solar orbit compared with ~220 Myr Galactic orbit.
    a_internal=5.93e-3
    a_com=1.7e-10
    R=220e6
    frac=contamination_fraction(a_internal,a_com,R)
    print(f"Earth annual-orbit -> Galactic COM spectral-power contamination ~ {frac:.3e}")
    if frac>1e-12:
        raise SystemExit("FAIL: composite-body effacement benchmark too large")

    print("PASS: higher-order causal band gives normalized R^-4 fast-mode effacement")


if __name__ == '__main__':
    main()
