# Hellard Hybrid Electromagnetic Resource Theorem — Adversarial Audit

Date: 2026-09-09

## Bottom line

The finite-dimensional theorem survives a hostile re-derivation and independent numerical attacks under its stated abstract assumptions. The strongest defensible wording is:

> The Hellard value function is a **sharp universal lower envelope** for passive finite-dimensional scattering operators with a specified aggregate extinction burden, active correction rank, and Frobenius correction budget.

It is not the exact correction cost for every fixed scatterer. For a fixed deviation operator `D`, the exact cost is the singular-spectrum formula `E_fix(D;r,B)` in the formal theorem.

No literature search performed in this audit found the same electromagnetic extinction-to-active-rank/strength value function. That is encouraging but is **not proof of historical novelty**. The matrix approximation ingredients are classical.

---

## 1. Clean operator statement

Let

\[
Q=S_0^\dagger S,\qquad D=I-Q,
\]

with `S0` unitary and `Q` contractive. Then

\[
\|D\|_2\le2.
\]

For a complete orthonormal power-normalized `N`-channel basis,

\[
L\le 2\operatorname{Re}\operatorname{tr}D
\le2\|D\|_*.
\]

Hence, if `tau_i` are the singular values of `D`,

\[
\sum_i\tau_i\ge s,\qquad s\equiv L/2,
\]

with

\[
0\le\tau_i\le2.
\]

For a fixed `D`, the exact rank-`r`, Frobenius-budget-`B` correction value is

\[
E_{\rm fix}(D;r,B)
=
[T_r(D)-B]_+^2+\sum_{i=r+1}^N\tau_i^2,
\]

where

\[
T_r(D)=\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}.
\]

The sharp class envelope is

\[
E_H(N,r,L,B)=
\inf_{D\in\mathcal C_{N,L}}E_{\rm fix}(D;r,B).
\]

This distinction between a fixed-system optimum and a class envelope is essential.

---

## 2. New simplified phase-law form

The `clip(m_hat,m_min,m_max)` expression in the main theorem can be reduced to a transparent piecewise law.

For `0 < r < N`, define

\[
s=L/2,\qquad z=B\sqrt r,\qquad q=N-r.
\]

### Rank-capable regime: `s <= 2r`

Then

\[
\boxed{
E_H=\frac{[s-z]_+^2}{N}.
}
\]

Thus when the active rank is large enough to carry the required singular-value mass, only the aggregate correction-strength deficit remains.

Perfect class-envelope correction occurs exactly when

\[
z\ge s,
\]

or

\[
\boxed{B\ge \frac{L}{2\sqrt r}},
\]

provided independently that

\[
\boxed{L\le4r}.
\]

### Rank-overloaded regime: `s > 2r`

Define the crossover

\[
\boxed{
z_c=\frac{r(2N-s)}{N-r}.
}
\]

Then

\[
\boxed{
E_H=
\begin{cases}
\dfrac{(s-z)^2}{N},&0\le z\le z_c,\\[2mm]
\dfrac{(2r-z)^2}{r}+\dfrac{(s-2r)^2}{N-r},&z_c<z<2r,\\[2mm]
\dfrac{(s-2r)^2}{N-r},&z\ge2r.
\end{cases}
}
\]

This form makes the two independent obstructions explicit:

1. **strength wall:** insufficient `B` leaves an all-channel residual;
2. **rank wall:** once the controllable singular channels saturate at the passive cap, additional active strength cannot remove the residual singular mass forced into the remaining `N-r` channels.

For `r=N`,

\[
E_H=\frac{[s-B\sqrt N]_+^2}{N}.
\]

For `r=0`,

\[
E_H=\frac{s^2}{N}.
\]

---

## 3. Dimensionless phase variables

For `r>0`, define

\[
\rho=\frac{L}{4r}=\frac{s}{2r},
\qquad
\beta=\frac{B}{2\sqrt r}=\frac{z}{2r}.
\]

`rho` is a rank-loading ratio and `beta` is a correction-strength loading ratio relative to the passive singular-value cap.

