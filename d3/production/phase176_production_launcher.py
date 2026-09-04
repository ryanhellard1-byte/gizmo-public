#!/usr/bin/env python3
"""Phase176 machine-attested launcher for the frozen Phase172 campaign."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import phase173_production_launcher as core
CANONICAL_SOURCE_COMMIT='dc93bca31b19135a1f8510e838f23abc850869fb'; CANONICAL_CONFIG_SHA256='887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329'; CANONICAL_MANIFEST_SHA256='e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d'
class GateError(RuntimeError): pass
def sha256_file(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 return h.hexdigest()
def load_attestation(path:Path,executable:Path|None=None)->dict:
 if not path.is_file(): raise GateError(f"Phase176 machine attestation missing: {path}")
 obj=json.loads(path.read_text()); expected={'phase':176,'status':'PASS','build_provenance':'phase176_build_attest','canonical_source_commit':CANONICAL_SOURCE_COMMIT,'target_source_commit':CANONICAL_SOURCE_COMMIT,'production_config_sha256':CANONICAL_CONFIG_SHA256,'phase172_manifest_sha256':CANONICAL_MANIFEST_SHA256}; bad={k:{'observed':obj.get(k),'expected':v} for k,v in expected.items() if obj.get(k)!=v}
 if bad: raise GateError(f"Phase176 attestation mismatch: {bad}")
 eq=obj.get('equivalence',{})
 if eq.get('status')!='PASS': raise GateError('machine audit/production equivalence did not PASS')
 if tuple(x.get('name') for x in eq.get('records_checked',[]))!=('positions','velocities','particle_ids','masses'): raise GateError('machine physical-record equivalence contract incomplete')
 if not obj.get('production_executable_sha256'): raise GateError('attestation lacks production executable SHA')
 if executable is not None:
  if not executable.is_file(): raise GateError(f"production executable missing: {executable}")
  observed=sha256_file(executable)
  if observed!=obj['production_executable_sha256']: raise GateError(f"production executable is not attested binary: {observed} != {obj['production_executable_sha256']}")
 return obj
def provenance_from_attestation(path:Path,executable:Path|None=None)->dict:
 att=load_attestation(path,executable); prov=dict(att); prov['executable_sha256']=att['production_executable_sha256']; prov['phase176_attestation_sha256']=sha256_file(path); return prov
def parser():
 p=argparse.ArgumentParser(); p.add_argument('--machine-attestation',default='phase176_machine_attestation.json'); s=p.add_subparsers(dest='cmd',required=True); pre=s.add_parser('preflight'); pre.add_argument('--executable'); rp=s.add_parser('r0-plan'); rp.add_argument('--ic-root',default='./phase172_ics'); pl=s.add_parser('plan'); pl.add_argument('--run-id',required=True); pl.add_argument('--ic-root',default='./phase172_ics')
 for name in ('prepare','run'):
  x=s.add_parser(name); x.add_argument('--run-id',required=True); x.add_argument('--executable',required=True); x.add_argument('--ic-root',required=True); x.add_argument('--run-root',required=True); x.add_argument('--mpi-prefix',default=''); x.add_argument('--max-mem-mb',type=int,default=3500); x.add_argument('--time-limit-cpu',type=int,default=170000); x.add_argument('--no-generate-ic',action='store_true')
 return p
def main():
 args=parser().parse_args()
 try:
  manifest_path,rows=core.materialize_manifest(Path('.phase176')/'phase172_manifest.csv')
  for r in rows: core.validate_row(r)
  if args.cmd=='r0-plan':
   found=[core.plan(r,i,Path(args.ic_root)) for i,r in enumerate(rows) if r['group']=='R0_commissioning_not_for_claims']
   if len(found)!=8: raise GateError(f"expected 8 R0 rows, found {len(found)}")
   print(json.dumps({'phase':176,'status':'PASS','r0_runs':found},indent=2)); return 0
  if args.cmd=='plan': i,r=core.find_row(rows,args.run_id); print(json.dumps({'phase':176,'status':'PASS','plan':core.plan(r,i,Path(args.ic_root))},indent=2)); return 0
  exe=Path(args.executable).resolve() if args.executable else None; ap=Path(args.machine_attestation).resolve(); prov=provenance_from_attestation(ap,exe)
  if args.cmd=='preflight': print(json.dumps({'phase':176,'status':'PASS','gate':'machine-attested production launcher','manifest_sha256':CANONICAL_MANIFEST_SHA256,'rows':len(rows),'blind_runs':sum(r['blind_analysis']=='True' for r in rows),'canonical_source_commit':CANONICAL_SOURCE_COMMIT,'production_config_sha256':CANONICAL_CONFIG_SHA256,'machine_attestation':str(ap),'machine_attestation_sha256':sha256_file(ap),'production_executable_sha256':prov['executable_sha256'],'required_final_time_Gyr':core.EXPECTED_FINAL_TIME_GYR},indent=2)); return 0
  run_dir,row,command,pre=core.prepare(args,prov,rows,manifest_path); pre.update({'phase176_launcher_sha256':sha256_file(Path(__file__)),'phase176_machine_attestation':str(ap),'phase176_machine_attestation_sha256':sha256_file(ap),'canonical_source_commit':CANONICAL_SOURCE_COMMIT,'production_config_sha256':CANONICAL_CONFIG_SHA256}); (run_dir/'phase176_PRELAUNCH.json').write_text(json.dumps(pre,indent=2)+'\n'); print(json.dumps({'phase':176,'status':'PREPARED','run_dir':str(run_dir),'command':command,'executable_sha256':pre['executable_sha256'],'machine_attestation_sha256':pre['phase176_machine_attestation_sha256'],'ic_sha256':pre['ic_sha256'],'params_sha256':pre['params_sha256']},indent=2))
  if args.cmd=='prepare': return 0
  return core.execute(run_dir,row,command,pre)
 except (GateError,core.LaunchError,OSError,ValueError,subprocess.CalledProcessError) as exc: print(f"PHASE176 PRODUCTION LAUNCHER FAIL: {exc}",file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
