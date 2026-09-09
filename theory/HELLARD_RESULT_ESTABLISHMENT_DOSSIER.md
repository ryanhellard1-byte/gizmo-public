# Hellard Hybrid Electromagnetic Resource Theorem — Establishment Dossier

Date: 2026-09-09

## Bottom-line status

The finite-dimensional operator theorem is established mathematically under its stated assumptions. The exact Lorenz-Mie spherical specialization is established algebraically from the theorem plus the standard Mie extinction formula. The result has substantial numerical stress testing and Maxwell-model validation. Historical novelty is promising but not yet established to the standard of professional prior-art review and external peer review.

This dossier deliberately separates four claims:

1. theorem correctness;
2. electromagnetic interpretation;
3. exact spherical specialization;
4. historical novelty.

Only the first three are currently established internally.

---

## 1. Established mathematical theorem

Let

\[
Q=S_0^\dagger S,\qquad D=I-Q,
\]

where `S0` is unitary and `S` is passive, so `Q` is contractive. Let the incident space have dimension `N`, and define the burden

\[
L\le 2\operatorname{Re}\operatorname{tr}D.
\]

Let an active correction obey

\[
\operatorname{rank}(A)\le r,\qquad \|A\|_F\le B.
\]

For a fixed `D` with singular values `tau_1 >= ... >= tau_N`, the exact best active correction is

\[
E_{\rm fix}(D;r,B)
=
\left[\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}-B\right]_+^2
+\sum_{i=r+1}^N\tau_i^2.
\]

This is a direct consequence of standard low-rank approximation/SVD geometry.

Over the complete passive class specified only by `N` and burden `L`, define

\[
\mathcal V(N,r,L,B)
=
\inf_D E_{\rm fix}(D;r,B)
\]

subject to

\[
\|I-D\|_2\le1,
\qquad
2\operatorname{Re}\operatorname{tr}D\ge L.
\]

For `0<r<N`, set `s=L/2`, `q=N-r`,

\[
m_{\min}=\max\left(rs/N,s-2q,0\right),
\qquad
m_{\max}=\min(s,2r),
\]

\[
\widehat m=
\begin{cases}
s,&s\le B\sqrt r,\\
\dfrac{rs+qB\sqrt r}{N},&s>B\sqrt r,
\end{cases}
\]

and

\[
m_\star=\operatorname{clip}(\widehat m,m_{\min},m_{\max}).
\]

Then

\[
\boxed{
\mathcal V(N,r,L,B)=E_H(N,r,L,B)
}
\]

with

\[
\boxed{
E_H=
\left[\frac{m_\star}{\sqrt r}-B\right]_+^2
+\frac{(L/2-m_\star)^2}{N-r}.
}
\]

The edge cases are

\[
E_H(N,0,L,B)=L^2/(4N),
\]

\[
E_H(N,N,L,B)=\left[L/(2\sqrt N)-B\right]_+^2.
\]

The proof is sharp because the minimizing singular spectrum can be realized by a diagonal positive `D` with `Q=I-D` contractive.

### Perfect-correction class-envelope threshold

For `0<r<N`, the class envelope reaches zero if and only if

\[
\boxed{r\ge L/4}
\]

and

\[
\boxed{B\ge L/(2\sqrt r)}.
\]

Equivalently,

\[
\boxed{rB^2\ge L^2/4}
\]

plus the independent rank condition.

These are class-existence thresholds, not sufficient conditions for an arbitrary fixed physical `D`.

---

## 2. Physical burden identity

For a fixed physically specified unitary background `S0`,

\[
S-S_0=-S_0D.
\]

For unit-power incident state `x`, define background-relative output deviation power

\[
P_{\rm dev}=\|(S-S_0)x\|^2=\|Dx\|^2
\]

and passive absorbed/unreturned power

\[
P_{\rm abs}=\|x\|^2-\|Sx\|^2.
\]

Then exactly

\[
\boxed{
P_{\rm dev}+P_{\rm abs}
=2\operatorname{Re}\langle x,Dx\rangle.
}
\]

Therefore the theorem burden has a direct power-balance interpretation when the reference and channel normalization are fixed beforehand and the propagating channel basis is complete to controlled tolerance.

---

## 3. Exact Lorenz-Mie spherical specialization

For a homogeneous sphere, let

\[
x=ka.
\]

For standard electric and magnetic Mie coefficients `a_l`, `b_l`, the standard extinction efficiency is

\[
Q_{\rm ext}
=\frac{2}{x^2}
\sum_{\ell=1}^{\infty}(2\ell+1)
\operatorname{Re}(a_\ell+b_\ell).
\]

Using the scattering-channel normalization `D_l=2c_l`, the Hellard burden is

\[
L=4\sum_{\ell=1}^{\infty}(2\ell+1)
\operatorname{Re}(a_\ell+b_\ell).
\]

Hence exactly

\[
\boxed{L=2x^2Q_{\rm ext}}.
\]

Substitution into the class-envelope perfect-correction thresholds gives

\[
\boxed{
r\ge \frac{x^2Q_{\rm ext}}{2}}
\]

and

\[
\boxed{
B\ge\frac{x^2Q_{\rm ext}}{\sqrt r}.
}
\]

For integer active rank,

\[
r\ge\left\lceil x^2Q_{\rm ext}/2\right\rceil.
\]

For electrically large spheres, the classical extinction paradox gives `Q_ext -> 2`, so

\[
\boxed{r_{\min}\sim(ka)^2}.
\]

At the simultaneous continuous minimum-rank boundary,

\[
\boxed{B_{\min}\sim2ka}.
\]

This spherical corollary is exact given the theorem normalization and the standard Mie formula.

---

## 4. Numerical establishment already completed

