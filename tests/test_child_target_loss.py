"""Only child-authored record body tokens are supervised in the scout."""
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6 import preschool
from organism_v6.train_adapter import child_record_prefix_length, child_target_mask


class ChildTargetTests(unittest.TestCase):
    def test_prefix_and_boundary_straddles_are_not_targets(self):
        text = "Program event.\nMy measured action record: I measured 20%."
        prefix = child_record_prefix_length(text)
        offsets = [(0, 7), (7, prefix - 1), (prefix - 1, prefix + 1),
                   (prefix + 1, prefix + 10), (0, 0)]
        self.assertEqual(child_target_mask(offsets, prefix, [1, 1, 1, 1, 0]),
                         [False, False, False, True, False])

    def test_no_surviving_target_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "no child target"):
            child_target_mask([(0, 4), (4, 9)], 10, [1, 1])

    def test_bad_wrappers_fail_closed(self):
        for text in ("teacher text", "Program e.\nMy measured action record: ",
                     "Program e.\nMy measured action record: A\nMy measured action record: B"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                child_record_prefix_length(text)

    def test_mismatched_masks_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "disagree"):
            child_target_mask([(5, 9)], 4, [])

    def test_pre_outcome_record_is_rejected(self):
        outcome = "instructions 1000 -> 800 (20.0% reduction)"
        action = dict(kind="act", execution_id="event1", episode_id="train/item",
                      tick=1, action="-mem2reg", outcome=outcome)
        record = dict(action, kind="note_after", **preschool.parse_outcome(outcome))
        record["text"] = "I ran -mem2reg. Instructions went from 1000 to 800, a 20.0% reduction."
        with tempfile.TemporaryDirectory() as directory:
            sleep = Path(directory) / "sleep_0032"
            sleep.mkdir()
            result = preschool.gate_sleep([record, action], directory, str(sleep), "enforce")
            self.assertEqual(result["rejection_families"], {"provenance-pre-outcome-record": 1})
            self.assertTrue(result["training_skipped"])
            self.assertEqual(json.loads((sleep / "corpus.json").read_text())["corpus"], [])


if __name__ == "__main__":
    unittest.main()
