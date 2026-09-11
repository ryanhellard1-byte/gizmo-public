# MENDS-X Phase 3 — 16-Week Flight-Readiness Execution Plan

NASA Phase 3 provides four months to complete the build, demonstrate operation in a relevant space environment, prepare the test matrix and operational validation plan, and show readiness for host-spacecraft integration. This plan assumes Phase 2 has already produced a working, calibrated engineering model and a controlled as-built evidence package.

## Phase-3 execution principle
The sole applicant remains PI/system owner, configuration authority, data owner, and final acceptance authority. Specialized fabrication and qualification work is purchased from qualified machine shops, electronics manufacturers, calibration/vacuum facilities, atomic-oxygen facilities, and environmental-test laboratories. Contractor use adds capacity without transferring technical ownership of MENDS-X.

## Weeks 1–2 — Host-specific interface closure
- Receive/resolve host spacecraft ICD and environmental requirements as soon as they are available.
- Perform delta review against Phase-2 assumptions: mounting, keep-out, ram exposure, supply voltage, grounding, data interface, peak/average power, thermal sink/source assumptions, contamination, pointing, radiation, shock/vibration and EMI/EMC.
- Freeze flight/qualification BOM and long-lead procurement.
- Freeze qualification/acceptance test matrix and trace every test to a host or instrument requirement.

**Exit:** ICD compliance matrix, controlled flight BOM, released procurement package, approved verification cross-reference matrix.

## Weeks 2–6 — Flight-like build and qualification article
- Fabricate/assemble flight-like sensor and at least one spare or replaceable critical subassembly set.
- Inspect incoming machined, etched and PCBA hardware against drawings/BOM.
- Execute subsystem bring-up and acceptance tests before full assembly.
- Preserve serialized configuration and calibration history.

**Exit:** flight-like/protoflight article assembled, electrically safe, functional, and configuration-controlled.

## Weeks 4–8 — Calibration transfer and functional regression
- Transfer Phase-2 calibration method to the flight-like article.
- Repeat guarded dark/null, electron-on/gas-off, selected pure-gas, repeatability and end-to-end density reconstruction tests.
- Establish pre-environment reference data for later drift comparison.

**Exit:** pre-environment calibration dataset and signed functional baseline.

## Weeks 6–12 — Relevant-space-environment and qualification campaign
Tests are sequenced to isolate failures and protect the schedule rather than placing every stress into one irreversible campaign.

### Environmental sequence
1. Baseline functional/calibration check.
2. Vibration/shock to host-defined or agreed qualification/protoflight levels.
3. Functional regression.
4. Thermal-vacuum cycling at host-defined survival/operational limits.
5. Functional/calibration regression.
6. EMI/EMC emissions and susceptibility testing against host-defined requirements.
7. Atomic-oxygen exposure/aging or combined LEO-environment testing where applicable to exposed surfaces and calibration stability.
8. Final functional/calibration regression.

The exact order may be modified by the selected facility and host verification plan, but pre/post functional checks are mandatory so environmental drift can be measured rather than guessed.

**Exit:** traceable environmental reports, anomalies dispositioned, calibration drift quantified, no unresolved Catastrophic/Critical flight risk.

## Weeks 10–13 — Host integration rehearsal
- Verify mechanical fit, fasteners, keep-outs, connector access and harness routing using host drawings or representative fixture.
- Verify power-up/down sequence, inrush/steady/peak current, grounding and fault behavior.
- Verify command/telemetry packet formats and data-rate assumptions.
- Exercise safe mode and loss-of-command behavior.
- Update contamination/handling plan and remove-before-flight items if any.

**Exit:** signed ICD compliance matrix with objective evidence for each closed interface.

## Weeks 12–14 — Operational validation plan
- Freeze on-orbit commissioning sequence.
- Define health/status channels, calibration checks, data-quality flags, outlier handling and degraded-mode rules.
- Define comparison strategy against NRLMSIS/reference products without using them as hidden calibration truth.
- Define first-light and early-orbit acceptance thresholds.
- Freeze telemetry-to-density processing version and coefficients.

**Exit:** operational validation plan and ground-to-flight configuration record.

