#!/usr/bin/env python3
"""Compare the current Hellard circular branch against simple baselines on SPARC RAR.

This does NOT prove the nonlocal modified-inertia kernel. It isolates what the galaxy
RAR alone can and cannot tell us. The Hellard circular branch is intentionally the
same empirical-RAR-shaped one-parameter relation used in sparc_fit.py, so this script
makes that degeneracy explicit rather than hiding it.
"""
from __future__ import annotations

import math

from sparc_fit import load_sparc, hellard_circular_accel


def simple_mond_accel(gbar: float, a0: float) -> float:
    """Solve g * mu(g/a0)=gbar for mu(x)=x/sqrt(1+x^2)."""
    lo = max(gbar, 1e-30)
    hi = max(gbar + a0, math.sqrt(max(gbar * a0, 0.0)) * 20.0, 10.0 * a0)
    def f(g):
        x = g / a0
        mu = x / math.sqrt(1.0 + x*x)
        return g * mu - gbar
    while f(hi) < 0:
        hi *= 2.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def model_score(rows, predictor):
    chi2 = 0.0
    rss = 0.0
    for lgbar, e_lgbar, lgobs, e_lgobs in rows:
        gbar = 10.0 ** lgbar
        pred = predictor(gbar)
        lpred = math.log10(pred)
        dx = max(e_lgbar, 1e-4)
        pp = predictor(10.0 ** (lgbar + dx))
        pm = predictor(10.0 ** (lgbar - dx))
        slope = (math.log10(pp) - math.log10(pm)) / (2.0 * dx)
        sigma = math.sqrt(e_lgobs**2 + (slope * e_lgbar)**2)
        sigma = max(sigma, 1e-3)
        resid = lpred - lgobs
        chi2 += (resid / sigma) ** 2
        rss += resid * resid
    return chi2, math.sqrt(rss / len(rows))


def grid_fit(rows, family, lo=0.6e-10, hi=1.8e-10, n=481):
    best = None
    for i in range(n):
        a = lo + (hi-lo) * i/(n-1)
        predictor = lambda g, aa=a: family(g, aa)
        chi2, rms = model_score(rows, predictor)
        if best is None or chi2 < best[0]:
            best = (chi2, a, rms)
    return best


def criteria(chi2, k, n):
    return chi2 + 2*k, chi2 + k*math.log(n)


def main():
    rows = load_sparc()
    n = len(rows)

    newton_chi2, newton_rms = model_score(rows, lambda g: g)
    hell_chi2, hell_a, hell_rms = grid_fit(rows, hellard_circular_accel)
    mond_chi2, mond_a, mond_rms = grid_fit(rows, simple_mond_accel)

    models = [
        ("Newtonian", newton_chi2, 0, None, newton_rms),
        ("Hellard circular/RAR", hell_chi2, 1, hell_a, hell_rms),
        ("Simple MOND mu", mond_chi2, 1, mond_a, mond_rms),
    ]

    print(f"SPARC points: {n}")
    print("model comparison (same all-points likelihood approximation):")
    for name, chi2, k, scale, rms in models:
        aic, bic = criteria(chi2, k, n)
        scale_text = "-" if scale is None else f"{scale:.6e}"
        print(f"{name:22s} chi2={chi2:.2f} chi2/dof={chi2/max(n-k,1):.4f} "
              f"RMS={rms:.4f} dex AIC={aic:.2f} BIC={bic:.2f} scale={scale_text}")

    # Scientific guardrails.
    # The galaxy RAR should strongly reject the no-dark-matter Newtonian null under this
    # simplified one-relation comparison, while the Hellard circular branch must not be
    # advertised as distinct from the empirical RAR shape it was built to reproduce.
    if not hell_chi2 < newton_chi2:
        raise SystemExit("FAIL: Hellard circular branch does not improve on Newtonian null")

    print("INTERPRETATION: galaxy RAR validates the circular low-acceleration branch shape, "
          "not the nonlocal frequency kernel. theta0 and q remain identified by non-galaxy tests.")


if __name__ == "__main__":
    main()
