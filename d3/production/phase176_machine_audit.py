#!/usr/bin/env python3
"""Phase176 production-machine build provenance and physical-equivalence gate."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, platform, re, shlex, shutil, struct, subprocess, sys, tempfile
from pathlib import Path
from typing import Dict, List, Tuple
HERE=Path(__file__).resolve().parent
DEFAULT_REFERENCE=HERE/"phase176_ci_equivalence_reference.json"
AUDIT_DEFINE="SIDMX_D3_LIVE_AUDIT"
EXPECTED={"source_commit":"dc93bca31b19135a1f8510e838f23abc850869fb","workflow_run_id":33850670457,"artifact_id":9928241676,"artifact_digest":"sha256:401a92db93b2d68f0d5fe9a84e3053bb47191b0bbbfb5385ae2538279d06dc05","production_executable_sha256":"f11e011b9420ebe829eb77295a09c0d525dd6ae8c0411173231911cacfb98dc0","audit_executable_sha256":"760ed6ad69ca3e88295acbd24b2c4bfc1b2f1187df826ae7d1aa3c6d4df79d88","production_config_sha256":"887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329","phase172_manifest_sha256":"e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d","equivalence_status":"PASS","comparison":"GADGET format-1 physical record byte equality; header/provenance ignored"}
REQUIRED_RECORDS=("positions","velocities","particle_ids","masses")
class AuditError(RuntimeError): pass

def sha256_file(path:Path,chunk_size:int=8*1024*1024)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(chunk_size),b''): h.update(b)
 return h.hexdigest()
def run_text(cmd:List[str],cwd:Path|None=None)->str: return subprocess.run(cmd,cwd=cwd,check=True,capture_output=True,text=True).stdout.strip()
def load_reference(path:Path)->Dict:
 obj=json.loads(path.read_text()); bad={k:{"observed":obj.get(k),"expected":v} for k,v in EXPECTED.items() if obj.get(k)!=v}
 if bad: raise AuditError(f"canonical CI reference mismatch: {bad}")
 if tuple(obj.get('records_checked',()))!=REQUIRED_RECORDS: raise AuditError('canonical CI physical-record contract changed')
 return obj
def exact_source_commit(source_tree:Path,ref:Dict)->str:
 head=run_text(['git','-C',str(source_tree),'rev-parse','HEAD'])
 if head!=ref['source_commit']: raise AuditError(f"source must be canonical commit {ref['source_commit']}; observed {head}")
 for cmd,label in [(['git','-C',str(source_tree),'diff','--quiet'],'tracked'),(['git','-C',str(source_tree),'diff','--cached','--quiet'],'index')]:
  if subprocess.run(cmd).returncode!=0: raise AuditError(f"canonical source has {label} modifications")
 return head
def normalized_config(path:Path,remove_audit:bool)->Tuple[str,...]:
 out=[]
 for raw in path.read_text().splitlines():
  line=raw.strip()
  if not line or (line.startswith('#') and not line.startswith('#define')): continue
  if remove_audit and line==AUDIT_DEFINE: continue
  out.append(line)
 return tuple(out)
def verify_source_contract(source_tree:Path,ref:Dict)->Dict:
 prod=source_tree/'d3/Config_d3_production.sh'; audit=source_tree/'d3/Config_d3_ci.sh'
 for p in (prod,audit):
  if not p.is_file(): raise AuditError(f"missing build config: {p}")
 psha=sha256_file(prod)
 if psha!=ref['production_config_sha256']: raise AuditError(f"production config SHA mismatch: {psha}")
 if AUDIT_DEFINE in prod.read_text().splitlines(): raise AuditError('production config enables live audit')
 if AUDIT_DEFINE not in audit.read_text().splitlines(): raise AuditError('audit config missing live audit')
 if normalized_config(prod,False)!=normalized_config(audit,True): raise AuditError('audit/production configs differ by more than live-audit token')
 lock=source_tree/'d3/production/phase172_lock.py'; spec=importlib.util.spec_from_file_location('phase172_lock_target',lock)
 if spec is None or spec.loader is None: raise AuditError('cannot load Phase172 lock')
 mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); raw,rows=mod.load(); msha=hashlib.sha256(raw).hexdigest()
 if msha!=ref['phase172_manifest_sha256'] or len(rows)!=127: raise AuditError(f"frozen manifest mismatch: sha={msha} rows={len(rows)}")
 return {'production_config_sha256':psha,'phase172_manifest_sha256':msha,'manifest_rows':len(rows)}
def export_source(source_tree:Path,dest:Path)->None:
 dest.mkdir(parents=True,exist_ok=False); p1=subprocess.Popen(['git','-C',str(source_tree),'archive','HEAD'],stdout=subprocess.PIPE); p2=subprocess.run(['tar','-x','-C',str(dest)],stdin=p1.stdout); assert p1.stdout is not None; p1.stdout.close(); rc=p1.wait()
 if rc or p2.returncode: raise AuditError('failed to export canonical source')
def set_systype(tree:Path,systype:str|None)->None:
 if not systype: return
 p=tree/'Makefile.systype'; text=p.read_text(); new,n=re.subn(r'^SYSTYPE="[^"]*"',f'SYSTYPE="{systype}"',text,count=1,flags=re.M)
 if n!=1: raise AuditError('cannot set Makefile.systype deterministically')
 p.write_text(new)
def build(tree:Path,config_rel:str,executable_name:str,jobs:int,systype:str|None)->Path:
 set_systype(tree,systype); cfg=tree/config_rel
 if not cfg.is_file(): raise AuditError(f"build config missing: {cfg}")
 shutil.copyfile(cfg,tree/'Config.sh'); subprocess.run(['make',f'-j{jobs}','CONFIG=Config.sh',f'EXEC={executable_name}'],cwd=tree,check=True); exe=tree/executable_name
 if not exe.is_file(): raise AuditError(f"build did not produce {exe}")
 return exe
def make_params(template:Path,ic:Path,outdir:Path)->str:
 text=template.read_text(); reps={'@IC@':str(ic.resolve()),'@OUT@':str(outdir.resolve()),'@MODE@':'-1','TimeOfFirstSnapshot         0.00010':'TimeOfFirstSnapshot         0.00004','TimeMax                      0.00010':'TimeMax                      0.00004','MaxSizeTimestep              0.00002':'MaxSizeTimestep              0.000004','BoxSize                      2000.0':'BoxSize                      20.0'}
 for old,new in reps.items():
  if old not in text: raise AuditError(f"equivalence template changed; missing {old!r}")
  text=text.replace(old,new)
 return text
def launch(exe:Path,params:Path,mpi_prefix:str,log:Path)->None:
 cmd=shlex.split(mpi_prefix)+[str(exe.resolve()),str(params.resolve()),'0']
 with log.open('w') as f: rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True).returncode
 text=log.read_text(errors='replace')
 if rc or not re.search(r'Simulation ends\.',text) or re.search(r'MPI_ABORT|ENDRUN issued|Fatal error',text): raise AuditError(f"{exe.name} equivalence execution failed; see {log}")
def latest_snapshot(outdir:Path)->Path:
 hits=sorted(p for p in outdir.glob('snapshot*') if p.is_file())
 if not hits: raise AuditError(f"no snapshot in {outdir}")
 return hits[-1]
def read_records(path:Path)->List[bytes]:
 data=path.read_bytes(); out=[]; pos=0
 while pos<len(data):
  if pos+4>len(data): raise AuditError(f"truncated record prefix: {path}")
  n=struct.unpack_from('<I',data,pos)[0]; pos+=4; payload=data[pos:pos+n]; pos+=n
  if pos+4>len(data): raise AuditError(f"truncated record suffix: {path}")
  m=struct.unpack_from('<I',data,pos)[0]; pos+=4
  if m!=n: raise AuditError(f"record marker mismatch in {path}")
  out.append(payload)
 return out
def compare_physical(a:Path,p:Path)->Dict:
 ar,pr=read_records(a),read_records(p)
 if len(ar)<5 or len(pr)<5: raise AuditError(f"too few GADGET records: {len(ar)}/{len(pr)}")
 result={'status':'PASS','comparison':EXPECTED['comparison'],'audit_snapshot_sha256':sha256_file(a),'production_snapshot_sha256':sha256_file(p),'records_checked':[]}
 for idx,name in ((1,'positions'),(2,'velocities'),(3,'particle_ids'),(4,'masses')):
  ah,ph=hashlib.sha256(ar[idx]).hexdigest(),hashlib.sha256(pr[idx]).hexdigest()
  if len(ar[idx])!=len(pr[idx]) or ah!=ph: raise AuditError(f"{name} physical record differs")
  result['records_checked'].append({'index':idx,'name':name,'bytes':len(ar[idx]),'sha256':ah})
 return result
def version_text(cmd:List[str])->str|None:
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=10); t=(p.stdout or p.stderr).strip(); return t.splitlines()[0] if t else None
 except Exception: return None
def build_attest(args)->Dict:
 refpath=Path(args.reference).resolve(); ref=load_reference(refpath); source=Path(args.source_tree).resolve(); head=exact_source_commit(source,ref); contract=verify_source_contract(source,ref)
 workroot=Path(args.work_dir).resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix='phase176-')); workroot.mkdir(parents=True,exist_ok=True); audit_tree=workroot/'src-audit'; prod_tree=workroot/'src-prod'
 for p in (audit_tree,prod_tree):
  if p.exists(): raise AuditError(f"refusing to reuse build tree: {p}")
 export_source(source,audit_tree); export_source(source,prod_tree); audit=build(audit_tree,'d3/Config_d3_ci.sh','GIZMO_D3_AUDIT',args.jobs,args.systype); prod=build(prod_tree,'d3/Config_d3_production.sh','GIZMO_D3_PROD',args.jobs,args.systype); asha,psha=sha256_file(audit),sha256_file(prod)
 if asha==psha: raise AuditError('audit and production executables are byte-identical')
 eq=workroot/'equivalence'; eq.mkdir(); ic=eq/'D3_equiv_cloud.dat'; gen=source/'d3/generate_d3_collision_cloud.py'; template=source/'d3/params_m11_smoke.template'
 subprocess.run([sys.executable,str(gen),'--n-total','1000','--seed','173001','--radius-kpc','1.0','--total-mass-msun','1.0e11','--stream-speed-kms','100','--dispersion-kms','100','--output',str(ic)],cwd=source,check=True); ao,po=eq/'audit',eq/'prod'; ao.mkdir(); po.mkdir(); ap,pp=eq/'audit.params',eq/'prod.params'; ap.write_text(make_params(template,ic,ao)); pp.write_text(make_params(template,ic,po)); launch(audit,ap,args.mpi_prefix,eq/'audit.log'); launch(prod,pp,args.mpi_prefix,eq/'prod.log'); equivalence=compare_physical(latest_snapshot(ao),latest_snapshot(po))
 outdir=Path(args.binary_dir).resolve(); outdir.mkdir(parents=True,exist_ok=True); audit_final=outdir/'GIZMO_D3_AUDIT'; prod_final=outdir/'GIZMO_D3_PROD'
 for src,dst in ((audit,audit_final),(prod,prod_final)):
  if dst.exists(): raise AuditError(f"refusing to overwrite production binary: {dst}")
  shutil.copy2(src,dst)
 result={'phase':176,'status':'PASS','gate':'production-machine self-build + audit-free physical equivalence','build_provenance':'phase176_build_attest','canonical_ci_reference_sha256':sha256_file(refpath),'canonical_source_commit':ref['source_commit'],'target_source_commit':head,**contract,'production_executable':str(prod_final),'production_executable_sha256':sha256_file(prod_final),'audit_executable':str(audit_final),'audit_executable_sha256':sha256_file(audit_final),'ci_production_executable_sha256':ref['production_executable_sha256'],'ci_binary_sha_match':sha256_file(prod_final)==ref['production_executable_sha256'],'build':{'systype':args.systype,'jobs':args.jobs},'equivalence':equivalence,'machine':{'platform':platform.platform(),'python':sys.version.split()[0],'cc':version_text(['cc','--version']),'make':version_text(['make','--version']),'mpi':version_text(shlex.split(args.mpi_prefix)[:1]+['--version']) if args.mpi_prefix.strip() else None}}
 output=Path(args.output).resolve(); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({**result,'attestation_path':str(output),'attestation_sha256':sha256_file(output)},indent=2)); return result
def parser():
 p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True); r=s.add_parser('reference-check'); r.add_argument('--reference',default=str(DEFAULT_REFERENCE)); c=s.add_parser('source-check'); c.add_argument('--reference',default=str(DEFAULT_REFERENCE)); c.add_argument('--source-tree',required=True); a=s.add_parser('build-attest'); a.add_argument('--reference',default=str(DEFAULT_REFERENCE)); a.add_argument('--source-tree',required=True); a.add_argument('--systype'); a.add_argument('--jobs',type=int,default=2); a.add_argument('--mpi-prefix',default=''); a.add_argument('--work-dir'); a.add_argument('--binary-dir',required=True); a.add_argument('--output',required=True); return p
def main():
 args=parser().parse_args()
 try:
  ref=load_reference(Path(args.reference))
  if args.cmd=='reference-check': print(json.dumps({'phase':176,'status':'PASS','reference':ref},indent=2)); return 0
  source=Path(args.source_tree).resolve(); head=exact_source_commit(source,ref); contract=verify_source_contract(source,ref)
  if args.cmd=='source-check': print(json.dumps({'phase':176,'status':'PASS','source_commit':head,**contract},indent=2)); return 0
  if args.jobs<=0: raise AuditError('--jobs must be positive')
  build_attest(args); return 0
 except (AuditError,OSError,ValueError,subprocess.CalledProcessError) as exc: print(f"PHASE176 MACHINE GATE FAIL: {exc}",file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
