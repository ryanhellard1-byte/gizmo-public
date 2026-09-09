# Hellard many-body effacement bound

## Setup

Let a composite body's center of mass execute a slow approximately harmonic motion with displacement scale \(L\), frequency \(\omega_s\), and acceleration amplitude

\[
A_s\simeq \omega_s^2 L.
\]

Let internal modes \(j\) have displacement amplitudes \(\ell_j\), frequencies \(\omega_j\ge\omega_s\), and acceleration amplitudes

\[
A_j\simeq\omega_j^2\ell_j.
\]

The higher-order causal band used by the Hellard memory construction has exact scale kernel

\[
K_2(x)=\frac{4x^4}{(1+x^2)^3},
\]

with \(K_2(1)=1/2\). Evaluated at the slow scale \(\lambda=\omega_s\), define

\[
R_j\equiv\frac{\omega_j}{\omega_s}\ge1.
\]

Each internal mode contributes

\[
A_j^2K_2(1/R_j)
=A_j^2\frac{4R_j^{-4}}{(1+R_j^{-2})^3}
\le 4A_j^2R_j^{-4}.
\]

Since the target slow-mode power at its own band is

\[
P_s=A_s^2K_2(1)=\frac12A_s^2,
\]

the total fast-to-slow fractional power contamination obeys the exact inequality

\[
\boxed{
\epsilon_{\rm fast\to slow}
\le
8\sum_j
\left(\frac{A_j}{A_s}\right)^2R_j^{-4}
}.
\]

Using \(A_j/A_s\simeq R_j^2\ell_j/L\), the frequency factors cancel:

\[
\boxed{
\epsilon_{\rm fast\to slow}
\le
8\sum_j\left(\frac{\ell_j}{L}\right)^2
}.
\]

The earlier asymptotic estimate gave the same geometric scaling with an order-unity coefficient. The exact kernel normalization fixes the conservative coefficient in this power-ratio definition to 8.

## Many-mode consequence

A sufficient condition for composite-body spectral effacement is

\[
\sum_j(\ell_j/L)^2\ll1.
\]

Thus large internal acceleration amplitudes do not by themselves contaminate the slow center-of-mass channel. For scale-separated harmonic modes, the relevant control parameter is the geometry of the internal displacement relative to the center-of-mass displacement scale.

For mass/power weighted modes, replace the sum with the corresponding nonnegative weighted quadratic size sum.

## Example

For an Earth-Sun internal orbital displacement of order 1 AU embedded in a Galactic center-of-mass orbit of order 8 kpc,

\[
(\ell/L)^2\sim10^{-19},
\]

so even the conservative coefficient leaves contamination at roughly \(10^{-18}\) in power. Stellar internal scales relative to a kiloparsec-scale Galactic orbit are still smaller.

## What this proves

This is a rigorous many-mode bound for the causal spectrometer channel under the assumptions:

1. scale-separated approximately harmonic modes;
2. additive nonnegative band powers;
3. the exact \(K_2\) higher-order causal kernel;
4. finite/convergent weighted quadratic internal-size sum.

## What remains

This is not yet a complete nonlinear center-of-mass theorem. To finish that proof one must additionally bound the map from a small error in causal band power to the resulting error in the nonlinear inertial functional. A sufficient route is to prove a finite Lipschitz constant for the inertial response on the physically used domain, after which the acceleration-level center-of-mass error is bounded by that constant times the spectral contamination above.
