# HELIOS-R19 reduced research branch

This branch explores a **simulation-only** HELIOS architecture using GIZMO as a possible future MHD/radiation-hydrodynamics backbone plus an external reduced fusion-burn model.

## Current architecture hypothesis

`magnetized compression -> localized D-T / fast-ignition trigger -> catalyzed D-D main burn -> partial neutron-energy recovery -> magnetic nozzle`

This is **not** a demonstrated fusion engine, reactor design, radiation-MHD solution, PIC solution, or neutron-transport solution.

## Why catalyzed D-D moved to the front

The existing HELIOS system audit found that pure D-T requires roughly 80.6% neutron-energy recovery at the older 145-kW/kg / 80%-nozzle point, while the archived gram-scale liner estimate was only about 24-31%.

D-He3 greatly reduces the neutron problem but implies a mission-class He-3 burned inventory of order hundreds of kilograms for the current 30-day power level, far beyond present terrestrial supply.

Fully catalyzed D-D has a literature neutron-energy fraction around 38.3%. At sufficiently high propulsion specific power and nozzle efficiency, the required neutron-energy recovery drops into the same order as the archived 24-31% gram-scale estimate.

## Independent reduced-order AWS screen

A 600,000-sample deterministic screen using broad ranges for gain, transport, mix, symmetry, fast-ignition coupling, perturbation smoothing, instability suppression, cell mass, driver efficiency, repetition rate, specific power, nozzle efficiency, and 24-35% neutron recovery produced a small catalyzed-D-D survivor region.

Median survivor values were approximately:

- specific power: 221 kW/kg
- magnetic-nozzle efficiency: 87.4%
- clean gain: 92.8
- degraded/effective gain proxy: 60.7
- mix retention: 96.9%
- symmetry retention: 94.9%
- fast-ignition coupling: 7.6%
- initial perturbation smoothing: 4.7x
- instability-growth suppression: 41%
- firing-cell mass: 3.7 t
- repetition rate: 119 Hz aggregate
- neutron-energy recovery: 31%
- fusion pulse: 719 MJ
- electrical driver pulse: 23 MJ

The survivor fraction is a **design-space fraction, not a probability of physical success**.

## Zero-dimensional burn screen

`r19_catdd_screen.py` implements Bosch-Hale Maxwellian reactivities for DT, D-He3, and both D-D branches and integrates a fixed-temperature, fixed-volume D-D reaction network.

A representative screening point near 150 keV and n*tau = 3e22 m^-3 s gives about 78% D burn and about 38% neutron-energy fraction, close to the fully catalyzed limit. It implies only milligram-class initial deuterium for a ~720-MJ idealized pulse.

This result is not predictive until hydrodynamic expansion, radiation, magnetic transport, mix, non-Maxwellian kinetics, and charged-particle deposition are coupled.

## Interesting fuel-cycle hypothesis

The same reduced network leaves residual tritium after a catalyzed-D-D pulse. At the representative screening point, ideal recovery could supply roughly the tritium inventory corresponding to a ~15-MJ D-T spark on a later pulse.

That suggests a falsifiable self-seeding hypothesis:

`startup tritium -> D-D pulse -> recover bred tritium -> next localized ignition seed`

Product recovery at useful efficiency and repetition rate is completely unproven.

## Next simulation gates

1. Couple the reduced reaction network to a validated MHD/radiation-hydrodynamics calculation.
2. Sweep 120-180 keV and n*tau ~3-5e22 m^-3 s rather than freezing the 38.3% neutron fraction.
3. Model incomplete He-3 secondary burn, which can raise the neutron fraction.
4. Track radiation, alpha/proton deposition, magnetic transport, mix, and hydrodynamic expansion.
5. Couple the resulting plasma state to a nozzle-efficiency model rather than using one constant efficiency.
6. Treat tritium-product recovery as a measured gate, not an assumed feature.

GIZMO already provides ideal/non-ideal MHD, radiation hydrodynamics, anisotropic conduction/viscosity, cooling, and adaptive fluid methods. The repository does not presently expose a fusion reaction network in the public code search, so the burn module must remain external or be added as a research extension.