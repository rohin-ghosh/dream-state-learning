"""CPU context-policy checks with the real history, stream and journal."""

import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest

from gpu import orch_r125_continual_native as native
from gpu import orch_r166_corrected_retelling as retelling
from gpu import orch_r179_context_survival as policy
from gpu.orch_r125_stream_journal import StreamJournal
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest
from organism_v6.orch_r125_plain_context import VERSION


def event(actor, text, name):
    return TrainEvent(event_id=name, actor=actor, split='TRAIN', phase='experience',
        episode_id='test', source_id='CPU_FIXTURE', source_sha256=digest([name, text]),
        origin='TRAIN_COLLECTION', text=text)


class ContextSurvivalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.journal = StreamJournal(self.root / 'stream', create=True)
        self.addCleanup(self.journal.close)
        self.stream = ContinualStream(TrainHistory(system_prompt='Standing purpose.',
            birth_prompt='Work on your actual object.'), context_limit=16384,
            segment_tokens=512, segments_per_sleep=2, deadline_unix=time.time()+100,
            model_state_sha256='a'*64, allow_eviction=True)
        self.stream.set_presentation(dict(version=VERSION, system_prompt='Standing purpose.',
            birth_prompt='Work on your actual object.'), 16384)
        self.prompts = []
        self.next_text = 'My object is a bridge design. The load result is unresolved.'
        self.child = SimpleNamespace(plan=dict(root=str(self.root),
            compaction_invitation='Retell your actual work.', presleep_variant='free_distillation'),
            generate=self.generate, count_tokens=self.count_tokens)

    def count_tokens(self, messages):
        return sum(len(message['content'].split()) for message in messages)

    def generate(self, messages, **options):
        self.prompts.append(deepcopy(messages))
        return dict(raw=self.next_text, token_ids=[101, 102, 2], terminal=True, truncated=False)

    def step(self, incoming=()):
        return self.stream.step(self.generate, self.count_tokens, self.journal.record, incoming=incoming)

    def prepare(self, source=None, cycle=1):
        patched = policy.patch_native(source or Path(native.__file__).read_text())
        function = next(node for node in ast.parse(patched).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'prepare_sleep')
        namespace = dict(native.__dict__)
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<CPU-context-policy>', 'exec'), namespace)
        namespace['prepare_sleep'](self.child, self.stream, self.journal, cycle)

    def sleep(self, cycle):
        rows = self.stream.pending_rows()
        pending = self.stream.checkpoint()
        pending['state']['pending'] = 'sleep:' + digest([row['source_sha256'] for row in rows])
        pending['sha256'] = digest(pending['state'])
        self.journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
        return self.stream.commit_sleep(dict(status='COMPLETE', cycle=cycle, optimizer_steps=16,
            new_row_sha256=[row['source_sha256'] for row in rows],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64)), self.journal.record)

    def prime(self):
        self.step([event('parent', 'Rohin: distinguish a prediction from a measured load.', 'parent1'),
                   event('environment', 'The instrument reported a failed measurement.', 'tool1')])
        self.step()

    def test_low_context_retains_conversation_through_two_sleeps_and_restore(self):
        self.prime()
        for cycle in (1, 2):
            self.prepare(cycle=cycle)
            before = self.stream.history.checkpoint()
            self.assertEqual(self.stream.history.visible_frontier.event_count, 0)
            checkpoint = self.sleep(cycle)
            self.assertEqual(self.stream.history.checkpoint(), before)
            self.stream = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
            self.step()
            rendered = str(self.prompts[-1])
            self.assertIn('measured load', rendered)
            self.assertIn('failed measurement', rendered)
            self.assertIn('bridge design', rendered)
            self.step()
        self.assertEqual(self.stream.history.operations, ())

    def test_retelling_stays_own_target_and_external_text_stays_masked(self):
        self.prime()
        previous = deepcopy(self.stream.rows)
        self.prepare()
        self.assertEqual(self.stream.rows[:-1], previous)
        row = self.stream.rows[-1]
        self.assertEqual(row['target'], self.next_text)
        self.assertFalse(row['prefix_loss'])
        self.assertTrue(row['target_loss'])
        self.assertEqual(row['actor'], 'child')
        self.assertTrue(any('Rohin:' in message['content'] for message in row['prefix']))
        rendered = self.stream.render(self.count_tokens)
        self.assertTrue(all(label == -100 for label in rendered.labels))

    def test_threshold_compacts_only_view_and_keeps_raw_evidence(self):
        self.prime()
        self.child.count_tokens = lambda messages: 12288
        raw_before = len(self.stream.history.events)
        self.prepare()
        self.assertGreater(len(self.stream.history.events), raw_before)
        self.assertEqual(self.stream.history.operations[-1]['kind'], 'compaction')
        self.assertEqual(self.stream.history.visible_frontier.event_count, len(self.stream.history.events)-1)
        self.assertTrue(any(entry.event_id == 'parent1' for entry in self.stream.history.events))
        before = self.stream.history.checkpoint()
        self.sleep(1)
        self.assertEqual(self.stream.history.checkpoint(), before)

    def test_threshold_overflow_does_not_invoke_oldest_eviction(self):
        self.prime()
        self.child.count_tokens = lambda messages: 15000
        self.prepare()
        self.assertEqual([item['kind'] for item in self.stream.history.operations], ['compaction'])

    def test_no_distillation_does_not_add_a_target_or_change_view(self):
        self.prime()
        self.child.plan['presleep_variant'] = 'no_distillation'
        before = self.stream.checkpoint()
        self.prepare()
        self.assertEqual(self.stream.checkpoint(), before)
        self.sleep(1)

    def test_empty_summary_retains_context_without_fabrication(self):
        self.prime()
        self.next_text = ''
        self.prepare()
        self.assertEqual(self.stream.history.operations, ())
        self.assertEqual(self.stream.rows[-1]['target'], '')

    def test_corrected_retelling_invitation_is_unchanged(self):
        self.prime()
        scope = dict(schema=retelling.SCHEMA, root=str(self.root),
            directive_sha256=retelling.DIRECTIVE_SHA256, parented=True,
            presleep_variant='free_distillation')
        source = retelling.patch_source(Path(native.__file__).read_text(), scope)
        self.prepare(source)
        self.assertTrue(any(retelling.INVITATION == message['content'] for message in self.prompts[-1]))
        self.assertEqual(self.stream.history.operations, ())

    def test_patch_does_not_change_any_other_native_function(self):
        source = Path(native.__file__).read_text()
        patched = policy.patch_native(source)
        self.assertEqual(retelling.without_prepare_sleep(ast.parse(source)),
                         retelling.without_prepare_sleep(ast.parse(patched)))
        with self.assertRaisesRegex(ValueError, 'successor_only'):
            policy.patch_native(patched)
        with self.assertRaisesRegex(ValueError, 'one_exact'):
            policy.patch_native(source.replace('stream.history.compact(summary,', 'other(summary,'))

    def test_threshold_and_actual_summary_binding(self):
        self.assertEqual(policy.threshold_tokens(self.stream), 12288)
        self.prime()
        actual = self.stream.history.events[-2]
        fake = replace(actual, event_id='compaction:1', phase='compaction', text='Invented replacement.')
        with self.assertRaisesRegex(ValueError, 'actual_latest_child'):
            policy.retain_or_compact(self.child, self.stream, self.journal, fake, 1)


if __name__ == '__main__':
    unittest.main()
