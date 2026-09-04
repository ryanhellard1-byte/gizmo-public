#!/usr/bin/env python3
"""Deterministic GADGET-2 format-1 homogeneous H/L streaming box for Phase 178."""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np

MSUN_G = 1.98847e33
KPC_CM = 3.0856775814913673e21

def block(f, payload: bytes):
    n=len(payload)
    f.write(struct.pack('<I',n)); f.write(payload); f.write(struct.pack('<I',n))

def header(n_each, box):
    npart=[0,n_each,n_each,0,0,0]
    mass=[0.0]*6
    npart_total=npart[:]
    b=bytearray()
    b += struct.pack('<6I',*npart)
    b += struct.pack('<6d',*mass)
    b += struct.pack('<d',0.0)  # time
    b += struct.pack('<d',0.0)  # redshift
    b += struct.pack('<i',0)    # flag_sfr
    b += struct.pack('<i',0)    # flag_feedback
    b += struct.pack('<6I',*npart_total)
    b += struct.pack('<i',0)    # flag_cooling
    b += struct.pack('<i',1)    # num_files
    b += struct.pack('<d',box)
    b += struct.pack('<d',0.0)  # Omega0
    b += struct.pack('<d',0.0)  # OmegaLambda
    b += struct.pack('<d',1.0)  # HubbleParam
    b += struct.pack('<i',0)    # flag_stellarage
    b += struct.pack('<i',0)    # flag_metals
    b += struct.pack('<6I',0,0,0,0,0,0)
    b += struct.pack('<i',0)    # flag_entropy_instead_u
    b += bytes(60)
    assert len(b)==256, len(b)
    return bytes(b)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--n-each',type=int,default=4096)
    ap.add_argument('--box',type=float,default=0.02,help='box side in kpc code units')
    ap.add_argument('--v',type=float,default=81.682,help='L stream speed in km/s')
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    rng=np.random.default_rng(args.seed)
    n=args.n_each; nt=2*n
    # Particle ordering must be contiguous by GADGET type: type 1 H, type 2 L.
    pos=rng.uniform(0.0,args.box,size=(nt,3)).astype('<f4')
    vel=np.zeros((nt,3),dtype='<f4')
    vel[n:,0]=args.v
    ids=np.arange(1,nt+1,dtype='<u4')
    masses=np.concatenate((np.full(n,3.0,dtype='<f4'),np.full(n,1.0,dtype='<f4')))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('wb') as f:
        block(f,header(n,args.box))
        block(f,pos.tobytes(order='C'))
        block(f,vel.tobytes(order='C'))
        block(f,ids.tobytes(order='C'))
        block(f,masses.tobytes(order='C'))
    rho_h_g_cm3=n*3.0*MSUN_G/(args.box*KPC_CM)**3
    meta={
      'n_H':n,'n_L':n,'mass_H_code':3.0,'mass_L_code':1.0,'mass_ratio':3.0,
      'box_kpc':args.box,'v_H_km_s':[0,0,0],'v_L_km_s':[args.v,0,0],
      'seed':args.seed,'rho_H_g_cm3':rho_h_g_cm3,
      'snapshot':str(out),'snapshot_sha256':hashlib.sha256(out.read_bytes()).hexdigest()
    }
    Path(str(out)+'.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))
if __name__=='__main__': main()
