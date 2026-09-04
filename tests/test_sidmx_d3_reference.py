#!/usr/bin/env python3
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "sidm" / "sidmx_d3_impl.h").read_text()

# Fail if frozen constants or the unit conversion silently change.
for needle in (
    "6.89, 275.0",
    "6.89/3.0, 825.0",
    "1.125, 2200.0",
    "UNIT_VEL_IN_CGS / 1.0e5",
    "case 2: return ch == SIDMX_D3_HL",
    "case 3: return ch != SIDMX_D3_HL",
):
    assert needle in SRC, f"missing frozen-source invariant: {needle}"


def simpson(f, a=-1.0, b=1.0, n=20000):
    if n % 2:
        n += 1
    h = (b-a)/n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4.0 if i % 2 else 2.0) * f(a + i*h)
    return s*h/3.0


def ds_rutherford(mu, v, s0, w):
    return s0*w**4 / (2.0*(w*w + v*v*(1.0-mu)/2.0)**2)


def ds_moller(mu, v, s0, w):
    v2, w2 = v*v, w*w
    v4, w4 = v2*v2, w2*w2
    num = s0*w4*((3.0*mu*mu+1.0)*v4 + 4.0*v2*w2 + 4.0*w4)
    den = ((1.0-mu*mu)*v4 + 4.0*v2*w2 + 4.0*w4)**2
    return num/den


def moller_total(v, s0, w):
    z = (v/w)**2
    if z < 1.0e-5:
        z2, z3, z4 = z*z, z*z*z, z*z*z*z
        return s0*(0.5 - 0.5*z + (7.0/12.0)*z2 - (2.0/3.0)*z3 + (11.0/15.0)*z4)
    y = z/(z+2.0)
    return s0*(1.0/(1.0+z) - 2.0*math.atanh(y)/(z*(z+2.0)))


def rutherford_total(v, s0, w):
    z = (v/w)**2
    return s0/(1.0+z)


def moller_anti(mu, z):
    y = z/(z+2.0)
    t = y*y
    if y < 1.0e-7:
        return mu
    return 2.0*mu/(1.0-t*mu*mu) - math.atanh(y*mu)/y


def moller_cdf(mu, z):
    if z < 1.0e-5:
        return 0.5*(mu+1.0)
    am, ap = moller_anti(-1.0, z), moller_anti(1.0, z)
    return (moller_anti(mu, z)-am)/(ap-am)


def moller_inv(u, v, w):
    z = (v/w)**2
    if z < 1.0e-5:
        return 2.0*u-1.0
    lo, hi = -1.0, 1.0
    for _ in range(60):
        mid = 0.5*(lo+hi)
        if moller_cdf(mid, z) < u:
            lo = mid
        else:
            hi = mid
    return 0.5*(lo+hi)


def ruth_inv(u, v, w):
    z = (v/w)**2
    return 1.0 - 2.0*(1.0-u)/(1.0+u*z)


# Closed-form total cross sections must reproduce direct angular integration.
for v in (1.0, 50.0, 81.6815, 300.0, 1000.0):
    got = moller_total(v, 6.89, 275.0)
    ref = simpson(lambda mu: ds_moller(mu, v, 6.89, 275.0))
    assert abs(got/ref - 1.0) < 2.0e-8, ("Moller total", v, got, ref)

    got = rutherford_total(v, 1.125, 2200.0)
    ref = simpson(lambda mu: ds_rutherford(mu, v, 1.125, 2200.0))
    assert abs(got/ref - 1.0) < 2.0e-8, ("Rutherford total", v, got, ref)

assert abs(moller_total(1.0e-8, 6.89, 275.0) - 6.89/2.0) < 1e-12
assert abs(rutherford_total(1.0e-8, 1.125, 2200.0) - 1.125) < 1e-12

# Exact inverse CDF checks.
for v in (50.0, 81.6815, 300.0, 1000.0):
    for u in (0.01, 0.1, 0.5, 0.9, 0.99):
        mu = ruth_inv(u, v, 2200.0)
        z = (v/2200.0)**2
        # analytic Rutherford CDF evaluated at mu
        cdf = ((1.0/(1.0 + z*(1.0-mu)/2.0)) - (1.0/(1.0+z))) / (1.0 - 1.0/(1.0+z)) if z > 1e-14 else 0.5*(mu+1.0)
        assert abs(cdf-u) < 5e-12, ("Rutherford inverse CDF", v, u, cdf)

        mu = moller_inv(u, v, 275.0)
        cdf = moller_cdf(mu, (v/275.0)**2)
        assert abs(cdf-u) < 5e-12, ("Moller inverse CDF", v, u, cdf)

# Unequal-mass elastic COM update used by the C implementation.
def scatter(va, vb, ma, mb, mu, phi):
    dv = [va[k]-vb[k] for k in range(3)]
    speed = math.sqrt(sum(x*x for x in dv))
    if speed == 0:
        return va[:], vb[:]
    n = [x/speed for x in dv]
    a = [1.0,0.0,0.0] if abs(n[0]) < 0.8 else [0.0,1.0,0.0]
    e1 = [n[1]*a[2]-n[2]*a[1], n[2]*a[0]-n[0]*a[2], n[0]*a[1]-n[1]*a[0]]
    q = math.sqrt(sum(x*x for x in e1)); e1 = [x/q for x in e1]
    e2 = [n[1]*e1[2]-n[2]*e1[1], n[2]*e1[0]-n[0]*e1[2], n[0]*e1[1]-n[1]*e1[0]]
    st = math.sqrt(max(0.0,1.0-mu*mu))
    nh = [mu*n[k] + st*(math.cos(phi)*e1[k]+math.sin(phi)*e2[k]) for k in range(3)]
    dr = [speed*nh[k]-dv[k] for k in range(3)]
    mt = ma+mb
    return ([va[k] + mb/mt*dr[k] for k in range(3)],
            [vb[k] - ma/mt*dr[k] for k in range(3)])

rng = random.Random(171201)
max_p = max_e = 0.0
for _ in range(10000):
    va = [rng.gauss(0,100) for _ in range(3)]
    vb = [rng.gauss(0,100) for _ in range(3)]
    mu = rng.uniform(-1,1); phi = rng.uniform(0,2*math.pi)
    ma, mb = 3.0, 1.0
    p0 = [ma*va[k]+mb*vb[k] for k in range(3)]
    e0 = 0.5*ma*sum(x*x for x in va)+0.5*mb*sum(x*x for x in vb)
    a,b = scatter(va,vb,ma,mb,mu,phi)
    p1 = [ma*a[k]+mb*b[k] for k in range(3)]
    e1 = 0.5*ma*sum(x*x for x in a)+0.5*mb*sum(x*x for x in b)
    pe = math.sqrt(sum((p1[k]-p0[k])**2 for k in range(3))) / (math.sqrt(sum(x*x for x in p0))+1e-300)
    ee = abs(e1-e0)/(abs(e0)+1e-300)
    max_p, max_e = max(max_p,pe), max(max_e,ee)

assert max_p < 1e-12, max_p
assert max_e < 1e-12, max_e
print(f"SIDMx-D3 reference gates PASS; max dP/P={max_p:.3e}, max dK/K={max_e:.3e}")
