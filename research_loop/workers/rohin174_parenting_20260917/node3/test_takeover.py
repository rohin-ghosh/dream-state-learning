"""CPU-only takeover checks, with no subprocess signals or filesystem mutation."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


specification = importlib.util.spec_from_file_location('node3_takeover', Path(__file__).with_name('takeover.py'))
operator = importlib.util.module_from_spec(specification)
specification.loader.exec_module(operator)


class TakeoverTests(unittest.TestCase):
    def test_identity_rejects_reused_pid(self):
        old = dict(pid=12, ticks='100', argv=['parent', 'serve'])
        self.assertTrue(operator.same(old, dict(old)))
        self.assertFalse(operator.same(old, dict(old, ticks='101')))
        self.assertFalse(operator.same(old, dict(old, argv=['child'])))

    def test_release_exact_six_assignments(self):
        helper, rows = operator.release()
        self.assertEqual({physical: (row['arm'], row['cadence']) for physical, row in rows.items()},
                         {0: ('A', 1), 1: ('B', 2), 2: ('C', 3), 3: ('D', 3), 4: ('A', 1), 7: ('C', 3)})

    def test_configuration_keeps_both_lifetime_cursors_and_child(self):
        helper, rows = operator.release()
        original = dict(root='/unchanged/root', source_root='/unchanged/source', hard_end_unix=operator.HARD_END,
                        start_after_request_count=4, start_after_response_count=3)
        for physical, assignment in rows.items():
            with self.subTest(physical=physical), patch.object(operator, 'sha', return_value='pinned'):
                config = operator.make_config(original, assignment, helper, operator.HERE / 'principles',
                    '/unchanged/oldparent', 'started_pin', dict(request_cursor=135, response_cursor=134))
                self.assertEqual(config['start_after_request_count'], 135)
                self.assertEqual(config['start_after_response_count'], 134)
                self.assertEqual(config['root'], original['root'])
                self.assertEqual(config['source_root'], original['source_root'])
                self.assertEqual(config['schedule_on'], 'response')
                self.assertEqual(config['cadence_responses'], assignment['cadence'])
                self.assertEqual(config['hard_end_unix'], operator.HARD_END)

    def test_wrong_wall_is_rejected(self):
        helper, rows = operator.release()
        original = dict(root='/root', source_root='/source', hard_end_unix=operator.HARD_END + 1)
        with patch.object(operator, 'sha', return_value='pinned'), self.assertRaisesRegex(ValueError, 'child_and_wall'):
            operator.make_config(original, rows[0], helper, operator.HERE / 'principles', '/old', 'pin',
                                 dict(request_cursor=5, response_cursor=4))

    def test_outside_scope_write_refused_before_execution(self):
        with patch.object(operator.subprocess, 'run') as runner, self.assertRaisesRegex(ValueError, 'owned_artifacts'):
            operator.write(operator.REPO / 'gpu/NOT_ALLOWED.json', {})
        runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
