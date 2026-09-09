"""Adversarial numerical checks for the Hellard hybrid EM resource theorem.

These tests do NOT prove the theorem.  They independently stress the closed form
against direct constrained optimization, random non-normal contractions, the
piecewise phase-law simplification, and the broadband convex program.
"""

import math
import numpy as np
from scipy.optimize import minimize

SEED = 20260909


def EH(N, r, L, B):
    s = L / 2.0
    if r == 0:
        return s * s / N
    if r == N:
        return max(s / math.sqrt(N) - B, 0.0) ** 2

    q = N - r
    mmin = max(r * s / N, s - 2 * q, 0.0)
    mmax = min(s, 2 * r)
    if s <= B * math.sqrt(r):
        mhat = s
    else:
        mhat = (r * s + q * B * math.sqrt(r)) / N
    mstar = min(max(mhat, mmin), mmax)
    return max(mstar / math.sqrt(r) - B, 0.0) ** 2 + (s - mstar) ** 2 / q


def EH_piecewise(N, r, L, B):
    """Equivalent phase-law form for 0 <= L <= 4N."""
    s = L / 2.0
    if r == 0:
        return s * s / N
    if r == N:
        return max(s - B * math.sqrt(N), 0.0) ** 2 / N

    q = N - r
    z = B * math.sqrt(r)

    if s <= 2 * r:
        return max(s - z, 0.0) ** 2 / N

    zc = r * (2 * N - s) / q
    if z <= zc:
        return (s - z) ** 2 / N
    if z < 2 * r:
        return (2 * r - z) ** 2 / r + (s - 2 * r) ** 2 / q
    return (s - 2 * r) ** 2 / q


def direct_singular_value_optimum(N, r, L, B):
    """Numerically minimize over the full ordered singular-value vector."""
    s = L / 2.0
    x0 = np.full(N, s / N)

    def objective(tau):
        if r == 0:
            return float(np.dot(tau, tau))
        if r == N:
            return max(np.linalg.norm(tau) - B, 0.0) ** 2
        return max(np.linalg.norm(tau[:r]) - B, 0.0) ** 2 + float(
            np.dot(tau[r:], tau[r:])
        )

    constraints = [{"type": "ineq", "fun": lambda t: np.sum(t) - s}]
    for i in range(N - 1):
        constraints.append(
            {"type": "ineq", "fun": lambda t, i=i: t[i] - t[i + 1]}
        )

    out = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[(0.0, 2.0)] * N,
        constraints=constraints,
        options={"maxiter": 2000, "ftol": 1e-12, "disp": False},
    )
    return float(out.fun), bool(out.success)


def random_unitary(rng, n):
    z = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    q, rr = np.linalg.qr(z)
    d = np.diag(rr)
    phase = np.where(np.abs(d) > 0, d / np.abs(d), 1.0)
    return q * phase.conj()


def fixed_D_optimum(tau, r, B):
    tau = np.sort(np.asarray(tau, dtype=float))[::-1]
    if r == 0:
        return float(np.dot(tau, tau))
    top = np.linalg.norm(tau[:r])
    return max(top - B, 0.0) ** 2 + float(np.dot(tau[r:], tau[r:]))


def broadband_direct(N, r, w, Lomega, Pomega):
    """Direct convex optimization over per-frequency (s,m,b) variables."""
    M = len(w)
    W = float(np.sum(w))
    q = N - r
    s_avg = Lomega / (2 * W)
    s0 = np.full(M, s_avg)
    m0 = np.minimum(
        np.maximum(r * s0 / N, s0 - 2 * q), np.minimum(s0, 2 * r)
    )
    b0 = np.full(M, math.sqrt(Pomega / W) if Pomega > 0 else 0.0)
    x0 = np.r_[s0, m0, b0]

    def objective(x):
        s = x[:M]
        m = x[M : 2 * M]
        b = x[2 * M :]
        return float(
            np.sum(
                w
                * (
                    np.maximum(m / math.sqrt(r) - b, 0.0) ** 2
                    + (s - m) ** 2 / q
                )
            )
        )

    constraints = [
        {"type": "ineq", "fun": lambda x: np.sum(w * x[:M]) - Lomega / 2},
        {"type": "ineq", "fun": lambda x: Pomega - np.sum(w * x[2 * M :] ** 2)},
    ]
    for k in range(M):
        constraints.extend(
            [
                {"type": "ineq", "fun": lambda x, k=k: x[M + k] - r * x[k] / N},
                {"type": "ineq", "fun": lambda x, k=k: x[M + k] - (x[k] - 2 * q)},
                {"type": "ineq", "fun": lambda x, k=k: x[k] - x[M + k]},
                {"type": "ineq", "fun": lambda x, k=k: 2 * r - x[M + k]},
            ]
        )

    bounds = [(0.0, 2 * N)] * M + [(0.0, 2 * r)] * M + [(0.0, None)] * M
    out = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 3000, "ftol": 1e-11, "disp": False},
    )
    return float(out.fun), bool(out.success)


