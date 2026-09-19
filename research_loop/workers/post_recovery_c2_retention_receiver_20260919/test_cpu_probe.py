"""Real pinned C2 reader against synthetic journals, never a production journal."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import random
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


OWN = Path(__file__).resolve().parent
SOURCE = OWN.parent / 'rohin233_recovery_node4_20260918/private/port_C2'
sys.path.insert(0, str(SOURCE))
specification = importlib.util.spec_from_file_location('c2_journal_fixture', SOURCE / 'tests/test_orch_r125_stream_journal.py')
fixture = importlib.util.module_from_spec(specification)
specification.loader.exec_module(fixture)

from gpu.orch_r125_stream_journal import StreamJournal
from research_loop.workers.post_recovery_c2_retention_receiver_20260919 import cpu_probe
from research_loop.workers.post_recovery_c2_retention_receiver_20260919.receiver import (
    CONFINEMENT, DEADLINE, GPU_UUID, R188_SHA256, TRIAL)
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import digest


class TailTests(unittest.TestCase):
    step = fixture.StreamJournalTests.step
    receipt = fixture.StreamJournalTests.receipt
    parent = fixture.StreamJournalTests.parent

    def setUp(self):
        fixture.StreamJournalTests.setUp(self)
        self.journal.close()
        self.root = self.root.parent / 'life/stream'
        self.root.parent.mkdir()
        self.journal = StreamJournal(self.root, create=True)
        self.addCleanup(self.journal.close)
        self.stream.deadline_unix = DEADLINE
        self.parent()
        self.step(incoming=self.journal.read_inbox())
        self.step()
        reference = self.journal.record('R197_CORRECTION_CYCLE', dict(ledger=dict(
            schema='R197_CORRECTION_LEDGER_V1', life_id=TRIAL, cycles=[])))
        StreamJournal._publish(self.journal._root_fd, 'correction_ledger.json',
            dict(record_index=reference['index'], record_sha256=reference['sha256']))
        self.stream.commit_sleep(self.receipt(), self.journal.record)
        self.selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=str(self.root),
            journal_id=self.journal._manifest['journal_id'], complete_index=self.journal._state['index'] - 1,
            complete_sha256=self.journal._state['previous'], life_id=TRIAL, max_tail_records=2048,
            max_tail_bytes=1073741824, sidecars=[dict(name='correction_ledger.json',
                kind='R197_CORRECTION_CYCLE', required=True)], persist_complete_anchors=True)
        self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1))
        self.candidate = dict(head_index=self.journal._state['index'] - 1,
            head_sha256=self.journal._state['previous'], resume_state=self.stream.checkpoint())

    def pins(self):
        return {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob('*') if path.is_file()}

    def scan(self):
        return cpu_probe.readonly_tail(SOURCE, self.candidate, self.selection)

    def test_exact_scanner_and_native_match_C2_fullsourcepins(self):
        import json
        stage = json.loads((OWN.parent / 'post_recovery_retention_rollout_20260919/C2_STAGED.json').read_bytes())
        for name in ('gpu/orch_r125_stream_journal.py', 'gpu/checkpoint_tail_runtime.py',
                'gpu/orch_r125_continual_native.py'):
            self.assertEqual(hashlib.sha256((SOURCE / name).read_bytes()).hexdigest(), stage['new_source_pins'][name])

    def test_real_scan_under_active_fixture_writer_lock_never_writes_or_locks(self):
        before = self.pins()
        with patch('fcntl.flock', side_effect=AssertionError('reader_must_not_acquire_writer_lock')):
            result = self.scan()
        self.assertEqual(before, self.pins())
        self.assertTrue(result['read_only'] and result['sidecars_verified'] and result['inbox_preserved'])
        self.assertEqual(result['journal_writes'], 0)
        self.assertFalse(result['writer_lock_acquired'])
        self.assertTrue(self.selection['persist_complete_anchors'])
        self.assertFalse((self.root / 'COMPLETE_ANCHOR.json').exists())

    def test_no_prefix_request_response_body_replay(self):
        original = StreamJournal._read_json
        decoded = []
        def observe(directory, name):
            decoded.append(name)
            return original(directory, name)
        with patch.object(StreamJournal, '_read_json', side_effect=observe):
            result = self.scan()
        permitted = set(result['decoded_prefix_indices']) | {item['record_index'] for item in result['sidecars']}
        for name in decoded:
            if name[:20].isdigit() and not name.endswith('.intent.json'):
                index = int(name[:20])
                if index <= self.selection['complete_index']:
                    self.assertIn(index, permitted)
        self.assertEqual(result['prefix_work'], 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY')
        self.assertGreater(result['raw_record_bytes_hashed'], 0)

    def test_wrong_exact_complete_pin_refuses(self):
        self.selection['complete_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'checkpoint_tail_exact_complete_pin'):
            self.scan()

    def test_wrong_journal_or_life_sidecar_refuses(self):
        for key, value in (('journal_id', 'b' * 32), ('life_id', 'other-life')):
            original = self.selection[key]
            self.selection[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.scan()
            self.selection[key] = original

    def test_missing_required_ledger_refuses(self):
        (self.root / 'correction_ledger.json').unlink()
        with self.assertRaisesRegex(ValueError, 'regular_evidence_file'):
            self.scan()

    def test_prefix_byte_corruption_refuses_without_repair(self):
        path = self.root / 'records/00000000000000000000.json'
        path.write_bytes(path.read_bytes().replace(b'Synthetic', b'Corrupted', 1) + b' ')
        before = self.pins()
        with self.assertRaises(ValueError):
            self.scan()
        self.assertEqual(before, self.pins())

    def test_tail_bound_refuses(self):
        self.selection['max_tail_records'] = 0
        with self.assertRaises(ValueError):
            self.scan()

    def test_changed_head_refuses(self):
        self.journal.record('NOTE', dict(after_candidate=True))
        with self.assertRaisesRegex(ValueError, 'unraced_complete_tail_candidate'):
            self.scan()

    def test_pending_request_is_never_cleared(self):
        def fail(*arguments, **keywords):
            raise RuntimeError('synthetic-generation-interrupted')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=fail)
        before = self.pins()
        with self.assertRaisesRegex(ValueError, 'same_resolved_C2_state'):
            self.scan()
        self.assertEqual(before, self.pins())

    def test_CPU_environment_and_C2_identity_enforced_before_import(self):
        plan = dict(physical=1, hard_end_unix=DEADLINE, think_act_learn=dict(trial_id=TRIAL))
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': GPU_UUID}):
            with self.assertRaisesRegex(ValueError, 'CPU_only_probe_environment'):
                cpu_probe.probe(SOURCE, self.candidate, plan, 'tail', self.selection)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            plan['think_act_learn']['trial_id'] = 'frozen-pair'
            with self.assertRaisesRegex(ValueError, 'learned_C2_identity'):
                cpu_probe.probe(SOURCE, self.candidate, plan, 'tail', self.selection)

    def test_exact_r188_command_constructed_but_never_invoked(self):
        path = OWN.parent / 'post_recovery_matched_cohort_runtime_20260918/receiving/source/gpu/r188_node5_confinement.py'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), R188_SHA256)
        function = next(node for node in ast.parse(path.read_bytes()).body
            if isinstance(node, ast.FunctionDef) and node.name == 'command')
        namespace = dict(Path=Path, sys=sys, time=SimpleNamespace(time=lambda: DEADLINE - 600),
            digest=lambda value: hashlib.sha256(value).hexdigest(), require=cpu_probe.require,
            DEVICE=GPU_UUID, MODULE=CONFINEMENT)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
        config_path = self.root / 'SYNTHETIC_GUARD.json'
        config_path.write_text('{}')
        guard = ModuleType('gpu.orch_r125_continual_guard')
        guard.validate = lambda path: (dict(attempt_dir='/synthetic/control'),
            dict(hard_end_unix=DEADLINE, source_root='/synthetic/source'))
        with patch.dict(sys.modules, {'gpu.orch_r125_continual_guard': guard}):
            command = namespace['command'](config_path, 'child', now=DEADLINE - 600)
        for argument in ('--property=User=2524', '--property=Group=2524', '--property=DevicePolicy=strict',
                '--property=CapabilityBoundingSet=', '--property=NoNewPrivileges=yes',
                '--property=DeviceAllow=/dev/nvidia1 rw', 'CUDA_VISIBLE_DEVICES=' + GPU_UUID):
            self.assertIn(argument, command)
        self.assertIn(CONFINEMENT, command)
        for minor in (0, 2, 3, 4, 5, 6, 7):
            self.assertNotIn('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw', command)


class CheckpointProbeLogicTests(unittest.TestCase):
    def setUp(self):
        tensor = lambda: SimpleNamespace(device=SimpleNamespace(type='cpu'), shape=(2, 2),
            dtype='uint8', numel=lambda: 16)
        self.payload = dict(optimizer_steps=8, parameter_names=['lora_A', 'lora_B'],
            optimizer=dict(param_groups=[dict(params=[0, 1])], state={index: dict(step=8,
                exp_avg=tensor(), exp_avg_sq=tensor()) for index in range(2)}),
            cpu_rng=b'synthetic-cpu-state', python_rng=random.Random(1).getstate(), cuda_rng=[tensor()])
        self.restores = []
        self.torch = SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: False), uint8='uint8',
            load=lambda *arguments, **keywords: self.payload,
            Generator=lambda **keywords: SimpleNamespace(set_state=self.restores.append),
            isfinite=lambda value: SimpleNamespace(all=lambda: True))
        self.candidate = dict(checkpoint=dict(optimizer_rng_path='/synthetic/no-file', optimizer_steps=8,
            checkpoint_sha256=dict(adapter='a', optimizer='b', rng='b')))
        self.candidate['resume_state'] = dict(state=dict(model_state_sha256=digest(
            self.candidate['checkpoint']['checkpoint_sha256'])))
        self.native = SimpleNamespace(NativeChild=SimpleNamespace(verify_checkpoint=lambda checkpoint: None), digest=digest)

    def check(self):
        with patch.dict(sys.modules, {'torch': self.torch}):
            return cpu_probe.checkpoint_probe(self.native, self.candidate)

    def test_learned_physical_one_positive_steps_not_frozen(self):
        result = self.check()
        self.assertTrue(result['learned_C2'] and result['no_GPU_calls'])
        self.assertEqual(self.restores, [b'synthetic-cpu-state'])
        self.assertEqual(result['saved_cuda_rng_validation'], 'CPU_tensor_bytes_only_not_GPU_restore')

    def test_zero_steps_cannot_be_misclassified_as_frozen_sibling(self):
        self.payload['optimizer_steps'] = self.candidate['checkpoint']['optimizer_steps'] = 0
        with self.assertRaisesRegex(ValueError, 'learned_C2_not_frozen_pair_control'):
            self.check()

    def test_missing_or_wrong_optimizer_state_refuses(self):
        self.payload['optimizer']['state'][0]['step'] = 7
        with self.assertRaisesRegex(ValueError, 'saved_AdamW_state_and_steps'):
            self.check()

    def test_nonfinite_CPU_optimizer_refuses(self):
        self.torch.isfinite = lambda value: SimpleNamespace(all=lambda: False)
        with self.assertRaisesRegex(ValueError, 'finite_CPU_optimizer_state'):
            self.check()

    def test_initialized_GPU_refuses_and_saved_model_mismatch_refuses(self):
        self.torch.cuda.is_initialized = lambda: True
        with self.assertRaisesRegex(ValueError, 'no_GPU_initialized'):
            self.check()
        self.torch.cuda.is_initialized = lambda: False
        self.candidate['resume_state']['state']['model_state_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'saved_working_state_no_GPU_load'):
            self.check()


if __name__ == '__main__':
    unittest.main()
