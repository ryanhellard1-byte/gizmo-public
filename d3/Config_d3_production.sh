# Frozen production compile contract for D3/SIDMx GIZMO.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6
OUTPUT_ADDITIONAL_RUNINFO

# Phase184 production evidence requires full mechanical-energy telemetry.
# Keep this diagnostic token identical between evidence and control builds;
# only SIDMX_D3_LIVE_AUDIT may differ between the two configurations.
COMPUTE_POTENTIAL_ENERGY

# Intentionally omit SIDMX_D3_LIVE_AUDIT. The audit build is commissioned in
# d3-sidmx-ci; production equivalence CI proves this omission changes logging,
# not particle evolution.
