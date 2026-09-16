"""Non-material CPU regressions for native bindings and journal recovery."""

from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r125_continual_native as native
from gpu.orch_r125_continual_native import NativeChild
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


def make_plan(directory):
    directory = Path(directory)
    return dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        system_prompt=native.SYSTEM, birth_prompt=native.BIRTH,
        compaction_invitation=native.COMPACTION_INVITATION,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25,
        seed=0, segments_per_sleep=2, segment_tokens=16, context_limit=8192,
        max_sleeps=2, physical=0, gpu_uuid='GPU-synthetic',
        hard_end_unix=time.time()+600, lease_end_unix=time.time()+1000,
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05,
                     no_repeat_ngram_size=16),
        root=str(directory/'life'), model_dir=str(directory/'model'),
        anchors=str(directory/'anchors'), source_root=str(directory/'source'))


class Tokenizer:
    eos_token_id = 2
    all_special_ids = [0, 1, 2]

    def apply_chat_template(self, messages, **kwargs):
        if kwargs != dict(tokenize=True, add_generation_prompt=True, return_dict=False):
            raise AssertionError('unexpected chat template options')
        return [1] + [ord(character)+100 for message in messages for character in message['content']]

    def decode(self, tokens, **kwargs):
        if kwargs != dict(skip_special_tokens=False, clean_up_tokenization_spaces=False):
            raise AssertionError('unexpected decode options')
        return ''.join(chr(token-100) for token in tokens)


