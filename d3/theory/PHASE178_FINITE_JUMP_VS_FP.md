# Phase 178 — Finite-Jump Action Dynamics versus Fokker–Planck

## Verdict

**FINITE-JUMP ACTION STRUCTURE: CONFIRMED IN AN ANALYTIC ACTION-SPACE TEST.**

**SECOND-ORDER FOKKER–PLANCK: NOT A CONTROLLED LOW-EXPOSURE REPRESENTATION OF THE TESTED D3 HL JUMP PROCESS.**

**MANY-COLLISION GAUSSIAN LIMIT: RECOVERED AS EXPECTED.**

**M11 HALO ACCURACY: NOT INFERRED FROM THIS TOY POTENTIAL.**

Phase 177 established that the exact D3 unequal-mass H-L collision produces finite species-asymmetric velocity, energy, and angular-momentum jumps. Phase 178 asks the next question: after mapping those exact collisions into orbital actions, how much information is lost if the collision master equation is truncated after the first two Kramers–Moyal moments?

The test deliberately uses a spherical harmonic potential rather than the M11 halo because the radial action is analytic. This removes numerical action-inversion error from the comparison.

## 1. Analytic action map

For

```text
Phi(r) = 0.5 Omega^2 r^2,
```

the spherical harmonic oscillator satisfies

```text
E = Omega (2 J_r + L)
```

and therefore

```text
J_r = (E/Omega - L)/2.
```

The Phase178 test uses

```text
Omega = 80 km/s/kpc
r_collision = 1 kpc
m_H/m_L = 3
sigma_H = 60 km/s
sigma_L = sqrt(3) sigma_H
```

so the two local Gaussian velocity populations have the same kinetic temperature, `m_H sigma_H^2 = m_L sigma_L^2`.

Candidate encounters are weighted by the physical D3 H-L rate factor

```text
g sigma_HL(g)
```

with

```text
sigma_HL(g) = 1.125 / [1 + (g/2200 km/s)^2] cm^2/g
```

on the frozen heavy-mass basis. Scattering angles are sampled from the exact D3 Rutherford inverse CDF.

## 2. What a second-order FP truncation keeps

For an exact local compound-Poisson jump process with mean collision exposure `Lambda`, let `Y=Delta J_r` be one collision jump. Its cumulants are

```text
kappa_n = Lambda E[Y^n].
```

A second-order Fokker–Planck/Kramers–Moyal truncation keeps only

```text
kappa_1 = Lambda E[Y]
kappa_2 = Lambda E[Y^2]
```

and sets the higher local generator moments to zero.

The exact compound-Poisson standardized third and fourth cumulants are therefore

```text
gamma_1 = E[Y^3] / [sqrt(Lambda) E[Y^2]^(3/2)]

gamma_2 = E[Y^4] / [Lambda E[Y^2]^2].
```

They decay as `Lambda^-1/2` and `Lambda^-1`, respectively. That is the expected central-limit trend. The question is how large they are before that limit.

## 3. Deterministic 120,000-sample result

The CI run uses 120,000 candidate H-L pairs, giving an effective collision-weighted sample size of about 102,507.

Mechanical checks pass:

```text
max pair momentum residual      = 3.84e-16
max pair total-energy residual  = 9.48e-16
minimum computed J_r            = 3.92e-6 > 0
common-temperature relative err = 2.22e-16
```

### Heavy species H

Weighted one-event radial-action jump statistics give

```text
P(|Delta J_r| / I_pre > 0.10) = 0.41515
P(|Delta J_r| / I_pre > 0.25) = 0.11335
```

where `I_pre=E/Omega=2J_r+L` is the positive total harmonic action scale.

The exact compound-Poisson non-Gaussian cumulants are

| Lambda | standardized kappa3 | standardized kappa4 |
|---:|---:|---:|
| 0.1 | -0.3798 | 86.7924 |
| 0.3 | -0.2193 | 28.9308 |
| 1 | -0.1201 | 8.67924 |
| 3 | -0.06934 | 2.89308 |
| 10 | -0.03798 | 0.867924 |
| 30 | -0.02193 | 0.289308 |
| 100 | -0.01201 | 0.0867924 |

### Light species L

```text
P(|Delta J_r| / I_pre > 0.10) = 0.56856
P(|Delta J_r| / I_pre > 0.25) = 0.21396
```

and

| Lambda | standardized kappa3 | standardized kappa4 |
|---:|---:|---:|
| 0.1 | 0.2741 | 73.1920 |
| 0.3 | 0.1583 | 24.3973 |
| 1 | 0.08668 | 7.31920 |
| 3 | 0.05005 | 2.43973 |
| 10 | 0.02741 | 0.731920 |
| 30 | 0.01583 | 0.243973 |
| 100 | 0.008668 | 0.0731920 |

A Gaussian diffusion surrogate with the same drift and variance has standardized third and fourth cumulants equal to zero by construction.

## 4. Interpretation

This establishes a precise local statement.

At low collision exposure, the tested D3 H-L action process is not well described as a collection of infinitesimal Gaussian action increments. Individual accepted collisions frequently move a particle by an appreciable fraction of its orbital action, and the compound jump distribution retains large non-Gaussian fourth cumulants.

This explains why a finite-jump master operator is the safer formal starting point for D3:

```text
finite collision law
      -> finite (Delta E, Delta L)
      -> finite Delta J
      -> gain-loss master equation
```

rather than assuming from the outset

```text
finite collision law -> drift + diffusion only.
```

The result does **not** say that a Fokker–Planck approximation is useless. The exact higher standardized cumulants decrease with increasing collision exposure exactly as the central limit theorem predicts. In this controlled test they become small only after many collisions. Whether a particular halo region is in that many-collision regime is an empirical/local question.

The value `0.10` used by the code to report an illustrative Gaussianity exposure is only a descriptive yardstick. It is not a preregistered D3 physics acceptance threshold.

## 5. Why this matters for the action-space theory

Phase 146 already showed that an isotropic `f(E)` closure can leave the realizable manifold. Phase 147 showed that angular momentum must be retained. Phase 177 established exact unequal-mass action-driving jumps. Phase 178 now shows that, at finite collision exposure, retaining only the first two jump moments can discard substantial information even when the action itself is computed exactly.

The natural reduced equation therefore remains the finite-jump action-space gain-loss equation

```text
partial_t F_a(J) = C_a^jump[F_H,F_L;Phi]
```

coupled to the common gravitational potential. A diffusion equation may emerge as a controlled limiting approximation in regions with sufficiently large effective collision exposure, but it should be derived from the jump operator rather than assumed globally.

## Claim boundary

Phase178 is an analytic-potential collision/action diagnostic. It is not a self-gravitating M11 calculation and does not determine the 10-Gyr or 80-Gyr halo profile.

The strongest defensible statement is:

> For the frozen D3 unequal-mass H-L Rutherford law, exact action jumps in a controlled spherical system are large and strongly non-Gaussian at low collision exposure. A second-order Fokker–Planck generator therefore omits substantial finite-jump information in that regime, while the expected Gaussian limit emerges after many collisions. This supports using a finite-jump action-space Boltzmann/master operator as the primary reduced theory and treating diffusion as a derived limit.

The quantitative self-gravitating D3 halo prediction remains subject to the frozen live-GIZMO production, convergence, and blind-analysis campaign.
