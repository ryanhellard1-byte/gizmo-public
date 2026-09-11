# MENDS-X Phase 2 — 16-Week Execution Plan

NASA Phase 2 gives winners four months to finalize the design, build an engineering model, and demonstrate the required measurement in ground testing. Full flight environmental qualification is not the Phase-2 exit condition; the Phase-2 exit is a finalized/documented design, hosted-payload compatibility, a requirements-linked development/test plan, and an engineering model that demonstrates the measurement in ground testing. Phase 3 closes the relevant-space-environment and flight-readiness evidence.

This plan is deliberately parallelized so external-facility and manufacturing lead times do not sit serially on the critical path.

## Workstream A — Measurement breadboard and calibration

### Weeks 1–2
Freeze controlled requirements, estimator, 5E×2F command set, interfaces, acceptance rules, test scripts, and data schema. Complete G0/G1 guarded dark-baseline and steering-only null testing. Exit: measured baseline/drift and steering-synchronous residual; redesign if the ≤0.5 fA allocation is missed.

### Weeks 2–4
G2 electron-on/gas-off map versus energy, field state, electron current, and temperature. Exit: measured background distribution/covariance.

### Weeks 4–7
G3 pure N2/O2/He 5E×2F response calibration and electron-energy metrology. Exit: measured response matrix, repeatability, linearity, energy centroid/EEDF width, covariance.

### Weeks 7–8
G4 blind mixtures with coefficients and estimator frozen before reveal. Internal goal: ≥95% of supported cases within ±15% absolute density error.

## Workstream B — Engineering-model hardware, started in parallel

### Week 1
Freeze hosted-payload planning envelope and interface assumptions. Release long-lead RFQs/POs for machined structure, etched grids/electrodes, PCBA, connectors, harnessing, source/cathode components, and critical spares.

### Weeks 1–3
Complete preliminary flight-like mechanical/electrical CAD and controlled BOM. Release build-to-print mechanical parts no later than the end of Week 2 where possible. This is intentionally earlier than breadboard calibration completion so a nominal 4–6 week build-to-print machining lead does not consume the back half of Phase 2.

### Weeks 3–7
Vendor fabrication proceeds while Workstream A calibration continues. Breadboard discoveries that affect the flight-like unit are handled through controlled change review; noncritical geometry changes are deferred rather than allowing uncontrolled scope growth.

### Weeks 6–9
Receive, inspect, and assemble engineering-model hardware. Bring up power, digital control, electron source, steering, Faraday-cup normalization, guarded readout, and telemetry independently before integrated operation.

### Weeks 9–12
Integrated engineering-model functional test and calibration transfer. Measure actual mass, volume, average/peak power, data rate, thermal behavior, pointing sensitivity, electrical noise, repeatability, and recovery after power cycling.

## Workstream C — Facilities and environment risk reduction

### Week 1
Confirm/book at least one vacuum/gas-calibration path and one backup. Maintain separate atomic-oxygen and environmental-test paths so one unavailable facility cannot stop the measurement demonstration.

### Weeks 4–10
Execute external vacuum/gas work as facility access permits. G5 atomic-oxygen response/aging is completed as early as practical, but atomic oxygen is not allowed to become a single-point blocker for the Phase-2 ground measurement demonstration. If AO access slips, preserve the dated facility plan and close the relevant-environment evidence in Phase 3.

### Weeks 11–14
Thermal, vibration and EMI/EMC risk-reduction or pre-compliance testing on the engineering model as appropriate to the still-provisional host assumptions. These tests reduce Phase-3 risk; they are not mislabeled as final flight qualification before a host-specific interface/environment is known.

## Workstream D — Evidence closure and site-visit package

### Weeks 12–15
G6: propagate measured response/background/EEDF distributions through the unchanged 23,760-state NRLMSIS campaign. Freeze the truthful altitude/performance claim and its uncertainty statement.

### Weeks 15–16
Repeat the end-to-end ground measurement demonstration, close all Phase-2 requirements, archive raw/processed data and calibration coefficients, freeze the engineering-model as-built configuration, and prepare the site-visit evidence package. Week 16 contains explicit schedule margin rather than new development scope.

## Phase-2 critical path and decision gates

