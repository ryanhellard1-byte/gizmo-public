# Minimal compile contract for the D3/SIDMx GIZMO integration.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6

# Keep the CI build intentionally small.  DM_SIDM automatically activates
# collisionless-particle neighbor smoothing machinery in GIZMO.
OUTPUT_ADDITIONAL_RUNINFO

# Commissioning/live evidence audit.  This records probabilities, accepted
# channel counts, and exact pair-conservation residuals without changing the
# stochastic decisions or kicks.
SIDMX_D3_LIVE_AUDIT

# Phase187 claim instrumentation.  GIZMO's normal statistics routine then
# evaluates the self-gravitating potential before writing energy.txt.  The
# production claim evaluator re-opens frozen snapshots in restart-from-snapshot
# mode and reads that exact engine energy; no approximate Python gravity is used.
COMPUTE_POTENTIAL_ENERGY
