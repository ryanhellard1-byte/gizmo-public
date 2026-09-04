# Phase176: production-machine build provenance gate

Phase175 already means **safe native-GIZMO checkpoint/resume** in this repository. Phase176 is therefore the separate production-machine provenance bridge.

## Frozen evidence

The canonical audit-on versus audit-off equivalence proof is GitHub Actions run `33850670457` at source commit `dc93bca31b19135a1f8510e838f23abc850869fb`. Artifact `9928241676` has digest `sha256:401a92db93b2d68f0d5fe9a84e3053bb47191b0bbbfb5385ae2538279d06dc05`.

That run proved byte equality of the final GADGET physical records for positions, velocities, particle IDs, and masses. The CI audit-free executable SHA-256 is `f11e011b9420ebe829eb77295a09c0d525dd6ae8c0411173231911cacfb98dc0`. The production config SHA-256 is `887c247b3e968b84b4152db990e37ae55d6b906180ce01fddc9385010e5ee329`. The frozen Phase172 manifest remains `e0d1e6ab4d2a58cbdab5b1991d75f231dc6a5bea28127ba6b7a11deb27a0e28d` with 127 rows, 119 blind.

## Why this gate builds the binaries itself

A target HPC executable is not required to have the same byte hash as an Ubuntu GitHub Actions build. Compiler, linker, MPI, and library differences can legitimately change executable bytes. Accepting arbitrary prebuilt binaries would weaken provenance.

`phase176_machine_audit.py build-attest` therefore exports the exact canonical Git commit twice, builds the audit and audit-free binaries itself from the frozen configs, runs the same deterministic 1000-particle full-D3 equivalence experiment on the target machine, and only then writes the machine attestation. The attestation binds the exact target production executable SHA-256.

Optional `--systype NAME` changes only the build-system selector inside temporary exported build trees. It does not alter the canonical source checkout, D3 physics, config, manifest, or blind gates.

## Target-machine command

```bash
python3 d3/production/phase176_machine_audit.py build-attest \
  --source-tree /path/to/clean/checkout-at-dc93bca31b19135a1f8510e838f23abc850869fb \
  --systype Frontera --jobs 8 --mpi-prefix "mpirun -np 2" \
  --binary-dir /secure/d3/bin \
  --output /secure/d3/phase176_machine_attestation.json
```

Then run the attested launcher preflight and inspect the eight R0 commissioning rows. For long scheduler-limited runs, enter the existing Phase175 checkpoint/resume engine through `phase176_safe_resume.py`; it injects the Phase176 attested provenance instead of Phase175's historical Phase173 GitHub-binary lock.

## Claim boundary

A Phase176 PASS proves target-machine build provenance plus audit-enabled/audit-free physical equivalence. It does not prove the halo effect. R0 remains commissioning-only, and the 119 frozen blind runs still have to earn production, convergence, and blind-physics gates.
