#!/usr/bin/env python3
"""Phase184 full-energy evidence entry point for the Phase175 safe-resume engine."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase175_safe_resume as resume  # noqa: E402
import phase184_machine_evidence as evidence  # noqa: E402

PHASE = 184


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--machine-attestation", required=True)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("dispatch", "inspect"):
        x = sub.add_parser(name)
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
    attestation_path = Path(args.machine_attestation).resolve()
    executable = Path(args.executable).resolve()
    try:
        provenance = evidence.provenance_from_attestation(attestation_path, executable)

        def load_campaign():
            manifest_path, rows = resume.p173.materialize_manifest(
                Path(".phase184") / "phase172_manifest.csv"
            )
            for row in rows:
                resume.p173.validate_row(row)
            return provenance, manifest_path, rows

        resume.load_campaign = load_campaign
        if args.command == "dispatch":
            return resume.dispatch(args)
        return resume.inspect(args)
    except (
        evidence.base.EvidenceGateError,
        resume.ResumeError,
        resume.p173.LaunchError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"phase": PHASE, "status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
