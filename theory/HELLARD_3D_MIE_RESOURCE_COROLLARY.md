# Hellard 3-D Lorenz-Mie Resource Corollary

Date: 2026-09-09

## Purpose

This note connects the finite-dimensional Hellard hybrid electromagnetic resource theorem to an exact family of full 3-D Maxwell scatterers: homogeneous spheres described by Lorenz-Mie theory.

The result is a **corollary of the Hellard class-envelope theorem plus standard Mie extinction theory**. The underlying Mie formulas and the large-sphere extinction paradox are classical. The potentially distinctive statement is the active rank/strength consequence obtained by inserting the exact Mie extinction burden into the Hellard resource thresholds.

---

## 1. Vector spherical channels

For a homogeneous sphere of radius `a` in a homogeneous background, define the size parameter

\[
x=ka.
\]

Let `a_l` and `b_l` be the standard electric and magnetic Lorenz-Mie coefficients. For each electric or magnetic channel, use

\[
S_\ell=1-2c_\ell,
\qquad
D_\ell=2c_\ell,
\]

where `c_l` denotes either `a_l` or `b_l`.

The normalized per-channel Hellard burden is

\[
X_\ell=2\operatorname{Re}D_\ell=4\operatorname{Re}c_\ell.
\]

Including every azimuthal mode `m=-ell,...,+ell` and both electric and magnetic polarizations, the total burden is

\[
\boxed{
L=4\sum_{\ell=1}^{\infty}(2\ell+1)
\operatorname{Re}(a_\ell+b_\ell).
}
\]

For passive channels,

\[
X_\ell-|D_\ell|^2
=4\operatorname{Re}c_\ell-4|c_\ell|^2
=1-|S_\ell|^2\ge0.
\]

---

## 2. Exact connection to Mie extinction efficiency

The standard Lorenz-Mie extinction efficiency is

\[
Q_{\rm ext}
=\frac{2}{x^2}
\sum_{\ell=1}^{\infty}(2\ell+1)
\operatorname{Re}(a_\ell+b_\ell).
\]

Therefore the Hellard burden is exactly

\[
\boxed{
L=2x^2Q_{\rm ext}.
}
\]

This identity removes an arbitrary channel-count parameter from the spherical resource threshold. It expresses the burden directly in a measurable/classical scattering quantity.

---

## 3. Exact spherical class-envelope rank threshold

The Hellard class-envelope perfect-correction rank condition is

\[
L\le4r.
\]

Substituting the exact Mie burden gives

\[
2x^2Q_{\rm ext}\le4r,
\]

or

\[
\boxed{
r\ge r_{\rm H,Mie}(x)
\equiv\frac{x^2Q_{\rm ext}(x)}{2}.}
\]

Since `r` is an integer, a physical finite-channel implementation uses

\[
\boxed{
r\ge
\left\lceil\frac{x^2Q_{\rm ext}(x)}{2}\right\rceil.}
\]

Interpretation: within the abstract active-correction model, a sphere whose exact normalized extinction burden is `L` cannot lie on the zero-residual class envelope unless the active correction has at least this many independent singular control dimensions.

This is a **class-existence necessary condition**, not a guarantee that any particular actuator layout can perfectly cloak the fixed sphere.

---

## 4. Exact spherical strength threshold

The independent Hellard strength condition is

\[
B\ge\frac{L}{2\sqrt r}.
\]

Using `L=2x^2 Q_ext`,

\[
\boxed{
B\ge\frac{x^2Q_{\rm ext}(x)}{\sqrt r}.}
\]

Equivalently,

\[
\boxed{
rB^2\ge x^4Q_{\rm ext}^2(x).}
\]

Again, `B` is the Frobenius norm of the effective correction operator. It is not automatically amplifier watts or radiated energy without a hardware coupling/normalization model.

At the minimum continuous rank threshold

\[
r=\frac{x^2Q_{\rm ext}}{2},
\]

the corresponding minimum abstract strength is

\[
\boxed{
B_{\rm min,rank}=x\sqrt{2Q_{\rm ext}}.
}
\]

---

## 5. Electrically large sphere asymptotics

The classical extinction paradox states that for a sufficiently large sphere,

\[
Q_{\rm ext}\to2.
\]

Therefore

\[
L\sim4x^2,
\]

and the Hellard spherical resource thresholds become

\[
\boxed{
r_{\rm H,Mie}\sim x^2=(ka)^2,}
\]

\[
\boxed{B\gtrsim\frac{2x^2}{\sqrt r}.}
\]

At the minimum rank scaling `r~x^2`,

\[
\boxed{B\gtrsim2x=2ka.}
\]

Thus the abstract control problem has an area-like rank burden and a linear-in-electrical-size minimum operator-amplitude burden when both resources are simultaneously used at their class-envelope threshold.