class EncodingAndPlanTests(unittest.TestCase):
    def row(self):
        return dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
            prefix=[dict(role='system', content='s'), dict(role='user', content='p')],
            token_ids=[197, 198, 2], target='ab', terminal=True)

    def test_encode_masks_entire_prefix_and_preserves_native_eos(self):
        row = self.row()
        before = deepcopy(row)
        encoded = native.encode_own(row, Tokenizer(), 6)
        self.assertEqual(encoded.input_ids, (1, 215, 212, 197, 198, 2))
        self.assertEqual(encoded.labels, (-100, -100, -100, 197, 198, 2))
        self.assertEqual(encoded.target_ids, (197, 198, 2))
        self.assertEqual(row, before)

    def test_nonterminal_target_never_gets_synthetic_eos(self):
        row = dict(self.row(), token_ids=[197, 198], terminal=False)
        encoded = native.encode_own(row, Tokenizer(), 5)
        self.assertEqual(encoded.input_ids, (1, 215, 212, 197, 198))
        self.assertEqual(encoded.target_ids, (197, 198))

    def test_encode_rejects_visibility_and_token_mutations(self):
        cases = [
            ({'split': 'HELD'}, 'child_targets_only'),
            ({'actor': 'parent'}, 'child_targets_only'),
            ({'prefix_loss': True}, 'child_targets_only'),
            ({'target_loss': False}, 'child_targets_only'),
            ({'prefix_loss': 0}, 'child_targets_only'),
            ({'target_loss': 1}, 'child_targets_only'),
            ({'token_ids': []}, 'actual_native_target_ids'),
            ({'token_ids': [True, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [-1, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [197.0, 2]}, 'actual_native_target_ids'),
            ({'token_ids': [197, 198]}, 'actual_terminal_eos'),
            ({'token_ids': [197, 2, 2]}, 'no_special_token_target_injection'),
            ({'token_ids': [1, 2]}, 'no_special_token_target_injection'),
            ({'terminal': False}, 'no_special_token_target_injection'),
            ({'target': 'rewritten'}, 'native_target_roundtrip'),
        ]
        for changes, reason in cases:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, reason):
                native.encode_own(dict(self.row(), **changes), Tokenizer(), 100)

    def test_encode_rejects_one_token_over_budget_without_trimming(self):
        row = self.row()
        before = deepcopy(row)
        with self.assertRaisesRegex(ValueError, 'whole_source_no_training_trim'):
            native.encode_own(row, Tokenizer(), 5)
        self.assertEqual(row, before)

    def test_schedule_rounds_then_old_rows_once_without_mutation(self):
        new_rows = [dict(source_sha256='first'), dict(source_sha256='second')]
        old_rows = [dict(source_sha256='old-first'), dict(source_sha256='old-second')]
        before = deepcopy((new_rows, old_rows))
        schedule = native.presentation_schedule(new_rows, old_rows)
        self.assertEqual([(kind, row['source_sha256']) for kind, row in schedule],
            [('NEW', 'first'), ('NEW', 'second')]*16
            + [('REHEARSAL', 'old-first'), ('REHEARSAL', 'old-second')])
        self.assertTrue(all(row is new_rows[index % 2] for index, (_, row) in enumerate(schedule[:32])))
        self.assertEqual((new_rows, old_rows), before)
        self.assertEqual(len(native.presentation_schedule(new_rows, [])), 32)
        with self.assertRaisesRegex(ValueError, 'new_rows_required'):
            native.presentation_schedule([], old_rows)

    def test_plan_accepts_inclusive_limits_and_unbounded_sleep_count(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(native.time, 'time', return_value=100):
            plan = make_plan(directory)
            for changes in (dict(segment_tokens=1, context_limit=2),
                            dict(segment_tokens=1024, context_limit=8192, physical=7),
                            dict(max_sleeps=None, hard_end_unix=880, lease_end_unix=1000)):
                candidate = dict(plan, **changes)
                self.assertIs(native.validate_plan(candidate), candidate)

    def test_plan_rejects_contract_schedule_path_and_wall_mutations(self):
        cases = [
            ('schema', 'other', 'frozen_native_contract'),
            ('base_sha256', '0'*64, 'frozen_native_contract'),
            ('system_prompt', native.SYSTEM+' ', 'exact_posted_prompts'),
            ('birth_prompt', 'other', 'exact_posted_prompts'),
            ('compaction_invitation', 'other', 'exact_posted_prompts'),
            ('new_presentations', 15, 'declared_presentation_and_anchor_schedule'),
            ('rehearsal_presentations', 2, 'declared_presentation_and_anchor_schedule'),
            ('anchor_lambda', 0.5, 'declared_presentation_and_anchor_schedule'),
            ('seed', 1, 'initial_native_schedule'),
            ('segments_per_sleep', 3, 'initial_native_schedule'),
            *[('segment_tokens', value, 'bounded_native_segment') for value in (True, 0, 1025, 1.5)],
            *[('context_limit', value, 'bounded_native_context') for value in (True, 16, 8193)],
            *[('max_sleeps', value, 'explicit_smoke_or_long_life') for value in (True, 0, -1, 1.5)],
            *[('physical', value, 'explicit_gpu_identity') for value in (True, -1, 8)],
            ('gpu_uuid', 'other', 'explicit_gpu_identity'),
            *[('hard_end_unix', value, 'within_lease_wall') for value in (100, 99, 981)],
            ('decoder', {}, 'posted_decoder'),
            *[(key, 'relative', 'absolute_path:'+key) for key in ('root', 'model_dir', 'anchors', 'source_root')],
        ]
        with tempfile.TemporaryDirectory() as directory, patch.object(native.time, 'time', return_value=100):
            plan = make_plan(directory)
            for key, value, reason in cases:
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, reason):
                    native.validate_plan(dict(plan, **{key: value}))
            source = Path(plan['source_root'])
            source.mkdir()
            alias = Path(directory)/'alias'
            alias.symlink_to(source, target_is_directory=True)
            for root in (source, source/'raw', alias/'raw'):
                with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'raw_outside_source_tree'):
                    native.validate_plan(dict(plan, root=str(root)))


