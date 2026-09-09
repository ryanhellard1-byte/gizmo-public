# Hellard Hybrid Electromagnetic Resource Theorem — Complete Proof

Date: 2026-09-09

This document supplies a self-contained proof of the finite-dimensional abstract theorem, separating classical matrix-approximation ingredients from the electromagnetic burden reduction.

## Theorem setup

Let

\[
Q=S_0^\dagger S,
\qquad
D=I-Q,
\]

where `S0` is unitary and `S` is passive, so

\[
\|Q\|_2\le1.
\]

Let the incident channel space have finite dimension `N`, with a complete orthonormal power-normalized basis. Define

\[
X_a=2\operatorname{Re}\langle x_a,Dx_a\rangle
\]

and suppose

\[
\sum_{a=1}^N X_a\ge L.
\]

Let the active correction obey

\[
\operatorname{rank}(A)\le r,
\qquad
\|A\|_F\le B,
\qquad
0\le r\le N.
\]

Define

\[
\mathcal C_{N,L}
=\left\{D:\ \|I-D\|_2\le1,
\quad 2\operatorname{Re}\operatorname{tr}D\ge L\right\}.
\]

The sharp passive-class envelope is

\[
\mathcal V(N,r,L,B)
=\inf_{D\in\mathcal C_{N,L}}
\inf_{\substack{\operatorname{rank}(A)\le r\\\|A\|_F\le B}}
\|D+A\|_F^2.
\]

We prove that `V=E_H`.

---

# Lemma 1 — Passivity gives the singular-value cap and nuclear burden

Because

\[
D=I-Q,
\]

we have

\[
\|D\|_2\le\|I\|_2+\|Q\|_2\le2.
\]

Thus every singular value `tau_i(D)` satisfies

\[
0\le\tau_i\le2.
\]

Also

\[
\sum_a X_a
=2\operatorname{Re}\operatorname{tr}D
\ge L.
\]

Using

\[
\operatorname{Re}\operatorname{tr}D
\le|\operatorname{tr}D|
\le\|D\|_*
=\sum_i\tau_i,
\]

we obtain

\[
\boxed{
\sum_i\tau_i\ge s,
\qquad s\equiv L/2.
}
\]

Since `tau_i<=2`, feasibility requires

\[
s\le2N,
\]

or

\[
\boxed{0\le L\le4N.}
\]

---

# Lemma 2 — Exact correction cost for a fixed D

Let the singular values of a fixed `D` be

\[
\tau_1\ge\tau_2\ge\cdots\ge\tau_N\ge0.
\]

For `r>=1`, define

\[
T_r(D)=\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}.
\]

The Eckart-Young-Mirsky theorem says that a rank-`r` correction can only act optimally in the singular subspaces associated with the largest `r` singular values. With no Frobenius-budget constraint, the best rank-`r` cancellation removes those components exactly and leaves

\[
\sum_{i=r+1}^N\tau_i^2.
\]

With the additional constraint `||A||_F<=B`, the controllable singular-value vector

\[
(\tau_1,\ldots,\tau_r)
\]

is projected radially onto the Euclidean ball of radius `B`. Therefore the uncancelled controllable norm is

\[
[T_r(D)-B]_+.
\]

Hence

\[
\boxed{
E_{\rm fix}(D;r,B)
=
[T_r(D)-B]_+^2
+
\sum_{i=r+1}^N\tau_i^2.
}
\]

For `r=0`,

\[
E_{\rm fix}(D;0,B)=\|D\|_F^2.
\]

This lemma is a direct matrix-approximation result and is not, by itself, claimed as novel.

---

# Lemma 3 — The universal minimizer uses exactly the minimum nuclear mass s

The spectral objective in Lemma 2 is coordinatewise nondecreasing in the nonnegative singular values. Suppose a candidate spectrum has

\[
\sum_i\tau_i=t>s.
\]

Scale every singular value by

\[
\alpha=s/t<1.
\]

The ordering and cap `tau_i<=2` remain valid, the total mass becomes exactly `s`, and neither term of `E_fix` can increase.

Therefore the relaxed spectral minimization attaining the universal lower envelope can be restricted to

\[
\boxed{\sum_i\tau_i=s.}
\]

Sharpness will later be established by constructing a passive diagonal `D` realizing the minimizing spectrum with exactly this burden.

---

# Lemma 4 — Reduction to one scalar m

Assume `0<r<N` and set

\[
q=N-r.
\]

Let

\[
m=\sum_{i=1}^r\tau_i
\]

be the singular-value mass in the controllable group. Then the tail mass is

\[
s-m.
\]

For fixed `m`, Cauchy-Schwarz gives

