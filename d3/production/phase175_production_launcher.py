#!/usr/bin/env python3
"""Phase 175 machine-attested launcher for the frozen Phase172 campaign.

Phase173 remains the frozen run-row/render/execute engine. Phase175 replaces its
obsolete GitHub-hosted executable lock with a target-machine attestation created
by phase175_machine_audit.py. The physics manifest itself is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase173_production_launcher as core  # noqa: E402

CANONICAL_SOURCE_COMMIT = "dc93bca31b19135a1f8510e838f23abc850869fb"
CANONICAL_CONFIG_SHA256 = "887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329"
CANONICAL_MANIFEST_SHA256 = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"


class GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_attestation(path: Path, executable: Path | None = None) -> dict:
    if not path.is_file():
        raise GateError(f"Phase175 machine attestation missing: {path}")
    obj = json.loads(path.read_text())
    expected = {
        "phase": 175,
        "status": "PASS",
        "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
        "target_source_commit": CANONICAL_SOURCE_COMMIT,
        "production_config_sha256": CANONICAL_CONFIG_SHA256,
        "phase172_manifest_sha256": CANONICAL_MANIFEST_SHA256,
    }
    bad = {k: {"observed": obj.get(k), "expected": v} for k, v in expected.items() if obj.get(k) != v}
    if bad:
        raise GateError(f"Phase175 machine-attestation contract mismatch: {bad}")
    eq = obj.get("equivalence", {})
    if eq.get("status") != "PASS":
        raise GateError("target-machine audit/production physical equivalence did not PASS")
    names = tuple(x.get("name") for x in eq.get("records_checked", []))
    if names != ("positions", "velocities", "particle_ids", "masses"):
        raise GateError(f"target-machine physical-record contract incomplete: {names}")
    if not obj.get("production_executable_sha256"):
        raise GateError("machine attestation has no production executable SHA")
    if executable is not None:
        if not executable.is_file():
            raise GateError(f"production executable missing: {executable}")
        observed = sha256_file(executable)
        if observed != obj["production_executable_sha256"]:
            raise GateError(f"production executable is not the machine-attested binary: {observed} != {obj['production_executable_sha256']}")
    return obj


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--machine-attestation", default="phase175_machine_attestation.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    pre = sub.add_parser("preflight")
    pre.add_argument("--executable")

    rp = sub.add_parser("r0-plan")
    rp.add_argument("--ic-root", default="./phase172_ics")

    pl = sub.add_parser("plan")
    pl.add_argument("--run-id", required=True)
    pl.add_argument("--ic-root", default="./phase172_ics")

    for name in ("prepare", "run"):
        x = sub.add_parser(name)
        x.add_argument("--run-id", required=True)
        x.add_argument("--executable", required=True)
        x.add_argument("--ic-root", required=True)
        x.add_argument("--run-root", required=True)
        x.add_argument("--mpi-prefix", default="")
        x.add_argument("--max-mem-mb", type=int, default=3500)
        x.add_argument("--time-limit-cpu", type=int, default=170000)
        x.add_argument("--no-generate-ic", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        manifest_path, rows = core.materialize_manifest(Path(".phase175") / "phase172_manifest.csv")
        for row in rows:
            core.validate_row(row)

        if args.cmd == "r0-plan":
            found = [core.plan(row, i, Path(args.ic_root)) for i, row in enumerate(rows)
                     if row["group"] == "R0_commissioning_not_for_claims"]
            if len(found) != 8:
                raise GateError(f"expected 8 R0 commissioning rows, found {len(found)}")
            print(json.dumps({"phase": 175, "status": "PASS", "r0_runs": found}, indent=2))
            return 0

        if args.cmd == "plan":
            idx, row = core.find_row(rows, args.run_id)
            print(json.dumps({"phase": 175, "status": "PASS", "plan": core.plan(row, idx, Path(args.ic_root))}, indent=2))
            return 0

        executable = Path(args.executable).resolve() if args.executable else None
        attestation_path = Path(args.machine_attestation).resolve()
        attestation = load_attestation(attestation_path, executable)

        if args.cmd == "preflight":
            print(json.dumps({
                "phase": 175,
                "status": "PASS",
                "gate": "machine-attested production launcher",
                "manifest_sha256": CANONICAL_MANIFEST_SHA256,
                "rows": len(rows),
                "blind_runs": sum(r["blind_analysis"] == "True" for r in rows),
                "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
                "production_config_sha256": CANONICAL_CONFIG_SHA256,
                "machine_attestation": str(attestation_path),
                "machine_attestation_sha256": sha256_file(attestation_path),
                "production_executable_sha256": attestation["production_executable_sha256"],
                "ci_binary_sha_match": attestation.get("ci_binary_sha_match"),
                "required_final_time_Gyr": core.EXPECTED_FINAL_TIME_GYR,
            }, indent=2))
            return 0

        provenance = dict(attestation)
        provenance["executable_sha256"] = attestation["production_executable_sha256"]
        run_dir, row, command, pre = core.prepare(args, provenance, rows, manifest_path)
        pre.update({
            "phase": 175,
            "phase175_launcher_sha256": sha256_file(Path(__file__)),
            "phase175_machine_attestation": str(attestation_path),
            "phase175_machine_attestation_sha256": sha256_file(attestation_path),
            "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
            "production_config_sha256": CANONICAL_CONFIG_SHA256,
        })
        (run_dir / "phase175_PRELAUNCH.json").write_text(json.dumps(pre, indent=2) + "\n")
        print(json.dumps({
            "phase": 175,
            "status": "PREPARED",
            "run_dir": str(run_dir),
            "command": command,
            "executable_sha256": pre["executable_sha256"],
            "machine_attestation_sha256": pre["phase175_machine_attestation_sha256"],
            "ic_sha256": pre["ic_sha256"],
            "params_sha256": pre["params_sha256"],
        }, indent=2))
        if args.cmd == "prepare":
            return 0
        rc = core.execute(run_dir, row, command, pre)
        post173 = run_dir / "phase173_POST.json"
        if post173.is_file():
            post = json.loads(post173.read_text())
            post["phase"] = 175
            post["phase175_machine_attestation_sha256"] = sha256_file(attestation_path)
            (run_dir / "phase175_POST.json").write_text(json.dumps(post, indent=2) + "\n")
        return rc
    except (GateError, core.LaunchError, OSError, ValueError) as exc:
        print(f"PHASE175 PRODUCTION LAUNCHER FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
