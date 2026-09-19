"""Synthetic CPU tests against the isolated, runtime-source-bound fork."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[3]
sys.path.insert(0, str(REPOSITORY))


def load(name, relative):
    specification = importlib.util.spec_from_file_location(name, OWN / 'fork' / relative)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


history_module = load('organism_v6.orch_r124_train_history', 'organism_v6/orch_r124_train_history.py')
stream_module = load('organism_v6.orch_r125_continual_stream', 'organism_v6/orch_r125_continual_stream.py')
driver_module = load('gpu.orch_r184_think_act_learn', 'gpu/orch_r184_think_act_learn.py')


def event(identifier, text, actor='parent', **overrides):
    arguments = dict(event_id=identifier, text=text, actor=actor, split='TRAIN', phase='experience',
        episode_id='synthetic', source_id='synthetic:' + identifier,
        source_sha256=stream_module.digest([identifier, text]), origin='TRAIN_COLLECTION')
    arguments.update(overrides)
    return history_module.TrainEvent(**arguments)


def token_count(messages):
    return sum(len(message['content'].split()) + 4 for message in messages)


class Journal:
    def __init__(self):
        self.records = []

    def record(self, kind, document):
        self.records.append((kind, copy.deepcopy(document)))
        return dict(index=len(self.records), sha256=stream_module.digest([kind, document]))


class Child:
    count_tokens = staticmethod(token_count)

    def generate(self, messages, **options):
        return dict(raw='Actual synthetic artifact.', token_ids=[1, 2], terminal=True, truncated=False)


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.history = history_module.TrainHistory(system_prompt='System.', birth_prompt='Birth.')
        self.stream = stream_module.ContinualStream(self.history, context_limit=4096,
            segment_tokens=128, segments_per_sleep=3, deadline_unix=time.time() + 600,
            model_state_sha256='f' * 64)
        self.journal = Journal()
        self.child = Child()
        self.current = event('parent:current', 'Keep seventeen fixed. Verify by a second method.')
        self.stale = event('parent:old', 'Unrelated old reading prompt.')

    def seed_compacted(self):
        self.history.append(self.stale)
        self.history.append(event('child:prior', 'Earlier child summary.', actor='child'))
        self.history.append(self.current)
        summary = event('summary', 'Earlier child summary.', actor='child', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())

    def render(self, retained=None, budget=4096):
        return self.history.render(token_count, budget, retained_parent_event_id=retained)

    def driver(self):
        config = dict(schema=driver_module.SCHEMA, trial_id='synthetic', reflection_policy='explicit',
            think_segments=1, cpu_gate_root='/synthetic/not_dispatched', cpu_gate_sha256='e' * 64,
            stage_boundary_policy=driver_module.STAGE_BOUNDARY_POLICY)
        return driver_module.ThinkActLearn(self.child, self.stream, self.journal, config)

    def test_baseline_loses_current_parent_after_compaction(self):
        self.seed_compacted()
        self.assertNotIn(self.current.text, str(self.render().messages))

    def test_retains_exact_current_source_not_stale_prompt(self):
        self.seed_compacted()
        rendered = self.render(self.current.event_id)
        messages = [message for message in rendered.messages if self.current.text in message['content']]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        metadata = json.loads(messages[0]['content'].split('\n', 2)[1])
        self.assertEqual(metadata['source_sha256'], self.current.source_sha256)
        self.assertEqual(metadata['source_id'], self.current.source_id)
        self.assertEqual(metadata['actor'], 'parent')
        self.assertNotIn(self.stale.text, str(rendered.messages))
        self.assertTrue(all(label == -100 for label in rendered.labels))

    def test_render_does_not_mutate_or_permanently_pin_history(self):
        self.seed_compacted()
        before = self.history.checkpoint()
        self.render(self.current.event_id)
        self.assertEqual(before, self.history.checkpoint())
        self.assertNotIn(self.current.text, str(self.render().messages))

    def test_visible_parent_not_duplicated(self):
        self.history.append(self.current)
        self.assertEqual(str(self.render(self.current.event_id).messages).count(self.current.text), 1)

    def test_existing_human_pin_not_duplicated_or_removed(self):
        self.seed_compacted()
        self.history.pin_parent_event(self.current.event_id)
        self.assertEqual(str(self.render(self.current.event_id).messages).count(self.current.text), 1)
        self.assertIn(self.current.text, str(self.render().messages))

    def test_context_budget_stays_hard(self):
        self.seed_compacted()
        with self.assertRaises(history_module.CompactionRequired):
            self.render(self.current.event_id, budget=1)

    def test_cannot_retain_unknown_or_child_as_parent(self):
        self.seed_compacted()
        for identifier in ('missing', 'child:prior'):
            with self.subTest(identifier=identifier), self.assertRaisesRegex(ValueError, 'existing_parent_input'):
                self.render(identifier)

    def test_sealed_or_unattributed_event_still_rejected(self):
        for changes in ({'split': 'FINAL'}, {'origin': 'READOUT'}, {'source_sha256': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                event('forbidden', 'Not admitted.', **changes)

    def test_default_render_and_checkpoint_restore_unchanged(self):
        self.seed_compacted()
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(restored.render(token_count, 4096), self.render())
        self.assertEqual(restored.render(token_count, 4096, retained_parent_event_id=self.current.event_id),
            self.render(self.current.event_id))

    def test_driver_latest_fresh_parent_only_and_no_historical_resurrection(self):
        self.history.append(self.stale)
        driver = self.driver()
        self.assertIsNone(driver._retain_stage_parent('THINK', [self.stale]))
        self.assertEqual(driver._retain_stage_parent('THINK', [self.current]), self.current.event_id)
        self.history.append(self.current)
        self.assertEqual(driver._retain_stage_parent('THINK', []), self.current.event_id)
        self.assertEqual(driver._retain_stage_parent('ACT', []), self.current.event_id)
        newer = event('parent:new', 'New current correction.')
        self.assertEqual(driver._retain_stage_parent('ACT', [newer]), newer.event_id)
        self.assertIsNone(driver._retain_stage_parent('LEARN', []))
        self.assertIsNone(driver._retain_stage_parent('THINK', [self.current]))

    def test_console_input_does_not_replace_active_task_parent(self):
        driver = self.driver()
        driver._retain_stage_parent('THINK', [self.current])
        console = event('human:console', 'Rohin: Direct question.')
        self.assertEqual(driver._retain_stage_parent('ACT', [console], console_events=[console]),
            self.current.event_id)

    def test_parent_must_have_been_rendered_not_merely_archived(self):
        self.seed_compacted()
        driver = self.driver()
        driver._remember_rendered_parent(self.render().messages)
        self.assertIsNone(driver._active_parent_event_id)
        driver._remember_rendered_parent(self.render(self.current.event_id).messages)
        self.assertEqual(driver._active_parent_event_id, self.current.event_id)
        driver._remember_rendered_parent([dict(role='assistant', content=self.current.text)])
        self.assertIsNone(driver._active_parent_event_id)

    def test_unattributed_copy_does_not_select_an_archived_parent_source(self):
        self.seed_compacted()
        driver = self.driver()
        driver._remember_rendered_parent([dict(role='user', content=self.current.text)])
        self.assertIsNone(driver._active_parent_event_id)

    def test_plain_presentation_keeps_exact_source_with_no_archived_duplicate(self):
        from organism_v6.orch_r125_plain_context import VERSION
        self.seed_compacted()
        current = event('parent:visible', self.current.text)
        self.history.append(current)
        self.stream.presentation = dict(version=VERSION, system_prompt='System.', birth_prompt='Birth.')
        driver = self.driver()
        rendered = self.history.render(token_count, 4096, presentation=self.stream.presentation)
        driver._remember_rendered_parent(rendered.messages)
        self.assertEqual(driver._active_parent_event_id, current.event_id)
        summary = event('summary:next', 'Summary.', actor='child', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())
        rendered = self.history.render(token_count, 4096, presentation=self.stream.presentation,
            retained_parent_event_id=current.event_id)
        driver._remember_rendered_parent(rendered.messages)
        self.assertEqual(driver._active_parent_event_id, current.event_id)
        self.assertTrue(all(label == -100 for label in rendered.labels))
        self.assertEqual(str(rendered.messages).count(current.text), 1)

    def test_preexisting_visible_parent_survives_current_think_act(self):
        self.history.append(self.current)
        driver = self.driver()
        driver._generate_stage('THINK', incoming=[])
        self.assertEqual(driver._active_parent_event_id, self.current.event_id)
        summary = event('summary', 'Child distillation.', actor='child', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())
        driver._generate_stage('THINK', incoming=[])
        driver._generate_stage('ACT', incoming=[])
        requests = [document for kind, document in self.journal.records if kind == 'REQUEST']
        self.assertEqual(len(requests), 3)
        self.assertTrue(all(self.current.text in str(request['messages']) for request in requests))

    def test_integrated_think_compaction_act_retains_and_masks_parent(self):
        driver = self.driver()
        driver._generate_stage('THINK', incoming=[self.current])
        summary = event('summary', 'I considered a method.', actor='child', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())
        for index in range(15):
            self.history.append(event('pressure:' + str(index), 'old words ' * 140, actor='child'))
        driver._generate_stage('ACT', incoming=[])
        request = [document for kind, document in self.journal.records if kind == 'REQUEST'][-1]
        self.assertIn(self.current.text, str(request['messages']))
        self.assertEqual(request['retained_parent_input']['source_sha256'], self.current.source_sha256)
        self.assertTrue(request['render_receipt']['all_history_tokens_masked'])
        self.assertLess(request['prompt_tokens'], 3072)
        self.assertLessEqual(request['prompt_tokens'] + request['max_new_tokens'], 4096)
        self.assertTrue(any(kind == 'COMPACTION' for kind, document in self.journal.records))
        for row in self.stream.rows:
            self.assertFalse(row['prefix_loss'])
            self.assertNotIn(self.current.text, row['target'])

    def test_oversized_retained_parent_fails_before_generation(self):
        large = event('parent:large', 'exact words ' * 1000)
        self.history.append(large)
        self.history.append(event('child:prior', 'Small summary.', actor='child'))
        summary = event('summary', 'Small summary.', actor='child', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())
        with self.assertRaises(history_module.CompactionRequired):
            self.stream.step(self.child.generate, token_count, self.journal.record,
                compaction_threshold=400, retained_parent_event_id=large.event_id)
        self.assertFalse(any(kind == 'REQUEST' for kind, document in self.journal.records))
        self.assertEqual(self.stream.rows, [])
        self.assertIn(large, self.history.events)


if __name__ == '__main__':
    unittest.main(verbosity=2)
