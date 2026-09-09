# Hellard Hybrid Electromagnetic Resource Theorem
## Rigorous finite-dimensional statement

### 1. Setup

Let the incident-channel space be `N`-dimensional and power normalized. Let

\[
Q=S_0^\dagger S,\qquad D=I-Q,
\]

where `S0` is unitary and the passive scattering operator `S` is contractive. Hence `Q` is contractive:

\[
\|Q\|_2\le 1,
\]

and therefore

\[
\boxed{\|D\|_2\le 2.}
\]

For an orthonormal basis \(\{x_a\}_{a=1}^N\), define

\[
X_a=2\operatorname{Re}\langle x_a,Dx_a\rangle.
\]

Assume the total burden obeys

\[
\sum_{a=1}^N X_a\ge L.
\]

Then

\[
\frac L2\le \operatorname{Re}\operatorname{tr}D
\le |\operatorname{tr}D|
\le \|D\|_*.
\]

If \(\tau_1\ge\cdots\ge\tau_N\ge0\) are the singular values of `D`, then

\[
\boxed{\sum_i\tau_i\ge L/2,\qquad 0\le\tau_i\le2.}
\]

An active correction `A` is constrained by

\[
\operatorname{rank}(A)\le r,\qquad \|A\|_F\le B,
\]

with \(0\le r\le N\). The residual is \(D+A\).

---

## 2. Exact optimum for a fixed physical system

For a **fixed** admissible deviation operator `D`, the exact best correction is determined by the actual singular values of `D`.

For \(r\ge1\), define

\[
T_r(D)=\left(\sum_{i=1}^r\tau_i^2\right)^{1/2}.
\]

Then the Eckart-Young-Mirsky theorem together with Euclidean projection of the controllable singular-value vector onto the Frobenius ball gives

\[
\boxed{
E_{\rm fix}(D;r,B)
=
\inf_{\substack{\operatorname{rank}(A)\le r\\\|A\|_F\le B}}
\|D+A\|_F^2
=
[T_r(D)-B]_+^2+\sum_{i=r+1}^{N}\tau_i^2.
}
\]

For \(r=0\),

\[
\boxed{E_{\rm fix}(D;0,B)=\|D\|_F^2.}
\]

Thus the Hellard value below is **not** the exact correction cost of every fixed `D`. It is the sharp universal lower envelope over the entire passive class with only the aggregate burden `L` specified.

---

## 3. Sharp universal Hellard resource envelope

Define the passive burden class

\[
\mathcal C_{N,L}
=
\left\{D:\ \|I-D\|_2\le1,\quad 2\operatorname{Re}\operatorname{tr}D\ge L\right\}.
\]

Define the class-optimal value

\[
\mathcal V(N,r,L,B)
=
\inf_{D\in\mathcal C_{N,L}}
\inf_{\substack{\operatorname{rank}(A)\le r\\\|A\|_F\le B}}
\|D+A\|_F^2.
\]

For \(0<r<N\), let \(s=L/2\), and let `m` denote the total singular-value mass placed in the `r` controllable modes. At fixed `m`, convexity minimizes the squared singular-value cost by equalization:

\[
\tau_1=\cdots=\tau_r=\frac mr,
\]

\[
\tau_{r+1}=\cdots=\tau_N=\frac{s-m}{N-r}.
\]

Ordering and the cap \(\tau_i\le2\) give the exact feasible interval

\[
\boxed{
m_{\min}=\max\left(\frac{rL}{2N},\frac L2-2(N-r),0\right),
}
\]

\[
\boxed{
m_{\max}=\min\left(\frac L2,2r\right).
}
\]

At fixed `m`, the minimum residual is

\[
F(m)
=
\left[\frac m{\sqrt r}-B\right]_+^2
+
\frac{(L/2-m)^2}{N-r}.
\]

Its unconstrained minimizer is

\[
\widehat m=
\begin{cases}
L/2,&L/2\le B\sqrt r,\\[2mm]
\dfrac{rL/2+(N-r)B\sqrt r}{N},&L/2>B\sqrt r.
\end{cases}
\]

Set

\[
\boxed{m_\star=\operatorname{clip}(\widehat m,m_{\min},m_{\max}).}
\]

Then define

\[
\boxed{
E_H(N,r,L,B)
=
\left[\frac{m_\star}{\sqrt r}-B\right]_+^2
+
\frac{(L/2-m_\star)^2}{N-r}.
}
\]

### Theorem

For \(0<r<N\),

\[
\boxed{\mathcal V(N,r,L,B)=E_H(N,r,L,B).}
\]

Equivalently, every admissible fixed system obeys the universal inequality

\[
\boxed{E_{\rm fix}(D;r,B)\ge E_H(N,r,L,B),}
\]

