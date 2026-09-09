# Hellard Selective-Escape Law

## Status

This is a reduced-order engineering closure relation for magnetically selective fusion-product escape. It is not a fundamental law of nature and is not a substitute for self-consistent PIC/hybrid-PIC, FRC equilibrium, or experiment.

## Species magnetization parameter

For fusion product species s, define

Lambda_s = R / r_L,s = |q_s| B R / sqrt(2 m_s E_s).

For the D-D products T(1.01 MeV, +e) and He-3(0.82 MeV, +2e),

r_L,T / r_L,He3 = 2 sqrt(1.01/0.82) ~= 2.22,

so

Lambda_T ~= Lambda_He3 / 2.22.

A passive orbital-selectivity window exists when

1 < Lambda_He3 < 2.22,

which is equivalent to

r_L,He3 < R < r_L,T.

This is necessary but not sufficient because off-axis births, axial loss cones, collisions, electric fields, and time-dependent fields alter the loss fractions.

## Source compactness

Define

chi = sigma_fusion / R,

where sigma_fusion characterizes the width of the fusion-product birth distribution.

The current reduced 3-D orbit and stochastic perturbation screens show a strong transition near

chi ~ 0.12-0.17.

In the 250,000-case stochastic screen:

- chi = 0.07-0.12: 96.4% of sampled perturbation cases passed the hard selective-escape gate.
- chi = 0.12-0.17: 19.3% passed.
- chi = 0.17-0.22: 0% passed.

This makes compact source formation a controlling variable rather than a cosmetic target preference.

## Fast-escape / scattering parameter

Define

K_s = tau_escape,s / tau_scatter,s.

Prompt orbit selectivity requires

K_T << 1,

so a triton on a loss orbit escapes before collisions erase its fast-ion orbit identity.

## Electrostatic distortion parameter

Define

epsilon_E,s = |Z_s e DeltaPhi| / E_s.

For passive gyro-orbit discrimination, electrostatic potentials must not overwhelm the MeV-scale birth-energy separation. Small or deliberately tuned potentials can modify species loss and may assist separation, but require self-consistent treatment.

## Effective neutron fraction

Let L_T be the prompt loss fraction of D-D-produced tritons and L_He the prompt loss fraction of D-D-produced He-3. If retained T subsequently burns by D-T and retained He-3 subsequently burns by D-He3, the effective neutron-energy fraction is

f_n,eff = [2.45 + 14.1(1-L_T)] / [7.30 + 17.6(1-L_T) + 18.3(1-L_He)].

This provides the direct bridge from orbit physics to propulsion energy accounting.

## Selective-escape closure number

For a mission/fuel architecture with maximum tolerable neutron fraction f_n,max, define

S_H = f_n,max / f_n,eff.

Then

S_H >= 1

is the selective-product-escape neutron-budget closure condition.

It must be satisfied simultaneously with the Hellard momentum-energy propulsion closure, target-gain closure, mass/repetition closure, thermal closure, and hardware lifetime constraints.

## Equivalent triton-loss requirement

For a prescribed neutron ceiling f_* and He-3 loss L_He,

L_T,min = 1 - { f_*[7.30 + 18.3(1-L_He)] - 2.45 } / {14.1 - 17.6 f_*},

provided the denominator is positive.

At the current R28 propulsion reference, f_* is about 0.238. If L_He = 0.10, the required prompt triton loss is only about 0.676. The current reduced orbit models produce roughly 0.80-0.98 triton loss in the compact-source magnetic-mirror basin.

## Current R28 reduced-order basin

Representative compact-source region:

- B ~ 120-200 T
- mirror ratio ~ 4
- axial half-length ~ 2-4 R
- chi = sigma_fusion/R <= ~0.12 preferred
- triton prompt loss ~ 0.9-0.98
- He-3 prompt loss ~ 0.10-0.15 in favorable 3-D mirror cases
- effective neutron fraction ~ 0.12-0.16

The 250,000-case stochastic perturbation screen varied scattering times 20-200 ns, axial potentials +/-60 kV, B modulation 0-15%, field strength 120-200 T, and source width 0.07-0.22 R. Hard-gate pass fraction was 38.7%; survivor medians were approximately B=158 T, chi=0.099, T loss=0.955, He-3 loss=0.129, f_n,eff=0.128.

## Claim boundary

The present result is a falsifiable reduced-order engineering law:

Selective escape requires simultaneous orbital ordering, compact source formation, prompt escape relative to scattering, acceptable electrostatic distortion, and an effective neutron fraction below the mission ceiling.

The next decisive validation step is self-consistent PIC/hybrid-PIC or equivalent kinetic simulation with realistic FRC/mirror equilibrium, collisions, ambipolar fields, turbulence, and time-dependent compression. If those calculations do not preserve the required L_T/L_He separation, this law remains only a screening relation rather than a viable propulsion mechanism.