def main():
    rng = np.random.default_rng(SEED)

    # 1. Closed-form clip formula versus simplified piecewise phase law.
    worst_piecewise = 0.0
    for _ in range(100_000):
        N = int(rng.integers(1, 30))
        r = int(rng.integers(0, N + 1))
        L = float(rng.uniform(0.0, 4.0 * N))
        B = float(rng.uniform(0.0, 20.0))
        worst_piecewise = max(worst_piecewise, abs(EH(N, r, L, B) - EH_piecewise(N, r, L, B)))

    # 2. Direct nonlinear optimization over all singular values.
    worst_direct = 0.0
    direct_mismatches = 0
    direct_solver_failures = 0
    for _ in range(1000):
        N = int(rng.integers(2, 13))
        r = int(rng.integers(1, N))
        L = float(rng.uniform(1e-3, 4.0 * N))
        B = float(rng.uniform(0.0, 8.0))
        numeric, success = direct_singular_value_optimum(N, r, L, B)
        err = abs(numeric - EH(N, r, L, B))
        worst_direct = max(worst_direct, err)
        if not success:
            direct_solver_failures += 1
        elif err > 1e-7:
            direct_mismatches += 1

    # 3. Full random complex contractions Q, including non-normal Q.
    contraction_violations = 0
    smallest_nontrivial_margin = math.inf
    for _ in range(30_000):
        N = int(rng.integers(1, 9))
        U = random_unitary(rng, N)
        V = random_unitary(rng, N)
        qsv = rng.uniform(0.0, 1.0, N)
        Q = U @ np.diag(qsv) @ V.conj().T
        D = np.eye(N) - Q
        tau = np.linalg.svd(D, compute_uv=False)
        L = float(2.0 * np.real(np.trace(D)))
        L = min(max(L, 0.0), 4.0 * N)  # numerical guard only
        r = int(rng.integers(0, N + 1))
        B = float(rng.uniform(0.0, 4.0))
        fixed = fixed_D_optimum(tau, r, B)
        envelope = EH(N, r, L, B)
        margin = fixed - envelope
        if margin < -1e-9:
            contraction_violations += 1
        if envelope > 1e-8:
            smallest_nontrivial_margin = min(smallest_nontrivial_margin, margin)

    # 4. Joint-convexity Jensen attack in (L,B).
    convexity_violations = 0
    worst_jensen_excess = 0.0
    for _ in range(300_000):
        N = int(rng.integers(1, 15))
        r = int(rng.integers(0, N + 1))
        L1, L2 = rng.uniform(0.0, 4.0 * N, 2)
        B1, B2 = rng.uniform(0.0, 10.0, 2)
        t = float(rng.uniform())
        lhs = EH(N, r, t * L1 + (1 - t) * L2, t * B1 + (1 - t) * B2)
        rhs = t * EH(N, r, L1, B1) + (1 - t) * EH(N, r, L2, B2)
        excess = lhs - rhs
        worst_jensen_excess = max(worst_jensen_excess, excess)
        if excess > 1e-9:
            convexity_violations += 1

    # 5. Direct broadband convex program versus broadband closed form.
    worst_broadband = 0.0
    broadband_mismatches = 0
    broadband_failures = 0
    for _ in range(500):
        N = int(rng.integers(2, 10))
        r = int(rng.integers(1, N))
        M = int(rng.integers(2, 6))
        w = rng.uniform(0.1, 2.0, M)
        W = float(np.sum(w))
        Lavg = float(rng.uniform(0.01, 4.0 * N))
        Lomega = W * Lavg
        Brms = float(rng.uniform(0.0, 6.0))
        Pomega = W * Brms * Brms
        numeric, success = broadband_direct(N, r, w, Lomega, Pomega)
        closed = W * EH(N, r, Lavg, Brms)
        err = abs(numeric - closed)
        worst_broadband = max(worst_broadband, err)
        if not success:
            broadband_failures += 1
        elif err > 1e-6:
            broadband_mismatches += 1

    print("HELLARD ADVERSARIAL AUDIT")
    print(f"piecewise equivalence: worst abs error = {worst_piecewise:.6e}")
    print(f"direct singular optimization: mismatches >1e-7 = {direct_mismatches}/1000")
    print(f"direct singular optimization: solver failures = {direct_solver_failures}/1000")
    print(f"direct singular optimization: worst abs error = {worst_direct:.6e}")
    print(f"random complex contractions: violations = {contraction_violations}/30000")
    print(f"random complex contractions: smallest nontrivial fixed-minus-envelope margin = {smallest_nontrivial_margin:.6e}")
    print(f"joint-convexity Jensen tests: violations = {convexity_violations}/300000")
    print(f"joint-convexity Jensen tests: worst positive excess = {worst_jensen_excess:.6e}")
    print(f"broadband direct optimization: mismatches >1e-6 = {broadband_mismatches}/500")
    print(f"broadband direct optimization: solver failures = {broadband_failures}/500")
    print(f"broadband direct optimization: worst abs error = {worst_broadband:.6e}")


if __name__ == "__main__":
    main()