class SyntheticChild:
    def __init__(self, plan, checkpoint=None):
        self.plan = plan
        self.tokenizer = Tokenizer()
        self.engine = SimpleNamespace(runtime={'synthetic': True})
        self.optimizer_steps = checkpoint['optimizer_steps'] if checkpoint else 0
        self.generations = 0
        self.sleeps = []
        self.loaded_checkpoint = checkpoint
        if checkpoint:
            NativeChild.verify_checkpoint(checkpoint)

    def adapter_hash(self):
        return digest(['synthetic-adapter', self.optimizer_steps])

    def checkpoint(self, directory):
        directory = Path(directory)
        adapter_path = directory/'adapter'
        adapter_path.mkdir(parents=True)
        (adapter_path/'weights').write_text(str(self.optimizer_steps))
        optimizer_path = directory/'optimizer_rng.pt'
        optimizer_path.write_text('synthetic optimizer and RNG '+str(self.optimizer_steps))
        files = {'weights': native.sha(adapter_path/'weights')}
        checkpoint = dict(base_sha256=native.BASE_SHA256, adapter_path=str(adapter_path),
            adapter_files=files, adapter_state_sha256=self.adapter_hash(),
            optimizer_rng_path=str(optimizer_path), optimizer_steps=self.optimizer_steps,
            checkpoint_sha256=dict(adapter=digest(files), optimizer=native.sha(optimizer_path),
                                   rng=native.sha(optimizer_path)))
        native.write_once(directory/'COMMIT.json', checkpoint)
        return checkpoint

    def count_tokens(self, messages):
        return sum(len(message['content'].split())+4 for message in messages)

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.generations += 1
        if self.generations > 12:
            raise AssertionError('synthetic generation budget exhausted')
        if deadline_unix != self.plan['hard_end_unix'] or max_new_tokens != self.plan['segment_tokens']:
            raise AssertionError('generation budget changed')
        raw = 'own '+str(self.generations)
        return dict(raw=raw, token_ids=[ord(character)+100 for character in raw]+[2],
                    terminal=True, truncated=False)

    def sleep(self, new_rows, old_rows, anchors, record):
        self.sleeps.append(deepcopy((new_rows, old_rows)))
        schedule = native.presentation_schedule(new_rows, old_rows)
        self.optimizer_steps += len(schedule)
        record('UPDATE', dict(optimizer_step=self.optimizer_steps, synthetic=True))
        return dict(optimizer_steps=len(schedule), total_optimizer_steps=self.optimizer_steps)


class NativeLoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plan = make_plan(self.directory)
        Path(self.plan['root']).mkdir()
        self.plan_path = self.directory/'plan.json'
        native.write_once(self.plan_path, self.plan)
        self.children = []
        self.readouts = []
        self.fail_generate = False
        self.fail_sleep = False
        self.stop_after_readout = None
        self.stop_before_readout = None
        self.start_patch(patch.object(native, 'NativeChild', side_effect=self.make_child))
        self.start_patch(patch.object(native, 'fresh_readout', side_effect=self.observe_readout))
        self.start_patch(patch('gpu.orch_r107_base_anchors_inventory.build_inventory',
                               return_value=({}, {'synthetic': True})))
        self.start_patch(patch.object(native.signal, 'signal'))
        self.start_patch(patch.object(native.signal, 'setitimer'))
        self.start_patch(patch.object(native.subprocess, 'Popen', side_effect=AssertionError('no launches')))
        self.start_patch(patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def make_child(self, plan, checkpoint=None):
        child = SyntheticChild(plan, checkpoint)
        if self.fail_generate:
            child.generate = self.interrupt
        if self.fail_sleep:
            child.sleep = self.interrupt
        self.children.append(child)
        return child

    @staticmethod
    def interrupt(*args, **kwargs):
        raise RuntimeError('synthetic interruption')

    def records(self):
        return [native.read(path) for path in sorted((Path(self.plan['root'])/'stream'/'records').glob('*.json'))
                if not path.name.endswith('.intent.json')]

    def observe_readout(self, child, plan_path, checkpoint, cycle):
        records = self.records()
        self.assertIn(records[-1]['kind'], ('LOADED', 'SLEEP_COMPLETE'))
        committed = next(record for record in reversed(records)
                         if record['kind'] in ('COMMITTED', 'SLEEP_COMPLETE'))
        self.assertEqual(committed['kind'], 'COMMITTED' if cycle == 0 else 'SLEEP_COMPLETE')
        state = committed['document']['state' if cycle == 0 else 'resume_state']['state']
        self.assertEqual(state['model_state_sha256'], digest(checkpoint['checkpoint_sha256']))
        self.assertEqual(child.optimizer_steps, checkpoint['optimizer_steps'])
        self.assertEqual(plan_path, self.plan_path)
        if self.stop_before_readout == cycle:
            self.interrupt()
        native.write_once(Path(self.plan['root'])/'readouts'/f'sleep_{cycle:06d}_DISPATCH.json',
                          dict(cycle=cycle, synthetic=True))
        self.readouts.append(cycle)
        if self.stop_after_readout == cycle:
            self.interrupt()

    def restore(self):
        with StreamJournal(Path(self.plan['root'])/'stream') as journal:
            return ContinualStream.restore(**journal.latest_checkpoint())

    def test_two_sleeps_use_native_compaction_order_and_real_journal(self):
        native.run(self.plan_path)
        records = self.records()
        expected = ['COMMITTED', 'LOADED']
        for unused in range(2):
            expected += ['REQUEST', 'RESPONSE', 'COMMITTED']*3
            expected += ['COMPACTION', 'SLEEP_REQUEST', 'UPDATE', 'SLEEP_COMPLETE']
        expected += ['REQUEST', 'RESPONSE', 'COMMITTED', 'TERMINAL']
        self.assertEqual([record['kind'] for record in records], expected)
        self.assertEqual(self.readouts, [0, 1, 2])
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(stream.sleep_frontier, 6)
        self.assertEqual(len(stream.rows), 7)
        self.assertEqual(len(stream.sleep_receipts), 2)
        self.assertEqual([len(new) for new, old in self.children[0].sleeps], [3, 3])
        self.assertEqual([len(old) for new, old in self.children[0].sleeps], [0, 3])
        self.assertEqual(self.children[0].optimizer_steps, 99)
        self.assertEqual([row['source_sha256'] for row in stream.pending_rows()], [stream.rows[-1]['source_sha256']])
        self.assertEqual(stream.rows[-1]['model_state_sha256'], stream.model_state_sha256)
        self.assertEqual(Counter(operation['kind'] for operation in stream.history.operations), {'compaction': 2})
        for index, operation in enumerate(stream.history.operations):
            self.assertEqual(operation['summary']['text'], stream.rows[index*3+2]['target'])
            self.assertEqual(operation['summary']['actor'], 'child')
        self.assertFalse(records[-1]['document']['retained_learning_claim'])

    def test_empty_summary_does_not_stop_continuation_or_invent_compaction(self):
        original = SyntheticChild.generate

        def generate(child, messages, **kwargs):
            response = original(child, messages, **kwargs)
            response.update(raw='', token_ids=[2], terminal=True, truncated=False)
            return response

        with patch.object(SyntheticChild, 'generate', generate):
            native.run(self.plan_path)
        records = self.records()
        stream = self.restore()
        self.assertEqual(sum(record['kind'] == 'COMPACTION_SKIPPED' for record in records), 2)
        self.assertEqual(len(stream.rows), 7)
        self.assertEqual(len(stream.sleep_receipts), 2)
        self.assertEqual(len(stream.history.operations), 0)
        budget = stream.history.events[0]
        self.assertEqual(budget.event_id, 'runtime:birth_budget')
        self.assertEqual(budget.actor, 'environment')
        self.assertIn('context_limit', budget.text)

    def test_pending_generation_resume_never_loads_or_redispatches(self):
        self.fail_generate = True
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        before = self.records()
        self.assertEqual(before[-1]['kind'], 'REQUEST')
        self.assertIsNotNone(self.restore().pending)
        with self.assertRaisesRegex(ValueError, 'unresolved_generation_or_sleep_requires_reconciliation'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_pending_sleep_resume_cannot_fall_back_to_initial_adapter(self):
        self.fail_sleep = True
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        before = self.records()
        self.assertEqual(before[-1]['kind'], 'SLEEP_REQUEST')
        self.assertTrue(self.restore().pending.startswith('sleep:'))
        with self.assertRaisesRegex(ValueError, 'unresolved_generation_or_sleep_requires_reconciliation'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def stop_at_committed_sleep(self):
        self.stop_after_readout = 1
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        self.assertIsNone(self.restore().pending)
        self.stop_after_readout = None

    def test_resume_after_sleep_loads_exact_checkpoint_without_replaying_birth(self):
        self.stop_at_committed_sleep()
        first_rows = deepcopy(self.restore().rows)
        native.run(self.plan_path, resume=True)
        stream = self.restore()
        self.assertEqual(stream.rows[:3], first_rows)
        self.assertEqual(self.readouts, [0, 1, 2])
        self.assertEqual(self.children[1].loaded_checkpoint['optimizer_steps'], 48)
        self.assertEqual(self.children[1].optimizer_steps, 99)
        self.assertEqual(len(self.children[1].sleeps), 1)
        self.assertEqual([receipt['cycle'] for receipt in stream.sleep_receipts], [1, 2])
        self.assertEqual(len(stream.rows), 7)

    def test_resume_dispatches_missing_sleep_readout_before_new_generation(self):
        self.stop_before_readout = 1
        with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
            native.run(self.plan_path)
        self.assertEqual(self.readouts, [0])
        self.assertIsNone(self.restore().pending)
        self.assertEqual(self.restore().sleep_frontier, len(self.restore().rows))
        self.stop_before_readout = None
        native.run(self.plan_path, resume=True)
        self.assertEqual(self.readouts, [0, 1, 2])
        self.assertEqual(self.children[1].loaded_checkpoint['optimizer_steps'], 48)

    def test_committed_unslept_generation_cannot_resume_stale_rng(self):
        original_step = ContinualStream.step

        def stop_after_commit(stream, *args, **kwargs):
            original_step(stream, *args, **kwargs)
            self.interrupt()

        with patch.object(ContinualStream, 'step', stop_after_commit):
            with self.assertRaisesRegex(RuntimeError, 'synthetic interruption'):
                native.run(self.plan_path)
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(len(stream.rows), 1)
        self.assertEqual(stream.sleep_frontier, 0)
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'resume_requires_saved_RNG_sleep_boundary'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_terminal_continuation_is_not_a_saved_rng_resume_boundary(self):
        native.run(self.plan_path)
        stream = self.restore()
        self.assertIsNone(stream.pending)
        self.assertEqual(len(stream.rows)-stream.sleep_frontier, 1)
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'resume_requires_saved_RNG_sleep_boundary'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_resume_rejects_missing_or_ambiguous_exact_model_checkpoint(self):
        self.stop_at_committed_sleep()
        checkpoint_path = Path(self.plan['root'])/'checkpoints'/'sleep_000001'/'COMMIT.json'
        checkpoint = native.read(checkpoint_path)
        checkpoint_path.write_text(json.dumps(dict(checkpoint,
            checkpoint_sha256=dict(adapter='0'*64, optimizer='1'*64, rng='1'*64))))
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'one_exact_model_checkpoint_for_stream'):
            native.run(self.plan_path, resume=True)
        checkpoint_path.write_text(json.dumps(checkpoint))
        native.write_once(Path(self.plan['root'])/'checkpoints'/'duplicate'/'COMMIT.json', checkpoint)
        with self.assertRaisesRegex(ValueError, 'one_exact_model_checkpoint_for_stream'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_resume_rejects_changed_wall_even_with_updated_admission_hash(self):
        self.stop_at_committed_sleep()
        self.plan_path.write_text(json.dumps(dict(self.plan,
            hard_end_unix=self.plan['hard_end_unix']-1)))
        before = self.records()
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=native.sha(self.plan_path)):
            with self.assertRaisesRegex(ValueError, 'same_resume_wall'):
                native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_resume_rejects_corrupted_adapter_before_new_journal_records(self):
        self.stop_at_committed_sleep()
        adapter = Path(self.plan['root'])/'checkpoints'/'sleep_000001'/'adapter'/'weights'
        adapter.write_text('changed adapter bytes')
        before = self.records()
        with self.assertRaisesRegex(ValueError, 'adapter_file_binding'):
            native.run(self.plan_path, resume=True)
        self.assertEqual(self.records(), before)
        self.assertEqual(len(self.children), 1)

    def test_unadmitted_plan_fails_before_child_or_journal_creation(self):
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256='0'*64):
            with self.assertRaisesRegex(ValueError, 'admitted_plan_environment'):
                native.run(self.plan_path)
        self.assertFalse((Path(self.plan['root'])/'stream').exists())
        self.assertEqual(self.children, [])


class FreshReadoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.plan = make_plan(self.directory)
        self.plan_path = self.directory/'plan.json'
        native.write_once(self.plan_path, self.plan)
        self.child = SyntheticChild(self.plan)
        self.checkpoint = self.child.checkpoint(self.directory/'checkpoint')
        self.state = dict(optimizer_steps=0, python_rng='synthetic resident RNG')
        self.child.offload_for_readout = Mock(return_value=self.state)
        self.child.restore_after_readout = Mock()
        self.child.history = 'PRIVATE_RESIDENT_HISTORY_SENTINEL'
        self.output = Path(self.plan['root'])/'readouts'/'sleep_000001'
        self.process = Mock(pid=123456789)
        self.process.wait.return_value = 0
        self.process.poll.return_value = 0
        self.command = None

    def spawn(self, command, **kwargs):
        self.command = command
        self.assertEqual(kwargs['stdin'], native.subprocess.DEVNULL)
        self.assertEqual(kwargs['cwd'], self.plan['source_root'])
        self.assertTrue(kwargs['start_new_session'])
        self.child.offload_for_readout.assert_called_once_with()
        self.assertEqual(command, [native.sys.executable, '-B', '-m', 'gpu.orch_r125_continual_readout',
            '--plan', str(self.plan_path), '--checkpoint',
            str(Path(self.checkpoint['adapter_path']).parent/'COMMIT.json'), '--output', str(self.output)])
        self.assertNotIn(self.child.history, json.dumps(command))
        return self.process

    def dispatch(self, spawn=None):
        with patch.object(native.subprocess, 'Popen', side_effect=spawn or self.spawn) as launch, \
                patch.object(native.os, 'killpg', side_effect=AssertionError('unexpected process signal')):
            native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        self.assertEqual(launch.call_count, 1)
        self.child.restore_after_readout.assert_called_once_with(self.state)

    def test_fresh_process_gets_checkpoint_only_and_dispatch_is_byte_bound(self):
        def completed(command, **kwargs):
            process = self.spawn(command, **kwargs)
            native.write_once(self.output/'COMPLETE.json', {'synthetic': True})
            return process
        checkpoint_before = native.sha(Path(self.checkpoint['adapter_path']).parent/'COMMIT.json')
        self.dispatch(completed)
        dispatch = native.read(self.output.parent/'sleep_000001_DISPATCH.json')
        self.assertEqual(dispatch['command_sha256'], digest(self.command))
        self.assertEqual(dispatch['checkpoint_sha256'], checkpoint_before)
        self.assertFalse(dispatch['history_shared'])
        self.assertFalse(dispatch['parent_present'])
        self.assertNotIn(self.child.history, json.dumps(dispatch))
        self.assertFalse((self.output.parent/'sleep_000001_FAILED.json').exists())
        NativeChild.verify_checkpoint(self.checkpoint)

    def test_nonzero_exit_preserves_failure_and_restores_resident_state(self):
        self.process.wait.return_value = 7
        self.process.poll.return_value = 7
        self.dispatch()
        failure = native.read(self.output.parent/'sleep_000001_FAILED.json')
        self.assertEqual(failure['error'], 'fresh_readout_incomplete')
        self.assertFalse(failure['retry_allowed'])
        self.assertTrue(failure['continued_training_not_evidence_of_readout_success'])
        self.assertFalse((self.output/'COMPLETE.json').exists())
        NativeChild.verify_checkpoint(self.checkpoint)

    def test_zero_exit_without_completion_is_still_failure(self):
        self.dispatch()
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error'],
                         'fresh_readout_incomplete')

    def test_completion_marker_cannot_override_nonzero_exit(self):
        def failed_after_marker(command, **kwargs):
            process = self.spawn(command, **kwargs)
            native.write_once(self.output/'COMPLETE.json', {'synthetic': True})
            process.wait.return_value = 7
            process.poll.return_value = 7
            return process
        self.dispatch(failed_after_marker)
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error'],
                         'fresh_readout_incomplete')
        self.assertEqual(native.read(self.output/'COMPLETE.json'), {'synthetic': True})

    def test_spawn_failure_restores_resident_and_cannot_implicitly_retry(self):
        self.dispatch(Mock(side_effect=OSError('synthetic spawn failure')))
        failure_path = self.output.parent/'sleep_000001_FAILED.json'
        before = failure_path.read_bytes()
        with patch.object(native.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'readout_no_implicit_replay'):
                native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        launch.assert_not_called()
        self.child.offload_for_readout.assert_called_once_with()
        self.assertEqual(failure_path.read_bytes(), before)

    def test_existing_output_is_not_reused_or_overwritten(self):
        native.write_once(self.output/'COMPLETE.json', {'preserved': True})
        with patch.object(native.subprocess, 'Popen') as launch:
            with self.assertRaisesRegex(ValueError, 'readout_no_implicit_replay'):
                native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        launch.assert_not_called()
        self.child.offload_for_readout.assert_not_called()
        self.assertEqual(native.read(self.output/'COMPLETE.json'), {'preserved': True})

    def test_timeout_reaps_owned_process_before_restoring_resident(self):
        events = []
        self.process.wait.side_effect = [native.subprocess.TimeoutExpired('synthetic', 1),
                                        native.subprocess.TimeoutExpired('synthetic', 5), -9]
        self.process.poll.return_value = None
        self.child.restore_after_readout.side_effect = lambda state: events.append(('restore', state))
        with patch.object(native.subprocess, 'Popen', side_effect=self.spawn), \
                patch.object(native.os, 'killpg', side_effect=lambda pid, signum: events.append((pid, signum))):
            native.fresh_readout(self.child, self.plan_path, self.checkpoint, 1)
        self.assertEqual(events, [(self.process.pid, native.signal.SIGTERM),
                                  (self.process.pid, native.signal.SIGKILL), ('restore', self.state)])
        self.assertEqual(self.process.wait.call_count, 3)
        self.assertEqual(native.read(self.output.parent/'sleep_000001_FAILED.json')['error_type'],
                         'TimeoutExpired')


