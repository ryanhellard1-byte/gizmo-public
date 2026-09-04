#!/usr/bin/env python3
"""Phase 172 frozen production-manifest lock."""
from __future__ import annotations
import argparse, base64, csv, hashlib, io, json, zlib
from pathlib import Path

EXPECTED_SHA = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
BLOB = """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"""

MODE = {"CDM":0.0,"SIDMx":-2.0,"HL_off":-3.0,"SIDM2v":-1.0,
        "HH_only":-4.0,"LL_only":-5.0,"HL_HH":-6.0,"HL_LL":-7.0,
        "SIDM2c_const":-8.0}

def load():
    raw=zlib.decompress(base64.b64decode(BLOB))
    sha=hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise SystemExit(f"embedded manifest SHA mismatch: {sha}")
    rows=list(csv.DictReader(io.StringIO(raw.decode())))
    return raw,rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--write",default=None,help="materialize the frozen CSV")
    args=ap.parse_args()
    raw,rows=load()
    checks={}
    checks["rows_127"]=len(rows)==127
    checks["blind_119"]=sum(r["blind_analysis"]=="True" for r in rows)==119
    checks["unique_ids"]=len({r["run_id"] for r in rows})==127

    core=[r for r in rows if r["group"]=="core_blind_production"]
    checks["core_48"]=len(core)==48
    checks["core_4x3x4"]=all(
      len([r for r in core if r["branch"]==b and r["resolution_tier"]==t])==4
      for b in ("CDM","SIDMx","HL_off","SIDM2v")
      for t in ("R1_base","R2_double","R3_gold"))

    checks["mass_contract"]=all(
      abs(float(r["particle_mass_ratio_H_over_L"]) -
          (1.0 if r["group"]=="identical_label_null" else 3.0)) < 1e-12
      for r in rows)

    def mode_ok(r):
        x=float(r["runtime_interaction_parameter"])
        if r["group"]=="identical_label_null":
            return r["runtime_contract"]=="standard_constant_identical_labels" and abs(x-1.125)<1e-12
        if r["group"]=="zero_cross_section_null":
            return r["runtime_contract"]=="d3_zero_cross_section" and abs(x+9.0)<1e-12
        return r["runtime_contract"]=="d3_frozen" and abs(x-MODE[r["branch"]])<1e-12
    checks["runtime_modes"]=all(mode_ok(r) for r in rows)

    core_r2={(r["branch"],r["seed"]) for r in core if r["resolution_tier"]=="R2_double"}
    checks["half_dt_paired"]=all((r["branch"],r["seed"]) in core_r2
      for r in rows if r["group"]=="half_timestep_convergence")
    checks["neighbor_paired"]=all((r["branch"],r["seed"]) in core_r2
      for r in rows if r["group"]=="neighbor_kernel_convergence")

    s2v={(r["resolution_tier"],r["seed"]) for r in core if r["branch"]=="SIDM2v"}
    checks["ablations_paired"]=all((r["resolution_tier"],r["seed"]) in s2v
      for r in rows if r["group"]=="channel_ablation")

    c2={r["seed"] for r in rows if r["group"]=="constant_SIDM2c_benchmark"
         and r["resolution_tier"]=="R2_double"}
    checks["sidm2c_half_dt_paired"]=all(r["seed"] in c2
      for r in rows if r["group"]=="constant_SIDM2c_half_timestep")

    cdm={r["seed"] for r in core if r["branch"]=="CDM" and r["resolution_tier"]=="R2_double"}
    checks["zero_xs_paired"]=all(r["seed"] in cdm
      for r in rows if r["group"]=="zero_cross_section_null")

    s2v_r2={r["seed"] for r in core if r["branch"]=="SIDM2v" and r["resolution_tier"]=="R2_double"}
    checks["permutation_paired"]=all(
      r["seed"] in s2v_r2 and r["ic_order"]=="shuffled_within_species"
      for r in rows if r["group"]=="permutation_reproducibility")

    ok=all(checks.values())
    if args.write:
        Path(args.write).write_bytes(raw)
    print(json.dumps({"status":"PASS" if ok else "FAIL",
      "manifest_sha256":EXPECTED_SHA,"checks":checks},indent=2))
    raise SystemExit(0 if ok else 1)

if __name__=="__main__":
    main()
