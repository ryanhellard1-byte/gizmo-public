#!/usr/bin/env python3
"""Phase184 machine-evidence bridge for full-energy R0 commissioning.

This reuses the tested Phase181 evidence machinery while pinning it to a source
revision that exposes GIZMO's TimeBetStatistics through DEVELOPER_MODE. Every
other affected developer parameter is explicitly restored to the exact upstream
non-DEVELOPER_MODE default. Audit and control builds carry the same diagnostic
contract and may differ only by SIDMX_D3_LIVE_AUDIT.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase181_machine_evidence as base  # noqa: E402

PHASE = 184
CANONICAL_SOURCE_COMMIT = "2aafd369d2f26eef0bcc3cd8fcd6d4a4c1a7ed53"
ENERGY_DEFINE = "COMPUTE_POTENTIAL_ENERGY"
DEVELOPER_DEFINE = "DEVELOPER_MODE"

base.CANONICAL_SOURCE_COMMIT = CANONICAL_SOURCE_COMMIT
_original_verify_source_contract = base.verify_source_contract
_original_load_attestation = base.load_attestation


def _verify_source_contract_with_energy(tree: Path):
    result = _original_verify_source_contract(tree)
    for rel in ("d3/Config_d3_ci.sh", "d3/Config_d3_production.sh"):
        tokens = {line.strip() for line in (tree / rel).read_text().splitlines()}
        for required in (ENERGY_DEFINE, DEVELOPER_DEFINE):
            if required not in tokens:
                raise base.EvidenceGateError(f"Phase184 source contract missing {required} in {rel}")

    renderer = (tree / "d3/production/phase172_render_run.py").read_text()
    required_renderer = (
        "ENERGY_STATS_INTERVAL_GYR = 0.25",
        '"ErrTolIntAccuracy": 0.02',
        '"ErrTolTheta": 0.7',
        '"CourantFac": 0.4',
        '"ErrTolForceAcc": 0.0025',
        '"MaxRMSDisplacementFac": 0.25',
        '"MaxNumNgbDeviation": 0.05',
        "return max(float(neighbors) / 640.0, 0.05)",
        "TimeBetStatistics",
        "AGS_MaxNumNgbDeviation",
    )
    missing = [x for x in required_renderer if x not in renderer]
    if missing:
        raise base.EvidenceGateError(f"Phase184 renderer lost explicit-default contract: {missing}")

    smoke = (tree / "d3/params_m11_smoke.template").read_text()
    required_smoke = (
        "TimeBetStatistics            0.00001",
        "ErrTolIntAccuracy            0.02",
        "ErrTolTheta                  0.7",
        "CourantFac                   0.4",
        "ErrTolForceAcc               0.0025",
        "MaxRMSDisplacementFac        0.25",
        "MaxNumNgbDeviation           0.05",
        "AGS_DesNumNgb                64",
        "AGS_MaxNumNgbDeviation       0.1",
    )
    missing_smoke = [x for x in required_smoke if x not in smoke]
    if missing_smoke:
        raise base.EvidenceGateError(f"Phase184 equivalence smoke lost default mirror: {missing_smoke}")

    result.update({
        "phase184_energy_define": ENERGY_DEFINE,
        "phase184_developer_define": DEVELOPER_DEFINE,
        "phase184_energy_statistics_interval_Gyr": 0.25,
        "phase184_repeated_statistics_smoke": True,
        "phase184_developer_mode_defaults_frozen": True,
        "phase184_R0_AGS_neighbors": 64,
        "phase184_R0_AGS_max_deviation": 0.1,
    })
    return result


base.verify_source_contract = _verify_source_contract_with_energy


def load_attestation(path: Path, executable: Path | None = None):
    obj = _original_load_attestation(path, executable)
    expected = {
        "canonical_source_commit": CANONICAL_SOURCE_COMMIT,
        "phase184_energy_define": ENERGY_DEFINE,
        "phase184_developer_define": DEVELOPER_DEFINE,
        "phase184_energy_statistics_interval_Gyr": 0.25,
        "phase184_repeated_statistics_smoke": True,
        "phase184_developer_mode_defaults_frozen": True,
        "phase184_R0_AGS_neighbors": 64,
        "phase184_R0_AGS_max_deviation": 0.1,
    }
    bad = {k: {"observed": obj.get(k), "expected": v} for k, v in expected.items() if obj.get(k) != v}
    if bad:
        raise base.EvidenceGateError(f"Phase184 attestation contract mismatch: {bad}")
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
