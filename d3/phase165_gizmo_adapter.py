#!/usr/bin/env python3
"""Fail-closed Phase165 -> native GIZMO_D3 production adapter.

This file does not define or tune physics. It converts a frozen manifest row into
an IC generation command, a native GIZMO parameter file, and provenance records.
Execution is opt-in (--execute); default behavior is a dry-run staging audit.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, shlex, subprocess, sys
from pathlib import Path

FROZEN_MANIFEST_SHA256 = "08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3"
FROZEN_MASTER_COMMIT = "a5e7b7e777bd211bf0f0b5c667a9957f476ef0ec"
FROZEN_EXECUTABLE_SHA256 = "677a881fc0964012df39c4736180ce77fb8400ca494f1a6b2776110b6d560155"

# Native modes are frozen in sidm/sidmx_d3_impl.h. Aliases cover historical
# manifest labels without changing their physical meaning.
MODE = {
    "CDM": -9, "null": -9,
    "SIDMx": -2, "HL": -2, "HL_only": -2,
    "HL_off": -3, "HH_LL": -3,
    "HH_only": -4, "LL_only": -5,
    "HL_HH": -6, "HL_LL": -7,
    "SIDM2c": -8, "constant": -8,
    "SIDM2v": -1, "full": -1,
}

RESOLUTION = {
    "R0": (100_000, 100_000, 0.060),
    "R1": (300_000, 300_000, 0.040),
    "R2": (600_000, 600_000, 0.028),
    "R3": (1_200_000, 1_200_000, 0.020),
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def pick(row, *names, default=None):
    for n in names:
        if n in row and str(row[n]).strip() != "": return str(row[n]).strip()
    return default

def parse_int(row, *names, default=None):
    v=pick(row,*names,default=default)
    return None if v is None else int(float(v))

def branch_mode(row):
    b=pick(row,"branch","model","physics_branch","channel_set")
    if b not in MODE: raise SystemExit(f"unsupported/fail-closed branch label: {b!r}")
    return b, MODE[b]

def resolution(row):
    r=pick(row,"resolution","res","resolution_level")
    if r in RESOLUTION:
        nh,nl,eps=RESOLUTION[r]
    else:
        nh=parse_int(row,"n_H","N_H","n_h")
        nl=parse_int(row,"n_L","N_L","n_l")
        eps=float(pick(row,"softening_kpc","epsilon_kpc","epsilon","softening"))
        if nh is None or nl is None: raise SystemExit("missing resolution/N_H/N_L")
    if nh != nl: raise SystemExit(f"species contract violated: N_H={nh} N_L={nl}")
    return r or "custom",nh,nl,eps

def render_params(ic: Path, out: Path, mode: int, eps: float, ngb: int, dtmax: float, timemax: float):
    return f"""% Phase165 native GIZMO_D3 production parameters. Generated fail-closed.\nInitCondFile {ic.resolve()}\nOutputDir {out.resolve()}/\nICFormat 1\nSnapFormat 1\nSnapshotFileBase snapshot\nRestartFile restart\nOutputListOn 0\nNumFilesPerSnapshot 1\nNumFilesWrittenInParallel 1\nTimeOfFirstSnapshot {timemax:.17g}\nTimeBetSnapshot 2.0\nTimeLimitCPU 259200\nCpuTimeBetRestartFile 3600\nMaxMemSize 120000\nPartAllocFactor 4.0\nBufferSize 256\nTimeBegin 0.0\nTimeMax {timemax:.17g}\nMaxSizeTimestep {dtmax:.17g}\nMinSizeTimestep 1.0e-12\nUnitLength_in_cm 3.085678e21\nUnitMass_in_g 1.989e33\nUnitVelocity_in_cm_per_s 1.0e5\nGravityConstantInternal 0\nComovingIntegrationOn 0\nBoxSize 2000.0\nOmega_Matter 0\nOmega_Lambda 0\nOmega_Baryon 0\nHubbleParam 1.0\nAGS_DesNumNgb {ngb}\nTreeRebuild_ActiveFraction 0.01\nSoftening_Type0 {eps:.17g}\nSoftening_Type1 {eps:.17g}\nSoftening_Type2 {eps:.17g}\nSoftening_Type3 {eps:.17g}\nSoftening_Type4 {eps:.17g}\nSoftening_Type5 {eps:.17g}\nDM_InteractionCrossSection {mode}\nDM_InteractionVelocityScale 0\nDM_DissipationFactor 0\nDM_KickPerCollision 0\n"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("run_id")
    ap.add_argument("--executable", type=Path, required=True)
    ap.add_argument("--work-root", type=Path, default=Path("phase165_runs"))
    ap.add_argument("--generator", type=Path, default=Path(__file__).with_name("phase141_generate_m11_ic.py"))
    ap.add_argument("--mpiexec", default="mpirun -np 4")
    ap.add_argument("--execute", action="store_true")
    args=ap.parse_args()

    if sha256(args.manifest) != FROZEN_MANIFEST_SHA256:
        raise SystemExit("FATAL: Phase165 manifest SHA256 mismatch")
    if sha256(args.executable) != FROZEN_EXECUTABLE_SHA256:
        raise SystemExit("FATAL: GIZMO_D3 executable SHA256 mismatch")

    with args.manifest.open(newline="") as f: rows=list(csv.DictReader(f))
    row=next((r for r in rows if pick(r,"run_id","id","run") == args.run_id),None)
    if row is None: raise SystemExit(f"run_id not found: {args.run_id}")

    branch,mode=branch_mode(row)
    res,nh,nl,eps=resolution(row)
    seed=parse_int(row,"seed","random_seed","ic_seed")
    if seed is None: raise SystemExit("missing seed")
    ngb=parse_int(row,"neighbors","num_neighbors","ngb",default="32")
    # Time values are read from the frozen manifest where available. The fallback
    # is the frozen 10-Gyr production endpoint expressed in the project's native
    # time convention; sites may override only by manifest field, never CLI.
    timemax=float(pick(row,"time_max","TimeMax","t_final",default="10.0"))
    dtmax=float(pick(row,"max_timestep","MaxSizeTimestep","dt_max",default="0.002"))
    taper=float(pick(row,"taper_rd_over_r200","taper",default="0.05"))

    run_dir=args.work_root/args.run_id; run_dir.mkdir(parents=True,exist_ok=True)
    ic_dir=args.work_root/"ic_cache"; ic_dir.mkdir(parents=True,exist_ok=True)
    ic=ic_dir/f"M11_{res}_seed{seed}_taper{taper:g}.dat"
    meta=Path(str(ic)+".json")
    gen=[sys.executable,str(args.generator),"--n-total",str(nh+nl),"--seed",str(seed),"--taper",str(taper),"--output",str(ic),"--metadata",str(meta)]
    if not ic.exists():
        if not args.execute: print("DRY-RUN IC:",shlex.join(gen))
        else: subprocess.run(gen,check=True)
    if args.execute and not ic.exists(): raise SystemExit("IC generation failed")

    params=run_dir/"params.txt"
    params.write_text(render_params(ic,run_dir,mode,eps,ngb,dtmax,timemax))
    cmd=shlex.split(args.mpiexec)+[str(args.executable.resolve()),str(params.resolve())]
    prov={"run_id":args.run_id,"branch":branch,"d3_mode":mode,"resolution":res,"N_H":nh,"N_L":nl,
          "softening_kpc":eps,"neighbors":ngb,"seed":seed,"taper":taper,"TimeMax":timemax,"MaxSizeTimestep":dtmax,
          "manifest_sha256":FROZEN_MANIFEST_SHA256,"master_commit":FROZEN_MASTER_COMMIT,
          "executable_sha256":FROZEN_EXECUTABLE_SHA256,"params_sha256":sha256(params),
          "ic_sha256":sha256(ic) if ic.exists() else None,"command":cmd,"executed":bool(args.execute)}
    (run_dir/"prelaunch_provenance.json").write_text(json.dumps(prov,indent=2)+"\n")
    print(json.dumps(prov,indent=2))
    if args.execute:
        with (run_dir/"gizmo.stdout.log").open("w") as log:
            p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        (run_dir/"exit_code.txt").write_text(str(p.returncode)+"\n")
        if p.returncode: raise SystemExit(p.returncode)

if __name__ == "__main__": main()