## Weeks 14–16 — Final closeout and delivery margin
- Repeat end-to-end acceptance test after all environmental work.
- Close open anomalies or formally accept/defer them with rationale.
- Archive drawings, BOM, serial numbers, calibration, software/firmware hashes, test reports, risk register and verification matrix.
- Complete packing/handling/delivery documentation.
- Hold final schedule margin for retest, rework, replacement of a failed subassembly, or host-requested interface delta.

**Exit:** flight-readiness evidence package and on-time delivery to the integration path.

## Phase-3 risk-control rules

### If vibration fails
Inspect first, replace modular mechanical/electronic subassembly if isolated, repeat sine-burst/random-vibe only after root-cause containment. Maintain spare critical brackets, grids, boards and source components.

### If thermal-vacuum causes drift
Compare against pre-environment calibration, localize thermal coefficient, update compensation only if the physics remains stable and a repeat test verifies it. Otherwise narrow operating temperature range or revise thermal interface.

### If EMI/EMC fails
Apply filtering, shielding, grounding or clock/edge-rate mitigation at modular interfaces. Repeat only the failed emission/susceptibility cases before complete regression.

### If atomic oxygen causes material/calibration drift
Replace exposed material/coating, add AO-resistant shielding where it does not disturb neutral sampling, or quantify and compensate only if drift is repeatable and bounded. If an AO mitigation changes the sampling physics, return to calibration before flight acceptance.

### If a primary test facility slips
Use pre-qualified backup providers for separate test domains; do not make one facility responsible for every qualification gate. The qualification matrix is portable because requirements, fixtures, instrumentation channels and pass/fail criteria are documented independently of the facility.

### If host requirements arrive late or change
Maintain modular mechanical mounting, power conditioning and digital interface until the ICD delta review. Use the Phase-3 schedule margin for host-specific changes rather than redesigning the science core.

## Why the schedule is feasible
- Phase 2 has already retired the fundamental measurement risk before Phase 3 begins.
- Phase 3 is mostly flight-like fabrication, qualification, calibration regression and host integration, not invention of the sensing principle.
- Long-lead hardware is released in the first two weeks.
- Qualification tests run through specialist facilities rather than requiring the applicant to build aerospace infrastructure.
- Fabrication, documentation, software verification and facility scheduling run in parallel.
- The final two weeks are protected as retest/integration margin, not assigned to new features.

## Candidate external capacity already identified
Publicly documented facilities/vendors provide the required classes of work:
- University of Illinois LEO Synergistic Environment Simulation Facility: high vacuum, -80°C to +170°C thermal cycling, ~5 eV atomic oxygen, VUV, in-situ electrical connections/diagnostics.
- NASA Glenn EPRB: VF-9 atomic-oxygen environmental testing and VF-10 oil-free vacuum/thermal testing capability.
- Engineered Testing Systems, Indianapolis: aerospace vibration, shock, temperature and EMI/EMC testing.
- Kent Machine: precision aerospace prototype/build-to-print machining and inspection.
- UWE/PMA: AS9100D/ISO 9001 photochemical etching for precision aerospace metal parts.
- East/West Manufacturing Enterprises: AS9100-certified prototype/production PCBA and electromechanical box-build capability.

Facility identification is evidence of available market capability, not a claim of a reservation or contractual commitment. Written quotations and bookings are tracked separately.

## NASA scoring traceability
This execution plan is organized directly around the four Phase-3 25-point criteria:
1. Complete build and on-time delivery.
2. Build to host-spacecraft interface requirements.
3. Test/analysis for anticipated flight conditions and operation in a relevant space environment.
4. Flight-risk mitigation plus test matrix and operational validation plan.

## Source references
- NASA Orbital Clarity evaluation criteria: https://occ.nasatechleap.org/evaluation-criteria/
- NASA Orbital Clarity technical guidelines: https://occ.nasatechleap.org/technical-guidelines/
- NASA Orbital Clarity challenge timeline: https://occ.nasatechleap.org/challenge-phases-and-timeline/
- Illinois LEO facility: https://aerospace.illinois.edu/research/research-facilities/space-testing-equipment-services/LEO-facility
- NASA Glenn EPRB: https://www.nasa.gov/centers-and-facilities/glenn/electric-propulsion-research-building/
- Engineered Testing Systems: https://engineeredtesting.com/
- Kent Machine: https://kentmachine.com/industries/aerospace/
- UWE/PMA: https://uwepma.com/
- East/West Manufacturing Enterprises: https://www.ewme.com/pcb-assembly
