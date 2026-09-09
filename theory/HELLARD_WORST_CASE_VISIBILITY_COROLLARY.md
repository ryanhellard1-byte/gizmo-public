# Hellard Worst-Case and Average Visibility Corollary

Date: 2026-09-09

## Setup

Under the Hellard finite-dimensional theorem, let

\[
M=D+A
\]

be the residual channel operator after active correction. The sharp passive-class envelope gives

\[
\|M\|_F^2\ge E_H(N,r,L,B).
\]

This Frobenius statement immediately implies physically useful average- and worst-case visibility floors.

---

## 1. Average over a complete orthonormal incident basis

For any orthonormal basis `{x_a}` of the `N`-dimensional incident space,

\[
\sum_{a=1}^N\|Mx_a\|^2=\|M\|_F^2.
\]

Therefore

\[
\boxed{
\frac1N\sum_{a=1}^N\|Mx_a\|^2
\ge
\frac{E_H(N,r,L,B)}{N}.
}
\]

Thus the theorem is an average residual-power floor across every complete orthonormal channel basis.

---

## 2. Isotropic random-incidence average

Let `x` be uniformly distributed on the unit sphere of the complex `N`-dimensional incident space. Then

\[
\mathbb E[xx^\dagger]=I/N.
\]

Hence

\[
\mathbb E\|Mx\|^2
=\operatorname{tr}\left(M^\dagger M\,\mathbb E[xx^\dagger]\right)
=\frac{\|M\|_F^2}{N}.
\]

Therefore

\[
\boxed{
\mathbb E\|Mx\|^2
\ge
\frac{E_H(N,r,L,B)}{N}.
}
\]

This statement is basis independent.

---

## 3. Worst-case incident-channel floor

The spectral and Frobenius norms obey

\[
\|M\|_F^2\le N\|M\|_2^2.
\]

Consequently

\[
\boxed{
\|M\|_2^2
\ge
\frac{E_H(N,r,L,B)}{N}.
}
\]

Since

\[
\|M\|_2
=
\max_{\|x\|=1}\|Mx\|,
\]

there exists at least one unit-power incident channel combination satisfying

\[
\boxed{
\|Mx\|^2
\ge
\frac{E_H(N,r,L,B)}{N}.
}
\]

Thus if `E_H>0`, no active system satisfying the theorem assumptions can make every incident channel simultaneously residual-free.

---

## 4. Uniform-cloaking necessary condition

Suppose the design goal is the all-incidence requirement

\[
\|Mx\|^2\le\varepsilon
\qquad
\text{for every }\|x\|=1.
\]

Equivalently,

\[
\|M\|_2^2\le\varepsilon.
\]

A necessary condition is therefore

\[
\boxed{
\varepsilon
\ge
\frac{E_H(N,r,L,B)}{N}.
}
\]

If a target `epsilon` lies below this threshold, it is impossible within the abstract resource class regardless of how the active correction is optimized.

---

## 5. Broadband version

If the broadband theorem gives

\[
\int_\Omega w(\omega)\|M(\omega)\|_F^2d\omega
\ge
W E_H\left(
N,r,L_\Omega/W,\sqrt{P_\Omega/W}
\right),
\]

then

\[
\boxed{
\int_\Omega w(\omega)\|M(\omega)\|_2^2d\omega
\ge
\frac{W}{N}
E_H\left(
N,r,L_\Omega/W,\sqrt{P_\Omega/W}
\right).
}
\]

Likewise the weighted frequency integral of the isotropic random-incidence mean residual power is bounded below by the same right-hand side.

---

## 6. Physical interpretation

When `S0` is the fixed no-object/background propagation and the channels are power normalized, `Mx` is the residual background-relative outgoing deviation after active correction in the abstract model.

The corollary therefore converts the Hellard Frobenius resource envelope into two directly interpretable statements:

1. a lower bound on average residual visibility over incident-channel space;
2. a lower bound on the worst incident channel that an all-angle/all-polarization cloak must confront.

The result remains an operator-level statement. Translating `||Mx||^2` into a particular laboratory radar cross section, angular detector reading, or source power requires the corresponding channel normalization and measurement operator.
