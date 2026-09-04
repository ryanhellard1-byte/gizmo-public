# Phase 173: production campaign executor

Phase173 is the execution layer above the frozen Phase172 preregistration lock.
It does **not** modify physics, thresholds, seeds, analysis times, or the frozen
127-row manifest.

## Safety split

The campaign is deliberately split into two launch phases:

- `commissioning`: exactly the 8 non-blind rows;
- `blind`: exactly the 119 blinded rows.

`--submit --phase all` is forbidden. This prevents a scheduler smoke test from
accidentally releasing the entire blind campaign.

## Stage the 8 non-blind runs

```bash
python3 d3/production/phase173_execute_campaign.py \
  --phase commissioning \
  --backend slurm \
  --executable /path/to/GIZMO_D3 \
  --work-root /scratch/$USER/d3-phase173
```

This materializes and hashes the frozen Phase172 manifest, generates/caches the
required deterministic ICs, renders all preregistered 80-Gyr parameter/output
lists, and writes one scheduler script per run. It does not submit anything
without `--submit`.

## Submit commissioning

Scheduler resources are operational settings and must match the actual cluster.
Example only:

```bash
python3 d3/production/phase173_execute_campaign.py \
  --phase commissioning \
  --backend slurm \
  --executable /path/to/GIZMO_D3 \
  --work-root /scratch/$USER/d3-phase173 \
  --nodes 2 --ntasks-per-node 16 --mem-gb 128 --walltime 48:00:00 \
  --account YOUR_ACCOUNT --partition YOUR_PARTITION \
  --submit
```

After the 8 commissioning runs complete and the frozen Phase172 output validator
passes, launch the blind phase explicitly with `--phase blind --submit`.

## Claim boundary

Phase173 only fixes orchestration. It cannot convert a queued job into physics
evidence. The claim still requires completed 80-Gyr outputs, convergence, causal
controls, and blind validation under the already-frozen Phase172 rules.
