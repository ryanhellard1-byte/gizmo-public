# Hellard's Law of Fusion Propulsive Closure

## Status

This is a derived systems-level closure criterion for pulsed fusion propulsion under the stated reduced-order assumptions. It is **not** a new fundamental law of nature and is not experimentally validated as a universal fusion-propulsion law.

## Definition

For a mission whose trajectory/vehicle model requires minimum direct propulsive efficiency `eta_min(alpha)` at integrated source specific power `alpha`, define the dimensionless Hellard closure number

\[
\mathcal H = \frac{\eta_N\,[1-f_n(1-C_n)]}{\eta_{\min}(\alpha)}.
\]

Where:

- `eta_N` = conversion efficiency from recoverable pulse energy to directed jet energy in the magnetic nozzle;
- `f_n` = fraction of fusion energy initially carried by neutrons;
- `C_n` = fraction of neutron energy recovered into nozzle-coupled ejectable plasma;
- `eta_min(alpha)` = minimum direct propulsion efficiency required by the mission at source specific power `alpha`.

The reduced-order energy side of the mission closes iff

\[
\boxed{\mathcal H \ge 1}.
\]

The recoverable fusion-energy fraction is

\[
\epsilon_{rec}=1-f_n(1-C_n)=(1-f_n)+f_n C_n.
\]

Thus the directed-jet fraction is `eta_N * epsilon_rec`.

## Equivalent neutron bounds

Minimum neutron recovery:

\[
C_{n,min}=1-\frac{1-\eta_{min}/\eta_N}{f_n}.
\]

Maximum tolerable neutron fraction at fixed recovery:

\[
f_{n,max}=\frac{1-\eta_{min}/\eta_N}{1-C_n}.
\]

These relations expose the trade between fuel choice, neutron capture, magnetic-nozzle efficiency, and source specific power.

## HELIOS examples

Using the archived 30-day efficiency envelope:

- D-T, `f_n=0.8006`, `C_n=0.30`, `alpha=145 kW/kg`, `eta_N=0.80`: `H ~= 0.52` -> FAIL.
- D-T, same point with `C_n~=0.81`: `H ~= 1.00` -> boundary/pass.
- Catalyzed D-D, `f_n=0.383`, `C_n=0.30`, `alpha=220 kW/kg`, `eta_N=0.88`: `H ~= 1.048` -> PASS.
- Catalyzed D-D, `f_n=0.383`, `C_n=0.30`, `alpha=145 kW/kg`, `eta_N=0.80`: `H ~= 0.866` -> FAIL.

## Validation performed 2026-09-09

A deterministic AWS reduced-order stress test evaluated 1,000,000 points spanning specific power, nozzle efficiency, neutron-energy fraction, and neutron recovery. The `H>=1` classification produced zero mismatches against the explicit energy-balance inequality because the criterion is its dimensionless normalized form.

Boundary cases solved at `H=1` and perturbed by +/-0.1% crossed the boundary in the expected direction.

## Limits

This criterion says nothing by itself about whether the fusion target ignites, whether gain is achieved, plasma stability, material lifetime, radiation damage, nozzle scaling, repetition-rate feasibility, fuel availability, or whether the assumed neutron-recovery mechanism can physically be built. Those require separate experimental and high-fidelity simulation gates.

A complete HELIOS architecture must therefore satisfy this closure criterion **and** independent target, stability, thermal, mass, lifetime, and fuel-cycle constraints.
