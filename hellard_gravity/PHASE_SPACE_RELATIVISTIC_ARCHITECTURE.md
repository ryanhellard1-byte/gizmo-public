# Covariant phase-space architecture for Hellard memory

## Why phase space is required

The Hellard trigger is built from trajectory-frequency content. A stationary spacetime field
does not encode the orbital frequencies of a multi-stream stellar system. A collisionless
galaxy also does not possess one unique matter four-velocity field u^a(x).

Therefore the natural covariant continuum description is phase space.

Let f(x,p) be a distribution on the mass shell and let L be the Liouville/characteristic
operator associated with the physical particle dynamics.

For each phase-space characteristic introduce scale-free memory variables M_lambda(x,p)

    L M_lambda + lambda M_lambda = lambda X(x,p)

with measure d ln lambda.

The driver X is the magnitude of the aether-relative acceleration

    mathfrak_a^a = c^2 h^a_b u^c nabla_c q^b,
    q^a = h^a_b u^b,
    h^a_b = delta^a_b + A^a A_b.

Its static weak-field geodesic limit is |grad Phi|.

Higher-order scale localization is formed using derivatives with respect to ln lambda,
for example

    B_lambda = (partial_ln_lambda^2 - partial_ln_lambda) M_lambda,

whose fast-to-slow leakage falls as R^-4.

## Matter and gravity

The full generally covariant action should contain

    S = S_grav[g,A,phi] + S_phase[f,M_lambda; g,A,phi] + S_matter.

The memory contribution to the metric equations is

    T_mem_ab = -(2/sqrt(-g)) delta S_phase / delta g^ab.

Joint diffeomorphism invariance then implies covariant conservation of the total stress
tensor when the field equations hold.

## Lensing requirement

A phase-space memory sector localized only on particle characteristics is not enough by
itself to create an extended halo-like lensing potential. Either:

1. the memory sector must source a propagating scalar/vector mediator whose stress/field
   extends beyond the baryons; or
2. it must alter the universal physical metric to which both matter and photons couple.

The mediator must reproduce the weak-field target in
DEEP_HELLARD_LENSING_TARGET.md.

## Open proof obligations

- construct a local/in-in parent action for f and the memory continuum;
- derive the modified characteristic equations from that action;
- prove positivity/stability of the coupled phase-space/memory sector;
- derive the weak-field Hellard closure rather than imposing it;
- verify universal photon and matter coupling;
- derive cosmological perturbations and tensor/vector/scalar spectra.
