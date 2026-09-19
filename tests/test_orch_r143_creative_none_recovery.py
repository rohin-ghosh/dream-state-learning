import ast
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r143_creative_none_recovery as recovery
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


class Tensor:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return [self.value]


class AdamW:
    def __init__(self):
        self.state = {'state': {'weight': {'step': 690, 'momentum': 1.25}}}

    def state_dict(self):
        return deepcopy(self.state)

    def load_state_dict(self, state):
        self.state = deepcopy(state)


class Torch:
    Tensor = Tensor
    optim = SimpleNamespace(AdamW=AdamW)

    def __init__(self):
        self.counter = 0
        self.cuda = self
        self.memory = SimpleNamespace(get_allocator_backend=lambda: 'native')

    def get_rng_state(self):
        return Tensor(self.counter)

    def get_rng_state_all(self):
        return [Tensor(self.counter)]

    def set_rng_state(self, value):
        self.counter = value.value

    def set_rng_state_all(self, values):
        self.counter = values[0].value

    def load(self, source, **kwargs):
        return deepcopy(self.payload)

    def device_count(self):
        return 1

    def synchronize(self):
        pass

    def reset_peak_memory_stats(self):
        pass

    def mem_get_info(self):
        return 100, 1000

    def max_memory_allocated(self):
        return 700

    def max_memory_reserved(self):
        return 800


class NativeChild:
    def __init__(self, plan):
        self.plan = plan
        self.optimizer_steps = 690
        self.optimizer = AdamW()
        self.torch = Torch()
        self.parameters = {'weight': object()}
        self.engine = SimpleNamespace(verify_base=lambda: None)
        self.adapter = 'a'*64
        self.calls = 0
        self.mismatch = False
        self.fail_sleep = False
        self.experiment = None

    def check(self, label):
        recovery.require(time.time() < self.plan['hard_end_unix'], 'deadline')

    def adapter_hash(self):
        return self.adapter

    def verify_checkpoint(self, checkpoint):
        recovery.verify_saved_files(checkpoint)

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.calls += 1
        self.torch.counter += 1
        return dict(raw=str(random.random()) + ('mismatch' if self.mismatch else ''),
            token_ids=[self.torch.counter, 151645], terminal=True, truncated=False,
            prompt_tokens=len(messages), prompt_token_ids_sha256=digest(messages),
            adapter_state_sha256=self.adapter, base_sha256='b'*64, decoder=self.plan['decoder'])

    def sleep(self, new_rows, old_rows, anchors, record):
        record('TARGET_ELIGIBILITY', dict(version=self.plan['presentation_version'], excluded=[],
            new_row_sha256=[row['source_sha256'] for row in new_rows],
            rehearsal_row_sha256=[row['source_sha256'] for row in old_rows], raw_modified=False))
        for index in range(62):
            self.optimizer_steps += 1
            record('UPDATE', dict(optimizer_step=self.optimizer_steps, source_sha256=new_rows[0]['source_sha256']))
            if self.fail_sleep:
                raise RuntimeError('synthetic_backward_OOM')
        self.adapter = 'c'*64
        return dict(optimizer_steps=62, total_optimizer_steps=self.optimizer_steps)

    def checkpoint(self, path):
        path.mkdir(parents=True)
        return dict(optimizer_steps=self.optimizer_steps, experiment=None,
                    checkpoint_sha256=dict(adapter='c'*64, optimizer='d'*64, rng='d'*64))


class CreativeNoneRecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root, self.source = self.base/'run1', self.base/'source1'
        self.root.mkdir()
        self.destination = self.root/'recoveries'/'r143-creative-none-sleep16-20260916-attempt1'
        self.saved_random = random.getstate()
        self.addCleanup(random.setstate, self.saved_random)
        for name, value in [('BASE', self.base), ('ROOT', self.root), ('SOURCE', self.source), ('RECOVERY', self.destination)]:
            self.patch(name, value)
        self.plan = dict(root=str(self.root), source_root=str(self.source), physical=5, gpu_uuid=recovery.GPU_UUID,
            segment_tokens=4, context_limit=16384, hard_end_unix=time.time()+3600,
            decoder={'temperature': 0.7}, presentation_version='R125_PLAIN_CONTEXT_V1',
            system_prompt='System.', birth_prompt='Birth.')
        self.child = NativeChild(self.plan)
        self.journal = StreamJournal(self.root/'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=16384, segment_tokens=4, segments_per_sleep=2,
            deadline_unix=self.plan['hard_end_unix'], model_state_sha256='0'*64)
        self.stream.set_presentation(dict(version=self.plan['presentation_version'], system_prompt='System.', birth_prompt='Birth.'), 16384)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        directory = self.root/'checkpoints'/'sleep_000015'
        (directory/'adapter').mkdir(parents=True)
        (directory/'adapter'/'adapter.bin').write_bytes(b'adapter')
        (directory/'optimizer_rng.pt').write_bytes(b'synthetic_optimizer_rng')
        files = {'adapter.bin': recovery.sha(directory/'adapter'/'adapter.bin')}
        hashes = dict(adapter=digest(files), optimizer=recovery.sha(directory/'optimizer_rng.pt'), rng=recovery.sha(directory/'optimizer_rng.pt'))
        self.checkpoint = dict(optimizer_steps=690, adapter_files=files, checkpoint_sha256=hashes,
            adapter_path=str(directory/'adapter'), optimizer_rng_path=str(directory/'optimizer_rng.pt'),
            adapter_state_sha256=self.child.adapter, base_sha256='b'*64)
        for cycle in range(1, 16):
            for unused in range(2):
                self.stream.step(self.child.generate, len, self.journal.record)
            self.sleep_request(cycle)
            if cycle == 15:
                state = self.journal._scan()
                previous = state['previous']
                for index in range(state['index'], 833):
                    item = dict(schema=self.journal._manifest['schema'], journal_id=self.journal._manifest['journal_id'],
                        index=index, kind='CHECKPOINT_METADATA', previous_sha256=previous, document={'fixture': True})
                    item['sha256'] = digest(item)
                    for suffix, document in [('.json', item), ('.intent.json', self.journal._intent(item))]:
                        (self.root/'stream'/'records'/f'{index:020d}{suffix}').write_text(json.dumps(document))
                    previous = item['sha256']
            self.stream.pending = None
            self.stream.commit_sleep(dict(status='COMPLETE', cycle=cycle, optimizer_steps=32,
                checkpoint=self.checkpoint, checkpoint_sha256=hashes,
                new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()]), self.journal.record)
        self.child.torch.payload = dict(optimizer=self.child.optimizer.state_dict(), parameter_names=['weight'],
            optimizer_steps=690, python_rng=random.getstate(), cpu_rng=self.child.torch.get_rng_state(),
            cuda_rng=self.child.torch.get_rng_state_all())
        for unused in range(2):
            self.stream.step(self.child.generate, len, self.journal.record, incoming=self.journal.read_inbox())
        self.sleep_request(16)
        self.journal.record('TARGET_ELIGIBILITY', dict(version=self.plan['presentation_version'], excluded=[],
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            rehearsal_row_sha256=[row['source_sha256'] for row in self.stream.rows[:self.stream.sleep_frontier]], raw_modified=False))
        self.records = recovery.journal_records(self.journal)[1]
        for name, index in [('HEAD', 841), ('SLEEP_REQUEST', 840), ('SAVED', 833)]:
            self.patch(name, self.records[index]['sha256'])
        evidence = {
            'control1/PLAN.json': json.dumps(self.plan),
            'control1/EXIT.json': json.dumps({'exit_code': 1}),
            'control1/NATIVE.log': 'Traceback (most recent call last):\n(loss*weight).backward()\ntorch.OutOfMemoryError: CUDA out of memory.',
            'run1/checkpoints/sleep_000015/COMMIT.json': json.dumps(self.checkpoint),
            'source1/gpu/orch_r125_continual_native.py': inspect.getsource(NativeChild),
            'source1/gpu/orch_r133_node3_programmes.py': 'fixture = True\n',
        }
        for name, value in evidence.items():
            path = self.base/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        guard = dict(plan_sha256=recovery.sha(self.base/'control1/PLAN.json'), source_pins={
            str(path.relative_to(self.source)): recovery.sha(path) for path in self.source.rglob('*.py')})
        (self.base/'control1/GUARD.json').write_text(json.dumps(guard))
        evidence['control1/GUARD.json'] = json.dumps(guard)
        self.patch('PINS', {name: recovery.sha(self.base/name) for name in evidence})
        cpu = self.base/'CPU.json'
        cpu.write_text(json.dumps(dict(status='PASS', module_sha256=recovery.sha(Path(recovery.__file__).absolute()))))
        self.manifest = dict(schema=recovery.SCHEMA, root=str(self.root), recovery_root=str(self.destination),
            journal_head=recovery.HEAD, semantics=recovery.SEMANTICS, allocator=recovery.ALLOCATOR,
            module_sha256=recovery.sha(Path(recovery.__file__).absolute()),
            cpu_evidence=dict(path=str(cpu), sha256=recovery.sha(cpu)))
        self.acknowledge()
        self.patch('runtime_environment', lambda torch: {'fixture': True})
        self.child.calls = 0

    def patch(self, name, value):
        patcher = patch.object(recovery, name, value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def acknowledge(self):
        path = self.base/'ACK.json'
        path.write_text(json.dumps(dict(author='Main', approved=True, manifest_sha256=digest(self.manifest))))
        self.ack = dict(path=str(path), sha256=recovery.sha(path))

    def sleep_request(self, cycle):
        checkpoint = self.stream.checkpoint()
        checkpoint['state']['pending'] = 'sleep:'+digest([row['source_sha256'] for row in self.stream.pending_rows()])
        checkpoint['sha256'] = digest(checkpoint['state'])
        self.journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=checkpoint))
        self.stream.pending = checkpoint['state']['pending']

    def replay(self):
        return recovery.recover_rng(self.child, self.stream, self.journal, self.manifest, self.ack)

    def test_two_exact_generations_preserve_suffix_optimizer_and_pending(self):
        before = self.stream.checkpoint()
        result = self.replay()
        self.assertEqual(self.child.calls, 2)
        self.assertEqual(self.stream.checkpoint(), before)
        self.assertEqual(recovery.journal_records(self.journal)[1], self.records)
        self.assertEqual(result['optimizer_steps'], 690)
        self.assertFalse(result['exact_update691_replay_claim'])
        self.assertFalse(result['original_update691_state_available'])
        self.assertEqual(result['historical_abandoned_updates'], 0)

    def test_mismatch_fails_closed_and_cannot_retry(self):
        self.child.mismatch = True
        with self.assertRaisesRegex(ValueError, 'exact_generation_match:0'):
            self.replay()
        self.assertTrue((self.destination/'FAILED.json').exists())
        self.assertEqual(recovery.journal_records(self.journal)[1], self.records)
        with self.assertRaises(FileExistsError):
            self.replay()

    def test_missing_ack_before_generation(self):
        (self.base/'ACK.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.replay()
        self.assertEqual(self.child.calls, 0)

    def test_changed_manifest_needs_matching_ack(self):
        self.manifest['cpu_evidence']['path'] = str(self.base/'CPU_COPY.json')
        (self.base/'CPU_COPY.json').write_bytes((self.base/'CPU.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Main_acknowledges_exact_manifest'):
            self.replay()

    def test_changed_recipe_rejected(self):
        self.child.plan['context_limit'] = 8192
        with self.assertRaisesRegex(ValueError, 'no_recipe_deadline_visibility_changes'):
            self.replay()

    def test_checkpoint_corruption_rejected(self):
        Path(self.checkpoint['optimizer_rng_path']).write_bytes(b'corruption')
        with self.assertRaisesRegex(ValueError, 'saved_file_hashes'):
            self.replay()

    def test_wrong_optimizer_step_rejected(self):
        self.child.optimizer_steps = 691
        with self.assertRaisesRegex(ValueError, 'loaded_sleep15_adapter690'):
            self.replay()

    def test_new_journal_metadata_rejected(self):
        self.journal.record('CHECKPOINT_METADATA', {'unexpected': True})
        with self.assertRaisesRegex(ValueError, 'exact_creative-none_833_841_suffix'):
            self.replay()

    def test_recompute_preserves_failed_attempt_without_inventing_updates(self):
        receipt = self.replay()
        saved = recovery.finish_pending_sleep(self.child, self.stream, self.journal, {}, self.manifest, self.ack, receipt)
        self.assertEqual(saved['optimizer_steps'], 752)
        records = recovery.journal_records(self.journal)[1]
        self.assertEqual(records[:842], self.records)
        updates = [item['document'] for item in records[842:] if item['kind'] == 'UPDATE']
        self.assertEqual(len(updates), 62)
        self.assertEqual(updates[0]['optimizer_step'], 691)
        self.assertIsNone(updates[0]['r143_original_abandoned_record'])
        self.assertEqual(self.stream.sleep_frontier, 32)
        self.assertIsNone(self.stream.pending)
        self.assertTrue((self.destination/'ACTUAL_SLEEP_MEMORY.json').exists())

    def test_recompute_failure_keeps_original_history_and_pending(self):
        receipt = self.replay()
        self.child.fail_sleep = True
        with self.assertRaisesRegex(RuntimeError, 'synthetic_backward_OOM'):
            recovery.finish_pending_sleep(self.child, self.stream, self.journal, {}, self.manifest, self.ack, receipt)
        self.assertEqual(recovery.journal_records(self.journal)[1][:842], self.records)
        self.assertIsNotNone(self.stream.pending)
        self.assertTrue((self.destination/'RECOMPUTE_FAILED.json').exists())

    def test_high_valid_reserved_memory_does_not_stop_recovered_child(self):
        self.child.torch.max_memory_reserved = lambda: 999
        receipt = self.replay()
        recovery.finish_pending_sleep(self.child, self.stream, self.journal, {}, self.manifest, self.ack, receipt)
        self.assertEqual(self.stream.sleep_frontier, 32)
        self.assertTrue((self.destination/'SLEEP_RECOMPUTED.json').exists())


class ContainmentTests(unittest.TestCase):
    def test_original_launcher_guards_and_seven_minor_checks_are_retained(self):
        from gpu import orch_r133_node3_programmes as original
        adapted = recovery.adapted_node_function('contained_native')
        self.assertIs(adapted.__globals__['verify_containment'], original.verify_containment)
        self.assertIs(adapted.__globals__['guard'], original.guard)
        self.assertIn('all_seven_foreign_minors_denied', inspect.getsource(original.verify_containment))
        supervisor = recovery.adapted_node_function('supervise')
        self.assertIs(supervisor.__globals__['guard'], original.guard)
        with patch.object(original, 'device_minor', return_value=5):
            with self.assertRaisesRegex(ValueError, 'actual_UUID_minor5_not_index_assumption'):
                supervisor.__globals__['containment_command']({'gpu_uuid': recovery.GPU_UUID}, {'minor': 6}, [], 60)

    def command(self):
        return ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict',
            '--property=NoNewPrivileges=yes', '--property=DeviceAllow=',
            '--property=DeviceAllow=/dev/nvidia5 rw', '--property=DeviceAllow=/dev/nvidiactl rw',
            '--property=DeviceAllow=/dev/nvidia-uvm rw', '/usr/bin/env', '-i',
            'CUDA_VISIBLE_DEVICES='+recovery.GPU_UUID, '/venv/python', '-m', 'owned_launcher']

    def test_allocator_inside_clean_env_and_all_other_bytes_preserved(self):
        original = self.command()
        actual = recovery.allocator_command(original)
        position = original.index('/usr/bin/env')+2
        self.assertEqual(actual[position], 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
        self.assertEqual(actual[:position]+actual[position+1:], original)

    def test_foreign_device_and_conflicting_allocator_rejected(self):
        for addition in ['--property=DeviceAllow=/dev/nvidia0 rw', 'PYTORCH_ALLOC_CONF=backend:cudaMallocAsync']:
            command = self.command()
            command.insert(3, addition)
            with self.assertRaises(ValueError):
                recovery.allocator_command(command)

    def test_proc_inherited_environment_required(self):
        environ = {'CUDA_VISIBLE_DEVICES': recovery.GPU_UUID, 'PYTORCH_CUDA_ALLOC_CONF': recovery.ALLOCATOR}
        encoded = b'\0'.join((key+'='+value).encode() for key, value in environ.items())
        with patch.dict(os.environ, environ, clear=True):
            self.assertTrue(recovery.runtime_environment(Torch(), encoded)['proc_environ_verified'])
            with self.assertRaisesRegex(ValueError, 'inherited_native_environment'):
                recovery.runtime_environment(Torch(), b'')


if __name__ == '__main__':
    unittest.main()
