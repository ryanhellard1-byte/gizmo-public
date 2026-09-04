# Minimal compile contract for the D3/SIDMx GIZMO integration.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6

# Keep the CI build intentionally small.  DM_SIDM automatically activates
# collisionless-particle neighbor smoothing machinery in GIZMO.
OUTPUT_ADDITIONAL_RUNINFO
