#!/usr/bin/env python3
"""Synthetic adversarial self-test for Phase172 blind physics validation.
Fixtures test the validator only. They are never physics evidence.
"""
import argparse,importlib.util,tempfile
from pathlib import Path
import numpy as np,pandas as pd
TIMES=(0.,.25,.5,1.,2.,5.,10.,20.,40.,55.28,80.);BINS=(.05,.2,1.);SPECIES=('H','L','total');CHANNELS=('HH','LL','HL')
def load(p):
 s=importlib.util.spec_from_file_location('v',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def effect(r,sp):
 b=r.branch
 if r.group=='zero_cross_section_null':b='CDM'
 if r.group=='permutation_reproducibility':b='SIDM2v'
 if r.group=='identical_label_null':return 1.
 return 1+{'CDM':0,'SIDMx':.05 if sp=='H' else -.05 if sp=='L' else 0,'HL_off':.01 if sp=='H' else -.01 if sp=='L' else 0,'SIDM2v':.04 if sp=='H' else -.03 if sp=='L' else .005,'SIDM2c_const':.02,'HH_only':.015 if sp=='H' else 0,'LL_only':-.015 if sp=='L' else 0,'HL_HH':.03 if sp=='H' else -.02,'HL_LL':.03 if sp=='H' else -.025}.get(b,0)
def make(manifest,root):
 M=pd.read_csv(manifest);R=[];P=[];X=[]
 for _,r in M.iterrows():
  seed=int(r.seed);j=((seed%7)-3)*.001
  S={'SIDMx':.20,'HL_off':.02,'SIDM2v':.15,'CDM':.005}.get(r.branch,.08)+j
  if r.group=='zero_cross_section_null':S=.005+j
  if r.group=='identical_label_null':S=j*.1
  R.append({'run_id':r.run_id,'branch':r.branch,'group':r.group,'resolution_tier':r.resolution_tier,'seed':seed,'status':'COMPLETE','executable_sha256':'1'*64,'analysis_sha256':'2'*64,'output_sha256':f"{int(str(r.run_id).split('-')[-1]):064x}",'final_time_Gyr':80.,'energy_drift_abs_max':.001,'momentum_drift_abs_max':1e-6,'max_pair_dP_over_P':1e-14,'max_pair_dK_over_K':1e-14,'prob_clip_fraction_max':.001,'particle_loss_untracked':0,'cdm_profile_median_drift_10Gyr':.01 if r.branch=='CDM' else np.nan,'sidm2c_profile_median_error_10Gyr':.05 if r.branch=='SIDM2c_const' else np.nan,'sidm2c_collapse_clock_error_frac':.10 if r.branch=='SIDM2c_const' else np.nan,'S_inner_10Gyr':S,'O_overlap_10Gyr':.5,'H_in_L_out_score':.2 if r.branch=='SIDMx' else .02,'notes':'synthetic validator fixture'})
  for t in TIMES:
   for bi,rr in enumerate(BINS):
    base=10/(1+5*rr)
    for sp in SPECIES:
     val=base*effect(r,sp)
     if r.group not in ('zero_cross_section_null','permutation_reproducibility','identical_label_null'):val*=1+j
     if r.resolution_tier=='R3_gold' and r.branch=='SIDM2v' and r.group=='core_blind_production':val*=1.01
     if r.group=='half_timestep_convergence' and r.branch=='SIDM2v':val*=1.01
     if r.group=='neighbor_kernel_convergence' and r.branch=='SIDM2v':val*=.98 if r.kernel_control=='K_low' else 1.02
     if r.group=='zero_cross_section_null':val=base*(1+j)
     if r.group=='permutation_reproducibility':val=base*effect(r,sp)*(1+j)
     if r.group=='identical_label_null':
      sign=1 if (int(str(r.run_id).split('-')[-1])+bi)%2==0 else -1
      val=base*(1+.002*sign) if sp=='H' else base*(1-.002*sign) if sp=='L' else base
     P.append({'run_id':r.run_id,'time_Gyr':t,'r_mid_over_rs':rr,'r_lo_over_rs':rr*.8,'r_hi_over_rs':rr*1.2,'species':sp,'rho':val,'rho_initial':base,'rho_rel':val/base,'sigma2':1.,'beta':0.,'mass_enclosed':100*rr})
  mode=float(r.runtime_interaction_parameter)
  if r.branch=='CDM' and mode==0 or mode==-9:allowed=set()
  elif mode==-2:allowed={'HL'}
  elif mode==-3:allowed={'HH','LL'}
  elif mode==-4:allowed={'HH'}
  elif mode==-5:allowed={'LL'}
  elif mode==-6:allowed={'HH','HL'}
  elif mode==-7:allowed={'LL','HL'}
  else:allowed=set(CHANNELS)
  for ch in CHANNELS:
   n=100 if ch in allowed else 0;X.append({'run_id':r.run_id,'channel':ch,'collision_count':n,'mean_sigma_factor':1. if n else 0.,'mean_mu':0.,'max_pair_dP_over_P':1e-14 if n else 0.,'max_pair_dK_over_K':1e-14 if n else 0.,'prob_clip_fraction_max':.001 if n else 0.})
 rp=root/'run_summary.csv';pp=root/'profiles.csv';cp=root/'collision_log_summary.csv';pd.DataFrame(R).to_csv(rp,index=False);pd.DataFrame(P).to_csv(pp,index=False);pd.DataFrame(X).to_csv(cp,index=False);return rp,pp,cp
def gate(C,n):return next(x for x in C if x['gate']==n)
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--validator',required=True);a=p.parse_args();v=load(a.validator)
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);rp,pp,cp=make(a.manifest,root);ok,C=v.validate(a.manifest,rp,pp,cp)
  if not ok:raise SystemExit('PASS fixture failed: '+str([x for x in C if x['fatal'] and not x['passed']]))
  print('PASS fixture: PASS');M=pd.read_csv(a.manifest)
  R=pd.read_csv(rp);R.loc[0,'final_time_Gyr']=10;R.to_csv(root/'bad_time.csv',index=False);ok,C=v.validate(a.manifest,root/'bad_time.csv',pp,cp);assert not ok and not gate(C,'all_runs_complete_and_80Gyr')['passed'];print('80-Gyr truncation fixture: correctly FAIL')
  P=pd.read_csv(pp);rid=M[(M.group=='half_timestep_convergence')&(M.branch=='SIDM2v')].iloc[0].run_id;z=(P.run_id==rid)&np.isclose(P.time_Gyr,10)&P.species.isin(['H','L'])&P.r_mid_over_rs.between(.03,3);P.loc[z,'rho']*=1.2;P.to_csv(root/'bad_dt.csv',index=False);ok,C=v.validate(a.manifest,rp,root/'bad_dt.csv',cp);assert not ok and not gate(C,'SIDM2v_half_timestep_profile_convergence')['passed'];print('timestep convergence fixture: correctly FAIL')
  P=pd.read_csv(pp);rid=M[(M.group=='neighbor_kernel_convergence')&(M.branch=='SIDM2v')&(M.kernel_control=='K_high')].iloc[0].run_id;z=(P.run_id==rid)&np.isclose(P.time_Gyr,10)&P.species.isin(['H','L'])&P.r_mid_over_rs.between(.03,3);P.loc[z,'rho']*=1.2;P.to_csv(root/'bad_ngb.csv',index=False);ok,C=v.validate(a.manifest,rp,root/'bad_ngb.csv',cp);assert not ok and not gate(C,'SIDM2v_K_high_profile_convergence')['passed'];print('neighbor convergence fixture: correctly FAIL')
  X=pd.read_csv(cp);rid=M[(M.group=='core_blind_production')&(M.branch=='SIDMx')].iloc[0].run_id;X.loc[(X.run_id==rid)&(X.channel=='HH'),'collision_count']=1;X.to_csv(root/'bad_ch.csv',index=False);ok,C=v.validate(a.manifest,rp,pp,root/'bad_ch.csv');assert not ok and not gate(C,'forbidden_channels_zero')['passed'];print('forbidden-channel fixture: correctly FAIL')
 print('Phase172 blind physics validator self-test: PASS')
if __name__=='__main__':main()
