# Phase165 native GIZMO production bridge

This directory binds the frozen Phase165 production experiment to the GIZMO
implementation that passed the master software gate.

The original 24,374-byte Phase165 CSV is embedded byte-exactly in
`phase165_manifest_frozen.py`. Materializing it reproduces the frozen SHA256:

`08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3`

## Frozen provenance

- Physics source commit: `a5e7b7e777bd211bf0f0b5c667a9957f476ef0ec`
- Green master workflow: `33842630968`
- Artifact: `9925447558`
- Artifact digest: `sha256:307f1185e41d47b30ab0c5e7ec26f37846ba70b579455e77e53bcc808f41ede3`
- `GIZMO_D3` SHA256: `677a881fc0964012df39c4736180ce77fb8400ca494f1a6b2776110b6d560155`

## Native branch mapping

| Manifest branch | GIZMO D3 sentinel |
|---|---:|
| CDM | `0` |
| SIDM2v | `-1` |
| SIDMx | `-2` |
| HL_off | `-3` |
| HH_only | `-4` |
| LL_only | `-5` |
| HL_HH | `-6` |
| HL_LL | `-7` |
| SIDM2c_const | `-8` |
| zero_cross_section_null group | `-9` |

The adapter renders a real GIZMO parameter file. It does not pass fictional
`--branch` or `--channels` flags to the executable.

## Fail-closed special rows

Four diagnostic rows are deliberately blocked:

- `PH165-0122`, `PH165-0123`: `identical_label_null`
- `PH165-0126`, `PH165-0127`: `permutation_reproducibility`

Their Phase165 notes require executor-side transformations whose exact semantics
are not frozen in current GIZMO. The adapter refuses to guess. The 123 other
rows, including all R0 commissioning rows and the claim-bearing core matrix, are
directly supported. The two zero-cross-section null rows use native mode 9.

## Materialize the frozen manifest

Run once after checkout:

```bash
python3 d3/production/phase165_manifest_frozen.py \
  d3/production/phase165_production_live_nbody_manifest.csv
```

Then verify it if desired:

```bash
sha256sum d3/production/phase165_production_live_nbody_manifest.csv
```

## Preflight

```bash
python3 d3/phase165_gizmo_adapter.py preflight
```

Expected result:

- 127 manifest rows
- 123 directly executable
- exactly 4 frozen special rows blocked

## Plan the first R0 commissioning row

```bash
python3 d3/phase165_gizmo_adapter.py plan \
  --run-id PH165-0049 \
  --ic-cache /scratch/d3/ic
```

Planning performs no expensive IC generation.

## Prepare a real run

Obtain the exact `GIZMO_D3` binary identified in `provenance_master_a5e7.json`,
then run:

```bash
python3 d3/phase165_gizmo_adapter.py prepare \
  --run-id PH165-0049 \
  --executable /opt/d3/GIZMO_D3 \
  --output-root /scratch/d3/runs \
  --ic-cache /scratch/d3/ic
```

Preparation verifies the manifest and executable hashes, generates or reuses the
deterministic M11 IC, verifies the IC SHA256, converts the frozen Gyr times to
GIZMO code time, writes `output_times.txt` and `params.txt`, and records the full
prelaunch provenance. It does not execute the simulation.

## Execute

Single-process commissioning launch:

```bash
python3 d3/phase165_gizmo_adapter.py run \
  --run-id PH165-0049 \
  --executable /opt/d3/GIZMO_D3 \
  --output-root /scratch/d3/runs \
  --ic-cache /scratch/d3/ic
```

For an HPC launcher, add for example:

```bash
--mpi-prefix "srun -n 64"
```

The adapter appends the actual GIZMO interface only:

```text
GIZMO_D3 params.txt 0
```

## Claim boundary

This bridge prepares and launches real GIZMO production rows. It does not invent
Phase166 observables. `profiles.csv`, `collision_log_summary.csv`, and the final
`run_summary.csv` must be derived from real outputs before the frozen blind gate
validator can pass.
