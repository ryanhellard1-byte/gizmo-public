"""3-D Lorenz-Mie scaling test for the Hellard rank-strength resource theorem.

This script connects the abstract extinction burden L to exact vector-spherical
Maxwell channels for homogeneous spheres.  It checks passivity channel by channel
and measures the class-envelope rank threshold r_crit=L/4 versus size parameter x=ka.

This is a physics validation/scaling test, not a proof of the theorem and not a
claim that every object's physical actuator rank is exactly L/4.
"""

import math
import numpy as np
from scipy.special import spherical_jn, spherical_yn


def wiscombe_lmax(x):
    """Conservative Mie truncation, close to Wiscombe's widely used criterion."""
    return int(math.ceil(x + 4.0 * x ** (1.0 / 3.0) + 2.0))


def mie_coefficients(m, x, lmax=None):
    if lmax is None:
        lmax = wiscombe_lmax(x)
    ell = np.arange(1, lmax + 1)

    jx = spherical_jn(ell, x)
    jxp = spherical_jn(ell, x, derivative=True)
    yx = spherical_yn(ell, x)
    yxp = spherical_yn(ell, x, derivative=True)

    mx = m * x
    jm = spherical_jn(ell, mx)
    jmp = spherical_jn(ell, mx, derivative=True)

    psi_x = x * jx
    dpsi_x = jx + x * jxp
    psi_m = mx * jm
    dpsi_m = jm + mx * jmp

    xi_x = x * (jx + 1j * yx)
    dxi_x = (jx + 1j * yx) + x * (jxp + 1j * yxp)

    a = (m * psi_m * dpsi_x - psi_x * dpsi_m) / (
        m * psi_m * dxi_x - xi_x * dpsi_m
    )
    b = (psi_m * dpsi_x - m * psi_x * dpsi_m) / (
        psi_m * dxi_x - m * xi_x * dpsi_m
    )
    return ell, a, b


def sphere_metrics(m, x):
    lmax = wiscombe_lmax(x)
    ell, a, b = mie_coefficients(m, x, lmax)
    degeneracy = 2 * ell + 1

    # With S_l = 1 - 2c_l and D_l=2c_l, each electric or magnetic
    # channel contributes X_l = 4 Re(c_l) to the burden.
    L = float(4.0 * np.sum(degeneracy * (np.real(a) + np.real(b))))

    # Electric + magnetic channels, including every m=-ell,...,+ell.
    K = int(2 * lmax * (lmax + 2))

    # Passive-channel identity: X-|D|^2 = 1-|S|^2 >= 0.
    pass_a = 4.0 * np.real(a) - 4.0 * np.abs(a) ** 2
    pass_b = 4.0 * np.real(b) - 4.0 * np.abs(b) ** 2

    return {
        "x": float(x),
        "lmax": lmax,
        "K": K,
        "L": L,
        "rcrit": L / 4.0,
        "rank_fraction": L / (4.0 * K),
        "min_passivity_margin": float(min(np.min(pass_a), np.min(pass_b))),
    }


def power_fit(xs, ys):
    p, logc = np.polyfit(np.log(xs), np.log(ys), 1)
    return float(p), float(np.exp(logc))


def main():
    materials = {
        "lossless_n1p5": 1.5 + 0.0j,
        "absorbing_n2p5_k0p2": 2.5 + 0.2j,
    }

    print("HELLARD 3-D LORENZ-MIE CHANNEL SCALING")
    print()

    for name, m in materials.items():
        print(f"material={name}, m={m}")
        for x in [4, 8, 12, 16, 20]:
            d = sphere_metrics(m, float(x))
            print(
                "x={x:5.1f} lmax={lmax:3d} K={K:5d} "
                "L={L:12.6f} rcrit={rcrit:11.6f} "
                "rcrit/K={rank_fraction:.8f} pass_min={min_passivity_margin:.3e}".format(**d)
            )

        xs = np.arange(10.0, 101.0, 2.0)
        rs = np.array([sphere_metrics(m, x)["rcrit"] for x in xs])
        exponent, coefficient = power_fit(xs, rs)
        print(
            f"fit x=10..100: rcrit ~= {coefficient:.8g} x^{exponent:.8f}; "
            f"rcrit/x^2 at x=100 = {rs[-1]/10000.0:.8f}"
        )
        print()


if __name__ == "__main__":
    main()
