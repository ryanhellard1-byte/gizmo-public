# Phase 175: target-machine production provenance gate

## Status entering this phase

The exact-head CI equivalence run **33850670457** at source commit
`dc93bca31b19135a1f8510e838f23abc850869fb` passed. Its audit-enabled and
audit-free binaries produced byte-identical GADGET physical records for
positions, velocities, particle IDs, and masses. The production artifact is
**9928241676**, with artifact digest
`sha256:401a92db93b2d68f0d5fe9a84e3053bb47191b0bbbfb5385ae2538279d06dc05`.

The CI audit-free executable SHA-256 is
`f11e011b9420ebe829eb77295a09c0d525dd6ae8c0411173231911cacfb98dc0` and the
production config SHA-256 is
`887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329`.

## Why Phase 175 exists

Phase173 locked production to an older GitHub-hosted **audit-enabled** binary.
That was useful as an historical provenance check, but it is the wrong contract
for a portable production campaign. A correctly rebuilt HPC executable can have
a different byte hash because the compiler, linker, MPI, and shared-library
environment differ even when the source and physics are identical.

Phase175 therefore freezes the source/config/manifest and requires the target
machine to earn its own executable attestation.

## Canonical immutable inputs

- physics/equivalence source commit: `dc93bca31b19135a1f8510e838f23abc850869fb`
- production config SHA-256: `887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329`
- frozen Phase172 manifest SHA-256: `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d`
- CI equivalence reference: `phase175_ci_equivalence_reference.json`

No physics parameter, manifest row, analysis time, or blind gate is changed by
Phase175.

## Target-machine procedure

1. Make a clean detached checkout/worktree at the canonical source commit.
2. Build one commissioning binary with `d3/Config_d3_ci.sh` and one production
   binary with `d3/Config_d3_production.sh` on the target machine.
3. From the current tooling checkout, run:

```bash
python3 d3/production/phase175_machine_audit.py attest \
  --source-tree /path/to/canonical-dc93bca-worktree \
  --audit-executable /path/to/GIZMO_D3_AUDIT \
  --production-executable /path/to/GIZMO_D3_PROD \
  --mpi-prefix "mpirun -np 2" \
  --output /secure/path/phase175_machine_attestation.json
```

The audit reruns the deterministic 1000-particle full-D3 equivalence test on the
target machine and fails unless positions, velocities, particle IDs, and masses
are byte-identical between audit-enabled and audit-free builds. It also requires
the exact canonical source commit, a clean source tree, exact production config,
and exact frozen manifest.

The target production binary is then bound by its **own** SHA-256 in the machine
attestation. Matching the Ubuntu CI executable hash is recorded but is not
required.

## Production launcher

After the machine audit passes:

```bash
python3 d3/production/phase175_production_launcher.py \
  --machine-attestation /secure/path/phase175_machine_attestation.json \
  preflight --executable /path/to/GIZMO_D3_PROD
```

Then inspect the eight commissioning rows:

```bash
python3 d3/production/phase175_production_launcher.py r0-plan
```

Only after the target-machine gate is green should the eight R0 commissioning
runs be launched. R0 remains excluded from physics claims. The 119 blind runs
remain frozen and untouched.

## Claim boundary

A Phase175 machine-audit PASS proves executable provenance and audit-free
physical equivalence on the production machine. It does **not** prove the halo
physics. `P_production`, `P_convergence`, and `P_blind` remain unearned until the
registered simulations and frozen validators actually pass.
