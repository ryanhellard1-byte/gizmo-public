# Phase165 native GIZMO production adapter

This adapter binds the frozen Phase165 production manifest to the proven native `GIZMO_D3` executable. It does **not** redefine physics or validation gates.

Frozen provenance:

- master software proof commit: `a5e7b7e777bd211bf0f0b5c667a9957f476ef0ec`
- frozen Phase165 manifest SHA256: `08c62df08a23c990789dc3678b44a8c2b42be30de703acd0100e032a07b8a0a3`
- proven `GIZMO_D3` executable SHA256: `677a881fc0964012df39c4736180ce77fb8400ca494f1a6b2776110b6d560155`

Native D3 branch mapping:

| Phase165 meaning | native sentinel |
|---|---:|
| SIDM2v/full HH+LL+HL | -1 |
| SIDMx/HL only | -2 |
| HL-off/HH+LL | -3 |
| HH only | -4 |
| LL only | -5 |
| HL+HH | -6 |
| HL+LL | -7 |
| SIDM2c constant/isotropic | -8 |
| CDM/null | -9 |

Resolution contract:

| level | N_H | N_L | softening kpc |
|---|---:|---:|---:|
| R0 | 100000 | 100000 | 0.060 |
| R1 | 300000 | 300000 | 0.040 |
| R2 | 600000 | 600000 | 0.028 |
| R3 | 1200000 | 1200000 | 0.020 |

## Usage

Dry-run/staging audit (default):

```bash
python3 d3/phase165_gizmo_adapter.py phase165_production_live_nbody_manifest.csv RUN_ID \
  --executable /path/to/GIZMO_D3
```

Execute only after the dry-run provenance is inspected:

```bash
python3 d3/phase165_gizmo_adapter.py phase165_production_live_nbody_manifest.csv RUN_ID \
  --executable /path/to/GIZMO_D3 --mpiexec "srun -n 64" --execute
```

The adapter fails closed if the manifest hash or executable hash differs from the frozen values. It enforces `N_H=N_L`, maps only recognized branch labels, generates/caches deterministic Phase141 M11 ICs, renders a native GIZMO parameter file, and records prelaunch provenance including hashes and the exact MPI command.

Production sites should stage the frozen manifest and the exact proven executable artifact. The existing Phase166 blind validator remains authoritative for final output acceptance; this adapter deliberately does not modify its thresholds.
