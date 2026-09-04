# D3 SIDMx first-pass GIZMO integration

This branch adds a guarded first-pass D3/SIDMx two-species scattering scaffold to GIZMO-public.

## Current execution status

Smoke-test workflow added and refreshed to force a branch update.

## Compile flags

Enable the stock SIDM machinery and the guarded D3 branch:

```c
#define DM_SIDM
#define D3_SIDMX
```

`DM_SIDM` keeps the original GIZMO SIDM neighbor search, timestep limiting, wakeup, and bookkeeping active. `D3_SIDMX` swaps the stock scalar SIDM pair probability/kick branch for a two-species D3 branch.

## Species routing

First-pass routing uses particle type rather than adding a new particle field:

- Type 2 -> heavy species H
- Type 3 -> light species L
- Other types -> ignored by the D3 branch

The IC/parameter setup must enforce:

- `N_H = N_L`
- `m_H / m_L = 3`
- mass table Type 2 / Type 3 = 3

## Patch target

The main patch target is:

```text
sidm/sidm_core_flux_computation.h
```

That is where GIZMO already checks SIDM candidate pairs, prevents duplicate pair evaluation, calls `prob_of_interaction`, and applies the collision kick.

## New file

```text
sidm/d3_sidmx_kernel_inline.h
```

This header is intentionally header-only for first-pass integration so the GIZMO build system does not need Makefile edits yet.

## Hard warnings

This is a first-pass research scaffold, not final validated production physics.

Before production launch, the patched binary must pass:

1. Compile with `DM_SIDM + D3_SIDMX`.
2. Type routing test: Type 2 = H, Type 3 = L.
3. HH/LL/HL/LH two-particle forced-collision conservation test.
4. No-double-kick test.
5. M11 IC validation.
6. Row-0 commissioning.
7. Full Phase165 production manifest.
8. Frozen blind validator on real outputs.

If any of those fail, production remains blocked.
