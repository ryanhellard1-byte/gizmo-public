# MENDS-X P95-Based Uncertainty Budget

Status: engineering requirement allocation, not measured performance.

## Statistical correction
A 12% 1-sigma RSS budget does **not** imply margin to a 20% P95 accuracy target. For zero-mean Gaussian error, absolute-error P95 is approximately 1.96 sigma. Therefore 12% sigma corresponds to about 23.5% P95 before positive covariance.

## Revised allocations

| Term | Target 1-sigma/equivalent |
|---|---:|
| Absolute scale | 3.0% |
| Relative gain | 0.75% |
| Steering/background | 1.5% |
| Electron-energy contribution | 1.0% |
| Mixture/model residual | 4.5% |
| Ram-angle contribution | 2.0% |
| Thermal contribution | 1.5% |
| Spacecraft-potential/plasma contribution | 2.0% |

Independent combined sigma: approximately 6.58%, corresponding to approximately 12.90% Gaussian P95.

With a physically motivated positive-correlation screen (thermal↔electron energy, thermal↔gain, ram angle↔spacecraft potential, steering background↔spacecraft potential), combined sigma rises to approximately 7.02% and Gaussian P95 to approximately 13.75%. A one-million-draw correlated Monte Carlo reproduced approximately 13.75% P95, 96.74% within ±15%, and 99.56% within ±20% under those requirement-allocation assumptions.

These are requirements-budget calculations. G0–G6 must replace assumed distributions and covariance with measured values.
