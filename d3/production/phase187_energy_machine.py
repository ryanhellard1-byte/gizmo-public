#!/usr/bin/env python3
"""Phase187 source-pinned exact-energy post-processing executable.

This does not evolve production. It builds the frozen D3 source with one extra
GIZMO diagnostic define, COMPUTE_POTENTIAL_ENERGY, then uses restart-from-
snapshot mode to ask GIZMO for the exact engine K+U of immutable campaign
snapshots.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, platform, re, shlex, shutil, subprocess, sys, tempfile
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
D3 = HERE.parent
sys.path.insert(0, str(HERE))
import phase176_machine_audit as p176  # noqa: E402

PHASE = 187
CANONICAL_SOURCE_COMMIT = "578a777a85282ead6ebd50c4d59d4aa4096f01ab"
PHASE172_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
ENERGY_DEFINE = "COMPUTE_POTENTIAL_ENERGY"
ENERGY_CONFIG = "d3/Config_d3_claim_energy.sh"
BASE_CONFIG = "d3/Config_d3_production.sh"

class EnergyGateError(RuntimeError):
    pass

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8*1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def run_text(cmd: List[str], cwd: Path|None=None) -> str:
    return subprocess.run(cmd,cwd=cwd,check=True,capture_output=True,text=True).stdout.strip()

def version_text(cmd: List[str]) -> str|None:
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
        text=(p.stdout or p.stderr).strip()
        return text.splitlines()[0] if text else None
    except Exception:
        return None

def verify_commit_exists(repo: Path) -> None:
    p=subprocess.run(["git","-C",str(repo),"cat-file","-e",CANONICAL_SOURCE_COMMIT+"^{commit}"],capture_output=True)
    if p.returncode:
        raise EnergyGateError(f"canonical Phase187 source commit missing: {CANONICAL_SOURCE_COMMIT}")

def make_worktree(repo: Path,target: Path) -> None:
    if target.exists():
        raise EnergyGateError(f"refusing to reuse source worktree {target}")
    subprocess.run(["git","-C",str(repo),"worktree","add","--detach",str(target),CANONICAL_SOURCE_COMMIT],check=True)
    if run_text(["git","-C",str(target),"rev-parse","HEAD"]) != CANONICAL_SOURCE_COMMIT:
        raise EnergyGateError("wrong Phase187 source checkout")
    if run_text(["git","-C",str(target),"status","--porcelain"]):
        raise EnergyGateError("Phase187 source worktree is dirty")

def normalized_config(path: Path, remove_energy: bool) -> tuple[str,...]:
    out=[]
    for raw in path.read_text().splitlines():
        line=raw.strip()
        if not line or (line.startswith("#") and not line.startswith("#define")):
            continue
        if remove_energy and line == ENERGY_DEFINE:
            continue
        out.append(line)
    return tuple(out)

def verify_source_contract(tree: Path) -> Dict:
    if run_text(["git","-C",str(tree),"rev-parse","HEAD"]) != CANONICAL_SOURCE_COMMIT:
        raise EnergyGateError("wrong canonical source checkout")
    energy_cfg=tree/ENERGY_CONFIG
    base_cfg=tree/BASE_CONFIG
    energy_lines=energy_cfg.read_text().splitlines()
    if ENERGY_DEFINE not in energy_lines:
        raise EnergyGateError("claim-energy config lacks COMPUTE_POTENTIAL_ENERGY")
    if ENERGY_DEFINE in base_cfg.read_text().splitlines():
        raise EnergyGateError("production config unexpectedly enables claim-energy diagnostic")
    if normalized_config(energy_cfg,True) != normalized_config(base_cfg,False):
        raise EnergyGateError("claim-energy config differs from production by more than potential-energy diagnostic")
    lock=tree/"d3"/"production"/"phase172_lock.py"
    spec=importlib.util.spec_from_file_location("p187_phase172_lock",lock)
    if spec is None or spec.loader is None:
        raise EnergyGateError("cannot import Phase172 lock")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    raw,rows=mod.load()
    sha=hashlib.sha256(raw).hexdigest()
    if sha != PHASE172_MANIFEST_SHA256 or len(rows)!=127:
        raise EnergyGateError(f"Phase172 manifest mismatch sha={sha} rows={len(rows)}")
    return {
        "canonical_source_commit":CANONICAL_SOURCE_COMMIT,
        "phase172_manifest_sha256":sha,
        "phase172_manifest_rows":len(rows),
        "energy_config_sha256":sha256_file(energy_cfg),
        "base_config_sha256":sha256_file(base_cfg),
        "only_compile_delta":ENERGY_DEFINE,
    }

def replace_param(text: str, key: str, value: str) -> str:
    pat=re.compile(rf"(?m)^(\s*{re.escape(key)}\s+).*$")
    if not pat.search(text):
        raise EnergyGateError(f"parameter {key} missing from source params")
    return pat.sub(lambda m:m.group(1)+value,text,count=1)

def render_probe_params(base_params: Path, source: Path, outdir: Path, time_code: float) -> str:
    text=base_params.read_text()
    empty=outdir/"phase187_empty_output_times.txt"
    empty.write_text("")
    delta=max(1.0e-8, abs(time_code)*1.0e-12)
    text=replace_param(text,"InitCondFile",str(source.resolve()))
    text=replace_param(text,"OutputDir",str(outdir.resolve())+"/")
    if re.search(r"(?m)^\s*OutputListFilename\s+", text):
        text=replace_param(text,"OutputListFilename",str(empty.resolve()))
    text=replace_param(text,"TimeMax",f"{time_code+delta:.17g}")
    text=replace_param(text,"MaxSizeTimestep",f"{delta:.17g}")
    text=replace_param(text,"TimeLimitCPU","120")
    text=replace_param(text,"CpuTimeBetRestartFile","120")
    text=replace_param(text,"DM_InteractionCrossSection","0")
    return text

def first_energy_row(path: Path) -> Dict[str,float]:
    if not path.is_file():
        raise EnergyGateError(f"energy table missing: {path}")
    for raw in path.read_text(errors="replace").splitlines():
        fields=raw.split()
        if len(fields)<4:
            continue
        try:
            vals=[float(fields[i]) for i in range(4)]
        except ValueError:
            continue
        time,eint,epot,ekin=vals
        total=eint+epot+ekin
        if not all(math.isfinite(x) for x in (time,eint,epot,ekin,total)):
            raise EnergyGateError("non-finite energy statistic")
        if epot == 0.0:
            raise EnergyGateError("potential energy is exactly zero; diagnostic build is invalid for self-gravity")
        return {"time_code":time,"energy_internal":eint,"energy_potential":epot,"energy_kinetic":ekin,"energy_total":total}
    raise EnergyGateError(f"no parseable GIZMO energy row in {path}")

def launch_probe(executable: Path, base_params: Path, source: Path, time_code: float,
                 restart_flag: int, mpi_prefix: str, work_dir: Path) -> Dict:
    work_dir.mkdir(parents=True,exist_ok=False)
    params=work_dir/"params.txt"
    params.write_text(render_probe_params(base_params,source,work_dir,time_code))
    (work_dir/"stop").write_text("")
    cmd=shlex.split(mpi_prefix)+[str(executable.resolve()),str(params.resolve()),str(restart_flag)]
    log=work_dir/"probe.log"
    with log.open("w") as fh:
        p=subprocess.run(cmd,stdout=fh,stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise EnergyGateError(f"energy probe failed rc={p.returncode}: {log}")
    txt=log.read_text(errors="replace")
    if re.search(r"MPI_ABORT|ENDRUN issued|Fatal error",txt):
        raise EnergyGateError(f"fatal marker in energy probe: {log}")
    row=first_energy_row(work_dir/"energy.txt")
    row.update({
        "source":str(source.resolve()),"source_sha256":sha256_file(source),
        "params_sha256":sha256_file(params),"log_sha256":sha256_file(log),
        "restart_flag":restart_flag,
    })
    return row

def build_attest(args) -> Dict:
    repo=Path(args.source_repo).resolve()
    verify_commit_exists(repo)
    work=Path(args.work_dir).resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="phase187-energy-"))
    work.mkdir(parents=True,exist_ok=True)
    tree=work/"src"
    make_worktree(repo,tree)
    contract=verify_source_contract(tree)
    exe=p176.build(tree,ENERGY_CONFIG,"GIZMO_D3_CLAIM_ENERGY",args.jobs,args.systype)

    fixture=work/"M11.dat"
    subprocess.run([sys.executable,str(tree/"d3"/"phase141_generate_m11_ic.py"),
                    "--n-total","1000","--seed","187001","--output",str(fixture)],
                   cwd=tree/"d3",check=True)
    template=tree/"d3"/"params_m11_smoke.template"
    smoke=work/"smoke"
    smoke.mkdir()
    base=smoke/"base.params"
    text=template.read_text().replace("@IC@",str(fixture.resolve())).replace("@OUT@",str((smoke/"unused").resolve())).replace("@MODE@","-9")
    base.write_text(text)
    probe=launch_probe(exe,base,fixture,0.0,0,args.mpi_prefix,smoke/"probe")
    if probe["energy_potential"] >= 0.0:
        raise EnergyGateError(f"self-gravitating smoke potential is not negative: {probe['energy_potential']}")

    outdir=Path(args.binary_dir).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    final=outdir/"GIZMO_D3_CLAIM_ENERGY"
    if final.exists():
        raise EnergyGateError(f"refusing to overwrite {final}")
    shutil.copy2(exe,final)
    result={
        "phase":PHASE,"status":"PASS","kind":"source_pinned_exact_energy_postprocessor",
        **contract,
        "energy_executable":str(final),"energy_executable_sha256":sha256_file(final),
        "smoke":probe,
        "build":{"systype":args.systype,"jobs":args.jobs},
        "machine":{
            "platform":platform.platform(),"python":sys.version.split()[0],
            "cc":version_text(["cc","--version"]),"make":version_text(["make","--version"]),
        },
        "claim_boundary":"This executable is analysis-only. Production evolution remains on the Phase181 attested evidence binary.",
    }
    out=Path(args.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

def load_attestation(path: Path, executable: Path|None=None) -> Dict:
    if not path.is_file():
        raise EnergyGateError(f"Phase187 energy attestation missing: {path}")
    obj=json.loads(path.read_text())
    expected={"phase":PHASE,"status":"PASS","kind":"source_pinned_exact_energy_postprocessor",
              "canonical_source_commit":CANONICAL_SOURCE_COMMIT,
              "phase172_manifest_sha256":PHASE172_MANIFEST_SHA256,
              "only_compile_delta":ENERGY_DEFINE}
    bad={k:{"observed":obj.get(k),"expected":v} for k,v in expected.items() if obj.get(k)!=v}
    if bad:
        raise EnergyGateError(f"Phase187 energy attestation mismatch: {bad}")
    sha=obj.get("energy_executable_sha256")
    if not sha:
        raise EnergyGateError("energy attestation lacks executable SHA")
    if executable is not None:
        if not executable.is_file():
            raise EnergyGateError(f"energy executable missing: {executable}")
        obs=sha256_file(executable)
        if obs != sha:
            raise EnergyGateError(f"energy executable SHA mismatch: {obs} != {sha}")
    smoke=obj.get("smoke",{})
    if not isinstance(smoke,dict) or float(smoke.get("energy_potential",0.0)) >= 0.0:
        raise EnergyGateError("energy attestation lacks a negative-potential self-gravity smoke")
    return obj

def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("source-check"); s.add_argument("--source-repo",required=True)
    b=sub.add_parser("build-attest")
    b.add_argument("--source-repo",required=True); b.add_argument("--systype")
    b.add_argument("--jobs",type=int,default=2); b.add_argument("--mpi-prefix",default="")
    b.add_argument("--work-dir"); b.add_argument("--binary-dir",required=True); b.add_argument("--output",required=True)
    v=sub.add_parser("verify"); v.add_argument("--attestation",required=True); v.add_argument("--executable",required=True)
    return p

def main() -> int:
    args=parser().parse_args()
    try:
        if args.command=="source-check":
            repo=Path(args.source_repo).resolve(); verify_commit_exists(repo)
            with tempfile.TemporaryDirectory(prefix="phase187-source-") as td:
                tree=Path(td)/"src"; make_worktree(repo,tree); result=verify_source_contract(tree)
            print(json.dumps({"phase":PHASE,"status":"PASS",**result},indent=2,sort_keys=True)); return 0
        if args.command=="verify":
            obj=load_attestation(Path(args.attestation).resolve(),Path(args.executable).resolve())
            print(json.dumps({"phase":PHASE,"status":"PASS","energy_executable_sha256":obj["energy_executable_sha256"]},indent=2)); return 0
        if args.jobs <= 0: raise EnergyGateError("--jobs must be positive")
        result=build_attest(args); print(json.dumps(result,indent=2,sort_keys=True)); return 0
    except (EnergyGateError,p176.AuditError,OSError,ValueError,subprocess.CalledProcessError) as exc:
        print(json.dumps({"phase":PHASE,"status":"FAIL","error":str(exc)},indent=2),file=sys.stderr); return 2

if __name__=="__main__":
    raise SystemExit(main())
