# HELIOS-R31: Ambipolar and Magnetic-Disorder Closure

## Purpose
This revision adds two effects that cannot be ignored in a named selective-escape law: ambipolar electrostatic feedback and magnetic-field disorder.

## 1. Ambipolar compatibility
For a fast ion born near the mirror center, the adiabatic axial escape condition in a central positive electrostatic potential Phi is modified by both magnetic moment and electrostatic energy. For an isotropic population with mirror ratio M, product energy E, and charge q, the prompt axial loss fraction h implies the conservative potential ceiling

Phi_max = (E/q) [ M - 1 - M(1-h)^2 ].

Define the Hellard ambipolar compatibility number

A_Phi = Phi_max / Phi_amb.

Ambipolar-compatible selective confinement requires A_Phi >= 1.

For He-3 (E = 0.82 MeV, q = 2e) and h = 0.15:
- M = 4: Phi_max ~ 45 kV
- M = 6: Phi_max ~ 273 kV
- M = 10: Phi_max ~ 728 kV

Thus M=4 is fragile to a hot-plasma ambipolar potential, whereas M~6 or higher provides substantially more electrostatic margin.

## 2. Coupled 3-D orbit + electrostatic sensitivity test
A reduced 3-D Boris orbit model used:
- R = 1.9 mm
- L = 2R
- core source width sigma = 0.08R
- B0 ~ 130-150 T
- mirror ratio M = 6-7
- central positive parabolic potential Phi_c = 150-300 kV
- isotropic 1.01 MeV tritons and 0.82 MeV He-3 products

Repeated 1,200-particle-per-species runs around the best region gave representative results:

B0=140 T, M=6, Phi_c=150 kV:
- T prompt loss ~ 93.5%
- He-3 prompt loss ~ 11.1%
- effective neutron fraction ~ 13.6%
- corrected momentum-energy closure H_PM ~ 1.094

B0=140 T, M=6, Phi_c=200 kV:
- T prompt loss ~ 93.8%
- He-3 prompt loss ~ 12.8%
- effective neutron fraction ~ 13.6%
- H_PM ~ 1.094

B0=140 T, M=6, Phi_c=250 kV:
- T prompt loss ~ 94.3%
- He-3 prompt loss ~ 13.3%
- effective neutron fraction ~ 13.5%
- H_PM ~ 1.095

These are reduced test-particle calculations, not self-consistent PIC.

## 3. Magnetic-disorder compatibility
Because rho_L is proportional to 1/B, a local field depression can push He-3 product orbits across the radial boundary. A conservative one-sigma robust-containment condition is

2 rho_He/(1-delta_B) + sigma_fusion < R.

Solving for the tolerable fractional field depression gives

delta_B,max = 1 - 2 rho_He/(R - sigma_fusion).

At B0=140 T, R=1.9 mm:
- sigma/R = 0.05 -> delta_B,max ~ 10.6%
- sigma/R = 0.08 -> delta_B,max ~ 7.7%
- sigma/R = 0.10 -> delta_B,max ~ 5.7%
- sigma/R = 0.12 -> delta_B,max ~ 3.5%

The He-3-retention side controls the disorder tolerance; the triton orbit remains much larger.

Define the Hellard magnetic-disorder margin

A_B = delta_B,max / delta_B,actual.

Robust passive selectivity requires A_B >= 1.

## 4. Updated prompt selective-escape closure
A conservative R31 engineering closure requires simultaneous satisfaction of:

1. orbit separation: kappa = rho_T/rho_He > 1;
2. compact source: chi_H = sigma_fusion/R <= chi_crit;
3. prompt timing: Pi_T = tau_escape,T/tau_DT << 1;
4. ambipolar compatibility: A_Phi >= 1;
5. magnetic-disorder compatibility: A_B >= 1;
6. neutron closure: S_H = f_n,max/f_n,eff >= 1;
7. spacecraft momentum-energy closure: H_PM >= 1.

The combined Hellard prompt-selective engineering number may be written

H_Hellard = min(kappa/kappa_min, chi_crit/chi_H, Pi_crit/Pi_T, A_Phi, A_B, S_H, H_PM).

Closure requires H_Hellard >= 1.

## Claim boundary
This is a derived engineering closure criterion supported by reduced 3-D orbit and systems calculations. It is not a demonstrated fundamental law of nature. The remaining decisive validation is self-consistent kinetic/PIC or experiment with evolving electric fields, collisions, plasma currents, and realistic FRC/mirror topology.
