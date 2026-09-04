#!/usr/bin/env python3
"""Phase 177: exact unequal-mass D3 jump identities and action-space theory gate.

This is a theorem/kinematics gate, not an N-body result.

For one elastic H-L collision at a common position with m_H/m_L = r,
momentum conservation and the exact center-of-mass scattering map imply

    Delta v_L = -r Delta v_H.

Therefore, event by event,

    Delta epsilon_L = -r Delta epsilon_H
    Delta ell_L     = -r Delta ell_H

for specific orbital energy epsilon=v^2/2+Phi (Phi fixed during the
instantaneous collision) and specific angular-momentum vector ell=x cross v.
Their second jump moments have an exact r^2 kinematic ratio before the
nonlinear action map and orbit averaging are applied.

The script samples the same Rutherford inverse-CDF used by sidmx_d3_impl.h and
checks these identities numerically, together with pair momentum/energy
conservation and the common-temperature hydrostatic segregation relation.
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
DEFAULT_EVENTS = 50000
DEFAULT_SEED = 177001

PAIR_TOL = 2.0e-12
JUMP_VECTOR_TOL = 2.0e-12
SPECIFIC_ENERGY_SCALED_TOL = 2.0e-12
SECOND_MOMENT_RATIO_TOL = 2.0e-12


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
    e1n = norm(e1)
    if e1n == 0.0:
        raise RuntimeError("degenerate basis")
    e1 = scale(1.0 / e1n, e1)
    e2 = cross(n, e1)
    return e1, e2


def rutherford_mu(g_kms: float, u: float) -> float:
    """Exact D3 HL inverse CDF from sidmx_d3_impl.h."""
    if u <= 0.0:
        u = 2.0 ** -53
    if u >= 1.0:
        u = 1.0 - 2.0 ** -53
    z = (g_kms / W_HL_KMS) ** 2
    mu = 1.0 - 2.0 * (1.0 - u) / (1.0 + u * z)
    return max(-1.0, min(1.0, mu))


def rutherford_cdf_from_x(mu: float, x: float) -> float:
    """Closed-form CDF corresponding to the D3 HL inverse sampler."""
    mu = max(-1.0, min(1.0, mu))
    z = x * x
    return (1.0 + mu) / (2.0 + z * (1.0 - mu))


def finite_jump_diagnostic():
    """Quantify why the exact HL process should not be assumed small-angle.

    For m_H/m_L=3,
        |Delta v_H|/g = sqrt(2-2 mu)/4.
    Therefore q_H > q0 iff mu < 1-8 q0^2.
    """
    rows = []
    for x in (0.0, 0.05, 0.10, 0.25, 1.0):
        mu_q025 = 1.0 - 8.0 * 0.25**2
        mu_q040 = 1.0 - 8.0 * 0.40**2
        rows.append({
            "g_over_w": x,
            "P_abs_Delta_vH_over_g_gt_0p25": rutherford_cdf_from_x(mu_q025, x),
            "P_abs_Delta_vH_over_g_gt_0p40": rutherford_cdf_from_x(mu_q040, x),
        })
    return {
        "low_velocity_isotropic_limit": {
            "mean_abs_Delta_vH_squared_over_g_squared": 1.0 / 8.0,
            "rms_abs_Delta_vH_over_g": math.sqrt(1.0 / 8.0),
            "mean_abs_Delta_vL_squared_over_g_squared": 9.0 / 8.0,
            "rms_abs_Delta_vL_over_g": 3.0 * math.sqrt(1.0 / 8.0),
        },
        "large_jump_probabilities": rows,
        "interpretation": (
            "At g/w << 1 the D3 HL angular law approaches isotropic scattering, "
            "so accepted collisions generate order-unity relative-velocity kicks. "
            "Retaining the finite-jump master operator is therefore safer than "
            "assuming a controlled small-angle Kramers-Moyal truncation."
        ),
    }


def scatter_hl(v_h, v_l, u_mu: float, u_phi: float):
    """Apply the same unequal-mass COM-frame delta map as GIZMO D3."""
    d_v = sub(v_h, v_l)
    g = norm(d_v)
    if g <= 0.0:
        return v_h, v_l, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

    n = scale(1.0 / g, d_v)
    e1, e2 = orthonormal_basis(n)
    mu = rutherford_mu(g, u_mu)
    sint = math.sqrt(max(0.0, 1.0 - mu * mu))
    phi = 2.0 * math.pi * u_phi
    nhat = tuple(
        mu * n[k] + sint * (math.cos(phi) * e1[k] + math.sin(phi) * e2[k])
        for k in range(3)
    )
    drel = sub(scale(g, nhat), d_v)

    mt = M_H + M_L
    delta_h = scale(M_L / mt, drel)
    delta_l = scale(-M_H / mt, drel)
    return add(v_h, delta_h), add(v_l, delta_l), delta_h, delta_l


def unit_vector(rng):
    z = 2.0 * rng.random() - 1.0
    phi = 2.0 * math.pi * rng.random()
    s = math.sqrt(max(0.0, 1.0 - z * z))
    return (s * math.cos(phi), s * math.sin(phi), z)


def random_position(rng):
    # Identity tests do not depend on a halo profile. A log radial span merely
    # prevents accidentally testing one special geometry.
    radius = 9.10 * math.exp(rng.uniform(math.log(0.03), math.log(3.0)))
    return scale(radius, unit_vector(rng))


def hydrostatic_segregation_gate():
    """Check the common-T species-ratio identity on a smooth toy potential.

    For isotropic ideal species at the same local temperature T(r),
        d ln(n_H/n_L)/dr = -(m_H-m_L) Phi'(r)/(k T).
    We set k=1 and use Phi(r)=-1/(1+r), T(r)=1+0.2r.
    """
    def dphi(r):
        return 1.0 / (1.0 + r) ** 2

    def temp(r):
        return 1.0 + 0.2 * r

    radii = [0.05 + 0.01 * i for i in range(396)]
    log_ratio = [0.0]
    for a, b in zip(radii, radii[1:]):
        mid = 0.5 * (a + b)
        rhs = -(M_H - M_L) * dphi(mid) / temp(mid)
        log_ratio.append(log_ratio[-1] + rhs * (b - a))

    max_fd_error = 0.0
    monotone = True
    for i in range(1, len(radii) - 1):
        fd = (log_ratio[i + 1] - log_ratio[i - 1]) / (radii[i + 1] - radii[i - 1])
        rhs = -(M_H - M_L) * dphi(radii[i]) / temp(radii[i])
        max_fd_error = max(max_fd_error, abs(fd - rhs))
        monotone &= log_ratio[i + 1] < log_ratio[i]

    passed = monotone and max_fd_error < 2.0e-4
    return {
        "passed": passed,
        "identity": "d ln(n_H/n_L)/dr = -(m_H-m_L) Phi'(r)/(k T(r))",
        "toy_potential": "Phi=-1/(1+r)",
        "toy_temperature": "kT=1+0.2r",
        "max_centered_fd_error": max_fd_error,
        "heavy_to_light_ratio_decreases_outward": monotone,
    }


def run(events: int, seed: int):
    rng = random.Random(seed)

    max_pair_p = 0.0
    max_pair_e = 0.0
    max_dv_identity = 0.0
    max_de_identity_scaled = 0.0
    max_dell_identity = 0.0

    sum_dv2_h = 0.0
    sum_dv2_l = 0.0
    sum_de2_h = 0.0
    sum_de2_l = 0.0
    sum_dell2_h = 0.0
    sum_dell2_l = 0.0

    for _ in range(events):
        v_h = tuple(rng.gauss(0.0, 70.0) for _ in range(3))
        v_l = tuple(rng.gauss(0.0, 70.0) for _ in range(3))
        x = random_position(rng)

        v_h2, v_l2, dv_h, dv_l = scatter_hl(v_h, v_l, rng.random(), rng.random())
        g2 = norm2(sub(v_h, v_l))

        p0 = add(scale(M_H, v_h), scale(M_L, v_l))
        p1 = add(scale(M_H, v_h2), scale(M_L, v_l2))
        pscale = M_H * norm(v_h) + M_L * norm(v_l) + 1.0e-300
        max_pair_p = max(max_pair_p, norm(sub(p1, p0)) / pscale)

        e0 = 0.5 * M_H * norm2(v_h) + 0.5 * M_L * norm2(v_l)
        e1 = 0.5 * M_H * norm2(v_h2) + 0.5 * M_L * norm2(v_l2)
        max_pair_e = max(max_pair_e, abs(e1 - e0) / (abs(e0) + 1.0e-300))

        dv_resid = add(dv_l, scale(MASS_RATIO, dv_h))
        dv_scale = norm(dv_l) + MASS_RATIO * norm(dv_h) + 1.0e-300
        max_dv_identity = max(max_dv_identity, norm(dv_resid) / dv_scale)

        de_h = 0.5 * (norm2(v_h2) - norm2(v_h))
        de_l = 0.5 * (norm2(v_l2) - norm2(v_l))
        max_de_identity_scaled = max(
            max_de_identity_scaled,
            abs(de_l + MASS_RATIO * de_h) / max(g2, 1.0),
        )

        dell_h = cross(x, dv_h)
        dell_l = cross(x, dv_l)
        dell_resid = add(dell_l, scale(MASS_RATIO, dell_h))
        dell_scale = norm(dell_l) + MASS_RATIO * norm(dell_h) + 1.0e-300
        max_dell_identity = max(max_dell_identity, norm(dell_resid) / dell_scale)

        sum_dv2_h += norm2(dv_h)
        sum_dv2_l += norm2(dv_l)
        sum_de2_h += de_h * de_h
        sum_de2_l += de_l * de_l
        sum_dell2_h += norm2(dell_h)
        sum_dell2_l += norm2(dell_l)

    ratios = {
        "velocity_jump_second_moment_L_over_H": sum_dv2_l / sum_dv2_h,
        "specific_energy_jump_second_moment_L_over_H": sum_de2_l / sum_de2_h,
        "specific_angular_momentum_vector_jump_second_moment_L_over_H": sum_dell2_l / sum_dell2_h,
    }
    expected_ratio2 = MASS_RATIO ** 2
    ratio_errors = {k: abs(v / expected_ratio2 - 1.0) for k, v in ratios.items()}

    hydro = hydrostatic_segregation_gate()
    finite_jump = finite_jump_diagnostic()

    gates = {
        "pair_momentum_conservation": max_pair_p < PAIR_TOL,
        "pair_kinetic_energy_conservation": max_pair_e < PAIR_TOL,
        "event_velocity_jump_identity": max_dv_identity < JUMP_VECTOR_TOL,
        "event_specific_energy_jump_identity": max_de_identity_scaled < SPECIFIC_ENERGY_SCALED_TOL,
        "event_specific_angular_momentum_vector_jump_identity": max_dell_identity < JUMP_VECTOR_TOL,
        "second_jump_moments_equal_mass_ratio_squared": max(ratio_errors.values()) < SECOND_MOMENT_RATIO_TOL,
        "common_temperature_hydrostatic_segregation_identity": hydro["passed"],
    }

    return {
        "phase": 177,
        "status": "PASS" if all(gates.values()) else "FAIL",
        "purpose": "exact D3 unequal-mass jump theorem and action-space theory gate; not an N-body result",
        "events": events,
        "seed": seed,
        "mass_ratio_H_over_L": MASS_RATIO,
        "rutherford_w_km_s": W_HL_KMS,
        "exact_event_identities": {
            "velocity": "Delta v_L = -(m_H/m_L) Delta v_H",
            "specific_orbital_energy_at_collision": "Delta epsilon_L = -(m_H/m_L) Delta epsilon_H",
            "specific_angular_momentum_vector": "Delta ell_L = -(m_H/m_L) Delta ell_H",
            "second_jump_moment_ratio": "(m_H/m_L)^2",
        },
        "max_errors": {
            "pair_momentum_relative": max_pair_p,
            "pair_kinetic_energy_relative": max_pair_e,
            "velocity_jump_identity_relative": max_dv_identity,
            "specific_energy_identity_scaled_by_max_g2_1": max_de_identity_scaled,
            "specific_angular_momentum_vector_identity_relative": max_dell_identity,
        },
        "second_jump_moments": {
            **ratios,
            "expected": expected_ratio2,
            "max_fractional_error": max(ratio_errors.values()),
        },
        "hydrostatic_common_temperature_gate": hydro,
        "finite_jump_diagnostic": finite_jump,
        "gates": gates,
        "theory_boundary": [
            "The exact jump identities are kinematic consequences of elastic unequal-mass scattering, not a new fundamental force.",
            "The factor-nine statement applies to event-level specific jump moments before the nonlinear J_r(E,L;Phi) map and orbit averaging.",
            "Common local temperature does not imply common spatial composition in gravity.",
            "The quantitative self-gravitating 80-Gyr M11 trajectory still requires the frozen live-GIZMO production and blind convergence campaign.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=int, default=DEFAULT_EVENTS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.events <= 0:
        raise SystemExit("events must be positive")

    result = run(args.events, args.seed)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
