# Phase 185: Atomic campaign-verdict package

## Corrected verdict boundary

**ATOMIC NUMERICAL VERDICT PACKAGING: CLOSED. FINAL PHYSICS PROMOTION IS BLOCKED UNTIL PHASE186 IS READY.**

Phase184 assembles the complete campaign evidence set. Phase174 contains the
frozen radial-convergence and collision-audit gates. Phase185 packages those two
pieces atomically so a valid negative numerical result is preserved rather than
mistaken for corrupt evidence.

Phase186 adds an additional pre-data interlock: Phase185 is not allowed to call
that package a final physics verdict until every preregistered fatal Phase165
claim gate has an implemented evaluator.

This correction changes no D3 physics law, manifest row, numerical tolerance,
radial bin, claim epoch, RNG, collision kernel, or acceptance threshold.

## What Phase185 does

`phase185_final_verdict.py`:

1. requires Phase186 claim-completeness readiness before final-physics promotion;
2. refuses to overwrite an existing final verdict directory;
3. runs the frozen Phase184 collector against the immutable 127 completed runs;
4. verifies Phase184 PASS, 127-run cardinality, and the frozen manifest SHA256;
5. writes the exact embedded Phase172 manifest into a staging package;
6. runs the frozen Phase174 radial/collision validator directly on the assembled
   campaign artifacts;
7. writes `phase174_physics_verdict.json`, explicitly scoped to registered
   convergence/collision gates;
8. hashes the manifest, evidence files, Phase184 report, and Phase174 verdict;
9. writes `phase185_final_verdict.json` with provenance and the Phase186
   claim-completeness report;
10. atomically promotes the whole directory only after all required checks finish.

A valid Phase174 **FAIL is preserved and promoted** once Phase186 is ready. That
is deliberate. A negative registered result is science, not corrupted output.
Incomplete or invalid evidence is deleted from staging rather than promoted.

## Why Phase186 currently blocks this command

The original Phase165/167 final claim ladder also requires evaluators for:

- global energy drift;
- center-of-mass momentum drift;
- CDM total-profile stability through 10 Gyr;
- constant-SIDM2c total-profile recovery against the frozen Yang-style M11
  benchmark;
- SIDMx-minus-CDM H/L causal segregation at R2 and R3;
- HL-off mimic rejection;
- seed scatter smaller than the promoted branch separation.

Those evaluators are not supplied by Phase174. Therefore a green Phase174 result
is a convergence/collision PASS, not yet the complete preregistered physics PASS.

See `PHASE186_CLAIM_COMPLETENESS_GATE.md` for the machine-readable inventory.

## Intended final command after Phase186 becomes READY

```bash
python3 d3/production/phase185_final_verdict.py \
  --run-root /path/to/immutable/runs \
  --final-dir /path/to/phase185_final_verdict \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

Exit codes remain:

- `0`: complete evidence and the reachable registered numerical gates PASS;
- `1`: complete evidence but a registered numerical gate FAILS;
- `2`: claim-contract, evidence, provenance, or packaging error.

While Phase186 is `BLOCKED`, Phase185 exits through the error path before reading
campaign outputs or creating a final directory.

## Scientific claim boundary

A future Phase185 PASS is allowed only after Phase186 verifies full evaluator
coverage for the preregistered fatal Phase165 gate set. Even then it means the
completed internal numerical campaign passed its frozen internal validation
contract. It does **not** establish dark-matter discovery, observational
uniqueness, or external reproduction.
