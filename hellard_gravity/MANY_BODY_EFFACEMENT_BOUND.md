# Hellard geometric many-body effacement bound

## Setup

Let a composite body's center of mass execute a slow approximately harmonic motion with characteristic displacement scale L and angular frequency omega_s. Let an internal degree of freedom have displacement amplitude ell and frequency omega_f >> omega_s.

The higher-order causal band used by the Hellard memory construction has fast-to-slow power leakage

    K_2(omega_s/omega_f) ~ 4 (omega_s/omega_f)^4.

The internal acceleration amplitude is approximately

    A_int ~ omega_f^2 ell,

while the center-of-mass acceleration amplitude is

    A_CM ~ omega_s^2 L.

Therefore the fractional contamination of slow-band acceleration power by that internal mode is bounded asymptotically by

    epsilon_CM
      <= 4 (A_int/A_CM)^2 (omega_s/omega_f)^4
      = 4 (ell/L)^2.

Hence

    epsilon_CM <= 4 (ell/L)^2

for a single well-separated harmonic internal mode.

For multiple incoherent internal modes k with mass-weighted displacement amplitudes ell_k, the same argument gives the additive bound

    epsilon_CM <= 4 sum_k w_k (ell_k/L)^2,

where w_k are the relevant nonnegative mass/power weights, provided the internal bands are sufficiently separated from the slow center-of-mass band for the asymptotic K_2 tail to apply.

## Physical significance

The result is important because the large internal acceleration cancels against the quartic frequency suppression. Composite-body effacement is then governed by geometry rather than internal acceleration magnitude.

Examples:

* Earth-Sun internal orbital scale ell ~ 1 AU and Galactic center-of-mass scale L ~ 8 kpc gives epsilon_CM of order 1e-18.
* Stellar internal scales relative to an 8 kpc Galactic orbit give far smaller contamination.

## Scope

This is an asymptotic bound for scale-separated approximately harmonic internal modes. It is not yet a theorem for arbitrary broadband chaotic internal motion, resonant comparable-frequency modes, or strongly nonlinear many-body spectra. Those cases must be bounded using the exact causal kernel rather than the R^-4 asymptotic.
