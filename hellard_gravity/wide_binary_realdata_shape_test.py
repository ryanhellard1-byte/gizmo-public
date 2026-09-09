#!/usr/bin/env python3
"""Real-data wide-binary shape test for the Hellard research branch.

Downloads the 2,464-system statistically pure Gaia DR3 MS-MS sample published by
K.-H. Chae (Zenodo 10062232).  The test intentionally avoids treating the
absolute velocity normalization as a discovery statistic.  It calibrates a
single common normalization on the inner, high-acceleration binaries and tests
the *separation dependence* of the outer-bin transverse-velocity profile.

Observed quantity:
    u_perp = v_perp / sqrt(G M_tot / r_proj)

A Monte-Carlo Newtonian projection/eccentricity library is built using each
system's catalog eccentricity proxy.  The Hellard comparator uses the same
realization and multiplies the local orbital velocity by sqrt(a_Hellard/g_N),
where a_Hellard is obtained from the frozen v0.1 spectral-dominance reduced
closure.  This is a quasi-Kepler diagnostic, not yet the final causal-memory
many-body likelihood.

Scientific guardrail: this script may reject the current candidate.  It must not
retune a_H, p or beta to the wide-binary data.
"""
from __future__ import annotations

import csv
import io
import math
import urllib.request
import numpy as np
from scipy.optimize import brentq

URL = "https://zenodo.org/records/10062232/files/gaia_dr3_MSMS_purewb_revised.csv?download=1"
G = 6.67430e-11
M_SUN = 1.98847e30
AU = 1.495978707e11
A_H = 1.12e-10
A_BG = 1.7e-10
P_EXP = 2.0
BETA = 1.0
KM_PER_S_PER_MASYR_PC = 4.74047e-3
RNG = np.random.default_rng(20260909)


def mu(x: float) -> float:
    return x / math.sqrt(1.0 + x*x)


def dominance(a: float) -> float:
    return a*a / (a*a + BETA*A_BG*A_BG)


def mu_eff(a: float) -> float:
    d = dominance(a)
    return 1.0 - d**P_EXP * (1.0 - mu(a/A_H))


def accel_ratio(g_n: float) -> float:
    """Return a/g_N for the frozen v0.1 reduced spectral-dominance closure."""
    def f(a: float) -> float:
        return a*mu_eff(a) - g_n
    lo = max(g_n, 1e-30)
    hi = max(50*A_H, 50*g_n, 50*A_BG)
    flo, fhi = f(lo), f(hi)
    for _ in range(20):
        if flo*fhi <= 0:
            break
        hi *= 2
        fhi = f(hi)
    root = brentq(f, lo, hi, xtol=1e-18, rtol=1e-12)
    return root/g_n


