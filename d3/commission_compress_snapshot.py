#!/usr/bin/env python3
"""Create a dense commissioning snapshot without changing D3 microphysics.

This is deliberately NOT a production halo IC. It takes a deterministic
GADGET format-1 snapshot and scales only its Coordinates block about the
origin. Velocities, particle IDs, types, masses, and the header are preserved.
The purpose is to raise the physical pair density enough that GitHub CI can
exercise the real accepted-collision branch of GIZMO while keeping the frozen
D3 cross sections untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


def read_record(f):
    raw = f.read(4)
    if len(raw) != 4:
        raise EOFError("missing GADGET record prefix")
    (n,) = struct.unpack("<I", raw)
    payload = f.read(n)
    if len(payload) != n:
        raise EOFError("truncated GADGET record")
    raw2 = f.read(4)
    if len(raw2) != 4 or struct.unpack("<I", raw2)[0] != n:
        raise ValueError("GADGET record framing mismatch")
    return payload


def write_record(f, payload):
    f.write(struct.pack("<I", len(payload)))
    f.write(payload)
    f.write(struct.pack("<I", len(payload)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--scale", type=float, default=0.04)
    args = ap.parse_args()
    if not (0.0 < args.scale <= 1.0):
        raise SystemExit("--scale must be in (0,1]")

    src = Path(args.input)
    dst = Path(args.output)
    with src.open("rb") as f:
        header = read_record(f)
        coords = read_record(f)
        remaining = f.read()

    if len(header) != 256:
        raise SystemExit(f"expected 256-byte GADGET header, got {len(header)}")
    if len(coords) % 12:
        raise SystemExit("coordinate block is not float32 Nx3")

    pos = np.frombuffer(coords, dtype="<f4").copy().reshape(-1, 3)
    pos *= np.float32(args.scale)

    with dst.open("wb") as f:
        write_record(f, header)
        write_record(f, pos.astype("<f4", copy=False).tobytes(order="C"))
        f.write(remaining)

    meta = {
        "transform": "commission_compress_snapshot.py",
        "input": str(src.resolve()),
        "output": str(dst.resolve()),
        "position_scale": args.scale,
        "density_scale": args.scale ** -3,
        "n_particles": int(pos.shape[0]),
        "input_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        "production_ic": False,
        "purpose": "live accepted-collision commissioning only",
    }
    Path(str(dst) + ".json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
