#!/usr/bin/env python3
import argparse, csv, json, math, struct
from pathlib import Path
import numpy as np


def rec(f):
    n=struct.unpack('<I',f.read(4))[0]
    b=f.read(n)
    n2=struct.unpack('<I',f.read(4))[0]
    if n!=n2: raise RuntimeError('record marker mismatch')
    return b

def read_gadget1(path):
    with open(path,'rb') as f:
        h=rec(f)
        npart=np.array(struct.unpack_from('<6I',h,0),dtype=int)
        mass_table=np.array(struct.unpack_from('<6d',h,24),dtype=float)
        n=int(npart.sum())
        pos=np.frombuffer(rec(f),dtype='<f4').reshape(n,3).astype(float)
        vel=np.frombuffer(rec(f),dtype='<f4').reshape(n,3).astype(float)
        ids=np.frombuffer(rec(f),dtype='<u4').astype(np.uint64)
        types=np.concatenate([np.full(npart[t],t,dtype=np.int8) for t in range(6)])
        need_mass=sum(npart[t] for t in range(6) if npart[t] and mass_table[t]==0)
        masses=np.empty(n,float); off=0
        mass_block=None
        if need_mass:
            mass_block=np.frombuffer(rec(f),dtype='<f4').astype(float)
        im=0
        for t in range(6):
            nt=npart[t]
            if not nt: continue
            if mass_table[t]>0: masses[off:off+nt]=mass_table[t]
            else:
                masses[off:off+nt]=mass_block[im:im+nt]; im+=nt
            off+=nt
    return {'npart':npart,'pos':pos,'vel':vel,'ids':ids,'type':types,'mass':masses}

def center(x,m): return np.sum(x*m[:,None],axis=0)/np.sum(m)
def weighted_q(r,m,q):
    o=np.argsort(r); rr=r[o]; mm=m[o]; c=np.cumsum(mm)
    return float(rr[np.searchsorted(c,q*c[-1],side='left')])
def stats(d):
    m=d['mass']; p=d['pos']; v=d['vel']; typ=d['type']
    c=center(p,m); vc=center(v,m); r=np.linalg.norm(p-c,axis=1)
    out={'N':int(len(m)),'mass':float(m.sum()),'com':c.tolist(),'vcom':vc.tolist(),
         'r10':weighted_q(r,m,.1),'r50':weighted_q(r,m,.5),'r90':weighted_q(r,m,.9)}
    for t,name in [(1,'H'),(2,'L')]:
        z=typ==t; mt=m[z]; pt=p[z]; vt=v[z]; rt=np.linalg.norm(pt-c,axis=1)
        dv=vt-center(vt,mt)
        out[name]={'N':int(z.sum()),'mass':float(mt.sum()),'com':center(pt,mt).tolist(),
                   'r10':weighted_q(rt,mt,.1),'r50':weighted_q(rt,mt,.5),'r90':weighted_q(rt,mt,.9),
                   'sigma1D':float(np.sqrt(np.mean(np.sum(dv*dv,axis=1))/3.0))}
    return out

def energy_drift(path):
    p=Path(path)
    if not p.exists(): return {'available':False}
    rows=[]
    for line in p.read_text(errors='ignore').splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        try: a=[float(x) for x in line.split()]
        except: continue
        if len(a)>=5: rows.append(a)
    if len(rows)<2: return {'available':False,'rows':len(rows)}
    # Standard GADGET/GIZMO energy.txt: time, Eint, Epot, Ekin, Etot, ...
    e0,e1=rows[0][4],rows[-1][4]
    den=max(abs(e0),1e-300)
    return {'available':True,'rows':len(rows),'time0':rows[0][0],'time1':rows[-1][0],
            'Etot0':e0,'Etot1':e1,'relative_drift':abs(e1-e0)/den,
            'first_row':rows[0][:10],'last_row':rows[-1][:10]}

def audit(paths):
    out={c:{'pair_trials':0,'sum_probability':0.0,'accepted_collisions':0,'prob_gt_0p2':0} for c in ('HH','LL','HL')}
    for path in paths:
        for r in csv.DictReader(open(path),delimiter='\t'):
            if r['channel'] not in out: continue
            z=out[r['channel']]
            for k in ('pair_trials','accepted_collisions','prob_gt_0p2'): z[k]+=int(r[k])
            z['sum_probability']+=float(r['sum_probability'])
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--initial',required=True); ap.add_argument('--final',required=True)
    ap.add_argument('--energy',required=True); ap.add_argument('--audit',nargs='*',default=[])
    ap.add_argument('--output',required=True); ap.add_argument('--label',default='M11')
    ap.add_argument('--max-mass-rel',type=float,default=1e-6)
    ap.add_argument('--max-com-kpc',type=float,default=5.0)
    ap.add_argument('--r50-min-ratio',type=float,default=0.25); ap.add_argument('--r50-max-ratio',type=float,default=4.0)
    ap.add_argument('--r90-min-ratio',type=float,default=0.5); ap.add_argument('--r90-max-ratio',type=float,default=2.0)
    ap.add_argument('--max-energy-drift',type=float,default=0.05)
    args=ap.parse_args()
    a=stats(read_gadget1(args.initial)); b=stats(read_gadget1(args.final))
    ed=energy_drift(args.energy); au=audit(args.audit)
    mass_rel=abs(b['mass']/a['mass']-1.0)
    com_shift=float(np.linalg.norm(np.array(b['com'])-np.array(a['com'])))
    r50=b['r50']/a['r50']; r90=b['r90']/a['r90']
    checks={
      'particle_count':b['N']==a['N'],
      'species_counts':b['H']['N']==a['H']['N'] and b['L']['N']==a['L']['N'],
      'mass_conservation':mass_rel<=args.max_mass_rel,
      'center_drift':com_shift<=args.max_com_kpc,
      'r50_sane':args.r50_min_ratio<=r50<=args.r50_max_ratio,
      'r90_sane':args.r90_min_ratio<=r90<=args.r90_max_ratio,
      'rare_scatter':sum(x['prob_gt_0p2'] for x in au.values())==0,
      'energy_drift':(not ed['available']) or ed['relative_drift']<=args.max_energy_drift,
    }
    res={'label':args.label,'initial':a,'final':b,'mass_relative_change':mass_rel,'com_shift_kpc':com_shift,
         'r50_ratio':r50,'r90_ratio':r90,'energy':ed,'audit':au,'checks':checks,
         'status':'PASS' if all(checks.values()) else 'FAIL'}
    Path(args.output).write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps(res,indent=2))
    raise SystemExit(0 if res['status']=='PASS' else 1)
if __name__=='__main__': main()
