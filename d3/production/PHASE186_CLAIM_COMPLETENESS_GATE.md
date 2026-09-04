# Phase 186: Preregistered claim-completeness gate

## Verdict

**CURRENT FINAL-PHYSICS PIPELINE: BLOCKED, BY DESIGN.**

Phase185 atomically packages the Phase184 evidence and the implemented registered
verdict gates. Phase186 prevents that package from being promoted as the complete
Phase165/167 physics verdict until every preregistered fatal evaluator exists.

Phase186 adds no particle physics, no threshold, no radial bin, no fit, and no
post-output tuning. It inventories the fatal gates frozen before the real
production outputs exist and fails closed on missing implementation.

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

## Current executable coverage: 8 / 13

The production verdict path now implements:

- global energy drift, via Phase187;
- center-of-mass momentum-drift proxy, via Phase187;
- pair conservation;
- probability clipping;
- particle-ID preservation across the scheduled snapshots;
- SIDM2v R2-to-R3 radial-profile convergence;
- timestep convergence;
- neighbor convergence.

Phase187 uses GIZMO's canonical global energy diagnostic with gravitational
potential energy enabled and the frozen Phase165/166 `<1%` hard energy gate. It
also freezes the old center-of-mass momentum proxy as H+L mass-weighted COM
velocity drift and evaluates the original `<1e-4` hard threshold.

## What is still missing: 5 / 13

The current final-claim path still lacks executable evaluators for:

- CDM total-profile stability through 10 Gyr;
- constant-SIDM2c total-profile recovery at 10 Gyr;
- SIDMx-minus-CDM H/L causal segregation at R2 and R3;
- HL-off mimic rejection at the frozen statistical boundary;
- seed scatter versus branch separation stability.

Those are not optional decorations. The Phase165 claim ladder requires CDM
stability and SIDM2c recovery before D3 halo interpretation, then SIDMx causal
segregation plus HL-off rejection, then full SIDM2v convergence and seed
stability before the 10-Gyr physical M11 prediction is allowed.

## Why this phase exists

A validator can truthfully return PASS for every gate it implements and still be
incomplete relative to a preregistration. Phase186 prevents that category error.
A green Phase174 result means its registered convergence/collision checks passed.
A green Phase187 result means its registered runtime-invariant gates passed. Neither
may silently become the complete final-physics verdict while five registered
fatal gate families still lack evaluators.

## Current machine-readable result

```bash
python3 d3/production/phase186_claim_completeness.py
```

returns status `BLOCKED` while the five missing fatal evaluators above remain.

`--require-ready` is available for the final-promotion workflow and returns
nonzero until all fatal claim gates have executable coverage.

## Scientific boundary

Phase186 does **not** decide whether D3 passes or fails physically. It guarantees
that the project cannot make that decision with an incomplete gate set.

The next implementation work is sharply defined: close the five missing
evaluators without altering the frozen physics or acceptance thresholds, then run
the real campaign and let the result be whatever the result is.
