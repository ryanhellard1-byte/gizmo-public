#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "d3" / "production" / "phase180_target_machine_packet.py"
spec = importlib.util.spec_from_file_location("phase180_target_machine_packet", MOD)
assert spec is not None and spec.loader is not None
p180 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p180)

assert p180.canonical_source_commit() == p180.p176.EXPECTED["source_commit"]
assert p180.canonical_source_commit() == "dc93bca31b19135a1f8510e838f23abc850869fb"

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    packet = td / "phase180_packet.sh"
    cmd = [
        "python3", str(MOD), "write-packet",
        "--operator-tree", str(td / "operator"),
        "--canonical-source-tree", str(td / "canonical"),
        "--binary-dir", str(td / "bin"),
        "--machine-attestation", str(td / "attest" / "phase176_machine_attestation.json"),
        "--ic-root", str(td / "ics"),
        "--run-root", str(td / "runs"),
        "--batch-root", str(td / "batch"),
        "--systype", "Frontera",
        "--build-jobs", "8",
        "--build-mpi-prefix", "mpirun -np 2",
        "--run-mpi-prefix", "srun",
        "--mpi-tasks", "64",
        "--slurm-option", "--nodes=2",
        "--slurm-option", "--ntasks=64",
        "--slurm-option", "--time=48:00:00",
        "--output", str(packet),
    ]
    result = subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["phase"] == 180
    assert payload["canonical_source_commit"] == p180.canonical_source_commit()
    assert packet.is_file()
    text = packet.read_text()

    assert "OPERATOR_TREE=" in text
    assert "CANONICAL_SOURCE_TREE=" in text
    assert "EXPECTED_CANONICAL_SOURCE_COMMIT=" in text
    assert p180.canonical_source_commit() in text
    assert "phase176_machine_audit.py build-attest" in text
    assert "--source-tree" in text
    assert "phase176_production_launcher.py" in text
    assert "phase179_machine_batch_submit.py stage --phase commissioning" in text
    assert "phase179_machine_batch_submit.py verify-commissioning" in text
    assert "phase179_machine_batch_submit.py stage --phase blind" in text
    assert "phase176_safe_resume.py" not in text  # Phase179 writes those job scripts, not Phase180.
    assert "phase175_safe_resume.py" not in text
    assert "--slurm-option --nodes=2" in text
    assert "--slurm-option --ntasks=64" in text
    assert "--slurm-option --time=48:00:00" in text

    try:
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        assert "refusing to overwrite existing packet" in exc.stderr
    else:
        raise AssertionError("Phase180 overwrote an existing packet")

    bad = cmd.copy()
    idx = bad.index("--slurm-option") + 1
    bad[idx] = "nodes=2"
    bad[-1] = str(td / "bad_packet.sh")
    try:
        subprocess.run(bad, cwd=ROOT, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        assert "invalid --slurm-option value" in exc.stderr
    else:
        raise AssertionError("Phase180 accepted unsafe scheduler option")

print("Phase180 target-machine packet gate PASS")
