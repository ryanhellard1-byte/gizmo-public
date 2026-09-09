# HELIOS-R28: 3-D Mirror Selective Escape Screen

Status: reduced-order single-particle transport result, not a full plasma proof.

## Purpose

Test whether the R27 triton/He-3 selectivity survives explicit 3-D motion with axial losses in a divergence-free near-axis analytic magnetic mirror field.

## Particle model

D-D products:

- triton: 1.01 MeV, q=+e
- He-3: 0.82 MeV, q=+2e

The Larmor-radius ratio is approximately

r_LT/r_LHe = 2*sqrt(1.01/0.82) ~= 2.22.

Particles are born isotropically from a core-weighted Gaussian source and advanced with a Boris pusher under the Lorentz force. Absorbing boundaries are imposed at radial radius R and axial half-length L.

Analytic mirror field near axis:

Bz = B0 [1 + (M-1) z^2/L^2]
Br = -B0 (M-1) r z/L^2

which satisfies div B = 0 in the near-axis model.

## AWS discovery sweep

60 configurations were screened over source widths, B0, mirror ratios and axial aspect ratios. One stretch-gate point:

- R = 1.9 mm
- source sigma = 0.08 R
- B0 = 150 T
- mirror ratio M = 4
- L = 2 R

returned approximately:

- triton prompt loss: 96.7%
- He-3 prompt loss: 10.0%
- triton radial loss: 71.7%
- triton axial loss: 25.0%
- He-3 axial loss: 10.0%

Eight sampled configurations met the robust gate L_T >= 70% and L_He <= 15%. One met the stretch gate L_T >= 80% and L_He <= 10% in the coarse AWS sweep.

## Higher-statistics local confirmation

A 1500-particle-per-species rerun at B0=150 T, M=4, L=2R gave:

- sigma=0.08R: T loss 97.7%, He-3 loss 14.1%
- sigma=0.12R: T loss 97.0%, He-3 loss 15.4%
- sigma=0.16R: T loss 96.0%, He-3 loss 19.7%
- sigma=0.20R: T loss 95.8%, He-3 loss 23.1%

A 5% constant transverse field-error perturbation at sigma=0.08R left:

- T loss 97.3%
- He-3 loss 13.0%

Thus core localization is a hard requirement. Broadening the source degrades He-3 retention much faster than it harms triton loss.

## Effective neutron fraction

For triton prompt loss L_T and He-3 prompt loss L_He, assume retained T later burns by DT and retained He-3 later burns by D-He3. Then

f_n,eff = [2.45 + 14.1(1-L_T)] / [7.30 + 17.6(1-L_T) + 18.3(1-L_He)].

At the higher-statistics sigma=0.08R reference point:

- L_T = 0.9767
- L_He = 0.1413

this gives f_n,eff ~= 11.9%.

Even sigma=0.20R gives f_n,eff ~= 13.8% in this simplified bookkeeping because triton prompt loss remains very high.

## Hellard selective-escape boundary

Given an allowable neutron fraction f*, the minimum triton prompt-loss fraction for a specified He-3 loss is

L_T,min = 1 - { f*[7.30 + 18.3(1-L_He)] - 2.45 } / { 14.1 - 17.6 f* }

for 14.1 - 17.6 f* > 0.

This is the R28 algebraic selective-product-escape boundary.

## Claim boundary

This screen does NOT include:

- self-consistent electric fields
- Coulomb collisions or pitch-angle scattering
- plasma pressure/current modification of the imposed field
- turbulence or MHD perturbations
- wall/sheath interaction
- charge exchange
- time-dependent compression or field evolution
- realistic FRC separatrices

Therefore R28 is not proof of a working species separator. It is evidence that the R27 mechanism survives the first explicit 3-D axial-orbit attack in an analytic mirror field.

## Next required solver

The next calculation should use self-consistent electromagnetic fields from an FRC/mirror equilibrium and full-orbit particles, then add collisions and field perturbations. The pass gates remain:

- L_T >= 70% minimum, >=80% preferred
- L_He <= 15% minimum, <=10% preferred
- f_n,eff <= 24% minimum, <=18% preferred
- source width sigma <= 0.15R preferred
