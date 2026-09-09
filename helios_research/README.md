# HELIOS Reduced-Order Research

This branch contains a reproducible reduced-order research model for the HELIOS hotspot-reservoir fusion concept and the proposed Hellard Burn-Transport Angle Criterion.

## Status

This is **not** a validated radiation-MHD model and does not establish a new law of physics. It is a falsifiable surrogate used to:
- track assumptions explicitly,
- reproduce parameter sweeps,
- test analytic transport scalings,
- identify regions that deserve 3-D MHD simulation,
- kill bad ideas quickly.

## Current candidate

For species Hall parameter chi_s, define

F_s(theta) = cos^2(theta) + sin^2(theta)/(1 + chi_s^2)

and

a_s = chi_s^2/(1 + chi_s^2).

For the burn-transport objective

H = (1-F_e)[w_alpha F_alpha + (1-w_alpha)F_e],

the interior optimum is

sin^2(theta*) = 1 / {2 [w_alpha a_alpha + (1-w_alpha) a_e]}

when the denominator coefficient is >= 1/2; otherwise theta*=90 degrees.

In the strong-electron-magnetization limit:

sin^2(theta*) = 1 / {2 [1-w_alpha + w_alpha chi_alpha^2/(1+chi_alpha^2)]}.

Representative HELIOS-like values chi_e=10, chi_alpha=1, w_alpha=0.5 predict theta*=55.0 deg and B_theta/B_z ~= 1.43.

## Research gates

1. Hotspot alpha-runaway under realistic loss physics.
2. Reservoir burn propagation in evolving helical fields.
3. 3-D MRT/mix with DSP-like topology.
4. Repetitive multi-MJ pulsed-power coupling and lifetime.
5. External validation of the pitch-angle scaling.

See `model.py`, `sweep.py`, and `test_model.py`.
