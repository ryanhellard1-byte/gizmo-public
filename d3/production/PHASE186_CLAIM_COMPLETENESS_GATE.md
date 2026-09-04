# Phase 186: Preregistered claim-completeness gate

## Verdict

**CURRENT EVALUATOR COVERAGE: READY, 13/13 FATAL GATE FAMILIES IMPLEMENTED.**

This is an implementation-completeness verdict only. It is **not** a physics
PASS and it does not mean any production halo has satisfied the registered
gates.

Phase186 adds no particle physics, threshold, radial bin, fit, or post-output
tuning. It inventories the fatal gates frozen before the real production outputs
exist and refuses final-physics promotion unless every one has an evaluator wired
into the final-verdict path.

Phase187 closes the seven evaluator gaps that existed when Phase186 was first
introduced. Phase185 now executes Phase174 plus Phase187 on real campaign
evidence before it can return a final numerical PASS or FAIL.

## Frozen fatal gate inventory

The preregistered final-claim set requires:

1. energy drift;
2. momentum-drift proxy;
3. pair conservation;
4. Monte-Carlo probability clipping;
5. no untracked particle loss;
6. constant-SIDM2c total-profile recovery;
7. CDM stability;
8. SIDMx H/L causal signal at R2 and R3;
9. HL-off mimic rejection;
10. SIDM2v R2-to-R3 convergence;
11. timestep convergence;
12. neighbor convergence;
13. seed stability / branch separation.

The SIDM2c collapse-clock check remains a registered non-fatal diagnostic.

## Evaluator coverage

Phase174 plus the Phase181/184 evidence path implements:

- pair conservation;
- probability clipping;
- particle-ID preservation across scheduled snapshots;
- SIDM2v R2-to-R3 radial-profile convergence;
- timestep convergence;
- neighbor convergence.

Phase187 implements the remaining fatal families:

- global energy drift from an analysis-only, collisionless GIZMO
  `COMPUTE_POTENTIAL_ENERGY` probe;
- center-of-mass momentum-drift proxy from immutable scheduled snapshots;
- CDM total-profile stability through 10 Gyr;
- Yang-style constant-SIDM2c total-profile recovery at 10 Gyr;
- SIDMx H/L causal segregation at R2 and R3;
- HL-off mimic rejection;
- SIDM2v seed stability.

For seed stability, the frozen Phase165 wording is implemented literally as
"seed scatter smaller than branch separation." For each of R2 and R3, Phase187
uses matched SIDM2v-minus-CDM paired seed deltas and requires

```text
abs(mean(delta_S)) / sample_std(delta_S) >= 1
```

The denominator is the sample seed scatter, not the SEM. No threshold was changed.

## Machine-readable result

```bash
python3 d3/production/phase186_claim_completeness.py --require-ready
```

returns `READY` when all 13 fatal families have implemented coverage. `READY`
means only that the evaluator set is complete enough for Phase185 to read real
campaign evidence.

## Scientific boundary

Phase186 does **not** decide whether D3 passes or fails physically. The next
scientific decision requires the completed 127-run, 80-Gyr campaign, followed by
Phase174 and Phase187 evaluation through Phase185. A legitimate registered FAIL
must remain a physics FAIL rather than being mislabeled as corrupt evidence.
