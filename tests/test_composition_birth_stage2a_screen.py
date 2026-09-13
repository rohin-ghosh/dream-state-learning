"""Logical subset checks only; no canonical IDs, runtime or admission gate."""

from collections import Counter
import unittest

from organism_v6 import composition_birth_stage2a_primitives as primitives
from organism_v6 import composition_birth_stage2a_screen as source


class ScreenTests(unittest.TestCase):
    def test_exact_reduced_counts_and_original_ordinals(self):
        roster = source.reduced_screen("D1")
        self.assertEqual(len(roster), 280)
        self.assertEqual(Counter(entry.kind for entry in roster),
                         {"CHAIN": 232, "INTERVENTION": 32, "CANARY": 16})
        self.assertEqual(tuple(dict.fromkeys(entry.index for entry in roster if entry.kind == "CHAIN")),
                         (0, 4, 8, 12, 16, 20, 24, 28))
        self.assertTrue(all(entry.member == 0 for entry in roster if entry.kind == "CHAIN"))
        self.assertEqual(roster[29].slot, primitives.chain_slot("D1", 2, 0, 0))
        self.assertEqual(roster[232].slot, primitives.intervention_slot("D1", "SEEK", 0, 0))
        self.assertEqual(roster[-1].slot, primitives.canary_slot("D1", 15))
        self.assertEqual(len({entry.slot.global_ordinal for entry in roster}), 280)

    def test_every_skill_contains_exact_four_paired_indices(self):
        for transition in primitives.TRANSITIONS:
            selected = tuple(entry for entry in source.reduced_screen("D1") if entry.transition == transition)
            self.assertEqual(tuple((entry.index, entry.member) for entry in selected),
                             tuple((pair, member) for pair in (0, 2, 4, 6) for member in (0, 1)))

    def test_preservation_reorders_but_never_renumbers_or_duplicates(self):
        entries = source.preservation_import("D1")
        self.assertEqual(tuple(entry.custody_id for entry in entries),
                         tuple(f"C{index:03d}" for index in range(1, 281)))
        self.assertEqual(entries[0].upstream.kind, "INTERVENTION")
        self.assertEqual(entries[31].upstream.kind, "INTERVENTION")
        self.assertEqual(entries[32].upstream.slot, primitives.chain_slot("D1", 0, 0, 0))
        self.assertEqual(entries[263].upstream.slot, primitives.chain_slot("D1", 14, 0, 28))
        self.assertEqual(tuple(entry.alias_to_cold_canary for entry in entries[264:]), tuple(range(16)))
        self.assertTrue(all(entry.alias_to_cold_canary is None for entry in entries[:264]))
        self.assertEqual({entry.upstream for entry in entries}, set(source.reduced_screen("D1")))

    def test_d2_uses_reserved_offset_and_same_subset(self):
        for first, second in zip(source.reduced_screen("D1"), source.reduced_screen("D2")):
            self.assertEqual(second.slot.global_ordinal, first.slot.global_ordinal + 1008)
            self.assertEqual((first.kind, first.index, first.member, first.transition),
                             (second.kind, second.index, second.member, second.transition))

    def test_same_stage_pairing_has_same_seed_and_closed_gates(self):
        master = b"synthetic-screen-fixture"
        first = source.reduced_decode_seeds("D1", master=master)
        self.assertEqual(first, source.reduced_decode_seeds("D1", master=master))
        for entry, seed in zip(source.reduced_screen("D1"), first):
            self.assertEqual(seed, primitives.decode_seed(master, entry.slot.panel_label,
                                                          entry.slot.global_ordinal))
        self.assertFalse(any(source.SCIENCE_GATES.values()))
        for stage in ("BASE", "P31", 1, None):
            with self.assertRaises(ValueError):
                source.reduced_screen(stage)


if __name__ == "__main__":
    unittest.main()
