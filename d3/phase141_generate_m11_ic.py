#!/usr/bin/env python3
"""
Deterministic M11 two-species equilibrium IC generator for the D3/SIDMx program.

Physics frozen from the project:
  M200 = 1e11 Msun
  rho_s = 6.89e6 Msun/kpc^3
  r_s = 9.10 kpc
  m_H/m_L = 3, equal particle numbers
  isotropic equilibrium velocities from numerical Eddington inversion
  NFW inside r200 with C1 exponential continuation outside r200

Default taper rd/r200 = 0.05 is the Phase-139 primary. 0.03 and 0.10 are
explicit stress values because the exact Yang/SpherIC decay length is not public.

Output: GADGET-2 snapshot format 1, two collisionless particle types:
  type 1 = H, type 2 = L
Units: kpc, km/s, Msun. Time=0, redshift=0, non-cosmological.
"""
from __future__ import annotations
import argparse, json, math, hashlib, struct
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

G = 4.30091e-6
RHO_S = 6.89e6
R_S = 9.10
M200 = 1.0e11
MASS_RATIO = 3.0
A_MASS = 4.0*math.pi*RHO_S*R_S**3
C200 = brentq(lambda c: A_MASS*(math.log1p(c)-c/(1+c))-M200, 1.0, 30.0)
R200 = C200*R_S
A_PSI = 4.0*math.pi*G*RHO_S*R_S**2

class TruncatedNFW:
    def __init__(self, q=0.05, n_outer=12000):
        self.q=float(q)
        self.rd=self.q*R200
        self.epsilon=-(R_S+3.0*R200)/(R_S+R200)+R200/self.rd
        self.rho200=RHO_S/(C200*(1+C200)**2)
        self.rmax=R200+max(50.0*self.rd,5.0*R200)
        self.rg=np.geomspace(R200,self.rmax,n_outer)
        rho=self.rho(self.rg)
        mout=np.concatenate([[0.0],cumulative_trapezoid(4*math.pi*self.rg**2*rho,self.rg)])
        self.Mg=M200+mout
        self.Mtot=float(self.Mg[-1])
        fint=G*self.Mg/self.rg**2
        rev=cumulative_trapezoid(fint[::-1],self.rg[::-1],initial=0.0)
        self.psig=-rev[::-1]+G*self.Mtot/self.rmax
        self.psi200=float(self.psig[0])
        self.psi0=self.psi200+A_PSI*(1.0-math.log1p(C200)/C200)

    def rho(self,r):
        r=np.asarray(r,float)
        x=r/R_S
        inner=RHO_S/(np.maximum(x,1e-300)*(1+x)**2)
        outer=self.rho200*(r/R200)**self.epsilon*np.exp(-(r-R200)/self.rd)
        return np.where(r<=R200,inner,outer)

    def rho_derivs(self,r):
        r=np.asarray(r,float); rho=self.rho(r)
        ain=-1/r-2/(r+R_S); apin=1/r**2+2/(r+R_S)**2
        aout=self.epsilon/r-1/self.rd; apout=-self.epsilon/r**2
        a=np.where(r<=R200,ain,aout); ap=np.where(r<=R200,apin,apout)
        return rho,rho*a,rho*(a*a+ap)

    def M(self,r):
        arr=np.asarray(r,float); x=arr/R_S
        inner=A_MASS*(np.log1p(x)-x/(1+x))
        flat=arr.ravel()
        outer=np.interp(flat,self.rg,self.Mg,left=self.Mg[0],right=self.Mg[-1])
        outer=np.where(flat>self.rmax,self.Mtot,outer).reshape(arr.shape)
        return np.where(arr<=R200,inner,outer)

    def psi(self,r):
        arr=np.asarray(r,float); x=arr/R_S
        ratio=np.where(x<1e-8,1-x/2+x*x/3,np.log1p(x)/x)
        inner=self.psi200+A_PSI*(ratio-math.log1p(C200)/C200)
        flat=arr.ravel()
        outer=np.interp(flat,self.rg,self.psig,left=self.psig[0],right=self.psig[-1])
        outer=np.where(flat>self.rmax,G*self.Mtot/flat,outer).reshape(arr.shape)
        return np.where(arr<=R200,inner,outer)

    def d2rho_dpsi2(self,r):
        arr=np.asarray(r,float)
        rho,rp,rpp=self.rho_derivs(arr); M=self.M(arr)
        psip=-G*M/arr**2
        psipp=-G*(4*math.pi*rho-2*M/arr**3)
        return (rpp*psip-rp*psipp)/(psip**3)

    def build_inverse(self):
        ri=np.geomspace(1e-8*R_S,R200,12000)
        ro=self.rg[1:]
        extra=np.geomspace(self.rmax*1.001,self.rmax*1e5,3000)
        rr=np.concatenate([ri,ro,extra])
        pp=np.concatenate([self.psi(np.concatenate([ri,ro])),G*self.Mtot/extra])
        self._map_r=rr[::-1]; self._map_psi=pp[::-1]

    def r_of_psi(self,psi):
        if not hasattr(self,"_map_r"): self.build_inverse()
        p=np.asarray(psi,float)
        pc=np.clip(p,self._map_psi[0],self._map_psi[-1])
        return np.exp(np.interp(pc,self._map_psi,np.log(self._map_r)))

