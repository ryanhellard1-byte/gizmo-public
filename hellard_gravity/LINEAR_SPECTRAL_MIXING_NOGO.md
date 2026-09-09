# Hellard linear spectral-mixing no-go theorem

## Status

This note records a structural result for the Hellard modified-inertia research branch. It rules out an entire class of tempting spectral actions. It is **not** a proof of a new law of nature.

## Setup

Work first with a finite Fourier truncation (e.g. a periodic trajectory over a long interval), with nonnegative dimensionless modal powers

\[
P_i = |a_i|^2/a_H^2,
\]

positive kinematic weights \(\alpha_i>0\) (for the usual acceleration-space representation, \(\alpha_i\propto\omega_i^{-2}\)), and linear spectral mixing

\[
Q_i = P_i + \sum_{j\ne i} M_{ij}P_j,
\qquad M_{ij}\ge 0.
\]

Let \(\Phi\) be differentiable and satisfy the MOND/Newton interpolation limits

\[
\Phi'(Q)\to 0 \quad(Q\to0),
\qquad
\Phi'(Q)\to1 \quad(Q\to\infty).
\]

Consider

\[
\mathcal K = \sum_i \alpha_i\,\Phi(Q_i).
\]

The normalized inertial coefficient for modal power \(P_k\) is

\[
c_k = \frac{1}{\alpha_k}\frac{\partial\mathcal K}{\partial P_k}
= \Phi'(Q_k)
+\sum_{i\ne k}\frac{\alpha_i}{\alpha_k}M_{ik}\Phi'(Q_i).
\]

## Theorem 1: uncompensated linear mixing fails the exact Newtonian multimode limit

Scale every occupied modal power as \(P_i\mapsto\lambda P_i\), with each relevant \(P_i>0\), and let \(\lambda\to\infty\). Then every mixed norm with support tends to infinity and

\[
\lim_{\lambda\to\infty} c_k
=1+\sum_{i\ne k}\frac{\alpha_i}{\alpha_k}M_{ik}.
\]

Therefore, if mode \(k\) feeds any other mixed norm (some \(M_{ik}>0\)), its high-acceleration coefficient is strictly larger than one. Exact Newtonian multimode inertia is recovered only if all such cross weights vanish.

## Theorem 2: the obvious linear compensation fixes the UV limit but fails global low-amplitude positivity

A natural attempted repair is

\[
\mathcal K_c
=\sum_i\alpha_i
\left[
\Phi(Q_i)-\sum_{j\ne i}M_{ij}P_j
\right].
\]

Now

\[
c_k^{(c)}
=\Phi'(Q_k)
+\sum_{i\ne k}\frac{\alpha_i}{\alpha_k}M_{ik}
\left[\Phi'(Q_i)-1\right].
\]

The high-amplitude limit is exactly one. But as all modal powers tend to zero,

\[
\Phi'(Q_i)\to0,
\]

and hence

\[
\lim_{P\to0}c_k^{(c)}
=-\sum_{i\ne k}\frac{\alpha_i}{\alpha_k}M_{ik}.
\]

For any mode that feeds at least one other mixed norm, this limit is negative. Thus this compensated linear-mixing class cannot be globally positive/convex over the full low-amplitude multimode domain.

## Consequence

A viable Hellard action must go beyond linear mixing of modal powers. The cross-environment contribution must be nonlinear and must switch off in **both** limits:

1. when the relevant source/target spectral power vanishes, and
2. when the complete system is in the Newtonian high-acceleration regime.

Promising remaining classes include nonlinear bounded pair interactions, auxiliary-memory fields, and doubled/in-in effective actions with a causal initial-value prescription.

## Scientific interpretation

This theorem does not establish modified inertia, MOND, or a Hellard law. It removes a broad class of superficially attractive completions and provides explicit mathematical requirements for the next candidate.
