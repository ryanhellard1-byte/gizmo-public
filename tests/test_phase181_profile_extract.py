#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "d3" / "production" / "phase181_profile_extract.py"
spec = importlib.util.spec_from_file_location("p181_profile", MOD_PATH)
assert spec and spec.loader
p181 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p181)


def record(payload: bytes) -> bytes:
    return struct.pack("<I", len(payload)) + payload + struct.pack("<I", len(payload))


def write_snapshot(path: Path, *, time_code=0.0, mass_table=False, duplicate_id=False):
    npart = [0, 4, 4, 0, 0, 0]
    header = bytearray(256)
    struct.pack_into("<6I", header, 0, *npart)
    mt = [0.0] * 6
    if mass_table:
        mt[1], mt[2] = 3.0, 1.0
    struct.pack_into("<6d", header, 24, *mt)
    struct.pack_into("<d", header, 72, time_code)

    radii = np.array([0.31, 0.36, 0.42, 0.50, 0.32, 0.38, 0.44, 0.52], dtype=np.float32)
    pos = np.column_stack((radii, np.zeros(8, dtype=np.float32), np.zeros(8, dtype=np.float32)))
    vel = np.array([
        [1,1,0],[2,-1,0],[3,1,1],[4,-1,-1],
        [-1,1,0],[-2,-1,0],[-3,1,-1],[-4,-1,1],
    ], dtype=np.float32)
    ids = np.arange(1, 9, dtype=np.uint32)
    if duplicate_id:
        ids[-1] = ids[-2]
    mass = np.r_[np.full(4, 3.0, dtype=np.float32), np.ones(4, dtype=np.float32)]

    blob = record(bytes(header))
    blob += record(pos.astype("<f4").tobytes())
    blob += record(vel.astype("<f4").tobytes())
    blob += record(ids.astype("<u4").tobytes())
    if not mass_table:
        blob += record(mass.astype("<f4").tobytes())
    path.write_bytes(blob)


class Phase181ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixed_profile_contract(self):
        self.assertEqual(p181.N_BINS, 48)
        self.assertAlmostEqual(p181.EDGES_OVER_RS[0], 0.03)
        self.assertAlmostEqual(p181.EDGES_OVER_RS[-1], 5.0)
        self.assertEqual(p181.R_S_KPC, 9.1)
        self.assertEqual(len(p181.EXPECTED_TIMES_GYR), 11)
        self.assertEqual(p181.EXPECTED_TIMES_GYR[-2:], (55.28, 80.0))

    def test_reads_explicit_mass_format1(self):
        path = self.root / "snap"
        write_snapshot(path, time_code=2.5)
        s = p181.read_gadget_format1(path)
        self.assertEqual(len(s.ids), 8)
        self.assertAlmostEqual(s.time_code, 2.5)
        self.assertTrue(np.all(s.ptype[:4] == 1))
        self.assertTrue(np.all(s.ptype[4:] == 2))
        self.assertTrue(np.allclose(s.mass[:4], 3.0))
        self.assertTrue(np.allclose(s.mass[4:], 1.0))

    def test_reads_header_mass_format1_without_mass_record(self):
        path = self.root / "snap"
        write_snapshot(path, mass_table=True)
        s = p181.read_gadget_format1(path)
        self.assertTrue(np.allclose(s.mass[:4], 3.0))
        self.assertTrue(np.allclose(s.mass[4:], 1.0))

    def test_duplicate_particle_ids_fail(self):
        path = self.root / "snap"
        write_snapshot(path, duplicate_id=True)
        with self.assertRaises(p181.ProfileError):
            p181.read_gadget_format1(path)

    def test_centered_state_has_zero_mass_weighted_com_and_bulk(self):
        path = self.root / "snap"
        write_snapshot(path)
        s = p181.read_gadget_format1(path)
        x, v = p181.centered(s)
        self.assertTrue(np.allclose(np.sum(x * s.mass[:,None], axis=0), 0.0, atol=1e-12))
        self.assertTrue(np.allclose(np.sum(v * s.mass[:,None], axis=0), 0.0, atol=1e-12))

    def test_truncated_variable_mass_record_fails_closed(self):
        path = self.root / "snap"
        write_snapshot(path)
        raw = path.read_bytes()
        # Remove the complete mass record.
        mass_payload = 8 * 4
        path.write_bytes(raw[:-(mass_payload + 8)])
        with self.assertRaises((p181.ProfileError, TypeError)):
            p181.read_gadget_format1(path)


if __name__ == "__main__":
    unittest.main()