def download_rows():
    req = urllib.request.Request(URL, headers={"User-Agent":"hellard-gravity-research/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def f(row, key):
    try:
        return float(row[key])
    except (ValueError, TypeError, KeyError):
        return math.nan


def select(rows):
    out=[]
    for r in rows:
        rp=f(r,"s[kau]"); d1=f(r,"d1[pc]"); d2=f(r,"d2[pc]")
        e1d=f(r,"d1_err[pc]"); e2d=f(r,"d2_err[pc]")
        m1=f(r,"M1[Msun]"); m2=f(r,"M2[Msun]")
        chance=f(r,"R_chance"); ruwe=max(f(r,"ruwe1"),f(r,"ruwe2"))
        mag1=f(r,"MagG1"); mag2=f(r,"MagG2")
        dec1=f(r,"DEC1[deg]")
        c1=f(r,"bp_rp1"); c2=f(r,"bp_rp2")
        if not all(math.isfinite(x) for x in [rp,d1,d2,e1d,e2d,m1,m2,chance,ruwe,mag1,mag2,dec1,c1,c2]):
            continue
        mt=m1+m2
        d=(d1/e1d**2+d2/e2d**2)/(1/e1d**2+1/e2d**2)
        derr=max(e1d/d1,e2d/d2)
        pmvals=[]
        bad=False
        for comp in ("1","2"):
            for ax in ("ra","dec"):
                v=f(r,f"mu{comp}{ax}[mas/yr]")
                er=f(r,f"mu{comp}{ax}_err[mas/yr]")
                if not math.isfinite(v) or not math.isfinite(er) or abs(v)<1e-12:
                    bad=True; break
                pmvals.append(abs(er/v))
            if bad: break
        if bad: continue
        pmerr=max(pmvals)
        # Same spirit as the published pure-sample velocity-profile defaults.
        a_col=4-3.6*17/11.5+0.1; b_col=3.6/11.5
        if not (0.2 <= rp <= 30 and d < 200 and 0.5 < mt < 2.0 and chance < 0.01 and
                ruwe < 1.2 and 4 < mag1 < 14 and 4 < mag2 < 14 and dec1 > -28 and
                c1 > a_col+b_col*mag1 and c2 > a_col+b_col*mag2 and
                pmerr < 0.003 and derr < 0.003):
            continue
        dpm=math.hypot(f(r,"mu1ra[mas/yr]")-f(r,"mu2ra[mas/yr]"),
                       f(r,"mu1dec[mas/yr]")-f(r,"mu2dec[mas/yr]"))
        vp=KM_PER_S_PER_MASYR_PC*d*dpm
        vc=math.sqrt(G*(mt*M_SUN)/(rp*1000*AU))/1000
        u=vp/vc
        ecc=min(max(f(r,"e"),0.001),0.999)
        out.append((rp,mt,u,ecc))
    return np.array(out,float)


def solve_kepler(M, e):
    E=M.copy()
    for _ in range(8):
        E -= (E-e*np.sin(E)-M)/(1-e*np.cos(E))
    return E


def model_u(rp_kau, mt, ecc, hellard=False, draws=256):
    """Projected normalized velocity MC conditioned approximately on r_proj."""
    n=len(rp_kau)
    M=RNG.uniform(0,2*np.pi,(draws,n))
    omega=RNG.uniform(0,2*np.pi,(draws,n))
    cosi=RNG.uniform(0,1,(draws,n))
    sini=np.sqrt(1-cosi*cosi)
    e=np.broadcast_to(ecc,(draws,n))
    E=solve_kepler(M,e)
    sf=np.sqrt(1+e)*np.sin(E/2)
    cf=np.sqrt(1-e)*np.cos(E/2)
    nu=2*np.arctan2(sf,cf)
    uarg=nu+omega
    proj_r=np.sqrt(np.cos(uarg)**2 + cosi**2*np.sin(uarg)**2)
    proj_r=np.maximum(proj_r,1e-3)
    # r is inferred from observed projected separation and random orientation.
    r_true=(rp_kau[None,:]*1000*AU)/proj_r
    aorb=r_true*(1+e*np.cos(nu))/(1-e*e)
    scale=np.sqrt(G*(mt[None,:]*M_SUN)/aorb)/(np.sqrt(1-e*e))
    vr=scale*e*np.sin(nu)
    vt=scale*(1+e*np.cos(nu))
    vx=vr*np.cos(uarg)-vt*np.sin(uarg)
    vy=(vr*np.sin(uarg)+vt*np.cos(uarg))*cosi
    vp=np.sqrt(vx*vx+vy*vy)
    if hellard:
        # quasi-Kepler local force rescaling, frozen parameters only
        # cache via rounded log g_N to avoid thousands of root solves
        gn=G*(mt[None,:]*M_SUN)/(r_true*r_true)
        lg=np.round(np.log10(gn),3)
        uniq=np.unique(lg)
        table={z:accel_ratio(10**float(z)) for z in uniq}
        eta=np.vectorize(table.get)(lg)
        vp*=np.sqrt(eta)
    vnorm=np.sqrt(G*(mt[None,:]*M_SUN)/(rp_kau[None,:]*1000*AU))
    return vp/vnorm


def bootstrap_median(x, reps=1000):
    if len(x)<3: return np.nan,np.nan
    med=float(np.median(x))
    idx=RNG.integers(0,len(x),(reps,len(x)))
    meds=np.median(x[idx],axis=1)
    return med,float(np.std(meds,ddof=1))


def main():
    rows=download_rows()
    data=select(rows)
    print(f"catalog rows={len(rows)} selected={len(data)}")
    if len(data)<100:
        raise SystemExit("FAIL: too few systems after quality cuts")
    rp,mt,uobs,ecc=data.T
    edges=np.geomspace(0.2,30,7)
    obs=[]; err=[]; rmid=[]; counts=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(rp>=lo)&(rp<hi)
        med,se=bootstrap_median(uobs[mask])
        obs.append(med); err.append(se); rmid.append(math.sqrt(lo*hi)); counts.append(mask.sum())
    obs=np.array(obs); err=np.array(err); rmid=np.array(rmid)

    un=model_u(rp,mt,ecc,hellard=False)
    uh=model_u(rp,mt,ecc,hellard=True)
    mn=[]; mh=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(rp>=lo)&(rp<hi)
        mn.append(float(np.median(un[:,mask])))
        mh.append(float(np.median(uh[:,mask])))
    mn=np.array(mn); mh=np.array(mh)

    # Inner two bins set one common nuisance normalization for each model.
    inner=np.arange(2)
    wn=1/np.maximum(err[inner],1e-4)**2
    sn=np.sum(wn*obs[inner]*mn[inner])/np.sum(wn*mn[inner]**2)
    sh=np.sum(wn*obs[inner]*mh[inner])/np.sum(wn*mh[inner]**2)
    predn=sn*mn; predh=sh*mh
    outer=np.arange(2,6)
    chin=float(np.sum(((obs[outer]-predn[outer])/np.maximum(err[outer],1e-4))**2))
    chih=float(np.sum(((obs[outer]-predh[outer])/np.maximum(err[outer],1e-4))**2))

    print("bin  rmid[kAU] N   observed±bootSE   Newton   Hellard")
    for i in range(6):
        print(f"{i+1:>2} {rmid[i]:9.3f} {counts[i]:4d} {obs[i]:.4f}±{err[i]:.4f} {predn[i]:.4f} {predh[i]:.4f}")
    print(f"inner calibration scale: Newton={sn:.4f} Hellard={sh:.4f}")
    print(f"outer-shape chi2 (4 bins): Newton={chin:.3f} Hellard={chih:.3f} delta_chi2(H-N)={chih-chin:+.3f}")
    print("INTERPRETATION: this is a real-catalog quasi-Kepler shape diagnostic, not the final full nuisance-marginalized likelihood.")


if __name__ == "__main__":
    main()
