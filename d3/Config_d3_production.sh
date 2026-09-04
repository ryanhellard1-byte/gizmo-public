# Frozen production compile contract for D3/SIDMx GIZMO.
# Type 1 = H, Type 2 = L, so DM_SIDM bitmask = 2^1 + 2^2 = 6.
DM_SIDM=6
OUTPUT_ADDITIONAL_RUNINFO

# Phase187 claim instrumentation. This only populates GIZMO's diagnostic
# potential-energy field when statistics are requested; the same flag is used
# in the evidence and audit-free control builds so the Phase181 equivalence
# proof continues to isolate SIDMX_D3_LIVE_AUDIT itself.
COMPUTE_POTENTIAL_ENERGY

# Intentionally omit SIDMX_D3_LIVE_AUDIT. The audit build is commissioned in
# d3-sidmx-ci; production equivalence CI proves this omission changes logging,
# not particle evolution.
