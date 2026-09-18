"""Owned A40R7 CPU tests; synthetic replay is not real-model evidence."""

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r145_a40r7_recovery as recovery


class ReplayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.destination = root/'recovery'
        self.records = [{'kind': 'METADATA', 'document': {}} for unused in range(1375)]
        outputs = []
        for number, index in enumerate((1366, 1369)):
            self.records[index]['document'] = dict(messages=[{'role': 'user', 'content': str(number)}],
                max_new_tokens=512, deadline_unix=10**12)
            response = {'raw': str(number), 'token_ids': [number]}
            self.records[index+1]['document'] = dict(response=response)
            outputs.append(response)
        directory = root/'stream'/'records'
        directory.mkdir(parents=True)
        for index in range(1365, 1375):
            for suffix in ('.json', '.intent.json'):
                (directory/(f'{index:020d}'+suffix)).write_text('{}')
        self.journal = SimpleNamespace(root=directory.parent, _mutex=threading.RLock())
        self.snapshot = dict(sha256='original', state={'history': ['unchanged'], 'carry': ['unchanged'], 'pending': 'sleep23'})
        self.stream = SimpleNamespace(checkpoint=lambda: deepcopy(self.snapshot))
        self.child = SimpleNamespace(plan={'hard_end_unix': 10**12}, optimizer_steps=1166,
            adapter_hash=lambda: 'saved_adapter', generate=Mock(side_effect=outputs),
            engine=SimpleNamespace(verify_base=Mock()), torch=object())
        evidence = {'run1/checkpoints/sleep_000022/COMMIT.json': json.dumps({'adapter_state_sha256': 'saved_adapter'}).encode()}
        for name, replacement in [('RECOVERY', self.destination), ('verify_manifest', Mock()),
                ('runtime_environment', Mock(return_value={})), ('pinned_evidence', Mock(return_value=evidence)),
                ('verify_runtime', Mock(return_value='original_recipe')), ('bind', Mock(return_value=self.records)),
                ('restore', Mock(return_value='optimizer')), ('rng', Mock(return_value={'rng': 'saved'})),
                ('optimizer_fingerprint', Mock(return_value='optimizer'))]:
            patcher = patch.object(recovery, name, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_two_exact_replays_preserve_state_and_zero_learning(self):
        result = recovery.recover_rng(self.child, self.stream, self.journal, {}, {})
        self.assertEqual(result['matched_generations'], 2)
        self.assertEqual(result['optimizer_steps'], 1166)
        self.assertEqual(result['optimizer_updates'], 0)
        self.assertTrue(result['pending_unchanged'])
        self.assertEqual(self.child.generate.call_count, 2)
        self.assertFalse(result['original_postgeneration_rng_snapshot_available'])
        self.assertTrue((self.destination/'GENERATIONS_VERIFIED.json').exists())

    def test_replay_mismatch_fails_without_claiming_completion(self):
        self.child.generate.side_effect = [{'raw': 'wrong'}]
        with self.assertRaisesRegex(ValueError, 'exact_generation_match:0'):
            recovery.recover_rng(self.child, self.stream, self.journal, {}, {})
        self.assertTrue((self.destination/'FAILED.json').exists())
        self.assertFalse((self.destination/'GENERATIONS_VERIFIED.json').exists())

    def test_pending_history_mutation_fails(self):
        def generate(*args, **kwargs):
            self.snapshot['state']['carry'] = ['changed']
            return {'raw': '0', 'token_ids': [0]}
        self.child.generate.side_effect = generate
        with self.assertRaisesRegex(ValueError, 'no_replay_history_plan_mutation'):
            recovery.recover_rng(self.child, self.stream, self.journal, {}, {})


class ReplacementTests(unittest.TestCase):
    def setUp(self):
        from gpu.orch_r145_suffix_boundary import POLICY
        self.journal = SimpleNamespace(record=Mock())
        self.eligibility = dict(new_row_sha256=['new0','new1'], rehearsal_row_sha256=[str(index) for index in range(44)],
                                excluded=[], raw_modified=False)
        self.binding = dict(runtime={'sha256':'runtime'}, proof={'sha256':'proof'})
        self.metadata = dict(runtime_memory_policy=POLICY, runtime_sha256='runtime', GPU_validation_sha256='proof')
        self.recorder = recovery.ReplacementRecorder(self.journal,self.eligibility,self.binding,'one_attempt')

    def begin(self):
        self.recorder('TARGET_ELIGIBILITY',self.eligibility)
        self.recorder('CHECKPOINT_METADATA',self.metadata)

    def test_full76_replaces1167_without_counting_historical_update(self):
        self.begin()
        for index,source in enumerate(self.recorder.sources):
            self.recorder('UPDATE',dict(optimizer_step=1167+index,source_sha256=source))
        self.recorder.complete()
        self.assertEqual(self.recorder.updates[-1]['optimizer_step'],1242)
        self.assertEqual(self.journal.record.call_count,78)
        self.assertEqual(self.journal.record.call_args.args[1]['r145_a40r7_original_abandoned_record'],1374)

    def test_missing_metadata_cannot_update(self):
        self.recorder('TARGET_ELIGIBILITY',self.eligibility)
        with self.assertRaisesRegex(ValueError,'eligibility_and_proof_metadata_before_updates'):
            self.recorder('UPDATE',dict(optimizer_step=1167,source_sha256='new0'))

    def test_unknown_or_duplicate_metadata_rejected(self):
        self.recorder('TARGET_ELIGIBILITY',self.eligibility)
        with self.assertRaisesRegex(ValueError,'one_exact_proven_runtime_metadata_only'):
            self.recorder('CHECKPOINT_METADATA',dict(self.metadata,extra='unapproved'))
        self.recorder('CHECKPOINT_METADATA',self.metadata)
        with self.assertRaises(ValueError):
            self.recorder('CHECKPOINT_METADATA',self.metadata)

    def test_changed_eligibility_and_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            self.recorder('TARGET_ELIGIBILITY',dict(self.eligibility,runtime_policy='R144'))
        with self.assertRaises(ValueError):
            self.recorder('INBOX',{})

    def test_steps_order_and_rehearsal_cannot_be_changed(self):
        self.begin()
        for document in (dict(optimizer_step=1168,source_sha256='new0'),
                         dict(optimizer_step=1167,source_sha256='new1')):
            with self.subTest(document=document), self.assertRaisesRegex(ValueError,'replacement_exact_contiguous_original_schedule'):
                self.recorder('UPDATE',document)
        with self.assertRaisesRegex(ValueError,'complete_original_76_updates'):
            self.recorder.complete()


class AdmissionTests(unittest.TestCase):
    def command(self):
        return ['sudo', '-n', 'systemd-run', '--property=DevicePolicy=strict',
            '--property=DeviceAllow=/dev/nvidia4 rw', '--property=DeviceAllow=/dev/nvidiactl rw',
            '--property=DeviceAllow=/dev/nvidia-uvm rw', '/usr/bin/env', '-i',
            'CUDA_VISIBLE_DEVICES='+recovery.GPU_UUID, '/python', '-B']

    def test_allocator_inside_original_env_i_only(self):
        before = self.command()
        after = recovery.allocator_command(before)
        position = after.index('/usr/bin/env')
        self.assertEqual(after[position+2], 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')
        self.assertEqual(after[:position+2]+after[position+3:], before)

    def test_physical_index_is_not_actual_minor(self):
        command = [entry.replace('/dev/nvidia4 rw', '/dev/nvidia7 rw') for entry in self.command()]
        with self.assertRaisesRegex(ValueError, 'only_a40r7_physical7'):
            recovery.allocator_command(command)

    def test_reject_foreign_device_and_alias(self):
        for entry in ('--property=DeviceAllow=/dev/nvidia3 rw', 'PYTORCH_ALLOC_CONF=other'):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                recovery.allocator_command([entry]+self.command())

    def test_reject_nonclean_environment(self):
        with self.assertRaisesRegex(ValueError, 'original_strict_clean_environment'):
            recovery.allocator_command([entry for entry in self.command() if entry != '-i'])

    def test_original_admission_functions_retained(self):
        from gpu import orch_r137_node4_containment as original
        supervisor = recovery.adapted_node_function('contained_supervise')
        native = recovery.adapted_node_function('contained_native')
        self.assertIs(supervisor.__globals__['scan'], original.scan)
        self.assertIs(native.__globals__['verify_device_containment'], original.verify_device_containment)
        self.assertIs(supervisor.__globals__['subprocess'], original.subprocess)
        self.assertIn('gpu.orch_r145_a40r7_recovery', supervisor.__code__.co_consts)
        self.assertIn('gpu.orch_r145_a40r7_recovery', native.__code__.co_consts)

    def test_runtime_UUID_and_allocator_both_inherited(self):
        torch = SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: 1,
            memory=SimpleNamespace(get_allocator_backend=lambda: 'native')))
        environment = dict(CUDA_VISIBLE_DEVICES=recovery.GPU_UUID, PYTORCH_CUDA_ALLOC_CONF=recovery.ALLOCATOR)
        raw = b'\0'.join((key+'='+value).encode() for key,value in environment.items())
        with patch.dict(os.environ, environment, clear=True):
            self.assertTrue(recovery.runtime_environment(torch,raw)['proc_environ_verified'])
            with self.assertRaisesRegex(ValueError, 'inherited_native_environment'):
                recovery.runtime_environment(torch,b'CUDA_VISIBLE_DEVICES=7')

    def test_memory_proof_required_before_ack(self):
        manifest = dict(schema=recovery.SCHEMA, root=str(recovery.ROOT), recovery_root=str(recovery.RECOVERY),
            semantics=recovery.SEMANTICS, journal_head=recovery.HEAD, allocator=recovery.ALLOCATOR,
            module_sha256='module', cpu_evidence={}, memory={})
        with patch.object(recovery,'sha',return_value='module'), self.assertRaisesRegex(ValueError,'exact_memory_binding_fields'):
            recovery.verify_manifest(manifest,{})

    def test_only_two_child_requests_in_exact_suffix(self):
        self.assertEqual(recovery.TAIL.count('REQUEST'),2)
        self.assertEqual(recovery.TAIL.count('UPDATE'),1)
        self.assertNotIn('INBOX',recovery.TAIL)
        self.assertEqual(recovery.PINS['run1/checkpoints/sleep_000022/COMMIT.json'],
            'd9f716b7cb5a60fc9d81fb6dd1e772e49ef528fc61a79ca22d122e2ab83c0843')


if __name__ == '__main__':
    unittest.main()
