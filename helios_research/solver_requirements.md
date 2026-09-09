# HELIOS Solver Requirements and Closure Targets

This file records the minimum physics and numerical outputs required to advance HELIOS beyond reduced-order theory.

## Burn propagation requirement

Reference target yield: 165 MJ.

For a representative hotspot contribution of 10 MJ, the cold DT reservoir must supply 155 MJ.
Using a DT specific fusion energy of approximately 3.39e14 J/kg, the minimum reservoir burn fractions are:

- 10 mg reservoir: 4.57%
- 15 mg reservoir: 3.05%
- 20 mg reservoir: 2.29%
- 25 mg reservoir: 1.83%

These are energy-inventory bounds only. They do not predict whether a burn wave actually propagates before disassembly.

## Minimum simulation physics

A serious HELIOS validation solver needs:

1. 3-D compressible MHD.
2. Resistive induction with temperature-dependent conductivity.
3. Anisotropic electron thermal conduction.
4. Hall-term magnetic-field transport.
5. Nernst advection / thermoelectric magnetic transport.
6. Radiation transport or a validated radiation-diffusion closure.
7. DT fusion reactivity and alpha source terms.
8. Alpha energy/momentum deposition with magnetized transport.
9. Multi-material liner/fuel interfaces and mix diagnostics.
10. Cylindrical/helical DSP initial fields and evolving Btheta/Bz.

## Required output metrics

For each pitch history or initial pitch ratio, record:

- total fusion yield
- reservoir burn fraction
- hotspot burn fraction
- burn-front velocity and direction
- alpha deposition fraction
- electron conductive heat flux
- Btheta/Bz versus time at the burn front
- electron and alpha Hall parameters versus time
- MRT mode amplitudes / growth factors
- liner-fuel mix fraction
- disassembly time

## HELIOS magnetic prediction to falsify

Reduced-order transport predicts a state-dependent optimum pitch

sin^2(theta*) = min[1, 1/(2*(w_alpha*a_alpha + (1-w_alpha)*a_e))]

a_s = chi_s^2/(1+chi_s^2)

with Btheta/Bz = tan(theta*).

The dynamic HR52 surrogate predicts approximately:

- burn onset: Btheta/Bz ~ 1.2
- peak burn: Btheta/Bz ~ 1.0-1.05

Ideal late-stage flux compression from C ~ 25-26 to C ~ 30 produces nearly the same change.

The hypothesis fails if a real 3-D solver does not show improved combined burn+stability performance near the predicted state-dependent pitch trajectory.

## Public code scaffold note

AthenaPK is a promising open MHD scaffold because it exposes 3-D MHD plus anisotropic thermal conduction, viscosity, and resistivity infrastructure. It is not currently a turnkey HELIOS solver: fusion alpha transport, Hall/Nernst terms, radiation physics, EOS/material models for the target, and validated Spitzer transport must be implemented and verified before using it for HELIOS claims.
