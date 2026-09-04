#!/usr/bin/env python3
"""Phase179 machine-attested batch scheduler bridge for the frozen D3 campaign."""
from __future__ import annotations
import argparse, hashlib, json, os, shlex, subprocess, sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import phase174_batch_submit as p174  # noqa: E402
import phase176_production_launcher as p176  # noqa: E402
PHASE=179; EXPECTED_TOTAL=127; EXPECTED_COMMISSIONING=8; EXPECTED_BLIND=119
REQUIRED_RECORDS=("positions","velocities","particle_ids","masses")
class BatchError(RuntimeError): pass

def sha256_file(path:Path,chunk_size:int=8*1024*1024)->str:
 h=hashlib.sha256()
 with path.open('rb') as fh:
  for block in iter(lambda:fh.read(chunk_size),b''): h.update(block)
 return h.hexdigest()

def truthy(value:str)->bool: return str(value).strip().lower()=="true"

def load_attested(machine_attestation:Path, executable:Path)->Dict:
 att=p176.load_attestation(machine_attestation, executable)
 eq=att.get('equivalence',{})
 if eq.get('status')!='PASS': raise BatchError('Phase176 machine equivalence is not PASS')
 names=tuple(x.get('name') for x in eq.get('records_checked',[]))
 if names!=REQUIRED_RECORDS: raise BatchError(f'Phase176 physical-record contract mismatch: {names}')
 return att

def frozen_rows()->Tuple[List[Dict[str,str]],List[Dict[str,str]],List[Dict[str,str]]]:
 rows,commissioning,blind=p174.frozen_rows()
 if len(rows)!=EXPECTED_TOTAL: raise BatchError(f'expected {EXPECTED_TOTAL} rows, got {len(rows)}')
 if len(commissioning)!=EXPECTED_COMMISSIONING: raise BatchError(f'expected {EXPECTED_COMMISSIONING} commissioning rows, got {len(commissioning)}')
 if len(blind)!=EXPECTED_BLIND: raise BatchError(f'expected {EXPECTED_BLIND} blind rows, got {len(blind)}')
 return rows,commissioning,blind

def validate_slurm_options(options:Iterable[str], for_submit:bool)->List[str]:
 return p174.validate_slurm_options(list(options), for_submit)

def verify_phase176_completion(record:Dict, attestation:Dict)->None:
 provenance=record.get('provenance')
 if not isinstance(provenance,dict): raise BatchError('completed run lacks Phase176 provenance object')
 expected={'phase':176,'status':'PASS','build_provenance':'phase176_build_attest','canonical_source_commit':p176.CANONICAL_SOURCE_COMMIT,'target_source_commit':p176.CANONICAL_SOURCE_COMMIT,'production_config_sha256':p176.CANONICAL_CONFIG_SHA256,'phase172_manifest_sha256':p176.CANONICAL_MANIFEST_SHA256,'production_executable_sha256':attestation['production_executable_sha256']}
 bad={k:{'observed':provenance.get(k),'expected':v} for k,v in expected.items() if provenance.get(k)!=v}
 if bad: raise BatchError(f'completed run provenance is not Phase176-attested: {bad}')
 if record.get('executable_sha256')!=attestation['production_executable_sha256']:
  raise BatchError('completed run executable SHA does not match Phase176 attestation')

def verify_commissioning(run_root:Path, proof_path:Path, machine_attestation:Path, executable:Path)->Dict:
 att=load_attested(machine_attestation, executable)
 base=p174.verify_commissioning(run_root, proof_path)
 failures=list(base.get('failures',[])); _,commissioning,_=frozen_rows()
 for row in commissioning:
  run_dir=run_root/row['run_id']; post_path,post=p174.completion_record(run_dir)
  if post_path is None or post is None: continue
  try: verify_phase176_completion(post, att)
  except BatchError as exc: failures.append(f"{row['run_id']}: {exc}")
 proof=dict(base); proof.update({'phase':PHASE,'kind':'phase179_machine_attested_commissioning_release_gate','base_phase174_status':base.get('status'),'status':'PASS' if base.get('status')=='PASS' and not failures else 'FAIL','machine_attestation':str(machine_attestation.resolve()),'machine_attestation_sha256':sha256_file(machine_attestation),'canonical_source_commit':p176.CANONICAL_SOURCE_COMMIT,'production_config_sha256':p176.CANONICAL_CONFIG_SHA256,'production_executable':str(executable.resolve()),'production_executable_sha256':att['production_executable_sha256'],'phase176_equivalence_status':att.get('equivalence',{}).get('status'),'phase176_records_checked':[x.get('name') for x in att.get('equivalence',{}).get('records_checked',[])],'failures':failures})
 proof_path.parent.mkdir(parents=True,exist_ok=True); proof_path.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n'); return proof

