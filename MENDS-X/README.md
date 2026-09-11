# MENDS-X — NASA Orbital Clarity Challenge

Controlled Phase-1 engineering baseline, frozen 2026-09-10.

## Primary objective
Hosted in-situ thermospheric neutral mass-density sensing for LEO. Density is the primary product; coarse composition is secondary and quality-gated.

## Controlled sensing architecture

- Open neutral sampling path with plasma rejection
- Straight-path electron ionization terminated in a Faraday cup for electron-current normalization
- Five commanded electron energies: **14, 18, 22, 35, 100 eV**
- Two steering-field states: **20 and 80 V/m**
- Ten observables per scan
- Dual fixed collectors with bipolar push-pull steering and synchronous differential readout
- Weighted nonnegative least-squares density retrieval over modeled neutral species with bounded neutral-temperature profiling
- No quadrupole, time-of-flight analyzer, pump, accommodation chamber in the primary science path, or moving mechanism

## NASA benchmark
NASA Orbital Clarity identifies in-situ neutral mass density as the lead measurand. Target benchmark: **20% or better accuracy, 10% or better precision, 30 s or faster resolution** in the declared altitude range.

## Verified computational foundation

- Frozen NRLMSIS 2.1 campaign: **23,760 states**, 300–800 km
- Model implementation reference validation: **201 tests passed**, including 200 case-by-case reference cases
- Retained atmosphere-output SHA-256: `de5b576dbf62ef0770152efc451f37d951be7e005eaff22219e83ae0d2dc3ba1`
- Retained E.6 broad-screen result: **11.39% modeled P95 absolute density error overall; 11.62% at 800 km**
- These are computational results, not demonstrated hardware accuracy.

## Evidence rule
Every claim is classified as analytical, computational, requirement allocation, prior-art precedent, or measured. No simulated result is promoted to measured performance.

## Empirical closure gates

G0 dark baseline → G1 steering-only null → G2 electron-on/gas-off background → G3 N2/O2/He 5E×2F response + EEDF metrology → G4 blind mixtures → G5 atomic-O response → G6 measured-matrix propagation through the immutable 23,760-state atmosphere campaign.

## Current engineering targets

- Recurring delivered production cost: **< $10,000/unit at quantity 100**
- Mass: **<300 g** target; current planning roll-up 270 g
- Volume: **<0.5U equivalent** target
- Average power: **<5 W** target; current planning roll-up 4.5 W
- Nominal science telemetry: **0.5–1.0 kbps**
- Production objective: **~10 accepted units/week** after process qualification

These targets require supplier quotes, measurements, and final host-interface closure before being represented as verified.
