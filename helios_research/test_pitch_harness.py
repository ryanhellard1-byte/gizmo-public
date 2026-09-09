from pitch_harness import SweepCase, combined_score, PITCHES
from kill_criteria import ValidationResult, evaluate


def test_representative_discrete_peak_near_135():
    case = SweepCase(chi_e=10, chi_alpha=1, w_alpha=0.5, magnetic_tension=1.0, burn_weight=0.5)
    scored = [combined_score(case, p) for p in PITCHES]
    best = max(scored, key=lambda row: row["score"])
    assert best["pitch"] in (1.35, 1.75)


def test_kill_criteria_pass():
    ok, failures = evaluate(
        ValidationResult(
            combined_peak_pitch=1.35,
            peak_prominence=0.08,
            multi_scale_repeatability=0.8,
            max_mrt_growth=8,
            target_gain=6,
        )
    )
    assert ok
    assert not failures


def test_kill_criteria_reject_boundary_peak():
    ok, failures = evaluate(
        ValidationResult(
            combined_peak_pitch=2.5,
            peak_prominence=0.08,
            multi_scale_repeatability=0.8,
            max_mrt_growth=8,
            target_gain=6,
        )
    )
    assert not ok
    assert failures


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("pitch harness tests passed")