class CheckpointBindingTests(unittest.TestCase):
    def test_checkpoint_rejects_file_and_receipt_mutations(self):
        for mutation, reason in (
                ('base', 'checkpoint_base'), ('optimizer_file', 'optimizer_RNG_file_binding'),
                ('rng_digest', 'optimizer_RNG_file_binding'), ('adapter_file', 'adapter_file_binding'),
                ('extra_adapter_file', 'adapter_file_binding'), ('missing_adapter_file', 'adapter_file_binding'),
                ('adapter_digest', 'adapter_file_binding')):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                checkpoint = SyntheticChild(make_plan(directory)).checkpoint(Path(directory)/'checkpoint')
                NativeChild.verify_checkpoint(checkpoint)
                adapter = Path(checkpoint['adapter_path'])
                if mutation == 'base':
                    checkpoint['base_sha256'] = '0'*64
                elif mutation == 'optimizer_file':
                    Path(checkpoint['optimizer_rng_path']).write_text('changed optimizer and RNG')
                elif mutation == 'rng_digest':
                    checkpoint['checkpoint_sha256']['rng'] = '0'*64
                elif mutation == 'adapter_file':
                    (adapter/'weights').write_text('changed adapter')
                elif mutation == 'extra_adapter_file':
                    (adapter/'extra').write_text('unexpected file')
                elif mutation == 'missing_adapter_file':
                    (adapter/'weights').unlink()
                else:
                    checkpoint['checkpoint_sha256']['adapter'] = '0'*64
                with self.assertRaisesRegex(ValueError, reason):
                    NativeChild.verify_checkpoint(checkpoint)


if __name__ == '__main__':
    unittest.main()
