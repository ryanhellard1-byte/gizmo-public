#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "d3" / "production"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lock = load_module("phase172_lock", PROD / "phase172_lock.py")
exe = load_module("phase173_execute_campaign", PROD / "phase173_execute_campaign.py")
raw, rows = lock.load()

assert len(rows) == exe.EXPECTED_TOTAL == 127
assert sum(exe.truthy(r["blind_analysis"]) for r in rows) == exe.EXPECTED_BLIND == 119
assert len(exe.select(rows, "commissioning")) == exe.EXPECTED_COMMISSIONING == 8
assert len(exe.select(rows, "blind")) == 119
assert len(exe.select(rows, "all")) == 127
assert all(not exe.truthy(r["blind_analysis"]) for _, r in exe.select(rows, "commissioning"))
assert all(exe.truthy(r["blind_analysis"]) for _, r in exe.select(rows, "blind"))

source = (PROD / "phase173_execute_campaign.py").read_text()
assert '--submit --phase all is forbidden' in source
assert 'refusing overwrite' in source
assert 'EXPECTED_MANIFEST_SHA = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"' in source
assert exe.MASTER_SHA == "9242675125649f1e0a8852efe0abe13324e98311"

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    params = td / "params.txt"
    params.write_text("TimeMax 1\n")
    binary = td / "GIZMO_D3"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    slurm = td / "submit.slurm"
    exe.write_slurm_script(
        slurm, "PH173-TEST", params, binary,
        nodes=2, ntasks_per_node=8, cpus_per_task=1,
        mem_gb=64, walltime="12:00:00", account=None, partition=None,
    )
    text = slurm.read_text()
    assert "#SBATCH --nodes=2" in text
    assert "#SBATCH --ntasks-per-node=8" in text
    assert "srun" in text and "GIZMO_D3" in text

commissioning_ids = [r["run_id"] for _, r in exe.select(rows, "commissioning")]
print("Phase173 executor gate PASS")
print("commissioning IDs:", ",".join(commissioning_ids))
