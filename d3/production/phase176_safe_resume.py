#!/usr/bin/env python3
"""Machine-attested entry point for the existing Phase175 safe-resume engine."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import phase175_safe_resume as resume
import phase176_production_launcher as p176
class BridgeError(RuntimeError): pass
def parser():
 p=argparse.ArgumentParser(); p.add_argument('--machine-attestation',required=True); s=p.add_subparsers(dest='command',required=True)
 for name in ('dispatch','inspect'):
  x=s.add_parser(name); x.add_argument('--run-id',required=True); x.add_argument('--executable',required=True); x.add_argument('--run-root',required=True); x.add_argument('--mpi-prefix',default=''); x.add_argument('--mpi-tasks',type=int,default=None)
  if name=='dispatch': x.add_argument('--ic-root',required=True); x.add_argument('--max-mem-mb',type=int,default=3500); x.add_argument('--time-limit-cpu',type=int,default=170000); x.add_argument('--no-generate-ic',action='store_true')
 return p
def main():
 args=parser().parse_args(); ap=Path(args.machine_attestation).resolve(); exe=Path(args.executable).resolve()
 try:
  prov=p176.provenance_from_attestation(ap,exe)
  def load_campaign():
   manifest_path,rows=resume.p173.materialize_manifest(Path('.phase176')/'phase172_manifest.csv')
   for r in rows: resume.p173.validate_row(r)
   return prov,manifest_path,rows
  resume.load_campaign=load_campaign; return resume.dispatch(args) if args.command=='dispatch' else resume.inspect(args)
 except (BridgeError,p176.GateError,resume.ResumeError,resume.p173.LaunchError,OSError,ValueError) as exc: print(json.dumps({'phase':176,'status':'FAIL','error':str(exc)},indent=2),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
