from collections import Counter
from dataclasses import FrozenInstanceError
from hashlib import sha256
from unittest.mock import patch
import unittest

from organism_v6 import composition_birth_stage2a_tape as source


class PresentationTapeTests(unittest.TestCase):
    MASTER = b"SYNTHETIC-TAPE-ONLY"

    def setUp(self):
        self.roster = [f"p{pair:02}/m{member}/u{slot}" for pair in range(32)
                       for member in range(2) for slot in range(4)]
        self.tape = source.build_presentation_tape(master=self.MASTER, unit_ids=self.roster)

    def test_exact_unit_roster_and_input_permutation_invariance(self):
        self.assertEqual(source.unit_identifiers(), tuple(self.roster))
        self.assertEqual(self.tape, source.build_presentation_tape(master=self.MASTER,
                                                                 unit_ids=list(reversed(self.roster))))
        self.assertEqual(self.tape, source.build_presentation_tape(master=self.MASTER,
                                                                 unit_ids=self.roster[70:] + self.roster[:70]))

    def test_independent_digest_order_and_eight_rotations(self):
        order = sorted(self.roster, key=lambda unit: (
            sha256(self.MASTER + b"\x00target-order\x00" + unit.encode()).hexdigest(), unit))
        for presentation in range(8):
            observed = [unit for batch in self.tape[64 * presentation:64 * (presentation + 1)]
                        for unit in batch.unit_ids]
            expected = [order[(position + 73 * presentation) % 256] for position in range(256)]
            self.assertEqual(observed, expected)
            self.assertEqual(Counter(observed), Counter(self.roster))

    def test_all_updates_batch_slots_and_rng_seeds(self):
        self.assertEqual(len(self.tape), 512)
        for update, batch in enumerate(self.tape, start=1):
            self.assertEqual(batch.update_number, update)
            self.assertEqual(batch.presentation_index, (update - 1) // 64)
            self.assertEqual(len(batch.unit_ids), 4)
            self.assertEqual(len(set(batch.unit_ids)), 4)
            raw = self.MASTER + b"\0dropout\0" + update.to_bytes(4, "big")
            self.assertEqual(batch.rng_start_seed, int.from_bytes(sha256(raw).digest()[-8:], "big"))

    def test_d1_boundary_and_conditional_d2_continuity(self):
        self.assertEqual(self.tape[255].stage, "D1")
        self.assertEqual(self.tape[255].presentation_index, 3)
        self.assertEqual(self.tape[256].stage, "D2")
        self.assertEqual(self.tape[256].update_number, 257)
        self.assertEqual(self.tape[256].presentation_index, 4)
        for batches, count in ((self.tape[:256], 4), (self.tape, 8)):
            observed = Counter(unit for batch in batches for unit in batch.unit_ids)
            self.assertEqual(observed, {unit: count for unit in self.roster})
            self.assertEqual(sum(observed.values()), 256 * count)

    def test_digest_ties_use_raw_unit_bytes(self):
        with patch.object(source, "sha256") as digest:
            digest.return_value.digest.return_value = b"\0" * 32
            tape = source.build_presentation_tape(master=self.MASTER, unit_ids=list(reversed(self.roster)))
        self.assertEqual(tuple(unit for batch in tape[:64] for unit in batch.unit_ids), tuple(sorted(self.roster)))

    def test_reject_missing_extra_duplicate_and_malformed_ids(self):
        for roster in (self.roster[:-1], self.roster + ["p32/m0/u0"], self.roster[:-1] + [self.roster[0]],
                       self.roster[:-1] + ["p31/m1/u4"], self.roster[:-1] + ["p31/m1/u03"],
                       self.roster[:-1] + [b"p31/m1/u3"], self.roster[:-1] + [None],
                       self.roster[:-1] + ["p31/m1/u3\n"], self.roster[:-1] + ["p31/m1/ü3"], set(self.roster)):
            with self.subTest(roster=repr(roster[-1:]) if isinstance(roster, list) else type(roster)), self.assertRaises(ValueError):
                source.build_presentation_tape(master=self.MASTER, unit_ids=roster)

    def test_master_and_immutability(self):
        for master in (None, "master", b"", b"\0", b"\xff"):
            with self.assertRaises(ValueError):
                source.build_presentation_tape(master=master, unit_ids=self.roster)
        with self.assertRaises(FrozenInstanceError):
            self.tape[0].update_number = 100
        with self.assertRaises(TypeError):
            self.tape[0].unit_ids[0] = "other"
        before = self.tape[0].unit_ids
        self.roster[:] = []
        self.assertEqual(self.tape[0].unit_ids, before)

    def test_symbolic_only_no_runtime_or_science_qualification(self):
        self.assertEqual(source.STATUS, "SYMBOLIC_SOURCE_ONLY")
        self.assertFalse(any(source.SCIENCE_GATES.values()))


if __name__ == "__main__":
    unittest.main()
