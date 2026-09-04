#!/usr/bin/env python3
"""Phase172 blind physics gate validator. Run after phase172_time_contract.py.
Synthetic/mock data validate this program only, never the physics.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np,pandas as pd
SHA='e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d'
TH={'energy':.01,'energy_med':.003,'momentum':1e-4,'pair':1e-12,'clip':.005,'cdm':.03,'c2':.10,'clock':.15,'res':.10,'dt':.05,'ngb':.07,'sigma':1.0}
RUN={'run_id','branch','group','resolution_tier','seed','status','executable_sha256','analysis_sha256','output_sha256','final_time_Gyr','energy_drift_abs_max','momentum_drift_abs_max','max_pair_dP_over_P','max_pair_dK_over_K','prob_clip_fraction_max','particle_loss_untracked','cdm_profile_median_drift_10Gyr','sidm2c_profile_median_error_10Gyr','sidm2c_collapse_clock_error_frac','S_inner_10Gyr','O_overlap_10Gyr','H_in_L_out_score','notes'}
PRO={'run_id','time_Gyr','r_mid_over_rs','species','rho'}
COL={'run_id','channel','collision_count','max_pair_dP_over_P','max_pair_dK_over_K','prob_clip_fraction_max'}
FORB={-9:{'HH','LL','HL'},-7:{'HH'},-6:{'LL'},-5:{'HH','HL'},-4:{'LL','HL'},-3:{'HL'},-2:{'HH','LL'},-1:set(),-8:set()}
def A(C,n,p,d,f=True): C.append({'gate':n,'passed':bool(p),'fatal':f,'detail':d}); return bool(p) or not f
def sem(x):
 x=pd.to_numeric(pd.Series(x),errors='coerce').dropna(); return float('inf') if len(x)<2 else float(x.std(ddof=1)/math.sqrt(len(x)))
def prof(P,ids):
 q=P[P.run_id.astype(str).isin(set(map(str,ids)))].copy(); q=q[np.isclose(pd.to_numeric(q.time_Gyr),10,atol=1e-6,rtol=0)]; q=q[q.species.astype(str).str.upper().isin(['H','L'])]; r=pd.to_numeric(q.r_mid_over_rs,errors='coerce'); q=q[(r>=.03)&(r<=3)].copy(); q['r']=pd.to_numeric(q.r_mid_over_rs).round(12); q['sp']=q.species.astype(str).str.upper(); q['rho']=pd.to_numeric(q.rho,errors='coerce')
 if q.empty or (q.groupby([q.run_id.astype(str),'sp','r']).size()!=1).any(): return None
 return q.groupby(['sp','r'],as_index=False).rho.mean()
def delta(P,test,base):
 a,b=prof(P,test),prof(P,base)
 if a is None or b is None:return float('inf')
 m=a.merge(b,on=['sp','r'],suffixes=('_a','_b'),how='outer',indicator=True)
 if not (m._merge=='both').all() or (m.rho_b<=0).any(): return float('inf')
 return float(np.max(np.abs(m.rho_a-m.rho_b)/np.abs(m.rho_b)))
def paired(P,M,test,base_seed):
 v=[]
 for rid in test:
  s=int(M.loc[M.run_id.astype(str)==str(rid),'seed'].iloc[0]); b=base_seed.get(s)
  if b is None:return float('inf')
  v.append(delta(P,[rid],[b]))
 return max(v) if v else float('inf')
def ids(M,g=None,b=None,r=None,t=None,k=None):
 q=M
 for col,val in [('group',g),('branch',b),('resolution_tier',r),('timestep_control',t),('kernel_control',k)]:
  if val is not None:q=q[q[col]==val]
 return list(q.run_id.astype(str))
def validate(mp,rp,pp,cp):
 C=[];ok=True; mp=Path(mp); M=pd.read_csv(mp);R=pd.read_csv(rp);P=pd.read_csv(pp);X=pd.read_csv(cp)
 obs=hashlib.sha256(mp.read_bytes()).hexdigest();ok&=A(C,'manifest_sha256_frozen',obs==SHA,{'observed':obs,'expected':SHA})
 for n,D,req in [('run_summary',R,RUN),('profiles',P,PRO),('collision_summary',X,COL)]:
  miss=sorted(req-set(D.columns));ok&=A(C,n+'_schema',not miss,{'missing':miss})
 if not RUN<=set(R.columns) or not PRO<=set(P.columns) or not COL<=set(X.columns):return False,C
 mid=set(M.run_id.astype(str)); rid=set(R.run_id.astype(str));ok&=A(C,'exact_manifest_run_ids',mid==rid and R.run_id.nunique()==len(R),{'missing':sorted(mid-rid)[:10],'extra':sorted(rid-mid)[:10]})
 J=M.merge(R,on='run_id',suffixes=('_m','_r')); bad=[]
 for c in ['branch','group','resolution_tier','seed']:
  if (J[c+'_m'].astype(str)!=J[c+'_r'].astype(str)).any():bad.append(c)
 ok&=A(C,'manifest_metadata_matches_outputs',not bad,{'mismatch_columns':bad})
 ft=pd.to_numeric(R.final_time_Gyr,errors='coerce');ok&=A(C,'all_runs_complete_and_80Gyr',R.status.astype(str).str.upper().eq('COMPLETE').all() and ft.notna().all() and ft.min()>=80-1e-6,{'min_final_Gyr':float(ft.min()) if ft.notna().any() else None})
 for c in ['energy_drift_abs_max','momentum_drift_abs_max','max_pair_dP_over_P','max_pair_dK_over_K','prob_clip_fraction_max','particle_loss_untracked']:R[c]=pd.to_numeric(R[c],errors='coerce')
 for n,c,z in [('energy_drift','energy_drift_abs_max',TH['energy']),('momentum_drift','momentum_drift_abs_max',TH['momentum']),('pair_dP','max_pair_dP_over_P',TH['pair']),('pair_dK','max_pair_dK_over_K',TH['pair']),('probability_clip','prob_clip_fraction_max',TH['clip'])]:ok&=A(C,n,R[c].notna().all() and R[c].max()<z,{'max':float(R[c].max()),'threshold':z})
 A(C,'energy_median_preferred',R.energy_drift_abs_max.median()<TH['energy_med'],{'median':float(R.energy_drift_abs_max.median()),'preferred':TH['energy_med']},False)
 ok&=A(C,'particle_loss',R.particle_loss_untracked.notna().all() and R.particle_loss_untracked.max()<=0,{'max':float(R.particle_loss_untracked.max())})
 X['rid']=X.run_id.astype(str);X['ch']=X.channel.astype(str).str.upper();X['n']=pd.to_numeric(X.collision_count,errors='coerce'); pairs=set(zip(X.rid,X.ch)); exp={(r,c) for r in mid for c in ['HH','LL','HL']}
 ok&=A(C,'collision_HH_LL_HL_complete',pairs==exp and not X.duplicated(['rid','ch']).any(),{'missing':list(sorted(exp-pairs))[:10],'extra':list(sorted(pairs-exp))[:10]})
 for n,c,z in [('collision_pair_dP','max_pair_dP_over_P',TH['pair']),('collision_pair_dK','max_pair_dK_over_K',TH['pair']),('collision_clip','prob_clip_fraction_max',TH['clip'])]:
  v=pd.to_numeric(X[c],errors='coerce');v=v.where(~((X.n==0)&v.isna()),0);ok&=A(C,n,v.notna().all() and v.max()<z,{'max':float(v.max()),'threshold':z})
 MI=M.set_index(M.run_id.astype(str));bad=[]
 for _,x in X.iterrows():
  m=MI.loc[x.rid];mode=float(m.runtime_interaction_parameter); forb={'HH','LL','HL'} if m.branch=='CDM' and mode==0 else FORB.get(int(mode),set()) if mode<0 and mode.is_integer() else set()
  if x.ch in forb and float(x.n)!=0:bad.append((x.rid,x.ch,float(x.n)))
 ok&=A(C,'forbidden_channels_zero',not bad,{'bad':bad[:10]})
 cdm=pd.to_numeric(R[R.branch=='CDM'].cdm_profile_median_drift_10Gyr,errors='coerce').dropna();ok&=A(C,'CDM_profile_stability',len(cdm)>0 and cdm.max()<TH['cdm'],{'max':float(cdm.max()) if len(cdm) else None,'threshold':TH['cdm']})
 c2=R[R.branch=='SIDM2c_const'];v=pd.to_numeric(c2.sidm2c_profile_median_error_10Gyr,errors='coerce').dropna();ok&=A(C,'SIDM2c_profile_recovery',len(v)>0 and v.max()<TH['c2'],{'max':float(v.max()) if len(v) else None,'threshold':TH['c2']});v=pd.to_numeric(c2.sidm2c_collapse_clock_error_frac,errors='coerce').dropna();A(C,'SIDM2c_clock_preferred',len(v)>0 and v.max()<TH['clock'],{'max':float(v.max()) if len(v) else None,'preferred':TH['clock']},False)
 Q=J[J.group_m=='core_blind_production'].copy();Q['S_inner_10Gyr']=pd.to_numeric(Q.S_inner_10Gyr,errors='coerce');Q['H_in_L_out_score']=pd.to_numeric(Q.H_in_L_out_score,errors='coerce');sx=Q[(Q.branch_m=='SIDMx')&Q.resolution_tier_m.isin(['R2_double','R3_gold'])];hl=Q[(Q.branch_m=='HL_off')&Q.resolution_tier_m.isin(['R2_double','R3_gold'])];cd=Q[(Q.branch_m=='CDM')&Q.resolution_tier_m.isin(['R2_double','R3_gold'])]
 sm=float(sx.S_inner_10Gyr.mean()) if len(sx) else float('nan');ok&=A(C,'SIDMx_positive_Hin_Lout',len(sx)>=8 and sm>0 and sx.H_in_L_out_score.mean()>0,{'count':len(sx),'S_mean':sm,'direction':float(sx.H_in_L_out_score.mean()) if len(sx) else None});ok&=A(C,'SIDMx_beats_seed_noise',len(sx)>1 and abs(sm)>sem(sx.S_inner_10Gyr),{'mean':sm,'sem':sem(sx.S_inner_10Gyr) if len(sx) else None});sep=sm-float(hl.S_inner_10Gyr.mean()) if len(hl) else float('nan');ok&=A(C,'HL_off_mimic_rejection',math.isfinite(sep) and sep>0,{'separation':sep});den=math.sqrt(sem(sx.S_inner_10Gyr)**2+sem(cd.S_inner_10Gyr)**2) if len(cd) else float('inf');z=abs(sm-float(cd.S_inner_10Gyr.mean()))/den if den>0 and math.isfinite(den) else float('inf');ok&=A(C,'SIDMx_branch_separation_1sigma',z>=1,{'sigma':z})
 r2=ids(M,'core_blind_production','SIDM2v','R2_double','T_base','K_base');r3=ids(M,'core_blind_production','SIDM2v','R3_gold','T_base','K_base');d=delta(P,r3,r2);ok&=A(C,'SIDM2v_R2_R3_profile_convergence',d<TH['res'],{'max_relative_delta':d,'threshold':TH['res']});base={int(x.seed):str(x.run_id) for _,x in M[M.run_id.astype(str).isin(r2)].iterrows()};h=ids(M,'half_timestep_convergence','SIDM2v','R2_double','T_half','K_base');d=paired(P,M,h,base);ok&=A(C,'SIDM2v_half_timestep_profile_convergence',d<TH['dt'],{'max_relative_delta':d,'threshold':TH['dt']})
 for k in ['K_low','K_high']:
  d=paired(P,M,ids(M,'neighbor_kernel_convergence','SIDM2v','R2_double','T_base',k),base);ok&=A(C,'SIDM2v_'+k+'_profile_convergence',d<TH['ngb'],{'max_relative_delta':d,'threshold':TH['ngb']})
 def env(baseids):return max(delta(P,[r],baseids) for r in baseids)
 cids=ids(M,'core_blind_production','CDM','R2_double','T_base','K_base');cb={int(x.seed):str(x.run_id) for _,x in M[M.run_id.astype(str).isin(cids)].iterrows()};e=env(cids);d=paired(P,M,ids(M,'zero_cross_section_null'),cb);ok&=A(C,'zero_cross_reproduces_CDM_within_seed_noise',d<=e,{'delta':d,'envelope':e});e=env(r2);d=paired(P,M,ids(M,'permutation_reproducibility'),base);ok&=A(C,'particle_order_reproducibility_within_seed_noise',d<=e,{'delta':d,'envelope':e})
 iq=P[P.run_id.astype(str).isin(ids(M,'identical_label_null'))].copy();iq=iq[np.isclose(pd.to_numeric(iq.time_Gyr),10,atol=1e-6,rtol=0)];rr=pd.to_numeric(iq.r_mid_over_rs,errors='coerce');iq=iq[(rr>=.03)&(rr<=3)&iq.species.astype(str).str.upper().isin(['H','L'])].copy();iq['r']=pd.to_numeric(iq.r_mid_over_rs).round(12);iq['sp']=iq.species.astype(str).str.upper();pv=iq.pivot_table(index=['run_id','r'],columns='sp',values='rho',aggfunc='first').dropna();fr=(pv.H-pv.L)/((pv.H+pv.L)/2) if len(pv) else pd.Series(dtype=float);se=sem(fr);ident=len(fr)>1 and math.isfinite(se) and abs(float(fr.mean()))<=2*se;ok&=A(C,'identical_label_H_L_statistical_null',ident,{'mean_fractional_H_minus_L':float(fr.mean()) if len(fr) else None,'sem':se,'two_sigma':2*se if math.isfinite(se) else None})
 for c,n in [('executable_sha256','executable_fingerprint'),('analysis_sha256','analysis_fingerprint'),('output_sha256','output_fingerprint')]:
  g=R[c].astype(str).str.fullmatch(r'[0-9a-fA-F]{64}').fillna(False);ok&=A(C,n,g.all(),{'invalid':int((~g).sum()),'unique':int(R[c].nunique())})
 return ok,C
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--run-summary',required=True);p.add_argument('--profiles',required=True);p.add_argument('--collision-summary',required=True);p.add_argument('--out-json');a=p.parse_args();ok,c=validate(a.manifest,a.run_summary,a.profiles,a.collision_summary);z={'status':'PASS' if ok else 'FAIL','thresholds':TH,'checks':c};s=json.dumps(z,indent=2);print(s);Path(a.out_json).write_text(s+'\n') if a.out_json else None;sys.exit(0 if ok else 1)
if __name__=='__main__':main()
