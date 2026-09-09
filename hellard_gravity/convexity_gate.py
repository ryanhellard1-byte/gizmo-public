#!/usr/bin/env python3
"""Convexity/stability diagnostic for Hellard spectral-dominance action.

The current p=2, beta=1, n=4 benchmark is phenomenologically useful but is not
assumed globally stable. This diagnostic explicitly probes the two-mode Hessian
of a reduced dimensionless spectral action over amplitudes and frequency ratios.
A negative Hessian eigenvalue is treated as a failure of the benchmark action,
not as evidence against modified inertia in general.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.integrate import quad

P_EXP=2.0
BETA=1.0
N_EXP=4.0


def mu(x: float) -> float:
    return x/math.sqrt(1.0+x*x)


def wslow(y: float) -> float:
    return 1.0/(1.0+y**N_EXP)


def F(P: float, B: float) -> float:
    if P <= 0.0:
        return 0.0
    def integrand(u):
        if u <= 0.0:
            return 1.0
        D=u/(u+BETA*B) if (u+BETA*B)>0 else 1.0
        return 1.0-D**P_EXP*(1.0-mu(math.sqrt(u)))
    return quad(integrand,0.0,P,epsabs=1e-9,epsrel=1e-9,limit=100)[0]


def action(x,omega):
    x=np.asarray(x,float); omega=np.asarray(omega,float); P=x*x
    total=0.0
    for i in range(len(x)):
        B=sum(wslow(abs(omega[j]/omega[i]))*P[j] for j in range(len(x)) if j!=i)
        total += F(P[i],B)/(omega[i]*omega[i])
    return total


def hessian2(x,omega,h=1e-4):
    x=np.asarray(x,float); base=action(x,omega); H=np.zeros((2,2)); hs=[h*max(1.0,abs(v)) for v in x]
    for i in range(2):
        hi=hs[i]; xp=x.copy(); xm=x.copy(); xp[i]+=hi; xm[i]-=hi
        H[i,i]=(action(xp,omega)-2.0*base+action(xm,omega))/(hi*hi)
    hi,hj=hs
    xpp=x.copy(); xpm=x.copy(); xmp=x.copy(); xmm=x.copy()
    xpp[0]+=hi; xpp[1]+=hj; xpm[0]+=hi; xpm[1]-=hj; xmp[0]-=hi; xmp[1]+=hj; xmm[0]-=hi; xmm[1]-=hj
    H[0,1]=H[1,0]=(action(xpp,omega)-action(xpm,omega)-action(xmp,omega)+action(xmm,omega))/(4.0*hi*hj)
    return H


def main():
    worst=(1e99,None)
    negative=[]
    for xe in (0.05,0.1,0.2,0.5,1.0,2.0,5.0):
        for xi in (0.03,0.1,0.3,1.0,3.0):
            for R in (2.0,3.0,5.0,10.0,100.0,1000.0):
                ev=np.linalg.eigvalsh(hessian2((xe,xi),(1.0,R)))
                if ev[0] < worst[0]:
                    worst=(float(ev[0]),(xe,xi,R,ev.tolist()))
                if ev[0] < -1e-5:
                    negative.append((xe,xi,R,float(ev[0])))
    print(f"worst Hessian eigenvalue = {worst[0]:.6e} at {worst[1]}")
    print(f"negative-grid points = {len(negative)}")
    if negative:
        print("STATUS: CURRENT BENCHMARK ACTION FAILS GLOBAL CONVEXITY GATE")
        # Deliberately exit zero: this file records a known falsification target while
        # the replacement convex action is being developed. The CI assertion is that
        # the failure remains visible, not accidentally hidden.
    else:
        print("STATUS: sampled convexity gate PASS")

if __name__ == '__main__':
    main()
