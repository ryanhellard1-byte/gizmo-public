#!/usr/bin/env python3
"""Fail-closed checker for SIDMx-D3 live-engine AUDIT lines."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

CHANNELS = ("HH", "LL", "HL")


def parse_value(x: str):
    try:
        if any(c in x for c in ".eE"):
            return float(x)
        return int(x)
    except ValueError:
        return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--mode", type=int, required=True)
    ap.add_argument("--signal-channels", nargs="*", choices=CHANNELS, default=[])
    ap.add_argument("--forbid-channels", nargs="*", choices=CHANNELS, default=[])
    ap.add_argument("--expect-null", action="store_true")
    ap.add_argument("--min-expected", type=float, default=2.0)
    ap.add_argument("--sigma-tolerance", type=float, default=5.0)
    ap.add_argument("--max-conservation-residual", type=float, default=1.0e-12)
    ap.add_argument("--max-probability", type=float, default=0.2)
    args = ap.parse_args()

    rows = []
    for line in Path(args.log).read_text(errors="replace").splitlines():
        if not line.startswith("SIDMx-D3 AUDIT "):
            continue
        row = {}
        for key, val in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line):
            row[key] = parse_value(val)
        rows.append(row)

    if not rows:
        raise SystemExit("FAIL: no SIDMx-D3 AUDIT rows found")
    if any(int(r.get("mode", -1)) != args.mode for r in rows):
        raise SystemExit("FAIL: audit contains unexpected D3 mode")

    totals = {}
    for ch in CHANNELS:
        totals[f"pairs_{ch}"] = sum(int(r.get(f"pairs_{ch}", 0)) for r in rows)
        totals[f"expected_{ch}"] = sum(float(r.get(f"expected_{ch}", 0.0)) for r in rows)
        totals[f"events_{ch}"] = sum(int(r.get(f"events_{ch}", 0)) for r in rows)
        totals[f"pgt02_{ch}"] = sum(int(r.get(f"pgt02_{ch}", 0)) for r in rows)
        totals[f"pge1_{ch}"] = sum(int(r.get(f"pge1_{ch}", 0)) for r in rows)
        totals[f"maxprob_{ch}"] = max(float(r.get(f"maxprob_{ch}", 0.0)) for r in rows)

    max_mom = max(float(r.get("max_momentum_residual", 0.0)) for r in rows)
    max_energy = max(float(r.get("max_energy_residual", 0.0)) for r in rows)
    totals["max_momentum_residual"] = max_mom
    totals["max_energy_residual"] = max_energy
    totals["audit_rows"] = len(rows)

    if args.expect_null:
        for ch in CHANNELS:
            if abs(totals[f"expected_{ch}"]) > 1e-15 or totals[f"events_{ch}"] != 0:
                raise SystemExit(
                    f"FAIL: null mode has {ch} expected={totals[f'expected_{ch}']:.6g} events={totals[f'events_{ch}']}"
                )

    signal_results = {}
    for ch in args.signal_channels:
        lam = totals[f"expected_{ch}"]
        obs = totals[f"events_{ch}"]
        if lam < args.min_expected:
            raise SystemExit(f"FAIL: expected_{ch}={lam:.6g} < min {args.min_expected}")
        if obs <= 0:
            raise SystemExit(f"FAIL: no accepted {ch} collisions")
        allowance = max(5.0, args.sigma_tolerance * math.sqrt(max(lam, 1.0)))
        if abs(obs - lam) > allowance:
            raise SystemExit(
                f"FAIL: {ch} observed={obs} expected={lam:.6g}; deviation {abs(obs-lam):.6g} > {allowance:.6g}"
            )
        signal_results[ch] = {
            "observed": obs,
            "expected_sum_probability": lam,
            "poisson_sigma_units": (obs - lam) / math.sqrt(max(lam, 1.0)),
        }

    for ch in args.forbid_channels:
        if abs(totals[f"expected_{ch}"]) > 1e-15 or totals[f"events_{ch}"] != 0:
            raise SystemExit(
                f"FAIL: forbidden {ch} channel has expected={totals[f'expected_{ch}']:.6g} events={totals[f'events_{ch}']}"
            )

    if any(totals[f"pge1_{ch}"] for ch in CHANNELS):
        raise SystemExit("FAIL: p>=1 event-probability evaluations occurred")
    if max(totals[f"maxprob_{ch}"] for ch in CHANNELS) > args.max_probability:
        raise SystemExit("FAIL: pair probability exceeded commissioning ceiling")
    if max_mom > args.max_conservation_residual:
        raise SystemExit(f"FAIL: momentum residual {max_mom:.6g} too large")
    if max_energy > args.max_conservation_residual:
        raise SystemExit(f"FAIL: energy residual {max_energy:.6g} too large")

    report = {
        "status": "PASS",
        "mode": args.mode,
        "signal_channels": signal_results,
        "forbid_channels": args.forbid_channels,
        "expect_null": args.expect_null,
        **totals,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
