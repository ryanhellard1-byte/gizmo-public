#!/usr/bin/env python3
"""Create a collision-stress GADGET snapshot by scaling only particle positions.

This is a commissioning tool, not a production IC generator. It preserves the
header, velocities, IDs, particle types, masses, and therefore the frozen D3
microphysics. Compressing positions raises density so a tiny CI run produces
real SIDM collisions instead of passing with zero accepted events.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
import numpy as np


def read_record(f):
    raw=f.read(4)
    if not raw:
        return None
    if len(raw)!=4:
        raise ValueError("truncated record header")
    (n,)=struct.unpack("<I",raw)
    data=f.read(n)
    if len(data)!=n:
        raise ValueError("truncated record body")
    tail=f.read(4)
    if len(tail)!=4 or struct.unpack("<I",tail)[0]!=n:
        raise ValueError("record marker mismatch")
    return data


def write_record(f,data: bytes):
    f.write(struct.pack("<I",len(data)))
    f.write(data)
    f.write(struct.pack("<I",len(data)))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--scale",type=float,required=True)
    args=ap.parse_args()
    if not (0.0 < args.scale <= 1.0):
        raise SystemExit("--scale must be in (0,1]")

    records=[]
    with open(args.input,"rb") as f:
        while True:
            r=read_record(f)
            if r is None: break
            records.append(r)
    if len(records)<4:
        raise SystemExit(f"expected GADGET format-1 records, got {len(records)}")
    if len(records[0])!=256:
        raise SystemExit(f"expected 256-byte GADGET header, got {len(records[0])}")
    if len(records[1])%12:
        raise SystemExit("position record is not N x 3 float32")

    pos=np.frombuffer(records[1],dtype="<f4").copy().reshape(-1,3)
    before=np.max(np.linalg.norm(pos,axis=1))
    pos*=args.scale
    after=np.max(np.linalg.norm(pos,axis=1))
    records[1]=pos.astype("<f4",copy=False).tobytes(order="C")

    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    with open(args.output,"wb") as f:
        for r in records:
            write_record(f,r)

    print(f"COLLISION_STRESS_IC n={len(pos)} scale={args.scale:.8g} rmax_before={before:.8g} rmax_after={after:.8g}")
    print("NOTE: positions only were scaled; velocities, IDs, masses, and types are byte-identical to the input snapshot")


if __name__=="__main__":
    main()
