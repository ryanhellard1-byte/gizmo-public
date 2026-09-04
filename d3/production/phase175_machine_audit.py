#!/usr/bin/env python3
"""Phase 175 target-machine provenance and audit-free equivalence gate.

This gate binds a locally built production executable to the exact source/config
that passed the CI audit-on vs audit-off equivalence test, then reruns the same
small deterministic physical-record comparison on the target machine. It does
not require the target executable to have the same bytes as the Ubuntu CI build.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
DEFAULT_REFERENCE = HERE / "phase175_ci_equivalence_reference.json"
AUDIT_DEFINE = "#define SIDMX_D3_LIVE_AUDIT"
EXPECTED = {
    "source_commit": "dc93bca31b19135a1f8510e838f23abc850869fb",
    "workflow_run_id": 33850670457,
    "artifact_id": 9928241676,
    "artifact_digest": "sha256:401a92db93b2d68f0d5fe9a84e3053bb47191b0bbbfb5385ae2538279d06dc05",
    "production_executable_sha256": "f11e011b9420ebe829eb77295a09c0d525dd6ae8c0411173231911cacfb98dc0",
    "audit_executable_sha256": "760ed6ad69ca3e88295acbd24b2c4bfc1b2f1187df826ae7d1aa3c6d4df79d88",
    "production_config_sha256": "887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329",
    "phase172_manifest_sha256": "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d",
    "equivalence_status": "PASS",
    "comparison": "GADGET format-1 physical record byte equality; header/provenance ignored",
}
REQUIRED_RECORDS = ("positions", "velocities", "particle_ids", "masses")


class AuditError(RuntimeError):
    pass


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def run_text(cmd: List[str], cwd: Path | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return p.stdout.strip()


def load_reference(path: Path) -> Dict:
    obj = json.loads(path.read_text())
    bad = {k: {"observed": obj.get(k), "expected": v} for k, v in EXPECTED.items() if obj.get(k) != v}
    if bad:
        raise AuditError(f"canonical CI reference mismatch: {bad}")
    if tuple(obj.get("records_checked", ())) != REQUIRED_RECORDS:
        raise AuditError("canonical CI reference physical-record contract changed")
    return obj


def exact_source_commit(source_tree: Path, reference: Dict) -> str:
    head = run_text(["git", "-C", str(source_tree), "rev-parse", "HEAD"])
    if head != reference["source_commit"]:
        raise AuditError(f"source tree must be detached/checked out at canonical commit {reference['source_commit']}; observed {head}")
    dirty = subprocess.run(["git", "-C", str(source_tree), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout.strip()
    if dirty:
        raise AuditError("canonical source tree is dirty; target build provenance would be ambiguous")
    return head


def normalized_config(path: Path, remove_audit: bool) -> Tuple[str, ...]:
    lines = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or (line.startswith("#") and not line.startswith("#define")):
            continue
        if remove_audit and line == AUDIT_DEFINE:
            continue
        lines.append(line)
    return tuple(lines)


def verify_source_contract(source_tree: Path, reference: Dict) -> Dict:
    prod_cfg = source_tree / "d3/Config_d3_production.sh"
    audit_cfg = source_tree / "d3/Config_d3_ci.sh"
    for p in (prod_cfg, audit_cfg):
        if not p.is_file():
            raise AuditError(f"missing canonical build config: {p}")
    prod_sha = sha256_file(prod_cfg)
    if prod_sha != reference["production_config_sha256"]:
        raise AuditError(f"production config SHA mismatch: {prod_sha}")
    if AUDIT_DEFINE in prod_cfg.read_text().splitlines():
        raise AuditError("production config unexpectedly enables SIDMX_D3_LIVE_AUDIT")
    if AUDIT_DEFINE not in audit_cfg.read_text().splitlines():
        raise AuditError("commissioning config is missing SIDMX_D3_LIVE_AUDIT")
    if normalized_config(prod_cfg, False) != normalized_config(audit_cfg, True):
        raise AuditError("audit and production configs differ by more than SIDMX_D3_LIVE_AUDIT")

    lock_path = source_tree / "d3/production/phase172_lock.py"
    if not lock_path.is_file():
        raise AuditError("canonical Phase172 lock module is missing")
    spec = importlib.util.spec_from_file_location("phase172_lock_target", lock_path)
    if spec is None or spec.loader is None:
        raise AuditError("cannot load canonical Phase172 lock module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw, rows = mod.load()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    if manifest_sha != reference["phase172_manifest_sha256"]:
        raise AuditError(f"Phase172 manifest SHA mismatch: {manifest_sha}")
    if len(rows) != 127:
        raise AuditError(f"expected 127 frozen rows, observed {len(rows)}")
    return {"production_config_sha256": prod_sha, "phase172_manifest_sha256": manifest_sha, "manifest_rows": len(rows)}


def make_params(template: Path, ic: Path, outdir: Path) -> str:
    text = template.read_text()
    replacements = {
        "@IC@": str(ic.resolve()),
        "@OUT@": str(outdir.resolve()),
        "@MODE@": "-1",
        "TimeOfFirstSnapshot         0.00010": "TimeOfFirstSnapshot         0.00004",
        "TimeMax                      0.00010": "TimeMax                      0.00004",
        "MaxSizeTimestep              0.00002": "MaxSizeTimestep              0.000004",
        "BoxSize                      2000.0": "BoxSize                      20.0",
    }
    for old, new in replacements.items():
        if old not in text:
            raise AuditError(f"equivalence parameter template contract changed; missing {old!r}")
        text = text.replace(old, new)
    return text


def launch(executable: Path, params: Path, mpi_prefix: str, log: Path) -> None:
    cmd = shlex.split(mpi_prefix) + [str(executable.resolve()), str(params.resolve()), "0"]
    with log.open("w") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, text=True)
    text = log.read_text(errors="replace")
    if proc.returncode != 0:
        raise AuditError(f"{executable.name} returned {proc.returncode}; see {log}")
    if not re.search(r"Simulation ends\.", text):
        raise AuditError(f"{executable.name} has no normal completion marker")
    if re.search(r"MPI_ABORT|ENDRUN issued", text):
        raise AuditError(f"{executable.name} emitted a fatal marker")


def latest_snapshot(outdir: Path) -> Path:
    hits = sorted(p for p in outdir.glob("snapshot*") if p.is_file())
    if not hits:
        raise AuditError(f"no output snapshot found in {outdir}")
    return hits[-1]


def read_records(path: Path) -> List[bytes]:
    import struct
    data = path.read_bytes()
    out: List[bytes] = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise AuditError(f"truncated record prefix in {path}")
        n = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        payload = data[pos:pos+n]
        pos += n
        if pos + 4 > len(data):
            raise AuditError(f"truncated record suffix in {path}")
        m = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if m != n:
            raise AuditError(f"record marker mismatch in {path}: {n} != {m}")
        out.append(payload)
    return out


def compare_physical(audit_snapshot: Path, prod_snapshot: Path) -> Dict:
    ar, pr = read_records(audit_snapshot), read_records(prod_snapshot)
    if len(ar) < 5 or len(pr) < 5:
        raise AuditError(f"too few GADGET records: audit={len(ar)} prod={len(pr)}")
    checks = ((1, "positions"), (2, "velocities"), (3, "particle_ids"), (4, "masses"))
    result = {
        "status": "PASS",
        "comparison": EXPECTED["comparison"],
        "audit_snapshot_sha256": sha256_file(audit_snapshot),
        "production_snapshot_sha256": sha256_file(prod_snapshot),
        "audit_record_sizes": [len(x) for x in ar],
        "production_record_sizes": [len(x) for x in pr],
        "records_checked": [],
    }
    for idx, name in checks:
        if len(ar[idx]) != len(pr[idx]):
            raise AuditError(f"{name} record size mismatch")
        ah, ph = hashlib.sha256(ar[idx]).hexdigest(), hashlib.sha256(pr[idx]).hexdigest()
        if ah != ph:
            raise AuditError(f"{name} physical record differs: {ah} != {ph}")
        result["records_checked"].append({"index": idx, "name": name, "bytes": len(ar[idx]), "sha256": ah})
    return result


def version_text(cmd: List[str]) -> str | None:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        text = (p.stdout or p.stderr).strip()
        return text.splitlines()[0] if text else None
    except Exception:
        return None


def attest(args: argparse.Namespace) -> Dict:
    reference_path = Path(args.reference).resolve()
    reference = load_reference(reference_path)
    source_tree = Path(args.source_tree).resolve()
    production = Path(args.production_executable).resolve()
    audit = Path(args.audit_executable).resolve()
    for p in (production, audit):
        if not p.is_file():
            raise AuditError(f"executable missing: {p}")

    source_head = exact_source_commit(source_tree, reference)
    source_contract = verify_source_contract(source_tree, reference)
    prod_sha, audit_sha = sha256_file(production), sha256_file(audit)
    if prod_sha == audit_sha:
        raise AuditError("audit and production executables are byte-identical; audit-free build separation was not established")

    generator = source_tree / "d3/generate_d3_collision_cloud.py"
    template = source_tree / "d3/params_m11_smoke.template"
    if not generator.is_file() or not template.is_file():
        raise AuditError("canonical equivalence generator/template missing")

    keep = Path(args.work_dir).resolve() if args.work_dir else None
    temp_ctx = None
    if keep is None:
        temp_ctx = tempfile.TemporaryDirectory(prefix="phase175-")
        work = Path(temp_ctx.name)
    else:
        work = keep
        work.mkdir(parents=True, exist_ok=True)
    audit_out, prod_out = work / "audit", work / "prod"
    audit_out.mkdir(parents=True, exist_ok=True)
    prod_out.mkdir(parents=True, exist_ok=True)
    ic = work / "D3_equiv_cloud.dat"

    gen_cmd = [sys.executable, str(generator), "--n-total", "1000", "--seed", "173001", "--radius-kpc", "1.0", "--total-mass-msun", "1.0e11", "--stream-speed-kms", "100", "--dispersion-kms", "100", "--output", str(ic)]
    subprocess.run(gen_cmd, cwd=source_tree, check=True)
    audit_params, prod_params = work / "audit.params", work / "prod.params"
    audit_params.write_text(make_params(template, ic, audit_out))
    prod_params.write_text(make_params(template, ic, prod_out))
    audit_log, prod_log = work / "audit.log", work / "prod.log"
    launch(audit, audit_params, args.mpi_prefix, audit_log)
    launch(production, prod_params, args.mpi_prefix, prod_log)
    equivalence = compare_physical(latest_snapshot(audit_out), latest_snapshot(prod_out))

    result = {
        "phase": 175,
        "status": "PASS",
        "gate": "target-machine audit-enabled vs audit-free physical equivalence",
        "canonical_ci_reference_sha256": sha256_file(reference_path),
        "canonical_source_commit": reference["source_commit"],
        "target_source_commit": source_head,
        **source_contract,
        "production_executable": str(production),
        "production_executable_sha256": prod_sha,
        "audit_executable": str(audit),
        "audit_executable_sha256": audit_sha,
        "ci_production_executable_sha256": reference["production_executable_sha256"],
        "ci_binary_sha_match": prod_sha == reference["production_executable_sha256"],
        "equivalence": equivalence,
        "machine": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "mpi": version_text(shlex.split(args.mpi_prefix)[:1] + ["--version"]) if args.mpi_prefix.strip() else None,
            "cc": version_text(["cc", "--version"]),
        },
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    result["attestation_path"] = str(output)
    result["attestation_sha256"] = sha256_file(output)
    if temp_ctx is not None:
        temp_ctx.cleanup()
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reference-check")
    r.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    a = sub.add_parser("attest")
    a.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    a.add_argument("--source-tree", required=True)
    a.add_argument("--production-executable", required=True)
    a.add_argument("--audit-executable", required=True)
    a.add_argument("--mpi-prefix", default="")
    a.add_argument("--work-dir")
    a.add_argument("--output", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.cmd == "reference-check":
            ref = load_reference(Path(args.reference))
            print(json.dumps({"phase": 175, "status": "PASS", "reference": ref}, indent=2))
            return 0
        result = attest(args)
        print(json.dumps(result, indent=2))
        return 0
    except (AuditError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"PHASE175 MACHINE AUDIT FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
