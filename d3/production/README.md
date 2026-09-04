# D3/SIDMx production campaign

This directory contains the frozen live-GIZMO production campaign and the fail-closed machinery that carries it from preregistration to the final blind physics gate.

## Frozen campaign

The Phase172 campaign is fixed at **127 runs**:

- **8 non-blind commissioning runs**;
- **119 blind runs**;
- manifest SHA-256 `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`.

The required analysis schedule for every row is exactly:

`0, 0.25, 0.5, 1, 2, 5, 10, 20, 40, 55.28, 80 Gyr`.

Materialize and audit the frozen manifest:

```bash
python3 d3/production/phase172_lock.py \
  --write d3/production/phase172_production_live_nbody_manifest.csv

python3 d3/production/phase172_time_contract.py \
  --manifest d3/production/phase172_production_live_nbody_manifest.csv \
  --manifest-only
```

## Canonical production path

The production path is intentionally split so commissioning can be inspected without opening blind results early.

### 1. Target-machine attestation

Use the Phase180/181 target-machine packet and evidence build to establish the exact production environment and executable. The production jobs must use the evidence-attested executable, not an arbitrary locally rebuilt binary.

### 2. Run only the eight non-blind commissioning jobs

Stage or submit commissioning through:

`phase185_machine_batch_submit.py`

The generated jobs execute through `phase185_safe_resume.py`, which delegates the actual simulation to the already-validated Phase181/Phase175 safe-resume stack.

A scheduler/CPU-time cutoff remains `PAUSED_RESTARTABLE`. A completed **commissioning** run is then finalized into an external commissioning-evidence root by `phase185_commissioning_evidence.py`.

The commissioning finalizer writes:

- `run_summary.csv`;
- `profiles.csv`;
- `collision_log_summary.csv`;
- `phase185_COMMISSIONED.json`.

Those files are forbidden from being written inside any fingerprinted raw run directory.

### 3. Verify commissioning and unlock the blind campaign

After all eight commissioning runs are complete, create the Phase185 commissioning PASS proof with `phase185_machine_batch_submit.py verify-commissioning`.

Blind staging does not merely trust that old proof. It re-verifies the current machine attestation, executable, all eight raw-run fingerprints, all eight Phase185 finalization records, and all derived artifact hashes.

The blind release also requires **no per-run Phase185 evidence directory to exist for any of the 119 blind run IDs**.

### 4. Run the 119 blind jobs raw-only

The same Phase185 scheduler launches the blind jobs, but `phase185_safe_resume.py` explicitly forbids Phase185 per-run profile/collision finalization for blind rows.

Blind jobs therefore expose only their raw simulation state (`PAUSED_RESTARTABLE` or `COMPLETE`). Their profiles and collision summaries remain unopened until the full campaign is complete.

### 5. Open all 127 runs together with Phase184

Only after every frozen run is complete, run:

```bash
python3 d3/production/phase184_campaign_evidence.py \
  --run-root /path/to/immutable/raw-runs \
  --output-dir /path/to/phase184_campaign_evidence \
  --machine-attestation /path/to/phase181_machine_attestation.json \
  --executable /path/to/GIZMO_D3_EVIDENCE
```

Phase184 independently re-verifies all 127 raw runs and extracts the canonical campaign-level:

- `run_summary.csv`;
- `profiles.csv`;
- `collision_log_summary.csv`;
- `phase184_collection_report.json`.

The final evidence directory and its temporary staging directory must live outside every raw run directory. The complete directory is promoted by one same-filesystem rename only after all 127 runs and the Phase172 output contract pass. A failed collection leaves no partial final evidence set.

The early Phase185 commissioning evidence is a **release gate only**. It is not concatenated into the final campaign evidence by hand.

### 6. Run the frozen physics validator

Run the already-frozen Phase174 radial/convergence validator on the Phase184 campaign artifacts:

```bash
python3 d3/production/phase174_radial_convergence_validator.py \
  --manifest d3/production/phase172_production_live_nbody_manifest.csv \
  --run-summary /path/to/phase184_campaign_evidence/run_summary.csv \
  --profiles /path/to/phase184_campaign_evidence/profiles.csv \
  --collision-summary /path/to/phase184_campaign_evidence/collision_log_summary.csv \
  --out-json /path/to/phase184_campaign_evidence/phase174_physics_verdict.json
```

## Live GIZMO runtime mapping

The D3 engine uses the frozen sentinels:

- `0`: CDM / zero ordinary SIDM cross section
- `-1`: full SIDM2v = HH+LL+HL
- `-2`: SIDMx = HL only
- `-3`: HL-off = HH+LL
- `-4`: HH only
- `-5`: LL only
- `-6`: HL+HH
- `-7`: HL+LL
- `-8`: constant isotropic SIDM2c benchmark, HH=2.25, LL=0.75, HL=1.125 cm^2/g
- `-9`: D3 zero-cross-section null

The equal-label null intentionally uses the ordinary positive constant-SIDM path at `1.125 cm^2/g` with `mH=mL=1`. This tests label invariance without weakening the frozen `mH/mL=3` D3 contract.

## Frozen causal pairing

Numerical controls reuse baseline IC seeds wherever the comparison is causal:

- half-timestep rows pair to R2 baseline runs;
- 48/96-neighbor rows pair to R2 baseline runs;
- channel ablations pair to full SIDM2v at the same resolution and seed;
- SIDM2c half-timestep rows pair to SIDM2c base rows;
- D3 mode-9 nulls pair to CDM R2 rows;
- particle-order tests pair to normal R2 SIDM2v rows and change only within-species file order while preserving particle IDs.

## Claim boundary

Passing the software, attestation, commissioning-release, and evidence-assembly gates means the experiment is executable, provenance-locked, resumable, and analyzable without opening blind results early.

It does **not** mean the halo physics has passed. The real 127-run, 80-Gyr live-gravity outputs must still establish the frozen convergence, causal-separation, conservation, and blind profile gates before any physical D3/SIDMx halo claim is allowed.