The perfect-correction region of the abstract class envelope is simply

\[
\boxed{\rho\le1,\qquad \beta\ge\rho.}
\]

Equivalently,

\[
\boxed{L\le4r,\qquad rB^2\ge L^2/4.}
\]

This is the cleanest phase-diagram interpretation of the theorem found in this audit.

---

## 4. Why the phase law follows from the clipped formula

When `s > B sqrt(r)`, the unconstrained stationary point is

\[
\widehat m=\frac{rs+(N-r)z}{N}.
\]

The ordering lower bound `m >= rs/N` never clips this stationary point because `z >= 0`.

The tail-cap lower bound `m >= s-2(N-r)` also never clips it for `0 <= s <= 2N`, since

\[
\widehat m-[s-2(N-r)]
=\frac{(N-r)(2N-s+z)}{N}\ge0.
\]

Therefore the only nontrivial clipping transition is the upper cap `m <= 2r` when `s>2r`. Solving `m_hat=2r` gives exactly `z_c` above. Substitution produces the three rank-overloaded branches.

This removes unnecessary apparent complexity from the original `m_star` representation without changing the value function.

---

## 5. Broadband proof structure

The current broadband statement is supported by a convex value-function argument.

For `0<r<N`, introduce the pointwise variables `(s,m,b)` with

\[
F(s,m,b)=\left[\frac{m}{\sqrt r}-b\right]_+^2+\frac{(s-m)^2}{N-r}
\]

and linear feasibility conditions

\[
m\ge rs/N,
\quad m\ge s-2(N-r),
\quad m\le s,
\quad m\le2r,
\quad s\ge0,
\quad b\ge0.
\]

`F` is jointly convex because it is the sum of a squared positive-part of an affine function and a quadratic affine form. The feasible set is jointly convex in `(s,m,b)`. Therefore the partial minimization defining `E_H` is convex in `(L,B)` after the scaling `s=L/2`.

It is also nondecreasing in `L` and nonincreasing in `B`.

Consequently, weighted Jensen plus Cauchy-Schwarz yields

\[
\mathcal E_\Omega
\ge
W E_H\!\left(
N,r,\frac{L_\Omega}{W},\sqrt{\frac{P_\Omega}{W}}
\right).
\]

The sharpness statement is an **abstract class sharpness** statement: constant-in-frequency extremizers attain equality when they satisfy the pointwise assumptions. Causal controller realizability, stability, latency, noise and actuator efficiency are additional constraints and are not included.

---

## 6. Independent adversarial numerical checks

The audit used independent code paths rather than only re-evaluating the scalar closed form.

### A. Full singular-value constrained optimization

- 1000 random cases
- `N=2..12`
- `0<r<N`
- `0<L<4N`
- random `B`
- SLSQP optimization over the entire ordered singular-value vector with the nuclear-mass lower bound and `tau_i<=2`

Among converged solver cases there were **zero mismatches larger than 1e-7**. A separate 1000-case run had a worst absolute closed-form/numerical difference of approximately `6.23e-12` among successful solves.

### B. Random non-normal passive contractions

- 30,000 random complex contractions
- `Q = U diag(q_i) V^dagger`
- independent Haar-like random unitary factors `U,V`
- `0<=q_i<=1`
- therefore includes strongly non-normal `Q`, not merely diagonal partial-wave systems

For each case, `D=I-Q`, the actual singular spectrum was used to calculate the exact fixed-system active optimum, then compared with `E_H` using the actual extinction burden.

Result:

\[
\boxed{30,000\ \text{cases},\qquad 0\ \text{violations}.}
\]

### C. Joint-convexity attack

- 300,000 random Jensen tests in `(L,B)`
- all edge ranks `0<=r<=N` included

Result:

\[
\boxed{0\ \text{convexity violations at }10^{-9}\text{ tolerance}.}
\]

### D. Direct broadband optimization

An independent finite-frequency convex optimization over all per-frequency `(s_k,m_k,b_k)` variables was compared with the broadband closed form.

A 500-case run produced **zero mismatches larger than 1e-6**; in a fully converged independent run the worst absolute difference was approximately `1.04e-10`.

