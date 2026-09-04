#!/usr/bin/env python3
"""Phase179 safe-resume entry point for the audited claim-production binary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase175_safe_resume as resume  # noqa: E402

MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"


class GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_attestation(path: Path, executable: Path) -> dict:
    if not path.is_file():
        raise GateError(f"Phase179 machine attestation missing: {path}")
    obj = json.loads(path.read_text())
    expected = {
        "phase": 179,
        "status": "PASS",
        "manifest_sha256": MANIFEST_SHA256,
        "omp_num_threads_contract": 1,
        "claim_production_requires_live_audit": True,
    }
    bad = {k: {"observed": obj.get(k), "expected": v} for k, v in expected.items() if obj.get(k) != v}
    if bad:
        raise GateError(f"Phase179 attestation contract mismatch: {bad}")

    tests = {str(t.get("label")): t for t in obj.get("tests", [])}
    if set(tests) != {"d3_full", "standard_equal_label"}:
        raise GateError("Phase179 attestation lacks both physical-equivalence fixtures")
    for label, test in tests.items():
        for name in ("baseline_vs_candidate_production", "candidate_production_vs_audited"):
            if test.get("comparisons", {}).get(name, {}).get("status") != "PASS":
                raise GateError(f"{label}: {name} did not PASS")
        if test.get("audit", {}).get("status") != "PASS":
            raise GateError(f"{label}: live audit did not PASS")

    expected_sha = str(obj.get("claim_production_executable_sha256", ""))
    if len(expected_sha) != 64:
        raise GateError("attestation lacks audited claim-production executable SHA")
    if not executable.is_file():
        raise GateError(f"audited claim-production executable missing: {executable}")
    observed = sha256_file(executable)
    if observed != expected_sha:
        raise GateError(f"wrong executable: {observed} != attested {expected_sha}")
    return obj


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--machine-attestation", required=True)
    s = p.add_subparsers(dest="command", required=True)
    for name in ("dispatch", "inspect"):
        x = s.add_parser(name)
        x.add_argument("--run-id", required=True)
        x.add_argument("--executable", required=True)
        x.add_argument("--run-root", required=True)
        x.add_argument("--mpi-prefix", default="")
        x.add_argument("--mpi-tasks", type=int, default=None)
        if name == "dispatch":
            x.add_argument("--ic-root", required=True)
            x.add_argument("--max-mem-mb", type=int, default=3500)
            x.add_argument("--time-limit-cpu", type=int, default=170000)
            x.add_argument("--no-generate-ic", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    ap = Path(args.machine_attestation).resolve()
    exe = Path(args.executable).resolve()
    try:
        att = load_attestation(ap, exe)
        provenance = dict(att)
        provenance["executable_sha256"] = att["claim_production_executable_sha256"]
        provenance["phase179_attestation_sha256"] = sha256_file(ap)
        provenance["production_role"] = "audited_claim_production"

        def load_campaign():
            manifest_path, rows = resume.p173.materialize_manifest(Path(".phase179") / "phase172_manifest.csv")
            for row in rows:
                resume.p173.validate_row(row)
            return provenance, manifest_path, rows

        resume.load_campaign = load_campaign
        os.environ["OMP_NUM_THREADS"] = "1"
        return resume.dispatch(args) if args.command == "dispatch" else resume.inspect(args)
    except (GateError, resume.ResumeError, resume.p173.LaunchError, OSError, ValueError) as exc:
        print(json.dumps({"phase": 179, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
