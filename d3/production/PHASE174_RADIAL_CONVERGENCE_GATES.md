# Phase 174: radial convergence physics gates

Phase172 fixes the 127-run / 119-blind production manifest, matched numerical controls, the full 0-to-80 Gyr clock, and required output artifacts. Phase174 closes the remaining validator gap: the old Phase166 blind validator used a scalar 10-Gyr proxy for SIDM2v resolution convergence and explicitly deferred the promised radial-profile calculation to a profile-level validator that did not exist.

## Frozen gates

No physics threshold is changed here. Phase174 implements the preregistered gates exactly:

- SIDM2v R2 -> R3 species density-profile change: **< 10%**
- T_base -> T_half species density-profile change: **< 5%**
- K_low/K_high -> K_base species density-profile change: **< 7%**
- radial domain: **0.03 <= r/r_s <= 3**
- claim epoch: **10 Gyr**
- per-pair momentum residual: **< 1e-12**
- per-pair kinetic-energy residual: **< 1e-12**
- collision-probability clipping fraction: **< 0.005**

The 10-Gyr epoch is retained because the superseded scalar convergence proxy was explicitly `S_inner_10Gyr`, while Phase172 separately enforces output completeness through 55.28 and 80 Gyr.

## Radial metric

For a preregistered reference/test pair, Phase174 requires identical radial bin edges and evaluates, for every H, L, and total-density bin in the frozen radial interval,

```text
abs(rho_test / rho_reference - 1)
```

The gate value is the maximum over all matched seeds, required species, and common radial bins. The comparison therefore cannot pass by averaging away a localized bad bin.

No interpolation, smoothing, fitting, radial averaging, or data-dependent tolerance is allowed. Missing bins, duplicate bins, missing required species, non-finite values, and non-positive reference/test densities fail closed.

Only `rho` is used for the three frozen convergence percentages. `profiles.csv` also carries `sigma2`, `beta`, and `mass_enclosed`, but extending the preregistered 10% / 5% / 7% acceptance thresholds to additional observables after the fact would create a new physics gate rather than implement the old one.

## Matched comparisons

Phase172 repaired the old Phase165 pairing problem before production outputs existed. Phase174 consumes that repaired manifest directly:

- resolution: R3_gold reference vs R2_double test, full SIDM2v, same seed;
- timestep: R2 T_base reference vs R2 T_half test, full SIDM2v, same seed;
- neighbor: R2 K_base reference vs R2 K_low and K_high tests, full SIDM2v, same seed.

The dedicated CI asserts exactly four resolution pairs, three half-timestep pairs, and six neighbor comparisons.

## Required real outputs

Run the validator only on the frozen Phase172 manifest and real production artifacts:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --manifest phase172_production_live_nbody_manifest.csv \
  --run-summary run_summary.csv \
  --profiles profiles.csv \
  --collision-summary collision_log_summary.csv \
  --out-json phase174_radial_convergence_result.json
```

Phase174 first invokes the Phase172 time/output contract, so truncated campaigns or missing 55.28/80-Gyr profile products fail before radial physics interpretation begins.

## Collision audit

`collision_log_summary.csv` is no longer decorative input. Phase174 consumes the real per-run/channel audit values and enforces the frozen pair-conservation and probability-clipping thresholds.

## Claim boundary

A green Phase174 CI run proves the validator logic is executable and adversarially tested. It does not prove SIDM2v converges in nature or even in the production halo campaign. Those physics gates remain undecided until real 127-run outputs are supplied unchanged and the validator returns PASS.
