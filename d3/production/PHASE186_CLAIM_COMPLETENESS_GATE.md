# Phase 186: Preregistered claim-completeness gate

## Verdict

**CURRENT FINAL-PHYSICS PIPELINE: BLOCKED, BY DESIGN.**

Phase185 can atomically package Phase184 evidence and a Phase174 numerical
convergence/collision verdict.  That is useful, but it is not yet the complete
preregistered Phase165/167 physics verdict.

Phase186 adds no particle physics, no threshold, no radial bin, no fit, and no
post-output tuning.  It simply inventories the fatal gates that were frozen
before the real production outputs exist and refuses to call the campaign
"final physics" until every one has an implemented evaluator.

## Frozen fatal gate inventory

The preregistered final-claim set requires:

1. energy drift;
2. momentum drift;
3. pair conservation;
4. Monte-Carlo probability clipping;
5. no untracked particle loss;
6. constant-SIDM2c total-profile recovery;
7. CDM stability;
8. SIDMx H/L causal signal, branch-minus-CDM at R2 and R3;
9. HL-off mimic rejection;
10. SIDM2v R2-to-R3 convergence;
11. timestep convergence;
12. neighbor convergence;
13. seed stability / branch separation.

The SIDM2c collapse-clock check is retained as a registered non-fatal diagnostic.

## What the current pipeline already covers

Phase174 plus the Phase181/184 evidence path already implements:

- pair conservation;
- probability clipping;
- particle-ID preservation across the scheduled snapshots;
- SIDM2v R2-to-R3 radial-profile convergence;
- timestep convergence;
- neighbor convergence.

## What is still missing

The current final-claim path does not yet implement evaluators for:

- global energy drift;
- center-of-mass momentum drift;
- CDM total-profile stability through 10 Gyr;
- Yang-style constant-SIDM2c total-profile recovery at 10 Gyr;
- SIDMx-minus-CDM H/L causal segregation at R2 and R3;
- HL-off mimic rejection at the frozen statistical boundary;
- seed-scatter versus branch-separation stability.

Those are not optional decorations.  The Phase165 claim ladder requires CDM
stability and SIDM2c recovery before D3 halo interpretation, then SIDMx causal
segregation plus HL-off rejection, then full SIDM2v convergence and seed
stability before the 10-Gyr physical M11 prediction is allowed.

## Why this phase exists

A validator can truthfully return PASS for every gate it implements and still be
incomplete relative to a preregistration.  Phase186 prevents that category error.
A green Phase174 result means the registered convergence/collision checks passed.
It must not silently become a green final-physics verdict while other registered
fatal gates have no evaluator.

## Current machine-readable result

```bash
python3 d3/production/phase186_claim_completeness.py
```

returns status `BLOCKED` while the seven missing fatal evaluators above remain.

`--require-ready` is available for any future final-promotion workflow that must
refuse to proceed until all fatal claim gates have executable coverage.

## Scientific boundary

Phase186 does **not** decide whether D3 passes or fails physically.  It guarantees
that the project cannot make that decision with an incomplete gate set.

The next implementation work is therefore sharply defined: close the seven
missing evaluators without altering the frozen physics or acceptance thresholds,
then run the real campaign and let the result be whatever the result is.
