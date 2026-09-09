# Hellard Joint Fusion-Propulsion Closure Criterion

## Purpose

This extends the propulsion-only Hellard closure number by forcing the same post-neutron-recovery fusion-energy pool to pay both for directed exhaust and for electrical recirculation.

It is an energy-conservation screening relation, not a fundamental law of nature and not a substitute for a coupled PGMN plasma simulation.

## Definitions

Let

- `eta_N` = magnetic-nozzle conversion efficiency applied to the energy remaining for thrust,
- `f_n` = fusion-energy fraction initially carried by neutrons,
- `C_n` = neutron-energy recovery fraction into useful plasma,
- `Q_eff` = degraded/effective target gain,
- `eta_d` = electrical-to-target driver efficiency,
- `a` = auxiliary electrical demand as a fraction of fusion energy,
- `eta_min(alpha)` = minimum propulsion efficiency required by the mission at integrated source specific power `alpha`.

The post-neutron-recovery usable fraction is

`A = 1 - f_n*(1-C_n)`.

The minimum electrical recirculation fraction is

`r = 1/(Q_eff*eta_d) + a`.

Assuming this electrical energy is drawn from the same recovered plasma-energy pool as thrust, the maximum remaining fraction available to the nozzle is

`A-r`.

Define

`H_joint = eta_N * [A-r] / eta_min(alpha)`

or

`H_joint = eta_N * [1-f_n*(1-C_n) - (1/(Q_eff*eta_d)+a)] / eta_min(alpha)`.

## Closure condition

- `H_joint >= 1`: reduced-order joint thrust + electrical recirculation closure.
- `H_joint < 1`: the design point cannot simultaneously meet mission thrust-energy demand and pay its stated electrical recirculation burden under these assumptions.

The propulsion-only criterion is recovered in the limit `Q_eff -> infinity` and `a -> 0`.

## Inverted gain requirement

Provided the denominator is positive,

`Q_eff,min = 1 / { eta_d * [A - a - eta_min(alpha)/eta_N] }`.

If

`A - a - eta_min(alpha)/eta_N <= 0`,

no finite target gain can close the point. This is important: sufficiently poor nozzle efficiency, high neutron fraction, low neutron recovery, or demanding mission specific-power point cannot be rescued by simply increasing fusion gain.

## R19 correction

For catalyzed D-D with

- `f_n = 0.383`,
- `C_n = 0.31`,
- `alpha = 220 kW/kg`,
- `eta_N = 0.88`,
- `Q_eff = 60`,
- `eta_d = 0.55`,
- `a = 0.02`,

we obtain approximately

- propulsion-only `H ~= 1.054`,
- joint `H_joint ~= 0.982`.

So the older nominal R19 point fails once electrical recirculation is paid from the same energy pool.

At the same specific power and neutron recovery, increasing the nozzle to `eta_N = 0.90` lowers the required effective gain to approximately `Q_eff,min ~= 55` and gives a small positive joint margin at `Q_eff=60`.

A more robust region lies toward higher specific power and/or higher nozzle efficiency, for example around `alpha ~ 240-250 kW/kg`, `eta_N ~ 0.90`, with improved target gain and driver efficiency.

## Validation

A 1,000,000-case deterministic AWS sweep was used to compare propulsion-only closure with this joint criterion over broad R19-like parameter ranges. Approximately 72.8% of points that passed propulsion-only closure were killed after recirculation was included. Boundary tests at exact `H_joint=1` flipped correctly under +/-0.1% perturbations in effective gain.

This screening result does not prove how a real power-generating magnetic nozzle partitions energy between thrust and electricity. That coupling must be measured or simulated directly.