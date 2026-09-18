import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r115_grid_native as grid
from gpu import orch_r119_grid_async_parent as mailbox
from gpu import orch_r119_grid_final_native as native
from gpu import orch_r139_grid_timer_custody as timer
from gpu import orch_r140_grid_continuation as subject
from gpu import orch_r140_grid_json as normalizer


class CharacterTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=True, add_generation_prompt=True, return_dict=False)
        return list(range(sum(len(message['content']) for message in messages)))


class Fixture(unittest.TestCase):
    def setUp(self):
        runtime = Path(os.environ.get('ORCH_TEST_RUNTIME', '/data/home/rohing/courier/runtime'))
        runtime.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=runtime)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.addCleanup(patch.stopall)
        self.task = dict(id='TRAIN_fixture', split='TRAIN')
        self.rows = []
        self.sent = []
        self.engine = SimpleNamespace(tokenizer=CharacterTokenizer(), batch=self.batch)
        patch.object(grid, 'reserve', side_effect=self.reserve).start()
        patch.object(grid, 'TRAIN_END', float('inf')).start()
        patch.object(grid.Life, 'event', return_value=None).start()
        self.original_life = grid.Life

    def write(self, path, document):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, sort_keys=True))
        return subject.ref(path)

    def reserve(self, root, kind, detail):
        self.rows.append(dict(kind=kind, **detail))
        return subject.FAILED + len(self.rows)

    def batch(self, messages, cap):
        self.sent.append((copy.deepcopy(messages), cap))
        return [dict(raw='synthetic response', token_ids=[1])]

    def normalized(self):
        life_type = subject.normalized_life(grid, normalizer)
        return life_type(self.root, self.engine, {}, subject.CYCLE)

    def overflow(self):
        return [dict(role='system', content='unchanged system'),
                dict(role='user', content=json.dumps(dict(prior_own_reflections='\u4e00' * 2800), sort_keys=True))]

    def history(self, *, failed=False):
        number = subject.FAILED if failed else subject.FAILED - 1
        path = self.root / 'calls' / f'N{number:05d}.json'
        messages = [dict(role='user', content='synthetic history')]
        record = dict(status='STARTED' if failed else 'COMPLETE', messages=messages, cap=384,
                      response=dict(raw='synthetic response', token_ids=[2]))
        self.write(path, record)
        cached = [dict(number=number, task_id=self.task['id'], purpose='episode')]
        parent = mailbox.life_class(grid, 'fixture', first_parent=325)
        parent.poll = Mock(side_effect=AssertionError('no history mailbox polling'))
        return parent, cached, messages, path