\[
\sum_{i=1}^r\tau_i^2\ge\frac{m^2}{r},
\]

with equality iff

\[
\tau_1=\cdots=\tau_r=m/r.
\]

Similarly,

\[
\sum_{i=r+1}^N\tau_i^2
\ge\frac{(s-m)^2}{q},
\]

with equality iff

\[
\tau_{r+1}=\cdots=\tau_N=(s-m)/q.
\]

Therefore the exact minimum at fixed `m` is

\[
\boxed{
F(m)=
\left[\frac{m}{\sqrt r}-B\right]_+^2
+
\frac{(s-m)^2}{q}.
}
\]

The equalized two-level spectrum is compatible with descending order iff

\[
\frac mr\ge\frac{s-m}{q},
\]

or

\[
m\ge\frac{rs}{N}.
\]

The singular-value cap gives

\[
\frac mr\le2
\quad\Rightarrow\quad
m\le2r,
\]

and

\[
\frac{s-m}{q}\le2
\quad\Rightarrow\quad
m\ge s-2q.
\]

Finally `0<=m<=s`. Thus

\[
\boxed{
m_{\min}=\max\left(\frac{rs}{N},s-2q,0\right),}
\]

\[
\boxed{m_{\max}=\min(s,2r).}
\]

Replacing `s=L/2` gives the form in the main theorem.

---

# Lemma 5 — Exact scalar minimizer

Let

\[
z=B\sqrt r.
\]

If `s<=z`, then the positive-part term can vanish while increasing `m` toward `s`; the unconstrained minimizer is

\[
\widehat m=s.
\]

If `s>z`, the stationary point lies in the active branch `m>z`. Differentiating

\[
F(m)=\left(\frac m{\sqrt r}-B\right)^2+rac{(s-m)^2}{q}
\]

gives

\[
\frac{dF}{dm}
=2\left(\frac mr-\frac{B}{\sqrt r}\right)
-2\frac{s-m}{q}.
\]

Setting this to zero yields

\[
N\widehat m=rs+qz,
\]

so

\[
\boxed{
\widehat m=\frac{rs+(N-r)B\sqrt r}{N}.
}
\]

Since `F` is convex, the constrained minimizer is its Euclidean clipping to the feasible interval:

\[
\boxed{
m_\star=\operatorname{clip}(\widehat m,m_{\min},m_{\max}).}
\]

Substitution gives

\[
\boxed{
E_H(N,r,L,B)=
\left[\frac{m_\star}{\sqrt r}-B\right]_+^2
+
\frac{(L/2-m_\star)^2}{N-r}.
}
\]

This proves the universal lower bound for `0<r<N`.

---

# Lemma 6 — Sharpness: the lower bound is attained by an admissible passive system

Take the minimizing two-level singular spectrum

\[
\tau_1=\cdots=\tau_r=m_\star/r,
\]

\[
\tau_{r+1}=\cdots=\tau_N=(s-m_\star)/(N-r).
\]

By construction every `tau_i` lies in `[0,2]`.

Define the diagonal Hermitian operator

\[
D_\star=\operatorname{diag}(\tau_1,\ldots,\tau_N)
\]

and

\[
Q_\star=I-D_\star.
\]

Each eigenvalue of `Q_star` is

\[
1-\tau_i\in[-1,1],
\]

so

\[
\|Q_\star\|_2\le1.
\]

Thus `D_star` belongs to the passive class. Moreover

\[
2\operatorname{Re}\operatorname{tr}D_\star
=2\sum_i\tau_i
=2s=L.
\]

Choose the active correction aligned with the first `r` singular directions and radially clipped to Frobenius norm `B`. Lemma 2 is then attained with equality, and Lemma 4 is attained with equality because both groups are equalized.

Therefore

\[
\boxed{
\mathcal V(N,r,L,B)=E_H(N,r,L,B).
}
\]

This establishes sharpness over the stated passive class.

---

# Edge cases

## r=0

Minimize

\[
\sum_{i=1}^N\tau_i^2
\]

subject to

\[
\sum_i\tau_i=s.
\]

Equalization gives `tau_i=s/N`, valid because `s<=2N`, and hence

\[
\boxed{E_H(N,0,L,B)=\frac{s^2}{N}=\frac{L^2}{4N}.}
\]

## r=N

All singular directions are controllable. For fixed total mass `s`, the minimum Frobenius norm is obtained by equalization:

\[
\|D\|_F=s/\sqrt N.
\]

Therefore

\[
\boxed{
E_H(N,N,L,B)=
\left[\frac{L}{2\sqrt N}-B\right]_+^2.
}
\]

---

# Perfect-correction threshold for the class envelope

