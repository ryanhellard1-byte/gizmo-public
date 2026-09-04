# Phase 173: provenance-locked production launcher

Phase172 freezes the repaired 127-run, 119-blind production campaign and its
full 0-to-80 Gyr output contract. Phase173 adds the missing execution bridge:
verify the exact green production binary, build the correct frozen IC, render the
real GIZMO parameter file, launch it, and fingerprint what actually ran.

## Provenance lock

Phase173 is tied to the successful master validation point:

- master commit: `6353e4de5e627d926dec9114d36614340c376f67`
- workflow run: `33845004328`
- artifact: `9926223195`
- artifact digest: `sha256:41fc1d224c358afefb661f3075df09d254857d32cb6cc4dd60e7327c3624b9f8`
- `GIZMO_D3` SHA256: `e9f8167339ad6c3de0f10607b35f0b37d767a499f2ff17a5547e43cf04f7aceb`
- Phase172 manifest SHA256: `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`
- required endpoint: `80 Gyr`

The executable SHA above was independently recomputed from the archived master
artifact, not copied blindly from a filename.

## Preflight

Without an executable, this checks the immutable campaign/provenance contract:

```bash
python3 d3/production/phase173_production_launcher.py preflight
```

On the production machine, verify the candidate executable too:

```bash
python3 d3/production/phase173_production_launcher.py preflight \
  --executable /opt/d3/GIZMO_D3
```

Any executable other than the exact green artifact fails closed.

## Inspect the commissioning matrix

```bash
python3 d3/production/phase173_production_launcher.py r0-plan \
  --ic-root /scratch/d3/ics
```

Exactly eight `R0_commissioning_not_for_claims` rows must be returned.

Inspect one row without generating particles or launching GIZMO:

```bash
python3 d3/production/phase173_production_launcher.py plan \
  --run-id PH165-0049 \
  --ic-root /scratch/d3/ics
```

## Prepare one real run

```bash
python3 d3/production/phase173_production_launcher.py prepare \
  --run-id PH165-0049 \
  --executable /opt/d3/GIZMO_D3 \
  --ic-root /scratch/d3/ics \
  --run-root /scratch/d3/runs
```

Preparation performs these checks in order:

1. reconstruct and SHA-verify the frozen Phase172 manifest;
2. validate all 127 repaired row contracts, including the 80 Gyr schedule;
3. SHA-verify the exact production `GIZMO_D3` executable;
4. generate or reuse the Phase172 IC with the manifest's particle count, seed,
   mass ratio, and ordering transformation;
5. verify the IC metadata and snapshot SHA256;
6. render the native GIZMO `params.txt` and `output_times.txt`;
7. independently re-read the rendered parameters and verify mode, neighbors,
   softening, timestep, 80 Gyr endpoint, IC path, and all output times;
8. record the exact launch command and every relevant fingerprint in
   `phase173_PRELAUNCH.json`.

`prepare` does not run the simulation.

## Launch

Single-process form:

```bash
python3 d3/production/phase173_production_launcher.py run \
  --run-id PH165-0049 \
  --executable /opt/d3/GIZMO_D3 \
  --ic-root /scratch/d3/ics \
  --run-root /scratch/d3/runs
```

For a real HPC allocation, prepend the scheduler/MPI command:

```bash
--mpi-prefix "srun -n 64"
```

The launcher itself only appends GIZMO's real interface:

```text
GIZMO_D3 params.txt 0
```

A run is marked structurally `COMPLETE` only if the process exits successfully,
GIZMO emits its normal final-time completion marker, no `MPI_ABORT`/`ENDRUN`
marker appears, and the run directory contains at least the ten positive-time
snapshots required by the frozen 0.25-to-80 Gyr schedule.

## Controls that Phase172 repaired

Phase173 consumes the repairs rather than reinterpreting them:

- equal-label null: `mH=mL=1`, standard constant SIDM at `1.125 cm^2/g`;
- zero-cross-section null: native D3 mode `-9`;
- permutation reproducibility: same paired physical realization with
  `shuffled_within_species` ordering while particle IDs are preserved;
- timestep, neighbor and ablation controls use paired baseline seeds.

## Claim boundary

A successful Phase173 launch is execution evidence, not a halo-physics result.
After the runs finish, real `run_summary.csv`, `profiles.csv`, and
`collision_log_summary.csv` still have to pass the frozen Phase172 time/output
contract and the downstream blind physics gates. No launch metadata is allowed
to substitute for those observables.
