import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_route_parent_campaign_trajectory as reduction


class TrajectoryTests(unittest.TestCase):
    def test_known_admission_rejections_keep_exact_reason(self):
        for reason in ('complete_reflection_required', 'reflection_not_answer_action_replay', 'teacher_bytes_in_target'):
            self.assertEqual(reduction.safe_error(reason), reason)

    def write(self, root, relative, value):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def test_censored_calls_do_not_become_completed_learning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'GUIDED/cycle1/experience/REQUEST.json', dict(started_unix=10, input_adapter={}))
            self.write(root, 'GUIDED/cycle1/experience/CALL_0001.json', dict(started_unix=11, messages=['PRIVATE']))
            value = reduction.snapshot(root, 1)
            phase = value['rows'][1]['phases']['experience']
            self.assertEqual(phase['status'], 'RUNNING_CENSORED')
            self.assertEqual(phase['calls']['pending'], 1)
            self.assertEqual(phase['calls']['responses'], 0)
            self.assertNotIn('PRIVATE', json.dumps(value))

    def test_raw_tasks_answers_and_unknown_errors_not_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = 'GUIDED/cycle1/experience/'
            self.write(root, folder+'REQUEST.json', dict(started_unix=10, input_adapter={}))
            self.write(root, folder+'EPISODE_01.json', dict(task={'goal':'SECRET_TASK'}, messages=['SECRET_PROMPT']))
            self.write(root, folder+'REFLECTION_01.json', dict(admitted=False, error='SECRET_ERROR',
                response=dict(raw='SECRET_ANSWER', terminal=False, truncated=True, generated_text_tokens=512)))
            value = reduction.snapshot(root, 1)
            self.assertNotIn('SECRET', json.dumps(value))
            phase = value['rows'][1]['phases']['experience']
            self.assertEqual(phase['reflection_counts']['admitted'], 0)
            self.assertEqual(len(phase['task_sha256s']), 1)

    def test_noop_preserves_identity_and_has_no_retention_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = dict(path=None, files=[], state_sha256='base', base_sha256='base')
            self.write(root, 'NO_LORA/cycle1/sleep/REQUEST.json', dict(started_unix=10, input_adapter=identity))
            self.write(root, 'NO_LORA/cycle1/sleep/COMPLETE.json', dict(finished_unix=11, output_adapter=identity,
                updates=0, fits=0, reason='NO_LORA', process=['boot',1]))
            self.write(root, 'NO_LORA/cycle2/experience/REQUEST.json', dict(started_unix=12, input_adapter=identity))
            self.write(root, 'NO_LORA/cycle2/experience/LOADED.json', dict(observed=identity, process=['boot',2], parent_present=True))
            value = reduction.snapshot(root, 2)
            row = value['rows'][-1]
            self.assertTrue(row['previous_sleep_to_actual_experience']['same_saved_state'])
            self.assertFalse(row['previous_sleep_to_actual_experience']['retained_behavior_demonstrated'])
            self.assertFalse(row['previous_sleep_to_actual_experience']['prior_state_changed'])

    def test_parent_wait_residual_not_labelled_pure_queue_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'GUIDED/cycle1/experience/REQUEST.json', dict(started_unix=10, input_adapter={}))
            self.write(root, 'parent_queue/000_GUIDED_C1.WAIT.json', dict(elapsed_seconds=20))
            self.write(root, 'parent_raw/000_GUIDED_C1/RECEIPT.json', dict(started_unix=12, finished_unix=17,
                actual_model='verified-model', transcript_quarantined_from_ongoing_L1=True))
            parents = reduction.snapshot(root, 1)['rows'][1]['phases']['experience']['parents']
            self.assertEqual(parents['wait_minus_provider_seconds'], 15)
            self.assertIn('NOT isolated queue', parents['interpretation'])

    def test_fresh_readout_checks_fail_for_wrong_state_or_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = dict(path=None, files=[], state_sha256='base', base_sha256='base')
            self.write(root, 'GUIDED/cycle1/sleep/REQUEST.json', dict(started_unix=10, input_adapter=identity))
            self.write(root, 'GUIDED/cycle1/sleep/COMPLETE.json', dict(finished_unix=11, output_adapter=identity,
                updates=0, fits=0, process=['boot',1]))
            self.write(root, 'GUIDED/cycle1/readout/REQUEST.json', dict(started_unix=12, input_adapter=identity))
            self.write(root, 'GUIDED/cycle1/readout/LOADED.json', dict(observed=dict(identity,state_sha256='wrong'),
                process=['boot',1],parent_present=True))
            checks = reduction.snapshot(root, 1)['rows'][1]['fresh_parent_free_saved_child']
            self.assertFalse(checks['identity_equal'])
            self.assertFalse(checks['fresh_process'])
            self.assertFalse(checks['parent_absent'])


if __name__ == '__main__':
    unittest.main()
