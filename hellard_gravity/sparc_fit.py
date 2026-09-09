#!/usr/bin/env python3
"""Fit the Hellard modified-inertia circular-orbit branch to the real SPARC RAR table.

Data source (official SPARC site):
https://astroweb.cwru.edu/SPARC/RAR.mrt

The script downloads the published all-points RAR table, parses log10(gbar),
errors, log10(gobs), errors, and evaluates the one-parameter acceleration scale
a_H using a simple chi-square in log acceleration. This is an observational
sanity check, not a full galaxy-by-galaxy nuisance-parameter likelihood.
"""
from __future__ import annotations

import math
import urllib.request

SPARC_RAR_URL = "https://astroweb.cwru.edu/SPARC/RAR.mrt"
DEFAULT_AH = 1.19e-10


def hellard_circular_accel(gbar: float, a_h: float) -> float:
    """Circular-orbit prediction used by the current benchmark.

    Uses the empirical-RAR-shaped isolated circular branch:
        g = gbar / (1 - exp(-sqrt(gbar/a_h)))
    which has Newtonian and deep low-acceleration limits.
    """
    x = math.sqrt(gbar / a_h)
    denom = 1.0 - math.exp(-x)
    return gbar / denom


def load_sparc(url: str = SPARC_RAR_URL):
    with urllib.request.urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8")
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            lgbar, e_lgbar, lgobs, e_lgobs = map(float, parts)
        except ValueError:
            continue
        rows.append((lgbar, e_lgbar, lgobs, e_lgobs))
    if len(rows) < 2600:
        raise RuntimeError(f"Expected ~2693 SPARC RAR points, parsed only {len(rows)}")
    return rows


def score_a_h(rows, a_h: float):
    chi2 = 0.0
    residuals = []
    for lgbar, e_lgbar, lgobs, e_lgobs in rows:
        gbar = 10.0 ** lgbar
        pred = hellard_circular_accel(gbar, a_h)
        lpred = math.log10(pred)
        # First-order propagation of x-error through the model slope by finite difference.
        dx = max(e_lgbar, 1e-4)
        gp = hellard_circular_accel(10.0 ** (lgbar + dx), a_h)
        gm = hellard_circular_accel(10.0 ** (lgbar - dx), a_h)
        slope = (math.log10(gp) - math.log10(gm)) / (2.0 * dx)
        sigma = math.sqrt(e_lgobs**2 + (slope * e_lgbar)**2)
        sigma = max(sigma, 1e-3)
        resid = lpred - lgobs
        residuals.append(resid)
        chi2 += (resid / sigma) ** 2
    n = len(rows)
    rms = math.sqrt(sum(r*r for r in residuals) / n)
    return chi2, chi2 / max(n - 1, 1), rms


def grid_fit(rows, lo=0.7e-10, hi=1.7e-10, n=401):
    best = None
    for i in range(n):
        a_h = lo + (hi - lo) * i / (n - 1)
        chi2, red, rms = score_a_h(rows, a_h)
        item = (chi2, a_h, red, rms)
        if best is None or item[0] < best[0]:
            best = item
    return best


def main():
    rows = load_sparc()
    chi2, a_h, red, rms = grid_fit(rows)
    base_chi2, base_red, base_rms = score_a_h(rows, DEFAULT_AH)
    print(f"SPARC points: {len(rows)}")
    print(f"best a_H = {a_h:.6e} m/s^2")
    print(f"best chi2/dof = {red:.4f}")
    print(f"best RMS(log10 g) = {rms:.4f} dex")
    print(f"benchmark a_H={DEFAULT_AH:.6e}: chi2/dof={base_red:.4f}, RMS={base_rms:.4f} dex")


if __name__ == "__main__":
    main()
