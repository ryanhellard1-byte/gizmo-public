"""Independent arbitrary-precision cross-check of selected Lorenz-Mie burdens.

Uses mpmath's ordinary half-integer Bessel functions rather than SciPy's
spherical_jn/spherical_yn path used by verify_hellard_mie_channel_scaling.py.
The purpose is to detect implementation/library-specific numerical errors.
"""

import math
import mpmath as mp

mp.mp.dps = 60


def sph_j(n, z):
    return mp.sqrt(mp.pi / (2 * z)) * mp.besselj(n + mp.mpf("0.5"), z)


def sph_y(n, z):
    return mp.sqrt(mp.pi / (2 * z)) * mp.bessely(n + mp.mpf("0.5"), z)


def sph_derivative(n, z, fn):
    if n == 0:
        return -fn(1, z)
    return fn(n - 1, z) - (n + 1) * fn(n, z) / z


def lmax_wiscombe_like(x):
    return int(math.ceil(x + 4.0 * x ** (1.0 / 3.0) + 2.0))


def burden(m, x):
    m = mp.mpc(m)
    x = mp.mpf(x)
    mx = m * x
    lmax = lmax_wiscombe_like(float(x))
    total = mp.mpf("0")

    for ell in range(1, lmax + 1):
        jx = sph_j(ell, x)
        yx = sph_y(ell, x)
        jxp = sph_derivative(ell, x, sph_j)
        yxp = sph_derivative(ell, x, sph_y)

        jm = sph_j(ell, mx)
        jmp = sph_derivative(ell, mx, sph_j)

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

        total += (2 * ell + 1) * (mp.re(a) + mp.re(b))

    return 4 * total


def main():
    # Reference values come from the independent SciPy implementation.
    cases = [
        (mp.mpc("1.5", "0"), 4.0, mp.mpf("129.6784707686975")),
        (mp.mpc("1.5", "0"), 20.0, mp.mpf("1628.669584304705")),
        (mp.mpc("2.5", "0.2"), 4.0, mp.mpf("88.7782407981958")),
        (mp.mpc("2.5", "0.2"), 20.0, mp.mpf("1799.2404472430733")),
    ]

    print("HELLARD MIE 60-DIGIT CROSS-CHECK")
    for m, x, ref in cases:
        val = burden(m, x)
        err = abs(val - ref)
        print(f"m={m}, x={x:g}, L_mp={mp.nstr(val, 30)}, abs_diff={mp.nstr(err, 8)}")


if __name__ == "__main__":
    main()
