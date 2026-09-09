# Real Gaia wide-binary status

The branch now runs `wide_binary_realdata_shape_test.py` against the public statistically pure Gaia DR3 MS-MS catalog from Zenodo record 10062232.

The current reproducible CI run read 2,463 catalog rows and selected 1,494 systems after the frozen quality cuts.

The measured median normalized transverse-velocity profile versus projected separation was compared with two forward Monte-Carlo shape predictions using the same eccentricity/projection realization:

1. Newtonian quasi-Kepler model;
2. frozen Hellard v0.1 reduced spectral-dominance model with `a_H=1.12e-10 m/s^2`, `p=2`, `beta=1`.

A single normalization for each model was calibrated only on the two innermost, high-acceleration bins. The four outer bins were then scored without retuning the gravity parameters.

CI result:

- Newtonian outer-shape chi-square: 23.890
- Hellard outer-shape chi-square: 22.463
- delta chi-square (Hellard - Newtonian): -1.427

For equal-complexity fixed-shape models this corresponds to only a weak likelihood preference of roughly `exp(1.427/2) ~= 2.0` in favor of the Hellard profile. It is **not** a statistically compelling detection.

The outer observed medians are also substantially above both clean-binary predictions, especially around projected separations of several to ten kAU. This is exactly the regime where unresolved hierarchical triples, chance alignments, mass errors, and projection/eccentricity systematics can dominate.

## Scientific interpretation

The first real-data test does **not** kill the Hellard candidate, but it also does **not** establish an anomaly in its favor.

The correct statement is:

> On the current 1,494-system selected Gaia sample, the frozen Hellard separation-dependent profile is marginally better than the Newtonian profile in a simple outer-bin shape statistic, but the difference is weak and both simplified models leave substantial outer-tail residuals.

## Required next likelihood

A publishable comparison must forward-model or marginalize over:

- orbital phase and orientation;
- eccentricity distribution;
- stellar-mass uncertainty;
- astrometric covariance / relative proper-motion error;
- unresolved hierarchical triples;
- chance alignments / flybys;
- sample selection function;
- local Galactic background field variation;
- the exact causal-memory Hellard response rather than only the frozen reduced closure.

The model parameters that were already fixed by galaxy/benchmark work must not be retuned to this dataset unless the analysis explicitly reports the corresponding parameter penalty and out-of-sample validation.