The `(ka)^2` scaling is consistent with independent electromagnetic degrees-of-freedom literature, where the number of dominant modes of electrically large objects is tied to shadow area measured in wavelength-squared units.

---

## 6. Numerical Lorenz-Mie verification

The accompanying script `verify_hellard_mie_channel_scaling.py` evaluates exact electric and magnetic Mie coefficients, includes every `(2ell+1)` azimuthal degeneracy, checks the passive channel identity, and computes

\[
r_{\rm crit}=L/4.
\]

Selected results:

| refractive index | x | retained vector channels K | L | rcrit=L/4 | rcrit/K |
|---|---:|---:|---:|---:|---:|
| 1.5 | 4 | 390 | 129.678471 | 32.419618 | 0.083127 |
| 1.5 | 8 | 720 | 227.548014 | 56.887004 | 0.079010 |
| 1.5 | 12 | 1248 | 713.088276 | 178.272069 | 0.142846 |
| 1.5 | 16 | 1798 | 1239.005884 | 309.751471 | 0.172276 |
| 1.5 | 20 | 2310 | 1628.669584 | 407.167396 | 0.176263 |
| 2.5+0.2i | 4 | 390 | 88.778241 | 22.194560 | 0.056909 |
| 2.5+0.2i | 8 | 720 | 314.126146 | 78.531536 | 0.109072 |
| 2.5+0.2i | 12 | 1248 | 675.150390 | 168.787597 | 0.135246 |
| 2.5+0.2i | 16 | 1798 | 1170.638001 | 292.659500 | 0.162769 |
| 2.5+0.2i | 20 | 2310 | 1799.240447 | 449.810112 | 0.194723 |

Over `10 <= x <= 100`, log-log fits give

\[
r_{\rm crit}\approx1.386\,x^{1.936}
\]

for `m=1.5`, and

\[
r_{\rm crit}\approx1.315\,x^{1.948}
\]

for `m=2.5+0.2i`.

At `x=100`, both families give

\[
r_{\rm crit}/x^2\approx1.05,
\]

consistent with convergence toward the exact large-sphere asymptotic coefficient `1` implied by `Q_ext -> 2`.

Passivity-channel residuals remained at floating-point roundoff for the lossless sphere and nonnegative for the absorbing sphere.

---

## 7. Modal truncation and padding

The exact Lorenz-Mie expansion is infinite. Numerical evaluation uses a finite multipole cutoff. A common Wiscombe-type far-field truncation scales as

\[
\ell_{\max}\simeq x+4x^{1/3}+2.
\]

The corresponding retained electric-plus-magnetic vector spherical channel count is

\[
K_{\rm sph}=2\ell_{\max}(\ell_{\max}+2).
\]

For rigorous use of the finite-dimensional Hellard theorem, an ambient numerical cutoff must not be mistaken for a fundamental physical channel count. The separate `HELLARD_TAIL_ROBUST_CHANNEL_COROLLARY.md` shows how to replace arbitrary ambient dimension by a resolved singular-channel count plus a controlled nuclear-norm tail.

---

## 8. Falsifiable spherical prediction

For a consistently normalized sphere scattering experiment/model with complete resolved channels and effective active correction operator `A`, the abstract theorem predicts that class-envelope perfect correction cannot occur unless

\[
\boxed{
r\ge\left\lceil x^2Q_{\rm ext}/2\right\rceil}
\]

and

\[
\boxed{B\ge x^2Q_{\rm ext}/\sqrt r.}
\]

A verified counterexample satisfying the exact same channel normalization, passivity conditions and operator-budget definition would falsify the theorem-to-Mie mapping or the theorem itself.

---

## 9. Literature ancestry

Classical ingredients that must be credited in any manuscript include:

- Lorenz-Mie vector spherical scattering theory and its extinction efficiency formula.
- The large-particle extinction paradox, `Q_ext -> 2`.
- Wiscombe-type Mie-series truncation criteria.
- Modern electromagnetic degrees-of-freedom/characteristic-mode results relating dominant modal count of electrically large objects to shadow area.

The resource consequence

\[
r\ge x^2Q_{\rm ext}/2,
\qquad
B\ge x^2Q_{\rm ext}/\sqrt r
\]

is the Hellard-theorem corollary being proposed for novelty review.

## Status

**Mathematical status:** exact corollary of the stated Hellard finite-dimensional class-envelope theorem and the standard Mie extinction formula, subject to consistent channel normalization and convergence of the modal representation.

**Physical status:** validated numerically for representative lossless and absorbing homogeneous spheres. Real active-cloak hardware has additional actuator geometry, causality, stability, sensing, latency, noise and efficiency constraints.

**Novelty status:** candidate. External literature review and peer review remain required before making a priority claim.
