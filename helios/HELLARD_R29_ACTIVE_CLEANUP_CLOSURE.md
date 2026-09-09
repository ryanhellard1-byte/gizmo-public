# HELIOS-R29 Active Cleanup Closure

## Status
Derived reduced-order engineering closure. Not a fundamental law of nature and not a validated RF/autoresonant hardware design.

## Motivation
HELIOS-R28 combines passive gyro-radius selectivity with mirror/loss-cone enhancement. The remaining triton tail may be addressed by an active resonant removal stage, motivated by published autoresonant mirror-product-removal work demonstrating selective fusion-product ejection in full 3-D particle dynamics while keeping fuel outside the driven bandwidth.

## Passive + mirror baseline
Let L_T0 be triton prompt-loss fraction before active cleanup and L_H be He-3 prompt-loss fraction. Representative R28 values are L_T0 ~ 0.955-0.977 and L_H ~ 0.10-0.15 for compact hotspots.

## Active cleanup variable
Let L_T* be the target triton-loss fraction after active cleanup and

Delta L_T = max(0, L_T* - L_T0).

Let E_kick be the average energy transferred by the active drive per additionally removed triton. This is a reduced-order energetic cost, not a detailed RF field solution.

Using the staged D-D / retained-He3 bookkeeping basis with E_cycle = 25.60 MeV per triton-producing cycle pair, an upper-bound fusion-power fraction for active cleanup is

P_AR / P_f <= Delta L_T * E_kick / E_cycle.

Define the Hellard Active-Cleanup Burden

A_H = Delta L_T * E_kick / E_cycle.

If the electrical/RF chain efficiency is eta_AR, then the required electrical fraction is

A_H,e = A_H / eta_AR.

## Representative R29 numbers
For L_T0 = 0.955 and L_T* = 0.99:

- Delta L_T = 0.035.
- If E_kick = 0.10 MeV, A_H = 1.367e-4 (0.0137% of fusion power).
- If E_kick = 0.25 MeV, A_H = 3.418e-4 (0.0342%).
- If E_kick = 0.50 MeV, A_H = 6.836e-4 (0.0684%).
- If E_kick = 1.01 MeV, A_H = 1.381e-3 (0.138%).

At P_f = 80.4 GW, the pessimistic 1.01-MeV-per-cleaned-triton bound corresponds to ~111 MW of resonant energy transfer. At eta_AR = 0.50 the electrical input bound is ~222 MW.

For the stronger passive baseline L_T0 = 0.977 and target L_T* = 0.99, the same worst-case 1.01 MeV bound falls to ~41 MW resonant transfer (~82 MW electrical at 50% efficiency).

## Neutron benefit
For He-3 prompt loss L_H = 0.13, the effective neutron fraction

f_n,eff = [2.45 + 14.1(1-L_T)] / [7.30 + 17.6(1-L_T) + 18.3(1-L_H)].

Representative values:

- L_T=0.900 -> f_n,eff ~ 0.1545
- L_T=0.955 -> f_n,eff ~ 0.1285
- L_T=0.977 -> f_n,eff ~ 0.1174
- L_T=0.990 -> f_n,eff ~ 0.1107
- L_T=0.995 -> f_n,eff ~ 0.1081

Therefore active cleanup provides diminishing neutron-return once passive+mirror selectivity is already strong. It should be treated as a cleanup stage, not the primary separation mechanism.

## R29 design rule
Use active resonance only if the passive/mirror stage has already satisfied the hard species-separation gate. Then require both

1. L_T* sufficient to satisfy system neutron closure, and
2. A_H,e below the available recirculating-power margin.

A compact combined engineering criterion is

C_R29 = min(S_H, P_margin/P_AR,e) >= 1,

where S_H is the selective-escape neutron closure number from R28.

## Claim boundary
The 2025 autoresonance paper demonstrates the mechanism for selective fusion-product removal in magnetic mirrors in full 3-D particle dynamics and Monte Carlo phase-space sampling. It does not provide a spacecraft-ready triton/He3 RF design for HELIOS. The present calculation only establishes that the energetic burden of cleaning up the residual triton tail can be small relative to the ~80-GW fusion scale under pessimistic per-particle energy-transfer bounds.

## Next required physics
A defensible R30 must solve the resonance-capture threshold and bandwidth for 1.01-MeV tritons in the actual R28 mirror/FRC field while checking that 0.82-MeV He-3 stays outside the capture band. Required outputs are drive amplitude, chirp rate, capture fraction, He-3 false-capture fraction, RF power, and robustness to collisions and time-dependent fields.
