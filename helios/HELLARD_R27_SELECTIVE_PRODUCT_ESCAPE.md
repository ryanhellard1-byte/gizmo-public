# HELIOS-R27 Selective Product Escape Screen

## Status
Reduced-order orbit/topology screen only. This is not a 3-D kinetic/MHD proof and not an engineering design.

## Product orbit asymmetry
For D-D products:
- triton: 1.01 MeV, charge +e, mass ~3u
- helium-3: 0.82 MeV, charge +2e, mass ~3u

The Larmor-radius ratio is

r_L,T / r_L,He3 = 2 sqrt(1.01/0.82) ~ 2.22.

For a characteristic hot-region radius R = 1.9 mm, the central-birth screening condition

r_L,He3 < R < r_L,T

exists for approximately 59 T < B < 132 T.

## Fast-ion timescale
A 1.01-MeV triton moves at ~8.1e6 m/s, crossing 1.9 mm in ~0.24 ns. Standard Spitzer fast-ion slowing estimates at Te ~100-200 keV and ne ~3e28 m^-3 are tens to hundreds of ns, so prompt-loss orbits can leave before thermalization in the reduced model.

## Why spatial source profile matters
A uniform product-birth distribution gives poor isotope selectivity because edge-born He-3 is also lost.

When the fusion source is core weighted, orbit selectivity improves strongly. Reduced cylindrical radial-orbit Monte Carlo screens found representative cases:

- sigma_source ~0.10 R, B ~140 T: T prompt loss ~85%, He-3 prompt loss ~2-3%.
- sigma_source ~0.20 R, B ~155 T: T prompt loss ~81%, He-3 prompt loss ~8%.

These values assume idealized axial confinement and a static radial boundary.

## Effective neutron fraction with selective prompt loss
Let L_T and L_He be prompt-loss fractions for the D-D-produced triton and He-3. Let retained products subsequently burn completely. For one pair of approximately equal D-D branches,

E_total = 7.30 + 17.6(1-L_T) + 18.3(1-L_He) MeV

E_neutron = 2.45 + 14.1(1-L_T) MeV

so

f_n,eff = [2.45 + 14.1(1-L_T)] / [7.30 + 17.6(1-L_T) + 18.3(1-L_He)].

For L_T ~0.88 and L_He ~0.02, f_n,eff is about 15% in this optimistic retained-product-burn screen.

## Coupled propulsion threshold
At the R27 reference settings used in the reduced model (specific power ~240 kW/kg, momentum collimation ~0.90, exhaust-energy retention ~0.95, Q_eff ~85, driver efficiency ~0.60, electrical recovery ~0.75, neutron recovery ~0.28), the corrected Hellard momentum-energy closure allows an effective neutron fraction up to approximately 23.8%.

If He-3 prompt loss is limited to 10%, closure requires tritium retention below ~32.4%, or tritium prompt loss above ~67.6%.

The core-weighted orbit screen reaches the needed T-loss range while retaining most He-3.

## Independent AWS screen
A deterministic AWS sandbox sweep varied:
- R = 1.2-2.8 mm
- source width sigma/R = 0.08-0.35
- B = 60-240 T

A reduced radial-orbit model with ideal axial confinement found many closure-passing points. Representative candidates had:
- T prompt loss ~88-90%
- He-3 prompt loss ~2-12%
- effective neutron fraction ~15%
- Hellard momentum-energy closure H_PM ~1.08

This is evidence that a useful topology window exists in the reduced model, not evidence that such a magnetic geometry can be built or remain stable.

## External precedent
Direct Fusion Drive / PFRC literature has long proposed two related ideas for reducing side-reaction neutrons in D-He3 plasmas:
1. selective He-3 heating using odd-parity rotating magnetic fields near the He-3 cyclotron response;
2. moving tritium produced by D-D side reactions into the exhaust stream.

That precedent supports investigating selective species transport rather than assuming all D-D products thermalize identically.

## R27 verdict
Simple uniform-volume gyro filtering: REJECTED.

Core-weighted selective prompt escape: PLAUSIBLE IN REDUCED ORDER.

The next hard gate is a full 3-D orbit/kinetic calculation with realistic FRC/cusp/mirror topology, finite source profile, collisions, pitch-angle scattering, evolving fields, and plasma instabilities. The reduced model specifically needs to test whether a configuration can simultaneously maintain:

L_T >= ~0.70,
L_He <= ~0.10,
source width <= ~0.2 R,
and adequate bulk-fuel confinement.
