# Frozen production compile contract for D3/SIDMx GIZMO.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6
OUTPUT_ADDITIONAL_RUNINFO

# Intentionally omit SIDMX_D3_LIVE_AUDIT. The audit build is commissioned in
# d3-sidmx-ci; production equivalence CI proves this omission changes logging,
# not particle evolution.
