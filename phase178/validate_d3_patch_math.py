#!/usr/bin/env python3
"""Independent numerical audit of the GIZMO D3 H/L patch math.

This validates the frozen Phase-139 differential laws, closed-form total rates,
exact angular samplers, Phase-142 HL mass-basis normalization, and exact COM
elastic kicks. It does not substitute for the required live GIZMO homogeneous-
box commissioning run.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss

OUT = Path(__file__).with_name("validate_d3_patch_math_results.json")
RNG = np.random.default_rng(20260903)

SIGMA0 = {"HH": 6.89, "LL": 6.89/3.0, "HL": 1.125}  # declared basis: H,H? LL=L, HL=H
W = {"HH": 275.0, "LL": 825.0, "HL": 2200.0}
MASS = {"H": 3.0, "L": 1.0}

mu_gl, w_gl = leggauss(768)

def dsigma_dmu(mu, v, ch):
    mu=np.asarray(mu,dtype=float); s0=SIGMA0[ch]; w=W[ch]
    if ch=="HL":
        return s0*w**4/(2.0*(w*w+v*v*(1.0-mu)/2.0)**2)
    v2=v*v; w2=w*w; v4=v2*v2; w4=w2*w2
    return s0*w4*((3*mu*mu+1)*v4+4*v2*w2+4*w4)/(((1-mu*mu)*v4+4*v2*w2+4*w4)**2)

def total_quad(v,ch):
    return float(np.dot(w_gl,dsigma_dmu(mu_gl,v,ch)))

def moller_factor(x):
    if x<1e-3:
        return 0.5-0.5*x+(7/12)*x*x-(2/3)*x**3+(11/15)*x**4
    return (x*x+2*x-(x+1)*math.log1p(x))/(x*(x+1)*(x+2))

def total_closed(v,ch):
    x=(v/W[ch])**2
    if ch=="HL": return SIGMA0[ch]/(1+x)
    return SIGMA0[ch]*moller_factor(x)

def rutherford_mu(x,u):
    return 1-2*(1-u)/(1+u*x)

def moller_sample(x,n,rng):
    out=np.empty(n); k=0; tries=0
    while k<n:
        m=max(1024,2*(n-k))
        u=rng.random(m)
        prop=(u*(x+2)-1)/(1+u*x)
        prop*=np.where(rng.random(m)<0.5,-1.0,1.0)
        a2=(x+2)**2; x2=x*x
        acc=(3*prop*prop*x2+a2)/(2*(prop*prop*x2+a2))
        keep=prop[rng.random(m)<acc]
        q=min(len(keep),n-k); out[k:k+q]=keep[:q]; k+=q; tries+=m
    return out, n/tries

def numerical_cdf(v,ch,mu):
    # Dense CDF from frozen law, intentionally independent of the closed-form sampler.
    grid=np.linspace(-1,1,32769)
    y=dsigma_dmu(grid,v,ch)
    area=np.concatenate(([0.0],np.cumsum(0.5*(y[:-1]+y[1:])*np.diff(grid))))
    area/=area[-1]
    return np.interp(mu,grid,area)

def ks_uniform_from_reference(samples,v,ch):
    z=np.sort(numerical_cdf(v,ch,samples))
    n=len(z); lo=np.arange(n)/n; hi=np.arange(1,n+1)/n
    return float(max(np.max(np.abs(z-lo)),np.max(np.abs(hi-z))))

def basis_macro_mass(ch,species,M):
    if ch in ("HH","LL"): return M
    return M if species=="H" else 3*M

def scatter(va,vb,ma,mb,mu,phi):
    va=np.asarray(va,float); vb=np.asarray(vb,float); u=va-vb
    s=np.linalg.norm(u)
    if s==0: return va.copy(),vb.copy()
    n=u/s; a=np.array([1.,0,0]) if abs(n[0])<.8 else np.array([0.,1,0])
    e1=np.cross(n,a); e1/=np.linalg.norm(e1); e2=np.cross(n,e1)
    nh=mu*n+math.sqrt(max(0.,1-mu*mu))*(math.cos(phi)*e1+math.sin(phi)*e2)
    uo=s*nh; mt=ma+mb; vcm=(ma*va+mb*vb)/mt
    return vcm+(mb/mt)*uo, vcm-(ma/mt)*uo

results={"status":"PASS","checks":{}}

# Closed total rate vs direct quadrature.
rate=[]; worst=0
for ch in ("HH","LL","HL"):
    for v in (1e-3,1,30,100,275,825,2200,5000,20000):
        q=total_quad(v,ch); c=total_closed(v,ch); e=abs(c/q-1); worst=max(worst,e)
        rate.append({"channel":ch,"v_km_s":v,"quadrature":q,"closed":c,"relerr":e})
results["checks"]["closed_total_vs_frozen_differential"]={"worst_relerr":worst,"pass":worst<2e-9,"rows":rate}

# Low-v convention.
low={ch:total_closed(1e-6,ch) for ch in ("HH","LL","HL")}
low_expected={"HH":SIGMA0["HH"]/2,"LL":SIGMA0["LL"]/2,"HL":SIGMA0["HL"]}
lowerr=max(abs(low[c]/low_expected[c]-1) for c in low)
results["checks"]["low_v_normalization"]={"computed":low,"expected":low_expected,"worst_relerr":lowerr,"pass":lowerr<1e-12}

# Angular samplers against independent dense numerical CDF of the full differential law.
angular=[]
for ch,v in (("HH",55),("HH",275),("HH",1000),("LL",55),("LL",825),("HL",55),("HL",2200),("HL",5000)):
    x=(v/W[ch])**2; n=50000
    if ch=="HL": samp=rutherford_mu(x,RNG.random(n)); eff=1.0
    else: samp,eff=moller_sample(x,n,RNG)
    D=ks_uniform_from_reference(samp,v,ch)
    angular.append({"channel":ch,"v_km_s":v,"n":n,"KS_D":D,"proposal_efficiency_lower_bound_measure":eff,"mean_mu":float(np.mean(samp))})
results["checks"]["angular_sampler"]={"rows":angular,"max_KS_D":max(r["KS_D"] for r in angular),"pass":max(r["KS_D"] for r in angular)<0.012}

# Phase-142 mass-basis normalization and stock-average-mass contrast.
M_H,M_L=3.0,1.0
hl_left=SIGMA0["HL"]*basis_macro_mass("HL","H",M_H)
hl_right=SIGMA0["HL"]*basis_macro_mass("HL","L",M_L)
stock_using_H_basis=SIGMA0["HL"]*0.5*(M_H+M_L)
correct=0.5*(hl_left+hl_right)
results["checks"]["HL_mass_basis_normalization"]={
    "conditional_H":hl_left,"conditional_L_converted_to_H_basis":hl_right,
    "symmetric_correct":correct,"stock_average_mass_if_sigma_stored_on_mH":stock_using_H_basis,
    "stock_over_correct":stock_using_H_basis/correct,
    "pass":abs(hl_left/hl_right-1)<1e-15 and abs(stock_using_H_basis/correct-2/3)<1e-15,
}

# Exact unequal-mass COM scattering conservation.
maxp=maxe=0.0
for ch,sa,sb in (("HH","H","H"),("LL","L","L"),("HL","H","L"),("HL","L","H")):
    ma,mb=MASS[sa],MASS[sb]
    for _ in range(20000):
        va=RNG.normal(0,200,3); vb=RNG.normal(0,200,3); v=np.linalg.norm(va-vb); x=(v/W[ch])**2
        if ch=="HL": mu=float(rutherford_mu(x,RNG.random()))
        else: mu=float(moller_sample(x,1,RNG)[0][0])
        phi=float(RNG.uniform(0,2*math.pi)); va2,vb2=scatter(va,vb,ma,mb,mu,phi)
        p0=ma*va+mb*vb; p1=ma*va2+mb*vb2
        e0=.5*ma*np.dot(va,va)+.5*mb*np.dot(vb,vb); e1=.5*ma*np.dot(va2,va2)+.5*mb*np.dot(vb2,vb2)
        pr=np.linalg.norm(p1-p0)/(np.linalg.norm(p0)+ma*np.linalg.norm(va)+mb*np.linalg.norm(vb)+1e-300)
        er=abs(e1-e0)/(abs(e0)+1e-300); maxp=max(maxp,pr); maxe=max(maxe,er)
results["checks"]["COM_conservation"]={"max_relative_momentum_residual":maxp,"max_relative_energy_residual":maxe,"pass":maxp<2e-15 and maxe<3e-15}

if not all(v.get("pass",True) for v in results["checks"].values()): results["status"]="FAIL"
OUT.write_text(json.dumps(results,indent=2,default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("STATUS:",results["status"])
print("worst total-rate relerr:",results["checks"]["closed_total_vs_frozen_differential"]["worst_relerr"])
print("max angular KS D:",results["checks"]["angular_sampler"]["max_KS_D"])
print("HL stock/correct normalization:",results["checks"]["HL_mass_basis_normalization"]["stock_over_correct"])
print("max momentum residual:",maxp)
print("max energy residual:",maxe)
print("results:",OUT)
raise SystemExit(0 if results["status"]=="PASS" else 1)
