# Phase 187: Global runtime-invariant gates

## Verdict

**ENERGY-DRIFT AND CENTER-OF-MASS MOMENTUM-DRIFT EVALUATORS: IMPLEMENTED BEFORE PRODUCTION DATA.**

Phase165/166 preregistered fatal global runtime gates but the old execution lock
never supplied an engine-specific producer for those fields. Phase187 closes that
implementation gap without changing the frozen acceptance thresholds.

No 127-run production output was used to choose these definitions.

## Frozen energy-drift definition

GIZMO already writes a canonical global `energy.txt` diagnostic. Phase187 uses
its total internal, gravitational-potential, and kinetic-energy columns:

```text
E_total(t) = E_internal(t) + E_potential(t) + E_kinetic(t)
```

and freezes

```text
energy_drift_abs_max = max_t |E_total(t) - E_total(0)| / |E_total(0)|
```

The original Phase165/166 hard gate remains unchanged:

```text
energy_drift_abs_max < 0.01
```

The previously registered preferred campaign median remains non-fatal:

```text
median(energy_drift_abs_max) < 0.003
```

### Required GIZMO diagnostic support

The production and audit configurations now both define:

```text
COMPUTE_POTENTIAL_ENERGY
```

Without that compile option, GIZMO's global energy accounting would not include
the gravitational potential term required by this diagnostic. The audit and
production configurations still differ only by `SIDMX_D3_LIVE_AUDIT`.

The production renderer also freezes:

```text
TimeBetStatistics = 0.25 Gyr
```

in code units. GIZMO initializes the statistics schedule so the first diagnostic
is evaluated at the integration start, giving Phase187 a real time-zero baseline.
The parser fails closed if the baseline is absent, if the 80-Gyr endpoint is not
covered, if the file has the wrong column count, or if any value is non-finite.

## Frozen center-of-mass momentum proxy

The old schema named `momentum_drift_abs_max` as a center-of-mass momentum-drift
proxy but did not define an engine-side producer. Phase187 freezes the producer as
H+L mass-weighted center-of-mass velocity drift over the preregistered snapshots:

```text
v_COM(t) = sum_i m_i v_i(t) / sum_i m_i
momentum_drift_abs_max = max_t ||v_COM(t) - v_COM(0)||
```

The original hard threshold remains:

```text
momentum_drift_abs_max < 1e-4
```

in GIZMO code velocity units.

This definition is intentionally not normalized by a post-hoc velocity scale.
The old threshold was dimensioned as the center-of-mass proxy itself, so Phase187
freezes the direct engine quantity rather than inventing a new denominator after
the claim contract was written.

## Evidence path

`phase187_runtime_invariants.py` measures both quantities for one completed run.

`phase184_campaign_evidence.py` now records, for every manifest run:

- `energy_drift_abs_max`;
- `momentum_drift_abs_max`;
- `energy_statistics_rows`;
- `energy_source_sha256`.

`phase185_final_verdict.py` evaluates the fatal Phase187 gates alongside the
Phase174 convergence/collision gates. A real Phase187 failure is preserved as a
scientific `FAIL`; it is not discarded as corrupt evidence.

## Claim-completeness effect

Phase186 moves from 6 implemented fatal gates to 8 of 13:

```text
implemented: 8
missing:     5
```

The remaining missing fatal evaluator families are:

1. CDM stability;
2. constant-SIDM2c total-profile recovery;
3. SIDMx H/L causal signal;
4. HL-off mimic rejection;
5. seed stability / branch separation.

Phase186 therefore remains `BLOCKED`. Phase187 closes two genuine preregistered
runtime gates; it does not grant the final physics claim.

## Scientific boundary

Phase187 defines and implements how the registered runtime invariants are measured
and evaluated. It does not claim that any future production run passes them. The
real 127-run/80-Gyr campaign must supply the evidence, and the result is allowed
to be PASS or FAIL without changing these definitions afterward.
