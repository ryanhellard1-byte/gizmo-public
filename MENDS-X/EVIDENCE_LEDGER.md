# MENDS-X Evidence Ledger

## Submission-safe computational claims

1. Frozen NRLMSIS 2.1 atmosphere campaign executed over 23,760 cases spanning 300–800 km and the predeclared latitude, local-time, seasonal, solar-flux, and geomagnetic grid.
2. NRLMSIS implementation reference validation passed 201 tests, including 200 case-by-case reference validations.
3. Atmosphere output SHA-256: `de5b576dbf62ef0770152efc451f37d951be7e005eaff22219e83ae0d2dc3ba1`.
4. Controlled E.6 candidate uses 14/18/22/35/100 eV and 20/80 V/m.
5. Retained E.6 broad-screen modeled result: 11.39% overall P95 absolute density error and 11.62% at 800 km. All altitude-bin P95 values were reported below 20%.
6. High-altitude atmosphere audit shows the 800-km H+He mass fraction is strongly regime-dependent and can approach unity in low-solar/quiet cases. These regimes remain mandatory validation cases.

## Quarantined / not submission-safe until reproduced

- Later finite-EEDF numbers reported as 11.25% full-grid P95 and 11.69% at 800 km.
- Any claim that the 10×species response matrix has numerical rank 8 and condition number ~776 unless the exact matrix, scaling convention, singular values, rank tolerance, covariance convention, code version, and hash are archived.

## Hardware evidence still open

- G0 guarded dark baseline and drift
- G1 steering-only synchronous residual, target ≤0.5 fA RMS equivalent after declared blanking/bandwidth
- G2 electron-on/gas-off background map versus energy, field, electron current, and temperature
- G3 N2/O2/He effective response coefficients for all 5E×2F states, including repeatability, linearity, covariance, electron-energy centroid and EEDF width
- G4 blind gas mixtures with estimator frozen before reveal; internal goal ≥95% of supported cases within ±15%
- G5 atomic-oxygen response and surface-exposure drift
- G6 measured-response propagation through the unchanged 23,760-state atmosphere ensemble

## Claim discipline

Do not say “demonstrated accuracy” for any modeled number. Do not say “flight ready” before environmental/interface verification. Do not say “NASA will save $1B.” The safe economic statement is a potential acquisition-cost comparison under explicit assumptions.
