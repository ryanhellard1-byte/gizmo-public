# Aether-relative acceleration weak-field theorem

Let A^a be a unit timelike vector field, A^a A_a = -1, and define the spatial projector

h^a_b = delta^a_b + A^a A_b.

For a massive particle with four-velocity u^a define the aether-relative spatial
four-vector

q^a = h^a_b u^b.

Define the covariant aether-relative acceleration observable

mathfrak_a^a = c^2 h^a_b u^c nabla_c q^b.

This is not the particle's proper four-acceleration. It measures the change of spatial
velocity relative to the preferred observer congruence.

## Geodesic weak-field limit

Write gamma = -A_a u^a, so q^a = u^a - gamma A^a.

If the particle is geodesic,

u^c nabla_c u^a = 0.

Then

u^c nabla_c q^a
 = -(d gamma/d tau) A^a - gamma u^c nabla_c A^a.

Projection with h^a_b kills the term parallel to A^a, giving

mathfrak_a^a
 = -c^2 gamma h^a_b u^c nabla_c A^b.

For a slowly moving particle relative to a static aether congruence, gamma approximately 1
and u^a approximately A^a, hence

mathfrak_a^a approximately -c^2 A^c nabla_c A^a.

In a static weak-field metric

g_00 = -(1 + 2 Phi/c^2) + O(c^-4),

the four-acceleration of the static observer congruence is

A^c nabla_c A^i = partial_i Phi / c^2 + O(c^-4).

Therefore

mathfrak_a^i = -partial_i Phi + higher-order corrections.

Thus

|mathfrak_a| approximately |grad Phi|,

which is the Newtonian gravitational-acceleration variable used in the isolated
Hellard branch.

## Significance

A memory functional built from mathfrak_a^a can be covariant and still reduce to the
Newtonian acceleration scale in a static galaxy. Using proper four-acceleration would fail,
because geodesic proper acceleration vanishes.

## Caveats

The exact expression contains velocity-dependent terms through u^a nabla_a A^b, and a
modified-inertia trajectory is not exactly geodesic. The full relativistic action must be
varied self-consistently. This theorem establishes only the leading weak-field geodesic
matching.
