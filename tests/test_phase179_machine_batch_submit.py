#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, tempfile
from argparse import Namespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'d3'/'production'/'phase179_machine_batch_submit.py'
spec=importlib.util.spec_from_file_location('phase179_machine_batch_submit',MOD)
assert spec is not None and spec.loader is not None
p179=importlib.util.module_from_spec(spec); spec.loader.exec_module(p179)
rows,commissioning,blind=p179.frozen_rows()
assert len(rows)==127 and len(commissioning)==8 and len(blind)==119
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp); exe=root/'GIZMO_D3_PROD'; exe.write_text('#!/bin/sh\nexit 0\n'); exe.chmod(0o755); exe_sha=p179.sha256_file(exe)
 att={'phase':176,'status':'PASS','gate':'production-machine self-build + audit-free physical equivalence','build_provenance':'phase176_build_attest','canonical_source_commit':p179.p176.CANONICAL_SOURCE_COMMIT,'target_source_commit':p179.p176.CANONICAL_SOURCE_COMMIT,'production_config_sha256':p179.p176.CANONICAL_CONFIG_SHA256,'phase172_manifest_sha256':p179.p176.CANONICAL_MANIFEST_SHA256,'manifest_rows':127,'production_executable':str(exe),'production_executable_sha256':exe_sha,'equivalence':{'status':'PASS','records_checked':[{'name':'positions'},{'name':'velocities'},{'name':'particle_ids'},{'name':'masses'}]}}
 att_path=root/'phase176_machine_attestation.json'; att_path.write_text(json.dumps(att,indent=2)+'\n')
 args=Namespace(phase='commissioning',machine_attestation=str(att_path),executable=str(exe),ic_root=str(root/'ics'),run_root=str(root/'runs'),batch_root=str(root/'batch_comm'),mpi_prefix='srun',mpi_tasks=32,max_mem_mb=4000,time_limit_cpu=12345,no_generate_ic=False,slurm_option=[],commissioning_proof=None,submit=False,sbatch='sbatch')
 report=p179.stage_or_submit(args)
 assert report['status']=='STAGED' and report['selected_runs']==8 and report['commissioning_selected']==8 and report['blind_selected']==0
 assert report['production_executable_sha256']==exe_sha and report['phase176_equivalence_status']=='PASS'
 assert report['phase176_records_checked']==['positions','velocities','particle_ids','masses']
 for entry in report['entries']:
  text=Path(entry['job_script']).read_text()
  assert 'phase176_safe_resume.py --machine-attestation' in text
  assert ' dispatch ' in text and '--mpi-tasks 32' in text and '--max-mem-mb 4000' in text and '--time-limit-cpu 12345' in text
 no_proof=Namespace(**{**args.__dict__,'phase':'blind','batch_root':str(root/'bad_blind')})
 try: p179.stage_or_submit(no_proof)
 except p179.BatchError: pass
 else: raise AssertionError('blind staging without commissioning proof was accepted')
 run_root=root/'complete_runs'
 for row in commissioning:
  rd=run_root/row['run_id']; rd.mkdir(parents=True)
  for i in range(10): (rd/f'snapshot_{i:03d}').write_bytes(f"{row['run_id']}-{i}".encode())
  digest,files=p179.p174.p173.directory_digest(rd,exclude={p179.p174.p175.STATE_NAME,p179.p174.p175.LOCK_NAME,p179.p174.p175.ATTEMPTS_NAME})
  post={'run_id':row['run_id'],'status':'COMPLETE','manifest_sha256':p179.p174.EXPECTED_MANIFEST_SHA256,'manifest_row':row,'provenance':att,'executable_sha256':exe_sha,'snapshot_count':10,'required_snapshot_count':10,'completion_marker':True,'fatal_marker':False,'attempt':1,'restart_flag':0,'run_directory_sha256':digest,'file_hashes':files}
  (rd/p179.p174.p175.STATE_NAME).write_text(json.dumps(post)+'\n')
 proof_path=root/'commissioning-proof.json'; proof=p179.verify_commissioning(run_root,proof_path,att_path,exe)
 assert proof['status']=='PASS', proof['failures']; assert proof['phase']==179 and proof['complete_runs']==8
 assert proof['machine_attestation_sha256']==p179.sha256_file(att_path) and proof['production_executable_sha256']==exe_sha
 p179.load_commissioning_proof(proof_path,commissioning,att,att_path,exe)
 blind_args=Namespace(**{**args.__dict__,'phase':'blind','batch_root':str(root/'batch_blind'),'commissioning_proof':str(proof_path)})
 blind_report=p179.stage_or_submit(blind_args)
 assert blind_report['status']=='STAGED' and blind_report['selected_runs']==119 and blind_report['blind_selected']==119 and blind_report['commissioning_selected']==0
 bad=json.loads(proof_path.read_text()); bad['production_executable_sha256']='0'*64; bad_path=root/'bad-proof.json'; bad_path.write_text(json.dumps(bad))
 try: p179.load_commissioning_proof(bad_path,commissioning,att,att_path,exe)
 except p179.BatchError: pass
 else: raise AssertionError('proof with wrong production executable SHA was accepted')
 first=commissioning[0]
 rd=run_root/first['run_id']
 for i in range(10): (rd/f'snapshot_{i:03d}').write_bytes(f"{first['run_id']}-{i}".encode())
 digest,files=p179.p174.p173.directory_digest(rd,exclude={p179.p174.p175.STATE_NAME,p179.p174.p175.LOCK_NAME,p179.p174.p175.ATTEMPTS_NAME})
 badpost={'run_id':first['run_id'],'status':'COMPLETE','manifest_sha256':p179.p174.EXPECTED_MANIFEST_SHA256,'manifest_row':first,'provenance':{'phase':175},'executable_sha256':exe_sha,'snapshot_count':10,'required_snapshot_count':10,'completion_marker':True,'fatal_marker':False,'run_directory_sha256':digest,'file_hashes':files}
 (rd/p179.p174.p175.STATE_NAME).write_text(json.dumps(badpost)+'\n')
 bad_attested=p179.verify_commissioning(run_root,root/'bad-attested-proof.json',att_path,exe)
 assert bad_attested['status']=='FAIL'
 assert any('Phase176-attested' in x or 'fingerprint' in x for x in bad_attested['failures'])
print('Phase179 attested batch submit gate PASS')
print('commissioning IDs:', ','.join(r['run_id'] for r in commissioning))
