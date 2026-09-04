#!/usr/bin/env python3
"""Phase173 fail-closed execution layer for the frozen Phase172 campaign.

This script does not tune or rewrite the frozen physics manifest. It materializes
that manifest from phase172_lock.py, selects either the 8 non-blind commissioning
rows or the 119 blind rows, stages deterministic ICs/parameter files, and emits
or submits scheduler jobs.

Default behavior is stage-only. --submit is an explicit execution boundary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCK = HERE / "phase172_lock.py"
MAKE_IC = HERE / "phase172_make_ic.py"
RENDER = HERE / "phase172_render_run.py"
EXPECTED_MANIFEST_SHA = "e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d"
EXPECTED_TOTAL = 127
EXPECTED_BLIND = 119
EXPECTED_COMMISSIONING = 8
MASTER_SHA = "9242675125649f1e0a8852efe0abe13324e98311"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd, *, cwd=None, capture=False):
    print("+", shlex.join(str(x) for x in cmd), flush=True)
    return subprocess.run(
        [str(x) for x in cmd], cwd=cwd, check=True,
        text=True, capture_output=capture,
    )


def truthy(x: str) -> bool:
    return str(x).strip().lower() == "true"


def load_manifest(work_root: Path):
    manifest = work_root / "phase172_production_live_nbody_manifest.csv"
    run([sys.executable, LOCK, "--write", manifest])
    got = sha256(manifest)
    if got != EXPECTED_MANIFEST_SHA:
        raise SystemExit(f"FATAL: frozen manifest SHA mismatch {got}")
    with manifest.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    blind = sum(truthy(r["blind_analysis"]) for r in rows)
    commissioning = len(rows) - blind
    if len(rows) != EXPECTED_TOTAL or blind != EXPECTED_BLIND or commissioning != EXPECTED_COMMISSIONING:
        raise SystemExit(
            f"FATAL: campaign cardinality changed: total={len(rows)} blind={blind} commissioning={commissioning}"
        )
    return manifest, rows


def select(rows, phase: str):
    if phase == "commissioning":
        picked = [(i, r) for i, r in enumerate(rows) if not truthy(r["blind_analysis"])]
        if len(picked) != EXPECTED_COMMISSIONING:
            raise SystemExit(f"FATAL: commissioning selection is {len(picked)}, expected 8")
        return picked
    if phase == "blind":
        picked = [(i, r) for i, r in enumerate(rows) if truthy(r["blind_analysis"])]
        if len(picked) != EXPECTED_BLIND:
            raise SystemExit(f"FATAL: blind selection is {len(picked)}, expected 119")
        return picked
    if phase == "all":
        return list(enumerate(rows))
    raise AssertionError(phase)


def ensure_ic(row, ic_root: Path):
    n = int(row["N_total"])
    seed = int(row["seed"])
    ratio = float(row["ic_mass_ratio"])
    order = row["ic_order"]
    tag = f"M11_N{n}_seed{seed}_mr{ratio:g}_{order}"
    ic = ic_root / f"{tag}.dat"
    if not ic.exists():
        run([
            sys.executable, MAKE_IC,
            "--n-total", n,
            "--seed", seed,
            "--mass-ratio", ratio,
            "--order", order,
            "--output", ic,
        ])
    meta = Path(str(ic) + ".json")
    if not ic.is_file() or not meta.is_file():
        raise SystemExit(f"FATAL: IC generation incomplete for {row['run_id']}")
    return ic


def write_slurm_script(path: Path, run_id: str, params: Path, executable: Path,
                       *, nodes: int, ntasks_per_node: int, cpus_per_task: int,
                       mem_gb: int, walltime: str, account: str | None,
                       partition: str | None):
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name=d3-{run_id}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks-per-node={ntasks_per_node}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --mem={mem_gb}G",
        f"#SBATCH --time={walltime}",
        f"#SBATCH --output={path.parent / 'slurm-%j.out'}",
        f"#SBATCH --error={path.parent / 'slurm-%j.err'}",
    ]
    if account:
        lines.append(f"#SBATCH --account={account}")
    if partition:
        lines.append(f"#SBATCH --partition={partition}")
    lines += [
        "set -euo pipefail",
        f"test -x {shlex.quote(str(executable.resolve()))}",
        f"test -f {shlex.quote(str(params.resolve()))}",
        f"srun {shlex.quote(str(executable.resolve()))} {shlex.quote(str(params.resolve()))} 0",
        "rc=$?",
        f"printf '%s\\n' \"$rc\" > {shlex.quote(str(path.parent / 'exit_code.txt'))}",
        "exit \"$rc\"",
    ]
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)


def write_local_script(path: Path, run_id: str, params: Path, executable: Path,
                       *, mpi_tasks: int):
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"test -x {shlex.quote(str(executable.resolve()))}",
        f"test -f {shlex.quote(str(params.resolve()))}",
        f"mpirun -np {mpi_tasks} {shlex.quote(str(executable.resolve()))} {shlex.quote(str(params.resolve()))} 0",
        "rc=$?",
        f"printf '%s\\n' \"$rc\" > {shlex.quote(str(path.parent / 'exit_code.txt'))}",
        "exit \"$rc\"",
    ]
    path.write_text("\n".join(lines) + "\n")
    path.chmod(0o755)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["commissioning", "blind", "all"], default="commissioning")
    ap.add_argument("--backend", choices=["slurm", "local"], default="slurm")
    ap.add_argument("--executable", type=Path, required=True)
    ap.add_argument("--work-root", type=Path, default=Path("phase173_runs"))
    ap.add_argument("--ic-root", type=Path, default=None)
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--ntasks-per-node", type=int, default=16)
    ap.add_argument("--cpus-per-task", type=int, default=1)
    ap.add_argument("--mem-gb", type=int, default=64)
    ap.add_argument("--walltime", default="48:00:00")
    ap.add_argument("--account", default=None)
    ap.add_argument("--partition", default=None)
    ap.add_argument("--local-mpi-tasks", type=int, default=4)
    args = ap.parse_args()

    if not args.executable.is_file() or not os.access(args.executable, os.X_OK):
        raise SystemExit(f"FATAL: executable missing/not executable: {args.executable}")
    for name, value in (
        ("nodes", args.nodes), ("ntasks-per-node", args.ntasks_per_node),
        ("cpus-per-task", args.cpus_per_task), ("mem-gb", args.mem_gb),
        ("local-mpi-tasks", args.local_mpi_tasks),
    ):
        if value <= 0:
            raise SystemExit(f"FATAL: {name} must be positive")

    args.work_root.mkdir(parents=True, exist_ok=True)
    ic_root = args.ic_root or (args.work_root / "ic_cache")
    ic_root.mkdir(parents=True, exist_ok=True)
    manifest, rows = load_manifest(args.work_root)
    chosen = select(rows, args.phase)

    plan = []
    for row_index, row in chosen:
        run_id = row["run_id"]
        run_dir = args.work_root / run_id
        if run_dir.exists():
            raise SystemExit(f"FATAL: run directory already exists; refusing overwrite: {run_dir}")
        ensure_ic(row, ic_root)
        run([
            sys.executable, RENDER,
            "--manifest", manifest,
            "--row-index", row_index,
            "--ic-root", ic_root,
            "--run-root", args.work_root,
        ])
        params = run_dir / "params.txt"
        if not params.is_file():
            raise SystemExit(f"FATAL: renderer did not create {params}")
        job = run_dir / ("submit.slurm" if args.backend == "slurm" else "run_local.sh")
        if args.backend == "slurm":
            write_slurm_script(
                job, run_id, params, args.executable,
                nodes=args.nodes, ntasks_per_node=args.ntasks_per_node,
                cpus_per_task=args.cpus_per_task, mem_gb=args.mem_gb,
                walltime=args.walltime, account=args.account, partition=args.partition,
            )
            submit_cmd = ["sbatch", str(job.resolve())]
        else:
            write_local_script(job, run_id, params, args.executable, mpi_tasks=args.local_mpi_tasks)
            submit_cmd = [str(job.resolve())]

        entry = {
            "run_id": run_id,
            "row_index": row_index,
            "blind_analysis": truthy(row["blind_analysis"]),
            "group": row["group"],
            "branch": row["branch"],
            "N_total": int(row["N_total"]),
            "required_final_time_Gyr": 80.0,
            "job_script": str(job.resolve()),
            "submit_command": submit_cmd,
        }
        if args.submit:
            if args.phase == "all":
                raise SystemExit("FATAL: --submit --phase all is forbidden; commission first, then launch blind explicitly")
            p = run(submit_cmd, capture=True)
            entry["submission_stdout"] = p.stdout.strip()
            entry["submitted"] = True
        else:
            entry["submitted"] = False
        plan.append(entry)

    report = {
        "phase173_status": "SUBMITTED" if args.submit else "STAGED",
        "master_sha": MASTER_SHA,
        "frozen_manifest_sha256": sha256(manifest),
        "phase": args.phase,
        "backend": args.backend,
        "selected_runs": len(plan),
        "blind_runs_selected": sum(bool(x["blind_analysis"]) for x in plan),
        "commissioning_runs_selected": sum(not bool(x["blind_analysis"]) for x in plan),
        "submit": bool(args.submit),
        "runs": plan,
    }
    out = args.work_root / f"phase173_{args.phase}_plan.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
