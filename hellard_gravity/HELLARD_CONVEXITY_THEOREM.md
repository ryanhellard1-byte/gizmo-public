# Hellard Convex Spectral-Norm Candidate

## Status
Research hypothesis only. This is not an established law of nature and not a relativistic completion.

## Reduced discrete-mode functional
For dimensionless acceleration amplitudes

x_i = a_i / a_H,

let

Q_i = x_i^2 + beta * sum_{j != i} W(|omega_j/omega_i|) x_j^2,

with beta >= 0 and W(y) >= 0. The benchmark uses

W(y) = 1/(1+y^n),  n=4.

Define

Phi(Q) = sqrt(Q(1+Q)) - asinh(sqrt(Q)),  Q >= 0.

Then

Phi'(Q) = sqrt(Q)/sqrt(1+Q),

Phi''(Q) = 1/[2 sqrt(Q) (1+Q)^(3/2)] > 0 for Q>0.

A reduced kinetic functional is a positive weighted sum of terms Phi(Q_i), for example the periodic-mode average

K_H = (m a_H^2 / 2) sum_i omega_i^{-2} Phi(Q_i),

up to Fourier-normalization conventions.

## Convexity theorem
Each Q_i is a nonnegative weighted sum of squared amplitudes. Therefore Q_i(x) is convex. Phi is nondecreasing and convex on Q>=0. The composition of a convex nondecreasing scalar function with a convex scalar function is convex. Consequently every Phi(Q_i(x)) is convex, and every positive weighted sum of them is convex.

Thus the reduced amplitude-space Hessian of K_H is positive semidefinite wherever the ordinary Hessian exists.

This removes the negative-Hessian instability found in the earlier ratio-gated spectral action.

## Isolated-mode limit
For a single mode, Q=x^2 and variation produces an inertia coefficient

Phi'(x^2)=|x|/sqrt(1+x^2)=mu(|a|/a_H).

Hence circular isolated motion retains

a mu(a/a_H)=g_N.

For a << a_H,

mu(a/a_H) ~ a/a_H,

so

a^2/a_H = g_N

and

v^4 = G M a_H.

## Background-dominated limit
A sufficiently strong slower spectral background increases Q_i through beta B_i. Then Phi'(Q_i) approaches 1, suppressing the low-acceleration modification and returning the internal mode toward Newtonian inertia.

No new dimensional time scale is introduced: W depends only on frequency ratios and a_H remains the only new dimensional acceleration scale in this reduced construction.

## Current numerical benchmark
The first broad scan favors beta roughly 8-16 with n=4. In the sampled domain M=0.5-2 M_sun, separation 3-30 kAU, and local background acceleration 1.4e-10 to 2.0e-10 m/s^2, beta=16,n=4 kept the worst circular-speed deviation below about 1%; beta=8,n=4 was around the percent level and retained a very small Solar-System anomaly.

These are reduced circular-orbit diagnostics, not a full Gaia likelihood.

## Remaining fatal gates
1. Full variational derivation for continuous spectra and real trajectories.
2. Conservation-law derivation with a precise Fourier convention and boundary conditions.
3. Initial-value/causality analysis.
4. Individual wide-binary likelihood from astrometry and radial velocities.
5. Full Solar-System ephemeris fit, not a quadrupole proxy.
6. Composite-body and universality-of-free-fall proof.
7. Relativistic completion giving correct lensing, gravitational-wave propagation, and cosmology.
