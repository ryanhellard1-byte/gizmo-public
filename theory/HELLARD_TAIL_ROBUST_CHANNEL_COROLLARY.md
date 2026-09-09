# Tail-Robust Hellard Channel Corollary

## Motivation

The sharp finite-dimensional envelope `E_H(N,r,L,B)` depends on the number `N` of channels in the passive class. If one artificially pads a model by adding channels on which `D=0`, the fixed physical correction problem is unchanged but the extinction-only class envelope becomes weaker because its ambient dimension increased.

Therefore a physical application should not treat an arbitrary numerical matrix dimension as a fundamental electromagnetic parameter.

The correct bridge is the number of **deviation-bearing scattering singular channels**, together with a controlled unresolved tail.

---

## Setup

Let `D` be an admissible passive deviation operator with singular values

\[
\tau_1\ge\tau_2\ge\cdots\ge0,
\]

and total burden

\[
2\operatorname{Re}\operatorname{tr}D\ge L.
\]

Passivity gives

\[
0\le\tau_i\le2,
\qquad
\sum_i\tau_i\ge L/2.
\]

Let the active correction satisfy

\[
\operatorname{rank}(A)\le r,
\qquad
\|A\|_F\le B.
\]

For a chosen resolved singular-channel count `K`, define the unresolved nuclear tail

\[
\boxed{
\delta_K=\sum_{i>K}\tau_i.
}
\]

and the guaranteed resolved burden

\[
\boxed{
L_K=[L-2\delta_K]_+.
}
\]

Let

\[
r_K=\min(r,K).
\]

---

## Corollary

The exact fixed-system residual obeys

\[
\boxed{
E_{\rm fix}(D;r,B)
\ge
E_H(K,r_K,L_K,B).
}
\]

That is,

\[
\boxed{
E_{\rm fix}(D;r,B)
\ge
E_H\!\left(
K,\min(r,K),[L-2\delta_K]_+,B
\right).
}
\]

This bound is invariant under the addition of arbitrary zero-deviation channels.

---

## Proof

From the nuclear-mass inequality,

\[
\sum_{i=1}^{K}\tau_i
=
\sum_i\tau_i-\delta_K
\ge
L/2-\delta_K
=
L_K/2
\]

whenever `L_K>0`.

For a fixed `D`, the exact active optimum is

\[
E_{\rm fix}(D;r,B)
=
\left[
\left(\sum_{i=1}^{r}\tau_i^2\right)^{1/2}-B
\right]_+^2
+
\sum_{i>r}\tau_i^2.
\]

### Case 1: `r <= K`

Discarding the nonnegative residual contribution from singular values beyond `K` gives

\[
E_{\rm fix}(D;r,B)
\ge
\left[
\left(\sum_{i=1}^{r}\tau_i^2\right)^{1/2}-B
\right]_+^2
+
\sum_{i=r+1}^{K}\tau_i^2.
\]

The first `K` singular values satisfy

\[
0\le\tau_i\le2,
\qquad
\sum_{i=1}^{K}\tau_i\ge L_K/2.
\]

Minimizing the right-hand side over every such `K`-component spectrum is exactly the Hellard class-envelope problem, giving

\[
E_{\rm fix}(D;r,B)\ge E_H(K,r,L_K,B).
\]

### Case 2: `r > K`

The controllable singular-vector norm in the full fixed-system optimum obeys

\[
\left(\sum_{i=1}^{r}\tau_i^2\right)^{1/2}
\ge
\left(\sum_{i=1}^{K}\tau_i^2\right)^{1/2}.
\]

Because `[x-B]_+^2` is nondecreasing in `x`, and because all omitted residual terms are nonnegative,

\[
E_{\rm fix}(D;r,B)
\ge
\left[
\left(\sum_{i=1}^{K}\tau_i^2\right)^{1/2}-B
\right]_+^2.
\]

Minimizing over the same resolved `K`-channel singular spectra gives

\[
E_{\rm fix}(D;r,B)\ge E_H(K,K,L_K,B).
\]

Combining the two cases proves the result.

---

## Exact finite-rank specialization

If

\[
\operatorname{rank}(D)\le K,
\]

then

\[
\delta_K=0
\]

and therefore

\[
\boxed{
E_{\rm fix}(D;r,B)
\ge
E_H(K,\min(r,K),L,B).
}
\]

This formulation depends on the maximum number of deviation-bearing singular channels, not on an arbitrarily padded ambient basis.

---

## Infinite-dimensional consequence

With only a total nuclear-mass/extinction burden and no finite-rank, effective-dimension, or tail constraint, there is no nonzero dimension-free Frobenius residual envelope.

Indeed, distribute singular mass `s=L/2` equally over `M` channels:

\[
\tau_i=s/M,\qquad i=1,\ldots,M.
\]

Then

\[
\sum_i\tau_i=s,
\]

while

\[
\|D\|_F^2=M(s/M)^2=\frac{s^2}{M}\to0
\]

as `M -> infinity`.

Therefore the finite/effective scattering-channel count is not cosmetic. Some physical restriction on modal dimension or unresolved tail is mathematically necessary for a nonzero extinction-only Frobenius bound.

---

## Physical Maxwell interpretation

For spherical-vector-wave descriptions, the exact electromagnetic channel space is infinite, but only a finite range of multipole orders is normally needed to approximate a bounded scatterer to a specified numerical tolerance. A commonly used Mie truncation estimate is the Wiscombe form

\[
\ell_{\max}\approx x+4x^{1/3}+2,
\qquad x=ka.
\]

Through multipole order `ell_max`, the number of electric-plus-magnetic vector spherical channels is

\[
\boxed{
K_{\rm sph}=2\sum_{\ell=1}^{\ell_{\max}}(2\ell+1)
=2\ell_{\max}(\ell_{\max}+2).
}
\]

For electrically large spherical regions this scales approximately as

\[
K_{\rm sph}\sim2(ka)^2.
\]

That scaling is an approximation to the number of retained spherical channels, not a universal exact rank theorem for arbitrary objects. A rigorous physical use of the Hellard envelope should either:

1. establish a true finite-rank scattering model, or
2. bound the singular-value tail `delta_K` and use the tail-robust formula above.

Recent work on finite-modal electromagnetic scattering operators and operator-norm convergence reinforces the need to control modal truncation rather than merely observe adjacent-order numerical agreement.

---

## Conditional active-resource scaling

Suppose a `K`-channel physical model has mean normalized extinction burden

\[
\bar X=L/K.
\]

The class-envelope perfect-correction rank condition

\[
L\le4r
\]

becomes

\[
\boxed{
\frac rK\ge\frac{\bar X}{4}.
}
\]

Thus, if the mean burden per significant channel remains of order unity while the number of significant 3-D spherical channels grows like `(ka)^2`, the required active rank must also grow like `(ka)^2`.

If `r=alpha K`, the strength threshold gives

\[
B^2\ge\frac{L^2}{4r}
=
\frac{\bar X^2}{4\alpha}K.
\]

Hence the squared **effective correction-operator budget** must grow at least linearly with the significant channel count under those assumptions.

This is not automatically amplifier power. A hardware coupling model is required to translate `B` into physical source power.

---

## Status

This corollary repairs the ambient-dimension/padding ambiguity of the finite-channel theorem and supplies a mathematically explicit route from finite-dimensional scattering matrices to converged modal Maxwell models.

It does not by itself prove historical novelty or a universal geometry-to-channel-count law.
