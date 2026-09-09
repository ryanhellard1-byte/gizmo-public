# Hellard Rank-Strength Resource Law

Date: 2026-09-09

## Status

This document isolates the cleanest exact form of the finite-dimensional Hellard resource envelope and separates the genuinely electromagnetic contribution from classical matrix approximation.

The result is a theorem under the stated abstract scattering assumptions. It is not yet claimed here as a universally new law of nature.

## Setup

Let

\[
Q=S_0^\dagger S,\qquad D=I-Q,
\]

with unitary reference `S0` and passive `S`, so `Q` is contractive. For a complete `N`-channel power-normalized basis define the aggregate extinction burden by

\[
2\operatorname{Re}\operatorname{tr}D\ge L,
\]

and let an active corrector satisfy

\[
\operatorname{rank}(A)\le r,\qquad \|A\|_F\le B.
\]

Define

\[
s=L/2,\qquad z=B\sqrt r.
\]

The exact fixed-system active correction formula is the classical singular-value reduction

\[
E_{\rm fix}(D;r,B)
=[T_r(D)-B]_+^2+\sum_{i>r}\tau_i^2,
\]

where `tau_i` are the singular values of `D` and

\[
T_r(D)=\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}.
\]

The Hellard quantity is the sharp lower envelope over the passive class having only the aggregate burden `L` specified.

## Exact phase law

For `0<r<N`:

### Rank-capable regime

If

\[
s\le 2r
\]

then

\[
\boxed{E_H=\frac{[s-z]_+^2}{N}.}
\]

Equivalently,

\[
\boxed{E_H=\frac{[L/2-B\sqrt r]_+^2}{N}.}
\]

The class envelope reaches zero exactly when

\[
L\le4r
\]

and

\[
B\ge \frac{L}{2\sqrt r}.
\]

Thus perfect correction of an envelope extremizer requires both sufficient controllable rank and sufficient correction strength.

### Rank-overloaded regime

If

\[
s>2r,
\]

define

\[
\boxed{z_c=\frac{r(2N-s)}{N-r}.}
\]

Then

\[
\boxed{
E_H=
\begin{cases}
\dfrac{(s-z)^2}{N},&0\le z\le z_c,\\[2mm]
\dfrac{(2r-z)^2}{r}+\dfrac{(s-2r)^2}{N-r},&z_c<z<2r,\\[2mm]
\dfrac{(s-2r)^2}{N-r},&z\ge2r.
\end{cases}}
\]

The third branch is a pure rank floor. Once the controllable singular channels are fully saturated and fully corrected, additional correction strength cannot remove the burden forced into the remaining `N-r` channels.

## Edge cases

For `r=0`,

\[
\boxed{E_H=\frac{L^2}{4N}.}
\]

For `r=N`,

\[
\boxed{E_H=\frac{[L/2-B\sqrt N]_+^2}{N}.}
\]

## Dimensionless form

For `r>0`, define

\[
\rho=\frac{L}{4r},\qquad \beta=\frac{B}{2\sqrt r}.
\]

The abstract perfect-correction region is

\[
\boxed{\rho\le1,\qquad \beta\ge\rho.}
\]

This gives a natural two-axis rank-strength phase diagram.

## Why the lower clip disappears

The original scalar minimization used

\[
\widehat m=\frac{rs+(N-r)z}{N}
\]

in the active-limited regime. The lower ordering bound is never active because

\[
\widehat m-rs/N=\frac{(N-r)z}{N}\ge0.
\]

The tail-cap lower bound is also never active for `0<=s<=2N` because

\[
\widehat m-[s-2(N-r)]
=\frac{(N-r)(2N-s+z)}{N}\ge0.
\]

Therefore the only nontrivial clipping transition is the upper cap `m<=2r`, which yields `z_c` above.

## Independent numerical verification performed in this session

1. 200,000 random valid `(N,r,L,B)` points comparing the original clipped expression with the explicit phase-law form: zero mismatches; worst absolute floating-point difference approximately `5.7e-14`.
2. 300 independent full singular-value constrained optimizations using SLSQP over the ordered singular-value vector with `0<=tau_i<=2` and `sum tau_i>=L/2`: among converged cases, worst absolute difference from the phase law approximately `1.65e-12`.

These are numerical verification checks, not the proof.

## Novelty boundary

The following ingredients are classical and must not be claimed as new:

- Eckart-Young-Mirsky low-rank approximation and singular-value truncation.
- Rank/norm constrained matrix-nearness problems and SVD-based closed forms.
- Active electromagnetic scattering cancellation using finite arrays of sources.
- Passive scattering-matrix contractivity, extinction identities, and causality/bandwidth bounds.

The current candidate contribution is narrower:

> the coupling of an aggregate passive electromagnetic extinction burden `L` to simultaneous active rank `r` and Frobenius correction budget `B`, yielding the exact sharp passive-class residual envelope `E_H(N,r,L,B)` and its explicit rank-strength phase law.

Targeted searches performed on 2026-09-09 located classical rank/norm matrix-nearness results and established active-cloaking work, but did not locate this exact extinction-to-rank/strength envelope. Absence from a targeted search is not proof of historical priority. External expert literature review remains required before a novelty claim is made in publication.

## Recommended claim level

Preferred formal name:

**Hellard Hybrid Electromagnetic Resource Theorem**

Preferred simplified engineering name:

**Hellard Rank-Strength Resource Law**

Strongest defensible statement at present:

> Under finite-dimensional power-normalized scattering, a unitary reference, passivity, an aggregate extinction burden, an active rank constraint, and a Frobenius correction budget, the Hellard value function gives the exact sharp universal lower envelope on residual operator mismatch. The envelope reduces to an explicit rank-strength phase law.
