# Phase 185: commissioning-only evidence release gate

## Verdict boundary

**COMMISSIONING RELEASE CAN BE EVIDENCE-GATED WITHOUT OPENING BLIND RESULTS.**

Phase184 is the canonical full-campaign evidence collector. It intentionally waits
until all 127 frozen runs are complete before materializing the campaign profile
and collision tables. Phase185 preserves that blind-analysis boundary while
closing the earlier release-gate gap: the eight non-blind commissioning runs can
be analyzed before the 119 blind jobs are released, but blind runs cannot produce
Phase185 per-run derived evidence.

No Phase172 manifest row, seed, output time, cross section, RNG, collision kick,
radial bin, or acceptance threshold changes here.

## Frozen partition

The embedded Phase172 campaign remains exactly:

- 127 total runs;
- 8 non-blind commissioning runs;
- 119 blind runs;
- manifest SHA256 `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`.

## Execution behavior

`phase185_safe_resume.py` delegates all simulation execution to the existing
Phase181-attested Phase175 safe-resume stack.

For a commissioning row:

- `PAUSED_RESTARTABLE` remains resumable and produces no derived evidence;
- `COMPLETE` triggers `phase185_commissioning_evidence.py`;
- the finalizer re-verifies the raw completion fingerprint and machine-attested
  executable before extracting evidence;
- `run_summary.csv`, `profiles.csv`, and `collision_log_summary.csv` are written
  to a separate commissioning-evidence root;
- the three derived artifacts plus the raw run digest and provenance are locked by
  `phase185_COMMISSIONED.json`.

For a blind row:

- no Phase185 profile or collision extraction is allowed;
- `PAUSED_RESTARTABLE` and `COMPLETE` remain raw-only states;
- existence of a per-run directory under the Phase185 evidence root is a hard
  failure, not something silently ignored.

The 119 blind outputs therefore remain unopened until the all-127 Phase184
collector runs.

## Blind release

Stage the eight commissioning jobs through Phase185:

```bash
python3 d3/production/phase185_machine_batch_submit.py stage \
  --phase commissioning \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/ics \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/commissioning-evidence \
  --batch-root /path/to/batch \
  --mpi-prefix srun \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

After all eight are complete and finalized:

```bash
python3 d3/production/phase185_machine_batch_submit.py verify-commissioning \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/commissioning-evidence \
  --proof /path/to/phase185_commissioning_PASS.json \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

Blind staging requires that PASS proof. It does not merely trust the old JSON:
Phase185 re-verifies all eight current raw run digests, finalization-record hashes,
and derived artifact hashes at release time. It also refuses release if any of the
119 blind run IDs already has per-run derived evidence in the commissioning
evidence root.

Then stage the blind campaign:

```bash
python3 d3/production/phase185_machine_batch_submit.py stage \
  --phase blind \
  --commissioning-proof /path/to/phase185_commissioning_PASS.json \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/ics \
  --run-root /path/to/raw-runs \
  --evidence-root /path/to/commissioning-evidence \
  --batch-root /path/to/batch \
  --mpi-prefix srun \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

## Phase184 handoff

After all 127 raw runs are complete, do not concatenate the eight Phase185 files
with blind results by hand. Run the canonical Phase184 campaign collector against
the immutable raw run root. Phase184 independently re-verifies all 127 completion
records and creates the one campaign evidence set consumed by the frozen Phase174
physics validator.

Phase185 commissioning evidence is therefore a **release gate**, not a second
campaign-analysis path.

## Claim boundary

A Phase185 PASS proves that the non-blind commissioning evidence is current,
provenance-locked, and sufficient to release the frozen blind job set without
opening blind profiles early.

It does not prove that the 119 blind jobs have run, that the 127-run campaign
converges, or that D3 is physically correct. Those remain production results.
