# Minimal compile contract for the D3/SIDMx GIZMO integration.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6

# Keep the CI build intentionally small. DM_SIDM automatically activates
# collisionless-particle neighbor smoothing machinery in GIZMO.
OUTPUT_ADDITIONAL_RUNINFO

# Phase184 production evidence requires full mechanical-energy telemetry.
COMPUTE_POTENTIAL_ENERGY

# TimeBetStatistics is exposed by upstream GIZMO only in DEVELOPER_MODE.
# Phase184 enables it in BOTH evidence/control builds and the renderer writes
# every affected developer parameter at the exact upstream hardcoded default,
# except TimeBetStatistics itself. Equivalence CI must remain byte-identical.
DEVELOPER_MODE

# Commissioning-only live engine audit. This records probabilities, accepted
# channel counts, and exact pair-conservation residuals without changing the
# stochastic decisions or kicks. Control builds omit only this token.
SIDMX_D3_LIVE_AUDIT
