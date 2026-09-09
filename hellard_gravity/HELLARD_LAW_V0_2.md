# Hellard Spectral-Dominance Law candidate v0.2

## Status

Research hypothesis. Not an established law of nature.

## Core statement

A dynamical degree of freedom departs from Newtonian inertia only when its acceleration is low and its causal scale-localized motion is dynamically dominant over slower environmental motion. Faster internal motion is effaced from slower center-of-mass dynamics by a scale-free causal memory hierarchy.

## Isolated circular branch

    a mu(a/a_H) = g_N,

with

    mu(x) = x/sqrt(1+x^2)

and current SPARC all-points fit

    a_H = 1.12e-10 m/s^2.

The deep isolated limit gives

    a ~= sqrt(a_H g_N)

and therefore

    v^4 = G M a_H.

## Causal scale-free spectrometer

Use a continuum of boost-covariant velocity-memory variables

    du_lambda/dt + lambda u_lambda = lambda v(t),   lambda > 0,

with measure d ln lambda. Under a Galilean boost v -> v+V, u_lambda -> u_lambda+V.

The logarithmic-scale derivative q_lambda = d u_lambda/d ln lambda and c_lambda = d q_lambda/dt give the normalized harmonic acceleration-power band

    |c_lambda|^2/|A|^2
      = omega^2 lambda^2/(lambda^2+omega^2)^2,

with

    2 int_0^infinity |c_lambda|^2 d ln lambda = |A|^2.

The higher-order band has exact kernel

    K_2(x) = 4 x^4/(1+x^2)^3

and fast-to-slow leakage K_2(1/R) ~ 4/R^4.

## Composite effacement

For scale-separated fast internal displacement spectrum xi(omega) and slow COM displacement scale L,

    epsilon_CM <= 4 <xi^2>_ln / L^2.

Thus large internal accelerations do not automatically contaminate slow COM motion; the asymptotic bound is geometric.

## Empirical status frozen at v0.2

SPARC all-points circular RAR:

    N = 2693
    best a_H = 1.12e-10 m/s^2
    chi2/dof = 1.6205
    RMS = 0.1329 dex.

First real Gaia DR3 pure-sample shape diagnostic:

    catalog rows = 2463
    quality-selected systems = 1494
    outer-shape chi2 Newtonian = 23.890
    outer-shape chi2 Hellard v0.1 comparator = 22.463
    Delta chi2(H-N) = -1.427.

This is a survival result, not a detection. The Gaia calculation is still a quasi-Kepler shape test rather than the final nuisance-marginalized causal-memory likelihood.

## Proven no-go results within the program

1. Universal diagonal low-acceleration inertia fails wide binaries.
2. Direct asymmetric spectral equations generically fail action reciprocity.
3. Linear spectral-power mixing cannot recover an exact multimode Newtonian limit with nonzero cross-coupling.
4. Finite constant-rate memory fields introduce forbidden preferred clocks in an exactly scale-free construction.
5. A Gaussian harmonic bath with only linear system-bath coupling cannot generate the required amplitude-nonlinear isolated inertia law.

## Open fatal gates

1. Derive a conservative nonlinear/interacting continuum parent or a controlled in-in parent theory.
2. Replace the quasi-Kepler Gaia comparator with a full causal-memory many-body likelihood including measurement covariance, hierarchical triples, eccentricity population and Galactic-environment variation.
3. Run full Solar-System ephemeris likelihood, not only reduced high-acceleration/Cassini proxies.
4. Construct a relativistic completion that explains lensing while preserving acceptable gravitational-wave propagation and degrees of freedom.
5. Confront clusters, CMB and structure formation.

Only after those gates are passed should the candidate be promoted beyond a nonrelativistic phenomenological law proposal.
