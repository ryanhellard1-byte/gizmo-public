#!/usr/bin/env python3
"""Validate live GIZMO HL homogeneous-box rates and MPI invariance."""
import argparse, glob, json, math
from pathlib import Path

KPC_CM=3.0856775814913673e21
KM_S_CM_S=1.0e5
SIGMA0_HL=1.125
W_HL=2200.0

def read_audit(path):
    lines=[x.strip() for x in Path(path).read_text().splitlines() if x.strip()]
    header=lines[0].lstrip('#').split()
    rows=[]
    for line in lines[1:]:
        vals=line.split()
        if len(vals)!=len(header):
            continue
        rows.append(dict(zip(header,[float(x) for x in vals])))
    if not rows: raise RuntimeError(f'no data rows in {path}')
    return rows

def run_summary(outdir, meta_path):
    rows=read_audit(Path(outdir)/'sidm_d3_audit.log')
    meta=json.loads(Path(meta_path).read_text())
    events=sum(r['HL'] for r in rows)
    hh=sum(r['HH'] for r in rows); ll=sum(r['LL'] for r in rows)
    p02=sum(r['p02_HL'] for r in rows); p1=sum(r['p1_HL'] for r in rows)
    t=max(r['time'] for r in rows)
    rho=meta['rho_H_g_cm3']; v=meta['v_L_km_s'][0]
    sigma=SIGMA0_HL/(1.0+(v/W_HL)**2)
    expected=meta['n_L']*rho*sigma*(v*KM_S_CM_S)*(t*KPC_CM/KM_S_CM_S)
    max_mom=max(r['max_mom_res'] for r in rows)
    max_energy=max(r['max_energy_res'] for r in rows)
    return {'events_HL':events,'events_HH':hh,'events_LL':ll,'expected_HL':expected,
            'rate_ratio':events/expected if expected else math.nan,'final_time_code':t,
            'p02_HL':p02,'p1_HL':p1,'max_momentum_residual':max_mom,
            'max_energy_residual':max_energy}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base',default='phase178_live_box')
    ap.add_argument('--seeds',nargs='+',type=int,required=True)
    ap.add_argument('--output',default='phase178_live_box/validation.json')
    a=ap.parse_args(); base=Path(a.base)
    allm={}; gates={}
    for mode in ('np1','np2'):
        runs=[]
        for seed in a.seeds:
            out=base/mode/f'seed{seed}'
            meta=base/'ic'/f'box_seed{seed}.dat.json'
            runs.append(run_summary(out,meta))
        ev=sum(r['events_HL'] for r in runs); ex=sum(r['expected_HL'] for r in runs)
        agg={'events_HL':ev,'expected_HL':ex,'rate_ratio':ev/ex,
             'events_HH':sum(r['events_HH'] for r in runs),'events_LL':sum(r['events_LL'] for r in runs),
             'p02_HL':sum(r['p02_HL'] for r in runs),'p1_HL':sum(r['p1_HL'] for r in runs),
             'max_momentum_residual':max(r['max_momentum_residual'] for r in runs),
             'max_energy_residual':max(r['max_energy_residual'] for r in runs),'runs':runs}
        allm[mode]=agg
        gates[f'{mode}_HL_rate_within_8pct']=abs(agg['rate_ratio']-1.0)<=0.08
        gates[f'{mode}_HH_disabled_zero']=agg['events_HH']==0
        gates[f'{mode}_LL_disabled_zero']=agg['events_LL']==0
        gates[f'{mode}_no_p_ge_1']=agg['p1_HL']==0
        gates[f'{mode}_no_p_gt_0p2']=agg['p02_HL']==0
        gates[f'{mode}_momentum_residual_lt_1e-12']=agg['max_momentum_residual']<1e-12
        gates[f'{mode}_energy_residual_lt_1e-12']=agg['max_energy_residual']<1e-12
    mpi_ratio=allm['np2']['rate_ratio']/allm['np1']['rate_ratio']
    gates['mpi_rate_ratio_within_8pct']=abs(mpi_ratio-1.0)<=0.08
    gates['nonzero_live_events']=allm['np1']['events_HL']>0 and allm['np2']['events_HL']>0
    status='PASS' if all(gates.values()) else 'FAIL'
    result={'phase':178,'test':'live GIZMO H/L homogeneous-box HL commissioning','status':status,
            'frozen_law':{'sigma0_HL_over_mH_cm2_g':SIGMA0_HL,'w_HL_km_s':W_HL},
            'modes':allm,'mpi_rate_ratio_np2_over_np1':mpi_ratio,'gates':gates}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2)); raise SystemExit(0 if status=='PASS' else 1)
if __name__=='__main__': main()
