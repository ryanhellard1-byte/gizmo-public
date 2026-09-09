# HELIOS-R28 Grand Closure Audit

## Status

Reduced-order systems closure only. This is not a demonstrated fusion device, flight engine, or proof of new fundamental physics.

## Purpose

R28 folds the R27 selective-product-escape concept into the entire HELIOS closure stack so that species selectivity, neutron fraction, target gain, propulsion momentum-energy closure, electrical recovery, thermal rejection, repetition architecture, and integrated source mass must pass in the same case.

## Selective-product escape

For approximately equal D-D branches, with prompt tritium loss L_T and He-3 loss L_He:

E_total = 7.30 + 17.6(1-L_T) + 18.3(1-L_He) MeV

E_n = 2.45 + 14.1(1-L_T) MeV

f_n = E_n / E_total

R27 development gates:
- L_T >= 0.70
- L_He <= 0.10
- f_n <= 0.24

Preferred:
- L_T >= 0.80
- f_n <= 0.18

## Momentum-energy closure

H_PM = psi^2 * eta_K * [1 - f_n(1-C_n) - (1/(Q_eff eta_d)+a)/eta_R] / eta_min(alpha)

Pass condition:

H_PM >= 1

where psi is axial momentum collimation, eta_K exhaust-energy retention, C_n neutron-energy recovery into useful ejectable plasma, eta_R plasma-to-electric recovery, eta_d driver efficiency, a auxiliary electrical burden, and alpha integrated source specific power.

## Target closure proxy

Q_eff = Q_clean * chi_transport * chi_symmetry * chi_mix * chi_instability

R28 screen required Q_eff >= 40.

## Mass/repetition closure

M_source = P_fusion / alpha

N_installed = ceil(f_aggregate / f_cell) + 3

M_hardware = N_installed m_cell + M_shared + M_radiator

Pass condition:

M_hardware <= M_source

## Thermal closure proxy

The radiator ledger includes recovery inefficiency, driver inefficiency, auxiliary power, and the fraction of nozzle/plasma losses deposited in hardware. Uncaptured neutron/plasma energy that escapes the vehicle is not charged to the radiator.

R28 screen required:
- modeled onboard heat <= 5.5 GW
- radiator mass <= 70 t

## Integrated AWS audit

500,000 deterministic cases were sampled across broad R27-like ranges.

Pass count: 55,620
Pass fraction: 11.124%

These are design-space fractions, not probabilities of success.

Survivor medians:
- prompt tritium loss L_T: 0.832
- prompt He-3 loss L_He: 0.0538
- effective neutron-energy fraction: 0.1748
- Q_eff: 53.37
- integrated source specific power: 233.2 kW/kg
- momentum collimation psi: 0.920
- exhaust-energy retention eta_K: 0.950
- neutron recovery C_n: 0.282
- driver efficiency eta_d: 0.605
- electrical recovery eta_R: 0.767
- auxiliary burden: 1.52%
- H_PM: 1.057
- aggregate pulse rate: 115.0 Hz
- cell pulse rate: 4.25 Hz
- installed cells: 31
- cell mass: 4.00 t
- shared hardware: 87.4 t
- modeled onboard heat: 4.53 GW
- radiator mass: 46.1 t
- integrated source mass: 365.6 t
- modeled hardware mass: 257.4 t

Largest reduced-order failure fractions in this intentionally broad sample:
- thermal gate: 64.7%
- momentum-energy gate: 61.7%
- selective-product-escape gate: 51.0%
- target Q_eff gate: 24.6%
- neutron-fraction gate: 6.2%
- mass/repetition gate: 0.13%

## R28 canonical research neighborhood

- L_T >= 0.80 preferred
- L_He <= 0.10
- f_n approximately 0.15-0.20
- Q_eff approximately 50-70 minimum development neighborhood, stretch >80
- alpha approximately 230-250 kW/kg
- psi approximately 0.91-0.93
- eta_K approximately 0.94-0.97
- eta_R approximately 0.75-0.80
- C_n approximately 0.27-0.32
- aggregate pulse rate approximately 110-120 Hz
- roughly 30-35 installed cells
- roughly 4 Hz/cell
- radiator mass roughly 40-55 t at the assumed all-in radiator performance

## Claim boundary

R28 shows that one internally consistent reduced-order design region exists if selective prompt tritium escape is real in a realistic 3-D magnetic topology. It does not establish that such selectivity survives self-consistent plasma fields, collisions, orbit stochasticity, MHD evolution, axial end losses, charge exchange, or reaction-source broadening.

The next decisive solver must therefore couple 3-D particle orbits (or hybrid/PIC fast ions) to an evolving magnetized plasma background and evaluate L_T, L_He, f_n, and energy/momentum transfer self-consistently.
