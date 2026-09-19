"""Synthetic CPU tests only: no model, runtime imports or held data."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_incremental_frontiers_match_canonical_hash_for_every_prefix(self):
        events = [event('entry-' + str(index), text=text) for index, text in enumerate(
            ('plain', '引号：３', '"quoted" \\ slashed\nnew line', '\x00\t', ''))]
        for item in events:
            self.history.append(item)
            for count in range(len(self.history.events) + 1):
                expected = history_module._digest([asdict(value) for value in self.history.events[:count]])
                self.assertEqual(self.history.frontier(count), history_module.Frontier(count, expected))
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        restored.append(event('after-restore', text='後に append'))
        for count in range(len(restored.events) + 1):
            expected = history_module._digest([asdict(value) for value in restored.events[:count]])
            self.assertEqual(restored.frontier(count), history_module.Frontier(count, expected))

    def test_frontier_reads_do_not_reserialize_immutable_events(self):
        self.history.append(event('first'))
        expected = self.history.frontier()
        with patch.object(history_module, 'asdict', side_effect=AssertionError('event reserialization')):
            for unused in range(30):
                self.assertEqual(self.history.frontier(), expected)
                self.assertEqual(self.history.frontier(0).event_count, 0)

    def test_failed_or_duplicate_appends_preserve_frontier_cache(self):
        first = event('first')
        self.history.append(first)
        before = self.history.to_json()
        self.assertFalse(self.history.append(first))
        with self.assertRaisesRegex(ValueError, 'conflicting_event_id'):
            self.history.append(event('first', text='different'))
        with self.assertRaisesRegex(ValueError, 'typed_event_required'):
            self.history.append(asdict(first))
        self.assertEqual(self.history.to_json(), before)
        self.history.append(event('second'))
        expected = history_module._digest([asdict(value) for value in self.history.events])
        self.assertEqual(self.history.frontier().sha256, expected)

    def test_deepcopy_retains_independent_incremental_frontier(self):
        self.history.append(event('first'))
        duplicate = deepcopy(self.history)
        self.assertEqual(duplicate.to_json(), self.history.to_json())
        self.history.append(event('original-only'))
        duplicate.append(event('copy-only'))
        for current in (self.history, duplicate):
            expected = history_module._digest([asdict(value) for value in current.events])
            self.assertEqual(current.frontier().sha256, expected)
        self.assertNotEqual(duplicate.frontier(), self.history.frontier())

    def test_optimized_restore_matches_uncached_operations_and_checkpoint_bytes(self):
        class UncachedHistory(history_module.TrainHistory):
            def frontier(self, event_count=None):
                count = len(self.events) if event_count is None else event_count
                return history_module.Frontier(count,
                    history_module._digest([asdict(value) for value in self.events[:count]]))

        original = UncachedHistory(system_prompt='PINNED SYSTEM', birth_prompt='PINNED BIRTH')
        for index in range(24):
            original.append(event('raw-' + str(index), text='中文 "quoted" ' + str(index)))
            original.compact(self.summary('summary-' + str(index)), through=original.frontier())
            if index % 3 == 0:
                original.evict_oldest(original.frontier(), reason='explicit threshold')
        expected = original.to_json()
        restored = history_module.TrainHistory.from_json(expected)
        self.assertEqual(restored.to_json(), expected)
        self.assertEqual(restored.operations, original.operations)
        for current in (original, restored):
            current.append(event('next'))
            current.compact(self.summary('next-summary'), through=current.frontier())
        self.assertEqual(restored.to_json(), original.to_json())

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

    def test_pinned_parent_is_verbatim_masked_once_across_compaction_eviction_and_restore(self):
        message = event('human', actor='parent', text='Rohin: Keep this exact\nsource_sha256 wording, ３ and spaces. ')
        self.history.append(message)
        self.history.append(event('answer'))
        self.assertTrue(self.history.pin_parent_event('human'))
        self.assertFalse(self.history.pin_parent_event('human'))
        self.history.compact(self.summary(), through=self.history.frontier())
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        for current in (self.history, restored):
            rendered = self.render(current)
            self.assertEqual(sum(item['content'] == message.text for item in rendered.messages), 1)
            self.assertEqual(rendered.messages[2], dict(role='user', content=message.text))
            self.assertTrue(all(label == -100 for label in rendered.labels))
            current.evict_oldest(through=current.frontier(), reason='synthetic pressure')
            self.assertIn(message.text, [item['content'] for item in self.render(current).messages])

    def test_child_cannot_be_pinned_and_pins_cannot_be_silently_truncated(self):
        self.history.append(event('child'))
        with self.assertRaisesRegex(ValueError, 'only_existing_parent_input_can_be_pinned'):
            self.history.pin_parent_event('child')
        self.history.append(event('large', actor='parent', text='Rohin: ' + 'vital ' * 100))
        self.history.pin_parent_event('large')
        self.history.compact(self.summary(), through=self.history.frontier())
        with self.assertRaises(history_module.CompactionRequired):
            self.render(budget=100)

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


class WorkingStateTest(unittest.TestCase):
    def setUp(self):
        self.history = history_module.TrainHistory(system_prompt='System.', birth_prompt='Birth.')

    def add_state(self, identifier, text, *, entry_id='work', kind='note'):
        source = event(identifier, text=text)
        span = history_module.WorkingStateSpan(entry_id, kind, 0, len(text))
        self.history.append(source)
        self.assertTrue(self.history.update_working_state(source, entries=[span]))
        return source, span

    def test_literal_span_derives_text_and_stable_source_fields(self):
        text = '  Café\nI have no result yet.\t '
        source = event('own', text='prefix\n' + text + '\nsuffix')
        self.history.append(source)
        span = history_module.WorkingStateSpan('unfinished', 'uncertainty', 7, 7 + len(text))
        events, operations, frontier = self.history.events, self.history.operations, self.history.frontier()
        self.assertTrue(self.history.update_working_state(source, entries=[span]))
        self.assertEqual(self.history.working_state, dict(schema=history_module.WORKING_STATE_SCHEMA,
            revision=1, entries=[dict(id='unfinished', kind='uncertainty', text=text, start=7,
                end=7 + len(text), source_event_id=source.event_id, source_id=source.source_id,
                source_sha256=source.source_sha256)]))
        self.assertEqual((self.history.events, self.history.operations, self.history.frontier()),
                         (events, operations, frontier))
        rendered = self.history.render(count_tokens, 100000)
        self.assertTrue(rendered.messages[2]['content'].endswith(text))
        self.assertEqual(rendered.messages[2]['role'], 'assistant')

    def test_json_escapes_are_literal_not_decoded_or_normalized(self):
        source = event('json', text=r'{"state_delta":{"text":"line one\nline two\u0021"}}')
        text = r'line one\nline two\u0021'
        start = source.text.index(text)
        self.history.append(source)
        self.history.update_working_state(source, entries=[
            history_module.WorkingStateSpan('literal', 'note', start, start + len(text))])
        self.assertEqual(self.history.working_state['entries'][0]['text'], text)
        self.assertNotEqual(self.history.working_state['entries'][0]['text'], 'line one\nline two!')

    def test_only_actual_appended_child_source_not_forged_or_summary(self):
        span = history_module.WorkingStateSpan('work', 'finding', 0, 1)
        for actor in ('parent', 'environment'):
            source = event(actor, actor=actor)
            self.history.append(source)
            before = self.history.to_json()
            with self.subTest(actor=actor), self.assertRaisesRegex(ValueError, 'own_child_state_source'):
                self.history.update_working_state(source, entries=[span])
            self.assertEqual(self.history.to_json(), before)
        source = event('own', text='Actual child text.')
        with self.assertRaisesRegex(ValueError, 'source_identity'):
            self.history.update_working_state(source, entries=[span])
        self.history.append(source)
        for field, value in (('source_id', 'forged'), ('source_sha256', '0' * 64),
                             ('text', 'invented'), ('event_id', 'invented')):
            before = self.history.to_json()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'source_identity'):
                self.history.update_working_state(replace(source, **{field: value}), entries=[span])
            self.assertEqual(self.history.to_json(), before)
        summary = event('summary', phase='compaction')
        self.history.compact(summary, through=self.history.frontier())
        with self.assertRaisesRegex(ValueError, 'committed_raw_source'):
            self.history.update_working_state(summary, entries=[span])

    def test_typed_fields_and_finite_character_bounds(self):
        invalid = [(True, 2), (0, False), (-1, 1), (1, 1), (2, 1), (0.0, 2),
                   (0, float('inf')), (0, float('nan')), (0, '2')]
        for start, end in invalid:
            with self.subTest(start=start, end=end), self.assertRaisesRegex(ValueError, 'source_span'):
                history_module.WorkingStateSpan('work', 'note', start, end)
        for identifier, kind in (('', 'note'), (None, 'note'), ('work', 'verified_fact'), ('work', None)):
            with self.subTest(identifier=identifier, kind=kind), self.assertRaises(ValueError):
                history_module.WorkingStateSpan(identifier, kind, 0, 1)
        source = event('own', text='  text')
        self.history.append(source)
        for entries in ([dict(id='untyped', kind='note', start=0, end=3)],
                        [history_module.WorkingStateSpan('past-end', 'note', 0, 7)],
                        [history_module.WorkingStateSpan('blank', 'note', 0, 2)]):
            before = self.history.to_json()
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                self.history.update_working_state(source, entries=entries)
            self.assertEqual(self.history.to_json(), before)
        for kind in sorted(history_module.WORKING_STATE_KINDS):
            self.assertEqual(history_module.WorkingStateSpan('id', kind, 0, 1).kind, kind)

    def test_r184_kinds_persist_as_child_spans_without_visible_stage_tokens(self):
        for kind in ('investigation', 'judgment', 'expected_consequence', 'process_adjustment'):
            with self.subTest(kind=kind):
                history = history_module.TrainHistory(system_prompt='System.', birth_prompt='Birth.')
                source = event(kind, text='An actual child-authored statement.')
                history.append(source)
                history.update_working_state(source, entries=[
                    history_module.WorkingStateSpan('work', kind, 0, len(source.text))])
                restored = history_module.TrainHistory.from_json(history.to_json())
                self.assertEqual(restored.working_state['entries'][0]['kind'], kind)
                presentation = dict(version='R125_PLAIN_CONTEXT_V1', system_prompt='System.', birth_prompt='Birth.')
                rendered = restored.render(count_tokens, 100000, presentation=presentation)
                self.assertEqual(rendered.messages[2]['content'], source.text)
                self.assertEqual(rendered.labels, (-100,) * rendered.token_count)

    def test_accumulation_revision_and_only_explicit_deletion(self):
        original, _ = self.add_state('first', 'First unfinished work.', entry_id='first')
        self.add_state('second', 'Another open question.', entry_id='second', kind='open_question')
        self.assertEqual([entry['id'] for entry in self.history.working_state['entries']], ['first', 'second'])
        self.add_state('revision', 'I will try a smaller input.', entry_id='first', kind='next_intention')
        entries = self.history.working_state['entries']
        self.assertEqual(entries[0]['source_event_id'], 'revision')
        self.assertEqual(entries[1]['source_event_id'], 'second')
        source = event('delete-first', text='Remove first from my working state.')
        self.history.append(source)
        self.assertTrue(self.history.update_working_state(source, delete=['first']))
        self.assertEqual([entry['id'] for entry in self.history.working_state['entries']], ['second'])
        final = event('delete-second', text='Remove second as well.')
        self.history.append(final)
        self.history.update_working_state(final, delete=['second'])
        self.assertEqual(self.history.working_state['entries'], [])
        self.assertEqual(self.history.working_state['revision'], 5)
        self.assertEqual(self.history.events[0], original)
        self.assertEqual(self.history.operations, ())
        self.assertEqual(len(self.history.working_state_updates), 5)
        self.assertFalse(any(message['content'].startswith('Child working state')
                             for message in self.history.render(count_tokens, 100000).messages))
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(restored.to_json(), self.history.to_json())
        self.assertFalse(restored.update_working_state(final, delete=['second']))

    def test_exact_retry_cannot_resurrect_and_source_rebinding_fails(self):
        older = event('older', text='Earlier unused statement.')
        self.history.append(older)
        source, span = self.add_state('first', 'My unfinished work.')
        with self.assertRaisesRegex(ValueError, 'conflicting_working_state_source'):
            self.history.update_working_state(source, entries=[replace(span, end=1)])
        with self.assertRaisesRegex(ValueError, 'stale_working_state_source'):
            self.history.update_working_state(older, entries=[replace(span, end=1)])
        alias = event('alias', text=source.text, source_id=source.source_id)
        self.history.append(alias)
        with self.assertRaisesRegex(ValueError, 'conflicting_working_state_source'):
            self.history.update_working_state(alias, entries=[span])
        deletion = event('delete', text='Remove work.')
        self.history.append(deletion)
        self.history.update_working_state(deletion, delete=['work'])
        before = self.history.to_json()
        self.assertFalse(self.history.update_working_state(source, entries=[span]))
        self.assertEqual(self.history.to_json(), before)
        self.assertEqual(self.history.working_state['entries'], [])

    def test_invalid_delta_is_atomic_and_does_not_delete_other_entries(self):
        self.add_state('first', 'Preserve this unfinished work.')
        source = event('next', text='The next child statement.')
        self.history.append(source)
        span = history_module.WorkingStateSpan('work', 'note', 0, len(source.text))
        for entries, delete in (([span, span], []), ([], ['work', 'work']), ([span], ['work']),
                                ([span], ['missing']), ([], 'work'), ([], [None]), ([], [])):
            before = self.history.to_json()
            with self.subTest(entries=entries, delete=delete), self.assertRaises(ValueError):
                self.history.update_working_state(source, entries=entries, delete=delete)
            self.assertEqual(self.history.to_json(), before)

    def test_compaction_eviction_and_checkpoint_preserve_active_state_verbatim(self):
        first, _ = self.add_state('first', '  First unfinished work.\n', entry_id='first')
        self.history.compact(event('summary', text='I considered the work.', phase='compaction'),
                             through=self.history.frontier())
        second, _ = self.add_state('second', 'Second unfinished work.', entry_id='second')
        expected = self.history.working_state
        self.history.evict_oldest(self.history.frontier(), reason='explicit context threshold')
        self.assertEqual(self.history.working_state, expected)
        self.assertEqual(self.history.events, (first, second))
        self.add_state('third', 'A new intention.', entry_id='second', kind='next_intention')
        checkpoint = self.history.checkpoint()
        restored = history_module.TrainHistory.restore(checkpoint, expected_sha256=checkpoint['state_sha256'])
        self.assertEqual(restored.to_json(), self.history.to_json())
        self.assertEqual(restored.events, self.history.events)
        self.assertEqual(restored.operations, self.history.operations)
        self.assertEqual(restored.working_state_updates, self.history.working_state_updates)
        restored.compact(event('again', text='I still have work.', phase='compaction'),
                         through=restored.frontier())
        restored.evict_oldest(restored.frontier(), reason='drop summary only')
        message = restored.render(count_tokens, 100000).messages[2]['content']
        for entry in self.history.working_state['entries']:
            self.assertIn(entry['text'], message)
        self.assertEqual(restored.working_state, self.history.working_state)

    def test_all_state_tokens_masked_plain_presentation_retains_literal_text(self):
        text = 'My own note: I have not obtained a result yet.'
        self.add_state('first', text)
        presentation = dict(version='R125_PLAIN_CONTEXT_V1', system_prompt='Plain system.', birth_prompt='Plain birth.')
        for style in (None, presentation):
            rendered = self.history.render(count_tokens, 100000, presentation=style)
            self.assertTrue(rendered.messages[2]['content'].endswith(text))
            self.assertEqual(rendered.token_count, count_tokens(rendered.messages))
            self.assertEqual(rendered.labels, (-100,) * rendered.token_count)
            self.assertEqual(rendered.target_token_ids, ())
        for split in ('DEV', 'FINAL', 'PROBE'):
            with self.subTest(split=split), self.assertRaisesRegex(ValueError, 'forbidden_in_readout'):
                self.history.render(count_tokens, 100000, split=split)
        before = self.history.to_json()
        required = self.history.render(count_tokens, 100000).token_count
        with self.assertRaises(history_module.CompactionRequired):
            self.history.render(count_tokens, required - 1)
        self.assertEqual(self.history.to_json(), before)

    def test_plain_state_has_no_injected_provenance_and_survives_eligible_rows(self):
        from organism_v6.orch_r125_plain_context import eligible_rows
        self.add_state('first', '  I need to test the boundary.\n', entry_id='boundary')
        self.add_state('second', 'I have no result yet.', entry_id='result', kind='uncertainty')
        self.history.compact(event('summary', text='I still have work.', phase='compaction'),
                             through=self.history.frontier())
        presentation = dict(version='R125_PLAIN_CONTEXT_V1', system_prompt='Plain system.', birth_prompt='Plain birth.')
        rendered = self.history.render(count_tokens, 100000, presentation=presentation)
        expected = '\n\n'.join(entry['text'] for entry in self.history.working_state['entries'])
        self.assertEqual(rendered.messages[2], dict(role='assistant', content=expected))
        for marker in ('source_sha256', 'receipt_sha256', 'TRAIN_COLLECTION', 'source_event_id',
                       'THINK_ACT_STATE_V1', 'CHILD_ASSERTION_NOT_VERIFIED_FACT'):
            self.assertFalse(any(marker in message['content'] for message in rendered.messages), marker)
        row = dict(prefix=rendered.messages, target='I will run the boundary test next.', source_sha256='a' * 64)
        accepted, excluded = eligible_rows([row], presentation)
        self.assertEqual(excluded, [])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]['prefix'][2], dict(role='assistant', content=expected))
        self.assertEqual(rendered.labels, (-100,) * rendered.token_count)
        restored = history_module.TrainHistory.from_json(self.history.to_json())
        self.assertEqual(restored.render(count_tokens, 100000, presentation=presentation), rendered)

    def test_state_byte_boundary_includes_metadata_and_never_truncates(self):
        self.add_state('boundary', 'x' * 1000)
        message = self.history.render(count_tokens, 100000).messages[2]['content']
        capacity = 1000 + history_module.WORKING_STATE_BYTE_BUDGET - len(message.encode('utf-8'))
        self.assertTrue(1000 <= capacity < 10000)
        for size in (capacity, capacity + 1):
            fresh = history_module.TrainHistory(system_prompt='System.', birth_prompt='Birth.')
            source = event('boundary', text='x' * size)
            fresh.append(source)
            span = history_module.WorkingStateSpan('work', 'note', 0, size)
            before = fresh.to_json()
            if size == capacity:
                self.assertTrue(fresh.update_working_state(source, entries=[span]))
                self.assertEqual(len(fresh.render(count_tokens, 100000).messages[2]['content'].encode('utf-8')),
                                 history_module.WORKING_STATE_BYTE_BUDGET)
                self.assertEqual(history_module.TrainHistory.from_json(fresh.to_json()).to_json(), fresh.to_json())
            else:
                with self.assertRaises(history_module.WorkingStateOverflow) as failure:
                    fresh.update_working_state(source, entries=[span])
                self.assertEqual(failure.exception.byte_count, history_module.WORKING_STATE_BYTE_BUDGET + 1)
                self.assertEqual(fresh.to_json(), before)
        source = event('unicode', text='é' * 1800)
        self.history.append(source)
        before = self.history.to_json()
        with self.assertRaises(history_module.WorkingStateOverflow):
            self.history.update_working_state(source, entries=[history_module.WorkingStateSpan('work', 'note', 0, 1800)])
        self.assertEqual(self.history.to_json(), before)

    def test_cumulative_overflow_requires_explicit_removal(self):
        self.add_state('first', 'x' * 800)
        source = event('second', text='y' * 800)
        self.history.append(source)
        span = history_module.WorkingStateSpan('second', 'prediction', 0, 800)
        before = self.history.to_json()
        with self.assertRaises(history_module.WorkingStateOverflow):
            self.history.update_working_state(source, entries=[span])
        self.assertEqual(self.history.to_json(), before)
        self.assertTrue(self.history.update_working_state(source, entries=[span], delete=['work']))
        self.assertEqual([entry['id'] for entry in self.history.working_state['entries']], ['second'])
        self.assertEqual(self.history.events[0].text, 'x' * 800)

    def test_detached_state_receipts_and_frozen_spans(self):
        source, span = self.add_state('first', 'My unfinished work.')
        with self.assertRaises(FrozenInstanceError):
            span.start = 1
        before = self.history.to_json()
        active = self.history.working_state
        active['entries'][0]['text'] = 'invented'
        updates = self.history.working_state_updates
        updates[0]['entries'][0]['start'] = 99
        self.history.checkpoint()['working_state']['entries'].clear()
        rendered = self.history.render(count_tokens, 100000)
        rendered.messages[2]['content'] = 'invented'
        self.assertEqual(self.history.to_json(), before)
        self.assertEqual(self.history.events[0], source)

    def test_resigned_checkpoint_cannot_fake_state_or_source_mapping(self):
        self.add_state('first', 'Actual child statement.')
        checkpoint = self.history.checkpoint()
        mutations = [
            ('entries', 'text', 'invented'), ('entries', 'source_event_id', 'missing'),
            ('entries', 'source_id', 'invented'), ('entries', 'source_sha256', '0' * 64),
            ('entries', 'start', True), ('entries', 'end', 999),
            ('updates', 'source_event_id', 'missing'), ('updates', 'source_id', 'invented'),
            ('updates', 'source_sha256', '0' * 64), ('updates', 'revision', True),
            ('updates', 'receipt_sha256', '0' * 64), ('updates', 'delete', ['missing'])]
        for section, field, value in mutations:
            changed = deepcopy(checkpoint)
            changed['working_state'][section][0][field] = value
            with self.subTest(section=section, field=field), self.assertRaises(ValueError):
                history_module.TrainHistory.restore(resign(changed))
        for field, value in (('schema', 'unknown'), ('revision', True), ('revision', 2),
                             ('rendered_byte_budget', 99999), ('updates', [])):
            changed = deepcopy(checkpoint)
            changed['working_state'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                history_module.TrainHistory.restore(resign(changed))
        changed = deepcopy(checkpoint)
        changed['working_state']['updates'].append(deepcopy(changed['working_state']['updates'][0]))
        with self.assertRaisesRegex(ValueError, 'update_integrity'):
            history_module.TrainHistory.restore(resign(changed))
        changed = deepcopy(checkpoint)
        changed['working_state']['updates'][0]['at'] = asdict(self.history.frontier(0))
        with self.assertRaisesRegex(ValueError, 'committed_raw_source'):
            history_module.TrainHistory.restore(resign(changed))
        for value in (True, 0.0, 999):
            changed = deepcopy(checkpoint)
            changed['working_state']['updates'][0]['entries'][0]['end'] = value
            with self.subTest(end=value), self.assertRaises(ValueError):
                history_module.TrainHistory.restore(resign(changed))

    def test_unused_state_preserves_legacy_checkpoint_bytes(self):
        for stage in ('empty', 'appended', 'compacted', 'evicted'):
            if stage == 'appended':
                self.history.append(event('first', text='Original history.'))
            elif stage == 'compacted':
                self.history.compact(event('summary', phase='compaction'), through=self.history.frontier())
            elif stage == 'evicted':
                self.history.evict_oldest(self.history.frontier(), reason='explicit')
            legacy = dict(schema='R124_TRAIN_HISTORY_V1', system_prompt='System.', birth_prompt='Birth.',
                          events=[asdict(item) for item in self.history.events],
                          operations=list(self.history.operations), frontier=asdict(self.history.frontier()))
            expected = json.dumps(resign(legacy), sort_keys=True, separators=(',', ':'), allow_nan=False)
            self.assertEqual(self.history.working_state['entries'], [])
            self.assertEqual(self.history.working_state_updates, ())
            self.assertNotIn('working_state', self.history.checkpoint())
            self.assertEqual(self.history.to_json(), expected, stage)
            self.assertEqual(history_module.TrainHistory.from_json(expected).to_json(), expected, stage)

    def test_state_follows_birth_without_displacing_raw_turns_or_latest_runtime_status(self):
        from organism_v6.orch_r125_plain_context import eligible_rows
        presentation = dict(version='R125_PLAIN_CONTEXT_V1', system_prompt='System.', birth_prompt='Birth.')
        for style in (None, presentation):
            with self.subTest(plain=style is not None):
                history = history_module.TrainHistory(system_prompt='System.', birth_prompt='Birth.')
                source = event('own', text='I will test the smallest input.')
                runtime = event('runtime', actor='environment', text='ACT: execute your chosen test now.')
                history.append(source)
                history.append(runtime)
                before = history.render(count_tokens, 100000, presentation=style).messages
                history.update_working_state(source, entries=[
                    history_module.WorkingStateSpan('next', 'next_intention', 0, len(source.text))])
                rendered = history.render(count_tokens, 100000, presentation=style)
                self.assertEqual(rendered.messages[:2], before[:2])
                self.assertEqual(rendered.messages[3:], before[2:])
                self.assertTrue(rendered.messages[2]['content'].endswith(source.text))
                self.assertEqual(rendered.messages[-1], before[-1])
                self.assertEqual(rendered.messages[-1]['role'], 'user')
                self.assertEqual(history.events, (source, runtime))
                self.assertEqual(rendered.labels, (-100,) * rendered.token_count)
                restored = history_module.TrainHistory.from_json(history.to_json())
                self.assertEqual(restored.render(count_tokens, 100000, presentation=style), rendered)
                if style is not None:
                    row = dict(prefix=rendered.messages, target='I am running that test.', source_sha256='a' * 64)
                    accepted, excluded = eligible_rows([row], style)
                    self.assertEqual(excluded, [])
                    self.assertEqual(accepted[0]['prefix'][2], dict(role='assistant', content=source.text))
                    self.assertEqual(accepted[0]['prefix'][-1], dict(role='user', content=runtime.text))


if __name__ == '__main__':
    unittest.main()
