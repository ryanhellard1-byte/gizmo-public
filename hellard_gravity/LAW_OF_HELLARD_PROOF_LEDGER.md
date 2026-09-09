# Law of Hellard proof ledger

This file is the canonical claim boundary for the research branch.

A claim may be marked only as:

- PROVED: derived analytically within the stated mathematical model;
- EMPIRICAL PASS: survived the named reproducible data/CI test;
- OPEN: not yet established;
- RULED OUT: a tested construction or claim failed.

## Core nonrelativistic branch

### Isolated low-acceleration relation
Status: PROVED within candidate.

a mu(a/a_H)=g_N,
mu(x)=x/sqrt(1+x^2).

Deep limit:

a approximately sqrt(a_H g_N).

For circular motion around an isolated spherical mass:

v^4 = G M a_H.

### Acceleration scale
Status: EMPIRICAL PASS.

SPARC all-points fit:
a_H approximately 1.12e-10 m/s^2.
Current CI all-points statistic:
chi2/dof approximately 1.6205,
RMS approximately 0.1329 dex.

This validates the circular low-acceleration branch shape, not the full spectral mechanism.

## Spectral / causal structure

### Finite constant-rate memory completion
Status: RULED OUT as an exactly scale-free fundamental mechanism.

A finite set of fixed relaxation rates introduces new dimensional clocks.

### Scale-free continuum memory
Status: PROVED at linear filter level.

d m_lambda/dt + lambda m_lambda = lambda a(t),
with measure d ln lambda.

For harmonic input, the logarithmic derivative reconstructs normalized acceleration power.

### Higher-order causal band
Status: PROVED.

b_lambda=(partial_ln_lambda^2-partial_ln_lambda)m_lambda

has normalized harmonic kernel

K2(x)=4 x^4/(1+x^2)^3.

Fast-to-slow leakage scales as R^-4.

### Geometric many-body effacement
Status: PROVED asymptotically for scale-separated harmonic/incoherent modes.

Fast internal contamination of slow center-of-mass power obeys a geometric bound of order

epsilon <= 8 sum_j (ell_j/L)^2

under the assumptions recorded in MANY_BODY_EFFACEMENT_BOUND.md.

Arbitrary resonant/broadband nonlinear systems remain OPEN.

### Conservative parent for linear memory
Status: PROVED as a representation.

Each exponential relaxation kernel admits a positive oscillator spectral representation.
The exact nonlinear Hellard coupling to that bath remains OPEN.

## Symmetry

### Galilean symmetry
Status: PROVED for nonrelativistic functionals built from acceleration histories,
time differences and rotational scalars.

### Point-particle weak equivalence principle
Status: PROVED conditionally.

If the same mass-proportional universal kinetic functional is used for every composition,
test mass cancels from the nonrelativistic equation of motion.

Strong-equivalence/composite self-gravity remains OPEN.

## Solar System

### High-acceleration reduced-model suppression
Status: EMPIRICAL/NUMERICAL PASS in current CI.

### Cassini
Status: OPEN at full ephemeris-likelihood level.

Reduced and action-level proxies are safely small, but no full Solar-System ephemeris fit
has yet been performed.

## Wide binaries

### Reduced stress tests
Status: EMPIRICAL/NUMERICAL PASS.

### Exact two-mode action stress
Status: EMPIRICAL/NUMERICAL PASS.

Current frozen two-mode action predicts only few-percent deviations over the tested grid.

### Real Gaia DR3 shape test
Status: EMPIRICAL PASS, NO DETECTION.

Selected systems: 1494.
Outer-bin shape scores:
Newtonian chi2 = 23.890.
Hellard chi2 = 22.463.
Delta chi2(H-N) = -1.427.

This is only a weak approximate 2:1 fixed-shape likelihood preference and is not
statistically compelling.

Full nuisance-marginalized likelihood remains OPEN.

## Relativistic completion

### Pure modified inertia with unmodified baryon-only metric
Status: RULED OUT as a complete dark-matter replacement because it cannot generate
the required extra lensing.

### Naive static-field covariant memory
Status: RULED OUT.

A stationary galaxy field does not encode the stellar trajectory frequency hierarchy.

### Aether-relative acceleration weak-field matching
Status: PROVED to leading weak-field geodesic order.

The projected change of spatial velocity relative to a static aether congruence reduces
to -grad Phi.

### Phase-space covariant architecture
Status: OPEN but structurally motivated.

Memory must live on matter characteristics / phase space to preserve trajectory-frequency
information in multi-stream galaxies.

### Luminal tensor scaffold
Status: AVAILABLE FROM PRIOR ART, not a Hellard result.

Known tensor-vector-scalar relativistic MOND classes exist with c_T=c. A Hellard
completion must embed inside such a healthy branch or satisfy equivalent constraints.

### Deep lensing target
Status: PROVED as a required weak-field consequence if Phi approximately Psi.

Deep force:
g_H=sqrt(G M a_H)/r.

Required equivalent density:
rho_eff=sqrt(G M a_H)/(4 pi G r^2).

Asymptotic deflection:
alpha=2 pi sqrt(G M a_H)/c^2.

Producing this from a stable covariant Hellard action remains OPEN.

## Clusters

### Current nonrelativistic spectral-dominance branch as a total dark-matter replacement
Status: RULED OUT.

The environmental mechanism only suppresses the isolated MOND-like enhancement, so
a_Hellard <= a_isolated.

Systems requiring more gravity than the isolated branch cannot be fixed by spectral
suppression alone.

A new relativistic mediator/stress contribution or residual matter is required.

## Cosmology

CMB background/perturbations: OPEN.
Matter power spectrum: OPEN.
Nonlinear structure formation: OPEN.
BBN consistency: OPEN.
Strong lensing/cluster cosmology: OPEN.
Black holes/neutron stars: OPEN.
Quantum completion: OPEN.

## Current allowed claim

The strongest defensible claim today is:

'Hellard spectral-dominance dynamics is a falsifiable nonrelativistic modified-inertia
candidate with a causal scale-free memory construction, analytic fast-mode effacement,
a successful galaxy RAR branch, and no current exclusion from the tested Solar-System
or Gaia wide-binary diagnostics.'

The following claim is NOT currently allowed:

'Hellard's Law is a proven fundamental law of gravity or a complete solution to dark
matter, dark energy, lensing, clusters, and cosmology.'

## Promotion rule

The project may be promoted from 'candidate' to 'relativistic theory candidate' only
after:

1. explicit covariant action;
2. complete tensor/vector/scalar constraint and stability analysis;
3. derivation of the Hellard nonrelativistic limit from that action;
4. correct galaxy lensing from the same parameters;
5. luminal gravitational waves;
6. full Solar-System likelihood;
7. full nuisance-marginalized wide-binary likelihood;
8. viable cluster treatment;
9. viable CMB and structure formation.

It may be called an experimentally established law only after independent observational
tests discriminate it successfully from GR+dark matter and competing modified-gravity
models.
