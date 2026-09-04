#!/usr/bin/env python3
"""Phase 178: exact finite-jump D3 action increments versus FP truncation.

This is a controlled theory diagnostic in an analytic spherical harmonic
potential, not an M11 halo result.  The harmonic potential is chosen because
its radial action is exact:

    E = Omega (2 J_r + L),  so  J_r = (E/Omega - L)/2.

We draw local common-temperature H/L velocity pairs, weight encounters by the
D3 HL collision rate g*sigma_HL(g), scatter with the exact D3 Rutherford
inverse CDF, and measure the exact one-collision jump moments in (J_r, L).

For a local compound-Poisson jump process with collision exposure Lambda,
the Kramers-Moyal/Fokker-Planck truncation retains only

    kappa_1 = Lambda <Delta J>
    kappa_2 = Lambda <(Delta J)^2>

and discards kappa_n = Lambda <(Delta J)^n>, n>=3.  We therefore report the
standardized third and fourth cumulants that a Gaussian FP surrogate erases.
No halo-scale acceptance gate is inferred from this toy potential.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

M_H = 3.0
M_L = 1.0
MASS_RATIO = M_H / M_L
W_HL_KMS = 2200.0
SIGMA0_HL = 1.125

OMEGA = 80.0  # km/s/kpc; analytic toy potential only
R_COLLISION = 1.0  # kpc
SIGMA_H = 60.0  # km/s
SIGMA_L = SIGMA_H * math.sqrt(MASS_RATIO)  # common kinetic temperature

DEFAULT_SAMPLES = 120000
DEFAULT_SEED = 178001
EXPOSURES = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)

PAIR_TOL = 3.0e-12
ACTION_TOL = 2.0e-12


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm2(a):
    return dot(a, a)


def norm(a):
    return math.sqrt(norm2(a))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scale(c, a):
    return tuple(c * x for x in a)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def orthonormal_basis(n):
    a = (1.0, 0.0, 0.0) if abs(n[0]) < 0.8 else (0.0, 1.0, 0.0)
    e1 = cross(n, a)
    q = norm(e1)
    if q <= 0.0:
        raise RuntimeError("degenerate basis")
    e1 = scale(1.0 / q, e1)
    e2 = cross(n, e1)
    return e1, e2


def rutherford_mu(g_kms: float, u: float) -> float:
    if u <= 0.0:
        u = 2.0 ** -53
    if u >= 1.0:
        u = 1.0 - 2.0 ** -53
    z = (g_kms / W_HL_KMS) ** 2
    mu = 1.0 - 2.0 * (1.0 - u) / (1.0 + u * z)
    return max(-1.0, min(1.0, mu))


def sigma_hl(g_kms: float) -> float:
    x = g_kms / W_HL_KMS
    return SIGMA0_HL / (1.0 + x * x)


def scatter(v_h, v_l, u_mu, u_phi):
    d_v = sub(v_h, v_l)
    g = norm(d_v)
    if g <= 0.0:
        return v_h, v_l
    n = scale(1.0 / g, d_v)
    e1, e2 = orthonormal_basis(n)
    mu = rutherford_mu(g, u_mu)
    st = math.sqrt(max(0.0, 1.0 - mu * mu))
    phi = 2.0 * math.pi * u_phi
    nhat = tuple(
        mu * n[k] + st * (math.cos(phi) * e1[k] + math.sin(phi) * e2[k])
        for k in range(3)
    )
    drel = sub(scale(g, nhat), d_v)
    mt = M_H + M_L
    dv_h = scale(M_L / mt, drel)
    dv_l = scale(-M_H / mt, drel)
    return add(v_h, dv_h), add(v_l, dv_l)


def actions(x, v):
    r2 = norm2(x)
    phi = 0.5 * OMEGA * OMEGA * r2
    e = 0.5 * norm2(v) + phi
    l = norm(cross(x, v))
    jr = 0.5 * (e / OMEGA - l)
    # Roundoff can make a circular orbit microscopically negative.
    if jr < 0.0 and jr > -ACTION_TOL:
        jr = 0.0
    return jr, l, e


class WeightedMoments:
    def __init__(self):
        self.w = 0.0
        self.w2 = 0.0
        self.raw = [0.0, 0.0, 0.0, 0.0]
        self.large_010 = 0.0
        self.large_025 = 0.0
        self.scale_w = 0.0

    def add(self, y, weight, action_scale):
        self.w += weight
        self.w2 += weight * weight
        p = y
        for i in range(4):
            self.raw[i] += weight * p
            p *= y
        q = abs(y) / max(action_scale, 1.0e-300)
        if q > 0.10:
            self.large_010 += weight
        if q > 0.25:
            self.large_025 += weight
        self.scale_w += weight * action_scale

    def finish(self):
        if self.w <= 0.0:
            raise RuntimeError("zero total encounter weight")
        m = [x / self.w for x in self.raw]
        neff = self.w * self.w / max(self.w2, 1.0e-300)
        m1, m2, m3, m4 = m
        if m2 <= 0.0:
            raise RuntimeError("non-positive second raw jump moment")

        exposure_rows = []
        for lam in EXPOSURES:
            skew = m3 / (math.sqrt(lam) * m2 ** 1.5)
            excess = m4 / (lam * m2 * m2)
            exposure_rows.append({
                "Lambda": lam,
                "exact_compound_poisson_standardized_kappa3": skew,
                "exact_compound_poisson_standardized_kappa4": excess,
                "matched_FP_standardized_kappa3": 0.0,
                "matched_FP_standardized_kappa4": 0.0,
            })

        # A transparent diagnostic scale, not a preregistered physics gate.
        target = 0.10
        lambda_skew = (abs(m3) / (target * m2 ** 1.5)) ** 2
        lambda_kurt = m4 / (target * m2 * m2)

        return {
            "encounter_weight_sum": self.w,
            "effective_weighted_samples": neff,
            "raw_jump_moments": {
                "E_dJ": m1,
                "E_dJ2": m2,
                "E_dJ3": m3,
                "E_dJ4": m4,
            },
            "weighted_mean_pre_total_action_I": self.scale_w / self.w,
            "weighted_probability_abs_dJr_over_I_gt_0p10": self.large_010 / self.w,
            "weighted_probability_abs_dJr_over_I_gt_0p25": self.large_025 / self.w,
            "compound_poisson_vs_matched_FP": exposure_rows,
            "illustrative_exposure_for_abs_kappa3_and_kappa4_below_0p10": max(lambda_skew, lambda_kurt),
            "illustrative_threshold_note": "0.10 is a descriptive Gaussianity yardstick, not a halo acceptance gate",
        }


def run(samples: int, seed: int):
    rng = random.Random(seed)
    x = (R_COLLISION, 0.0, 0.0)
    mh = WeightedMoments()
    ml = WeightedMoments()

    max_dp = 0.0
    max_de = 0.0
    min_jr = float("inf")
    max_common_temperature_rel_error = 0.0

    # Verify the chosen local Gaussian dispersions represent common temperature.
    t_h = M_H * SIGMA_H * SIGMA_H
    t_l = M_L * SIGMA_L * SIGMA_L
    max_common_temperature_rel_error = abs(t_h / t_l - 1.0)

    for _ in range(samples):
        vh = tuple(rng.gauss(0.0, SIGMA_H) for _ in range(3))
        vl = tuple(rng.gauss(0.0, SIGMA_L) for _ in range(3))
        g = norm(sub(vh, vl))
        if g <= 0.0:
            continue
        weight = g * sigma_hl(g)

        jh0, lh0, eh0 = actions(x, vh)
        jl0, ll0, el0 = actions(x, vl)
        vh1, vl1 = scatter(vh, vl, rng.random(), rng.random())
        jh1, lh1, eh1 = actions(x, vh1)
        jl1, ll1, el1 = actions(x, vl1)

        min_jr = min(min_jr, jh0, jl0, jh1, jl1)

        p0 = add(scale(M_H, vh), scale(M_L, vl))
        p1 = add(scale(M_H, vh1), scale(M_L, vl1))
        pscale = M_H * norm(vh) + M_L * norm(vl) + 1.0e-300
        max_dp = max(max_dp, norm(sub(p1, p0)) / pscale)

        # Same collision position, so pair potential energy is unchanged.
        e_pair0 = M_H * eh0 + M_L * el0
        e_pair1 = M_H * eh1 + M_L * el1
        max_de = max(max_de, abs(e_pair1 - e_pair0) / max(abs(e_pair0), 1.0))

        # I=E/Omega=2 Jr+L is the positive total harmonic action scale.
        ih0 = eh0 / OMEGA
        il0 = el0 / OMEGA
        mh.add(jh1 - jh0, weight, ih0)
        ml.add(jl1 - jl0, weight, il0)

    h = mh.finish()
    l = ml.finish()

    gates = {
        "common_temperature_input": max_common_temperature_rel_error < 1.0e-14,
        "pair_momentum_conservation": max_dp < PAIR_TOL,
        "pair_total_energy_conservation": max_de < PAIR_TOL,
        "harmonic_actions_nonnegative": min_jr >= -ACTION_TOL,
        "weighted_sample_size_H_gt_10000": h["effective_weighted_samples"] > 10000.0,
        "weighted_sample_size_L_gt_10000": l["effective_weighted_samples"] > 10000.0,
    }

    return {
        "phase": 178,
        "status": "PASS" if all(gates.values()) else "FAIL",
        "purpose": "finite-jump versus second-order FP diagnostic in an analytic action-space toy potential; not an M11 result",
        "samples": samples,
        "seed": seed,
        "toy_model": {
            "potential": "Phi(r)=0.5*Omega^2*r^2",
            "Omega_km_s_per_kpc": OMEGA,
            "collision_radius_kpc": R_COLLISION,
            "exact_action_relation": "J_r=(E/Omega-L)/2",
            "sigma_H_km_s": SIGMA_H,
            "sigma_L_km_s": SIGMA_L,
            "mH_over_mL": MASS_RATIO,
            "encounter_weight": "g * sigma_HL(g)",
            "HL_sigma": "1.125/(1+(g/2200 km/s)^2) cm^2/g on the heavy-mass basis",
        },
        "mechanical_errors": {
            "common_temperature_relative": max_common_temperature_rel_error,
            "max_pair_momentum_relative": max_dp,
            "max_pair_total_energy_relative": max_de,
            "minimum_radial_action": min_jr,
        },
        "H": h,
        "L": l,
        "gates": gates,
        "interpretation": [
            "The exact local collision generator is a finite-jump master operator.",
            "A matched second-order FP generator reproduces only the first two jump cumulants by construction.",
            "Nonzero standardized third/fourth compound-Poisson cumulants quantify information discarded by that truncation at finite collision exposure.",
            "Their decay with increasing Lambda is the expected central-limit trend and does not imply FP is always invalid.",
            "This analytic-potential diagnostic isolates collision/action-jump structure; self-gravitating M11 accuracy remains a separate production test.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.samples < 1000:
        raise SystemExit("samples must be >=1000")
    result = run(args.samples, args.seed)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
