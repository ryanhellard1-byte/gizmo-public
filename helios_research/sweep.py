from __future__ import annotations

import csv
from itertools import product

from model import PlasmaState, hellard_optimum_angle_deg, helical_pitch_ratio


def run_sweep(output_csv: str = "hellard_angle_sweep.csv") -> int:
    chi_es = [2, 5, 10, 20, 50]
    chi_alphas = [0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10]
    weights = [0.25, 0.5, 0.75]

    rows = []
    for ce, ca, wa in product(chi_es, chi_alphas, weights):
        s = PlasmaState(ce, ca, wa)
        rows.append(
            {
                "chi_e": ce,
                "chi_alpha": ca,
                "w_alpha": wa,
                "theta_opt_deg": hellard_optimum_angle_deg(s),
                "Btheta_over_Bz": helical_pitch_ratio(s),
            }
        )

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    count = run_sweep()
    print(f"wrote {count} cases")
