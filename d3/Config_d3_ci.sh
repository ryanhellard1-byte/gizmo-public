# Minimal compile contract for the D3/SIDMx GIZMO integration.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6

# Keep the CI build intentionally small.  DM_SIDM automatically activates
# collisionless-particle neighbor smoothing machinery in GIZMO.
OUTPUT_ADDITIONAL_RUNINFO

# Phase184 production evidence requires full mechanical-energy telemetry.
# This makes energy_statistics() evaluate the gravitational potential when
# statistics are emitted. It is diagnostic-only and is enabled in both the
# evidence and control builds so physical-equivalence CI can police it.
COMPUTE_POTENTIAL_ENERGY

# Commissioning-only live engine audit.  This records probabilities, accepted
# channel counts, and exact pair-conservation residuals without changing the
# stochastic decisions or kicks.  Production builds can omit this flag.
SIDMX_D3_LIVE_AUDIT
