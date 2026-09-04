# Phase187 post-processing energy-audit build.
# This is NOT the production evolution executable. It rebuilds the same frozen
# D3 physics source as the audit-free production control and adds exactly one
# diagnostic capability: self-gravitating potential-energy evaluation when
# GIZMO writes its normal energy statistics table.
DM_SIDM=6
OUTPUT_ADDITIONAL_RUNINFO
COMPUTE_POTENTIAL_ENERGY
