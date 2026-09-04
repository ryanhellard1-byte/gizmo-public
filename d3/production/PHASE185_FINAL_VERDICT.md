# Phase 185: Atomic campaign-verdict package

## Corrected verdict boundary

**ATOMIC NUMERICAL VERDICT PACKAGING: CLOSED. FINAL PHYSICS PROMOTION IS BLOCKED UNTIL PHASE186 IS READY.**

Phase184 assembles the complete campaign evidence set. Phase174 contains the
frozen radial-convergence and collision-audit gates. Phase187 contains the frozen
global energy-drift and center-of-mass momentum-drift gates. Phase185 packages
those implemented verdict families atomically so a valid negative numerical
result is preserved rather than mistaken for corrupt evidence.

Phase186 is the pre-data interlock: Phase185 is not allowed to call that package
a final physics verdict until every preregistered fatal Phase165 claim gate has
an implemented evaluator.

This architecture changes no D3 physics law, manifest row, radial-convergence
tolerance, claim epoch, RNG, collision kernel, or previously registered fatal
threshold.

## What Phase185 does

`phase185_final_verdict.py`:

1. requires Phase186 claim-completeness readiness before final-physics promotion;
2. refuses to overwrite an existing final verdict directory;
3. runs the frozen Phase184 collector against the immutable 127 completed runs;
4. verifies Phase184 PASS, 127-run cardinality, and the frozen manifest SHA256;
5. writes the exact embedded Phase172 manifest into a staging package;
6. runs the Phase174 radial/collision validator on the assembled evidence;
7. writes `phase174_physics_verdict.json`;
8. runs the Phase187 global runtime-invariant gates from `run_summary.csv`;
9. writes `phase187_runtime_verdict.json`;
10. combines Phase174 and Phase187 truth values without hiding a valid negative
    result;
11. hashes the manifest, evidence files, Phase184 report, and component verdicts;
12. writes `phase185_final_verdict.json` with provenance and the Phase186
    claim-completeness report;
13. atomically promotes the whole directory only after all required checks finish.

A valid Phase174 or Phase187 **FAIL is preserved and promoted** once Phase186 is
ready. That is deliberate. A negative registered result is science, not corrupted
output. Incomplete or invalid evidence is deleted from staging rather than
promoted.

## Why Phase186 still blocks final promotion

Phase187 closes two of the old missing families:

- global energy drift;
- center-of-mass momentum drift.

The remaining preregistered fatal evaluator families are:

- CDM total-profile stability through 10 Gyr;
- constant-SIDM2c total-profile recovery against the frozen M11 benchmark;
- SIDMx-minus-CDM H/L causal segregation at R2 and R3;
- HL-off mimic rejection;
- seed scatter versus branch separation stability.

Therefore the implemented claim-gate count is now 8 of 13 and Phase186 remains
`BLOCKED`. A green Phase174 plus green Phase187 result is still not the complete
preregistered physics verdict while those five families lack evaluators.

See `PHASE186_CLAIM_COMPLETENESS_GATE.md` and
`PHASE187_RUNTIME_INVARIANTS.md` for the machine-readable boundary and runtime
measurement definitions.

## Intended final command after Phase186 becomes READY

```bash
python3 d3/production/phase185_final_verdict.py \
  --run-root /path/to/immutable/runs \
  --final-dir /path/to/phase185_final_verdict \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

Exit codes remain:

- `0`: complete evidence and all implemented registered numerical gates PASS;
- `1`: complete evidence but at least one implemented registered numerical gate
  FAILS;
- `2`: claim-contract, evidence, provenance, or packaging error.

While Phase186 is `BLOCKED`, Phase185 exits through the error path before reading
campaign outputs or creating a final directory.

## Scientific claim boundary

A future Phase185 PASS is allowed only after Phase186 verifies full evaluator
coverage for the preregistered fatal Phase165 gate set. Even then it means the
completed internal numerical campaign passed its frozen internal validation
contract. It does **not** establish dark-matter discovery, observational
uniqueness, or external reproduction.
