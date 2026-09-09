#!/usr/bin/env python3
"""Public wide-binary data ingestion for Hellard-gravity tests.

This module intentionally separates DATA ACCESS from the gravity likelihood.
It supports two public catalogues:

1. Shariat, El-Badry & Bhattacharjee (2026), Gaia DR3 wide binaries out to 5 kpc.
   Zenodo record 17957444. The cleaned catalogue has R_chance_align < 0.1 and
   contains Gaia DR3 astrometry plus projected separation.

2. Pittordis & Sutherland (2023), Gaia EDR3 gravity-test sample.
   Zenodo record 7629240. The public table contains 73,087 candidate systems
   and was built specifically for wide-binary gravity tests.

The large files are not downloaded in ordinary CI because they are hundreds of
MB. Use --catalog dr3 or --catalog edr3 on a research runner/AWS instance.
"""
from __future__ import annotations

import argparse
import pathlib
import urllib.request

DR3_URL = (
    "https://zenodo.org/records/17957444/files/"
    "wide_binaries_5kpc_clean.fits.gz?download=1"
)
EDR3_URL = (
    "https://zenodo.org/records/7629240/files/"
    "CleanedWB_EDR3_Prlx300pc_Gmag20_20230111_Size73087_ZenodoSample.csv?download=1"
)


def stream_download(url: str, path: pathlib.Path, chunk: int = 2**20) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "hellard-gravity-research/1"})
    with urllib.request.urlopen(req, timeout=120) as response, path.open("wb") as out:
        while True:
            block = response.read(chunk)
            if not block:
                break
            out.write(block)
    return path


def catalog_url(name: str) -> str:
    if name == "dr3":
        return DR3_URL
    if name == "edr3":
        return EDR3_URL
    raise ValueError(name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", choices=["dr3", "edr3"], required=True)
    parser.add_argument("--outdir", default="data")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    url = catalog_url(args.catalog)
    print(f"catalog={args.catalog}")
    print(f"url={url}")
    if not args.download:
        print("dry run only; pass --download on a large-data runner")
        return

    suffix = "wide_binaries_5kpc_clean.fits.gz" if args.catalog == "dr3" else "wide_binaries_edr3_73087.csv"
    path = pathlib.Path(args.outdir) / suffix
    stream_download(url, path)
    print(f"downloaded={path} bytes={path.stat().st_size}")


if __name__ == "__main__":
    main()