def load_commissioning_proof(path:Path, commissioning:List[Dict[str,str]], attestation:Dict, machine_attestation:Path, executable:Path)->Dict:
 proof=p174.load_commissioning_proof(path, commissioning)
 if proof.get('phase')!=PHASE: raise BatchError('commissioning proof is not a Phase179 attested release proof')
 if proof.get('machine_attestation_sha256')!=sha256_file(machine_attestation): raise BatchError('commissioning proof attestation SHA mismatch')
 if proof.get('production_executable_sha256')!=attestation['production_executable_sha256']: raise BatchError('commissioning proof production executable SHA mismatch')
 if proof.get('canonical_source_commit')!=p176.CANONICAL_SOURCE_COMMIT: raise BatchError('commissioning proof canonical source mismatch')
 if proof.get('phase176_equivalence_status')!='PASS': raise BatchError('commissioning proof lacks Phase176 equivalence PASS')
 if tuple(proof.get('phase176_records_checked',[]))!=REQUIRED_RECORDS: raise BatchError('commissioning proof lacks complete physical-record equivalence list')
 if sha256_file(executable)!=attestation['production_executable_sha256']: raise BatchError('current executable no longer matches attestation')
 return proof

def write_job(path:Path,row:Dict[str,str],args,slurm_options:List[str])->None:
 path.parent.mkdir(parents=True,exist_ok=True); dispatcher=HERE/'phase176_safe_resume.py'
 if not dispatcher.is_file(): raise BatchError('Phase176 safe-resume dispatcher missing')
 command=[sys.executable,str(dispatcher),'--machine-attestation',str(Path(args.machine_attestation).resolve()),'dispatch','--run-id',row['run_id'],'--executable',str(Path(args.executable).resolve()),'--ic-root',str(Path(args.ic_root).resolve()),'--run-root',str(Path(args.run_root).resolve()),'--mpi-prefix',args.mpi_prefix]
 if args.mpi_tasks is not None: command.extend(['--mpi-tasks',str(args.mpi_tasks)])
 if args.no_generate_ic: command.append('--no-generate-ic')
 command.extend(['--max-mem-mb',str(args.max_mem_mb),'--time-limit-cpu',str(args.time_limit_cpu)])
 lines=['#!/usr/bin/env bash',f"#SBATCH --job-name=d3-{row['run_id']}",f"#SBATCH --output={path.parent / 'slurm-%j.out'}",f"#SBATCH --error={path.parent / 'slurm-%j.err'}"]
 lines.extend(f'#SBATCH {option}' for option in slurm_options)
 lines.extend(['set -euo pipefail',f"test -r {shlex.quote(str(Path(args.machine_attestation).resolve()))}",f"test -x {shlex.quote(str(Path(args.executable).resolve()))}",shlex.join(command)])
 path.write_text('\n'.join(lines)+'\n'); path.chmod(0o755)

