#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
s=src.read_text()
repls=[
("@@ -3,6 +3,14 @@ void apply_excision();\n #endif\n #ifdef DM_SIDM\n",
 "@@ -3,7 +3,15 @@ void apply_excision();\n #endif\n \n #ifdef DM_SIDM\n"),
("@@ -12,6 +13,16 @@\n #include \"../kernel.h\"\n #define GSLWORKSIZE 100000\n",
 "@@ -12,7 +13,17 @@\n #include \"../kernel.h\"\n \n #define GSLWORKSIZE 100000\n"),
("@@ -49,6 +60,276 @@ void calculate_interact_kick(double dV[3], double kick[3], double m)\n }\n #endif\n \n+#ifdef DM_SIDM_D3_HL\n",
 "@@ -49,7 +60,277 @@ void calculate_interact_kick(double dV[3], double kick[3], double m)\n }\n #endif\n \n \n+#ifdef DM_SIDM_D3_HL\n"),
("@@ -98,5 +379,12 @@ double geofactor_angle_integ(double u, void * params)\n     return wk;\n }\n /*! This function simply initializes some variables to prevent memory errors */\n-void init_self_interactions() {int i; for(i = 0; i < NumPart; i++) {P[i].dtime_sidm = 0; P[i].NInteractions = 0;}}\n",
 "@@ -98,8 +379,15 @@ double geofactor_angle_integ(double u, void * params)\n     return wk;\n }\n \n /*! This function simply initializes some variables to prevent memory errors */\n-void init_self_interactions() {int i; for(i = 0; i < NumPart; i++) {P[i].dtime_sidm = 0; P[i].NInteractions = 0;}}\n"),
]
for old,new in repls:
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'rebase anchor count {n}, expected 1: {old[:80]!r}')
    s=s.replace(old,new,1)
old = "+}\n #endif\ndiff --git a/sidm/sidm_core_flux_computation.h"
new = "+}\n \n #endif\ndiff --git a/sidm/sidm_core_flux_computation.h"
if s.count(old) != 1:
    raise SystemExit('final core blank-line anchor mismatch')
s=s.replace(old,new,1)
dst.write_text(s)
print('rebased_sha256',hashlib.sha256(s.encode()).hexdigest())
