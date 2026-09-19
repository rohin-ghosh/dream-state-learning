"""Synthetic CPU integration against one exact prepared source; never a live probe."""

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


SOURCE = None
METRICS = []


def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


class PairSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.recovery = importlib.import_module('gpu.r232_recovery')
        self.runtime = importlib.import_module('gpu.pair_retention_runtime')
        self.tail = importlib.import_module('gpu.checkpoint_tail_runtime')
        self.stream_module = importlib.import_module('organism_v6.orch_r125_continual_stream')
        self.history = importlib.import_module('organism_v6.orch_r124_train_history')
        self.digest = self.runtime.digest

    def boundary(self, physical=0):
        self.base = self.recovery.FrozenJournal if physical else self.recovery.LearnerJournal
        self.journal = self.base(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        stream_class = self.recovery.frozen.FrozenStream if physical else self.stream_module.ContinualStream
        self.stream = stream_class(self.history.TrainHistory(system_prompt='System.', birth_prompt='Birth.'),
            context_limit=6144, segment_tokens=128, segments_per_sleep=2,
            deadline_unix=10000, model_state_sha256='f' * 64)
        self.step()
        self.step()
        checkpoint = dict(optimizer_steps=0 if physical else 2, adapter_state_sha256='a' * 64,
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        receipt = dict(status='COMPLETE', cycle=1, optimizer_steps=checkpoint['optimizer_steps'],
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'])
        if physical:
            self.recovery.frozen.INITIAL = deepcopy(checkpoint)
            receipt.update(control_policy=self.recovery.frozen.POLICY, total_optimizer_steps=0,
                cumulative_optimizer_steps=0, weight_updates_enabled=False,
                no_update_reason='R232_frozen_sibling_updates_disabled', presentations=[],
                child_token_exposures=0, anchor_token_exposures=0, frozen_base_verified=True,
                before_adapter_sha256='a' * 64, after_adapter_sha256='a' * 64,
                before_optimizer_state_sha256='d' * 64, after_optimizer_state_sha256='d' * 64)
        self.stream.pending = 'sleep:' + self.digest([row['source_sha256'] for row in self.stream.pending_rows()])
        self.journal.record('SLEEP_REQUEST', dict(cycle=1, resume_state=self.stream.checkpoint()))
        self.stream.pending = None
        self.stream.commit_sleep(receipt, self.journal.record)
        complete_index = self.journal._state['index'] - 1
        complete_sha256 = self.journal._state['previous']
        learned = self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1, status='COMPLETE',
            checkpoint_sha256=checkpoint['checkpoint_sha256']))
        self.candidate = dict(checkpoint=checkpoint, resume_state=self.stream.checkpoint(),
            complete_index=complete_index, complete_sha256=complete_sha256, learn_sha256=learned['sha256'])
        self.plan = dict(source_root=str(self.root / 'epoch/source'), hard_end_unix=10000,
            physical=physical, think_act_learn=dict(trial_id='synthetic-pair'))
        self.selection = dict(policy=self.tail.POLICY, root=str(self.journal.root),
            journal_id=self.journal._manifest['journal_id'], complete_index=complete_index,
            complete_sha256=complete_sha256, life_id='synthetic-pair', max_tail_records=64,
            max_tail_bytes=16 * 1024 * 1024, sidecars=[], persist_complete_anchors=False)
        self.control = self.root / 'epoch/control'
        self.preservation = dict(checkpoint=checkpoint, coherent_state=self.candidate['resume_state'],
            checkpoint_tail_selection=self.selection)
        self.token = dict(old_native_exited=True, receiver=dict(plan=self.plan,
            plan_sha256=self.digest(self.plan), same_journal_root=str(self.journal.root)),
            exact_complete=self.candidate, deadline_unix=10000, epoch_id='synthetic-source-epoch',
            new_source_pins={'actual_local_source': 'synthetic-not-live-authority'})
        self.save_token()

    def save_token(self):
        put(self.control / 'PRESERVATION.json', self.preservation)
        self.token['receiver']['preservation_sha256'] = raw_sha(self.control / 'PRESERVATION.json')
        self.token['sha256'] = self.digest({key: value for key, value in self.token.items() if key != 'sha256'})
        put(self.control / 'RETENTION_HANDOFF.json', self.token)

    def step(self, fail=False):
        def generate(messages, **kwargs):
            if fail:
                raise RuntimeError('synthetic_pending_request')
            return dict(raw='Synthetic child output.', token_ids=[10, 2], terminal=True, truncated=False)
        return self.stream.step(generate, lambda messages: sum(len(message['content'].split()) + 4
            for message in messages), self.journal.record, now=lambda: 100)

    def inbox(self, name):
        path = self.journal.inbox / (name + '.json')
        put(path, dict(id=name, text='Retained parent message.', actor='parent', split='TRAIN'))
        return path

    def open_receiver(self):
        self.journal.close()
        started = time.monotonic()
        received = self.runtime.bind_journal(self.base, self.plan)(self.journal.root)
        self.addCleanup(received.close)
        elapsed = time.monotonic() - started
        METRICS.append(dict(physical=self.plan['physical'], open_seconds=elapsed,
            **received.checkpoint_tail_receipt))
        return received

    def test_exact_source_imports_and_single_r232_binding(self):
        for module in (self.runtime, self.tail, self.recovery):
            self.assertTrue(Path(module.__file__).resolve().is_relative_to(SOURCE))
        content = Path(self.recovery.__file__).read_text()
        self.assertEqual(content.count('bind_journal(journal_module.StreamJournal, plan)'), 1)

    def assert_parity(self, physical):
        self.boundary(physical)
        expected = deepcopy(self.journal._state)
        before = {str(path): path.read_bytes() for path in self.journal.root.rglob('*') if path.is_file()}
        self.journal.close()
        started = time.monotonic()
        with self.base(self.journal.root) as full:
            self.assertEqual(full._state, expected)
        full_seconds = time.monotonic() - started
        received = self.open_receiver()
        self.assertEqual(received._state['latest'], expected['latest'])
        self.assertEqual(received._state['inbox'], expected['inbox'])
        self.assertEqual(received._state['index'], expected['index'] + 1)
        epoch = received._read_json(received._records_fd, f'{expected["index"]:020d}.json')
        self.assertEqual(epoch['kind'], 'RETENTION_SOURCE_ADOPTED')
        self.assertFalse(epoch['document']['wall_extended'])
        self.assertEqual(epoch['document']['deadline_unix'], 10000)
        self.assertTrue(all(Path(path).read_bytes() == content for path, content in before.items()))
        METRICS[-1]['synthetic_full_replay_seconds'] = full_seconds

    def test_learner_exact_tail_and_full_replay_parity(self):
        self.assert_parity(0)

    def test_frozen_zero_update_exact_tail_and_full_replay_parity(self):
        self.assert_parity(1)
        self.assertEqual(self.candidate['checkpoint']['optimizer_steps'], 0)
        self.assertEqual(self.stream.sleep_receipts[-1]['child_token_exposures'], 0)

    def test_registered_and_late_inbox_files_are_preserved(self):
        self.boundary()
        first = self.inbox('registered')
        self.journal.read_inbox()
        late = self.inbox('late')
        pins = {path: raw_sha(path) for path in (first, late)}
        received = self.open_receiver()
        self.assertEqual(len(received.read_inbox()), 2)
        self.assertEqual(pins, {path: raw_sha(path) for path in pins})

    def test_pending_request_cannot_adopt(self):
        self.boundary()
        with self.assertRaisesRegex(RuntimeError, 'synthetic_pending_request'):
            self.step(fail=True)
        with self.assertRaisesRegex(ValueError, 'exact_resolved_saved_state'):
            self.open_receiver()

    def test_intervening_generation_cannot_adopt(self):
        self.boundary()
        self.step()
        with self.assertRaisesRegex(ValueError, 'exact_resolved_saved_state'):
            self.open_receiver()

    def test_wrong_learn_binding_rejected_without_epoch_write(self):
        self.boundary()
        self.candidate['learn_sha256'] = '0' * 64
        self.save_token()
        count = len(list((self.journal.root / 'records').iterdir()))
        with self.assertRaisesRegex(ValueError, 'same_driver_completion'):
            self.open_receiver()
        self.assertEqual(len(list((self.journal.root / 'records').iterdir())), count)

    def test_raw_prefix_corruption_rejected(self):
        self.boundary()
        path = self.journal.root / 'records/00000000000000000000.json'
        path.write_bytes(path.read_bytes().replace(b'System.', b'System!', 1))
        with self.assertRaisesRegex(ValueError, 'integrity'):
            self.open_receiver()

    def test_original_writer_lock_remains_exclusive(self):
        self.boundary()
        with self.assertRaises((ValueError, BlockingIOError)):
            self.runtime.bind_journal(self.base, self.plan)(self.journal.root)

    def test_explicit_audit_still_replays_every_transition(self):
        self.boundary()
        received = self.open_receiver()
        with patch.object(self.tail, 'scan', side_effect=AssertionError('audit_must_not_use_fast_path')), \
                patch.object(received, '_advance', wraps=received._advance) as advance:
            result = received.audit()
        self.assertEqual(advance.call_count, result['record_count'])
        self.assertTrue(any(call.args[1] == 'REQUEST' for call in advance.call_args_list))
        self.assertFalse(received._retention_full_audit)

    def test_partial_initialization_is_not_hidden_by_fast_path(self):
        self.boundary()
        (self.journal.root / 'marker.partial').write_bytes(b'partial')
        with self.assertRaisesRegex(ValueError, 'incomplete_journal_initialization'):
            self.open_receiver()

    def test_tail_bound_fails_without_full_replay_fallback(self):
        self.boundary()
        for name in ('first', 'second'):
            self.inbox(name)
        self.journal.read_inbox()
        self.selection['max_tail_records'] = 1
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'record_bound_exceeded'):
            self.open_receiver()

    def test_wrong_deadline_and_unexited_token_cannot_adopt(self):
        self.boundary()
        self.token['old_native_exited'] = False
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'exact_exited_source_epoch_token'):
            self.open_receiver()
        self.token['old_native_exited'] = True
        self.token['deadline_unix'] += 1
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'same_receiving_plan_and_deadline'):
            self.open_receiver()

    def test_cold_start_is_forbidden(self):
        self.boundary()
        with self.assertRaisesRegex(ValueError, 'same_journal_resume_only'):
            self.runtime.bind_journal(self.base, self.plan)(self.journal.root, create=True)


def main():
    global SOURCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.source.resolve()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_environment_required')
    sys.path.insert(0, str(SOURCE))
    with patch('subprocess.Popen', side_effect=AssertionError('no_subprocess_from_source_tests')), \
            patch('os.kill', side_effect=AssertionError('no_signals_from_source_tests')), \
            patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no_pidfd_signals')):
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(PairSourceTests))
    print(json.dumps(dict(passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), synthetic_only=True,
        GPU_calls=0, dispatches=0, native_signals=0, prefix_cost_samples=METRICS), sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
