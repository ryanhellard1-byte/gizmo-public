#!/usr/bin/env python3
"""Embedded byte-exact Phase165 production manifest.

The CSV is zlib-compressed and base64-encoded only to keep the repository bridge
compact. `csv_bytes()` reproduces the original 24,374-byte frozen file exactly.
"""
from __future__ import annotations
import base64, hashlib, zlib
from pathlib import Path

FROZEN_SHA256 = "08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3"
_COMPRESSED_B64 = """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"""

def csv_bytes() -> bytes:
    data = zlib.decompress(base64.b64decode(_COMPRESSED_B64))
    observed = hashlib.sha256(data.decode("utf-8").encode("utf-8")).hexdigest()
    if observed != FROZEN_SHA256:
        raise RuntimeError(f"embedded Phase165 manifest SHA mismatch: {observed}")
    return data

def csv_text() -> str:
    return csv_bytes().decode("utf-8")

def materialize(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(csv_bytes())
    return path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    args = ap.parse_args()
    p = materialize(args.output)
    print(p)
    print(FROZEN_SHA256)
