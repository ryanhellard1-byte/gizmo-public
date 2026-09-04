#!/usr/bin/env python3
"""Render one frozen Phase-172 manifest row into a live GIZMO parameter file."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

TIME_UNIT_GYR = 0.9777923542981722
EXPECTED_ANALYSIS_TIMES_GYR = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 55.28, 80.0)
TIME_TOL_GYR = 1.0e-9


def parse_frozen_times(text):
    times=tuple(float(x.strip()) for x in str(text).split(",") if x.strip())
    exact=(len(times)==len(EXPECTED_ANALYSIS_TIMES_GYR) and
           all(abs(a-b)<=TIME_TOL_GYR for a,b in zip(times,EXPECTED_ANALYSIS_TIMES_GYR)))
    monotonic=all(b>a for a,b in zip(times,times[1:]))
    if not exact or not monotonic or abs(times[-1]-80.0)>TIME_TOL_GYR:
        raise SystemExit(f"manifest analysis-time contract violation: {times}")
    return times


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--row-index",type=int,required=True)
    ap.add_argument("--ic-root",required=True)
    ap.add_argument("--run-root",required=True)
    ap.add_argument("--max-mem-mb",type=int,default=3500)
    ap.add_argument("--time-limit-cpu",type=int,default=170000)
    args=ap.parse_args()

    with open(args.manifest,newline="") as fh:
        rows=list(csv.DictReader(fh))
    if args.row_index < 0 or args.row_index >= len(rows):
        raise SystemExit("row-index out of range")
    r=rows[args.row_index]
    times=parse_frozen_times(r["analysis_times_Gyr"])
    final_time_Gyr=times[-1]

    run=Path(args.run_root)/r["run_id"]
    run.mkdir(parents=True,exist_ok=False)

    n=int(r["N_total"]); seed=int(r["seed"]); ratio=float(r["ic_mass_ratio"])
    order=r["ic_order"]
    tag=f"M11_N{n}_seed{seed}_mr{ratio:g}_{order}"
    ic=Path(args.ic_root)/(tag+".dat")
    if not ic.exists():
        raise SystemExit(f"IC missing: {ic}")

    outlist=run/"output_times.txt"
    # Time=0 is represented by the IC; every positive preregistered time is an explicit snapshot target.
    outlist.write_text("\n".join(f"{t/TIME_UNIT_GYR:.17g}" for t in times if t>0)+"\n")

    eps=float(r["epsilon_kpc"])
    maxdt=float(r["max_dt_Gyr"])/TIME_UNIT_GYR
    mode=float(r["runtime_interaction_parameter"])
    final_code=final_time_Gyr/TIME_UNIT_GYR
    params=run/"params.txt"
    params.write_text(f"""% Phase172 frozen production run {r['run_id']}
InitCondFile                {ic.resolve()}
OutputDir                   {run.resolve()}/
ICFormat                    1
SnapFormat                  1
SnapshotFileBase            snapshot
RestartFile                 restart
OutputListOn                1
OutputListFilename          {outlist.resolve()}
NumFilesPerSnapshot         1
NumFilesWrittenInParallel   1
TimeLimitCPU                {args.time_limit_cpu}
CpuTimeBetRestartFile       7200
MaxMemSize                  {args.max_mem_mb}
PartAllocFactor             4.0
BufferSize                  64

TimeBegin                    0.0
TimeMax                      {final_code:.17g}
MaxSizeTimestep              {maxdt:.17g}
MinSizeTimestep              1.0e-12

UnitLength_in_cm             3.085678e21
UnitMass_in_g                1.989e33
UnitVelocity_in_cm_per_s     1.0e5
GravityConstantInternal      0

ComovingIntegrationOn        0
BoxSize                      2000.0
Omega_Matter                 0
Omega_Lambda                 0
Omega_Baryon                 0
HubbleParam                  1.0

AGS_DesNumNgb                {int(r['neighbors'])}
TreeRebuild_ActiveFraction   0.01
Softening_Type0              {eps:.17g}
Softening_Type1              {eps:.17g}
Softening_Type2              {eps:.17g}
Softening_Type3              {eps:.17g}
Softening_Type4              {eps:.17g}
Softening_Type5              {eps:.17g}

DM_InteractionCrossSection   {mode:.17g}
DM_InteractionVelocityScale  0
DM_DissipationFactor         0
DM_KickPerCollision          0
""")

    meta={
      "manifest_row":r,"row_index":args.row_index,"ic":str(ic.resolve()),
      "params":str(params.resolve()),"output_times":str(outlist.resolve()),
      "analysis_times_Gyr":list(times),"required_final_time_Gyr":final_time_Gyr,
      "time_unit_Gyr":TIME_UNIT_GYR,"TimeMax_code":final_code,
      "MaxSizeTimestep_code":maxdt
    }
    (run/"render_metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    main()
