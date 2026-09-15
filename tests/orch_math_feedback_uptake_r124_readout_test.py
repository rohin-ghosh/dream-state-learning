from copy import deepcopy
import inspect
import unittest

from gpu import orch_math_feedback_uptake_r124_readout as probe
from gpu import orch_math_feedback_uptake_r124_boundary as boundary


class MatchedReadoutTests(unittest.TestCase):
    def fixture(self):
        tasks = [dict(id=f'dev{index}', split='DEV', question=f'What is {index}+2?') for index in range(8)]
        prompts = [probe.math.policy.readout_messages(task, 'held') for task in tasks]
        return tasks, prompts

    def test_fixed_empty_prompts(self):
        tasks,prompts = self.fixture()
        digest = probe.validate_prompts(tasks,prompts)
        self.assertEqual(digest,probe.validate_prompts(tasks,deepcopy(prompts)))
        self.assertEqual(len(digest),64)

    def test_carry_or_parent_rejected(self):
        tasks,prompts = self.fixture()
        prompts[0].insert(1,dict(role='assistant',content='prior thought'))
        with self.assertRaises(ValueError):probe.validate_prompts(tasks,prompts)

    def test_changed_question_rejected(self):
        tasks,prompts = self.fixture()
        prompts[1][-1]['content'] += 'Try harder.'
        with self.assertRaises(ValueError):probe.validate_prompts(tasks,prompts)

    def test_FINAL_rejected(self):
        tasks,prompts = self.fixture()
        tasks[0]['split']='FINAL'
        with self.assertRaises(ValueError):probe.validate_prompts(tasks,prompts)

    def test_full_response_before_reduction(self):
        text=inspect.getsource(probe.probe)
        self.assertIn('response=response',text)
        self.assertIn('actor.batch(prompts, 2048)',text)
        self.assertIn('raw_saved_before_parser=True',text)
        self.assertNotIn('judge(',text)
        self.assertIn('readout=True',text)

    def test_pair_does_not_load_optimizer(self):
        text=inspect.getsource(probe.paired_probe)+inspect.getsource(probe.probe)
        self.assertNotIn('torch.load',text)
        self.assertNotIn('poll_parent',text)

    def test_no_retry_and_bounded_pair(self):
        text=inspect.getsource(probe.paired_probe)
        self.assertIn("for role in ('before', 'after')",text)
        self.assertIn('new_probe_attempt_never_retried',text)
        self.assertIn('time.time()+600',text)

    def test_same_saved_boundary(self):
        checkpoint={'path_sha256':'a'}
        committed=dict(cycle=10,checkpoint=checkpoint)
        sleep=dict(checkpoint=checkpoint,cumulative_optimizer_steps=100)
        binding=dict(checkpoint=checkpoint,parent_free=True,train_rows=False,split='DEV')
        self.assertEqual(boundary.boundary_contract(committed,sleep,binding,[]),10)
        for later in (['cycle11'],):
            with self.assertRaises(ValueError):boundary.boundary_contract(committed,sleep,binding,later)
        binding['checkpoint']={'path_sha256':'wrong'}
        with self.assertRaises(ValueError):boundary.boundary_contract(committed,sleep,binding,[])

    def test_only_identity_bound_signals(self):
        text=inspect.getsource(boundary.execute)
        self.assertNotIn('os.kill(',text)
        self.assertNotIn('killpg(',text)
        self.assertIn('signal.pidfd_send_signal',text)
        self.assertIn('check_actor(request)',text)
        self.assertIn('existing_readout_finishes_without_signal',text)

    def test_live_source_unchanged(self):
        self.assertNotEqual(probe.SOURCE.name,'orch_math_feedback_uptake_r121_independent_source_20260915_v3')
        text=inspect.getsource(probe.resident)
        self.assertIn('offloaded_readout(',text)
        self.assertIn('history.extend(rows)',text)


if __name__ == '__main__':unittest.main()
