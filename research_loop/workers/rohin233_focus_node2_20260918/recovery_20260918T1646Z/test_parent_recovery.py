"""Small CPU seam tests; no process control or provider calls."""

import unittest

from c0_parent import replacements
from caption_endpoint import scoped_inspector
from observe import native_command


class ParentRecoveryTests(unittest.TestCase):
    def test_timeout_wrapper_is_not_a_second_native(self):
        command = [b'/owned/venv/bin/python', b'-B', b'-m', b'gpu.r233_node2_recovery', b'native',
            b'--config', b'/owned/GUARD.json']
        self.assertTrue(native_command(command, '/owned/GUARD.json'))
        self.assertFalse(native_command([b'timeout', b'100s'] + command, '/owned/GUARD.json'))
        self.assertFalse(native_command(command, '/different/GUARD.json'))

    def test_caption_only_current_loaded_records(self):
        original = "headers = [focus.metadata(path) for path in paths[-256:]]\nloaded_headers = [focus.metadata(path) for path in paths[:8]]"
        output = scoped_inspector(original, 3304)
        self.assertIn("entry['index'] >= 3304", output)
        self.assertIn('00000000000000003304.json', output)
        self.assertNotIn('paths[:8]', output)
        with self.assertRaises(ValueError):
            scoped_inspector(original.replace('paths[:8]', 'paths[:16]'), 3304)

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
