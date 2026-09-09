# HELIOS-R29 Evidence Closure Audit

## Purpose

Separate mathematical/reduced-order closure from experimentally demonstrated 2026 capability.

## Current reduced-order survivor neighborhood

Representative R28/R29 survivor point from integrated Monte Carlo screens:

- selective triton prompt loss LT ~ 0.83
- He-3 prompt loss LHe ~ 0.054
- effective neutron fraction fn ~ 0.175
- effective target gain Qeff ~ 53
- integrated source specific power ~ 233 kW/kg
- axial momentum fraction psi ~ 0.92
- exhaust kinetic/enthalpy retention etaK ~ 0.95
- electrical recovery etaR ~ 0.77
- neutron recovery Cn ~ 0.28
- hardware heat ~ 4.5 GW
- radiator mass ~ 46 t
- about 31 installed firing cells at about 4.25 Hz/cell

This neighborhood is mathematically self-consistent in the reduced-order closure model. It is not demonstrated hardware.

## Minimum propulsion thresholds around the representative survivor point

Holding the other median survivor values fixed, the momentum-energy block crosses H_PM = 1 at approximately:

- psi >= 0.885
- etaK >= 0.880
- etaR >= 0.383
- Qeff >= 21.4
- source specific power >= 165 kW/kg
- effective neutron fraction <= 0.259

At 10% He-3 prompt loss, the corresponding selective-product requirement is approximately:

- LT >= 0.612

Thus the reduced-order architecture does not intrinsically require 97% nozzle momentum conversion if selective charged-product escape truly lowers neutron production.

## 2026 evidence status

### Target gain

NIF publicly reports an 11th ignition on 20 June 2026 at 7.9 +/- 0.4 MJ and target gain about 3.8. This is not the same target architecture as HELIOS but it is an experimental benchmark showing that Qeff ~ 20-50 remains far beyond demonstrated inertial-fusion target gain.

### PJMIF / PLX compression

Published multidimensional PLX modeling includes anisotropic conduction, magnetic diffusion, radiation transport, kinetic effects, and 1D/2D/3D target/liner simulations. The published calculations report preheated magnetized targets around 40 eV and compression above 1 keV, still far below the advanced-fuel conditions assumed in HELIOS.

### Species selectivity

OMEGA D-He3 implosions accepted in Physical Review Research in August 2026 report the first persistent light-ion species separation through shock and compression phases, with about a 5% surplus of deuterium relative to the original mixture. This establishes multi-ion separation as real physics, but it is nowhere near a demonstration of the R27 requirement of roughly 60-80% prompt triton loss with <=10% He-3 loss.

### Magnetic nozzle and power recovery

The NASA power-generating magnetic-nozzle project is described as experimental/computational validation and scaling of thrust and flux-compression electrical generation. Current public descriptions do not establish the HELIOS-required simultaneous values for momentum collimation, exhaust-energy retention, and electrical recovery. A 2026 laser-fusion magnetic-nozzle experiment also reports that momentum efficiency depends on plasma density distribution and does not obey a simple universal scaling law.

## R29 conclusion

HELIOS-R29 is not experimentally closed.

The reduced-order equations define a finite, internally consistent survivor region, but four experimental demonstrations are still missing:

1. advanced-fuel target gain at least Qeff ~ 20 as an absolute propulsion-floor neighborhood, preferably >50 for useful margin;
2. self-consistent 3-D product selectivity with LT >= 0.61 at LHe <= 0.10 as a minimum threshold, preferably LT >= 0.80;
3. simultaneous magnetic-nozzle measurements near psi >= 0.89, etaK >= 0.88, and sufficient electrical recovery;
4. integrated source specific power at least ~165 kW/kg at the threshold point, preferably >230 kW/kg, with multi-GW waste-heat management.

The correct scientific status is therefore:

- mathematical systems closure: PASS in a reduced-order survivor region;
- experimental closure: FAIL / NOT YET DEMONSTRATED;
- next step: validated 3-D kinetic/MHD product-orbit simulation and experimentally anchored magnetic-nozzle plus advanced-fuel target data.
