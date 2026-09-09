# HELIOS-R25 staged D-D / D-He3 fuel cycle

## Status
Reduced-order systems concept only. Not a validated fusion target or flight design.

## Core cycle
1. Run a short D-D breeder pulse.
2. Expand/cool the exhaust before significant secondary D-T burn.
3. Separate helium from hydrogen isotopes in the exhaust processing loop.
4. Recycle produced He-3 into a later D-He3 propulsion pulse.
5. Route D/T to slower hydrogen-isotope processing/storage.

The key architectural point is that He-vs-hydrogen separation is performed between pulses in a continuous exhaust loop, not inside the nanosecond-scale burn region.

## Stoichiometric energy closure
Using ~50/50 D-D branching:
- D+D -> He3+n : 3.27 MeV
- D+D -> T+p : 4.03 MeV
- D+He3 -> He4+p : 18.3 MeV

Two D-D reactions produce one He-3 nucleus on average, so for every later D-He3 reaction the combined cycle releases:

7.30 + 18.30 = 25.60 MeV

Only 2.45 MeV is in the prompt D-D neutron if the produced tritium is prevented from secondary D-T burn. Thus the ideal staged-cycle neutron-energy fraction is 2.45/25.60 = 9.57%.

Energy split:
- D-D breeder stage: 7.30/25.60 = 28.52%
- D-He3 stage: 18.30/25.60 = 71.48%

## R25 nominal reduced-order point
Using the corrected momentum-energy accounting with representative values:
- directed jet power: 54.68 GW
- momentum collimation psi = 0.90
- exhaust energy retention eta_K = 0.95
- neutron recovery C_n = 0.28
- Q_eff = 80
- driver efficiency = 0.60
- auxiliaries = 1.5% of fusion power
- plasma-to-electric recovery eta_R = 0.75
- neutron fraction f_n = 0.0957

The resulting directed-jet fraction is approximately 0.680, requiring about 80.4 GW of total fusion power.

At 120 Hz aggregate pulse rate, average fusion yield is approximately 670 MJ/pulse.

If breeder and D-He3 pulses use equal fusion yield, steady-state pulse-rate split follows the stage energy split:
- breeder: ~34.2 Hz
- D-He3: ~85.8 Hz

For ~670 MJ equal-energy pulses:
- one D-D breeder pulse produces ~2.87 mg He-3
- one D-He3 pulse consumes ~1.15 mg He-3

34.2 breeder pulses/s × 2.87 mg ≈ 85.8 D-He3 pulses/s × 1.15 mg, so the He-3 inventory closes in steady state at the stoichiometric level.

Approximate steady-state He-3 production/consumption throughput is ~0.098 g/s at this power point.

## Separation architecture
The relevant separation is helium from hydrogen isotopes immediately after exhaust cooling/cleanup. Hydrogen-selective palladium-alloy permeation and related fusion exhaust-processing concepts are candidate technologies for this step. D/T isotope separation can occur later and does not need to keep pace with the burn on a per-pulse basis.

## Hard gates
R25 remains unproven until all of the following close:
1. D-D breeder pulse can terminate/expand before substantial secondary D-T burn.
2. Exhaust processing can recover He-3 with sufficiently high efficiency and sufficiently low inventory delay.
3. The continuous He-3 recycle loop can supply ~0.1 g/s class throughput at the nominal R25 point.
4. Separation-system mass, cryogenic/pumping power, and tritium inventory fit the integrated specific-power budget.
5. D-He3 target physics achieves the required degraded gain and repetition rate.
6. Corrected momentum/energy/nozzle closure remains satisfied when separation and recycle power are charged against auxiliaries.

## Claim boundary
The steady-state stoichiometric fuel-production balance closes algebraically. This does not demonstrate the plasma kinetics, separation hardware, target gain, or flight propulsion system.
