#!/usr/bin/env python3
"""Generate a Phase-172 M11 IC, including equal-label and permutation controls."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

from phase141_generate_m11_ic import (
    TruncatedNFW, build_df, sample_radii, sample_positions, sample_velocities,
    recenter, write_gadget_format1
)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n-total",type=int,required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--mass-ratio",type=float,choices=[1.0,3.0],required=True)
    ap.add_argument("--order",choices=["canonical","shuffled_within_species"],default="canonical")
    ap.add_argument("--taper",type=float,default=0.05,choices=[0.03,0.05,0.10])
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    if args.n_total <= 0 or args.n_total % 2:
        raise SystemExit("n-total must be a positive even integer")

    rng=np.random.default_rng(args.seed)
    halo=TruncatedNFW(args.taper)
    _,_,feval=build_df(halo)
    n=args.n_total//2

    rH=sample_radii(halo,n,rng); rL=sample_radii(halo,n,rng)
    pH=sample_positions(rH,rng); pL=sample_positions(rL,rng)
    vH=sample_velocities(halo,feval,rH,rng); vL=sample_velocities(halo,feval,rL,rng)

    ratio=float(args.mass_ratio)
    mL=halo.Mtot/(n*(ratio+1.0)); mH=ratio*mL
    pos=np.vstack([pH,pL]); vel=np.vstack([vH,vL])
    ptype=np.r_[np.ones(n,dtype=np.int32),np.full(n,2,dtype=np.int32)]
    mass=np.r_[np.full(n,mH),np.full(n,mL)]
    ids=np.arange(1,args.n_total+1,dtype=np.uint32)
    pos,vel=recenter(pos,vel,mass)

    if args.order=="shuffled_within_species":
        prng=np.random.default_rng(args.seed ^ 0x172D3)
        h=np.arange(0,n); l=np.arange(n,2*n)
        prng.shuffle(h); prng.shuffle(l)
        perm=np.r_[h,l]
        pos,vel,ptype,mass,ids=(x[perm] for x in (pos,vel,ptype,mass,ids))

    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    write_gadget_format1(out,pos,vel,ids,ptype,mass)
    meta={
      "generator":"phase172_make_ic.py","n_total":args.n_total,"n_H":n,"n_L":n,
      "seed":args.seed,"mass_ratio":ratio,"ic_order":args.order,
      "mH_num_Msun":mH,"mL_num_Msun":mL,"taper_rd_over_r200":args.taper,
      "snapshot":str(out.resolve()),
      "snapshot_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
      "total_momentum_Msun_km_s":np.sum(vel*mass[:,None],axis=0).tolist()
    }
    Path(str(out)+".json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
