# Hellard Electromagnetic Control-Resource Law — Novelty Audit

Date: 2026-09-09

## Candidate statement

For a fixed passive electromagnetic scattering system relative to a fixed unitary reference, let

\[
D=I-S_0^\dagger S
\]

with singular values \(\tau_1\ge\cdots\ge\tau_N\ge0\).  An active correction obeys

\[
\operatorname{rank}(A)\le r,\qquad \|A\|_F\le B.
\]

The exact fixed-system optimum is

\[
E_{\rm fix}(D;r,B)=\left[\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}-B\right]_+^2+\sum_{i>r}\tau_i^2.
\]

If only the passive extinction/deviation burden

\[
2\operatorname{Re}\operatorname{tr}D\ge L
\]

is known, the sharp passive-class envelope is the project value function \(E_H(N,r,L,B)\) derived in `HELLARD_HYBRID_ELECTROMAGNETIC_RESOURCE_LAW_FORMAL.md`.

The project should currently call this the **Hellard Electromagnetic Control-Resource Theorem** rather than a universal law of nature.

## Physical meaning of the burden

For a fixed unitary reference \(S_0\) and a unit-normalized incident channel \(x\),

\[
2\operatorname{Re}\langle x,Dx\rangle
=\|(S-S_0)x\|^2+\|x\|^2-\|Sx\|^2.
\]

Thus the burden equals background-relative scattered-deviation power plus absorbed power.  Summing over a complete orthonormal incident basis gives the trace burden used by the theorem.

## Exact spherical corollary

For a homogeneous sphere with size parameter \(x=ka\), standard Lorenz–Mie theory gives

\[
Q_{\rm ext}=\frac{2}{x^2}\sum_{\ell=1}^{\infty}(2\ell+1)\operatorname{Re}(a_\ell+b_\ell).
\]

With the channel normalization used in the project,

\[
L=4\sum_\ell(2\ell+1)\operatorname{Re}(a_\ell+b_\ell)=2x^2Q_{\rm ext}.
\]

Therefore the class-envelope perfect-correction rank threshold

\[
r\ge L/4
\]

becomes

\[
\boxed{r\ge \frac{(ka)^2Q_{\rm ext}}{2}}.
\]

The Frobenius-strength threshold becomes

\[
\boxed{B\ge \frac{(ka)^2Q_{\rm ext}}{\sqrt r}}.
\]

For electrically large opaque spheres, the classical extinction-paradox limit \(Q_{\rm ext}\to2\) yields the asymptotic scaling

\[
\boxed{r_{\min}\sim(ka)^2.}
\]

This is an exact Mie-theory corollary plus a standard asymptotic extinction result, not an empirical fit.

## Padding / infinite-dimensional issue

The finite-dimensional extinction-only envelope weakens if arbitrary zero-deviation channels are appended.  Therefore an arbitrary numerical matrix dimension cannot be treated as a physical universal parameter.  The tail-robust corollary in `HELLARD_TAIL_ROBUST_CHANNEL_COROLLARY.md` repairs this by using a resolved singular-channel count and a bounded nuclear tail.

This limitation is essential.  Without a finite/effective channel count or tail control, an extinction-only Frobenius lower bound can be driven to zero by spreading fixed nuclear mass over infinitely many channels.

## Literature audit

### Standard ingredients already known

1. **Low-rank approximation / singular values.**  Eckart–Young–Mirsky and projection onto norm balls are standard matrix-analysis tools.  The fixed-\(D\) formula is therefore not historically new by itself.

2. **Active electromagnetic cloaking.**  Selvanayagam and Eleftheriades experimentally demonstrated active microwave cloaking with a finite antenna array (Phys. Rev. X 3, 041011, 2013, DOI 10.1103/PhysRevX.3.041011).  Miller gave a sensor/source active-cloak construction much earlier (Opt. Express 14, 12457, 2006, DOI 10.1364/OE.14.012457).

3. **SVD / inverse-source active field control.**  Active EM field-control literature uses truncated SVD, Tikhonov regularization, source-count and power-budget studies.  Example: sensitivity analysis for active electromagnetic field manipulation in free space, 2022, DOI 10.1080/27690911.2022.2118270.

4. **Electromagnetic degrees of freedom.**  Miller's communication-mode framework uses SVD to count optimal electromagnetic channels (Adv. Opt. Photon. 11, 679–825, 2019, DOI 10.1364/AOP.11.000679).  More recent radiating-system work shows asymptotic degree-of-freedom scaling with shadow area for electrically large objects.

5. **Global scattering bounds.**  Modern operator-bound literature derives passive electromagnetic limits from power conservation and convex duality; e.g. Phys. Rev. Research 2, 033172 (2020), DOI 10.1103/PhysRevResearch.2.033172.  Passive cloak bandwidth/global-scattering limits are also well established.

### What this search did not locate

As of this audit, targeted searches did not locate a prior published theorem giving the same explicit sharp value function that maps only

\[
(N,r,L,B)
\]

to the minimum possible residual over the passive scattering class, nor the same extinction-to-rank/strength perfect-correction thresholds

\[
L\le4r,\qquad B\ge L/(2\sqrt r)
\]

as a single electromagnetic resource envelope.

This absence is not proof of historical novelty.  A peer-review-grade novelty claim still requires deeper database searching, citation chaining, and external expert review.

## Defensible current naming

**Hellard Electromagnetic Control-Resource Theorem**

Suggested one-sentence statement:

> In a finite or tail-controlled passive electromagnetic scattering channel space, a prescribed extinction/deviation burden imposes a sharp joint lower envelope on the residual obtainable by any active correction of bounded rank and Frobenius strength.

The spherical specialization may be called the **Hellard spherical active-control corollary** pending external novelty review.

## Claims not yet justified

- not a universal law of nature;
- not proof of practical invisibility;
- not a hardware power law unless \(B\) is mapped to actuator/source power;
- not a geometry-independent channel-count law;
- not historically novel until an external literature review confirms it.
