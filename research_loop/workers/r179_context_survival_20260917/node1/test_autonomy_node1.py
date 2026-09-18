"""CPU-only checks of milestone separation and no-signal rearm selection."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('autonomy_node1', HERE / 'autonomy_node1.py')
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


class AutonomyTests(unittest.TestCase):
    def test_complete_proof_posting_does_not_require_pending_progress(self):
        run = MONITOR.HERE / 'AUTONOMY_fixture'
        receipt = dict(path=str(run / 'proof.json'), sha256='b' * 64)
        observed = dict(status='POST_SLEEP_PROMPT_HISTORY_CUSTODY_VERIFIED', cycle=42,
                        sleep_complete_sha256='c' * 64, post_sleep_request_sha256='d' * 64,
                        full_raw_and_visible_history_preserved=True)
        loaded = dict(actor_pid=123, actor_start_ticks='456', saved_cycle=41, optimizer_steps=10, observed_unix=1)
        row = dict(physical=3, attempt=2, loaded=loaded, loaded_sha256='a' * 64, names=[], cursor=4)
        state = dict(cursors={}, observed={}, finished=[], rearm_attempted=[], posted=[])
        with patch.object(MONITOR, 'observe', return_value=(receipt, observed)), patch.object(MONITOR, 'post') as post:
            MONITOR.process_row(run, state, row, run / 'snapshot.json')
        self.assertEqual([call.args[2] for call in post.call_args_list],
                         ['LOADED:' + 'a' * 64, 'RETAINED_SLEEP_COMPLETE:2:3', 'POST_SLEEP_PROMPT_CUSTODY:2:3'])
        self.assertEqual(state['finished'], ['2:3'])

    def test_tail_does_not_export_training_text(self):
        record = dict(document={'messages': 'private fixture ' * 1000}, index=51, journal_id='fixture', kind='SLEEP_COMPLETE',
                      previous_sha256='a' * 64, schema='fixture', sha256='b' * 64)
        raw = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(MONITOR.tail_metadata(raw[-4096:], 51), dict(index=51, kind='SLEEP_COMPLETE', sha256='b' * 64))

    def test_wrong_tail_index_rejected(self):
        raw = json.dumps(dict(document={}, index=1, journal_id='fixture', kind='UPDATE',
                              previous_sha256='a' * 64, schema='fixture', sha256='b' * 64), sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError, 'actual_record_tail_identity'):
            MONITOR.tail_metadata(raw, 2)

    def test_metadata_kind_cannot_be_child_text(self):
        raw = json.dumps(dict(document={}, index=1, journal_id='fixture', kind='some child text',
                              previous_sha256='a' * 64, schema='fixture', sha256='b' * 64), sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError, 'actual_record_tail_identity'):
            MONITOR.tail_metadata(raw, 1)

    def test_retention_marker_is_not_completed_sleep(self):
        self.assertEqual(MONITOR.custody_events(dict(status='CONTEXT_RETAINED_SLEEP_IN_PROGRESS')), [])

    def test_completed_sleep_is_not_post_sleep_prompt(self):
        self.assertEqual(MONITOR.custody_events(dict(status='COMPLETED_RETAINED_SLEEP_WAITING_POST_SLEEP_REQUEST',
                         progress={'records': {'sleep_complete': {'sha256': 'a' * 64}}})), ['RETAINED_SLEEP_COMPLETE'])

    def test_positive_complete_custody_has_two_separate_milestones(self):
        self.assertEqual(MONITOR.custody_events(dict(status='POST_SLEEP_PROMPT_HISTORY_CUSTODY_VERIFIED',
                                                   full_raw_and_visible_history_preserved=True)),
                         ['RETAINED_SLEEP_COMPLETE', 'POST_SLEEP_PROMPT_CUSTODY'])

    def test_clean_expiry_can_rearm(self):
        row = dict(physical=5, attempt=2, names=['NO_BOUNDARY.json'], loaded=None, operator_state='ABSENT',
                   remaining_seconds=-1, timeout={'original_left_running': True})
        self.assertTrue(MONITOR.can_rearm(row))
        for updates in ({'operator_state': 'S'}, {'remaining_seconds': 1}, {'loaded': {}}, {'attempt': 3}, {'physical': 4},
                        {'successor_epoch_exists': True},
                        {'names': ['NO_BOUNDARY.json', 'BOUNDARY.json']}, {'names': ['NO_BOUNDARY.json', 'FAILURE_1.json']}):
            changed = deepcopy(row)
            changed.update(updates)
            with self.subTest(updates=updates):
                self.assertFalse(MONITOR.can_rearm(changed))


if __name__ == '__main__':
    unittest.main()
