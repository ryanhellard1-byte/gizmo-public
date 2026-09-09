"""Reduced-order HELIOS joint thrust + recirculation closure helper.

Research screening only. This is not a radiation-MHD/PIC/nozzle simulation.
"""

SP_GRID = (60.0, 80.0, 100.0, 120.0, 145.0, 180.0, 250.0)
ETA_GRID = (0.947, 0.831, 0.762, 0.716, 0.676, 0.639, 0.596)


def mission_eta_min(specific_power_kwkg: float) -> float:
    x = float(specific_power_kwkg)
    if x <= SP_GRID[0]:
        return ETA_GRID[0]
    if x >= SP_GRID[-1]:
        return ETA_GRID[-1]
    for x0, x1, y0, y1 in zip(SP_GRID[:-1], SP_GRID[1:], ETA_GRID[:-1], ETA_GRID[1:]):
        if x0 <= x <= x1:
            q = (x - x0) / (x1 - x0)
            return y0 + q * (y1 - y0)
    raise ValueError("specific power interpolation failed")


def usable_fraction(neutron_fraction: float, neutron_recovery: float) -> float:
    return 1.0 - neutron_fraction * (1.0 - neutron_recovery)


def recirculation_fraction(q_eff: float, driver_efficiency: float, aux_fraction: float) -> float:
    return 1.0 / (q_eff * driver_efficiency) + aux_fraction


def hellard_joint(
    specific_power_kwkg: float,
    nozzle_efficiency: float,
    neutron_fraction: float,
    neutron_recovery: float,
    q_eff: float,
    driver_efficiency: float,
    aux_fraction: float,
) -> float:
    available = usable_fraction(neutron_fraction, neutron_recovery)
    available -= recirculation_fraction(q_eff, driver_efficiency, aux_fraction)
    return nozzle_efficiency * available / mission_eta_min(specific_power_kwkg)


def minimum_q_eff(
    specific_power_kwkg: float,
    nozzle_efficiency: float,
    neutron_fraction: float,
    neutron_recovery: float,
    driver_efficiency: float,
    aux_fraction: float,
):
    available = usable_fraction(neutron_fraction, neutron_recovery)
    margin = available - aux_fraction - mission_eta_min(specific_power_kwkg) / nozzle_efficiency
    if margin <= 0.0:
        return None
    return 1.0 / (driver_efficiency * margin)


if __name__ == "__main__":
    # R19 nominal point, shown to fail after recirculation is included.
    params = dict(
        specific_power_kwkg=220.0,
        nozzle_efficiency=0.88,
        neutron_fraction=0.383,
        neutron_recovery=0.31,
        q_eff=60.0,
        driver_efficiency=0.55,
        aux_fraction=0.02,
    )
    print("H_joint =", hellard_joint(**params))
    print(
        "Q_eff,min =",
        minimum_q_eff(
            params["specific_power_kwkg"],
            params["nozzle_efficiency"],
            params["neutron_fraction"],
            params["neutron_recovery"],
            params["driver_efficiency"],
            params["aux_fraction"],
        ),
    )
