# Hellard Hybrid Electromagnetic Resource Theorem — Novelty Verdict

Date: 2026-09-09

## Bottom-line verdict

A targeted literature and patent search found substantial prior art for the major ingredients of the theorem, but did **not** locate the same combined electromagnetic resource theorem or the same exact Hellard-Mie rank/strength thresholds.

Therefore the current defensible status is:

**Mathematical correctness:** established internally under the stated assumptions.

**Electromagnetic mapping:** established internally and consistent with standard scattering/optical-theorem theory.

**Historical novelty:** plausible and presently unrefuted, but not proven by search alone.

**Priority claim:** should remain provisional until expert prior-art review and external peer review.

---

## Prior art that clearly exists

### 1. Low-rank matrix approximation

Eckart-Young-Mirsky and later generalized matrix-nearness literature already provide singular-value-based solutions to low-rank Frobenius approximation problems, including extensions with norm constraints. The Hellard theorem must therefore not claim invention of SVD low-rank approximation itself.

### 2. Scattering matrix, passivity and optical theorem

Classical scattering theory already relates passivity/unitarity to scattering operators and optical-theorem power balance. Modern electromagnetic operator-bound literature uses scattering/T operators plus conservation of power to derive limits on scattering, absorption, extinction and optical transformations.

### 3. Active electromagnetic cloaking

Active cloaking by equivalent surface currents, discrete electric/magnetic dipoles, multipole sources, Huygens surfaces and antenna arrays is well established. Experimental electromagnetic active cloaks have been demonstrated.

Selvanayagam and Eleftheriades explicitly determine the minimum number of dipoles in one 2-D implementation from Nyquist sampling of the required surface-current distribution. Norris, Amirkulova and Parnell, and related active-exterior-cloaking work, show that a small number of ideal multipole source locations can cloak prescribed regions in scalar wave problems.

### 4. Electromagnetic degrees of freedom

Modern work by Gustafsson and collaborators relates the number of dominant electromagnetic modes/degrees of freedom of electrically large radiating/scattering objects to shadow area measured in wavelength-squared units. Thus area-like `(ka)^2` modal scaling is not itself new.

---

## Result not located in the targeted search

The searches did not find a prior publication or patent presenting the following combined chain as a sharp class theorem:

1. define a fixed-reference passive deviation operator `D = I - S0^† S`;
2. use aggregate reference-relative extinction burden `L = 2 Re tr D` (or a lower bound on it);
3. constrain an active correction simultaneously by `rank(A) <= r` and `||A||_F <= B`;
4. minimize over the entire passive class to obtain a sharp universal lower envelope `E_H(N,r,L,B)`;
5. derive the separate perfect-correction resource thresholds

   `r >= L/4`

   and

   `B >= L/(2 sqrt(r))`;

6. combine the theorem with exact Lorenz-Mie extinction, `L = 2 (ka)^2 Q_ext`, to obtain

   `r >= (ka)^2 Q_ext / 2`

   and

   `B >= (ka)^2 Q_ext / sqrt(r)`.

No equivalent formulation was found under searches using combinations of: active cloaking, extinction, scattering matrix, T-matrix, singular values, rank, Frobenius norm, resource bounds, Mie coefficients, source number, antenna count, degrees of freedom, matrix nearness, optical theorem and passivity.

---

## Important distinction from closest neighbors

The active-cloak Nyquist source-count condition is a sampling condition for a particular surface-current representation. It depends on the spatial bandwidth of the desired equivalent current.

The Hellard rank threshold is instead a class-envelope condition derived from the aggregate passive extinction burden and an abstract correction-operator rank. It does not prescribe a particular surface discretization or actuator geometry.

Likewise, electromagnetic degrees-of-freedom results estimate the number of significant radiating/scattering modes from geometry and wavelength. They do not, in the sources located, give the Hellard extinction-to-active-rank/strength value function.

The similarities in area scaling are physically important ancestry, not evidence of identity.

---

## Recommended novelty claim

A manuscript should not say:

> We discovered the first law showing that larger electromagnetic objects require more active sources.

That would be false or at least badly overstated.

A defensible provisional claim is:

> We derive a sharp finite-dimensional passive-class lower envelope for residual electromagnetic deviation under simultaneous active-rank and Frobenius-strength constraints, parameterized only by an aggregate reference-relative extinction burden. Combining the envelope with exact Lorenz-Mie extinction yields explicit necessary active-resource thresholds for homogeneous spheres.

The candidate novel equations are therefore the class value function `E_H(N,r,L,B)` and its extinction-coupled consequences, not SVD approximation, optical-theorem physics, active cloaking, source sampling, or area-like electromagnetic degree-of-freedom scaling individually.

---

## Current status language

Use:

**Hellard Hybrid Electromagnetic Resource Theorem — candidate novel theorem, mathematically proved under stated assumptions, with no equivalent result located in the present targeted literature/patent search.**

Do not yet use:

**universally new law of nature**

or

**first-ever theorem**

without an independent expert prior-art review.

---

## Falsification / novelty failure conditions

The novelty claim fails if an earlier source is found that is mathematically equivalent after change of notation, even if it is not described as cloaking. In particular, an earlier result would count as equivalent if it combines:

- a contractive/passive scattering operator or equivalent optical-theorem burden;
- an aggregate trace/extinction constraint;
- simultaneous low-rank and norm-bounded active correction;
- a sharp class minimization producing the same piecewise value function or equivalent thresholds.

A paper giving only one or two of these ingredients is prior ancestry, not necessarily anticipation of the combined theorem.

## Verdict

**No exact prior-art match was found in the targeted search. The Hellard extinction-to-active-resource envelope remains a plausible original contribution. Historical uniqueness is not established until external expert review is completed.**