class NormalizationTests(Fixture):
    def test_CPU_integration_PROOF_uses_memory_only_and_preserves_failed_charge(self):
        failed = self.root / 'calls/N04456.json'
        self.write(failed, dict(status='STARTED', task_id=self.task['id'], purpose='episode',
                               messages=self.overflow(), cap=384))
        before = failed.read_bytes()
        result = subject.cpu_dispatch_record_proof(grid, normalizer, self.root, CharacterTokenizer())
        self.assertTrue(result['recorded_equals_dispatched'])
        self.assertTrue(result['STARTED_and_COMPLETE_verified'])
        self.assertEqual(result['real_reservations'], 0)
        self.assertEqual(result['disk_writes'], 0)
        self.assertEqual(failed.read_bytes(), before)
        self.assertFalse((self.root / 'calls/N04457.json').exists())

    def test_actual_base_Life_sends_and_records_normalized_messages(self):
        messages = self.overflow()
        original = copy.deepcopy(messages)
        self.normalized().calls([self.task], 'episode', [messages], 384)
        record = grid.read(self.root / 'calls/N04457.json')
        self.assertEqual(record['messages'], self.sent[0][0][0])
        self.assertNotEqual(record['messages'], original)
        self.assertEqual(record['status'], 'COMPLETE')
        self.assertEqual(record['cap'], self.sent[0][1])
        self.assertEqual(record['cap'], 384)
        self.assertEqual(normalizer.recover_original_messages(record['messages'], record['lossless_json_normalization']), original)
        self.assertEqual(messages, original)
        self.assertEqual(len(self.rows), 1)
        self.assertEqual(record['normalizer_sha256'], subject.NORMALIZER_SHA)

    def test_noop_has_no_repair_annotation(self):
        messages = [dict(role='user', content='short')]
        self.normalized().calls([self.task], 'episode', [messages], 384)
        record = grid.read(self.root / 'calls/N04457.json')
        self.assertEqual(record['messages'], messages)
        self.assertNotIn('lossless_json_normalization', record)

    def test_overflow_failure_never_reserves_or_dispatches(self):
        messages = [dict(role='user', content='x' * 17000)]
        with self.assertRaises(normalizer.ContextCapacityError):
            self.normalized().calls([self.task], 'episode', [messages], 384)
        self.assertEqual(self.rows, [])
        self.assertEqual(self.sent, [])

    def test_normalized_started_record_survives_dispatch_failure_no_retry(self):
        self.engine.batch = Mock(side_effect=RuntimeError('synthetic transport failure'))
        with self.assertRaises(RuntimeError):
            self.normalized().calls([self.task], 'episode', [self.overflow()], 384)
        record = grid.read(self.root / 'calls/N04457.json')
        self.assertEqual(record['status'], 'STARTED')
        self.assertEqual(record['messages'], self.engine.batch.call_args.args[0][0])
        self.assertEqual(self.engine.batch.call_count, 1)
        self.assertEqual(len(self.rows), 1)

    def test_readout_is_not_normalized(self):
        for attached, split in [(True, 'TRAIN'), (False, 'FINAL'), (False, 'DEV')]:
            with self.subTest(split=split, attached=attached), self.assertRaises(ValueError):
                self.normalized().calls([dict(self.task, split=split)], 'episode', [self.overflow()], 384,
                                        attached_readout=attached)
        self.assertEqual(self.sent, [])

    def test_wrapper_is_idempotent(self):
        wrapped = subject.normalized_life(grid, normalizer)
        with patch.object(grid, 'Life', wrapped):
            self.assertIs(subject.normalized_life(grid, normalizer), wrapped)

    def test_original_writer_restored_after_failure(self):
        writer = grid.write
        self.engine.batch = Mock(side_effect=RuntimeError('synthetic'))
        with self.assertRaises(RuntimeError):
            self.normalized().calls([self.task], 'episode', [self.overflow()], 384)
        self.assertIs(grid.write, writer)


