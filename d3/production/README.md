# Phase 172+: production live-GIZMO campaign

This directory contains the frozen production experiment, machine-attested
execution path, evidence collectors, convergence validators, and final fatal-gate
package for the D3/SIDMx campaign.

## Frozen campaign

Run count: **127**. Commissioning runs: **8**. Blind runs: **119**.

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

After production, the fail-closed evidence path requires every run to be complete,
reach its manifest endpoint of **80 Gyr**, and provide the scheduled snapshot,
profile, collision-audit, ID-preservation, and provenance evidence.

## Live GIZMO runtime mapping

The D3 engine implements the frozen runtime sentinels:

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

The equal-label null intentionally uses the ordinary positive constant-SIDM path
at `1.125 cm^2/g` with `mH=mL=1`. This tests label invariance without weakening
the frozen `mH/mL=3` D3 contract.

## Production execution chain

The current fail-closed chain is:

```text
Phase172 frozen manifest/time contract
  -> Phase176 target-machine build attestation
  -> Phase179/181 machine-attested batch dispatch and safe resume
  -> 8 commissioning runs and commissioning proof
  -> 119 blind production runs
  -> Phase181/184 immutable evidence collection
  -> Phase174 radial/convergence/collision gates
  -> Phase187 energy + seven fatal claim-family evaluators
  -> Phase185 atomic final numerical verdict
```

Phase186 is the implementation-completeness interlock. It now reports `READY`
when all 13 preregistered fatal gate families have evaluators wired into the final
path. `READY` does not mean the campaign physics passed.

## Final fatal-gate coverage

Phase174/181/184 cover pair conservation, probability clipping, particle
preservation, SIDM2v resolution convergence, timestep convergence, and neighbor
convergence.

Phase187 covers global energy drift, the center-of-mass momentum-drift proxy, CDM
stability, constant-SIDM2c total-profile recovery, SIDMx H/L causal segregation,
HL-off mimic rejection, and SIDM2v seed stability.

The Phase165 seed-stability rule is implemented literally as seed scatter smaller
than branch separation. At R2 and R3 independently:

```text
abs(mean(paired SIDM2v-minus-CDM delta_S)) / sample_std(paired delta_S) >= 1
```

The sample standard deviation is used for the seed scatter, not SEM.

## Claim boundary

The production **software and evaluator path can be ready while the physics is
still undecided**. The project does not have a final physical D3/SIDMx halo result
until all 127 live-gravity runs actually exist through 80 Gyr and Phase185 has
executed Phase174 plus Phase187 on those immutable outputs.

Even a future internal Phase185 PASS would establish only that the frozen internal
campaign contract passed. It would not by itself establish dark-matter discovery,
observational uniqueness, or independent external reproduction.
