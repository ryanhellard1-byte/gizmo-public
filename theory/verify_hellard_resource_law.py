import numpy as np
from scipy.optimize import minimize


def EH_closed(N, r, L, B):
    s = L / 2.0
    mmin = max(r * s / N, s - 2 * (N - r), 0.0)
    mmax = min(s, 2 * r)
    if s <= B * np.sqrt(r):
        mhat = s
    else:
        mhat = (r * s + (N - r) * B * np.sqrt(r)) / N
    mstar = min(max(mhat, mmin), mmax)
    E = max(mstar / np.sqrt(r) - B, 0.0) ** 2 + (s - mstar) ** 2 / (N - r)
    return E, mstar


def numerical_value(N, r, L, B):
    """Independent constrained optimization over the full singular-value vector."""
    s = L / 2.0
    x0 = np.full(N, min(2.0, s / N))
    rem = s - x0.sum()
    i = 0
    while rem > 1e-12 and i < N:
        add = min(2 - x0[i], rem)
        x0[i] += add
        rem -= add
        i += 1
    x0 = np.sort(x0)[::-1]

    def residual(tau):
        h = tau[:r]
        return max(np.linalg.norm(h) - B, 0.0) ** 2 + np.sum(tau[r:] ** 2)

    cons = [{"type": "ineq", "fun": lambda t: np.sum(t) - s}]
    for i in range(N - 1):
        cons.append({"type": "ineq", "fun": lambda t, i=i: t[i] - t[i + 1]})

    res = minimize(
        residual,
        x0,
        method="SLSQP",
        bounds=[(0, 2)] * N,
        constraints=cons,
        options={"maxiter": 3000, "ftol": 1e-12, "disp": False},
    )
    return res.fun, res.success, res.x


if __name__ == "__main__":
    rng = np.random.default_rng(20260909)
    worst = 0.0
    mismatches = 0
    cases = 500

    for _ in range(cases):
        N = int(rng.integers(2, 13))
        r = int(rng.integers(1, N))
        L = float(rng.uniform(0.01, 4 * N))
        B = float(rng.uniform(0, 8))

        closed, _ = EH_closed(N, r, L, B)
        numeric, success, _ = numerical_value(N, r, L, B)
        err = abs(closed - numeric)
        worst = max(worst, err)
        if success and err > 2e-6:
            mismatches += 1

    print(f"cases={cases}")
    print(f"successful-solver mismatches >2e-6={mismatches}")
    print(f"worst absolute difference={worst:.6e}")
