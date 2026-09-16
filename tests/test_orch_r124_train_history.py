"""Synthetic CPU tests only: no model, runtime imports or held data."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from organism_v6 import orch_r124_train_history as history_module


def event(identifier, actor='child', text=None, episode='E0', phase='experience', **changes):
    values = dict(event_id=identifier, actor=actor, text=identifier if text is None else text,
                  split='TRAIN', phase=phase, episode_id=episode, source_id='source/' + identifier,
                  source_sha256=hashlib.sha256(identifier.encode()).hexdigest(), origin='TRAIN_COLLECTION')
    values.update(changes)
    return history_module.TrainEvent(**values)


def count_tokens(messages):
    return sum(len(message['content']) + 1 for message in messages)


def resign(document):
    payload = {key: value for key, value in document.items() if key != 'state_sha256'}
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)
    document['state_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    return document


class TrainHistoryTest(unittest.TestCase):
    def setUp(self):
        self.history = history_module.TrainHistory(system_prompt='PINNED SYSTEM', birth_prompt='PINNED BIRTH')

    def render(self, history=None, budget=100000):
        return (self.history if history is None else history).render(count_tokens, budget)

    def summary(self, identifier='summary', text='I recorded an experience.'):
        return event(identifier, text=text, phase='compaction')

    def test_cross_episode_retention_and_new_episode_after_resume(self):
        first = event('E0_observation', actor='environment')
        reply = event('E0_reply')
        second = event('E1_observation', actor='environment', episode='E1')
        for item in (first, reply, second):
            self.history.append(item)
        rendered = self.render()
        self.assertTrue(rendered.messages[2]['content'].endswith(first.text))
        self.assertTrue(rendered.messages[3]['content'].endswith(reply.text))
        self.assertTrue(rendered.messages[4]['content'].endswith(second.text))
        resumed = history_module.TrainHistory.from_json(self.history.to_json())
        resumed.append(event('E2_observation', actor='environment', episode='E2'))
        self.assertEqual(resumed.events[:3], self.history.events)
        self.assertEqual(self.render(resumed).messages[:5], rendered.messages)

    def test_split_exclusion_including_attached_readout_opens(self):
        for split in ('DEV', 'FINAL', 'PROBE', 'UNKNOWN', 'train'):
            for phase in ('experience', 'open_turn'):
                with self.subTest(split=split, phase=phase), self.assertRaisesRegex(ValueError, 'TRAIN_only'):
                    event('held', split=split, phase=phase)
        self.assertEqual(self.history.events, ())

    def test_train_task_readout_open_requires_collection_origin(self):
        for origin in ('READOUT', 'DEV', 'FINAL', 'PROBE', 'READOUT_OPEN'):
            with self.subTest(origin=origin), self.assertRaisesRegex(ValueError, 'readout_origin'):
                event('open', phase='open_turn', origin=origin)
        for phase in ('readout', 'open_readout', 'dev_open_turn', 'unknown'):
            with self.subTest(phase=phase), self.assertRaisesRegex(ValueError, 'unknown_or_readout_phase'):
                event('open', phase=phase)

    def test_unknown_actor_and_missing_provenance_rejected(self):
        for actor in ('system', 'teacher', 'unknown'):
            with self.subTest(actor=actor), self.assertRaisesRegex(ValueError, 'unknown_actor'):
                event('bad', actor=actor)
        for value in ('', 'x' * 64, '0' * 63):
            with self.subTest(hash=value), self.assertRaisesRegex(ValueError, 'source_sha256|empty_event_field'):
                event('bad', source_sha256=value)
        with self.assertRaises(ValueError):
            event('bad', source_id='')
        with self.assertRaises(ValueError):
            event('bad', text=17)
        with self.assertRaisesRegex(ValueError, 'typed_event_required'):
            self.history.append(asdict(event('untyped')))

    def test_parent_once_only_delivery_survives_resume(self):
        parent = event('parent_request_1', actor='parent', text='Consider the observed result.')
        self.assertTrue(self.history.append(parent))
        self.assertFalse(self.history.append(parent))
        resumed = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertFalse(resumed.append(parent))
        rendered = self.render(resumed)
        self.assertEqual(len(rendered.messages), 3)
        self.assertIn('Parent advice (not an observed fact)', rendered.messages[-1]['content'])
        self.assertEqual(rendered.target_token_ids, ())

    def test_conflicting_duplicate_rejected_without_state_change(self):
        original = event('stable')
        self.history.append(original)
        before = self.history.to_json()
        for changed in (replace(original, text='changed'), replace(original, source_sha256='0' * 64),
                        replace(original, actor='parent'), replace(original, episode_id='E1')):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'conflicting_event_id'):
                self.history.append(changed)
            self.assertEqual(self.history.to_json(), before)

    def test_entire_history_is_masked_never_parent_or_child_targets(self):
        for actor in ('environment', 'parent', 'child'):
            self.history.append(event(actor, actor=actor))
        rendered = self.render()
        self.assertEqual(rendered.token_count, count_tokens(rendered.messages))
        self.assertEqual(rendered.labels, (-100,) * rendered.token_count)
        self.assertEqual(rendered.target_token_ids, ())
        self.assertEqual(rendered.messages[-1]['role'], 'assistant')
        self.assertEqual(rendered.messages[-2]['role'], 'user')
        self.assertFalse(hasattr(rendered, 'target'))
        for split in ('DEV', 'FINAL', 'PROBE'):
            with self.subTest(split=split), self.assertRaisesRegex(ValueError, 'history_forbidden_in_readout'):
                self.history.render(count_tokens, 100000, split=split)

    def test_compaction_keeps_raw_and_events_appended_while_child_summarizes(self):
        self.history.append(event('old', text='OLD-RAW-' * 500))
        consumed = self.history.frontier()
        self.history.append(event('recent', episode='E1', text='RECENT UNCONSUMED'))
        raw_before = self.history.events
        summary = self.summary()
        self.assertTrue(self.history.compact(summary, through=consumed))
        self.history.append(event('new', episode='E2', text='NEW AFTER COMPACTION'))
        self.assertEqual(self.history.events[:2], raw_before)
        self.assertEqual(self.history.visible_frontier, consumed)
        rendered = self.render()
        self.assertEqual(len(rendered.messages), 5)
        self.assertNotIn('OLD-RAW-', json.dumps(rendered.messages))
        self.assertIn(history_module.ASSERTION, rendered.messages[2]['content'])
        self.assertIn(consumed.sha256, rendered.messages[2]['content'])
        self.assertTrue(rendered.messages[3]['content'].endswith('RECENT UNCONSUMED'))
        self.assertTrue(rendered.messages[4]['content'].endswith('NEW AFTER COMPACTION'))
        self.assertEqual(rendered.target_token_ids, ())

    def test_compaction_json_file_and_resume_identical(self):
        self.history.append(event('first'))
        self.history.compact(self.summary(), through=self.history.frontier())
        self.history.append(event('next', episode='E1'))
        state = self.history.checkpoint()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.json'
            path.write_text(self.history.to_json())
            resumed = history_module.TrainHistory.from_json(path.read_text(), expected_sha256=state['state_sha256'])
        self.assertEqual(resumed.checkpoint(), state)
        self.assertEqual(resumed.to_json(), self.history.to_json())
        self.assertEqual(self.render(resumed), self.render())
        self.assertFalse(resumed.compact(self.summary(), through=resumed.frontier(1)))
        self.assertEqual(resumed.checkpoint(), state)

    def test_only_explicit_nonempty_child_summary(self):
        self.history.append(event('raw'))
        frontier = self.history.frontier()
        for summary in (event('parent_summary', actor='parent', phase='compaction'),
                        event('environment_summary', actor='environment', phase='compaction'),
                        event('not_summary'), self.summary(text='')):
            with self.subTest(summary=summary), self.assertRaises(ValueError):
                self.history.compact(summary, through=frontier)
        self.assertEqual(self.history.operations, ())
        self.assertTrue(self.history.compact(event('reflection', phase='reflection'), through=frontier))

    def test_empty_compaction_and_conflicting_summary_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty_compaction_frontier'):
            self.history.compact(self.summary(), through=self.history.frontier())
        raw = event('raw', phase='reflection')
        self.history.append(raw)
        with self.assertRaisesRegex(ValueError, 'raw_event_id'):
            self.history.compact(raw, through=self.history.frontier())
        self.history.compact(self.summary(), through=self.history.frontier())
        with self.assertRaisesRegex(ValueError, 'conflicting_event_id'):
            self.history.compact(self.summary(text='different'), through=self.history.frontier())
        self.history.append(event('next'))
        with self.assertRaisesRegex(ValueError, 'conflicting_summary_frontier'):
            self.history.compact(self.summary(), through=self.history.frontier())

    def test_compaction_frontier_regression_and_same_frontier_recompaction(self):
        self.history.append(event('first'))
        earlier = self.history.frontier()
        self.history.append(event('second'))
        self.history.compact(self.summary('long'), through=self.history.frontier())
        before = self.history.to_json()
        with self.assertRaisesRegex(ValueError, 'frontier_regression'):
            self.history.compact(self.summary('stale'), through=earlier)
        self.assertEqual(self.history.to_json(), before)
        self.history.compact(self.summary('short', 'Short.'), through=self.history.frontier())
        self.assertEqual(len(self.history.operations), 2)
        resumed = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(self.render(resumed), self.render())

    def test_bad_frontier_hash_and_count_fail_without_mutation(self):
        self.history.append(event('raw'))
        before = self.history.to_json()
        for frontier in (history_module.Frontier(1, '0' * 64), history_module.Frontier(2, '0' * 64)):
            with self.subTest(frontier=frontier), self.assertRaises(ValueError):
                self.history.compact(self.summary(), through=frontier)
            self.assertEqual(self.history.to_json(), before)
        for value in (-1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.history.frontier(value)

    def test_strict_overflow_never_mutates_or_truncates(self):
        self.history.append(event('long', text='LONG ' * 1000))
        before = self.history.to_json()
        required = self.render().token_count
        with self.assertRaises(history_module.CompactionRequired) as failure:
            self.render(budget=required - 1)
        self.assertEqual(failure.exception.token_count, required)
        self.assertEqual(self.history.to_json(), before)
        self.assertEqual(self.render(budget=required).token_count, required)
        self.history.compact(self.summary(), through=self.history.frontier())
        self.assertLess(self.render(budget=required - 1).token_count, required)

    def test_token_counter_and_budget_validation(self):
        for value in (True, -1, 1.5, '10'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'invalid_token_count'):
                self.history.render(lambda messages: value, 100)
        for budget in (True, -1, 1.5):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                self.history.render(count_tokens, budget)
        with self.assertRaises(ValueError):
            self.history.render(None, 100)

    def test_immutable_raw_and_detached_outputs(self):
        raw = event('raw')
        self.history.append(raw)
        with self.assertRaises(FrozenInstanceError):
            raw.text = 'changed'
        with self.assertRaises(AttributeError):
            self.history.events.append(raw)
        checkpoint = self.history.checkpoint()
        checkpoint['events'][0]['text'] = 'changed'
        rendered = self.render()
        rendered.messages[0]['content'] = 'changed'
        def mutating_counter(messages):
            messages[0]['content'] = 'changed'
            return 10
        self.assertEqual(self.history.render(mutating_counter, 10).messages[0]['content'], 'PINNED SYSTEM')
        self.assertEqual(self.history.events[0], event('raw'))

    def test_checkpoint_tampering_and_external_hash_binding(self):
        self.history.append(event('raw'))
        state = self.history.checkpoint()
        for field in ('birth_prompt', 'system_prompt'):
            changed = deepcopy(state)
            changed[field] = 'tampered'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'checkpoint_integrity'):
                history_module.TrainHistory.restore(changed)
        changed = deepcopy(state)
        changed['events'][0]['text'] = 'tampered'
        with self.assertRaisesRegex(ValueError, 'checkpoint_integrity'):
            history_module.TrainHistory.restore(changed)
        with self.assertRaisesRegex(ValueError, 'checkpoint_external_binding'):
            history_module.TrainHistory.restore(state, expected_sha256='0' * 64)

    def test_resigned_frontier_and_compaction_receipt_tampering(self):
        self.history.append(event('first'))
        self.history.compact(self.summary(), through=self.history.frontier())
        self.history.append(event('second'))
        state = self.history.checkpoint()
        for field in ('at', 'before', 'through'):
            changed = deepcopy(state)
            changed['operations'][0][field]['sha256'] = '0' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                history_module.TrainHistory.restore(resign(changed))
        changed = deepcopy(state)
        changed['frontier']['event_count'] = 1
        with self.assertRaisesRegex(ValueError, 'checkpoint_frontier'):
            history_module.TrainHistory.restore(resign(changed))
        changed = deepcopy(state)
        changed['operations'][0]['summary_status'] = 'VERIFIED_FACT'
        with self.assertRaisesRegex(ValueError, 'operation_integrity'):
            history_module.TrainHistory.restore(resign(changed))

    def test_restore_rejects_duplicate_events_operations_and_nontrain_events(self):
        self.history.append(event('raw'))
        self.history.compact(self.summary(), through=self.history.frontier())
        state = self.history.checkpoint()
        duplicate = deepcopy(state)
        duplicate['events'].append(duplicate['events'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate_checkpoint_event'):
            history_module.TrainHistory.restore(resign(duplicate))
        duplicate = deepcopy(state)
        duplicate['operations'].append(duplicate['operations'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate_compaction_receipt'):
            history_module.TrainHistory.restore(resign(duplicate))
        for split in ('DEV', 'FINAL', 'PROBE'):
            changed = deepcopy(state)
            changed['events'][0]['split'] = split
            with self.subTest(split=split), self.assertRaisesRegex(ValueError, 'TRAIN_only'):
                history_module.TrainHistory.restore(resign(changed))

    def test_json_duplicate_keys_nonfinite_and_unknown_schema_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_JSON_key'):
            history_module.TrainHistory.from_json('{"schema":1,"schema":2}')
        with self.assertRaisesRegex(ValueError, 'nonfinite_JSON_constant'):
            history_module.TrainHistory.from_json('{"schema":NaN}')
        state = self.history.checkpoint()
        state['schema'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'checkpoint_schema'):
            history_module.TrainHistory.restore(resign(state))

    def test_explicit_eviction_has_durable_ids_frontiers_and_pinned_prompts(self):
        oldest = event('oldest', text='OLD RAW ' * 1000)
        self.history.append(oldest)
        frontier = self.history.frontier()
        self.history.append(event('recent', text='KEEP RECENT', episode='E1'))
        before = self.history.to_json()
        with self.assertRaises(history_module.CompactionRequired):
            self.render(budget=2000)
        self.assertEqual(self.history.to_json(), before)
        receipt = self.history.evict_oldest(frontier, reason='Explicit R125 context budget policy')
        self.assertEqual(receipt['dropped_event_ids'], ['oldest'])
        self.assertEqual(receipt['before'], asdict(self.history.frontier(0)))
        self.assertEqual(receipt['through'], asdict(frontier))
        self.assertEqual(receipt['at'], asdict(self.history.frontier()))
        rendered = self.render(budget=2000)
        self.assertEqual([item['content'] for item in rendered.messages[:2]], ['PINNED SYSTEM', 'PINNED BIRTH'])
        self.assertIn('EXPLICIT_OLDEST_HISTORY_EVICTION', rendered.messages[2]['content'])
        self.assertNotIn('OLD RAW', json.dumps(rendered.messages))
        self.assertTrue(rendered.messages[-1]['content'].endswith('KEEP RECENT'))
        self.assertEqual(self.history.events[0], oldest)
        self.assertEqual(rendered.target_token_ids, ())
        self.assertEqual(set(rendered.labels), {-100})
        resumed = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(resumed.checkpoint(), self.history.checkpoint())
        self.assertEqual(self.render(resumed), self.render())
        self.assertEqual(resumed.evict_oldest(frontier, reason=receipt['reason']), receipt)
        self.assertEqual(len(resumed.operations), 1)
        resumed.append(event('after_eviction', episode='E2'))
        self.assertIn('after_eviction', self.render(resumed).messages[-1]['content'])

    def test_eviction_requires_explicit_reason_and_cannot_regress(self):
        self.history.append(event('first'))
        first = self.history.frontier()
        self.history.append(event('second'))
        for reason in ('', ' ', None):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, 'explicit_eviction_reason'):
                self.history.evict_oldest(first, reason=reason)
        self.history.evict_oldest(self.history.frontier(), reason='caller policy')
        with self.assertRaisesRegex(ValueError, 'frontier_regression'):
            self.history.evict_oldest(first, reason='caller policy')
        with self.assertRaises(history_module.CompactionRequired):
            self.render(budget=1)
        self.assertEqual(self.history.checkpoint()['system_prompt'], 'PINNED SYSTEM')
        self.assertEqual(self.history.checkpoint()['birth_prompt'], 'PINNED BIRTH')

    def test_eviction_can_drop_oldest_summary_without_dropping_new_events(self):
        self.history.append(event('old'))
        frontier = self.history.frontier()
        self.history.compact(self.summary(), through=frontier)
        self.history.append(event('new', episode='E1'))
        receipt = self.history.evict_oldest(frontier, reason='explicit summary eviction')
        self.assertEqual(receipt['dropped_event_ids'], [])
        self.assertEqual(receipt['dropped_summary_id'], 'summary')
        self.assertIn('new', self.render().messages[-1]['content'])
        self.assertEqual(self.history.operations[0]['summary']['event_id'], 'summary')
        resumed = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(resumed.checkpoint(), self.history.checkpoint())
        resumed.compact(self.summary('after_eviction'), through=resumed.frontier())
        self.assertEqual(history_module.TrainHistory.from_json(resumed.to_json()).to_json(), resumed.to_json())

    def test_eviction_receipt_tampering_and_duplicate_restore_rejected(self):
        self.history.append(event('old'))
        self.history.evict_oldest(self.history.frontier(), reason='explicit')
        state = self.history.checkpoint()
        for field, value in (('dropped_event_ids', []), ('reason', 'tampered'), ('receipt_sha256', '0' * 64)):
            changed = deepcopy(state)
            changed['operations'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'operation_integrity'):
                history_module.TrainHistory.restore(resign(changed))
        duplicate = deepcopy(state)
        duplicate['operations'].append(duplicate['operations'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate_eviction_receipt'):
            history_module.TrainHistory.restore(resign(duplicate))

    def test_later_compaction_preserves_visible_prior_eviction_notice(self):
        self.history.append(event('old', text='An old observation.'))
        receipt = self.history.evict_oldest(self.history.frontier(), reason='explicit budget policy')
        self.history.append(event('new', text='A newer observation.'))
        self.history.compact(self.summary(text='Only the newer observation is summarized.'),
                             through=self.history.frontier())
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        text = json.dumps(self.render(restored).messages)
        self.assertIn('History omission notice', text)
        self.assertIn(receipt['receipt_sha256'], text)
        self.assertIn('Only the newer observation is summarized.', text)


if __name__ == '__main__':
    unittest.main()
