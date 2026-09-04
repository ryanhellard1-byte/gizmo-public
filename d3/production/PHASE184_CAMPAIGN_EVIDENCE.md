# Phase 184: Campaign evidence collector

## Verdict boundary

**SOFTWARE EVIDENCE ASSEMBLY: CLOSED. REAL 127-RUN / 80-GYR CAMPAIGN STILL REQUIRED.**

Phase 181 froze the per-run profile and collision extractors, but the final
campaign-level `run_summary.csv` assembly was still missing. There was also a
provenance hazard: Phase 175 fingerprints a completed run directory, so writing
new post-processing files into that directory after completion can invalidate
the completion-integrity proof.

Phase 184 fixes both problems without changing the physics law, manifest,
thresholds, RNG, collision kernel, radial bins, or blind-analysis gates.

## What the collector does

`phase184_campaign_evidence.py`:

1. loads the embedded frozen 127-row Phase 172 manifest and verifies its SHA256;
2. verifies the Phase 181 machine attestation and evidence executable;
3. requires every manifest run to have a `COMPLETE` Phase175/173 record;
4. checks exact manifest-row identity, completion/fatal markers, snapshot count,
   Phase181 evidence provenance, IC SHA256, and the frozen run-directory digest;
5. reads each immutable run directory without modifying it;
6. runs the frozen Phase181 profile and collision extractors in memory;
7. requires exactly one verified 80-Gyr profile source snapshot for every run;
8. stages `run_summary.csv`, `profiles.csv`, and
   `collision_log_summary.csv` in a separate evidence directory;
9. runs the frozen Phase172 output contract over the assembled campaign files;
10. atomically promotes the artifacts only if the entire 127-run collection
    passes. Partial campaign outputs are deleted on failure.

The collector refuses to overwrite an existing final evidence set.

## Run it after all 127 production runs are complete

```bash
python3 d3/production/phase184_campaign_evidence.py \
  --run-root /path/to/immutable/runs \
  --output-dir /path/to/phase184_evidence \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

The output directory contains:

- `run_summary.csv`
- `profiles.csv`
- `collision_log_summary.csv`
- `phase184_collection_report.json`

No output is written into any completed GIZMO run directory.

## Open the frozen physics verdict

A Phase184 PASS is not the dark-matter conclusion. It proves that the full
campaign evidence was assembled from provenance-locked completed runs and that
the Phase172 output/time contract passes.

The next command is the already-frozen Phase174 physics gate:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --manifest /path/to/frozen/phase172_manifest.csv \
  --run-summary /path/to/phase184_evidence/run_summary.csv \
  --profiles /path/to/phase184_evidence/profiles.csv \
  --collision-summary /path/to/phase184_evidence/collision_log_summary.csv \
  --out-json /path/to/phase184_evidence/phase174_physics_verdict.json
```

Only that validator, on the completed 127-run / 80-Gyr outputs, can establish the
registered R2/R3 convergence, timestep/kernel convergence, collision
conservation/clipping gates, and the downstream blind physics verdict.
