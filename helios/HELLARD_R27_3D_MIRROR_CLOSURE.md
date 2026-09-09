# HELIOS-R27 3-D Mirror / Selective-Product Closure

## Status
Reduced-order topology screen only. This is not a validated 3-D orbit calculation, not a fusion-engine demonstration, and not a fundamental law of nature.

## Purpose
Test whether the R27 radial triton/He-3 orbit-selectivity idea survives the addition of axial mirror loss cones.

## Radial selectivity basis
For D-D products, the Larmor-radius ratio is approximately

r_L,T / r_L,He3 = 2 sqrt(1.01/0.82) ≈ 2.22,

because the triton has charge +e and the He-3 product has charge +2e at nearly the same mass.

Core-weighted radial-orbit screens produced candidate loss fractions near:
- LT,rad ≈ 0.88
- LHe,rad ≈ 0.017

for a representative B ≈ 130 T, R ≈ 1.9 mm, source width sigma ≈ 0.08 R.

## Axial mirror loss cone
For an isotropic midplane velocity distribution in an ideal magnetic mirror, the total two-ended loss-cone fraction is approximated by

L_ax = 1 - sqrt(1 - 1/Rm),

where Rm is mirror ratio.

Combining independent radial and axial losses:

L_total = L_rad + (1-L_rad) L_ax.

For the strong radial candidate:
- Rm = 4 -> LT ≈ 0.896, LHe ≈ 0.149, fails He-3 retention gate.
- Rm = 6 -> LT ≈ 0.890, LHe ≈ 0.103, slightly above the 10% He-3 loss gate.
- Rm = 8 -> LT ≈ 0.888, LHe ≈ 0.0805, passes.
- Rm = 10 -> LT ≈ 0.886, LHe ≈ 0.0674, passes.
- Rm = 15 -> LT ≈ 0.884, LHe ≈ 0.0503, passes.

Thus the reduced topology screen gives a practical requirement

Rm >= about 8

for the strongest core-peaked candidates if the total He-3 loss gate is <=10%.

## Effective neutron fraction
Using selective-product escape bookkeeping,

f_n,eff = [2.45 + 14.1(1-LT)] / [7.30 + 17.6(1-LT) + 18.3(1-LHe)].

At Rm=8 with LT≈0.8878 and LHe≈0.0805:

f_n,eff ≈ 0.1545.

## Momentum-energy closure
Using representative R27 propulsion assumptions:
- psi = 0.90 momentum collimation
- eta_K = 0.95 exhaust-energy retention
- Cn = 0.28 neutron recovery
- Qeff = 85
- driver efficiency = 0.60
- auxiliary fraction = 0.015
- electrical recovery eta_R = 0.75
- mission direct-efficiency requirement eta_min ≈ 0.61

the corrected Hellard momentum-energy closure gives

H_PM ≈ 1.063

for the Rm=8 reference point, so the reduced-order propulsion gate passes.

## R27 3-D topology requirements
Promote the following as falsifiable simulation gates:

1. Strongly core-peaked fusion-product source, sigma_fusion <= 0.2 R, preferred <=0.1 R.
2. Product-scale field roughly 100-200 T for mm-scale targets, with actual optimum determined by full orbit integration.
3. Mirror ratio Rm >= 8 as a first reduced-order target; higher may be required after finite-beta/FRC topology is included.
4. Total prompt triton loss LT >= 70%, preferred >=80%.
5. Total prompt He-3 loss LHe <=10%.
6. Effective neutron-energy fraction <=24%, preferred <=18%.
7. Momentum-energy closure H_PM >=1 with nonzero margin.

## Important caveats
The current screen assumes idealized isotropic mirror loss-cone theory plus independent radial orbit loss. Real FRC/mirror systems can violate these assumptions through:
- finite-beta modification of mirror ratio,
- non-adiabatic orbits,
- axial bounce resonances,
- tearing / MHD perturbations,
- electric fields and ambipolar potentials,
- pitch-angle scattering,
- self-generated fields,
- finite source geometry,
- time-varying compression fields,
- collective fast-ion instabilities.

Recent 2026 fast-ion experiments reported axial bounce resonances persisting through a mirror-to-FRC transition, which makes resonance-aware full-orbit simulation the next required step.

## Verdict
R27 is not killed by the first axial-loss correction. A high-mirror-ratio, strongly core-peaked FRC/mirror topology remains viable in reduced-order screening. The next decisive test is full 3-D orbit integration in a realistic time-dependent field with resonance and scattering physics.
