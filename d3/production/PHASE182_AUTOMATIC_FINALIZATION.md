# Phase 182: automatic production finalization

## Verdict

**RAW/DERIVED EVIDENCE BOUNDARY: REPAIRED. REAL 127-RUN PRODUCTION STILL REQUIRED.**

Phase181 closed the missing collision/profile extraction path, but those extractors
were still manual and its documented examples wrote derived CSV files into the
same raw run directory that Phase175 cryptographically fingerprints at completion.
That creates a bad integrity interaction: legitimate post-processing can make a
completed raw run appear modified on the next integrity check.

Phase182 fixes that before production outputs exist.

## Frozen things that do not change

Phase182 changes no manifest row, branch, seed, interaction parameter, cross
section, RNG, collision kick, analysis epoch, radial bin, or acceptance threshold.
The Phase172 manifest remains exactly 127 runs, 8 non-blind commissioning and 119
blind, with SHA-256:

`e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`

## Raw versus derived evidence

The Phase175 run directory remains the immutable raw simulation object. It contains
the exact IC/parameter fingerprints, appended GIZMO log, snapshots, restart state,
and completion digest.

Phase182 requires a separate evidence root. For each completed run it creates:

- `run_summary.csv`
- `profiles.csv`
- `collision_log_summary.csv`
- `phase181_profile_report.json`
- `phase181_collision_report.json`
- an exact frozen manifest copy
- `phase182_FINALIZED.json`

The finalization record hashes every derived artifact and also records the raw run
directory digest, completion-record hash, machine-attestation hash, and evidence
executable hash. Existing finalized evidence is idempotently verified; mismatched
or corrupted evidence is rejected rather than overwritten.

A Phase175 `PAUSED_RESTARTABLE` run is never finalized. Finalization occurs only
after raw status is `COMPLETE` and the Phase175 raw-directory digest re-verifies.

## Production scheduler

Stage the eight commissioning jobs through the Phase182 wrapper:

```bash
python3 d3/production/phase182_machine_batch_submit.py stage \
  --phase commissioning \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/bin/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/ics \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/derived-evidence \
  --batch-root /path/to/batch \
  --mpi-prefix "srun" \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

The generated Slurm job calls `phase182_safe_resume.py`. A scheduler/CPU-time pause
returns cleanly and remains restartable. A completed run automatically invokes the
external Phase182 finalizer.

After all eight commissioning jobs are complete and finalized:

```bash
python3 d3/production/phase182_machine_batch_submit.py verify-commissioning \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/derived-evidence \
  --proof /path/to/commissioning_PHASE182_PASS.json \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/bin/GIZMO_D3_EVIDENCE
```

Only that Phase182 PASS proof can release the 119 blind jobs:

```bash
python3 d3/production/phase182_machine_batch_submit.py stage \
  --phase blind \
  --commissioning-proof /path/to/commissioning_PHASE182_PASS.json \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/bin/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/ics \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/derived-evidence \
  --batch-root /path/to/batch \
  --mpi-prefix "srun" \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

## Full campaign assembly

Partial blind campaign assembly is intentionally rejected. Once all 127 frozen
runs are complete and finalized:

```bash
python3 d3/production/phase182_campaign_assemble.py \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/derived-evidence \
  --output-dir /path/to/campaign-ledger \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/bin/GIZMO_D3_EVIDENCE
```

The assembler re-verifies every raw completion and every per-run artifact hash,
concatenates the three frozen evidence CSVs in manifest order, reruns the Phase172
80-Gyr output contract, and then records the existing Phase174 radial convergence
result.

A Phase174 radial `FAIL` remains a scientific result. It does not get relabeled as
an evidence-pipeline crash. The ledger therefore distinguishes evidence integrity
from the eventual physics decision.

## Claim boundary

Passing Phase182 means the production campaign can move from scheduler completion
to validator-ready evidence without manual copy/paste and without corrupting the
raw-run integrity contract.

It still does **not** mean the 127 live 80-Gyr halo simulations have run, that the
convergence gates pass, that HL transport survives blind validation, or that D3 is
a correct physical description of dark matter. Those claims remain downstream of
the real production calculation.
