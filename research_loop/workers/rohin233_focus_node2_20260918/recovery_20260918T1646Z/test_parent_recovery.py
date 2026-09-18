"""Small CPU seam tests; no process control or provider calls."""

import unittest

from c0_parent import replacements


class ParentRecoveryTests(unittest.TestCase):
    def test_only_finite_epoch_source_and_current_record_floor_change(self):
        original = "\n".join((
            "require((legacy_directory/'EXIT.json').is_file() and (legacy_directory/control_name).is_file(), 'supported_old_reading_handoff_complete')",
            "state['record_cursor'] = min(state['record_cursor'], state['pending']['inbox']['index'])",
            "ROOT/'control/PLAN.json'", "ROOT/'source'", "keep_topics_and_parent_prompts()"))
        result = replacements(original, 3000)
        self.assertIn('max(state[\'record_cursor\'], 3000)', result)
        self.assertIn('verified_naturally_exited_previous_epoch', result)
        self.assertIn("ROOT/'control_r233_recovery/PLAN.json'", result)
        self.assertIn('keep_topics_and_parent_prompts()', result)
        self.assertNotIn('CANCEL_CURRICULUM_SERVICE', result)
        with self.assertRaises(ValueError):
            replacements(original + "\nROOT/'source'", 3000)


if __name__ == '__main__':
    unittest.main()
