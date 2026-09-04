#!/usr/bin/env python3
"""Phase181 target-machine evidence-binary attestation.

Phase176 correctly proved that live auditing is physically non-invasive for a
D3 sentinel run, but then designated the audit-free executable for production.
Phase172 simultaneously requires collision evidence for every run.  Phase181
repairs that contract without changing frozen physics or acceptance thresholds:

1. rebuild the exact canonical Phase181 physics source twice on the target;
2. audit-on build becomes GIZMO_D3_EVIDENCE;
3. audit-off build is a control only;
4. prove byte-identical GADGET physical records for both a full D3 sentinel run
   and the ordinary +1.125 cm^2/g equal-label path;
5. attest the evidence executable SHA for the scheduler/safe-resume bridge.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
D3 = HERE.parent
sys.path.insert(0, str(HERE))
import phase176_machine_audit as p176  # noqa: E402

PHASE = 181
CANONICAL_SOURCE_COMMIT = "1e7df731d83897f033255e81fc172473015f0c9d"
PHASE172_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
AUDIT_DEFINE = "SIDMX_D3_LIVE_AUDIT"
REQUIRED_RECORDS = ("positions", "velocities", "particle_ids", "masses")


class EvidenceGateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_text(cmd: List[str], cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def version_text(cmd: List[str]) -> str | None:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        text = (p.stdout or p.stderr).strip()
        return text.splitlines()[0] if text else None
    except Exception:
        return None


def verify_commit_exists(repo: Path) -> None:
    p = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", CANONICAL_SOURCE_COMMIT + "^{commit}"],
        capture_output=True,
    )
    if p.returncode != 0:
        raise EvidenceGateError(f"canonical Phase181 source commit missing: {CANONICAL_SOURCE_COMMIT}")


def make_worktree(repo: Path, target: Path) -> None:
    if target.exists():
        raise EvidenceGateError(f"refusing to reuse source worktree {target}")
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(target), CANONICAL_SOURCE_COMMIT],
        check=True,
    )
    head = run_text(["git", "-C", str(target), "rev-parse", "HEAD"])
    if head != CANONICAL_SOURCE_COMMIT:
        raise EvidenceGateError(f"worktree source drift: {head}")
    if run_text(["git", "-C", str(target), "status", "--porcelain"]):
        raise EvidenceGateError("canonical worktree is dirty before build")


def normalized_config(path: Path, remove_audit: bool) -> tuple[str, ...]:
    out = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or (line.startswith("#") and not line.startswith("#define")):
            continue
        if remove_audit and line == AUDIT_DEFINE:
            continue
        out.append(line)
    return tuple(out)


def verify_source_contract(tree: Path) -> Dict:
    if run_text(["git", "-C", str(tree), "rev-parse", "HEAD"]) != CANONICAL_SOURCE_COMMIT:
        raise EvidenceGateError("wrong canonical source checkout")
    audit_cfg = tree / "d3" / "Config_d3_ci.sh"
    control_cfg = tree / "d3" / "Config_d3_production.sh"
    if AUDIT_DEFINE not in audit_cfg.read_text().splitlines():
        raise EvidenceGateError("audit config does not enable live audit")
    if AUDIT_DEFINE in control_cfg.read_text().splitlines():
        raise EvidenceGateError("control config unexpectedly enables live audit")
    if normalized_config(audit_cfg, True) != normalized_config(control_cfg, False):
        raise EvidenceGateError("evidence/control configs differ by more than live-audit token")

    lock = tree / "d3" / "production" / "phase172_lock.py"
    spec = importlib.util.spec_from_file_location("p181_phase172_lock", lock)
    if spec is None or spec.loader is None:
        raise EvidenceGateError("cannot import Phase172 lock from canonical source")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw, rows = mod.load()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    if manifest_sha != PHASE172_MANIFEST_SHA256 or len(rows) != 127:
        raise EvidenceGateError(f"Phase172 frozen manifest mismatch sha={manifest_sha} rows={len(rows)}")
    return {
        "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
        "audit_config_sha256": sha256_file(audit_cfg),
        "control_config_sha256": sha256_file(control_cfg),
        "phase172_manifest_sha256": manifest_sha,
        "phase172_manifest_rows": len(rows),
    }


def render_params(template: Path, ic: Path, outdir: Path, mode: str) -> str:
    text = template.read_text()
    replacements = {
        "@IC@": str(ic.resolve()),
        "@OUT@": str(outdir.resolve()),
        "@MODE@": mode,
        "TimeOfFirstSnapshot         0.00010": "TimeOfFirstSnapshot         0.00004",
        "TimeMax                      0.00010": "TimeMax                      0.00004",
        "MaxSizeTimestep              0.00002": "MaxSizeTimestep              0.000004",
        "BoxSize                      2000.0": "BoxSize                      20.0",
    }
    for old, new in replacements.items():
        if old not in text:
            raise EvidenceGateError(f"smoke template changed; missing {old!r}")
        text = text.replace(old, new)
    return text


def verify_log(path: Path, *, audit: bool, mode: int) -> None:
    text = path.read_text(errors="replace")
    if not re.search(r"Simulation ends\.", text):
        raise EvidenceGateError(f"simulation did not reach final marker: {path}")
    if re.search(r"MPI_ABORT|ENDRUN issued|Fatal error", text):
        raise EvidenceGateError(f"fatal marker in {path}")
    has = bool(re.search(rf"SIDMx-D3 AUDIT .*mode={mode}(?:\s|$)", text))
    if audit and not has:
        raise EvidenceGateError(f"audit executable did not emit required mode={mode}: {path}")
    if not audit and "SIDMx-D3 AUDIT" in text:
        raise EvidenceGateError(f"audit-free control emitted live audit rows: {path}")


def equivalence_pair(
    root: Path,
    audit_exe: Path,
    control_exe: Path,
    template: Path,
    ic: Path,
    mode_text: str,
    audit_mode: int,
    mpi_prefix: str,
    label: str,
) -> Dict:
    eq = root / label
    ao, co = eq / "audit", eq / "control"
    ao.mkdir(parents=True)
    co.mkdir(parents=True)
    ap, cp = eq / "audit.params", eq / "control.params"
    ap.write_text(render_params(template, ic, ao, mode_text))
    cp.write_text(render_params(template, ic, co, mode_text))
    alog, clog = eq / "audit.log", eq / "control.log"
    p176.launch(audit_exe, ap, mpi_prefix, alog)
    p176.launch(control_exe, cp, mpi_prefix, clog)
    verify_log(alog, audit=True, mode=audit_mode)
    verify_log(clog, audit=False, mode=audit_mode)
    result = p176.compare_physical(p176.latest_snapshot(ao), p176.latest_snapshot(co))
    if result.get("status") != "PASS":
        raise EvidenceGateError(f"{label}: physical equivalence did not PASS")
    if tuple(x.get("name") for x in result.get("records_checked", [])) != REQUIRED_RECORDS:
        raise EvidenceGateError(f"{label}: physical record comparison incomplete")
    result.update({
        "label": label,
        "interaction_parameter": float(mode_text),
        "audit_mode": audit_mode,
        "audit_log_sha256": sha256_file(alog),
        "control_log_sha256": sha256_file(clog),
    })
    return result


def build_attest(args) -> Dict:
    repo = Path(args.source_repo).resolve()
    verify_commit_exists(repo)
    work = Path(args.work_dir).resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="phase181-"))
    work.mkdir(parents=True, exist_ok=True)
    audit_tree, control_tree = work / "src-audit", work / "src-control"
    make_worktree(repo, audit_tree)
    make_worktree(repo, control_tree)
    contract = verify_source_contract(audit_tree)
    verify_source_contract(control_tree)

    audit_exe = p176.build(audit_tree, "d3/Config_d3_ci.sh", "GIZMO_D3_EVIDENCE", args.jobs, args.systype)
    control_exe = p176.build(control_tree, "d3/Config_d3_production.sh", "GIZMO_D3_CONTROL", args.jobs, args.systype)
    if sha256_file(audit_exe) == sha256_file(control_exe):
        raise EvidenceGateError("evidence and control executables are unexpectedly byte-identical")

    fixtures = work / "fixtures"
    fixtures.mkdir()
    d3_ic = fixtures / "d3_ratio3.dat"
    subprocess.run([
        sys.executable, str(audit_tree / "d3" / "generate_d3_collision_cloud.py"),
        "--n-total", "1000", "--seed", "181101", "--radius-kpc", "1.0",
        "--total-mass-msun", "1.0e11", "--stream-speed-kms", "100",
        "--dispersion-kms", "100", "--output", str(d3_ic),
    ], cwd=audit_tree / "d3", check=True)

    equal_ic = fixtures / "equal_ratio1.dat"
    equal_gen = D3 / "phase181_generate_equal_collision_cloud.py"
    if not equal_gen.is_file():
        raise EvidenceGateError(f"Phase181 equal-mass fixture generator missing: {equal_gen}")
    subprocess.run([
        sys.executable, str(equal_gen), "--n-total", "1000", "--seed", "181102",
        "--radius-kpc", "1.0", "--total-mass-msun", "1.0e11",
        "--stream-speed-kms", "100", "--dispersion-kms", "100", "--output", str(equal_ic),
    ], cwd=D3, check=True)

    template = audit_tree / "d3" / "params_m11_smoke.template"
    d3_eq = equivalence_pair(work, audit_exe, control_exe, template, d3_ic, "-1", 1, args.mpi_prefix, "d3_full")
    std_eq = equivalence_pair(work, audit_exe, control_exe, template, equal_ic, "1.125", 10, args.mpi_prefix, "standard_equal_label")

    outdir = Path(args.binary_dir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    evidence_final = outdir / "GIZMO_D3_EVIDENCE"
    control_final = outdir / "GIZMO_D3_CONTROL"
    for src, dst in ((audit_exe, evidence_final), (control_exe, control_final)):
        if dst.exists():
            raise EvidenceGateError(f"refusing to overwrite attested binary {dst}")
        shutil.copy2(src, dst)

    result = {
        "phase": PHASE,
        "status": "PASS",
        "gate": "target-machine audit-enabled evidence executable with two-path physical equivalence",
        "build_provenance": "phase181_build_attest",
        **contract,
        "evidence_executable": str(evidence_final),
        "evidence_executable_sha256": sha256_file(evidence_final),
        "control_executable": str(control_final),
        "control_executable_sha256": sha256_file(control_final),
        "equal_fixture_generator_sha256": sha256_file(equal_gen),
        "equivalence": {
            "d3_full": d3_eq,
            "standard_equal_label": std_eq,
        },
        "build": {"systype": args.systype, "jobs": args.jobs},
        "machine": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "cc": version_text(["cc", "--version"]),
            "make": version_text(["make", "--version"]),
            "mpi": version_text(shlex.split(args.mpi_prefix)[:1] + ["--version"]) if args.mpi_prefix.strip() else None,
        },
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({**result, "attestation": str(output), "attestation_sha256": sha256_file(output)}, indent=2, sort_keys=True))
    return result


def load_attestation(path: Path, executable: Path | None = None) -> Dict:
    if not path.is_file():
        raise EvidenceGateError(f"Phase181 machine attestation missing: {path}")
    obj = json.loads(path.read_text())
    expected = {
        "phase": PHASE,
        "status": "PASS",
        "build_provenance": "phase181_build_attest",
        "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
        "phase172_manifest_sha256": PHASE172_MANIFEST_SHA256,
    }
    bad = {k: {"observed": obj.get(k), "expected": v} for k, v in expected.items() if obj.get(k) != v}
    if bad:
        raise EvidenceGateError(f"Phase181 attestation mismatch: {bad}")
    for label in ("d3_full", "standard_equal_label"):
        eq = obj.get("equivalence", {}).get(label, {})
        if eq.get("status") != "PASS":
            raise EvidenceGateError(f"Phase181 {label} equivalence is not PASS")
        if tuple(x.get("name") for x in eq.get("records_checked", [])) != REQUIRED_RECORDS:
            raise EvidenceGateError(f"Phase181 {label} equivalence record list incomplete")
    expected_sha = obj.get("evidence_executable_sha256")
    if not expected_sha:
        raise EvidenceGateError("attestation lacks evidence executable SHA")
    if executable is not None:
        if not executable.is_file():
            raise EvidenceGateError(f"evidence executable missing: {executable}")
        observed = sha256_file(executable)
        if observed != expected_sha:
            raise EvidenceGateError(f"executable is not attested evidence binary: {observed} != {expected_sha}")
    return obj


def provenance_from_attestation(path: Path, executable: Path | None = None) -> Dict:
    att = load_attestation(path, executable)
    prov = dict(att)
    prov["executable_sha256"] = att["evidence_executable_sha256"]
    prov["phase181_attestation_sha256"] = sha256_file(path)
    return prov


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("source-check")
    s.add_argument("--source-repo", required=True)
    a = sub.add_parser("build-attest")
    a.add_argument("--source-repo", required=True)
    a.add_argument("--systype")
    a.add_argument("--jobs", type=int, default=2)
    a.add_argument("--mpi-prefix", default="")
    a.add_argument("--work-dir")
    a.add_argument("--binary-dir", required=True)
    a.add_argument("--output", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--attestation", required=True)
    v.add_argument("--executable", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "source-check":
            repo = Path(args.source_repo).resolve()
            verify_commit_exists(repo)
            with tempfile.TemporaryDirectory(prefix="phase181-source-") as td:
                tree = Path(td) / "src"
                make_worktree(repo, tree)
                result = verify_source_contract(tree)
            print(json.dumps({"phase": PHASE, "status": "PASS", **result}, indent=2, sort_keys=True))
            return 0
        if args.command == "verify":
            att = load_attestation(Path(args.attestation).resolve(), Path(args.executable).resolve())
            print(json.dumps({"phase": PHASE, "status": "PASS", "evidence_executable_sha256": att["evidence_executable_sha256"]}, indent=2))
            return 0
        if args.jobs <= 0:
            raise EvidenceGateError("--jobs must be positive")
        build_attest(args)
        return 0
    except (EvidenceGateError, p176.AuditError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
