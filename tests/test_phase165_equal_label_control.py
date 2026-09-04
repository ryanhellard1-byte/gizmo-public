#!/usr/bin/env python3
"""Reference gate for the Phase165 identical-label hostile control.

The control must remove unequal-mass kinematics without changing the frozen HL
Rutherford law or weakening the 3:1 mass guard on physical D3 modes.
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPL = (ROOT / "sidm" / "sidmx_d3_impl.h").read_text()
CORE = (ROOT / "sidm" / "sidm_core.c").read_text()
HDR = (ROOT / "sidm" / "sidmx_d3.h").read_text()
IC = (ROOT / "d3" / "production" / "generate_phase165_ic.py").read_text()
CLOUD = (ROOT / "d3" / "generate_d3_collision_cloud.py").read_text()

# Source-contract checks. Physical modes remain 3:1; only mode 10 admits 1:1.
for needle in (
    "mode > 10",
    "case 10: return ch == SIDMX_D3_HL",
    "if(mode == 10)",
    "required 1",
    "required 3",
    "sidmx_d3_rutherford_total(v_km_s, 1.125, 2200.0)",
):
    assert needle in IMPL or needle in CORE, f"missing equal-label source invariant: {needle}"
assert "-10 identical-label control" in HDR
assert 'choices=[1.0, 3.0]' in IC
assert 'choices=[1.0, 3.0]' in CLOUD
assert "physical modes retain mH/mL=3" in (ROOT / "d3" / "production" / "phase165_gizmo_preflight.py").read_text()


def ruth_inv(u: float, v: float, w: float = 2200.0) -> float:
    z = (v / w) ** 2
    return 1.0 - 2.0 * (1.0 - u) / (1.0 + u * z)


def scatter(va, vb, ma, mb, mu, phi):
    dv = [va[k] - vb[k] for k in range(3)]
    speed = math.sqrt(sum(x*x for x in dv))
    if speed == 0.0:
        return va[:], vb[:]
    n = [x/speed for x in dv]
    a = [1.0, 0.0, 0.0] if abs(n[0]) < 0.8 else [0.0, 1.0, 0.0]
    e1 = [n[1]*a[2]-n[2]*a[1], n[2]*a[0]-n[0]*a[2], n[0]*a[1]-n[1]*a[0]]
    q = math.sqrt(sum(x*x for x in e1))
    e1 = [x/q for x in e1]
    e2 = [n[1]*e1[2]-n[2]*e1[1], n[2]*e1[0]-n[0]*e1[2], n[0]*e1[1]-n[1]*e1[0]]
    st = math.sqrt(max(0.0, 1.0-mu*mu))
    nh = [mu*n[k] + st*(math.cos(phi)*e1[k] + math.sin(phi)*e2[k]) for k in range(3)]
    dr = [speed*nh[k]-dv[k] for k in range(3)]
    mt = ma + mb
    return ([va[k] + mb/mt*dr[k] for k in range(3)],
            [vb[k] - ma/mt*dr[k] for k in range(3)])


# Equal-mass HL control uses the same Rutherford angle law and must conserve
# pair momentum and kinetic energy to the same numerical standard.
rng = random.Random(165010)
max_p = 0.0
max_e = 0.0
for _ in range(10000):
    va = [rng.gauss(0.0, 120.0) for _ in range(3)]
    vb = [rng.gauss(0.0, 120.0) for _ in range(3)]
    v = math.sqrt(sum((va[k]-vb[k])**2 for k in range(3)))
    mu = ruth_inv(rng.random(), v)
    phi = 2.0*math.pi*rng.random()
    ma = mb = 1.0
    p0 = [va[k] + vb[k] for k in range(3)]
    e0 = 0.5*sum(x*x for x in va) + 0.5*sum(x*x for x in vb)
    a, b = scatter(va, vb, ma, mb, mu, phi)
    p1 = [a[k] + b[k] for k in range(3)]
    e1 = 0.5*sum(x*x for x in a) + 0.5*sum(x*x for x in b)
    pscale = math.sqrt(sum(x*x for x in p0)) + math.sqrt(sum(x*x for x in va)) + math.sqrt(sum(x*x for x in vb)) + 1e-300
    max_p = max(max_p, math.sqrt(sum((p1[k]-p0[k])**2 for k in range(3))) / pscale)
    max_e = max(max_e, abs(e1-e0)/(abs(e0)+1e-300))

assert max_p < 2e-15, max_p
assert max_e < 3e-15, max_e
print(f"Phase165 equal-label reference gate PASS; max dP/P={max_p:.3e}, max dK/K={max_e:.3e}")
