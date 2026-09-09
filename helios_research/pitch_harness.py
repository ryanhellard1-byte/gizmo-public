from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from itertools import product

from model import PlasmaState, burn_transport_score


PITCHES = [0.0, 0.5, 0.75, 1.0, 1.35, 1.75, 2.5]


@dataclass(frozen=True)
class SweepCase:
    chi_e: float
    chi_alpha: float
    w_alpha: float
    magnetic_tension: float
    burn_weight: float


def pitch_to_theta_rad(pitch: float) -> float:
    return math.atan(pitch)


def mrt_rms_proxy(pitch: float, magnetic_tension: float) -> float:
    phis = [math.radians(x) for x in range(0, 181, 2)]
    growths = []
    norm = math.sqrt(1.0 + pitch * pitch)
    for ph in phis:
        projection = (math.cos(ph) + pitch * math.sin(ph)) / norm
        gamma2 = max(0.0, 1.0 - magnetic_tension * projection * projection)
        growths.append(math.sqrt(gamma2))
    return math.sqrt(sum(g * g for g in growths) / len(growths))


def combined_score(case: SweepCase, pitch: float) -> dict[str, float]:
    state = PlasmaState(case.chi_e, case.chi_alpha, case.w_alpha)
    theta = pitch_to_theta_rad(pitch)
    burn = max(1e-15, burn_transport_score(theta, state))
    mrt = mrt_rms_proxy(pitch, case.magnetic_tension)
    stability = max(1e-15, 1.0 - mrt)
    score = burn ** case.burn_weight * stability ** (1.0 - case.burn_weight)
    return {
        "pitch": pitch,
        "theta_deg": math.degrees(theta),
        "burn": burn,
        "mrt_rms": mrt,
        "stability": stability,
        "score": score,
    }


def run_matrix(output_csv: str = "pitch_matrix.csv") -> list[dict[str, float]]:
    cases = [
        SweepCase(*vals)
        for vals in product(
            [5.0, 10.0, 20.0],
            [0.5, 1.0, 2.0],
            [0.25, 0.5, 0.75],
            [0.3, 0.6, 1.0, 1.5, 2.0],
            [0.25, 0.5, 0.75],
        )
    ]
    rows = []
    for case in cases:
        scored = [combined_score(case, pitch) for pitch in PITCHES]
        best = max(scored, key=lambda row: row["score"])
        for row in scored:
            rows.append(
                {
                    "chi_e": case.chi_e,
                    "chi_alpha": case.chi_alpha,
                    "w_alpha": case.w_alpha,
                    "magnetic_tension": case.magnetic_tension,
                    "burn_weight": case.burn_weight,
                    **row,
                    "is_best": row["pitch"] == best["pitch"],
                }
            )
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    rows = run_matrix()
    print(f"wrote {len(rows)} rows")