and the bound is sharp: there exists an admissible diagonal passive `D` with the equalized spectrum above and an aligned optimal active correction for which equality holds.

The burden range required by passivity is

\[
\boxed{0\le L\le4N.}
\]

---

## 4. Edge cases

No active dimensions:

\[
\boxed{E_H(N,0,L,B)=\frac{L^2}{4N}.}
\]

Full active rank:

\[
\boxed{E_H(N,N,L,B)=\left[\frac{L}{2\sqrt N}-B\right]_+^2.}
\]

These formulas are again sharp universal class envelopes. For a particular fixed `D`, use \(E_{\rm fix}\).

---

## 5. Perfect-correction thresholds

### Fixed-system criterion

A particular `D` can be perfectly corrected iff

\[
\boxed{\operatorname{rank}(D)\le r\quad\text{and}\quad \|D\|_F\le B.}
\]

### Sharp class-existence threshold

For \(0<r<N\), the universal envelope reaches zero,

\[
E_H=0,
\]

iff

\[
\boxed{L\le4r}
\]

and

\[
\boxed{B\ge\frac{L}{2\sqrt r}.}
\]

Equivalently,

\[
\boxed{rB^2\ge\frac{L^2}{4}}
\]

together with the independent rank requirement

\[
\boxed{r\ge L/4.}
\]

Interpretation: these conditions say that **there exists** an admissible burden-`L` passive system lying on the sharp envelope that can be perfectly corrected. They do not guarantee perfect correction of every passive `D` with the same aggregate burden.

For \(r=N\), the class envelope reaches zero iff

\[
\boxed{B\ge L/(2\sqrt N).}
\]

For \(r=0\), it reaches zero iff \(L=0\).

---

## 6. Broadband corollary

Let

\[
W=\int_\Omega w(\omega)\,d\omega,
\]

and define the pointwise burden

\[
\ell(\omega)=\sum_aX_a(\omega).
\]

Suppose

\[
L_\Omega\le\int_\Omega w(\omega)\ell(\omega)\,d\omega,
\]

and

\[
P_\Omega=\int_\Omega w(\omega)\|A(\omega)\|_F^2\,d\omega,
\]

with pointwise passivity and \(\operatorname{rank}A(\omega)\le r\).

The value function \(E_H(N,r,L,B)\) is jointly convex in `(L,B)` on its feasible domain and nondecreasing in `L`, nonincreasing in `B`. Applying the pointwise theorem, Jensen's inequality, Cauchy-Schwarz, and the two monotonicities gives

\[
\boxed{
\mathcal E_\Omega
\ge
W\,E_H\left(
N,r,
\frac{L_\Omega}{W},
\sqrt{\frac{P_\Omega}{W}}
\right).
}
\]

The abstract class bound is sharp: frequency-independent equalized extremizers and constant resource density attain equality whenever the corresponding pointwise parameters are feasible.

The class-existence perfect-correction requirements become

\[
\boxed{L_\Omega\le4rW}
\]

and

\[
\boxed{P_\Omega\ge\frac{L_\Omega^2}{4rW},}
\]

or

\[
\boxed{4rWP_\Omega\ge L_\Omega^2,}
\]

together with the rank threshold.

---

## 7. What is proved and what is not

**Proved under the stated assumptions:**

1. the exact fixed-`D` active-correction formula \(E_{\rm fix}\);
2. the sharp universal passive-class lower envelope \(E_H\);
3. the edge cases and class-existence perfect-correction thresholds;
4. the broadband abstract corollary, subject to the stated pointwise assumptions.

**Not proved by this theorem:** practical invisibility, causal hardware realizability, stability, sensing/latency limits, noise limits, finite actuator efficiency, geometry-specific passive-cloak bounds, or historical novelty.

The mathematical ingredients include standard singular-value inequalities and Eckart-Young-Mirsky low-rank approximation. The potentially distinctive contribution is their coupling to the passive electromagnetic extinction burden and the resulting closed-form active rank/strength resource envelope. Historical novelty therefore requires a dedicated literature comparison against matrix-approximation theory, scattering-matrix bounds, active cloaking/control theory, and electromagnetic sum-rule literature.

---

## 8. Maxwell validation status

The theorem has been tested numerically against the project’s 2-D cylindrical partial-wave models and 3-D Lorenz-Mie vector partial-wave models without a reported violation. These simulations are validation of the electromagnetic mapping, not the proof itself.

A valid counterexample would be a consistently normalized passive Maxwell system satisfying all theorem assumptions for which

\[
E_{\rm fix}(D;r,B)<E_H(N,r,L,B).
\]

Such a case would falsify either the theorem or the assumed mapping/normalization.
