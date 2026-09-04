# Phase 184: Campaign evidence collector

## Verdict boundary

**SOFTWARE EVIDENCE ASSEMBLY: CLOSED. REAL 127-RUN / 80-GYR CAMPAIGN STILL REQUIRED.**

Phase181 froze the per-run profile and collision extractors, but the final campaign-level `run_summary.csv` assembly was still missing. There was also a provenance hazard: Phase175 fingerprints a completed run directory, so writing new post-processing files into that directory after completion can invalidate the completion-integrity proof.

Phase184 fixes both problems without changing the physics law, manifest, thresholds, RNG, collision kernel, radial bins, or blind-analysis gates.

Phase185 adds the upstream release boundary: only the eight **non-blind commissioning** runs may be analyzed before blind release. The 119 blind runs remain raw-only until this Phase184 collector opens all 127 runs together.

## What the collector does

`phase184_campaign_evidence.py`:

1. loads the embedded frozen 127-row Phase172 manifest and verifies its SHA256;
2. verifies the Phase181 machine attestation and evidence executable;
3. requires every manifest run to have a `COMPLETE` Phase175/173 record;
4. checks exact manifest-row identity, completion/fatal markers, snapshot count, Phase181 evidence provenance, IC SHA256, and the frozen run-directory digest;
5. reads each immutable run directory without modifying it;
6. runs the frozen Phase181 profile and collision extractors in memory;
7. requires exactly one verified 80-Gyr profile source snapshot for every run;
8. stages `run_summary.csv`, `profiles.csv`, and `collision_log_summary.csv` in a sibling temporary evidence directory that is forbidden inside any frozen raw run directory;
9. runs the frozen Phase172 output contract over the assembled campaign files;
10. removes the internal manifest copy and atomically renames the complete staging directory into the final evidence directory only if the entire 127-run collection passes.

The collector refuses any pre-existing final evidence directory. Failure removes the staging directory, so a crashed or rejected collection cannot leave a partially promoted final evidence set.

## Blind-analysis handoff

Before Phase184, the Phase185 commissioning release gate may create external per-run evidence for the eight non-blind commissioning rows only. That evidence exists solely to decide whether the 119 blind jobs may be released.

Phase184 does **not** merge those early files into the final campaign by hand. It independently re-reads and re-verifies the immutable raw outputs for all 127 runs and constructs one canonical campaign evidence set. This keeps the final blind analysis independent of the earlier commissioning artifacts.

No Phase185 per-run profile or collision evidence is permitted for any of the 119 blind run IDs.

## Run it after all 127 production runs are complete

```bash
python3 d3/production/phase184_campaign_evidence.py \
  --run-root /path/to/immutable/runs \
  --output-dir /path/to/phase184_evidence \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

The output directory contains exactly:

- `run_summary.csv`
- `profiles.csv`
- `collision_log_summary.csv`
- `phase184_collection_report.json`

The final output directory and its staging directory must be outside every completed GIZMO run directory.

## Open the frozen physics verdict

A Phase184 PASS is not the dark-matter conclusion. It proves that the full campaign evidence was assembled from provenance-locked completed runs and that the Phase172 output/time contract passes.

The next command is the already-frozen Phase174 physics gate:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --manifest /path/to/frozen/phase172_manifest.csv \
  --run-summary /path/to/phase184_evidence/run_summary.csv \
  --profiles /path/to/phase184_evidence/profiles.csv \
  --collision-summary /path/to/phase184_evidence/collision_log_summary.csv \
  --out-json /path/to/phase184_evidence/phase174_physics_verdict.json
```

Only that validator, on the completed 127-run / 80-Gyr outputs, can establish the registered R2/R3 convergence, timestep/kernel convergence, collision conservation/clipping gates, and the downstream blind physics verdict.
