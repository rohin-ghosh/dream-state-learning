"""Post-freeze readout safety tests; not part of the native executable snapshot."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from gpu import orch_code_channel_reduce as reducer
from gpu.orch_code_channel_screen import generate
from organism_v6 import orch_code_channel as policy
from tests.orch_code_channel_test import TASK, result


class ReadoutTests(unittest.TestCase):
    def test_unread_rows_stay_unreviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'LEGACY').mkdir()
            tasks = [dict(TASK, id=number) for number in range(64)]
            call = result('I add the arguments.\n{"expression":"left+right"}')
            call['messages'] = policy.prompt(tasks[0], 'LEGACY')[0]
            row = policy.capture(tasks[0], 'LEGACY', call)
            row['position'] = 0
            (root / 'LEGACY/CALL_000.json').write_text(json.dumps(row))
            rows, summary = reducer.audit(dict(tasks=tasks), root, {})
            self.assertEqual(rows[0]['semantic_status'], 'UNREVIEWED')
            self.assertFalse(rows[0]['admitted'])
            self.assertFalse(summary['candidate'])
            self.assertFalse(summary['native_call_coverage_complete'])
            self.assertFalse(summary['primary_refuted_by_necessary_gate'])
            self.assertEqual(summary['arms']['SEPARATED']['qualified_task_bounds'], [0, 64])

    def test_unknown_review_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                reducer.audit(dict(tasks=[dict(TASK, id=number) for number in range(64)]),
                              Path(directory), {'unknown': {}})

    def test_json_tuple_feedback_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'LEGACY').mkdir()
            tasks = [dict(TASK, id=number) for number in range(64)]
            call = result('{"expression":"(left,right)"}')
            call['messages'] = policy.prompt(tasks[0], 'LEGACY')[0]
            row = policy.capture(tasks[0], 'LEGACY', call)
            self.assertEqual(row['feedback']['observed'], (2, 3))
            row['position'] = 0
            (root / 'LEGACY/CALL_000.json').write_text(json.dumps(row))
            rows, summary = reducer.audit(dict(tasks=tasks), root, {})
            self.assertFalse(rows[0]['outcome_pass'])
            self.assertEqual(rows[0]['feedback']['observed'], [2, 3])

    def test_context_budget_not_truncated(self):
        engine = Mock()
        engine.tokenizer.apply_chat_template.return_value = [1] * 2561
        with self.assertRaisesRegex(ValueError, 'context_bound'):
            generate(engine, [], 1536)
        engine.model.generate.assert_not_called()

    def test_only_frozen_ceilings(self):
        with self.assertRaisesRegex(ValueError, 'prospective_source'):
            generate(Mock(), [], 1600)


if __name__ == '__main__':
    unittest.main()
