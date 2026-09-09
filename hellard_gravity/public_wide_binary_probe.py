#!/usr/bin/env python3
"""Probe public wide-binary datasets for Hellard spectral-dominance likelihood work.

This script deliberately does not claim a fit. It fetches small machine-readable
public data products and reports their schema so the next analysis step can map
observables to the action prediction without inventing columns.

Public sources:
- Chae 3D/HARPS value-added sample, Zenodo 17113129
- Chae general-gravity grid solution for the same sample
"""
from __future__ import annotations

import csv
import io
import urllib.request

FILES = {
    "chae_harps": "https://zenodo.org/records/17113129/files/gaia_purewb_3D_valueadded_harpscorr.csv?download=1",
    "chae_general_grid": "https://zenodo.org/records/17113129/files/gaia_purewb_3D_valueadded_harpscorr_perspective_gridsol_general.csv?download=1",
    "chae_newton_grid": "https://zenodo.org/records/17113129/files/gaia_purewb_3D_valueadded_harpscorr_perspective_gridsol_newton.csv?download=1",
}

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "hellard-gravity-research/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")

def summarize(name: str, text: str) -> None:
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    print(f"{name}: rows={len(rows)} columns={len(reader.fieldnames or [])}")
    print("columns:")
    print(",".join(reader.fieldnames or []))
    if rows:
        first = rows[0]
        print("first-row nonempty fields:")
        print({k: v for k, v in first.items() if v not in ("", None)})

def main() -> None:
    for name, url in FILES.items():
        print(f"\n=== {name} ===")
        summarize(name, fetch_text(url))

if __name__ == "__main__":
    main()
