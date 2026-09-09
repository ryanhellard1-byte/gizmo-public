import math

from model import (
    PlasmaState,
    burn_transport_score,
    hellard_optimum_angle_deg,
    helical_pitch_ratio,
    liner_kinetic_energy_mj,
    required_driver_energy_mj,
    shots_per_module,
    target_gain,
)


def test_representative_angle():
    s = PlasmaState(chi_e=10, chi_alpha=1, w_alpha=0.5)
    theta = hellard_optimum_angle_deg(s)
    assert 54.9 < theta < 55.1


def test_representative_pitch():
    s = PlasmaState(chi_e=10, chi_alpha=1, w_alpha=0.5)
    p = helical_pitch_ratio(s)
    assert 1.42 < p < 1.44


def test_analytic_angle_is_local_maximum():
    s = PlasmaState(chi_e=10, chi_alpha=1, w_alpha=0.5)
    th = math.radians(hellard_optimum_angle_deg(s))
    center = burn_transport_score(th, s)
    assert center >= burn_transport_score(th - math.radians(1), s)
    assert center >= burn_transport_score(th + math.radians(1), s)


def test_strong_magnetization_limit_goes_to_45_deg():
    s = PlasmaState(chi_e=1e6, chi_alpha=1e6, w_alpha=0.5)
    assert abs(hellard_optimum_angle_deg(s) - 45.0) < 1e-3


def test_liner_energy():
    assert abs(liner_kinetic_energy_mj(2.5, 55) - 3.78125) < 1e-9


def test_driver_gain_chain():
    useful = liner_kinetic_energy_mj(2.5, 55) + 1.158
    driver = required_driver_energy_mj(useful, 0.25)
    q = target_gain(165.0, driver)
    assert q > 5


def test_module_campaign():
    n = shots_per_module(30, 60, 12)
    assert abs(n - 12_960_000) < 1


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print(f"{len(tests)} tests passed")
