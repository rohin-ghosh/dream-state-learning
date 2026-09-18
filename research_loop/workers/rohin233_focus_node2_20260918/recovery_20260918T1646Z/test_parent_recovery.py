"""Small CPU seam tests; no process control or provider calls."""

import unittest
from unittest.mock import patch

from c0_parent import parent_identity, priority_chooser, replacements
from caption_endpoint import scoped_inspector
from observe import current_loaded, native_command


class ParentRecoveryTests(unittest.TestCase):
    def test_urgent_parent_turn_is_once_without_overlapping_pending(self):
        choose = priority_chooser(lambda state: 'normal', 'recall')
        state = {'pending': {'id': 'actual'}}
        self.assertEqual(choose(state), 'normal')
        self.assertNotIn('r233_priority_turn', state)
        state['pending'] = None
        self.assertEqual(choose(state), 'recall')
        self.assertTrue(state['r233_priority_turn'])
        self.assertEqual(choose(state), 'normal')

    def test_parent_identity_keeps_actual_journal(self):
        observed = {'native': {'pid': 42, 'start_ticks': 9}, 'loaded': {'index': 123},
            'original_journal_id': 'actual-journal'}
        actual = parent_identity(observed, '/owned/C0')
        self.assertEqual(actual['journal_id'], 'actual-journal')
        self.assertEqual(actual['pid'], 42)
        self.assertEqual(actual['start_ticks'], 9)

    def test_loaded_remains_visible_beyond_tail_window(self):
        paths = list(range(600))
        record = {'document': {'pid': 42, 'loaded_unix': 100}}
        with patch('observe.header', side_effect=lambda path: {'kind': 'LOADED' if path == 12 else 'UPDATE'}), \
                patch('observe.checked', return_value=record) as reader:
            self.assertEqual(current_loaded(paths, {'pid': 42}, 99), record)
            reader.assert_called_once_with(12)

    def test_inherited_or_reused_pid_is_not_current_loaded(self):
        with patch('observe.header', return_value={'kind': 'LOADED'}), \
                patch('observe.checked', return_value={'document': {'pid': 42, 'loaded_unix': 10}}):
            self.assertIsNone(current_loaded([1], {'pid': 42}, 100))
            self.assertIsNone(current_loaded([1], {'pid': 43}, 10))
            self.assertIsNone(current_loaded([1], None, 0))

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
