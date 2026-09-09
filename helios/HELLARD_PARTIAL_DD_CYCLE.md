# HELIOS-R24: Tritium-Stripped, He-3-Recycled D-D Screen

## Motivation
The corrected momentum-energy closure made fully catalyzed D-D require near-ideal magnetic-nozzle momentum collimation. A lower-neutron D-D fuel cycle can, in principle, reduce that burden without importing mission-scale He-3.

## Idealized fuel cycle
Assume approximately equal D-D branches:

- D + D -> He-3 + n, Q ~= 3.27 MeV, neutron energy ~= 2.45 MeV
- D + D -> T + p, Q ~= 4.03 MeV

Retain the produced He-3 and burn it:

- D + He-3 -> He-4 + p, Q ~= 18.3 MeV

Remove the produced tritium before it undergoes D-T burn.

For one event through each D-D branch plus one D-He3 burn, total released energy is approximately:

3.27 + 4.03 + 18.3 = 25.60 MeV

with 2.45 MeV in neutrons. Therefore the simple stoichiometric neutron-energy fraction is:

f_n ~= 2.45 / 25.60 = 0.0957

This is screening bookkeeping, not a validated inertial-fusion burn result.

## Momentum-energy implication
Using the HELIOS-R23 reference assumptions:

- integrated specific power = 250 kW/kg
- neutron-energy recovery Cn = 0.31
- effective Q = 80
- driver electrical efficiency = 0.60
- auxiliary fraction = 0.015
- plasma-to-electric recovery efficiency = 0.80
- exhaust-energy retention etaK = 0.95

Hellard momentum-energy closure gives a minimum momentum-collimation factor of approximately:

psi_min ~= 0.840

For fully catalyzed D-D at f_n = 0.383, the same point requires psi_min ~= 0.953.

## AWS broad design-space comparison
500,000 deterministic reduced-order samples per fuel branch gave:

- fully catalyzed D-D: 3.019% pass fraction
- tritium-stripped / He-3-recycled D-D: 62.061% pass fraction
- D-He3 reactor neutron-fraction case: 74.979% pass fraction
- D-T: 0% pass fraction

These are design-space fractions under assumed ranges, not probabilities of physical success.

## Critical kinetic wall
The low-neutron benefit only exists if D-D-produced tritium can be removed, segregated, or otherwise prevented from undergoing secondary D-T fusion before the useful D-He3 secondary burn completes.

That is not established for a microsecond-class inertial-fusion pulse. D-T reactivity is generally much higher than D-He3 at relevant temperatures, so the tritium-removal timescale may need to be shorter than the D-T burn timescale while He-3 remains available long enough to burn. This may be impossible in an ordinary homogeneous inertial plasma.

The next falsification criterion is therefore a timescale ordering:

    tau_T_remove < tau_DT_burn
    tau_He3_burn < tau_conf

simultaneously.

If this ordering cannot be achieved, HELIOS-R24 fails as an inertial fuel-cycle architecture even though its system-level energy accounting is attractive.

## Claim boundary
R24 is a systems-level fuel-cycle screen. It is not a demonstrated fuel-separation mechanism, not an ignition calculation, and not evidence that rapid tritium extraction from an inertial plasma is feasible.