def stage_or_submit(args)->Dict:
 _,commissioning,blind=frozen_rows(); executable=Path(args.executable).resolve(); machine_attestation=Path(args.machine_attestation).resolve(); att=load_attested(machine_attestation,executable)
 selected=commissioning if args.phase=='commissioning' else blind
 if args.phase=='blind':
  if not args.commissioning_proof: raise BatchError('blind phase requires --commissioning-proof')
  load_commissioning_proof(Path(args.commissioning_proof),commissioning,att,machine_attestation,executable)
 options=validate_slurm_options(args.slurm_option,args.submit); batch_root=Path(args.batch_root).resolve(); jobs_dir=batch_root/args.phase/'jobs'; jobs_dir.mkdir(parents=True,exist_ok=True)
 entries=[]
 for row in selected:
  job=jobs_dir/f"{row['run_id']}.slurm"
  if job.exists(): raise BatchError(f'refusing to overwrite existing scheduler job: {job}')
  write_job(job,row,args,options)
  entry={'run_id':row['run_id'],'group':row['group'],'branch':row['branch'],'resolution_tier':row['resolution_tier'],'N_total':int(row['N_total']),'seed':int(row['seed']),'blind_analysis':truthy(row['blind_analysis']),'job_script':str(job),'job_sha256':sha256_file(job),'submitted':False}
  if args.submit:
   p=subprocess.run([args.sbatch,str(job)],check=True,capture_output=True,text=True); entry['submitted']=True; entry['submission_stdout']=p.stdout.strip()
  entries.append(entry)
 report={'phase':PHASE,'status':'SUBMITTED' if args.submit else 'STAGED','campaign_phase':args.phase,'manifest_sha256':p176.CANONICAL_MANIFEST_SHA256,'selected_runs':len(entries),'blind_selected':sum(e['blind_analysis'] for e in entries),'commissioning_selected':sum(not e['blind_analysis'] for e in entries),'machine_attestation':str(machine_attestation),'machine_attestation_sha256':sha256_file(machine_attestation),'canonical_source_commit':p176.CANONICAL_SOURCE_COMMIT,'production_config_sha256':p176.CANONICAL_CONFIG_SHA256,'production_executable':str(executable),'production_executable_sha256':att['production_executable_sha256'],'phase176_equivalence_status':att.get('equivalence',{}).get('status'),'phase176_records_checked':[x.get('name') for x in att.get('equivalence',{}).get('records_checked',[])],'dispatcher':str((HERE/'phase176_safe_resume.py').resolve()),'dispatcher_sha256':sha256_file(HERE/'phase176_safe_resume.py'),'mpi_prefix':args.mpi_prefix,'mpi_tasks':args.mpi_tasks,'slurm_options':options,'entries':entries}
 report_path=batch_root/args.phase/'phase179_batch_report.json'; report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); return report

def parser()->argparse.ArgumentParser:
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='command',required=True)
 v=sub.add_parser('verify-commissioning'); v.add_argument('--run-root',required=True); v.add_argument('--proof',required=True); v.add_argument('--machine-attestation',required=True); v.add_argument('--executable',required=True)
 s=sub.add_parser('stage'); s.add_argument('--phase',choices=['commissioning','blind'],required=True); s.add_argument('--machine-attestation',required=True); s.add_argument('--executable',required=True); s.add_argument('--ic-root',required=True); s.add_argument('--run-root',required=True); s.add_argument('--batch-root',required=True); s.add_argument('--mpi-prefix',default='srun'); s.add_argument('--mpi-tasks',type=int,default=None); s.add_argument('--max-mem-mb',type=int,default=3500); s.add_argument('--time-limit-cpu',type=int,default=170000); s.add_argument('--no-generate-ic',action='store_true'); s.add_argument('--slurm-option',action='append',default=[]); s.add_argument('--commissioning-proof',default=None); s.add_argument('--submit',action='store_true'); s.add_argument('--sbatch',default='sbatch'); return ap

def main()->int:
 args=parser().parse_args()
 try:
  if args.command=='verify-commissioning':
   result=verify_commissioning(Path(args.run_root),Path(args.proof),Path(args.machine_attestation),Path(args.executable)); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result['status']=='PASS' else 2
  result=stage_or_submit(args); print(json.dumps(result,indent=2,sort_keys=True)); return 0
 except (BatchError,p174.BatchError,p176.GateError,p176.core.LaunchError,subprocess.CalledProcessError,ValueError,OSError) as exc:
  print(json.dumps({'phase':PHASE,'status':'FAIL','error':str(exc)},indent=2),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