def build_df(halo,nE=1300,nth=96):
    Elo=1e-2
    Emax=float(halo.psi(1e-4*R_S))*0.99999999
    dmin=max(halo.psi0-Emax,1e-6); dmax=halo.psi0-Elo
    E=(halo.psi0-np.geomspace(dmin,dmax,nE))[::-1]
    E=np.unique(np.concatenate([np.geomspace(Elo,min(1000.0,Emax),300),E]))
    E=E[(E>0)&(E<=Emax)]
    x,w=leggauss(nth); th=(x+1)*math.pi/4; wt=w*math.pi/4; st=np.sin(th)
    f=np.empty_like(E)
    for j,ee in enumerate(E):
        rr=halo.r_of_psi(ee*st**2)
        f[j]=(2*math.sqrt(ee)/(math.sqrt(8)*math.pi**2))*np.sum(wt*st*halo.d2rho_dpsi2(rr))
    pos=f>0
    Ep,fp=E[pos],f[pos]
    sp=PchipInterpolator(np.log(Ep),np.log(fp),extrapolate=False)
    def feval(q):
        q=np.asarray(q,float); out=np.zeros_like(q)
        m=(q>=Ep[0])&(q<=Ep[-1])
        out[m]=np.exp(sp(np.log(q[m])))
        return out
    return Ep,fp,feval

def make_mass_inverse(halo,n=20000):
    rg=np.geomspace(1e-7*R_S,halo.rmax,n)
    mg=halo.M(rg)
    keep=np.r_[True, np.diff(mg) > np.maximum(1e-12*np.maximum(mg[:-1],1.0), 0.0)]
    mgu=mg[keep]; rgu=rg[keep]
    if mgu[-1] < halo.Mtot*(1-1e-10):
        mgu=np.r_[mgu,halo.Mtot]; rgu=np.r_[rgu,halo.rmax]
    return PchipInterpolator(mgu,rgu,extrapolate=False)

def sample_radii(halo,n,rng):
    inv=make_mass_inverse(halo)
    u=(np.arange(n)+rng.random(n))/n
    rng.shuffle(u)
    return inv(np.maximum(u*halo.Mtot,halo.M(1e-7*R_S)))

def sample_positions(r,rng):
    mu=2*rng.random(len(r))-1
    phi=2*math.pi*rng.random(len(r))
    st=np.sqrt(np.maximum(0,1-mu*mu))
    return np.column_stack([r*st*np.cos(phi),r*st*np.sin(phi),r*mu])

def sample_speeds(halo,feval,r,rng):
    out=np.empty(len(r))
    for i,rr in enumerate(r):
        psi=float(halo.psi(rr)); ve=math.sqrt(2*psi)
        grid=np.linspace(0,ve,128)
        pg=grid*grid*feval(psi-.5*grid*grid)
        pmax=float(np.max(pg))*1.02+1e-300
        while True:
            v=ve*rng.random()
            p=v*v*float(feval(np.array([psi-.5*v*v]))[0])
            if rng.random()*pmax <= p:
                out[i]=v; break
    return out

def sample_velocities(halo,feval,r,rng):
    v=sample_speeds(halo,feval,r,rng)
    mu=2*rng.random(len(r))-1
    phi=2*math.pi*rng.random(len(r))
    st=np.sqrt(np.maximum(0,1-mu*mu))
    return np.column_stack([v*st*np.cos(phi),v*st*np.sin(phi),v*mu])

