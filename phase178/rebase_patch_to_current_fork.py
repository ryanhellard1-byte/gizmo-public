#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
s=src.read_text()
repls=[
("""@@ -3,6 +3,14 @@ void apply_excision();\n #endif\n #ifdef DM_SIDM\n""",
 """@@ -3,7 +3,15 @@ void apply_excision();\n #endif\n \n #ifdef DM_SIDM\n"""),
("""@@ -12,6 +13,16 @@\n #include \"../kernel.h\"\n #define GSLWORKSIZE 100000\n""",
 """@@ -12,7 +13,17 @@\n #include \"../kernel.h\"\n \n #define GSLWORKSIZE 100000\n"""),
]
for old,new in repls:
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'rebase anchor count {n}, expected 1: {old[:60]!r}')
    s=s.replace(old,new,1)
dst.write_text(s)
print('rebased_sha256',hashlib.sha256(s.encode()).hexdigest())
