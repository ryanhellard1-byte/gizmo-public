# Minimal compile contract for the D3/SIDMx GIZMO integration.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6

# Keep the CI build intentionally small.  DM_SIDM automatically activates
# collisionless-particle neighbor smoothing machinery in GIZMO.
OUTPUT_ADDITIONAL_RUNINFO

# Phase187 runtime-invariant diagnostic. Keep this identical to production so
# the audit/control equivalence contract still differs only by live-audit output.
COMPUTE_POTENTIAL_ENERGY

# Commissioning-only live engine audit.  This records probabilities, accepted
# channel counts, and exact pair-conservation residuals without changing the
# stochastic decisions or kicks.  Production builds can omit this flag.
SIDMX_D3_LIVE_AUDIT