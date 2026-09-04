# Phase179: machine-attested production batch gate

Phase179 adds no D3 physics, no manifest rows, and no new acceptance thresholds.

It replaces the stale Phase174 production-batch entry point with a scheduler
bridge that requires the Phase176 target-machine attestation before either
commissioning or blind jobs can be staged or submitted.

## What it locks

- exactly 8 non-claim R0 commissioning rows;
- exactly 119 blind rows;
- the embedded Phase172 manifest hash;
- the Phase176 machine attestation;
- the attested production executable SHA-256;
- audit-enabled/audit-free physical equivalence on the target machine;
- dispatch through `phase176_safe_resume.py`, not the historical Phase175-only path.

## Required order

1. Build and attest the production machine:

```bash
python3 d3/production/phase176_machine_audit.py build-attest \
  --source-tree "$PWD" \
  --systype Frontera \
  --jobs 8 \
  --mpi-prefix "mpirun -np 2" \
  --binary-dir /secure/d3/bin \
  --output /secure/d3/phase176_machine_attestation.json
```

2. Stage or submit the eight R0 commissioning jobs:

```bash
python3 d3/production/phase179_machine_batch_submit.py stage \
  --phase commissioning \
  --machine-attestation /secure/d3/phase176_machine_attestation.json \
  --executable /secure/d3/bin/GIZMO_D3_PROD \
  --ic-root /scratch/d3/ics \
  --run-root /scratch/d3/runs \
  --batch-root /scratch/d3/batch \
  --mpi-prefix "srun" \
  --mpi-tasks 64 \
  --slurm-option "--nodes=2" \
  --slurm-option "--ntasks=64" \
  --slurm-option "--time=48:00:00"
```

Add `--submit` only after the staged job scripts have been inspected.

3. Release the blind jobs only after commissioning completed and fingerprints pass:

```bash
python3 d3/production/phase179_machine_batch_submit.py verify-commissioning \
  --run-root /scratch/d3/runs \
  --machine-attestation /secure/d3/phase176_machine_attestation.json \
  --executable /secure/d3/bin/GIZMO_D3_PROD \
  --proof /scratch/d3/batch/commissioning/phase179_commissioning_proof.json
```

4. Stage or submit the 119 blind jobs:

```bash
python3 d3/production/phase179_machine_batch_submit.py stage \
  --phase blind \
  --machine-attestation /secure/d3/phase176_machine_attestation.json \
  --executable /secure/d3/bin/GIZMO_D3_PROD \
  --commissioning-proof /scratch/d3/batch/commissioning/phase179_commissioning_proof.json \
  --ic-root /scratch/d3/ics \
  --run-root /scratch/d3/runs \
  --batch-root /scratch/d3/batch \
  --mpi-prefix "srun" \
  --mpi-tasks 64 \
  --slurm-option "--nodes=2" \
  --slurm-option "--ntasks=64" \
  --slurm-option "--time=48:00:00"
```

## Claim boundary

A Phase179 PASS means the frozen campaign can be staged through the attested
production executable with commissioning-first blind release. It still does not
prove the halo claim. The 127 live-gravity runs, 80-Gyr outputs, convergence
gates, and blind validator still have to pass with real data.
