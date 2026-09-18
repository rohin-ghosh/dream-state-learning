"""No-model tests for the temporary, wholly masked Rohin console session."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from gpu.orch_r125_stream_console import follow_responses
from gpu.orch_r125_stream_journal import StreamJournal
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import run_loop
from gpu.orch_r194_console_reflection import ConsoleReflection, SCHEMA, validate_config
from organism_v6.orch_r124_train_history import TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream


class Child:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def count_tokens(self, messages):
        return sum(len(message['content'].split()) + 4 for message in messages)

    def generate(self, messages, **limits):
        self.calls.append(deepcopy(messages))
        return dict(raw=next(self.outputs), token_ids=[10, 2], terminal=True, truncated=False)


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(lambda: self.journal.close())
        self.stream = ContinualStream(TrainHistory(system_prompt='System.', birth_prompt='Investigate sums.'),
            context_limit=8192, segment_tokens=1024, segments_per_sleep=3,
            deadline_unix=time.time() + 600, model_state_sha256='f' * 64, allow_eviction=True)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.child = Child(['I repeated code instead of my chosen correction.', 'Nothing changed.', 'Normal child action.'])
        self.config = dict(schema=SCHEMA, session_id='synthetic_session')
        self.mode = ConsoleReflection(self.child, self.stream, self.journal, self.config,
            environment_facts='SymPy is now installed; tools remain held.')

    def records(self, kind):
        return [record['document'] for path in sorted((self.root / 'stream/records').glob('*.json'))
                if '.intent.' not in path.name and (record := json.loads(path.read_text()))['kind'] == kind]

    def test_idle_waits_without_generation_and_cannot_be_resumed_by_another_speaker(self):
        publish_parent(self.root, 'Astra', 'done')
        publish_parent(self.root, 'Fable', '/resume')
        self.assertEqual(self.mode.poll_once(), 'WAITING')
        self.assertEqual(self.mode.poll_once(), 'WAITING')
        self.assertEqual(self.child.calls, [])
        self.assertEqual(self.stream.rows, [])
        self.assertEqual(len(self.records('R194_MODE')), 1)

    def test_each_turn_answered_once_and_all_replies_remain_context_only(self):
        for text in ('Why did your action ignore the correction?', 'What do you think now?'):
            publish_parent(self.root, 'Rohin', text)
            self.assertEqual(self.mode.poll_once(), 'ANSWERED')
            self.assertEqual(self.mode.poll_once(), 'WAITING')
        self.assertEqual(len(self.child.calls), 2)
        self.assertEqual(self.stream.pending_rows(), [])
        self.assertEqual(self.stream.sleep_frontier, 0)
        self.assertEqual(self.stream.sleep_receipts, [])
        self.assertEqual(self.records('SLEEP_REQUEST'), [])
        self.assertEqual(self.records('R184_ACT'), [])
        self.assertTrue(all(record['training_eligible'] is False for record in self.records('REQUEST')))
        self.assertTrue(all(record['render_receipt']['all_history_tokens_masked'] for record in self.records('REQUEST')))
        self.assertEqual(len(self.records('CONTEXT_COMMITTED')), 2)
        self.assertIn('without a fixed field block', self.child.calls[0][-1]['content'])
        self.assertIn('SymPy is now installed', self.child.calls[0][-1]['content'])
        self.assertTrue(any('I repeated code instead of my chosen correction.' in message['content']
                            for message in self.child.calls[1]))
        self.assertEqual(list(follow_responses(self.root, max_polls=1)),
                         ['I repeated code instead of my chosen correction.', 'Nothing changed.'])
        self.journal.audit()

    def test_console_turn_compacts_before_three_quarter_context_limit(self):
        from organism_v6.orch_r124_train_history import TrainEvent
        from organism_v6.orch_r125_continual_stream import digest
        for index in range(16):
            text = 'Earlier child reflection. ' * 150
            self.stream.history.append(TrainEvent(event_id=f'older:{index}', text=text,
                actor='child', split='TRAIN', phase='experience', episode_id='console_pressure',
                source_id=f'test:older:{index}', origin='TRAIN_COLLECTION',
                source_sha256=digest([index, text])))
        self.journal.close()
        self.root = self.root / 'pressure'
        self.root.mkdir()
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.journal.record('COMMITTED', dict(kind='BIRTH', state=self.stream.checkpoint()))
        self.mode = ConsoleReflection(self.child, self.stream, self.journal, self.config)
        publish_parent(self.root, 'Rohin', 'What are your own conclusions?')
        self.assertEqual(self.mode.poll_once(), 'ANSWERED')
        self.assertLess(self.records('REQUEST')[-1]['prompt_tokens'], 6144)
        self.assertTrue(self.records('COMPACTION'))
        self.assertIn('What are your own conclusions?', str(self.child.calls[-1]))
        self.assertEqual(self.stream.rows, [])
        self.assertEqual(len([event for event in self.stream.history.events
            if event.event_id.startswith('older:')]), 16)
        self.journal.audit()

    def test_resume_is_explicit_persistent_and_normal_training_masks_console(self):
        publish_parent(self.root, 'Rohin', 'I am not done; keep reflecting.')
        self.assertEqual(self.mode.poll_once(), 'ANSWERED')
        publish_parent(self.root, 'Rohin', 'done')
        self.assertEqual(self.mode.poll_once(), 'RESUMED')
        self.assertEqual(len(self.child.calls), 1)
        checkpoint = self.journal.latest_checkpoint()
        self.journal.close()
        self.journal = StreamJournal(self.root / 'stream')
        restored = ContinualStream.restore(**checkpoint)
        again = ConsoleReflection(self.child, restored, self.journal, self.config)
        self.assertEqual(again.poll_once(), 'RESUMED')
        restored.step(self.child.generate, self.child.count_tokens, self.journal.record)
        self.assertEqual(len(restored.rows), 1)
        self.assertEqual(restored.rows[0]['target'], 'Nothing changed.')
        self.assertFalse(restored.rows[0]['prefix_loss'])
        self.assertTrue(any('I repeated code instead of my chosen correction.' in message['content']
                            for message in restored.rows[0]['prefix']))
        self.assertEqual(restored.rows[0]['event_id'], 'child:segment:0')
        self.journal.audit()

    def test_enter_refuses_unslept_training_rows(self):
        self.stream.step(self.child.generate, self.child.count_tokens, self.journal.record)
        with self.assertRaisesRegex(ValueError, 'complete_sleep_boundary'):
            self.mode.enter()

    def test_no_implicit_retry_after_unresolved_console_generation(self):
        publish_parent(self.root, 'Rohin', 'Reflect.')
        with patch.object(self.child, 'generate', side_effect=RuntimeError('synthetic generation failure')):
            with self.assertRaises(RuntimeError):
                self.mode.poll_once()
        self.assertIsNotNone(self.stream.pending)
        self.assertEqual(self.stream.rows, [])
        self.assertEqual(self.records('CONTEXT_COMMITTED'), [])

    def test_context_commit_cannot_sneak_in_a_training_row(self):
        publish_parent(self.root, 'Rohin', 'Reflect.')
        original = self.journal.record

        def invalid(kind, document):
            if kind == 'CONTEXT_COMMITTED':
                document = deepcopy(document)
                document['training_eligible'] = True
            return original(kind, document)

        with patch.object(self.journal, 'record', side_effect=invalid):
            with self.assertRaisesRegex(ValueError, 'context_commit_requires_masked_response'):
                self.mode.poll_once()
        self.assertIsNotNone(self.stream.pending)

    def test_wall_stop_does_not_release_act_or_sleep(self):
        self.assertFalse(self.mode.wait_until_resumed(now=lambda: self.stream.deadline_unix))
        self.assertEqual(self.child.calls, [])
        self.assertEqual(self.records('SLEEP_REQUEST'), [])
        self.assertTrue(self.records('R194_WALL_STOP')[0]['act_held'])

    def test_run_loop_gate_precedes_every_action_or_sleep(self):
        plan = dict(rehearsal_presentations=0, new_presentations=16,
                    think_act_learn=dict(console_reflection=self.config), hard_end_unix=time.time() + 60)
        with patch('gpu.orch_r184_think_act_learn.ThinkActLearn') as driver, \
                patch.object(ConsoleReflection, 'wait_until_resumed', return_value=False), \
                patch('gpu.orch_r125_continual_native.finish_sleep') as finish:
            run_loop(self.child, self.stream, self.journal, None, plan, self.root, self.root / 'PLAN.json', 45)
        driver.return_value.wake.assert_not_called()
        driver.return_value.prepare_sleep.assert_not_called()
        finish.assert_not_called()

    def test_config_is_explicit_and_bounded(self):
        self.assertEqual(validate_config(self.config), self.config)
        for config in ({}, dict(self.config, session_id='../bad'), dict(self.config, auto_resume=True)):
            with self.assertRaises(ValueError):
                validate_config(config)


if __name__ == '__main__':
    unittest.main()