For `0<r<N`, zero residual requires that all singular mass fit inside the `r` controllable directions while respecting `tau_i<=2`:

\[
s\le2r
\quad\Longleftrightarrow\quad
\boxed{L\le4r.}
\]

The smallest Frobenius norm of a controllable rank-`r` spectrum carrying total mass `s` is

\[
s/\sqrt r.
\]

Therefore the strength requirement is

\[
\boxed{B\ge s/\sqrt r=L/(2\sqrt r).}
\]

Equivalently,

\[
\boxed{rB^2\ge L^2/4}
\]

along with the independent rank condition `r>=L/4`.

These conditions characterize when **some passive system on the sharp class envelope** can be perfectly corrected. For a particular fixed `D`, perfect correction instead requires

\[
\operatorname{rank}(D)\le r,
\qquad
\|D\|_F\le B.
\]

---

# Simplified phase law

For `0<r<N`, let

\[
s=L/2,
\quad z=B\sqrt r,
\quad q=N-r.
\]

The lower clipping constraints never bind the stationary point:

\[
\widehat m-rs/N=qz/N\ge0,
\]

and

\[
\widehat m-(s-2q)
=\frac{q(2N-s+z)}{N}\ge0
\]

because `0<=s<=2N`.

Thus the only nontrivial clipping transition is the upper cap `m<=2r` when `s>2r`.

If `s<=2r`, substitution gives

\[
\boxed{E_H=\frac{[s-z]_+^2}{N}.}
\]

If `s>2r`, define

\[
\boxed{z_c=\frac{r(2N-s)}{N-r}.}
\]

Then

\[
\boxed{
E_H=
\begin{cases}
(s-z)^2/N,&0\le z\le z_c,\\[2mm]
(2r-z)^2/r+(s-2r)^2/(N-r),&z_c<z<2r,\\[2mm]
(s-2r)^2/(N-r),&z\ge2r.
\end{cases}
}
\]

This makes the strength wall and rank wall explicit.

---

# Broadband corollary

Let frequency-dependent variables satisfy the pointwise theorem, and define

\[
W=\int_\Omega w(\omega)d\omega,
\]

\[
L_\Omega\le\int_\Omega w(\omega)L(\omega)d\omega,
\]

\[
P_\Omega=\int_\Omega w(\omega)B^2(\omega)d\omega.
\]

For `0<r<N`, write the pointwise scalar program as

\[
F(s,m,b)
=
[m/\sqrt r-b]_+^2+(s-m)^2/(N-r),
\]

with the linear feasible relations

\[
m\ge rs/N,
\quad m\ge s-2(N-r),
\quad m\le s,
\quad m\le2r,
\quad s,b\ge0.
\]

`F` is jointly convex in `(s,m,b)`: the first term is the square of the positive part of an affine function, and the second is a convex quadratic. The feasible graph is convex. Partial minimization over `m` therefore makes `E_H` jointly convex in `(L,B)` after `s=L/2`.

`E_H` is nondecreasing in `L` and nonincreasing in `B`.

Pointwise,

\[
E(\omega)\ge E_H(N,r,L(\omega),B(\omega)).
\]

Weighted Jensen gives

\[
\frac1W\int wE_H\,d\omega
\ge
E_H\!\left(
N,r,
\frac{\int wL(\omega)d\omega}{W},
\frac{\int wB(\omega)d\omega}{W}
\right).
\]

By Cauchy-Schwarz,

\[
\frac{\int wB(\omega)d\omega}{W}
\le
\sqrt{\frac{P_\Omega}{W}}.
\]

Since `E_H` decreases with `B`, replacing the average `B` by this larger RMS upper bound can only decrease the right-hand side. Since the average burden is at least `L_Omega/W` and `E_H` increases with `L`, we conclude

\[
\boxed{
\mathcal E_\Omega
\ge
W E_H\!\left(
N,r,
\frac{L_\Omega}{W},
\sqrt{\frac{P_\Omega}{W}}
\right).
}
\]

Constant-in-frequency abstract extremizers attain equality whenever the corresponding pointwise parameters are feasible, so the broadband class bound is sharp under these assumptions.

---

# Scope

The proof establishes a sharp finite-dimensional operator envelope. It does not by itself impose:

- actuator geometry or singular-vector reachability,
- controller causality or stability,
- sensing noise or latency,
- material dispersion,
- finite efficiency,
- a geometry-to-channel-count law,
- historical novelty.

The tail-robust channel corollary addresses modal truncation/padding. The physical-normalization bridge identifies the burden with background-relative deviation plus absorption for a fixed unitary background. The Lorenz-Mie corollary converts the burden into the exact spherical extinction efficiency.