The following independent stress tests have been completed in the project:

- direct constrained optimization over singular values compared with the closed form;
- random complex non-normal passive contractions `Q`;
- direct broadband convex-program comparison;
- 2-D PEC-cylinder partial-wave Maxwell models;
- broadband PEC-cylinder models;
- lossy dielectric-cylinder models;
- passive multilayer plus active-correction models;
- full 3-D vector Lorenz-Mie spheres with electric and magnetic multipoles and azimuthal degeneracy;
- arbitrary-precision independent Mie implementation;
- tail-robust random truncation tests.

No verified violation has been found.

The theorem does not rely on these simulations for proof. They test implementation and the electromagnetic mapping.

---

## 5. Padding and infinite-dimensional issue

The raw finite-dimensional class envelope weakens if an analyst pads the ambient matrix with zero-deviation channels. Therefore arbitrary numerical matrix dimension must not be interpreted as a physical parameter.

For a resolved singular-channel count `K` and unresolved nuclear tail

\[
\delta_K=\sum_{i>K}\tau_i,
\]

define

\[
L_K=[L-2\delta_K]_+.
\]

Then the fixed-system residual obeys the tail-robust bound

\[
\boxed{
E_{\rm fix}(D;r,B)
\ge
E_H\left(K,\min(r,K),L_K,B\right).
}
\]

This is invariant under addition of exact zero-deviation channels.

Without a finite/effective channel count or controlled tail, extinction alone cannot give a nonzero dimension-free Frobenius residual bound, because a fixed nuclear mass can be spread over arbitrarily many infinitesimal singular values.

---

## 6. Literature ancestry confirmed

Any manuscript must explicitly credit the following established ingredients.

### Classical scattering-matrix framework

P. C. Waterman's 1971 work establishes vector spherical partial-wave scattering matrices and unitarity for lossless electromagnetic scattering.

### Low-rank matrix approximation

The fixed-`D` rank-constrained correction step is rooted in the Eckart-Young-Mirsky theorem and standard singular-value approximation theory. This component is not claimed as novel.

### Active electromagnetic cloaking

Active electromagnetic cloaking, source-array cancellation, incident-field estimation, multipolar active sources and experimental demonstrations all predate this project. Prior work demonstrates that source number, position and incident-field information affect cloak performance.

### Electromagnetic degrees of freedom

Modern work by Gustafsson and collaborators connects the number of dominant electromagnetic modes of electrically large objects to shadow area. This is compatible with, but independent of, the `(ka)^2` large-sphere rank scaling obtained here from Mie extinction plus the Hellard envelope.

### Mie extinction

The standard formula

\[
Q_{\rm ext}=\frac{2}{x^2}\sum_l(2l+1)\operatorname{Re}(a_l+b_l)
\]

and the large-object extinction-paradox limit `Q_ext -> 2` are classical.

---

## 7. Targeted novelty-search result

Targeted searches were performed for combinations of:

- active electromagnetic cloaking + rank bounds;
- extinction + active control rank;
- scattering-matrix trace/nuclear-norm bounds + active cancellation;
- singular-value/Frobenius resource bounds for cloaking;
- Mie extinction + minimum active source/channel count;
- active-cloak multipole/source-number lower bounds.

The searches recovered substantial neighboring literature, including source-number studies, SVD/regularization methods, active-cloak experiments, classical scattering theory and generic low-rank approximation.

No located source stated the same combined closed-form passive-extinction-to-active-rank/strength envelope

\[
E_H(N,r,L,B)
\]

or the same exact Mie consequence

\[
r\ge x^2Q_{\rm ext}/2,
\qquad
B\ge x^2Q_{\rm ext}/\sqrt r.
\]

This is evidence of possible novelty, not proof of historical priority. A publishable priority claim still requires expert literature review across IEEE Xplore, Web of Science/Scopus, Google Scholar, INSPEC, patents, dissertations and older operator/scattering-control literature.

---

## 8. What is now legitimately established

We can defend the following statements now:

1. **The finite-dimensional Hellard hybrid electromagnetic resource theorem is mathematically proved under its stated assumptions.**
2. **Its exact fixed-system correction formula is classical SVD geometry; the proposed contribution is the sharp passive-extinction class envelope and its resource interpretation.**
3. **The burden functional has an exact background-relative deviation-plus-absorption power interpretation.**
4. **The Lorenz-Mie sphere gives the exact identity `L=2(ka)^2 Q_ext` under the adopted channel normalization.**
5. **Therefore the spherical class-envelope thresholds `r >= (ka)^2 Q_ext/2` and `B >= (ka)^2 Q_ext/sqrt(r)` follow exactly.**
6. **The large-sphere asymptotic rank scaling `r_min ~ (ka)^2` follows from the classical limit `Q_ext -> 2`.**
7. **No numerical or Maxwell counterexample has yet been found in the project's test set.**

We cannot yet defend:

- universal historical novelty;
- a claim that this is a new fundamental law of nature;
- sufficiency for a particular physical actuator geometry;
- practical broadband invisibility;
- conversion of `B` into watts without a hardware normalization;
- complete external validation without independent researchers reproducing and reviewing the result.

---

## Proposed publication terminology

Use

**Hellard Hybrid Electromagnetic Resource Theorem**

for the proved finite-dimensional theorem.

Use

**Hellard-Mie Resource Corollary**

for the exact spherical specialization.

Reserve

**Hellard Electromagnetic Resource Law**

for later use only if independent peer review and historical novelty review support a broader physical-law interpretation.

## Current verdict

**Mathematical result: established internally.**

**Exact 3-D spherical Maxwell corollary: established internally.**

**Numerical validation: strong and multi-method.**

**Historical novelty: promising but not yet established externally.**

**Practical cloak: not established.**
