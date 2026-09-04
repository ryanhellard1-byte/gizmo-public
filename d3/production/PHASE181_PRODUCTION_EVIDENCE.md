# Phase 181: production evidence path

## Verdict

**SOFTWARE EVIDENCE PATH: REPAIRED / REAL 80-GYR PRODUCTION STILL REQUIRED.**

Phase 172 requires every production run to yield `run_summary.csv`, `profiles.csv`,
and `collision_log_summary.csv`, while the Phase176/179 launch path intentionally
selected the audit-free production binary.  That was a real contract mismatch:
a successful production campaign could have lacked the live collision telemetry
needed by its own frozen validators.

Phase181 repairs the evidence path without changing the frozen interaction laws,
manifest rows, analysis epochs, or acceptance thresholds.

## What changed

1. The ordinary positive-cross-section SIDM path now emits live audit telemetry
   when `SIDMX_D3_LIVE_AUDIT` is compiled, tagged as audit mode `10`.
2. Mode `10` is diagnostic only.  It is not a D3 runtime sentinel and does not
   replace the upstream positive-SIDM probability, RNG draw, or kick law.
3. A target machine now builds both:
   - `GIZMO_D3_EVIDENCE`: audit enabled, used for production evidence;
   - `GIZMO_D3_CONTROL`: audit disabled, used only for equivalence testing.
4. The target-machine attestation requires physical byte equality for both:
   - frozen D3 full mode `-1`;
   - ordinary equal-label `+1.125 cm^2/g` SIDM.
5. The scheduler routes the original 8 commissioning jobs and, only after their
   machine-readable PASS proof, the 119 blind jobs through the attested evidence
   executable and Phase175 safe-resume engine.
6. The live audit parser creates the frozen collision-summary columns from actual
   GIZMO telemetry.  Unmeasured `mean_sigma_factor` and `mean_mu` are left blank,
   never fabricated.
7. The snapshot profile extractor freezes the radial analysis before production:
   48 logarithmic bins over `0.03 <= r/r_s <= 5`, `r_s=9.1 kpc`, H/L/total,
   at the exact Phase172 times `0,0.25,0.5,1,2,5,10,20,40,55.28,80 Gyr`.

## CI proof

The Phase181 workflow independently builds audit-on and audit-off GIZMO binaries,
runs a dense equal-mass two-label `+1.125 cm^2/g` standard-SIDM evolution, requires
normal completion, requires mode-10 audit only in the audit-enabled executable,
compares the physical GADGET records (`positions`, `velocities`, `particle_ids`,
`masses`) byte-for-byte, and feeds the real audit log to the Phase181 collision
extractor.

The parser suite also rejects wrong audit modes, missing telemetry, unexpected
collisionless telemetry, `p>=1` evaluations, duplicate particle IDs, and malformed
snapshot records.

## Target-machine sequence

Build and attest the evidence executable from an operator checkout containing
Phase181:

```bash
python3 d3/production/phase181_machine_evidence.py build-attest \
  --source-repo /path/to/gizmo-public \
  --binary-dir /path/to/phase181/bin \
  --output /path/to/phase181/phase181_machine_attestation.json \
  --mpi-prefix "srun"
```

The attestation rebuilds the exact canonical Phase181 physics source commit and
refuses to pass unless both audit equivalence cases pass.

Stage the eight non-blind commissioning jobs:

```bash
python3 d3/production/phase181_machine_batch_submit.py stage \
  --phase commissioning \
  --machine-attestation /path/to/phase181/phase181_machine_attestation.json \
  --executable /path/to/phase181/bin/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/phase181/ics \
  --run-root /path/to/phase181/runs \
  --batch-root /path/to/phase181/batch \
  --mpi-prefix "srun" \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

After those eight complete, freeze their release proof:

```bash
python3 d3/production/phase181_machine_batch_submit.py verify-commissioning \
  --run-root /path/to/phase181/runs \
  --proof /path/to/phase181/commissioning_PASS.json \
  --machine-attestation /path/to/phase181/phase181_machine_attestation.json \
  --executable /path/to/phase181/bin/GIZMO_D3_EVIDENCE
```

Only a Phase181 PASS proof can release the 119 blind jobs:

```bash
python3 d3/production/phase181_machine_batch_submit.py stage \
  --phase blind \
  --commissioning-proof /path/to/phase181/commissioning_PASS.json \
  --machine-attestation /path/to/phase181/phase181_machine_attestation.json \
  --executable /path/to/phase181/bin/GIZMO_D3_EVIDENCE \
  --ic-root /path/to/phase181/ics \
  --run-root /path/to/phase181/runs \
  --batch-root /path/to/phase181/batch \
  --mpi-prefix "srun" \
  --mpi-tasks N \
  --slurm-option=--nodes=... \
  --slurm-option=--ntasks=... \
  --slurm-option=--time=... \
  --slurm-option=--partition=...
```

## Per-run evidence extraction

For an interacting run, produce the collision artifact from the actual appended
GIZMO log:

```bash
python3 d3/production/phase181_collision_summary.py \
  --manifest /path/to/phase172_manifest.csv \
  --run-id PH165-.... \
  --log /path/to/run/gizmo.log \
  --output /path/to/run/collision_log_summary.csv \
  --report-json /path/to/run/phase181_collision_report.json
```

Produce the radial profile artifact from the exact IC and completed snapshot set:

```bash
python3 d3/production/phase181_profile_extract.py \
  --manifest /path/to/phase172_manifest.csv \
  --run-id PH165-.... \
  --ic /path/to/exact/run/ic.dat \
  --run-dir /path/to/run \
  --output /path/to/run/profiles.csv \
  --report-json /path/to/run/phase181_profile_report.json
```

The campaign-level `run_summary.csv` still must be generated from the completed
run records, profile metrics, collision evidence, and GIZMO global conservation
telemetry before the blind physics verdict can be opened.  Phase181 does not
manufacture that missing live result.

## Claim boundary

Passing Phase181 means the production executable can retain required collision
telemetry without changing the tested physical evolution, and the scheduler and
profile/collision extraction path are fail-closed.

It does **not** mean the 127-run halo campaign has run.  It does **not** establish
R2/R3 convergence, the HL causal signal, blind acceptance, or a physical dark
matter conclusion.  Those remain outcomes of the real production calculation.
