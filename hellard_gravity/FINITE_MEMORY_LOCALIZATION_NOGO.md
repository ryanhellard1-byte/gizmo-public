# Finite-memory localization no-go for a scale-free Hellard response

## Statement

Consider a causal effective modified-inertia completion obtained by eliminating a finite number N of local linear auxiliary memory variables with constant coefficients. Its linearized transfer functions are rational functions of the Laplace/Fourier variable and have a finite set of poles at rates gamma_i.

If the reduced response is required to depend only on frequency ratios and to contain no new dimensional time or frequency scale, then no nontrivial bounded crossover filter can be produced by such a finite auxiliary system unless all finite nonzero gamma_i disappear.

## Reason

A finite autonomous linear memory system may be written

    dot z = A z + B a,
    r = C z + D a.

Its transfer function is

    H(s) = D + C (s I - A)^(-1) B.

The eigenvalues of A are poles with dimensions of inverse time. Any finite nonzero pole gamma_i defines a preferred clock 1/|gamma_i|. Under a global rescaling of time t -> alpha t, a genuinely scale-free response can depend on ratios of frequencies, but a fixed gamma_i transforms into the dimensionless combination omega/gamma_i and therefore breaks the required scale invariance.

Removing every finite nonzero rate leaves poles only at zero or infinity. The resulting finite rational functions reduce to combinations of derivatives, integrals, constants, and power-law monomials; they do not provide the bounded low/high-frequency spectral discrimination required by the Hellard phenomenology without either a new dimensional rate or additional nonlinear/dynamical structure.

## Consequence

A causal Hellard completion with no new dimensional time scale must use at least one of:

1. a continuum of relaxation rates with scale-invariant measure;
2. dynamically generated rates determined by the trajectory/state;
3. a nonlocal doubled/in-in effective action not reducible to finitely many constant-rate auxiliaries.

This is a narrowing theorem for the current research program, not a theorem excluding all modified-inertia theories.
