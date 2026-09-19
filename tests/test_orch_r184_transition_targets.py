from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import unittest

from gpu.orch_r184_transition_targets import (
    DependencySpan, MASK, TargetSpan, ViewSelection, build_views, presentation_schedule,
)
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory


class Tokenizer:
    eos_token_id = 0
    all_special_ids = [0, 1, 2, 3]

    def apply_chat_template(self, messages, **kwargs):
        tokens = []
        for message in messages:
            tokens.extend([{'system': 1, 'user': 2, 'assistant': 3}[message['role']]])
            tokens.extend(map(ord, message['content']))
            tokens.extend([0, 10])
        return tokens + [3]

    def decode(self, tokens, **kwargs):
        return ''.join(chr(token) for token in tokens)


def fixture(count=2):
    history = TrainHistory(system_prompt='Pinned runtime instructions', birth_prompt='Birth')
    messages = [dict(role='system', content='Pinned runtime instructions')]
    rows = []
    for index in range(count):
        text = 'Actual parent question ' + str(index)
        event = TrainEvent('parent:' + str(index), 'parent', text, 'TRAIN', 'experience', 'episode',
                           'inbox:' + str(index), hashlib.sha256(text.encode()).hexdigest(), 'TRAIN_COLLECTION')
        history.append(event)
        messages.append(dict(role='user', content=text))
        text = 'I checked the object. READY: try step ' + str(index)
        source = hashlib.sha256(text.encode()).hexdigest()
        event = TrainEvent('child:' + str(index), 'child', text, 'TRAIN', 'experience', 'episode',
                           'response:' + str(index), source, 'TRAIN_COLLECTION')
        rows.append(dict(split='TRAIN', actor='child', event_id=event.event_id, source_sha256=source,
                         prefix_loss=False, target_loss=True, prefix=deepcopy(messages), target=text,
                         token_ids=list(map(ord, text)) + [0], terminal=True))
        history.append(event)
        messages.append(dict(role='assistant', content=text))
        text = 'Runtime cost/environment observation ' + str(index)
        history.append(TrainEvent('cost:' + str(index), 'environment', text, 'TRAIN', 'feedback', 'episode',
                                 'cost:' + str(index), hashlib.sha256(text.encode()).hexdigest(), 'TRAIN_COLLECTION'))
        messages.append(dict(role='user', content=text))
    return rows, history


def dependency(rows, history, event_id='parent:0'):
    event = next(event for event in history.events if event.event_id == event_id)
    prefix = Tokenizer().apply_chat_template(rows[0]['prefix'])
    text = Tokenizer().decode(prefix)
    start = text.index(event.text)
    return DependencySpan(event_id, start, start + len(event.text))


def selected(row, start=0, stop=None, kind='transition', dependencies=()):
    return ViewSelection(kind, (TargetSpan(row['source_sha256'], start,
                         len(row['token_ids']) - 1 if stop is None else stop),), dependencies)


class TransitionTargetTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.history = fixture()
        self.tokenizer = Tokenizer()

    def build(self, selections, **kwargs):
        return build_views(kwargs.get('rows', self.rows), kwargs.get('history', self.history),
                           selections, self.tokenizer, kwargs.get('context_limit', 10000))

    def episode(self, rows=None):
        rows = self.rows if rows is None else rows
        return ViewSelection('complete_episode', tuple(TargetSpan(row['source_sha256'], 0,
                    len(row['token_ids']) - 1) for row in rows), (dependency(rows, self.history),))

    def test_transition_preserves_child_READY_and_masks_required_prefix(self):
        row = self.rows[0]
        span = dependency(self.rows, self.history)
        start = row['target'].index('READY')
        view = self.build([selected(row, start, dependencies=(span,))])[0]
        self.assertEqual(self.tokenizer.decode(view.target_ids), row['target'][start:])
        self.assertEqual(view.prefix_start, span.start)
        self.assertIn('Actual parent question 0', self.tokenizer.decode(view.input_ids))
        self.assertIn('I checked the object.', self.tokenizer.decode(view.input_ids))
        first = next(index for index, label in enumerate(view.labels) if label != MASK)
        self.assertTrue(all(label == MASK for label in view.labels[:first]))
        self.assertFalse(set(view.target_ids).intersection(self.tokenizer.all_special_ids))

    def test_completion_is_literal_selection_not_success_inference(self):
        view = self.build([selected(self.rows[0], stop=1, kind='completion')])[0]
        self.assertEqual(view.target_ids, (ord('I'),))
        self.assertEqual(view.labels[0], MASK)
        self.assertEqual(view.history_frontier_sha256, self.history.frontier(2).sha256)

    def test_complete_episode_multiple_actual_children_intervening_context_masked(self):
        view = self.build([self.episode()])[0]
        self.assertEqual(self.tokenizer.decode(view.target_ids), ''.join(row['target'] for row in self.rows))
        full = self.tokenizer.decode(view.input_ids)
        for text in ('Runtime cost/environment observation 0', 'Actual parent question 1'):
            start = full.index(text)
            self.assertEqual(view.labels[start:start + len(text)], (MASK,) * len(text))
        self.assertNotIn('Runtime cost/environment observation 1', full)
        self.assertEqual(view.source_sha256s, tuple(row['source_sha256'] for row in self.rows))

    def test_complete_episode_replaces_individual_exposures_exactly16(self):
        views = self.build([self.episode()])
        schedule = presentation_schedule(views)
        counts = Counter(source for kind, view in schedule for source in view.source_sha256s)
        self.assertEqual(set(kind for kind, view in schedule), {'NEW'})
        self.assertEqual(counts, {row['source_sha256']: 16 for row in self.rows})

    def test_transition_and_completion_cannot_add_duplicate_row_exposures(self):
        for selections in ([selected(self.rows[0]), selected(self.rows[0], kind='completion')],
                           [self.episode(), selected(self.rows[1])]):
            with self.subTest(selections=selections), self.assertRaisesRegex(ValueError, 'row_already_assigned'):
                self.build(selections)
        view = self.build([selected(self.rows[0])])[0]
        with self.assertRaisesRegex(ValueError, 'row_already_assigned'):
            presentation_schedule([view, view])

    def test_multiple_disjoint_spans_in_one_row_share16_exposures(self):
        row = self.rows[0]
        selection = ViewSelection('transition', (TargetSpan(row['source_sha256'], 0, 1),
                                   TargetSpan(row['source_sha256'], 3, 5)), ())
        view = self.build([selection])[0]
        self.assertEqual(view.target_ids, tuple(row['token_ids'][0:1] + row['token_ids'][3:5]))
        self.assertEqual(len(presentation_schedule([view])), 16)

    def test_no_hidden_row_selection_and_no_input_mutation(self):
        before = deepcopy(self.rows), self.history.checkpoint()
        view = self.build([selected(self.rows[1])])[0]
        self.assertEqual(view.source_sha256s, (self.rows[1]['source_sha256'],))
        self.assertEqual((self.rows, self.history.checkpoint()), before)
        self.assertEqual(self.build([]), [])
        self.assertEqual(presentation_schedule([]), [])

    def test_required_dependency_window_never_silently_trimmed(self):
        selection = selected(self.rows[0], dependencies=(dependency(self.rows, self.history),))
        view = self.build([selection])[0]
        self.assertEqual(self.build([selection], context_limit=len(view.input_ids)), [view])
        with self.assertRaisesRegex(ValueError, 'required_window_exceeds_context'):
            self.build([selection], context_limit=len(view.input_ids) - 1)

    def test_all_explicit_dependencies_preserved_in_minimal_contiguous_window(self):
        row = self.rows[1]
        spans = tuple(dependency([row], self.history, event_id)
                      for event_id in ('parent:0', 'cost:0', 'parent:1'))
        view = self.build([selected(row, dependencies=spans)])[0]
        self.assertEqual(view.prefix_start, min(span.start for span in spans))
        prefix_count = len(self.tokenizer.apply_chat_template(row['prefix'])) - view.prefix_start
        self.assertEqual(view.labels[:prefix_count], (MASK,) * prefix_count)
        for span in spans:
            event = next(event for event in self.history.events if event.event_id == span.event_id)
            self.assertIn(event.text, self.tokenizer.decode(view.input_ids))

    def test_declared_dependency_must_be_real_earlier_exact_context(self):
        good = dependency(self.rows, self.history)
        bad = [replace(good, event_id='invented'), replace(good, event_id='parent:1'),
               replace(good, start=good.start + 1), replace(good, stop=100000), replace(good, start=True)]
        for span in bad:
            with self.subTest(span=span), self.assertRaises(ValueError):
                self.build([selected(self.rows[0], dependencies=(span,))])
        with self.assertRaisesRegex(ValueError, 'unique_dependencies'):
            self.build([selected(self.rows[0], dependencies=(good, good))])

    def test_explicit_selection_and_dependency_types_required(self):
        good = selected(self.rows[0])
        for selection in (replace(good, kind='successful'), replace(good, targets=()),
                          replace(good, targets=list(good.targets)), replace(good, dependencies=None)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.build([selection])

    def test_special_tokens_never_targets_even_actual_terminal_EOS(self):
        with self.assertRaisesRegex(ValueError, 'no_special_target_tokens'):
            self.build([selected(self.rows[0], stop=len(self.rows[0]['token_ids']))])
        row = self.rows[0]
        row['token_ids'][0] = 1
        row['target'] = '\x01' + row['target'][1:]
        history = TrainHistory(system_prompt='System', birth_prompt='Birth')
        event = self.history.events[1]
        history.append(replace(event, text=row['target']))
        with self.assertRaisesRegex(ValueError, 'no_special_target_tokens'):
            self.build([selected(row)], history=history)

    def test_source_and_visibility_mismatches_are_fatal(self):
        changes = [dict(split='DEV'), dict(split='FINAL'), dict(actor='parent'), dict(actor='environment'),
                   dict(prefix_loss=True), dict(target_loss=False), dict(target='fabricated outcome'),
                   dict(event_id='parent:0'), dict(source_sha256='f' * 64), dict(terminal='yes'),
                   dict(token_ids=[True]), dict(token_ids=[65]), dict(prefix=[])]
        for changed in changes:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                rows = deepcopy(self.rows)
                rows[0].update(changed)
                self.build([selected(rows[0])], rows=rows)

    def test_unselected_eval_row_is_not_an_allowed_pool_member(self):
        self.rows[1]['split'] = 'DEV'
        with self.assertRaisesRegex(ValueError, 'actual_TRAIN_child_targets_only'):
            self.build([selected(self.rows[0])])

    def test_duplicate_pool_sources_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique_actual_rows'):
            self.build([selected(self.rows[0])], rows=[self.rows[0], self.rows[0]])

    def test_overlapping_reversed_empty_and_noninteger_targets_rejected(self):
        source = self.rows[0]['source_sha256']
        variants = [(TargetSpan(source, 1, 3), TargetSpan(source, 2, 4)),
                    (TargetSpan(source, 5, 6), TargetSpan(source, 0, 1)),
                    (TargetSpan(source, 0, 0),), (TargetSpan(source, False, 3),),
                    (TargetSpan('0' * 64, 0, 1),)]
        for targets in variants:
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                self.build([ViewSelection('transition', targets, ())])

    def test_episode_rejects_evicted_or_rewritten_recorded_prefix(self):
        selection = self.episode()
        self.rows[1]['prefix'][0]['content'] = 'Changed or compacted prompt'
        with self.assertRaisesRegex(ValueError, 'exact_recorded_continuation'):
            self.build([selection])

    def test_complete_episode_cannot_omit_an_intervening_child(self):
        self.rows, self.history = fixture(3)
        with self.assertRaisesRegex(ValueError, 'all_actual_child_rows'):
            self.build([self.episode([self.rows[0], self.rows[2]])])

    def test_complete_episode_requires_full_spans_not_partial_or_singleton(self):
        episode = self.episode()
        for selection in (replace(episode, targets=(replace(episode.targets[0], start=1), episode.targets[1])),
                          self.episode([self.rows[0]]), replace(episode, kind='completion')):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.build([selection])

    def test_complete_episode_cannot_cross_actual_episode_ids(self):
        history = TrainHistory(system_prompt='System', birth_prompt='Birth')
        for event in self.history.events:
            history.append(replace(event, episode_id='different') if event.event_id == 'child:1' else event)
        with self.assertRaisesRegex(ValueError, 'same_actual_episode'):
            self.build([self.episode()], history=history)


if __name__ == '__main__':
    unittest.main()
