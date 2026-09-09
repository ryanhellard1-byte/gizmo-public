# Hellard Modified-Inertia Research

This directory contains a falsification-first prototype for the current Hellard gravity hypothesis.

## Current benchmark

The surviving branch is a nonlocal modified-inertia model in frequency space:

\[
m\,\hat{\mathbf a}(\omega)\,\mu\!\left(\frac{\mathcal A_H(\omega)}{a_H}\right)=\hat{\mathbf F}(\omega),
\]

with

\[
\mathcal A_H(\omega)=\frac{1}{\sqrt{2}\pi}\int_0^\infty \theta_H(\omega'/\omega)\,|\hat{\mathbf a}(\omega')|\,d\omega'
\]

and benchmark kernel

\[
\theta_H(y)=\frac{7}{1+6y}.
\]

The acceleration scale is

\[
a_H=1.19\times10^{-10}\;\mathrm{m\,s^{-2}}.
\]

The interpolation used in the present test harness is

\[
\mu(x)=\frac{x}{\sqrt{1+x^2}}.
\]

## Required limits

1. Newtonian/high-acceleration: `mu -> 1`.
2. Isolated deep circular motion: `a^2/a_H = g_N`, giving `v^4 = G M a_H`.
3. High-frequency internal Solar-System motion embedded in a slow Galactic orbit must remain nearly Newtonian.
4. The benchmark scalar-amplitude, mode-separable functional has no leading angular quadrupole term; cross-frequency directional couplings are therefore a critical falsification target.

## What is and is not claimed

This is an effective research model, not a discovered law of nature and not yet a complete relativistic action. The code is intended to kill the hypothesis quickly if one universal parameter set cannot satisfy galaxy, Solar-System, wide-binary, conservation, and stability requirements.

## Files

- `hellard_kernel.py`: benchmark kernel and analytic-limit helpers.
- `run_tests.py`: deterministic Solar-System, circular-galaxy, and wide-binary proxy tests.

## Next research targets

- Replace proxy Solar-System checks with a derivation of the full planetary perturbation functional and Cassini-like quadrupole observable.
- Fit one universal kernel to raw SPARC rotation-curve data rather than an idealized RAR curve.
- Test wide-binary predictions against clean Gaia samples.
- Determine whether a conserved Galilean-invariant action can generate the benchmark mode-separable response.
