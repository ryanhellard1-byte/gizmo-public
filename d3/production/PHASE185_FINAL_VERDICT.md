# Phase 185: Atomic campaign-verdict package

## Verdict boundary

**ATOMIC FINAL-VERDICT LOGIC: IMPLEMENTED. REAL CAMPAIGN PHYSICS: NOT YET DECIDED.**

Phase184 assembles the complete campaign evidence set. Phase174 evaluates the
frozen radial-convergence and collision-audit gates. Phase187 derives and
evaluates the seven additional fatal Phase165 claim families that were missing at
the Phase186 boundary. Phase185 packages all of those results atomically.

Phase186 is the pre-data interlock. It must report `READY`, meaning all 13 fatal
gate families have an evaluator. `READY` is implementation completeness only and
is not itself a physics result.

This path changes no D3 physics law, manifest row, numerical tolerance, radial
bin, claim epoch, RNG, collision kernel, or acceptance threshold.

## What Phase185 does

`phase185_final_verdict.py`:

1. requires Phase186 claim-completeness readiness;
2. requires Phase187 global-energy evidence;
3. refuses to overwrite an existing final verdict directory;
4. runs the frozen Phase184 collector against the immutable 127 completed runs;
5. verifies Phase184 PASS, 127-run cardinality, and the frozen manifest SHA256;
6. writes the exact embedded Phase172 manifest into a staging package;
7. runs Phase174 directly on the assembled radial/collision evidence;
8. preserves the supplied Phase187 energy evidence in the staging package;
9. builds Phase187 scalar evidence from the immutable run summary, profiles,
   snapshots, and energy evidence;
10. independently re-runs the Phase187 fatal-gate validator on that scalar table;
11. combines the results conjunctively:

```text
final PASS = Phase174 PASS and Phase187 PASS
```

12. hashes the manifest, evidence, intermediate reports, and verdict artifacts;
13. writes `phase185_final_verdict.json` and atomically promotes the directory
    only after the complete package is internally consistent.

A valid Phase174 or Phase187 **FAIL is preserved as a scientific FAIL**. It is
not converted into an evidence/provenance error. Incomplete, contradictory, or
corrupt evidence fails closed through the error path instead.

## Phase187 fatal families

Phase187 evaluates:

- global energy drift;
- center-of-mass momentum-drift proxy;
- CDM total-profile stability;
- constant-SIDM2c total-profile recovery against the frozen Yang-style target;
- SIDMx H/L causal segregation at R2 and R3;
- HL-off mimic rejection;
- SIDM2v seed stability.

For the Phase165 seed-stability wording, "seed scatter smaller than branch
separation," the gate is applied independently at R2 and R3 as

```text
abs(mean(paired SIDM2v-minus-CDM delta_S)) / sample_std(paired delta_S) >= 1
```

The sample standard deviation is the seed scatter. SEM is not used for this gate.

## Final command once the real campaign exists

```bash
python3 d3/production/phase185_final_verdict.py \
  --run-root /path/to/immutable/runs \
  --final-dir /path/to/phase185_final_verdict \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE \
  --energy-evidence /path/to/phase187_energy_evidence.csv
```

Exit codes:

- `0`: complete evidence and all registered fatal numerical gates PASS;
- `1`: complete evidence but at least one registered fatal numerical gate FAILS;
- `2`: claim-contract, evidence, provenance, contradiction, or packaging error.

## Scientific claim boundary

A future Phase185 PASS means only that the completed internal 127-run/80-Gyr
campaign satisfied its frozen internal validation contract. It does **not** by
itself establish dark-matter discovery, observational uniqueness, or independent
external reproduction.
