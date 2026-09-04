# Phase 174: radial convergence gate closure

## Verdict

**RADIAL CONVERGENCE VALIDATOR IMPLEMENTED / REAL PRODUCTION OUTPUTS STILL REQUIRED.**

Phase166 froze the profile schema and the 10%, 5%, and 7% convergence thresholds,
but its executable validator only implemented a scalar `S_inner_10Gyr` R2/R3
proxy. The source itself said that a separate profile-level validator would
handle the full radial deltas. That validator was never wired to `profiles.csv`.

Phase174 closes that structural hole before production results are interpreted.

## Frozen inherited gates

The thresholds are unchanged:

- SIDM2v R2 -> R3 species profile change: `< 10%`
- SIDM2v `T_base` -> `T_half` profile change: `< 5%`
- SIDM2v `K_low`/`K_high` -> `K_base` profile change: `< 7%`

The inherited radial domain is unchanged:

```text
0.03 <= r/r_s <= 3.0
```

The fatal inherited comparison is evaluated at `10 Gyr`, the physical prediction
epoch used by the Phase165/166 acceptance package. Phase172 still requires the
full `0..80 Gyr` output schedule. Phase174 reports the same metric at every
Phase172 epoch as diagnostics, but does not silently turn those diagnostics into
new fatal thresholds.

## Pre-output metric clarification

The old files froze the threshold names as `*_profile_delta_max` but never
specified the exact denominator or radial reduction. Before looking at
production outputs, Phase174 makes that wording operational in the most literal
fail-closed way:

```text
resolution = max |rho_R2 / rho_R3 - 1|
timestep   = max |rho_Tbase / rho_Thalf - 1|
neighbor   = max(
               |rho_Klow  / rho_Kbase - 1|,
               |rho_Khigh / rho_Kbase - 1|
             )
```

The maximum is taken over:

- exact matched frozen seeds;
- species `H` and `L`;
- common radial bins with `0.03 <= r_mid/r_s <= 3`;
- the fatal epoch `t = 10 Gyr`.

There is no averaging, interpolation, smoothing, fit, rescaling, or
"close-enough" fallback. Compared runs must use identical radial bins.

The more refined/control calculation is the denominator: `R3`, `T_half`, or
`K_base`.

This clarification changes no numerical threshold and is frozen before real
production profiles are opened.

## Matched frozen pairs

Pairs are derived from the Phase172 manifest rather than hard-coded run IDs.

### Resolution

All four SIDM2v seeds in `R2_double` are matched to the same seeds in `R3_gold`.

### Timestep

All three SIDM2v `half_timestep_convergence` seeds are matched to their
`core_blind_production`, `R2_double`, `T_base`, `K_base` SIDM2v runs.

### Neighbor kernel

All three SIDM2v `K_low` and all three SIDM2v `K_high` rows are matched to their
same-seed `R2_double`, `K_base` SIDM2v runs.

If those frozen pair relations change, the validator fails.

## Required production tables

Run:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --profiles /path/to/profiles.csv \
  --collision-log-summary /path/to/collision_log_summary.csv \
  --out-json phase174_radial_convergence_result.json
```

The validator verifies the embedded Phase172 manifest checksum:

```text
e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d
```

`profiles.csv` must contain the frozen Phase166 species-profile schema and all
Phase172 analysis epochs for every run participating in a radial convergence
gate.

`collision_log_summary.csv` must contain `HH`, `LL`, and `HL` rows for every
participating SIDM2v run. Those rows must also obey the frozen runtime integrity
limits:

```text
max_pair_dP_over_P < 1e-12
max_pair_dK_over_K < 1e-12
prob_clip_fraction_max < 0.005
```

A radial profile cannot be promoted if the collision mechanics producing it
failed their own audit. Apparently even CSV files need adult supervision.

## Self-test

Run:

```bash
python3 d3/production/test_phase174_radial_convergence_validator.py
```

The fixture suite contains:

- one valid PASS case;
- R2/R3 >10% failure;
- half-timestep >5% failure;
- neighbor >7% failure;
- collision-conservation failure;
- mismatched radial-grid failure.

The tests use the actual frozen Phase172 manifest.

## Claim boundary

A green Phase174 self-test proves that the validator enforces the frozen
contract. It is not a physics result.

A production physics claim still requires real `profiles.csv` and
`collision_log_summary.csv` from the provenance-locked Phase173/Phase172 live
campaign.

```text
validator implemented != production profiles converged
```
