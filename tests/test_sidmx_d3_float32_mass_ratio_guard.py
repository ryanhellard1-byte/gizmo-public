#!/usr/bin/env python3
"""Regression gate for the D3 3:1 macro-mass startup contract.

GADGET format-1 stores particle masses as IEEE-754 float32. The H and L
masses are rounded independently, so a generator-level exact 3:1 ratio must
be checked at the precision of the stored representation rather than against
an arbitrary double-precision tolerance.
"""
from __future__ import annotations

import re
from pathlib import Path

TARGET = 3.0
FLT_EPSILON = 2.0 ** -23
RATIO_TOL = 2.0 * FLT_EPSILON * TARGET
OBSERVED_PHASE172_R0_RATIO = 2.9999997822839202


def accepted(ratio: float) -> bool:
    return abs(ratio - TARGET) <= RATIO_TOL


def main() -> int:
    assert accepted(OBSERVED_PHASE172_R0_RATIO), (OBSERVED_PHASE172_R0_RATIO, RATIO_TOL)
    assert not accepted(2.999999)
    assert not accepted(3.000001)
    assert not accepted(1.0)

    source = Path(__file__).resolve().parents[1] / "sidm" / "sidm_core.c"
    text = source.read_text()
    assert "const double ratio_target = 3.0;" in text
    assert "const double ratio_tol = 2.0 * FLT_EPSILON * ratio_target;" in text
    assert re.search(r"fabs\(ratio\s*-\s*ratio_target\)\s*>\s*ratio_tol", text)
    assert "fabs(ratio - 3.0) > 3.0e-8" not in text

    print(
        "PASS: float32-aware D3 mass-ratio guard "
        f"tol={RATIO_TOL:.17g} observed_error="
        f"{abs(OBSERVED_PHASE172_R0_RATIO - TARGET):.17g}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
