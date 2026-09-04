#!/usr/bin/env python3
"""Phase187 complete evaluator for the seven fatal Phase165/166 claim gates.

Thresholds are unchanged. This phase only turns the preregistered verbal/data
contracts into deterministic evaluators before production outputs exist.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, struct, sys
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Dict, List, Mapping, Sequence, Tuple

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import phase174_batch_submit as p174  # noqa: E402
import phase181_profile_extract as p181_profile  # noqa: E402
import phase187_energy_machine as p187_energy  # noqa: E402

PHASE=187
EXPECTED_MANIFEST_SHA256=p174.EXPECTED_MANIFEST_SHA256
EXPECTED_TOTAL=p174.EXPECTED_TOTAL
CLAIM_TIME_GYR=10.0
INNER_R_OVER_RS=0.75
INNER_R_HI_OVER_RS=max(float(x) for x in p181_profile.EDGES_OVER_RS if float(x) <= INNER_R_OVER_RS)
ENERGY_HARD_MAX=0.01
ENERGY_MEDIAN_PREFERRED=0.003
MOMENTUM_DRIFT_MAX=1.0e-4
CDM_PROFILE_MEDIAN_DRIFT_MAX=0.03
SIDM2C_PROFILE_MEDIAN_ERROR_MAX=0.10
SEED_SIGMA_MIN=1.0
RHO_S0_CODE=6.89e6/1.0e10
R_S0_KPC=9.1
COLLAPSE_TIME_GYR=55.28
YANG_TAU_10GYR=CLAIM_TIME_GYR/COLLAPSE_TIME_GYR
CORE_GROUP="core_blind_production"
TIERS=("R2_double","R3_gold")

class ClaimGateError(RuntimeError):
    pass

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8*1024*1024),b""): h.update(block)
    return h.hexdigest()

def add(checks: List[Dict], gate: str, passed: bool, detail: Mapping, fatal: bool=True) -> bool:
    checks.append({"gate":gate,"passed":bool(passed),"fatal":bool(fatal),"detail":dict(detail)})
    return bool(passed) or not fatal

def sem(values: Sequence[float]) -> float:
    vals=[float(x) for x in values if math.isfinite(float(x))]
    if len(vals)<=1: return float("inf")
    mu=sum(vals)/len(vals)
    var=sum((x-mu)**2 for x in vals)/(len(vals)-1)
    return math.sqrt(var/len(vals))

def mean(values: Sequence[float]) -> float:
    if not values: raise ClaimGateError("mean of empty sequence")
    return sum(float(x) for x in values)/len(values)

def frozen_manifest(path: Path) -> List[Dict[str,str]]:
    raw=path.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_MANIFEST_SHA256:
        raise ClaimGateError(f"manifest SHA mismatch: {sha}")
    with path.open(newline="") as fh: rows=list(csv.DictReader(fh))
    if len(rows)!=EXPECTED_TOTAL or len({r["run_id"] for r in rows})!=EXPECTED_TOTAL:
        raise ClaimGateError(f"manifest cardinality/IDs invalid: {len(rows)}")
    return rows

def load_csv(path: Path) -> List[Dict[str,str]]:
    if not path.is_file(): raise ClaimGateError(f"missing CSV: {path}")
    with path.open(newline="") as fh: return list(csv.DictReader(fh))

def fnum(row: Mapping[str,str], key: str) -> float:
    try:
        x=float(row[key])
    except Exception as exc:
        raise ClaimGateError(f"invalid {key} in row {row.get('run_id')}: {row.get(key)!r}") from exc
    if not math.isfinite(x): raise ClaimGateError(f"non-finite {key} in {row.get('run_id')}")
    return x

# Corrected Read-profile parameterization from Yang et al public parametricSIDM
# parametricRead.py, frozen here before campaign outputs.
def yang_rhos(tr: float) -> float:
    v=(1.33465688+0.77459132*tr+8.04226046*tr**5-13.89112027*tr**7+
       10.17999859*tr**9-0.1448*(1-1.33465688)*math.log(tr+0.001))
    return v*RHO_S0_CODE

def yang_rs(tr: float) -> float:
    v=(0.87711888-0.23724033*tr+0.22164058*tr**2-0.38678443*tr**3-
       0.1448*(1-0.87711888)*math.log(tr+0.001))
    return v*R_S0_KPC

def yang_rc(tr: float) -> float:
    v=(3.32381804*math.sqrt(tr)-4.89672376*tr+3.36707187*tr**2-
       2.51208772*tr**3+0.86989356*tr**4)
    return v*R_S0_KPC

def yang_read_rho_code(r_kpc: float, tr: float=YANG_TAU_10GYR) -> float:
    if r_kpc<=0: raise ClaimGateError("Yang target radius must be positive")
    rhos,rs,rc=yang_rhos(tr),yang_rs(tr),yang_rc(tr)
    f=math.tanh(r_kpc/rc)
    rho_nfw=rhos*rs/r_kpc/(1+r_kpc/rs)**2
    mr=4*math.pi*rhos*rs**3*(-1+rs/(r_kpc+rs)-math.log(rs)+math.log(r_kpc+rs))
    return f*rho_nfw+(1-f*f)*mr/(4*math.pi*r_kpc*r_kpc*rc)

def validate_yang_regression() -> Dict:
    refs={0.03:2.73884,0.05:2.62793,0.10:2.36667,0.20:1.90564,
          0.30:1.51853,0.50:0.94179,1.0:0.29247,2.0:0.05665,
          3.0:0.02043,5.0:0.00532}
    errs={}
    for x,target in refs.items():
        got=yang_read_rho_code(x*R_S0_KPC)/RHO_S0_CODE
        errs[str(x)]=abs(got-target)
    worst=max(errs.values())
    if worst>5.0e-4:
        raise ClaimGateError(f"Yang Read regression drifted: max abs error={worst}")
    return {"max_abs_error":worst,"reference_points":len(refs),
            "tau_10Gyr":YANG_TAU_10GYR,
            "rho_s_ratio":yang_rhos(YANG_TAU_10GYR)/RHO_S0_CODE,
            "r_s_ratio":yang_rs(YANG_TAU_10GYR)/R_S0_KPC,
            "r_c_ratio":yang_rc(YANG_TAU_10GYR)/R_S0_KPC}

def snapshot_time_code(path: Path) -> float:
    with path.open("rb") as fh:
        b=fh.read(4)
        if len(b)!=4 or struct.unpack("<I",b)[0]!=256:
            raise ClaimGateError(f"{path}: not a GADGET format-1 snapshot")
        header=fh.read(256); end=fh.read(4)
        if len(header)!=256 or len(end)!=4 or struct.unpack("<I",end)[0]!=256:
            raise ClaimGateError(f"{path}: malformed GADGET header")
        return float(struct.unpack_from("<d",header,72)[0])

def source_states(run_dir: Path, ic: Path) -> List[Tuple[float,Path,int]]:
    out=[(0.0,ic,0)]
    found=[]
    for p in sorted(x for x in run_dir.glob("snapshot*") if x.is_file()):
        tg=snapshot_time_code(p)*p181_profile.TIME_UNIT_GYR
        found.append((tg,p))
    for req in p181_profile.EXPECTED_TIMES_GYR[1:]:
        hits=[(t,p) for t,p in found if abs(t-req)<=p181_profile.TIME_TOL_GYR]
        if len(hits)!=1: raise ClaimGateError(f"{run_dir.name}: snapshot {req} Gyr has {len(hits)} matches")
        out.append((req,hits[0][1],2))
    return out

def com_velocity(path: Path) -> Tuple[float,float,float]:
    s=p181_profile.read_gadget_format1(path)
    mt=float(s.mass.sum())
    if not math.isfinite(mt) or mt<=0: raise ClaimGateError(f"{path}: invalid total H/L mass")
    v=(s.vel*s.mass[:,None]).sum(axis=0)/mt
    vals=tuple(float(x) for x in v)
    if not all(math.isfinite(x) for x in vals): raise ClaimGateError(f"{path}: non-finite COM velocity")
    return vals

def collect_runtime_metrics(manifest_rows: List[Dict[str,str]], run_summary: List[Dict[str,str]],
                            run_root: Path, energy_attestation: Path, energy_executable: Path,
                            mpi_prefix: str, work_root: Path) -> Tuple[List[Dict],Dict]:
    p187_energy.load_attestation(energy_attestation,energy_executable)
    summary={r["run_id"]:r for r in run_summary}
    if set(summary)!={r["run_id"] for r in manifest_rows}:
        raise ClaimGateError("run_summary IDs do not exactly match manifest")
    metrics=[]; detail={}
    for mrow in manifest_rows:
        run_id=mrow["run_id"]; srow=summary[run_id]
        if srow.get("status")!="COMPLETE": raise ClaimGateError(f"{run_id}: not COMPLETE")
        run_dir=run_root/run_id
        post_path,post=p174.completion_record(run_dir)
        if post_path is None or post is None or post.get("status")!="COMPLETE":
            raise ClaimGateError(f"{run_id}: COMPLETE record missing")
        ic=Path(str(post.get("ic","")))
        params=run_dir/"params.txt"
        if not ic.is_file() or not params.is_file(): raise ClaimGateError(f"{run_id}: IC/params missing")
        if srow.get("ic_sha256") and sha256_file(ic)!=srow["ic_sha256"]:
            raise ClaimGateError(f"{run_id}: IC SHA mismatch during Phase187")
        states=source_states(run_dir,ic)
        base_v=None; max_p=0.0; energies=[]; samples=[]
        for idx,(tg,source,flag) in enumerate(states):
            vc=com_velocity(source)
            if base_v is None: base_v=vc
            dp=math.sqrt(sum((vc[k]-base_v[k])**2 for k in range(3)))
            max_p=max(max_p,dp)
            tc=snapshot_time_code(source) if flag==2 else 0.0
            probe_dir=work_root/run_id/f"{idx:02d}_{tg:g}Gyr"
            er=p187_energy.launch_probe(energy_executable,params,source,tc,flag,mpi_prefix,probe_dir)
            energies.append(float(er["energy_total"]))
            samples.append({"time_Gyr":tg,"source_sha256":er["source_sha256"],
                            "energy_total":er["energy_total"],"energy_potential":er["energy_potential"],
                            "com_velocity_code":list(vc)})
        e0=energies[0]
        if abs(e0)<=1e-300: raise ClaimGateError(f"{run_id}: zero initial total energy")
        drifts=[abs(e-e0)/abs(e0) for e in energies]
        max_e=max(drifts)
        row={"run_id":run_id,"energy_drift_abs_max":max_e,
             "momentum_drift_abs_max":max_p,"energy_samples":len(energies)}
        metrics.append(row)
        detail[run_id]={"energy_drift_abs_max":max_e,"momentum_drift_abs_max":max_p,"samples":samples}
    return metrics,detail

def index_profiles(profile_rows: List[Dict[str,str]]) -> Dict[Tuple[str,float,str],List[Dict[str,str]]]:
    idx=defaultdict(list)
    for r in profile_rows:
        try: t=float(r["time_Gyr"])
        except Exception as exc: raise ClaimGateError(f"invalid profile time: {r}") from exc
        idx[(r["run_id"],t,r["species"])].append(r)
    return idx

def exact_time_rows(idx, run_id: str, time_gyr: float, species: str) -> List[Dict[str,str]]:
    hits=[]
    for (rid,t,sp),rows in idx.items():
        if rid==run_id and sp==species and abs(t-time_gyr)<=1e-9: hits.extend(rows)
    if len(hits)!=p181_profile.N_BINS:
        raise ClaimGateError(f"{run_id} {time_gyr}Gyr {species}: {len(hits)} profile bins, expected {p181_profile.N_BINS}")
    return sorted(hits,key=lambda r:fnum(r,"r_hi_over_rs"))

def inner_change(idx, run_id: str, species: str) -> float:
    a=exact_time_rows(idx,run_id,0.0,species)
    b=exact_time_rows(idx,run_id,CLAIM_TIME_GYR,species)
    def choose(rows):
        hits=[r for r in rows if abs(fnum(r,"r_hi_over_rs")-INNER_R_HI_OVER_RS)<=1e-12]
        if len(hits)!=1: raise ClaimGateError(f"{run_id}: inner radius bin missing for {species}")
        m=fnum(hits[0],"mass_enclosed")
        if m<=0: raise ClaimGateError(f"{run_id}: nonpositive inner enclosed mass for {species}")
        return m
    m0,m1=choose(a),choose(b)
    return math.log(m1/m0)

def s_inner(idx, run_id: str) -> Tuple[float,float,float]:
    h=inner_change(idx,run_id,"H"); l=inner_change(idx,run_id,"L")
    return h-l,h,l

def validate(manifest_rows: List[Dict[str,str]], run_summary: List[Dict[str,str]],
             profile_rows: List[Dict[str,str]], runtime_metrics: List[Dict]) -> Tuple[bool,List[Dict],Dict]:
    checks=[]; ok=True
    yang=validate_yang_regression()
    mids={r["run_id"]:r for r in manifest_rows}
    runt={r["run_id"]:r for r in runtime_metrics}
    expected=set(mids)
    ok &= add(checks,"runtime_metric_coverage",set(runt)==expected,
              {"observed":len(runt),"expected":len(expected),"missing":sorted(expected-set(runt))[:10]})
    if set(runt)!=expected: return False,checks,{"yang_regression":yang}
    emax=max(float(r["energy_drift_abs_max"]) for r in runtime_metrics)
    emed=median(float(r["energy_drift_abs_max"]) for r in runtime_metrics)
    pmax=max(float(r["momentum_drift_abs_max"]) for r in runtime_metrics)
    ok &= add(checks,"energy_drift",emax<ENERGY_HARD_MAX,{"max":emax,"threshold":ENERGY_HARD_MAX})
    add(checks,"energy_drift_median_preferred",emed<ENERGY_MEDIAN_PREFERRED,
        {"median_per_run_max":emed,"preferred":ENERGY_MEDIAN_PREFERRED},fatal=False)
    ok &= add(checks,"momentum_drift",pmax<MOMENTUM_DRIFT_MAX,{"max":pmax,"threshold":MOMENTUM_DRIFT_MAX})

    idx=index_profiles(profile_rows)
    cdm=[r for r in manifest_rows if r["group"]==CORE_GROUP and r["branch"]=="CDM"]
    cdm_metrics={}
    for r in cdm:
        per=[]
        for t in p181_profile.EXPECTED_TIMES_GYR:
            if t<=0 or t>CLAIM_TIME_GYR: continue
            rows=exact_time_rows(idx,r["run_id"],t,"total")
            per.append((t,median(abs(fnum(x,"rho_rel")-1.0) for x in rows)))
        cdm_metrics[r["run_id"]]=max(v for _,v in per)
    cdm_max=max(cdm_metrics.values()) if cdm_metrics else float("inf")
    ok &= add(checks,"CDM_stability",len(cdm)==12 and cdm_max<CDM_PROFILE_MEDIAN_DRIFT_MAX,
              {"runs":len(cdm),"max_run_median_drift_through_10Gyr":cdm_max,
               "threshold":CDM_PROFILE_MEDIAN_DRIFT_MAX,"per_run":cdm_metrics})

    c2=[r for r in manifest_rows if r["group"]=="constant_SIDM2c_benchmark" and r["branch"]=="SIDM2c_const"]
    c2_metrics={}
    for r in c2:
        rows=exact_time_rows(idx,r["run_id"],CLAIM_TIME_GYR,"total")
        errs=[]
        for x in rows:
            target=yang_read_rho_code(fnum(x,"r_mid_over_rs")*R_S0_KPC)
            rho=fnum(x,"rho")
            if target<=0 or rho<=0: raise ClaimGateError(f"{r['run_id']}: invalid SIDM2c density")
            errs.append(abs(rho/target-1.0))
        c2_metrics[r["run_id"]]=median(errs)
    c2_max=max(c2_metrics.values()) if c2_metrics else float("inf")
    ok &= add(checks,"SIDM2c_total_profile_recovery",len(c2)==9 and c2_max<SIDM2C_PROFILE_MEDIAN_ERROR_MAX,
              {"runs":len(c2),"max_run_median_error":c2_max,
               "threshold":SIDM2C_PROFILE_MEDIAN_ERROR_MAX,"per_run":c2_metrics,
               "yang_regression":yang})

    core={}
    for r in manifest_rows:
        if r["group"]==CORE_GROUP and r["resolution_tier"] in TIERS:
            core[(r["resolution_tier"],int(r["seed"]),r["branch"])]=r["run_id"]
    causal_detail={}; causal_pass=True; mimic_detail={}; mimic_pass=True; seed_detail={}; seed_pass=True
    for tier in TIERS:
        seeds=sorted({seed for (tt,seed,b) in core if tt==tier and b=="CDM"})
        if len(seeds)!=4: raise ClaimGateError(f"{tier}: expected four core CDM seeds")
        sx_vals=[]; sx_h=[]; sx_l=[]; mimic_vals=[]
        branch_vals={"SIDMx":[],"SIDM2v":[]}
        for seed in seeds:
            need={b:core.get((tier,seed,b)) for b in ("CDM","SIDMx","HL_off","SIDM2v")}
            if any(v is None for v in need.values()): raise ClaimGateError(f"{tier} seed {seed}: incomplete core branch match")
            cS,cH,cL=s_inner(idx,need["CDM"])
            branch_delta={}
            for b in ("SIDMx","HL_off","SIDM2v"):
                S,H,L=s_inner(idx,need[b])
                branch_delta[b]=(S-cS,H-cH,L-cL)
            sx_vals.append(branch_delta["SIDMx"][0]); sx_h.append(branch_delta["SIDMx"][1]); sx_l.append(branch_delta["SIDMx"][2])
            mimic_vals.append(branch_delta["SIDMx"][0]-branch_delta["HL_off"][0])
            branch_vals["SIDMx"].append(branch_delta["SIDMx"][0])
            branch_vals["SIDM2v"].append(branch_delta["SIDM2v"][0])
        sx_mean=mean(sx_vals); sx_sem=sem(sx_vals); hmean=mean(sx_h); lmean=mean(sx_l)
        tpass=sx_mean>0 and hmean>0 and lmean<0 and sx_mean>SEED_SIGMA_MIN*sx_sem
        causal_pass &= tpass
        causal_detail[tier]={"deltaS_mean":sx_mean,"deltaS_sem":sx_sem,"H_branch_minus_CDM_mean":hmean,
                             "L_branch_minus_CDM_mean":lmean,"seeds":seeds,"passed":tpass}
        mm=mean(mimic_vals); ms=sem(mimic_vals); mpass=mm>SEED_SIGMA_MIN*ms
        mimic_pass &= mpass
        mimic_detail[tier]={"paired_SIDMx_minus_HLoff_mean":mm,"paired_sem":ms,"sigma_required":SEED_SIGMA_MIN,"passed":mpass}
        for b,vals in branch_vals.items():
            sep=abs(mean(vals)); scat=sem(vals); spass=sep>SEED_SIGMA_MIN*scat
            seed_pass &= spass
            seed_detail[f"{b}:{tier}"]={"branch_minus_CDM_abs_mean":sep,"seed_sem":scat,
                                        "sigma_required":SEED_SIGMA_MIN,"passed":spass}
    ok &= add(checks,"SIDMx_HL_causal_signal",causal_pass,
              {"inner_radius_requested_over_rs":INNER_R_OVER_RS,"inner_radius_grid_hi_over_rs":INNER_R_HI_OVER_RS,
               "definition":"S=log[(M_H(<r)/M_L(<r))_10Gyr/(M_H(<r)/M_L(<r))_0], then matched branch-minus-CDM",
               "tiers":causal_detail})
    ok &= add(checks,"HL_off_mimic_rejection",mimic_pass,
              {"definition":"matched-seed (SIDMx-CDM) minus (HL_off-CDM) must exceed its paired SEM at both R2 and R3",
               "tiers":mimic_detail})
    ok &= add(checks,"seed_stability",seed_pass,
              {"definition":"for promoted SIDMx and SIDM2v branch-minus-CDM S, abs(mean) > 1 SEM at R2 and R3",
               "comparisons":seed_detail})

    detail={"yang_regression":yang,"cdm":cdm_metrics,"sidm2c":c2_metrics,
            "causal":causal_detail,"mimic":mimic_detail,"seed":seed_detail}
    return bool(ok),checks,detail

def write_runtime_csv(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=["run_id","energy_drift_abs_max","momentum_drift_abs_max","energy_samples"]
    with path.open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:r[k] for k in fields})

def evaluate_campaign(manifest_path: Path, run_summary_path: Path, profiles_path: Path,
                      run_root: Path, energy_attestation: Path, energy_executable: Path,
                      mpi_prefix: str, work_root: Path, runtime_csv: Path) -> Dict:
    manifest=frozen_manifest(manifest_path)
    run_summary=load_csv(run_summary_path)
    profiles=load_csv(profiles_path)
    metrics,metric_detail=collect_runtime_metrics(manifest,run_summary,run_root,energy_attestation,
                                                  energy_executable,mpi_prefix,work_root)
    write_runtime_csv(runtime_csv,metrics)
    passed,checks,detail=validate(manifest,run_summary,profiles,metrics)
    return {"phase":PHASE,"status":"PASS" if passed else "FAIL","kind":"complete_preregistered_missing_gate_evaluator",
            "claim_epoch_Gyr":CLAIM_TIME_GYR,
            "thresholds":{"energy_drift_abs_max":ENERGY_HARD_MAX,"energy_drift_median_preferred":ENERGY_MEDIAN_PREFERRED,
                          "momentum_drift_abs_max":MOMENTUM_DRIFT_MAX,"cdm_profile_median_drift":CDM_PROFILE_MEDIAN_DRIFT_MAX,
                          "sidm2c_profile_median_error":SIDM2C_PROFILE_MEDIAN_ERROR_MAX,"seed_sigma_min":SEED_SIGMA_MIN},
            "checks":checks,"detail":detail,"runtime_metrics":metric_detail,
            "runtime_metrics_csv":str(runtime_csv.resolve()),"runtime_metrics_csv_sha256":sha256_file(runtime_csv),
            "energy_attestation_sha256":sha256_file(energy_attestation),
            "energy_executable_sha256":sha256_file(energy_executable),
            "claim_boundary":"PASS evaluates the seven previously missing preregistered fatal gates. It is not a claim about data until run on the completed frozen campaign."}

def parser() -> argparse.ArgumentParser:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True); ap.add_argument("--run-summary",required=True)
    ap.add_argument("--profiles",required=True); ap.add_argument("--run-root",required=True)
    ap.add_argument("--energy-attestation",required=True); ap.add_argument("--energy-executable",required=True)
    ap.add_argument("--energy-mpi-prefix",default=""); ap.add_argument("--work-root",required=True)
    ap.add_argument("--runtime-csv",required=True); ap.add_argument("--out-json",required=True)
    return ap

def main() -> int:
    args=parser().parse_args()
    try:
        report=evaluate_campaign(Path(args.manifest),Path(args.run_summary),Path(args.profiles),
                                 Path(args.run_root),Path(args.energy_attestation),Path(args.energy_executable),
                                 args.energy_mpi_prefix,Path(args.work_root),Path(args.runtime_csv))
        Path(args.out_json).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
        return 0 if report["status"]=="PASS" else 1
    except (ClaimGateError,p187_energy.EnergyGateError,p181_profile.ProfileError,OSError,ValueError,struct.error) as exc:
        print(json.dumps({"phase":PHASE,"status":"ERROR","error":str(exc)},indent=2),file=sys.stderr); return 2

if __name__=="__main__":
    raise SystemExit(main())
