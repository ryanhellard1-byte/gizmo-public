#!/usr/bin/env python3
"""Fail-closed Phase165 -> native GIZMO_D3 adapter.

The frozen Phase165 manifest is expressed in physical Gyr while GIZMO's
non-cosmological time coordinate is in code time units. With the frozen units
(1 kpc, 1 km/s, h=1), one code time unit is 0.9777923542981722 Gyr.

Default operation stages one manifest row and writes provenance without running
GIZMO. --execute generates/caches the IC and launches the exact pinned binary.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, shlex, subprocess, sys
from pathlib import Path

FROZEN_MANIFEST_SHA256 = "08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3"
SOFTWARE_PROOF_COMMIT = "a5e7b7e777bd211bf0f0b5c667a9957f476ef0ec"
COMMISSIONING_EXECUTABLE_SHA256 = "677a881fc0964012df39c4736180ce77fb8400ca494f1a6b2776110b6d560155"
UNIT_LENGTH_CM = 3.085678e21
UNIT_VELOCITY_CM_S = 1.0e5
SECONDS_PER_GYR = 365.25 * 86400.0 * 1.0e9
GYR_PER_CODE_TIME = (UNIT_LENGTH_CM / UNIT_VELOCITY_CM_S) / SECONDS_PER_GYR

MODE = {
    "CDM": -9, "SIDMx": -2, "HL_off": -3, "SIDM2v": -1,
    "HH_only": -4, "LL_only": -5, "HL_HH": -6, "HL_LL": -7,
    "SIDM2c_const": -8,
}

RESOLUTION = {
    "R0_pilot": (100_000, 100_000, 0.060),
    "R1_base": (300_000, 300_000, 0.040),
    "R2_double": (600_000, 600_000, 0.028),
    "R3_gold": (1_200_000, 1_200_000, 0.020),
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def as_float(row, key):
    try: return float(row[key])
    except Exception as e: raise SystemExit(f"missing/invalid {key}: {row.get(key)!r}") from e

def as_int(row, key):
    try: return int(float(row[key]))
    except Exception as e: raise SystemExit(f"missing/invalid {key}: {row.get(key)!r}") from e

def parse_times(text: str):
    try: vals=[float(x.strip()) for x in text.split(",") if x.strip()]
    except Exception as e: raise SystemExit(f"invalid analysis_times_Gyr: {text!r}") from e
    if not vals or vals[0] != 0.0 or vals != sorted(vals):
        raise SystemExit(f"analysis_times_Gyr must be sorted and start at 0: {vals}")
    return vals

def validate_row(row):
    run_id=row.get("run_id","").strip()
    branch=row.get("branch","").strip()
    tier=row.get("resolution_tier","").strip()
    if not run_id: raise SystemExit("missing run_id")
    if branch not in MODE: raise SystemExit(f"{run_id}: unsupported branch {branch!r}")
    if tier not in RESOLUTION: raise SystemExit(f"{run_id}: unsupported resolution_tier {tier!r}")
    nh,nl,eps=RESOLUTION[tier]
    if as_int(row,"N_H") != nh or as_int(row,"N_L") != nl:
        raise SystemExit(f"{run_id}: N_H/N_L disagree with frozen {tier} contract")
    if as_int(row,"N_total") != nh+nl:
        raise SystemExit(f"{run_id}: N_total mismatch")
    if abs(as_float(row,"particle_mass_ratio_H_over_L")-3.0) > 1e-12:
        raise SystemExit(f"{run_id}: mass ratio is not 3")
    if abs(as_float(row,"epsilon_kpc")-eps) > 1e-12:
        raise SystemExit(f"{run_id}: epsilon disagrees with frozen {tier} contract")
    seed=as_int(row,"seed")
    neighbors=as_int(row,"neighbors")
    max_dt_gyr=as_float(row,"max_dt_Gyr")
    times_gyr=parse_times(row.get("analysis_times_Gyr",""))
    if max(times_gyr) < 10.0:
        raise SystemExit(f"{run_id}: does not reach 10 Gyr")
    return {
        "run_id":run_id,"group":row.get("group",""),"branch":branch,"d3_mode":MODE[branch],
        "resolution_tier":tier,"N_H":nh,"N_L":nl,"N_total":nh+nl,"epsilon_kpc":eps,
        "seed":seed,"neighbors":neighbors,"max_dt_Gyr":max_dt_gyr,
        "max_dt_code":max_dt_gyr/GYR_PER_CODE_TIME,
        "analysis_times_Gyr":times_gyr,
        "analysis_times_code":[t/GYR_PER_CODE_TIME for t in times_gyr],
        "TimeMax_code":max(times_gyr)/GYR_PER_CODE_TIME,
        "blind_analysis":row.get("blind_analysis","").strip().lower()=="true",
    }

def render_params(ic: Path, out: Path, output_list: Path, spec):
    e=spec["epsilon_kpc"]
    return f"""% Phase165 native GIZMO_D3 parameters. Generated from frozen manifest.\nInitCondFile {ic.resolve()}\nOutputDir {out.resolve()}/\nICFormat 1\nSnapFormat 1\nSnapshotFileBase snapshot\nRestartFile restart\nOutputListOn 1\nOutputListFilename {output_list.resolve()}\nNumFilesPerSnapshot 1\nNumFilesWrittenInParallel 1\nTimeLimitCPU 259200\nCpuTimeBetRestartFile 3600\nMaxMemSize 120000\nPartAllocFactor 4.0\nBufferSize 256\nTimeBegin 0.0\nTimeMax {spec['TimeMax_code']:.17g}\nMaxSizeTimestep {spec['max_dt_code']:.17g}\nMinSizeTimestep 1.0e-12\nUnitLength_in_cm {UNIT_LENGTH_CM:.17g}\nUnitMass_in_g 1.989e33\nUnitVelocity_in_cm_per_s {UNIT_VELOCITY_CM_S:.17g}\nGravityConstantInternal 0\nComovingIntegrationOn 0\nBoxSize 2000.0\nOmega_Matter 0\nOmega_Lambda 0\nOmega_Baryon 0\nHubbleParam 1.0\nAGS_DesNumNgb {spec['neighbors']}\nTreeRebuild_ActiveFraction 0.01\nSoftening_Type0 {e:.17g}\nSoftening_Type1 {e:.17g}\nSoftening_Type2 {e:.17g}\nSoftening_Type3 {e:.17g}\nSoftening_Type4 {e:.17g}\nSoftening_Type5 {e:.17g}\nDM_InteractionCrossSection {spec['d3_mode']}\nDM_InteractionVelocityScale 0\nDM_DissipationFactor 0\nDM_KickPerCollision 0\n"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("run_id")
    ap.add_argument("--executable",type=Path,required=True)
    ap.add_argument("--expected-executable-sha",default=COMMISSIONING_EXECUTABLE_SHA256)
    ap.add_argument("--work-root",type=Path,default=Path("phase165_runs"))
    ap.add_argument("--generator",type=Path,default=Path(__file__).with_name("phase141_generate_m11_ic.py"))
    ap.add_argument("--mpiexec",default="mpirun -np 4")
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    manifest_sha=sha256(args.manifest)
    if manifest_sha != FROZEN_MANIFEST_SHA256:
        raise SystemExit(f"FATAL manifest SHA mismatch: {manifest_sha}")
    exe_sha=sha256(args.executable)
    if exe_sha != args.expected_executable_sha:
        raise SystemExit(f"FATAL executable SHA mismatch: {exe_sha}")

    rows=list(csv.DictReader(args.manifest.open(newline="")))
    row=next((r for r in rows if r.get("run_id","").strip()==args.run_id),None)
    if row is None: raise SystemExit(f"run_id not found: {args.run_id}")
    spec=validate_row(row)

    run_dir=args.work_root/spec["run_id"]
    run_dir.mkdir(parents=True,exist_ok=True)
    ic_dir=args.work_root/"ic_cache"; ic_dir.mkdir(parents=True,exist_ok=True)
    ic=ic_dir/f"M11_{spec['resolution_tier']}_seed{spec['seed']}_taper0.05.dat"
    meta=Path(str(ic)+".json")
    output_list=run_dir/"output_times_code.txt"
    output_list.write_text("\n".join(f"{t:.17g}" for t in spec["analysis_times_code"])+"\n")
    params=run_dir/"params.txt"
    params.write_text(render_params(ic,run_dir,output_list,spec))
    gen=[sys.executable,str(args.generator),"--n-total",str(spec["N_total"]),"--seed",str(spec["seed"]),"--taper","0.05","--output",str(ic),"--metadata",str(meta)]
    cmd=shlex.split(args.mpiexec)+[str(args.executable.resolve()),str(params.resolve())]

    provenance={**spec,
        "manifest_sha256":manifest_sha,"software_proof_commit":SOFTWARE_PROOF_COMMIT,
        "executable_sha256":exe_sha,"expected_executable_sha256":args.expected_executable_sha,
        "GYR_PER_CODE_TIME":GYR_PER_CODE_TIME,"params_sha256":sha256(params),
        "output_list_sha256":sha256(output_list),"ic_path":str(ic),
        "ic_sha256":sha256(ic) if ic.exists() else None,"generator_command":gen,
        "launch_command":cmd,"executed":bool(args.execute)}
    (run_dir/"prelaunch_provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps(provenance,indent=2))

    if args.execute:
        if not ic.exists(): subprocess.run(gen,check=True)
        provenance["ic_sha256"]=sha256(ic)
        (run_dir/"prelaunch_provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        with (run_dir/"gizmo.stdout.log").open("w") as log:
            p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        (run_dir/"exit_code.txt").write_text(str(p.returncode)+"\n")
        if p.returncode: raise SystemExit(p.returncode)

if __name__=="__main__": main()