1. **Long-lead fabrication** — release by Week 2; dual-source or simplify any item whose confirmed delivery would exceed Week 7.
2. **Low-current noise/null** — G0/G1 failure triggers front-end/shielding/layout redesign before gas calibration.
3. **Pure-gas identifiability** — G3 failure triggers energy/field-set reduction or geometry change before blind mixtures.
4. **Blind-mixture density performance** — G4 determines the defensible altitude/species claim; the claim narrows before the evidence is stretched.
5. **Facility access** — external vacuum/gas testing gets a primary and backup path; AO/environmental qualification can move within the Phase-2/Phase-3 boundary without blocking the required Phase-2 ground measurement demonstration.
6. **Hosted-payload interface changes** — keep mechanical/electrical interfaces modular until NASA/flight-provider specifications mature.

## Current hosted-payload planning envelope
- Mass: 270 g roll-up, <300 g target
- Volume: <0.5U target
- Average power: 4.5 W roll-up, <5 W target
- Peak power: 10 W planning ceiling; requires margin reduction/verification
- Normal telemetry: ~0.5–1.0 kbps
- Ram pointing: ±5° baseline target; characterize to at least ±10°
- No independent radio, propulsion, deployable boom, or released object

Host-dependent radiation, vibration/shock, thermal, contamination, and EMI/EMC limits remain controlled assumptions until a flight provider/interface is selected.

## Phase-2 planning budget envelope
This is a management estimate pending dated supplier/facility quotes, not a quoted cost claim.

- System/instrumentation development and metrology: $20k
- Prototype mechanical parts and precision grids/electrodes: $15k
- Electronics/PCBA/harness prototypes and spares: $15k
- Vacuum/gas calibration and reference metrology: $25k
- Atomic-oxygen risk-reduction testing: $15k
- Thermal/vibration/EMI pre-compliance: $15k
- Specialist engineering/QA/test support: $15k
- Fixtures, shipping and travel: $10k
- Insurance/admin/documentation allowance: $5k
- Second-build/rework/critical spares allowance: $25k
- Management reserve: $40k

**Phase-2 not-to-exceed planning envelope: $200k**, with $160k allocated and $40k held as management reserve until quotes and host requirements are known.

## External-capacity basis
The execution model does not require the sole applicant to personally own specialist aerospace infrastructure. The applicant remains PI/system owner and contracts bounded services to qualified providers.

Publicly documented candidate capacity includes:
- University of Illinois LEO Synergistic Environment Simulation Facility: high vacuum, thermal cycling, atomic oxygen, VUV, electrical feedthroughs/in-situ diagnostics.
- NASA Glenn EPRB VF-9: atomic-oxygen environmental testing; VF-10: oil-free vacuum and thermal shroud for space-power-component testing.
- Engineered Testing Systems (Indianapolis): aerospace environmental and EMI/EMC testing including vibration, shock, temperature and radiated/conducted testing.
- Kent Machine (Indiana): aerospace prototype/build-to-print precision machining and inspection; published build-to-print lead-time planning is approximately 4–6 weeks.
- UWE/PMA: AS9100D/ISO 9001 photochemical etching for aerospace/defense precision metal parts.
- East/West Manufacturing Enterprises: AS9100-certified prototype through production PCBA/box-build capability with published quick-turn prototype support.

Candidate-provider identification is not a representation that a quote, booking, or commitment exists until written confirmation is received.

## Source references
- NASA Orbital Clarity evaluation criteria: https://occ.nasatechleap.org/evaluation-criteria/
- NASA Orbital Clarity technical guidelines: https://occ.nasatechleap.org/technical-guidelines/
- NASA Orbital Clarity FAQ: https://occ.nasatechleap.org/frequently-asked-questions/
- Illinois LEO facility: https://aerospace.illinois.edu/research/research-facilities/space-testing-equipment-services/LEO-facility
- NASA Glenn EPRB: https://www.nasa.gov/centers-and-facilities/glenn/electric-propulsion-research-building/
- Engineered Testing Systems: https://engineeredtesting.com/
- Kent Machine aerospace capability: https://kentmachine.com/industries/aerospace/
- UWE/PMA: https://uwepma.com/
- East/West Manufacturing Enterprises PCBA: https://www.ewme.com/pcb-assembly
