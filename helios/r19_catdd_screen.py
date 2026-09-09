"""HELIOS-R19 reduced-order catalyzed-D/D-He3 mission screen.

Research-only numerical model. This is NOT a radiation-MHD, PIC, neutron-transport,
or hardware design code. It combines:
  * Bosch-Hale Maxwellian reactivity fits for DT, D-He3, and both DD branches
  * a zero-dimensional, fixed-temperature DD burn network
  * the archived HELIOS 30-day propulsion efficiency envelope
  * simple pulse-energy and neutron-capture accounting

The purpose is to identify falsifiable target ranges for higher-fidelity simulations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EV_J = 1.602176634e-19
U_KG = 1.66053906660e-27
M_D = 2.01410177812 * U_KG
M_T = 3.01604928199 * U_KG
M_HE3 = 3.01602932265 * U_KG

# Reaction energies [MeV]
E_DDN = 3.2689
E_DDP = 4.0327
E_DT = 17.589
E_DHE3 = 18.353
N_DDN = 2.45
N_DT = 14.1

# Bosch-Hale reactivity constants, valid over the published temperature ranges.
REACTIONS = {
    "DT": dict(bg=34.3827, mrc2=1124656.0, c1=1.17302e-9, c2=0.0151361,
               c3=0.0751886, c4=0.00460643, c5=0.0135,
               c6=-0.00010675, c7=1.366e-5),
    "DHE3": dict(bg=68.7508, mrc2=1124572.0, c1=5.51036e-10, c2=0.00641918,
                 c3=-0.00202896, c4=-1.9108e-5, c5=0.000135776,
                 c6=0.0, c7=0.0),
    "DDN": dict(bg=31.397, mrc2=937814.0, c1=5.4336e-12, c2=0.00585778,
                c3=0.00768222, c4=0.0, c5=-2.964e-6, c6=0.0, c7=0.0),
    "DDP": dict(bg=31.397, mrc2=937814.0, c1=5.65718e-12, c2=0.00341267,
                c3=0.00199167, c4=0.0, c5=1.0506e-5, c6=0.0, c7=0.0),
}


def bosch_hale_reactivity(t_kev: float, c: dict[str, float]) -> float:
    """Return Maxwellian <sigma v> in m^3/s."""
    t = float(t_kev)
    theta1 = t * (c["c2"] + t * (c["c4"] + t * c["c6"])) / (
        1.0 + t * (c["c3"] + t * (c["c5"] + t * c["c7"]))
    )
    theta = t / (1.0 - theta1)
    xi = (c["bg"] ** 2 / (4.0 * theta)) ** (1.0 / 3.0)
    return (
        1.0e-6
        * c["c1"]
        * theta
        * math.sqrt(xi / (c["mrc2"] * t**3))
        * math.exp(-3.0 * xi)
    )


@dataclass
class BurnResult:
    temperature_kev: float
    ntau_m3s: float
    d_remaining: float
    t_remaining: float
    he3_remaining: float
    d_burn_fraction: float
    energy_mev_per_initial_d: float
    neutron_energy_fraction: float
    n_ddn: float
    n_ddp: float
    n_dt: float
    n_dhe3: float


def dd_burn_0d(t_kev: float, ntau_m3s: float, steps: int = 10000) -> BurnResult:
    """Integrate a fixed-T, fixed-volume DD burn in normalized n0*t coordinates.

    Species are normalized to initial deuteron density n_D0=1.  The independent
    variable is u=n_D0*t, so a single result describes any density/dwell pair with
    the same n*tau.  This is a screening model only: hydrodynamic expansion,
    radiation transport, magnetic transport, non-Maxwellian distributions, and
    alpha/proton deposition are omitted.
    """
    sv_ddn = bosch_hale_reactivity(t_kev, REACTIONS["DDN"])
    sv_ddp = bosch_hale_reactivity(t_kev, REACTIONS["DDP"])
    sv_dt = bosch_hale_reactivity(t_kev, REACTIONS["DT"])
    sv_dhe3 = bosch_hale_reactivity(t_kev, REACTIONS["DHE3"])

    # D, T, He3, integrated counts for DDN, DDP, DT, DHe3 reactions.
    y = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    du = ntau_m3s / steps

    def f(state: list[float]) -> list[float]:
        d, tr, he3, *_ = state
        r_ddn = 0.5 * d * d * sv_ddn
        r_ddp = 0.5 * d * d * sv_ddp
        r_dt = d * tr * sv_dt
        r_dhe3 = d * he3 * sv_dhe3
        return [
            -2.0 * (r_ddn + r_ddp) - r_dt - r_dhe3,
            r_ddp - r_dt,
            r_ddn - r_dhe3,
            r_ddn,
            r_ddp,
            r_dt,
            r_dhe3,
        ]

    for _ in range(steps):
        k1 = f(y)
        y2 = [yi + 0.5 * du * ki for yi, ki in zip(y, k1)]
        k2 = f(y2)
        y3 = [yi + 0.5 * du * ki for yi, ki in zip(y, k2)]
        k3 = f(y3)
        y4 = [yi + du * ki for yi, ki in zip(y, k3)]
        k4 = f(y4)
        y = [
            yi + du * (a + 2*b + 2*c + d4) / 6.0
            for yi, a, b, c, d4 in zip(y, k1, k2, k3, k4)
        ]
        y[0] = max(y[0], 0.0)
        y[1] = max(y[1], 0.0)
        y[2] = max(y[2], 0.0)

    d, tr, he3, n_ddn, n_ddp, n_dt, n_dhe3 = y
    e = n_ddn*E_DDN + n_ddp*E_DDP + n_dt*E_DT + n_dhe3*E_DHE3
    en = n_ddn*N_DDN + n_dt*N_DT
    return BurnResult(
        temperature_kev=t_kev,
        ntau_m3s=ntau_m3s,
        d_remaining=d,
        t_remaining=tr,
        he3_remaining=he3,
        d_burn_fraction=1.0-d,
        energy_mev_per_initial_d=e,
        neutron_energy_fraction=en/e if e > 0.0 else 0.0,
        n_ddn=n_ddn,
        n_ddp=n_ddp,
        n_dt=n_dt,
        n_dhe3=n_dhe3,
    )


SP_GRID = [60.0, 80.0, 100.0, 120.0, 145.0, 180.0, 250.0]
ETA_GRID = [0.947, 0.831, 0.762, 0.716, 0.676, 0.639, 0.596]


def mission_eta_required(specific_power_kwkg: float) -> float:
    """Linear interpolation of the archived 30-day HELIOS efficiency envelope."""
    x = float(specific_power_kwkg)
    if x <= SP_GRID[0]:
        return ETA_GRID[0]
    if x >= SP_GRID[-1]:
        return ETA_GRID[-1]
    for x0, x1, y0, y1 in zip(SP_GRID[:-1], SP_GRID[1:], ETA_GRID[:-1], ETA_GRID[1:]):
        if x0 <= x <= x1:
            q = (x-x0)/(x1-x0)
            return y0 + q*(y1-y0)
    raise RuntimeError("interpolation failure")


def neutron_capture_required(
    specific_power_kwkg: float,
    nozzle_efficiency: float,
    neutron_fraction: float,
) -> float:
    """Capture fraction needed for mission closure at given neutron fraction."""
    req = mission_eta_required(specific_power_kwkg)
    charged = 1.0-neutron_fraction
    return (req/nozzle_efficiency - charged)/neutron_fraction


def target_mass_for_yield(result: BurnResult, fusion_yield_mj: float) -> float:
    """Initial deuterium mass in kg needed for the requested yield in this 0-D burn."""
    j_per_initial_d = result.energy_mev_per_initial_d * 1.0e6 * EV_J
    j_per_kg_initial_d = j_per_initial_d / M_D
    return fusion_yield_mj * 1.0e6 / j_per_kg_initial_d


def recoverable_tritium_spark_mj(result: BurnResult, initial_d_mass_kg: float) -> float:
    """Upper-bound DT fusion energy if all residual tritium is recovered and later burned."""
    n0 = initial_d_mass_kg / M_D
    residual_t_mass = result.t_remaining * n0 * M_T
    j_per_kg_t = E_DT * 1.0e6 * EV_J / M_T
    return residual_t_mass * j_per_kg_t / 1.0e6


def main() -> None:
    print("HELIOS-R19 catalyzed-DD reduced screen")
    print("T_keV  nTau(m^-3 s)  D_burn  neutron_E  m_D_for_720MJ(mg)  max_recycled_DT_spark(MJ)")
    for t in (70.0, 100.0, 120.0, 150.0, 180.0, 200.0):
        for ntau in (2e22, 3e22, 5e22):
            r = dd_burn_0d(t, ntau)
            m = target_mass_for_yield(r, 720.0)
            spark = recoverable_tritium_spark_mj(r, m)
            print(f"{t:5.0f}  {ntau:11.2e}  {r.d_burn_fraction:6.3f}  "
                  f"{r.neutron_energy_fraction:9.3f}  {m*1e6:17.3f}  {spark:24.2f}")

    print("\nCatalyzed-DD neutron capture needed for 30-day mission:")
    for sp in (145.0, 180.0, 200.0, 220.0, 250.0):
        vals=[]
        for noz in (0.80, 0.85, 0.90):
            c = neutron_capture_required(sp, noz, 0.383)
            vals.append(f"etaN={noz:.2f}: Cn={c:.3f}")
        print(f"{sp:5.0f} kW/kg -> " + ", ".join(vals))


if __name__ == "__main__":
    main()