def recenter(pos,vel,mass):
    mt=mass.sum()
    pos-=np.sum(pos*mass[:,None],axis=0)/mt
    vel-=np.sum(vel*mass[:,None],axis=0)/mt
    return pos,vel

def write_record(f,b):
    f.write(struct.pack("<I",len(b))); f.write(b); f.write(struct.pack("<I",len(b)))

def write_gadget_format1(path,pos,vel,ids,ptype,mass):
    order=np.argsort(ptype,kind="stable")
    pos=np.asarray(pos[order],np.float32); vel=np.asarray(vel[order],np.float32)
    ids=np.asarray(ids[order],np.uint32); ptype=np.asarray(ptype[order],np.int32)
    mass=np.asarray(mass[order],np.float32)
    npart=np.array([(ptype==i).sum() for i in range(6)],dtype=np.uint32)
    mass_table=np.zeros(6,dtype=np.float64)
    npart_total=npart.copy()

    header=bytearray(256); off=0
    def put(fmt,*vals):
        nonlocal off
        b=struct.pack("<"+fmt,*vals); header[off:off+len(b)]=b; off+=len(b)
    put("6I",*npart.tolist()); put("6d",*mass_table.tolist())
    put("d",0.0); put("d",0.0); put("i",0); put("i",0)
    put("6I",*npart_total.tolist()); put("i",0); put("i",1)
    put("d",0.0); put("d",0.0); put("d",0.0); put("d",1.0)
    put("i",0); put("i",0)
    put("6I",*([0]*6)); put("i",0)

    with open(path,"wb") as f:
        write_record(f,bytes(header))
        write_record(f,pos.tobytes(order="C"))
        write_record(f,vel.tobytes(order="C"))
        write_record(f,ids.tobytes(order="C"))
        write_record(f,mass.tobytes(order="C"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n-total",type=int,default=1_000_000)
    ap.add_argument("--seed",type=int,default=126001)
    ap.add_argument("--taper",type=float,default=0.05,choices=[0.03,0.05,0.10])
    ap.add_argument("--output",default="M11_D3_1M.dat")
    ap.add_argument("--metadata",default=None)
    args=ap.parse_args()
    if args.n_total%2: raise SystemExit("n-total must be even")
    rng=np.random.default_rng(args.seed)
    halo=TruncatedNFW(args.taper)
    Ep,fp,feval=build_df(halo)

    n=args.n_total//2
    rH=sample_radii(halo,n,rng); rL=sample_radii(halo,n,rng)
    pH=sample_positions(rH,rng); pL=sample_positions(rL,rng)
    vH=sample_velocities(halo,feval,rH,rng); vL=sample_velocities(halo,feval,rL,rng)

    mL=halo.Mtot/(4*n)
    mH=3*mL
    pos=np.vstack([pH,pL]); vel=np.vstack([vH,vL])
    ptype=np.r_[np.ones(n,dtype=np.int32),np.full(n,2,dtype=np.int32)]
    mass=np.r_[np.full(n,mH),np.full(n,mL)]
    ids=np.arange(1,args.n_total+1,dtype=np.uint32)
    pos,vel=recenter(pos,vel,mass)
    write_gadget_format1(args.output,pos,vel,ids,ptype,mass)

    meta={
      "generator":"phase141_generate_m11_ic.py",
      "n_total":args.n_total,"n_H":n,"n_L":n,"seed":args.seed,
      "M200_Msun":M200,"rho_s_Msun_kpc3":RHO_S,"r_s_kpc":R_S,
      "c200":C200,"r200_kpc":R200,"taper_rd_over_r200":args.taper,
      "Mtotal_tapered_Msun":halo.Mtot,
      "mH_num_Msun":mH,"mL_num_Msun":mL,"mass_ratio":mH/mL,
      "snapshot":str(Path(args.output).resolve()),
      "snapshot_sha256":hashlib.sha256(Path(args.output).read_bytes()).hexdigest(),
      "total_momentum_Msun_km_s":np.sum(vel*mass[:,None],axis=0).tolist()
    }
    mpath=args.metadata or (args.output+".json")
    Path(mpath).write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
