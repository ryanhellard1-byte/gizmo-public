from __future__ import annotations

import math


def a(chi: float) -> float:
    if chi < 0:
        raise ValueError('chi must be nonnegative')
    return chi * chi / (1.0 + chi * chi)


def theta_star_deg(chi_e: float, chi_alpha: float, w_alpha: float) -> float:
    if not 0.0 <= w_alpha <= 1.0:
        raise ValueError('w_alpha must be in [0,1]')
    b = w_alpha * a(chi_alpha) + (1.0 - w_alpha) * a(chi_e)
    if b < 0.5:
        return 90.0
    s2 = 1.0 / (2.0 * b)
    return math.degrees(math.asin(math.sqrt(min(1.0, s2))))


def pitch_star(chi_e: float, chi_alpha: float, w_alpha: float) -> float:
    th = theta_star_deg(chi_e, chi_alpha, w_alpha)
    if th >= 89.999999:
        return math.inf
    return math.tan(math.radians(th))


def chi_alpha_transition(chi_e: float, w_alpha: float) -> float | None:
    '''Boundary where the interior optimum first appears.

    Solve w*a_alpha + (1-w)*a_e = 1/2.
    Returns 0 if all nonnegative chi_alpha are interior, None if the
    threshold cannot be reached for finite chi_alpha.
    '''
    if not 0.0 < w_alpha <= 1.0:
        raise ValueError('w_alpha must be in (0,1]')
    ae = a(chi_e)
    aa_req = (0.5 - (1.0 - w_alpha) * ae) / w_alpha
    if aa_req <= 0.0:
        return 0.0
    if aa_req >= 1.0:
        return None
    return math.sqrt(aa_req / (1.0 - aa_req))


if __name__ == '__main__':
    for ce in (5, 10, 50):
        for ca in (0.25, 0.5, 1.0, 2.0, 5.0):
            th = theta_star_deg(ce, ca, 0.5)
            p = pitch_star(ce, ca, 0.5)
            print(f'chi_e={ce:>3}, chi_alpha={ca:>4}: theta={th:6.2f} deg, pitch={p:6.3f}')
