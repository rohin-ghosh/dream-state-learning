import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('node5_poll', Path(__file__).with_name('poll_node5.py'))
poll = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(poll)


class LoadReceiptTests(unittest.TestCase):
    def test_staged_started_retired_and_launched_are_distinct(self):
        row = dict(status='WAITING_SAVED_BOUNDARY')
        self.assertEqual(poll.pre_load_status(row), 'ACTUAL_SOURCE_CPU_READY_NOT_STARTED')
        row['operator_started'] = {'path': '/started'}
        self.assertEqual(poll.pre_load_status(row), 'WAITING_SAVED_BOUNDARY')
        row['actual_boundary_ready'] = {'path': '/boundary'}
        self.assertEqual(poll.pre_load_status(row), 'SAVED_BOUNDARY_READY')
        row['owner_retired'] = {'path': '/retired'}
        self.assertEqual(poll.pre_load_status(row), 'OWNER_RETIRED_ADMISSION_PENDING')
        row['admission'] = {'clear': True}
        self.assertEqual(poll.pre_load_status(row), 'OWNER_RETIRED_ADMISSION_CLEAR')
        row['launch'] = {'pid': 123}
        self.assertEqual(poll.pre_load_status(row), 'SUCCESSOR_LAUNCH_RECORDED_LOAD_UNOBSERVED')

    def test_preload_failure_is_not_hidden_by_retirement_or_launch(self):
        row = dict(status='FAILED_CLOSED', failure={'reason': 'scanner'}, owner_retired={}, launch={})
        self.assertEqual(poll.pre_load_status(row), 'FAILED_CLOSED')

    def test_verified_Main_readmission_supersedes_failed_operator_current_state(self):
        row = dict(output='/old', status='FAILED_CLOSED', failure={'retired': True}, operator_live=False)
        receipt = dict(actor_pid=123, actor_start_ticks='456', optimizer_steps=10, adapter_sha256='adapter',
                       loaded_unix=100, loaded_record_sha256='record')
        poll.apply_readmission(row, receipt, dict(output='/recovery', actor_live=True))
        self.assertEqual(row['status'], 'CURRENT_READMISSION_LOADED')
        self.assertEqual(row['output'], '/recovery')
        self.assertNotIn('failure', row)
        self.assertEqual(row['historical_attempt']['failure'], {'retired': True})
        self.assertEqual(row['loaded']['pid'], 123)
        self.assertEqual(row['current_execution_attribution'], 'MAIN_READMISSION')

    def test_actual_native_adapter_sha256_field_matches_saved_state(self):
        event = poll.loaded_metadata(dict(pid=123, resume=True, adapter_sha256='actual', optimizer_steps=10),
                                     dict(adapter_state_sha256='actual', optimizer_steps=10), True)
        self.assertTrue(event['matches_saved_adapter_and_step'])
        self.assertEqual(event['attribution'], 'SUCCESSOR_LOADED')

    def test_missing_actual_adapter_field_is_not_repaired_or_invented(self):
        event = poll.loaded_metadata(dict(pid=123, resume=True, optimizer_steps=10),
                                     dict(adapter_state_sha256='actual', optimizer_steps=10), True)
        self.assertFalse(event['matches_saved_adapter_and_step'])
        self.assertEqual(event['attribution'], 'LOAD_BINDING_MISMATCH')

    def test_Main_readmission_is_not_claimed_as_our_failed_attempt_launch(self):
        event = poll.loaded_metadata(dict(pid=123, resume=True, adapter_sha256='actual', optimizer_steps=10),
                                     dict(adapter_state_sha256='actual', optimizer_steps=10), False)
        self.assertTrue(event['matches_saved_adapter_and_step'])
        self.assertEqual(event['attribution'], 'EXTERNAL_LOAD_OBSERVED_NOT_THIS_ATTEMPT')


if __name__ == '__main__':
    unittest.main()
