# Phase180: target-machine execution packet

Phase180 adds no D3 physics, no manifest rows, and no acceptance-threshold changes.

It solves the final operator handoff problem: the current `master` checkout contains the latest production tools, but the Phase176 production executable must be built and attested from the canonical Phase176 physics source commit recorded in `phase176_machine_audit.py`.

That requires two checkouts on the target machine:

1. **Operator checkout**: latest `master`, used for Phase176/179/180 tooling.
2. **Canonical source checkout**: the exact Phase176 source commit used to build the production executable.

The current canonical source commit is:

```text
dc93bca31b19135a1f8510e838f23abc850869fb
```

## Generate the packet

Run this from the operator checkout:

```bash
python3 d3/production/phase180_target_machine_packet.py write-packet \
  --operator-tree /secure/d3/operator/gizmo-public \
  --canonical-source-tree /secure/d3/source/gizmo-public-phase176 \
  --binary-dir /secure/d3/bin \
  --machine-attestation /secure/d3/phase176_machine_attestation.json \
  --ic-root /scratch/d3/ics \
  --run-root /scratch/d3/runs \
  --batch-root /scratch/d3/batch \
  --systype Frontera \
  --build-jobs 8 \
  --build-mpi-prefix "mpirun -np 2" \
  --run-mpi-prefix "srun" \
  --mpi-tasks 64 \
  --slurm-option "--nodes=2" \
  --slurm-option "--ntasks=64" \
  --slurm-option "--time=48:00:00" \
  --output /secure/d3/phase180_target_machine_launch.sh
```

Inspect the generated launch script, then execute it on the target machine.

## What the packet does

The generated script:

- bootstraps or updates the operator checkout to `master`;
- bootstraps or updates the canonical source checkout to the exact Phase176 source commit;
- verifies the canonical source tree is clean;
- runs `phase176_machine_audit.py build-attest` using the canonical source tree;
- runs the Phase176 production-launcher preflight against the attested executable;
- stages the eight R0 commissioning jobs through Phase179;
- prints the exact command to verify the commissioning proof;
- prints the exact command to stage the 119 blind jobs after commissioning passes.

## Claim boundary

A Phase180 PASS means the target machine has an auditable command packet for launching the frozen campaign through the attested production path.

It still does **not** execute the 127-run halo campaign and does **not** prove the astrophysical claim.

The physics claim still requires:

```text
127 frozen live-gravity runs
-> 80 Gyr outputs
-> matched-seed convergence
-> blind validator
```
