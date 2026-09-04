#!/usr/bin/env python3
"""Generate a Phase-172 M11 IC, including equal-label and permutation controls."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

# Reuse the frozen Phase-141 M11 equilibrium machinery without copying it.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from phase141_generate_m11_ic import (
    TruncatedNFW, build_df, sample_radii, sample_positions, sample_velocities,
    recenter, write_gadget_format1
)


def serialized_species_masses(total_mass: float, n_per_species: int, ratio: float):
    """Return float32-representable species masses preserving the exact ratio.

    GADGET format-1 stores the per-particle mass block as binary32 in the frozen
    writer.  Rounding m_H and m_L independently can therefore turn a mathematically
    exact 3:1 ratio into e.g. 2.999999782..., which correctly trips the fail-closed
    D3 species-contract guard when the IC is read back.

    Quantize the light mass once, derive the heavy mass from that serialized value,
    and fail closed unless the values that will actually be written retain the
    requested ratio exactly when promoted back to double precision.
    """
    target_mL = float(total_mass) / (int(n_per_species) * (float(ratio) + 1.0))
    stored_mL = float(np.float32(target_mL))
    stored_mH = float(np.float32(float(ratio) * stored_mL))
    observed_ratio = stored_mH / stored_mL
    if observed_ratio != float(ratio):
        raise RuntimeError(
            f"cannot represent requested H/L mass ratio exactly in float32: "
            f"requested={ratio!r} observed={observed_ratio!r} "
            f"mH={stored_mH!r} mL={stored_mL!r}"
        )
    return target_mL, stored_mH, stored_mL


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
    target_mL,mH,mL=serialized_species_masses(halo.Mtot,n,ratio)
    serialized_total_mass=n*(mH+mL)
    pos=np.vstack([pH,pL]); vel=np.vstack([vH,vL])
    ptype=np.r_[np.ones(n,dtype=np.int32),np.full(n,2,dtype=np.int32)]
    # Keep float64 arrays for recentering, but every value is already exactly
    # representable as float32, so write_gadget_format1's cast cannot change it.
    mass=np.r_[np.full(n,mH,dtype=np.float64),np.full(n,mL,dtype=np.float64)]
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
      "seed":args.seed,"mass_ratio":ratio,"serialized_mass_ratio":mH/mL,
      "ic_order":args.order,
      "mH_num_Msun":mH,"mL_num_Msun":mL,
      "target_mL_num_Msun":target_mL,
      "target_total_mass_Msun":halo.Mtot,
      "serialized_total_mass_Msun":serialized_total_mass,
      "relative_total_mass_quantization_error":(serialized_total_mass-halo.Mtot)/halo.Mtot,
      "mass_storage_contract":"float32_exact_species_ratio",
      "taper_rd_over_r200":args.taper,
      "snapshot":str(out.resolve()),
      "snapshot_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
      "total_momentum_Msun_km_s":np.sum(vel*mass[:,None],axis=0).tolist()
    }
    Path(str(out)+".json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
