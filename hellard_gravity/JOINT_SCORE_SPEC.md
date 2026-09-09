# Frozen joint observational score

This document defines the scoring rule before reading the final HARPS result.

## Frozen Hellard parameters

- a_H = 1.12e-10 m/s^2
- p = 2
- beta = 1
- local Galactic background acceleration = 1.7e-10 m/s^2

No Hellard parameter may be re-fit to a wide-binary or Solar-System dataset in
this score.

## Components

1. **SPARC RAR**
   - all 2693 public SPARC RAR points
   - use the existing Gaussian all-points chi-square approximation
   - Hellard circular branch has one already-frozen scale a_H
   - Newtonian null uses no fitted acceleration scale
   - simple MOND comparator uses its single best-fit acceleration scale only as
     a benchmark, not as a component of Hellard

2. **Gaia DR3 pure wide-binary shape**
   - public 2463-row Chae catalog, current quality cuts yield 1494 systems
   - one nuisance amplitude per hypothesis is calibrated on the same two inner
     bins
   - score only the four outer-bin shape residuals
   - this is explicitly a shape diagnostic, not a full orbital likelihood

3. **HARPS 3D public pilot**
   - 32 public full-3D systems
   - one common nuisance amplitude per hypothesis
   - frozen Hellard separation dependence
   - treat this as a pilot diagnostic until the full orbit-grid likelihood is
     implemented

4. **Solar-System hard gate**
   - the action-level high-acceleration decoupling must stay below the adopted
     Cassini-scale conservative proxy
   - this is a hard falsification gate, not an additive reward

## Reporting

Report SPARC, Gaia-shape and HARPS diagnostics separately and then the raw sum
of comparable chi-square diagnostics. Do not call the raw sum a formal global
Bayes factor because the approximations, nuisance structures, and data
covariances differ.

The correct language is:
- "joint frozen diagnostic score"
not
- "proof", "discovery", or "global posterior odds".

## Kill rule

If the frozen Hellard prediction is materially worse than Newton on both public
wide-binary diagnostics, the spectral-dominance benchmark is rejected even if
SPARC strongly prefers its circular low-acceleration branch over a baryons-only
Newtonian null.

If Hellard is competitive or better on the public wide-binary diagnostics and
passes the Solar-System hard gate, proceed to the full orbital-grid likelihood
and independent replication.
