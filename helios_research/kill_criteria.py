from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    combined_peak_pitch: float
    peak_prominence: float
    multi_scale_repeatability: float
    max_mrt_growth: float
    target_gain: float


def evaluate(result: ValidationResult) -> tuple[bool, list[str]]:
    """Return pass/fail for the research hypothesis, not for a flight vehicle."""
    failures: list[str] = []

    if not 1.15 <= result.combined_peak_pitch <= 1.60:
        failures.append("combined optimum falls outside predicted Hellard pitch band")
    if result.peak_prominence < 0.05:
        failures.append("interior optimum is too weak to distinguish from a flat response")
    if result.multi_scale_repeatability < 0.7:
        failures.append("optimum does not repeat across target scales/plasma regimes")
    if result.max_mrt_growth > 10:
        failures.append("MRT growth exceeds current research gate")
    if result.target_gain < 5:
        failures.append("target/system gain gate fails")

    return (not failures, failures)


if __name__ == "__main__":
    demo = ValidationResult(
        combined_peak_pitch=1.35,
        peak_prominence=0.08,
        multi_scale_repeatability=0.8,
        max_mrt_growth=8,
        target_gain=6,
    )
    print(evaluate(demo))
