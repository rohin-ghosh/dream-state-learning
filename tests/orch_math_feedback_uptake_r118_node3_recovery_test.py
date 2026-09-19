import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r118_node3_recover as recovery
from gpu import orch_math_feedback_uptake_r118_node3_broker as broker
import orch_math_feedback_uptake_base_test as fixture


native, policy = recovery.native, recovery.policy


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lane = self.root/'campaign_node3_style0'
        self.lane.mkdir()
        (self.lane/'R118_RECOVERY').mkdir()
        (self.lane/'r110_parent_queue').mkdir()
        principles = self.root/'principles'
        principles.write_text('Bound behavior parenting, not outcome gated. ' * 8)
        policy.bind_principles(principles, hashlib.sha256(principles.read_bytes()).hexdigest())

    def test_terminal_only_exact_owned_lane(self):
        self.assertEqual(broker.terminal_path(broker.LANE/'TERMINAL.json'), broker.LANE/'R118_RECOVERY/TERMINAL.json')
        other = broker.LANE.parent/'campaign_node3_style1/TERMINAL.json'
        self.assertEqual(broker.terminal_path(other), other)

    def test_failed_parent_preserves_teacher_without_new_plan(self):
        task = fixture.tasks()[0]
        output = self.lane/'R118_RECOVERY'
        native.common.write(self.lane/'READY.json', {})
        def deliver(unused):
            for path in (self.lane/'r110_parent_queue').glob('*.request.json'):
                archive = self.root/'parent_transcripts'/self.lane.name/path.name.removesuffix('.request.json')
                archive.mkdir(parents=True)
                native.common.write(archive/'FAILED.json', dict(status='FAILED'))
                native.common.write(path.with_name(path.name.replace('.request.', '.response.')),
                    dict(status='FAILED', request_sha256=native.common.sha(path), archive=dict(remote_root=str(archive),
                        files={'FAILED.json': native.common.sha(archive/'FAILED.json')}), error=dict(code='provider_failure')))
        with patch.object(native.time, 'sleep', side_effect=deliver):
            teacher, pending = native.parent(self.lane, output, 0, 8, 61, task,
                [policy.record(task, 'experience', fixture.response())], 9999999999, 'Prior valid guidance')
        self.assertEqual(teacher, 'Prior valid guidance')
        self.assertIsNone(pending)
        self.assertEqual(native.common.read(output/'PARENT_T061.json')['status'], 'MISSING')
        self.assertEqual(len((self.lane/'CALLS_PARENT.jsonl').read_text().splitlines()), 1)

    def test_partial_cycle_runs_only_four_remaining_then_eight_readout(self):
        write, read = native.common.write, native.common.read
        tasks = fixture.tasks()
        records = {tasks[0]['id']: [policy.record(tasks[0], purpose, fixture.response())
            for purpose in ('experience', 'check', 'revision')],
            tasks[1]['id']: [policy.record(tasks[1], 'experience', fixture.response())]}
        state = dict(memory=None, teacher='Prior valid guidance', pending=None, completed_train_segments=60)
        write(self.lane/'COHORT.json', dict(train=[tasks]*9, held=[fixture.tasks('HELD')*4]*9))
        write(self.lane/'READY.json', dict(cohort_sha256=native.common.sha(self.lane/'COHORT.json')))
        write(self.lane/'ACTIVATION.json', dict(native_deadline_unix=9999999999))
        (self.lane/'cycle7/experience').mkdir(parents=True)
        (self.lane/'cycle8/experience').mkdir(parents=True)
        write(self.lane/'cycle7/experience/STATE.json', dict(memory=None))
        write(self.lane/'cycle8/experience/EPISODES.json', records)
        write(self.lane/'R118_RECOVERY/INITIAL_STATE.json', state)
        preserved = (self.lane/'cycle8/experience/EPISODES.json').read_bytes()
        class Fake(fixture.FakeEngine):
            def __init__(self, model_dir, tokenizer, device, check):
                super().__init__(SimpleNamespace(adapter_dir=None, phase='readout'), tokenizer, check)
        original_read = Path.read_bytes
        with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=policy.DEVICES[0]), \
            patch.object(Path, 'read_bytes', autospec=True, side_effect=lambda path: ('CUDA_VISIBLE_DEVICES='+policy.DEVICES[0]).encode()
                if str(path) == '/proc/self/environ' else original_read(path)), \
            patch.object(native.reuse.driver.seam.portable, 'verify_base_files', return_value=dict(expected_base_sha256=policy.base.BASE_SHA)), \
            patch.object(native.reuse.driver.seam.native.source.native, 'load_local_tokenizer', return_value=fixture.Tokenizer()), \
            patch.object(native.reuse.driver.seam.native, 'process_identity', return_value=('new-boot', 2, 2)), \
            patch.object(native.reflection, 'engine_class', side_effect=lambda engine: engine), \
            patch.object(native, 'parent', side_effect=lambda *args: ('Prior valid guidance', None)) as parent:
            for phase in ('experience', 'readout'):
                native.run(self.lane, 0, 8, phase, Fake, lambda root: dict(bundle='/fixture', model_dir='/fixture'), 'plan')
            self.assertEqual([call.args[4] for call in parent.call_args_list], [61, 62, 63, 64])
        experience = self.lane/'R118_RECOVERY/cycle8/experience'
        calls = [read(path) for path in sorted(experience.glob('CALL_*.json'))]
        self.assertEqual([call['purpose'] for call in calls], ['check', 'revision', 'revision', 'revision'])
        self.assertEqual(read(experience/'STATE.json')['completed_train_segments'], 64)
        self.assertEqual((self.lane/'cycle8/experience/EPISODES.json').read_bytes(), preserved)
        held = self.lane/'R118_RECOVERY/cycle8/readout'
        self.assertEqual(len(list(held.glob('CALL_*.json'))), 8)
        self.assertTrue(all(not read(path)['parent_present'] for path in held.glob('CALL_*.json')))

    def test_source_keeps_bounds_and_no_optimizer(self):
        self.assertEqual(policy.CYCLES, 96)
        self.assertEqual(policy.NATIVE_CAP, 1536)
        self.assertEqual(policy.PARENT_CAPS[0], 768)
        source = Path(native.__file__).read_text()
        for forbidden in ('backward(', 'optimizer.step(', 'save_pretrained('):
            self.assertNotIn(forbidden, source)


if __name__ == '__main__':
    unittest.main()
