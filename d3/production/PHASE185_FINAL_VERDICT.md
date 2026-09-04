# Phase 185: Atomic final campaign verdict

## Verdict boundary

**FINAL SOFTWARE VERDICT PACKAGING: CLOSED. REAL 127-RUN / 80-GYR CAMPAIGN STILL REQUIRED.**

Phase184 assembles the complete campaign evidence set. Phase174 already contains
the frozen radial-convergence and collision-audit physics gates. The remaining
operator hazard was that those two steps were separate and a negative physics
result could be lost, overwritten, or treated like an execution error.

Phase185 closes that gap without changing any physics law, manifest row,
threshold, radial bin, claim epoch, RNG, collision kernel, or blind-analysis
rule.

## What Phase185 does

`phase185_final_verdict.py`:

1. refuses to overwrite an existing final verdict directory;
2. runs the frozen Phase184 collector against the immutable 127 completed runs;
3. verifies Phase184 PASS, 127-run cardinality, and the frozen manifest SHA256;
4. writes the exact embedded Phase172 manifest into a staging package;
5. runs the frozen Phase174 radial/collision validator directly on the assembled
   campaign artifacts;
6. writes `phase174_physics_verdict.json` with the unchanged registered gates;
7. hashes the manifest, evidence files, Phase184 report, and Phase174 verdict;
8. writes `phase185_final_verdict.json` with the campaign-level status and
   provenance;
9. atomically promotes the whole directory only after evidence assembly and
   verdict evaluation finish.

A valid Phase174 **FAIL is preserved and promoted**. That is deliberate. A
negative registered result is science, not corrupted output. Only incomplete or
invalid evidence causes the staging directory to be deleted.

## Run it after all 127 production runs are complete

```bash
python3 d3/production/phase185_final_verdict.py \
  --run-root /path/to/immutable/runs \
  --final-dir /path/to/phase185_final_verdict \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

Exit codes:

- `0`: complete evidence and frozen Phase174 physics gates PASS;
- `1`: complete evidence but frozen Phase174 physics gates FAIL;
- `2`: evidence/provenance/packaging error.

The final directory contains:

- `phase172_manifest.csv`
- `evidence/run_summary.csv`
- `evidence/profiles.csv`
- `evidence/collision_log_summary.csv`
- `evidence/phase184_collection_report.json`
- `phase174_physics_verdict.json`
- `phase185_final_verdict.json`

## Scientific claim boundary

A Phase185 PASS means the completed preregistered 127-run / 80-Gyr numerical
campaign satisfied the frozen Phase172 evidence contract and the frozen Phase174
computational convergence/collision gates.

It does **not** by itself prove dark matter, establish observational uniqueness,
or eliminate competing physical models. Those claims require the appropriate
scientific comparison beyond this numerical validation package.
