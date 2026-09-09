# Hellard modified-inertia observational data gate

This directory treats the model as a falsifiable research hypothesis, not a discovered law.

## SPARC radial acceleration relation

Official SPARC source:

- https://astroweb.cwru.edu/SPARC/
- all-points RAR table: https://astroweb.cwru.edu/SPARC/RAR.mrt

The table contains 2,693 published acceleration points with log10(gbar), its error,
log10(gobs), and its error. `sparc_fit.py` downloads and scores the current isolated
circular-orbit branch against these real measurements.

A full publication-quality likelihood still needs galaxy-level nuisance parameters,
correlated errors, mass-to-light uncertainty, distance/inclination treatment, and sample
selection. The current script is a first direct-data falsification gate.

## Gaia wide binaries

Primary 2026 null-result reference used for the present conservative gate:

Cookson et al., *A Quality Framework for Testing Gravity with Wide Binaries: No Evidence for MOND*,
MNRAS 547 (2026). The high-purity Gaia DR3 sample spans projected separations 1-30 kAU and
reports no ~20% MOND-like velocity enhancement, with Newtonian dynamics strongly preferred in
the cleanest subsets.

Because the raw high-purity catalogue/selection likelihood is not yet vendored here, the current
`combined_observational_gate.py` uses a conservative literature-level rule:

- planetary external-field proxy < 0.5%
- representative 10-100 kyr wide-binary external-field proxy < 2%
- `theta(1)=1` exactly, so the same universal kernel does not retune the isolated galaxy branch

This proxy is not a substitute for a raw Gaia likelihood. It exists to prevent a kernel change
that obviously resurrects the classical ~20% MOND wide-binary boost.

## Current benchmark

- a_H = 1.19e-10 m/s^2
- theta(y) = 7 / (1 + 6 y)
- y = omega_ext / omega_int

No dataset gets its own parameters. If future raw-data likelihoods cannot be fit by one universal
parameter set, the benchmark fails.
