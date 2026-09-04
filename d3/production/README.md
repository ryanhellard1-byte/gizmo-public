# Phase 172: production live-GIZMO lock

This directory starts the production physics campaign from the master software-validation point `a5e7b7e777bd211bf0f0b5c667a9957f476ef0ec`.

## Why Phase 172 exists

The earlier Phase-165/166 handoff was structurally useful but had four pre-output contradictions:

1. `identical_label_null` said to set `mH=mL` while the manifest and D3 startup contract required `mH/mL=3`.
2. timestep, neighbor-kernel, ablation, zero-cross-section, and permutation controls were not consistently paired to the same IC realization as their baselines.
3. the old blind validator declared profile and collision artifacts mandatory but only consumed `run_summary.csv`.
4. the old output gate accepted `final_time_Gyr >= 10` even though the frozen campaign explicitly requests analysis through 55.28 and 80.0 Gyr.

No production halo outputs existed when these repairs were made, so this is a preregistration repair, not post-hoc tuning.

## Frozen campaign

Run count: **127**. Blind runs: **119**.

Materialize and audit the frozen CSV:

```bash
python3 d3/production/phase172_lock.py --write d3/production/phase172_production_live_nbody_manifest.csv
```

Expected SHA-256:

`e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`

The required analysis schedule for every row is exactly:

`0, 0.25, 0.5, 1, 2, 5, 10, 20, 40, 55.28, 80 Gyr`.

Validate that schedule before launching production:

```bash
python3 d3/production/phase172_time_contract.py \
  --manifest d3/production/phase172_production_live_nbody_manifest.csv \
  --manifest-only
```

After production, the same fail-closed gate requires `run_summary.csv`, `profiles.csv`, and `collision_log_summary.csv`. Every run must be complete, reach its manifest endpoint of **80 Gyr**, and provide H/L/total profiles at every preregistered analysis time, including **55.28** and **80 Gyr**.

## Live GIZMO runtime mapping

The current master D3 engine already implements the required sentinels:

- `0`: CDM / zero ordinary SIDM cross section
- `-1`: full SIDM2v = HH+LL+HL
- `-2`: SIDMx = HL only
- `-3`: HL-off = HH+LL
- `-4`: HH only
- `-5`: LL only
- `-6`: HL+HH
- `-7`: HL+LL
- `-8`: constant isotropic SIDM2c benchmark, HH=2.25, LL=0.75, HL=1.125 cm^2/g
- `-9`: D3 zero-cross-section null

The equal-label null intentionally uses the ordinary positive constant-SIDM path at `1.125 cm^2/g` with `mH=mL=1`. This tests label invariance without weakening the frozen `mH/mL=3` D3 contract.

## Pairing repair

Numerical controls now reuse baseline IC seeds wherever the comparison is causal:

- half-timestep rows pair to R2 baseline runs;
- 48/96-neighbor rows pair to R2 baseline runs;
- channel ablations pair to full SIDM2v at the same resolution and seed;
- SIDM2c half-timestep rows pair to SIDM2c base rows;
- D3 mode-9 nulls pair to CDM R2 rows;
- particle-order tests pair to normal R2 SIDM2v rows and change only within-species file order while preserving particle IDs.

## Phase 174 radial convergence closure

Phase174 implements the profile-level convergence validator that the old Phase166 package promised but never wired to `profiles.csv`.

It preserves the frozen fatal thresholds and domain:

- SIDM2v R2 -> R3 profile delta `< 10%`;
- SIDM2v `T_base` -> `T_half` profile delta `< 5%`;
- SIDM2v `K_low`/`K_high` -> `K_base` profile delta `< 7%`;
- `0.03 <= r/r_s <= 3`;
- fatal inherited epoch `10 Gyr`.

The operational metric is the maximum pointwise fractional H/L density difference over exact matched seeds and identical radial bins. Interpolation and post-hoc smoothing are forbidden. The same metric is reported at the other Phase172 epochs as nonfatal diagnostics.

The validator also consumes `collision_log_summary.csv` and requires the participating SIDM2v runs to satisfy the frozen pair-conservation and probability-clipping limits.

Self-test:

```bash
python3 d3/production/test_phase174_radial_convergence_validator.py
```

Production validation:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --profiles /path/to/profiles.csv \
  --collision-log-summary /path/to/collision_log_summary.csv \
  --out-json phase174_radial_convergence_result.json
```

See `PHASE174_RADIAL_CONVERGENCE_GATE.md` for the frozen metric definition and claim boundary.

## Claim boundary

Passing this lock means the production experiment is executable and preregistered. It does **not** mean the halo physics has passed. Real live-gravity outputs must still satisfy CDM stability, SIDM2c recovery, SIDMx/HL-off causal separation, resolution/timestep/neighbor convergence, and blind profile analysis before a physical D3/SIDMx halo claim is allowed.
