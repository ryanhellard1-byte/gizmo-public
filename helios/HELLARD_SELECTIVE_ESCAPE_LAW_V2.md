# Hellard Selective-Escape Law v2

## Scope

This is a derived engineering closure law for magnetically selective loss of fast fusion products. It is not claimed as a fundamental law of nature.

## 1. Fast-product orbit ratio

For species s with mass m_s, charge q_s, kinetic energy E_s, and local magnetic field B,

r_L,s = sqrt(2 m_s E_s) / (|q_s| B).

For D-D products T(1.01 MeV,+e) and He-3(0.82 MeV,+2e),

kappa = r_L,T / r_L,He3 = 2 sqrt(1.01/0.82) = 2.219646...

## 2. Corrected passive radial-loss bound

For a particle born on axis in a uniform B field, the guiding center is displaced from the birth point. Maximum radial excursion is about 2 r_L for a 90-degree pitch particle, not r_L.

For isotropic velocity directions, define h as the allowed prompt He-3 radial loss fraction. The maximum triton radial-loss fraction achievable by gyro-radius selectivity alone is

L_T,max^radial(h) = sqrt(1 - (1-h^2)/kappa^2).

For the D-D product pair:

- h=0.05 -> L_T,max^radial = 0.8930
- h=0.10 -> L_T,max^radial = 0.8939
- h=0.15 -> L_T,max^radial = 0.8953
- h=0.20 -> L_T,max^radial = 0.8973

Thus passive uniform-field radial filtering alone cannot deliver arbitrarily high triton loss while preserving He-3.

## 3. Mirror enhancement

A representative 3-D mirror-orbit result gave approximately

L_T = 0.977, L_He3 = 0.141.

At h=0.141 the passive radial bound is only about 0.895. Therefore the mirror topology supplies an additional selective-loss channel of roughly 0.082 absolute triton-loss fraction in that reduced model, largely through axial loss-cone dynamics.

Define the mirror enhancement

Delta_M = L_T - L_T,max^radial(L_He3).

Delta_M > 0 measures separation performance beyond what a uniform-B radial-orbit mechanism can produce.

## 4. Source compactness

Define

chi_H = sigma_fusion / R,

where sigma_fusion is a characteristic fusion-source width and R is the hot-region radius.

A 250,000-case stochastic reduced-order screen that varied B, pitch-scattering time, axial potential, time-dependent B modulation, and source width found:

- chi_H < 0.12: 96.4% of sampled cases passed the hard selective-escape gate
- 0.12 < chi_H < 0.17: 19.3% passed
- chi_H > 0.17: 0% passed

These fractions are design-space fractions from the surrogate model, not probabilities of physical success.

The current reduced-order design target is therefore

chi_H <= 0.12,

with chi_H ~ 0.10 preferred.

## 5. Collision/escape ordering

Define

K_T = tau_escape,T / tau_scatter,T.

Prompt product selectivity requires

K_T << 1,

so that tritons on loss orbits leave before collisional pitch scattering or slowing erases their birth-orbit advantage.

## 6. Neutron-accounting closure

If L_T is prompt triton loss and L_H is prompt He-3 loss, while retained tritium later undergoes D-T burn and retained He-3 contributes D-He3 energy, then

f_n,eff = [2.45 + 14.1(1-L_T)] / [7.30 + 17.6(1-L_T) + 18.3(1-L_H)].

For a mission-allowed neutron fraction f_n,max, define

S_H = f_n,max / f_n,eff.

Selective-escape neutron closure requires

S_H >= 1.

Equivalently, for a prescribed neutron ceiling f*, the minimum triton-loss fraction is

L_T,min = 1 - { f*[7.30 + 18.3(1-L_H)] - 2.45 } / {14.1 - 17.6 f*},

provided 14.1 - 17.6 f* > 0.

## 7. Hellard Selective-Escape Law v2

A magnetically selective fast-product architecture satisfies reduced-order closure only if all four conditions hold simultaneously:

1. favorable species orbit separation, characterized by kappa > 1;
2. a sufficiently compact fusion source, chi_H <= chi_crit;
3. prompt loss faster than collisional randomization, K_T << 1;
4. neutron-accounting closure, S_H >= 1.

For the D-D triton/He-3 pair in the current HELIOS reduced model:

kappa = 2.2196,
chi_crit ~ 0.12,
preferred L_T >= 0.80,
preferred L_He3 <= 0.10-0.15.

The uniform-field radial mechanism has an analytic ceiling near L_T ~ 0.89 for He-3 losses of order 5-15%. Therefore any repeatable result above that ceiling at similar He-3 loss is evidence that mirror/axial/wave-particle topology is adding a second selective-loss mechanism.

## 8. Falsification gates

The criterion should be considered falsified for HELIOS if a self-consistent kinetic calculation or experiment shows one or more of the following under the target conditions:

- chi_H <= 0.12 does not produce preferential triton loss;
- collisions drive K_T to order unity before escape;
- ambipolar/self-consistent electric fields reverse the desired selectivity;
- realistic FRC/mirror topology produces L_He3 above the neutron-closure budget;
- the predicted passive radial ceiling and mirror enhancement fail to describe the measured transition.

## Claim boundary

The algebraic radial bound is derived from charged-particle orbit geometry. The hotspot threshold, mirror enhancement, and robustness values are reduced-order numerical findings and require independent PIC/hybrid-PIC validation and experiment before any claim stronger than an engineering closure law is justified.
