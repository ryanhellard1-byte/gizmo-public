# Hellard modified inertia: action-completion wall

## Current status

The benchmark effective equation

\[
\hat a(\omega)\,\mu\!\left[\mathcal A_H(\omega)/a_H\right]
=\hat F(\omega)/m
\]

with

\[
\theta(y)=\frac{7}{1+6y}
\]

passes the current circular-galaxy, planetary-proxy, and wide-binary-proxy checks. It is **not** yet a proven Euler-Lagrange system.

The discrete two-mode Helmholtz/reciprocity diagnostic in `variational_reciprocity.py` finds a relative cross-Jacobian mismatch of approximately 0.999985 for a representative 10^3 frequency hierarchy. Zero would be reciprocal in that toy diagnostic. Therefore the simple multiplicative effective EOM must not be advertised as having a conventional action completion without additional terms.

## Required next construction

Construct the action first, using symmetric frequency coupling, then derive its equations of motion.

A schematic starting invariant is

\[
Q[x]=\int d\omega\,d\omega'\;
\hat a_i^*(\omega)\,K(\omega,\omega')\,\hat a_i(\omega'),
\]

with

\[
K(\omega,\omega')=K^*(\omega',\omega).
\]

A single global quadratic invariant will probably be too coarse to reproduce mode-specific MOND behavior, so spectral auxiliary variables or a family of symmetric mode-window invariants may be required.

## Non-negotiable requirements

1. Galilean invariance in the nonrelativistic limit.
2. Time-translation invariance and an explicit conserved energy functional.
3. Symmetric second variation / Helmholtz reciprocity.
4. Deep circular limit `a^2/a_H = g_N`.
5. BTFR `v^4 = G M a_H`.
6. Newtonian recovery for high-acceleration internal Solar-System motion.
7. Derive, rather than suppress by assumption, all cross-frequency reaction terms.
8. Recompute the anisotropic Solar-System response and Cassini-scale quadrupole from the derived EOM.
9. Re-run SPARC and wide-binary gates with one universal parameter set.

## Kill criterion

If every reciprocal action completion that recovers the galaxy branch necessarily produces Solar-System or wide-binary leakage above observational limits, this branch is non-viable and should be closed rather than rescued by dataset-specific screening parameters.

## Claim discipline

The current work supports an explicit, falsifiable **effective modified-inertia hypothesis**. It does not establish a fundamental theory of gravity, a quantum completion, or a discovered law of nature.