### E. Piecewise-law equivalence

100,000 random valid `(N,r,L,B)` points were compared between the original clipped expression and the simplified phase-law expression.

Worst floating-point difference was at machine-precision scale (order `1e-14`).

These tests are reproducibility checks, not substitutes for the analytic proof.

---

## 7. Electromagnetic scope warning that must stay in the paper

The finite-dimensional scattering operator must be defined on a **complete set of included propagating channels** for the chosen physical problem and normalization. If the model projects away propagating channels into which the object can scatter, `||D+A||_F` measures only the retained-channel mismatch and need not equal total electromagnetic visibility.

Therefore any physical application must state:

1. the channel basis and normalization;
2. whether all relevant outgoing propagating channels are included;
3. how truncation error is controlled;
4. how the abstract Frobenius correction budget `B` maps to actual actuator power, voltage/current limits, radiated power, or stored energy.

In particular, `B^2` is an abstract squared operator-amplitude budget. It must not automatically be labeled amplifier watts or physical energy without a separate hardware normalization theorem.

---

## 8. Novelty audit

The mathematical ancestry is substantial and should be cited rather than hidden:

- Eckart-Young (1936) and Mirsky (1960): best low-rank approximation under unitarily invariant norms.
- Sondermann (1986) and Friedland-Torokhti (2007): generalized rank-constrained matrix approximation.
- Y.-L. Yu and D. Schuurmans, *Rank/Norm Regularization with Closed-Form Solutions* (UAI 2011): closed-form rank/norm-regularized matrix problems and SVD reductions.
- Z. Li and L.-H. Lim, *Generalized Matrix Nearness Problems*, SIAM J. Matrix Anal. Appl. 44 (2023), DOI 10.1137/22M1526034: closed-form generalized matrix-nearness problems for rank or norm constraints and related structures.
- R. T. Wang, C.-K. Li and L.-H. Lim, *Generalized matrix nearness problems II* (2026 preprint): extensions to affine/Kronecker settings and general orthogonally invariant norms.

Those works make it unlikely that the fixed-`D` SVD correction formula alone is a new theorem.

The electromagnetic ancestry is also clear:

- Selvanayagam & Eleftheriades, Phys. Rev. X 3, 041011 (2013): experimental active electromagnetic cloaking with a finite source array.
- Ang & Eleftheriades, Phys. Rev. Applied 16, 064005 (2021): adaptive incident-field estimation for active cloaking.
- Active and passive cloaking literature already recognizes that larger or more complicated scattering responses require additional controllable multipoles/degrees of freedom.
- Passive-cloak literature contains extensive causality, extinction, bandwidth and material-response bounds.

However, the searches performed for this audit did **not** locate a prior result with the same combined statement:

\[
\text{passive aggregate extinction burden }L
\quad+\quad
\text{active rank }r
\quad+\quad
\text{Frobenius correction budget }B
\]

mapped to the exact sharp passive-class residual envelope `E_H(N,r,L,B)` and its broadband aggregate form.

That is the current novelty candidate.

Absence from a targeted literature search is not proof of priority. A publication claim should still receive an expert literature review and external mathematical peer review.

---

## 9. Recommended name and claim level

The most defensible current name is

\[
\boxed{\textbf{Hellard Hybrid Electromagnetic Resource Theorem}}
\]

or, for the simplified phase interpretation,

\[
\boxed{\textbf{Hellard Rank-Strength Resource Law}}
\]

with “law” used as an engineering/resource relation rather than a claimed new fundamental law of nature.

The strongest current defensible claim is:

> Under finite-dimensional power-normalized scattering, a unitary reference, pointwise passivity, aggregate extinction information, an active rank constraint, and a Frobenius correction budget, the Hellard value function gives the exact sharp universal lower envelope on residual operator mismatch. The result reduces to an explicit rank-strength phase law and extends to a sharp abstract broadband envelope under an integrated squared correction budget.

That claim is mathematically stronger, cleaner, and easier to defend than “a universal law of invisibility.”
