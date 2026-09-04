#!/usr/bin/env python3
"""Phase184 machine-evidence bridge for full-energy R0 commissioning.

This deliberately reuses the already-tested Phase181 evidence machinery while
pinning it to the Phase184 canonical source revision. The only source-contract
addition is full gravitational-potential energy telemetry in BOTH audit-on and
audit-off builds. Interaction laws, RNG, manifest rows and acceptance gates are
unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_machine_evidence as base  # noqa: E402

PHASE = 184
CANONICAL_SOURCE_COMMIT = "eccc7f9d084aa40ffa82ebc1486496a0c8c6f426"
ENERGY_DEFINE = "COMPUTE_POTENTIAL_ENERGY"

base.CANONICAL_SOURCE_COMMIT = CANONICAL_SOURCE_COMMIT
_original_verify_source_contract = base.verify_source_contract
_original_load_attestation = base.load_attestation


def _verify_source_contract_with_energy(tree: Path):
    result = _original_verify_source_contract(tree)
    for rel in ("d3/Config_d3_ci.sh", "d3/Config_d3_production.sh"):
        tokens = {line.strip() for line in (tree / rel).read_text().splitlines()}
        if ENERGY_DEFINE not in tokens:
            raise base.EvidenceGateError(f"Phase184 source contract missing {ENERGY_DEFINE} in {rel}")
    renderer = (tree / "d3/production/phase172_render_run.py").read_text()
    if "ENERGY_STATS_INTERVAL_GYR = 0.25" not in renderer or "TimeBetStatistics" not in renderer:
        raise base.EvidenceGateError("Phase184 source contract lacks frozen 0.25 Gyr energy-statistics cadence")
    smoke = (tree / "d3/params_m11_smoke.template").read_text()
    if "TimeBetStatistics            0.00001" not in smoke:
        raise base.EvidenceGateError("Phase184 equivalence smoke does not exercise repeated energy statistics")
    result.update({
        "phase184_energy_define": ENERGY_DEFINE,
        "phase184_energy_statistics_interval_Gyr": 0.25,
        "phase184_repeated_statistics_smoke": True,
    })
    return result


base.verify_source_contract = _verify_source_contract_with_energy


def load_attestation(path: Path, executable: Path | None = None):
    obj = _original_load_attestation(path, executable)
    if obj.get("canonical_source_commit") != CANONICAL_SOURCE_COMMIT:
        raise base.EvidenceGateError("Phase184 canonical source mismatch")
    if obj.get("phase184_energy_define") != ENERGY_DEFINE:
        raise base.EvidenceGateError("Phase184 attestation lacks full-energy diagnostic contract")
    if obj.get("phase184_energy_statistics_interval_Gyr") != 0.25:
        raise base.EvidenceGateError("Phase184 attestation energy-statistics cadence mismatch")
    if obj.get("phase184_repeated_statistics_smoke") is not True:
        raise base.EvidenceGateError("Phase184 attestation lacks repeated-statistics equivalence proof")
    return obj


def provenance_from_attestation(path: Path, executable: Path | None = None):
    obj = load_attestation(path, executable)
    prov = dict(obj)
    prov["executable_sha256"] = obj["evidence_executable_sha256"]
    prov["phase181_attestation_sha256"] = base.sha256_file(path)
    prov["phase184_full_energy_contract"] = True
    return prov


def main() -> int:
    base.load_attestation = load_attestation
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
