# Hellard Hybrid Electromagnetic Resource Law — Lossy and Multilayer Validation

## 1. Lossy dielectric-cylinder validation

An exact 2-D scalar TM_z-like cylindrical partial-wave model was used for absorbing dielectric cylinders with complex refractive index. For each cylindrical harmonic m, the scattering eigenvalue was written as

S_m = 1 + 2 a_m,

with a_m obtained from exact Bessel/Hankel boundary matching.

The reference-deviation channel was

D_m = 1 - S_m,

and normalized extinction

X_m = 2 Re(D_m).

For passive absorbing channels,

X_m - |D_m|^2 = 1 - |S_m|^2 >= 0.

Tested material families included weak, moderate, strong, and high-index loss across ka = 0.5, 1, 2, 3, 5, 8 with multiple active-rank fractions.

Results:
- 96 physical lossy test cases
- 0 violations of the Hellard lower bound
- maximum optical/passivity identity error approximately 8.9e-16

This extends validation beyond lossless unitary scattering to genuinely contractive passive scattering.

## 2. Multilayer passive+active validation

A concentric multilayer cylindrical model was then built using exact radial transfer matrices. Geometry:

- lossy dielectric core radius a = 1
- two passive shells with outer radii 1.35 and 1.70
- core refractive index n_core = 2.5 + 0.08 i

Two shell refractive indices were optimized at design electrical size ka = 2.5 subject to passive loss constraints.

Optimized values:

n_shell1 = 1.256338551455561 + 0 i
n_shell2 = 0.8873386386801392 + 0 i

At the design frequency:

L_bare = 10.27724572218067
L_cloaked = 10.001228579609093

so

L_cloaked / L_bare = 0.9731428876925782

corresponding to approximately -0.118 dB reduction in total normalized extinction.

The passive cloak is modest, not impressive, but that makes this a useful coupled passive+active validation rather than a hand-picked near-perfect cloak.

An optimal finite-rank, finite-Frobenius-strength active corrector was then applied to the actual modal deviation operator of the passively cloaked structure.

Results:
- 32 coupled passive+active test cases
- 0 violations of the Hellard lower bound
- smallest actual-minus-bound margin approximately 1.38036
- passivity identity satisfied to numerical precision

## Interpretation

The Hellard law is an abstract best-case envelope. A particular physical scatterer has a fixed modal spectrum and therefore generally lies above the abstract optimum.

The validation chain now includes:

1. lossless PEC cylinders,
2. broadband PEC cylinders,
3. lossy dielectric cylinders with strictly contractive channels,
4. multilayer passive cloaks followed by finite-rank active correction.

No tested physical case has violated the theorem.

This is evidence, not proof of universal physical novelty. The theorem itself is mathematical; physical validation tests whether actual Maxwell scatterers obey the assumptions and remain above the predicted resource envelope.