class ReplayTests(Fixture):
    def test_COMPLETE_reused_without_dispatch_polling_or_charge(self):
        parent, cached, messages, path = self.history()
        before = path.read_bytes()
        life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
        result = life.calls([self.task], 'episode', [messages], 384)
        self.assertEqual(result[0]['reference'], grid.ref(path))
        self.assertEqual(result[0]['raw'], 'synthetic response')
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.rows, [])
        parent.poll.assert_not_called()

    def test_history_rejects_message_cap_task_purpose_and_status_mismatch(self):
        parent, cached, messages, path = self.history()
        for task, purpose, prompt, cap in [(self.task, 'wrong', messages, 384),
                (dict(self.task, id='other'), 'episode', messages, 384),
                (self.task, 'episode', [dict(role='user', content='changed')], 384),
                (self.task, 'episode', messages, 385)]:
            life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
            with self.assertRaises(ValueError):
                life.calls([task], purpose, [prompt], cap)
        self.write(path, dict(grid.read(path), status='STARTED'))
        life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
        with self.assertRaisesRegex(ValueError, 'COMPLETE'):
            life.calls([self.task], 'episode', [messages], 384)

    def test_dry_frontier_does_not_call_engine(self):
        parent, cached, messages, path = self.history(failed=True)
        life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
        with self.assertRaises(subject.FrontierReached):
            life.calls([self.task], 'episode', [messages], 384)
        self.assertEqual(life.frontier['failed_call'], grid.ref(path))
        self.assertEqual(self.rows, [])

    def test_missing_frontier_uses_fresh_normalized_reservation_no_old_mailbox(self):
        parent, cached, messages, path = self.history(failed=True)
        messages = self.overflow()
        self.write(path, dict(grid.read(path), messages=messages))
        before = path.read_bytes()
        normalized = subject.normalized_life(grid, normalizer)
        with patch.object(grid, 'Life', normalized):
            parent = mailbox.life_class(grid, 'fixture', first_parent=325)
            parent.poll = Mock(return_value=([], []))
            life = subject.replay_class(grid, parent, cached, dry=False,
                frontier_calls=normalized.calls)(self.root, self.engine, {}, 112)
            life.calls([self.task], 'episode', [messages], 384)
            parent.poll.assert_not_called()
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(grid.read(self.root / 'calls/N04457.json')['messages'], self.sent[0][0][0])
            life.calls([self.task], 'episode', [[dict(role='user', content='new turn')]], 384)
            parent.poll.assert_called_once()

    def test_cached_open_noop_state_is_unchanged_no_environment_invocation(self):
        parent, cached, messages, path = self.history()
        life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
        life.last_cached_raw = 'synthetic response'
        state = dict(done=True)
        receipt = self.root / 'cycles/0112/open_train/TRAIN_fixture_01.json'
        document = dict(task_id=self.task['id'], split='TRAIN', attached_readout=False, resulting_state=state,
            environment_call=dict(operation='NO_ENVIRONMENT_REQUEST', enacted=False,
                                  semantic_initiative='UNASSESSED', child_received=True))
        self.write(receipt, document)
        with patch.object(grid, 'enacted_environment', side_effect=AssertionError('no env replay')):
            result = life.environment(self.task, state, 'synthetic response', 'open_train', 1, open_turn=True)
        self.assertEqual(result[0], state)
        self.write(receipt, dict(document, resulting_state=dict(done=False)))
        with self.assertRaisesRegex(ValueError, 'cached_open_noop'):
            life.environment(self.task, state, 'synthetic response', 'open_train', 1, open_turn=True)

    def test_open_ask_projection_does_not_fabricate_receipt_or_retry_parents(self):
        parent, cached, messages, path = self.history()
        life = subject.replay_class(grid, parent, cached, dry=True)(self.root, None, {}, 112)
        self.assertEqual(life.ask(self.task, 0, 'open_turn'), dict(disposition=dict(guidance=None)))
        self.assertFalse(life.cached_asks[0]['timestamp_reconstructed'])
        self.assertEqual(self.rows, [])
        parent.poll.assert_not_called()
        with self.assertRaises(ValueError):
            life.ask(self.task, 1, 'open_turn')

    def test_dry_writer_never_mutates_inputs(self):
        path = self.root / 'receipt.json'
        self.write(path, dict(exact=True))
        before = path.read_bytes()
        writer = subject.reconstruction_writer(grid, self.root, dry=True)
        writer(path, dict(exact=True))
        for target, value, replace in [(path, dict(exact=False), False), (path, {}, True),
                                        (self.root / 'new.json', {}, False)]:
            with self.assertRaises(ValueError):
                writer(target, value, replace=replace)
        self.assertEqual(path.read_bytes(), before)

    def test_live_writer_cannot_overwrite_failed_native(self):
        parent, cached, messages, path = self.history(failed=True)
        with self.assertRaisesRegex(ValueError, 'old_native'):
            subject.reconstruction_writer(grid, self.root, dry=False)(path, {}, replace=True)


