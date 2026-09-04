#!/usr/bin/env python3
"""Phase179 audited-production provenance and physical-equivalence gate.

This gate repairs a preregistration plumbing contradiction before production:
Phase172 requires collision evidence for every run, while the Phase176 launcher
selected an audit-free executable. Phase179 therefore builds three binaries:

  baseline production  = last pre-Phase179 master, audit free
  candidate production = current exact physics blobs, audit free
  candidate audited    = same candidate config + SIDMX_D3_LIVE_AUDIT only

It requires physical Gadget-format records to be byte-identical across the
relevant comparisons for both a D3 unequal-mass cloud and an ordinary
positive-cross-section equal-label cloud. The audited candidate is the only
binary authorized for Phase179 claim-production dispatch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import phase176_machine_audit as p176  # noqa: E402

BASELINE_COMMIT = "76a310522ee0020581a8ca223269974f18aec8f6"
MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
AUDIT_DEFINE = "SIDMX_D3_LIVE_AUDIT"

# Git blob identities of every compiled SIDM source/config item allowed to
# affect Phase179 physics.  Analysis/workflow/docs may change without silently
# changing the production engine.
PHYSICS_BLOBS = {
    "sidm/sidm_core.c": "9d41bff5be67bc196b82a76f4e308534e6a536e7",
    "sidm/sidm_core_flux_computation.h": "f552221a48cbe0dbfcf5a2e348d54d77b9b8ce61",
    "sidm/sidmx_d3.h": "dc8a814fe4a3f21c89ef75a2d55f2e0afdda4577",
    "sidm/sidmx_d3_impl.h": "5f22bbb584e0ea89473099fc250dcff318dc31a3",
    "d3/Config_d3_production.sh": "068823c22e6fae68e3ddd08c3e3cec69a3877c2e",
    "d3/Config_d3_phase179_audit.sh": "dd3833dba40576c6e8f8442a5c3e1a625aa5ecee",
    "d3/production/phase172_lock.py": "735a9662dadedfcd112cbc03e5cfe7d7062989cc",
    "d3/phase141_generate_m11_ic.py": "48c382f31e9f4ad372cbd1927bd978b7795e8206",
    "d3/generate_d3_collision_cloud.py": "9b89a87dd1bdd6aba37f973bad231a9fcb59bcca",
    "d3/production/phase179_equal_label_cloud.py": "8e7d8c8f47d5f387b4713944a0409990baa31f0c",
}


class GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run_text(cmd, cwd=None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def blob_id(source: Path, rel: str) -> str:
    return run_text(["git", "-C", str(source), "hash-object", rel])


def verify_source(source: Path) -> dict:
    bad = {}
    for rel, expected in PHYSICS_BLOBS.items():
        path = source / rel
        if not path.is_file():
            bad[rel] = {"observed": None, "expected": expected}
            continue
        observed = blob_id(source, rel)
        if observed != expected:
            bad[rel] = {"observed": observed, "expected": expected}
    if bad:
        raise GateError(f"Phase179 physics blob contract mismatch: {bad}")

    prod = source / "d3/Config_d3_production.sh"
    audit = source / "d3/Config_d3_phase179_audit.sh"
    if AUDIT_DEFINE in prod.read_text().splitlines():
        raise GateError("production control config unexpectedly enables live audit")
    if AUDIT_DEFINE not in audit.read_text().splitlines():
        raise GateError("Phase179 audited config is missing live audit")
    if p176.normalized_config(prod, False) != p176.normalized_config(audit, True):
        raise GateError("Phase179 audit/production configs differ by more than live-audit token")

    raw, rows = __import__("phase172_lock").load()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    if manifest_sha != MANIFEST_SHA256 or len(rows) != 127:
        raise GateError(f"frozen manifest changed: sha={manifest_sha} rows={len(rows)}")
    return {
        "source_commit": run_text(["git", "-C", str(source), "rev-parse", "HEAD"]),
        "physics_blobs": dict(PHYSICS_BLOBS),
        "manifest_sha256": manifest_sha,
        "manifest_rows": len(rows),
    }


def export_ref(source: Path, ref: str, dest: Path) -> None:
    if dest.exists():
        raise GateError(f"refusing to reuse build tree: {dest}")
    dest.mkdir(parents=True)
    p1 = subprocess.Popen(["git", "-C", str(source), "archive", ref], stdout=subprocess.PIPE)
    assert p1.stdout is not None
    p2 = subprocess.run(["tar", "-x", "-C", str(dest)], stdin=p1.stdout)
    p1.stdout.close()
    rc = p1.wait()
    if rc or p2.returncode:
        raise GateError(f"failed to export source ref {ref}")


def build(tree: Path, config: str, exe_name: str, jobs: int, systype: str | None) -> Path:
    p176.set_systype(tree, systype)
    shutil.copyfile(tree / config, tree / "Config.sh")
    subprocess.run(["make", f"-j{jobs}", "CONFIG=Config.sh", f"EXEC={exe_name}"], cwd=tree, check=True)
    exe = tree / exe_name
    if not exe.is_file():
        raise GateError(f"build did not produce {exe}")
    return exe


def make_params(template: Path, ic: Path, outdir: Path, mode: float) -> str:
    text = template.read_text()
    replacements = {
        "@IC@": str(ic.resolve()),
        "@OUT@": str(outdir.resolve()),
        "@MODE@": f"{mode:.17g}",
        "TimeOfFirstSnapshot         0.00010": "TimeOfFirstSnapshot         0.00004",
        "TimeMax                      0.00010": "TimeMax                      0.00004",
        "MaxSizeTimestep              0.00002": "MaxSizeTimestep              0.000004",
        "BoxSize                      2000.0": "BoxSize                      20.0",
    }
    for old, new in replacements.items():
        if old not in text:
            raise GateError(f"parameter template changed; missing {old!r}")
        text = text.replace(old, new)
    return text


def launch(exe: Path, params: Path, mpi_prefix: str, log: Path) -> None:
    cmd = shlex.split(mpi_prefix) + [str(exe.resolve()), str(params.resolve()), "0"]
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    with log.open("w") as fh:
        rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True, env=env).returncode
    text = log.read_text(errors="replace")
    if rc or "Simulation ends." not in text or re.search(r"MPI_ABORT|ENDRUN issued|Fatal error", text):
        raise GateError(f"GIZMO execution failed: {exe.name}; see {log}")


def audit_check(source: Path, log: Path, mode: int, signal: tuple[str, ...]) -> dict:
    cmd = [sys.executable, str(source / "d3/check_d3_live_audit.py"), str(log), "--mode", str(mode),
           "--min-expected", "1.0", "--max-conservation-residual", "1e-12",
           "--max-probability", "0.2"]
    if signal:
        cmd += ["--signal-channels", *signal]
    p = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def run_case(source: Path, work: Path, label: str, ic: Path, mode: float,
             binaries: dict[str, Path], mpi_prefix: str, signal: tuple[str, ...]) -> dict:
    case = work / label
    case.mkdir(parents=True)
    template = source / "d3/params_m11_smoke.template"
    outputs = {}
    logs = {}
    for name, exe in binaries.items():
        outdir = case / name
        outdir.mkdir()
        params = case / f"{name}.params"
        params.write_text(make_params(template, ic, outdir, mode))
        log = case / f"{name}.log"
        launch(exe, params, mpi_prefix, log)
        outputs[name] = p176.latest_snapshot(outdir)
        logs[name] = log

    comparisons = {
        "baseline_vs_candidate_production": p176.compare_physical(outputs["baseline"], outputs["production"]),
        "candidate_production_vs_audited": p176.compare_physical(outputs["production"], outputs["audit"]),
    }
    mode_tag = int(round(-mode)) if mode < 0 else 10
    audit = audit_check(source, logs["audit"], mode_tag, signal)
    return {
        "label": label,
        "runtime_interaction_parameter": mode,
        "audit_mode": mode_tag,
        "comparisons": comparisons,
        "audit": audit,
        "logs": {k: str(v) for k, v in logs.items()},
    }


def build_attestation(args) -> dict:
    source = Path(args.source_tree).resolve()
    contract = verify_source(source)
    # The baseline is deliberately the final master immediately before the
    # Phase179 audit-source repair. Require it to exist in local git history.
    subprocess.run(["git", "-C", str(source), "cat-file", "-e", f"{BASELINE_COMMIT}^{{commit}}"], check=True)

    work = Path(args.work_dir).resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="phase179-"))
    work.mkdir(parents=True, exist_ok=True)
    base_tree, prod_tree, audit_tree = work / "src-base", work / "src-prod", work / "src-audit"
    export_ref(source, BASELINE_COMMIT, base_tree)
    export_ref(source, "HEAD", prod_tree)
    export_ref(source, "HEAD", audit_tree)

    baseline = build(base_tree, "d3/Config_d3_production.sh", "GIZMO_D3_BASELINE", args.jobs, args.systype)
    production = build(prod_tree, "d3/Config_d3_production.sh", "GIZMO_D3_PROD179", args.jobs, args.systype)
    audited = build(audit_tree, "d3/Config_d3_phase179_audit.sh", "GIZMO_D3_AUDIT179", args.jobs, args.systype)

    fixture = work / "fixtures"
    fixture.mkdir()
    d3_ic = fixture / "d3_ratio3.dat"
    equal_ic = fixture / "equal_label.dat"
    subprocess.run([sys.executable, str(source / "d3/generate_d3_collision_cloud.py"),
                    "--n-total", "1000", "--seed", "179101", "--radius-kpc", "1.0",
                    "--total-mass-msun", "1.0e10", "--stream-speed-kms", "100",
                    "--dispersion-kms", "100", "--output", str(d3_ic)], cwd=source / "d3", check=True)
    subprocess.run([sys.executable, str(source / "d3/production/phase179_equal_label_cloud.py"),
                    "--n-total", "1000", "--seed", "179102", "--radius-kpc", "1.0",
                    "--total-mass-msun", "1.0e10", "--stream-speed-kms", "100",
                    "--dispersion-kms", "100", "--output", str(equal_ic)], cwd=source, check=True)

    bins = {"baseline": baseline, "production": production, "audit": audited}
    tests = [
        run_case(source, work, "d3_full", d3_ic, -1.0, bins, args.mpi_prefix, ("HL",)),
        run_case(source, work, "standard_equal_label", equal_ic, 1.125, bins, args.mpi_prefix, ("HL",)),
    ]

    binary_dir = Path(args.binary_dir).resolve()
    binary_dir.mkdir(parents=True, exist_ok=True)
    prod_final = binary_dir / "GIZMO_D3_PROD179"
    audit_final = binary_dir / "GIZMO_D3_AUDIT179"
    for src, dst in ((production, prod_final), (audited, audit_final)):
        if dst.exists():
            raise GateError(f"refusing to overwrite binary: {dst}")
        shutil.copy2(src, dst)

    result = {
        "phase": 179,
        "status": "PASS",
        "gate": "audited claim-production binary with baseline + audit physical equivalence",
        "baseline_commit": BASELINE_COMMIT,
        **contract,
        "omp_num_threads_contract": 1,
        "control_executable": str(prod_final),
        "control_executable_sha256": sha256_file(prod_final),
        "claim_production_executable": str(audit_final),
        "claim_production_executable_sha256": sha256_file(audit_final),
        "claim_production_requires_live_audit": True,
        "tests": tests,
    }
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({**result, "attestation": str(out), "attestation_sha256": sha256_file(out)}, indent=2, sort_keys=True))
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--systype")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--mpi-prefix", default="")
    ap.add_argument("--work-dir")
    ap.add_argument("--binary-dir", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    try:
        if args.jobs <= 0:
            raise GateError("jobs must be positive")
        build_attestation(args)
        return 0
    except (GateError, p176.AuditError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"PHASE179 MACHINE GATE FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
