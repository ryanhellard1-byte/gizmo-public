#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase181_collision_summary.py"
spec = importlib.util.spec_from_file_location("p181_collision", MOD_PATH)
assert spec and spec.loader
p181 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p181)


def audit_line(*, task=0, ti=10, mode=2, hh=(0,0,0,0,0,0.0,0.0,0.0),
               ll=(0,0,0,0,0,0.0,0.0,0.0), hl=(10,2,1,0,0,1.5,0.3,0.19),
               dp=1e-16, dk=2e-16):
    # channel tuple: pairs, events, pgt02, pge1, unused, expected, expected2, maxprob
    values = {"HH": hh, "LL": ll, "HL": hl}
    parts = [f"SIDMx-D3 AUDIT task={task} ti={ti} mode={mode}"]
    for key_i, field in ((0,"pairs"),(5,"expected"),(6,"expected2"),(1,"events"),
                         (2,"pgt02"),(3,"pge1"),(7,"maxprob")):
        parts.extend(f"{field}_{ch}={values[ch][key_i]}" for ch in p181.CHANNELS)
    parts.append(f"max_momentum_residual={dp}")
    parts.append(f"max_energy_residual={dk}")
    return " ".join(parts)


class Phase181CollisionSummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def log(self, text: str) -> Path:
        p = self.root / "gizmo.log"
        p.write_text(text + "\n")
        return p

    def test_d3_aggregates_tasks_and_time_scoped_clipping(self):
        log = self.log("\n".join([
            audit_line(task=0, ti=10, mode=2, hl=(10,2,1,0,0,1.5,0.3,0.19)),
            audit_line(task=1, ti=10, mode=2, hl=(30,3,2,0,0,2.5,0.4,0.18)),
            audit_line(task=0, ti=20, mode=2, hl=(20,4,0,0,0,3.0,0.5,0.10)),
        ]))
        rows, report = p181.summarize({"run_id":"R","runtime_interaction_parameter":"-2"}, log)
        hl = next(r for r in rows if r["channel"] == "HL")
        self.assertEqual(hl["collision_count"], 9)
        self.assertEqual(hl["pair_evaluations"], 60)
        self.assertAlmostEqual(hl["expected_sum_probability"], 7.0)
        # ti=10 is globally 3/40; ti=20 is 0/20, so max is 0.075.
        self.assertAlmostEqual(hl["prob_clip_fraction_max"], 0.075)
        self.assertEqual(report["audit_mode"], 2)
        self.assertEqual(hl["mean_mu"], "")
        self.assertEqual(hl["mean_sigma_factor"], "")

    def test_positive_standard_sidm_requires_mode10(self):
        log = self.log(audit_line(mode=10, hh=(5,1,0,0,0,0.4,0.05,0.1),
                                  ll=(5,1,0,0,0,0.4,0.05,0.1),
                                  hl=(10,2,0,0,0,0.8,0.1,0.1)))
        rows, report = p181.summarize({"run_id":"EQ","runtime_interaction_parameter":"1.125"}, log)
        self.assertEqual(report["audit_mode"], 10)
        self.assertEqual(sum(r["collision_count"] for r in rows), 4)

    def test_positive_standard_sidm_wrong_mode_fails(self):
        log = self.log(audit_line(mode=8))
        with self.assertRaises(p181.EvidenceError):
            p181.summarize({"run_id":"EQ","runtime_interaction_parameter":"1.125"}, log)

    def test_nonzero_runtime_without_audit_fails(self):
        log = self.log("ordinary log line")
        with self.assertRaises(p181.EvidenceError):
            p181.summarize({"run_id":"R","runtime_interaction_parameter":"-1"}, log)

    def test_collisionless_control_emits_zero_coverage_row(self):
        log = self.log("Final time=1 reached. Simulation ends.")
        rows, report = p181.summarize({"run_id":"CDM","runtime_interaction_parameter":"0"}, log)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["channel"], "NONE")
        self.assertEqual(rows[0]["collision_count"], 0)
        self.assertEqual(report["audit_mode"], 0)

    def test_collisionless_control_with_audit_fails(self):
        log = self.log(audit_line(mode=9))
        with self.assertRaises(p181.EvidenceError):
            p181.summarize({"run_id":"CDM","runtime_interaction_parameter":"0"}, log)

    def test_pge1_is_fatal(self):
        log = self.log(audit_line(mode=2, hl=(10,2,0,1,0,1.5,0.3,1.1)))
        with self.assertRaises(p181.EvidenceError):
            p181.summarize({"run_id":"R","runtime_interaction_parameter":"-2"}, log)

    def test_unexpected_audit_line_can_be_mpi_prefixed(self):
        line = "[1,0]<stdout>:" + audit_line(mode=2)
        rows, _ = p181.summarize({"run_id":"R","runtime_interaction_parameter":"-2"}, self.log(line))
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