class TimerTests(Fixture):
    def namespace(self):
        with patch.object(subject, 'dependencies', return_value=(timer, None, None, normalizer)):
            return subject.timer_namespace({})

    def test_timer_callbacks_bound_to_new_source_and_output_clocks_unchanged(self):
        namespace = self.namespace()
        for name in ('arm', 'current_native', 'morning', 'wall_targets', 'signal_exact', 'command'):
            self.assertIs(namespace[name].__globals__, namespace)
        self.assertEqual(namespace['OUTPUT'], subject.TIMER_OUTPUT)
        for name in ('MORNING', 'EVAL_END', 'TRAIN_END', 'HARD_END', 'ACTIONS'):
            self.assertEqual(namespace[name], getattr(timer, name))
        path = self.root / 'plan.json'
        self.write(path, {})
        self.assertEqual(namespace['command']('current', path, '/pub')[0], str(Path(subject.__file__).resolve()))

    def test_custody_receipt_names_actual_continuation_entrypoint(self):
        namespace = self.namespace()
        plan = dict(controller_source={}, old_final_plan={}, initial_successor_receipt='initial',
                    morning_successor_receipt='morning', normalizer={})
        receipt = namespace['custody_receipt'](plan, {}, {})
        self.assertEqual(receipt['initial_resume_entrypoint'], 'continue')
        self.assertEqual(receipt['first_parent'], 325)
        self.assertEqual(receipt['existing_FINAL_quota'], 8)
        self.assertEqual(receipt['additional_FINAL_calls'], 0)
        self.assertFalse(receipt['sealed_inputs_to_parent'])

    def test_post_FINAL_resume_keeps_normalizer_and_parent_floor_evaluation_untouched(self):
        factory = Mock(return_value='prospective parent')
        legacy = SimpleNamespace(original=lambda: SimpleNamespace(mailbox=SimpleNamespace(life_class=factory)))
        prior = SimpleNamespace(mailbox=None)
        view = SimpleNamespace(validate=Mock(return_value=(prior, grid, {}, {})))
        resume = timer.bind(native.resume, custody=view)
        callbacks = dict(resume=resume, evaluate=native.evaluate)
        with (patch.object(subject, 'dependencies', return_value=(timer, None, legacy, normalizer)),
              patch.object(timer, 'adapted_native', return_value=callbacks),
              patch.object(grid, 'Life', self.original_life)):
            namespace = subject.timer_namespace({})
            result = namespace['adapted_native']({}, legacy, {}, {})
            result['resume'].__globals__['custody'].validate({})
            self.assertTrue(grid.Life._r140_normalized)
            self.assertEqual(prior.mailbox.life_class(grid, 'independent_r119_v1'), 'prospective parent')
            factory.assert_called_once_with(grid, 'independent_r119_v1', first_parent=325)
            self.assertIs(result['evaluate'], native.evaluate)

    def test_boundary_retires_only_exact_failed_charge_and_requires_all_others_COMPLETE(self):
        rows = [dict(number=4456, kind='NATIVE', cycle=112, split='TRAIN'),
                dict(number=4457, kind='NATIVE', cycle=112, split='TRAIN')]
        (self.root / 'LEDGER.jsonl').write_text('\n'.join(json.dumps(row) for row in rows))
        self.write(self.root / 'CARRY.json', [])
        self.write(self.root / 'cycles/0112/TRAIN_COMPLETE.json', dict(outcomes=[{}, {}], optimizer_steps=0, carry=[]))
        failed = self.root / 'calls/N04456.json'
        self.write(failed, dict(status='STARTED'))
        self.write(self.root / 'calls/N04457.json', dict(status='COMPLETE'))
        self.write(self.root / 'FAILED_PREDISPATCH.json', dict(failed_call=subject.ref(failed),
                   status='FAILED_PREDISPATCH_CONTEXT_OVERFLOW'))
        with patch.object(subject, 'OUTPUT', self.root), patch.object(subject, 'FAILED_SHA', subject.sha(failed)):
            result = subject.completed_boundary(self.root, None)
            self.assertEqual(result['next_cycle'], 113)
            self.assertEqual(grid.read(failed)['status'], 'STARTED')
            self.write(self.root / 'calls/N04457.json', dict(status='STARTED'))
            with self.assertRaisesRegex(ValueError, 'unfinished'):
                subject.completed_boundary(self.root, None)

    def test_all_runtime_modes_require_Main_publication(self):
        path = self.root / 'plan.json'
        self.write(path, {})
        for mode in ('timer', 'continue', 'current', 'morning', 'evaluate', 'resume'):
            with (self.subTest(mode=mode), patch.object(subject.sys, 'dont_write_bytecode', True),
                  patch.object(subject.sys, 'argv', ['continuation', mode, '--expected-self-sha256',
                    subject.sha(subject.__file__), '--plan', str(path), '--plan-sha256', subject.sha(path)]),
                  patch.object(subject, 'dependencies', side_effect=AssertionError('no runtime before publication'))):
                with self.assertRaisesRegex(ValueError, 'Main_plan'):
                    subject.main()


if __name__ == '__main__':
    unittest.main()
