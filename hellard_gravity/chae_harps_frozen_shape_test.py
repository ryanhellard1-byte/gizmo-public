#!/usr/bin/env python3
"""Frozen-parameter diagnostic on Chae's public 32-object HARPS 3D sample.

This is deliberately a simple shape/amplitude diagnostic, not a replacement for
Chae's full orbital-grid likelihood.  It uses each system's observed v/vc and a
fixed Hellard spectral-dominance circular acceleration ratio at its projected
separation.  No Hellard parameters are fitted here.

Frozen benchmark:
  a_H = 1.12e-10 m/s^2
  p = 2
  beta = 1
  Galactic background acceleration = 1.7e-10 m/s^2

We compare one nuisance normalization (fit identically for Newton and Hellard)
because projected separation, eccentric orbital phase and orientation broaden
v/vc even in Newtonian dynamics.  The scientific question is whether the frozen
Hellard *separation-dependent shape* improves or worsens the 32-object residuals.
"""
from __future__ import annotations
import csv, io, math, urllib.request
import numpy as np
from scipy.optimize import brentq

URL="https://zenodo.org/records/17113129/files/gaia_purewb_3D_valueadded_harpscorr.csv?download=1"
G=6.67430e-11
MS=1.98847e30
AU=1.495978707e11
A_H=1.12e-10
A_BG=1.7e-10
P=2.0
BETA=1.0

def mu(x):
    return x/math.sqrt(1+x*x)

def mu_eff(a):
    d=a*a/(a*a+BETA*A_BG*A_BG)
    return 1-d**P*(1-mu(a/A_H))

def accel_ratio(g_n):
    def f(a): return a*mu_eff(a)-g_n
    lo=max(g_n,1e-30); hi=max(50*A_H,50*g_n,50*A_BG)
    fl=f(lo); fh=f(hi)
    for _ in range(20):
        if fl*fh<=0: break
        hi*=2; fh=f(hi)
    root=brentq(f,lo,hi,xtol=1e-18,rtol=1e-12)
    return root/g_n

def fetch_rows():
    req=urllib.request.Request(URL,headers={"User-Agent":"hellard-gravity-research/0.2"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))

def main():
    rows=fetch_rows()
    obs=[]; sig=[]; newt=[]; hell=[]; sep=[]
    for r in rows:
        s=float(r["s[kau]"])
        mt=float(r["M1[Msun]"])+float(r["M2[Msun]"])
        v=float(r["v[km/s]"]); ev=float(r["v_err[km/s]"]); vc=float(r["vc[km/s]"])
        y=v/vc
        ey=max(ev/vc,0.015)  # conservative floor for orbital/projection/model scatter proxy
        rn=s*1000*AU
        gn=G*(mt*MS)/(rn*rn)
        eta=accel_ratio(gn)
        obs.append(y); sig.append(ey); newt.append(1.0); hell.append(math.sqrt(eta)); sep.append(s)

    obs=np.array(obs); sig=np.array(sig); newt=np.array(newt); hell=np.array(hell); sep=np.array(sep)
    w=1/sig**2
    # same one-parameter nuisance amplitude for each model
    an=np.sum(w*obs*newt)/np.sum(w*newt**2)
    ah=np.sum(w*obs*hell)/np.sum(w*hell**2)
    chin=float(np.sum(((obs-an*newt)/sig)**2))
    chih=float(np.sum(((obs-ah*hell)/sig)**2))
    corr=np.corrcoef(sep,obs)[0,1]
    print(f"objects={len(obs)}")
    print(f"common-amplitude Newton={an:.6f} Hellard={ah:.6f}")
    print(f"chi2 Newton={chin:.3f} Hellard={chih:.3f} delta_chi2(H-N)={chih-chin:+.3f}")
    print(f"Pearson corr(separation, observed v/vc)={corr:+.3f}")
    print("sep[kAU] obs_v/vc sigma Newton_pred Hellard_pred")
    order=np.argsort(sep)
    for i in order:
        print(f"{sep[i]:8.3f} {obs[i]:8.4f} {sig[i]:7.4f} {an:10.4f} {ah*hell[i]:12.4f}")
    print("INTERPRETATION: frozen-shape diagnostic only; full orbital-grid likelihood remains required.")

if __name__=="__main__":
    main()
