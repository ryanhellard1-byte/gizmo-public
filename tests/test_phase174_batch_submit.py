#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "d3" / "production" / "phase174_batch_submit.py"
spec = importlib.util.spec_from_file_location("phase174_batch_submit", MOD)
assert spec is not None and spec.loader is not None
p174 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p174)

rows, commissioning, blind = p174.frozen_rows()
assert len(rows) == 127
assert len(commissioning) == 8
assert len(blind) == 119
assert all(r["group"] == "R0_commissioning_not_for_claims" for r in commissioning)
assert all(not p174.truthy(r["blind_analysis"]) for r in commissioning)
assert all(p174.truthy(r["blind_analysis"]) for r in blind)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    fake_exe = td / "GIZMO_D3"
    fake_exe.write_text("#!/bin/sh\nexit 0\n")
    fake_exe.chmod(0o755)

    args = Namespace(
        phase="commissioning",
        executable=str(fake_exe),
        ic_root=str(td / "ics"),
        run_root=str(td / "runs"),
        batch_root=str(td / "batch_comm"),
        mpi_prefix="srun",
        slurm_option=[],
        commissioning_proof=None,
        submit=False,
        sbatch="sbatch",
    )
    report = p174.stage_or_submit(args)
    assert report["status"] == "STAGED"
    assert report["selected_runs"] == 8
    assert report["blind_selected"] == 0
    assert report["commissioning_selected"] == 8
    assert len(report["phase175_dispatcher_sha256"]) == 64
    for entry in report["entries"]:
        text = Path(entry["job_script"]).read_text()
        assert "phase175_safe_resume.py dispatch" in text
        assert "--mpi-prefix srun" in text

    # Build structurally valid completion records. Half use direct Phase173
    # compatibility and half use the resumed Phase175 completion path.
    run_root = td / "complete_runs"
    for i, row in enumerate(commissioning):
        rd = run_root / row["run_id"]
        rd.mkdir(parents=True)
        post = {
            "run_id": row["run_id"],
            "status": "COMPLETE",
            "manifest_sha256": p174.EXPECTED_MANIFEST_SHA256,
            "manifest_row": row,
            "snapshot_count": 10,
            "required_snapshot_count": 10,
            "completion_marker": True,
            "fatal_marker": False,
            "attempt": 2 if i % 2 else 1,
            "restart_flag": 1 if i % 2 else 0,
        }
        name = p174.p175.STATE_NAME if i % 2 else "phase173_POST.json"
        (rd / name).write_text(json.dumps(post) + "\n")

    proof_path = td / "commissioning-proof.json"
    proof = p174.verify_commissioning(run_root, proof_path)
    assert proof["status"] == "PASS"
    assert proof["complete_runs"] == 8
    assert {r["completion_record"] for r in proof["records"]} == {
        "phase173_POST.json", p174.p175.STATE_NAME
    }
    p174.load_commissioning_proof(proof_path, commissioning)

    blind_args = Namespace(
        phase="blind",
        executable=str(fake_exe),
        ic_root=str(td / "ics"),
        run_root=str(td / "blind_runs"),
        batch_root=str(td / "batch_blind"),
        mpi_prefix="srun",
        slurm_option=[],
        commissioning_proof=str(proof_path),
        submit=False,
        sbatch="sbatch",
    )
    blind_report = p174.stage_or_submit(blind_args)
    assert blind_report["selected_runs"] == 119
    assert blind_report["blind_selected"] == 119
    assert blind_report["commissioning_selected"] == 0

    # Corrupting the proof must fail closed.
    bad = json.loads(proof_path.read_text())
    bad["complete_runs"] = 7
    bad_path = td / "bad-proof.json"
    bad_path.write_text(json.dumps(bad))
    try:
        p174.load_commissioning_proof(bad_path, commissioning)
    except p174.BatchError:
        pass
    else:
        raise AssertionError("corrupt commissioning proof was accepted")

print("Phase174 batch submit gate PASS")
print("commissioning IDs:", ",".join(r["run_id"] for r in commissioning))
