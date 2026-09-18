import copy
import unittest

from organism_v6.orch_r124_train_history import CompactionRequired, TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import ContinualStream, digest


def token_count(messages):
    return sum(len(message['content'].split())+4 for message in messages)


def event(event_id, text, actor='parent', split='TRAIN'):
    return TrainEvent(event_id=event_id, text=text, actor=actor, split=split,
        phase='experience', episode_id='test_stream', source_id='test:'+event_id,
        origin='TRAIN_COLLECTION', source_sha256=digest([event_id, text, actor, split]))


class StreamTests(unittest.TestCase):
    def setUp(self):
        self.records = []
        self.prompts = []
        self.stream = ContinualStream(TrainHistory(system_prompt='Standing purpose.',
            birth_prompt='Accurate mechanism context.'),
            context_limit=4096, segment_tokens=128, segments_per_sleep=2, deadline_unix=1000,
            model_state_sha256='f'*64)

    def record(self, kind, value):
        self.records.append((kind, copy.deepcopy(value)))

    def generate(self, messages, *, max_new_tokens, deadline_unix):
        self.prompts.append(copy.deepcopy(messages))
        self.assertEqual(max_new_tokens, 128)
        self.assertEqual(deadline_unix, 1000)
        return dict(raw=f'Child passage {len(self.prompts)}.', token_ids=[10, 11, 2],
                    terminal=True, truncated=False)

    def step(self, **kwargs):
        return self.stream.step(self.generate, token_count, self.record, now=lambda: 100, **kwargs)

    def test_EOS_continues_without_synthetic_child_cue_or_new_request(self):
        self.assertTrue(self.step()['continue_after_EOS'])
        self.assertTrue(self.step()['continue_after_EOS'])
        self.assertIn('Child passage 1.', str(self.prompts[1]))
        self.assertNotIn('Next:', str(self.prompts))
        self.assertEqual(len(self.stream.rows), 2)
        self.assertTrue(self.stream.sleep_due)

    def test_threshold_compaction_precedes_generation_and_preserves_raw_input(self):
        older = [event(f'old:{index}', 'An earlier observation. ' * 35, actor='child')
            for index in range(14)]
        for item in older:
            self.stream.history.append(item)
        incoming = event('human:current', 'Answer this actual new question, not the old task.')
        self.step(incoming=(incoming,), compaction_threshold=400)
        requests = [value for kind, value in self.records if kind == 'REQUEST']
        compactions = [value for kind, value in self.records if kind == 'COMPACTION']
        self.assertEqual(len(requests), 1)
        self.assertLess(requests[0]['prompt_tokens'], 400)
        self.assertEqual(compactions[0]['threshold_tokens'], 400)
        self.assertFalse(compactions[0]['new_child_distillation'])
        self.assertIn('Your visible context was compacted at', str(self.prompts[0]))
        self.assertIn('Omitted passages remain in the raw journal', str(self.prompts[0]))
        self.assertNotIn('Your visible context was compacted at', self.stream.rows[0]['target'])
        self.assertEqual(self.stream.history.events[:len(older)], tuple(older))
        self.assertIn(incoming.text, str(self.prompts[0]))
        self.assertEqual(len(self.stream.rows), 1)
        restored = ContinualStream.restore(self.stream.checkpoint(),
            expected_sha256=self.stream.checkpoint()['sha256'])
        self.assertEqual(restored.checkpoint(), self.stream.checkpoint())

    def test_threshold_reuses_prior_child_distillation_not_later_failed_code(self):
        from dataclasses import replace
        first = event('chosen:child', 'Keep the observed failure separate from a guess.', actor='child')
        self.stream.history.append(first)
        summary = replace(first, event_id='chosen:summary', phase='compaction')
        self.stream.history.compact(summary, through=self.stream.history.frontier(1))
        for index in range(14):
            self.stream.history.append(event(f'old:{index}', 'Later attempted code. ' * 35, actor='child'))
        self.step(compaction_threshold=400)
        compactions = [value for kind, value in self.records if kind == 'COMPACTION']
        self.assertEqual(compactions[-1]['source_sha256'], first.source_sha256)
        self.assertEqual(compactions[-1]['carry_source_kind'], 'PRIOR_CHILD_COMPACTION')
        self.assertIn(first.text, str(self.prompts[-1]))

    def test_threshold_never_silently_drops_oversized_fresh_input(self):
        self.stream.history.append(event('prior:child', 'An earlier conclusion.', actor='child'))
        incoming = event('human:large', 'fresh important words ' * 200)
        with self.assertRaises(CompactionRequired):
            self.step(incoming=(incoming,), compaction_threshold=300)
        self.assertFalse(self.prompts)
        self.assertIn(incoming, self.stream.history.events)
        self.assertTrue(any(kind == 'R203_CONTEXT_BUDGET_BLOCKED' for kind, value in self.records))

    def test_incoming_parent_once_and_costs_are_never_targets(self):
        parent = event('parent:one', 'Look again at your assumption.')
        self.step(incoming=[parent])
        self.step(incoming=[parent])
        self.assertEqual(str(self.prompts[1]).count(parent.text), 1)
        self.assertIn('[cost]', str(self.prompts[1]))
        for row in self.stream.pending_rows():
            self.assertNotIn(parent.text, row['target'])
            self.assertNotIn('[cost]', row['target'])
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
            self.assertFalse(row['append_eos'])
            self.assertEqual(row['token_ids'], [10, 11, 2])

    def test_no_parent_wait_and_empty_inbox_still_generates(self):
        self.step(incoming=[])
        self.assertEqual(len(self.prompts), 1)
        self.assertEqual(self.records[0][0], 'REQUEST')
        self.assertEqual(self.records[0][1]['parent_wait_seconds'], 0)

    def test_readout_and_fake_child_inputs_rejected_before_model_call(self):
        for split in ('DEV', 'FINAL', 'PROBE'):
            with self.assertRaises(ValueError):
                self.step(incoming=[event('readout:'+split, 'hidden readout open', split=split)])
        with self.assertRaisesRegex(ValueError, 'external_input_never_child_authored'):
            self.step(incoming=[event('forged', 'Not actually generated.', actor='child')])
        self.assertEqual(self.prompts, [])

    def test_generation_failure_keeps_reservation_and_never_retries(self):
        def fail(*args, **kwargs):
            raise RuntimeError('model process failed')
        with self.assertRaises(RuntimeError):
            self.stream.step(fail, token_count, self.record, now=lambda: 100)
        checkpoint = self.stream.checkpoint()
        restored = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
        with self.assertRaisesRegex(ValueError, 'unresolved_request_never_redispatched'):
            restored.step(self.generate, token_count, self.record, now=lambda: 100)
        self.assertEqual(self.prompts, [])

    def test_request_receipt_alone_restores_unresolved_frontier(self):
        self.step()
        reservation = self.records[0][1]['resume_state']
        restored = ContinualStream.restore(reservation, expected_sha256=reservation['sha256'])
        with self.assertRaisesRegex(ValueError, 'unresolved_request_never_redispatched'):
            restored.step(self.generate, token_count, self.record, now=lambda: 100)

    def test_commit_log_failure_blocks_further_generation(self):
        def failed_commit(kind, value):
            if kind == 'COMMITTED':
                raise OSError('full evidence disk')
            self.record(kind, value)
        with self.assertRaises(OSError):
            self.stream.step(self.generate, token_count, failed_commit, now=lambda: 100)
        with self.assertRaisesRegex(ValueError, 'unresolved_request_never_redispatched'):
            self.step()

    def test_invalid_raw_is_preserved_before_validation(self):
        def malformed(*args, **kwargs):
            return dict(raw='Saved even though metadata is wrong.', token_ids=[], terminal=True, truncated=False)
        with self.assertRaisesRegex(ValueError, 'actual_bounded_child_tokens'):
            self.stream.step(malformed, token_count, self.record, now=lambda: 100)
        self.assertEqual(self.records[-1][0], 'RESPONSE')
        self.assertIn('Saved even', self.records[-1][1]['response']['raw'])
        self.assertIsNotNone(self.stream.pending)

    def test_cap_is_recorded_without_counting_as_EOS(self):
        def capped(*args, **kwargs):
            return dict(raw='Capped output.', token_ids=[10]*128, terminal=False, truncated=True)
        result = self.stream.step(capped, token_count, self.record, now=lambda: 100)
        self.assertFalse(result['continue_after_EOS'])
        self.assertTrue(self.stream.rows[0]['truncated'])
        self.step()
        self.assertEqual(len(self.stream.rows), 2)

    def test_runtime_wall_blocks_dispatch_not_relabelled_as_EOS(self):
        with self.assertRaisesRegex(ValueError, 'runtime_wall'):
            self.stream.step(self.generate, token_count, self.record, now=lambda: 1000)
        self.assertEqual(self.records, [])
        self.assertEqual(self.prompts, [])

    def test_explicit_eviction_keeps_birth_and_raw_evidence(self):
        self.stream.context_limit = 256
        self.stream.allow_eviction = True
        old = event('old', 'old '*200)
        self.step(incoming=[old])
        self.assertNotIn(old.text, str(self.prompts[0]))
        self.assertIn('Accurate mechanism context.', str(self.prompts[0]))
        self.assertIn('History omission notice', str(self.prompts[0]))
        self.assertEqual(self.stream.history.events[0], old)
        self.assertTrue(self.stream.history.operations)

    def test_strict_history_overflow_does_not_silently_drop_old_input(self):
        self.stream.context_limit = 256
        with self.assertRaises(CompactionRequired):
            self.step(incoming=[event('old', 'old '*200)])
        self.assertEqual(self.prompts, [])
        self.assertEqual(self.stream.history.operations, ())

    def test_explicit_eviction_can_drop_oversized_compaction_with_no_new_events(self):
        self.stream.history.append(event('original', 'An earlier observation.', actor='environment'))
        summary = TrainEvent(event_id='summary', actor='child', text='summary '*200, split='TRAIN',
            phase='compaction', episode_id='test_stream', source_id='test:summary',
            source_sha256='e'*64, origin='TRAIN_COLLECTION')
        self.stream.history.compact(summary, through=self.stream.history.frontier())
        self.stream.context_limit = 256
        self.stream.allow_eviction = True
        self.step()
        self.assertEqual(self.stream.history.operations[-1]['dropped_summary_id'], 'summary')
        self.assertIn('History omission notice', str(self.prompts[0]))

    def test_summary_eviction_preserves_newer_response_when_it_fits(self):
        self.stream.history.append(event('original', 'An earlier observation.', actor='environment'))
        summary = TrainEvent(event_id='summary', actor='child', text='summary '*200, split='TRAIN',
            phase='compaction', episode_id='test_stream', source_id='test:summary',
            source_sha256='e'*64, origin='TRAIN_COLLECTION')
        self.stream.history.compact(summary, through=self.stream.history.frontier())
        self.stream.history.append(event('newer', 'KEEP THE NEW CHILD RESPONSE', actor='child'))
        self.stream.context_limit = 320
        self.stream.allow_eviction = True
        self.step()
        self.assertIn('KEEP THE NEW CHILD RESPONSE', str(self.prompts[0]))
        self.assertEqual(self.stream.history.operations[-1]['dropped_event_ids'], [])

    def test_counter_cannot_mutate_dispatched_pinned_prompts(self):
        def mutating_counter(messages):
            count = token_count(messages)
            messages[0]['content'] = 'Untrusted counter mutation'
            return count
        self.stream.step(self.generate, mutating_counter, self.record, now=lambda: 100)
        self.assertEqual(self.prompts[0][0]['content'], 'Standing purpose.')
        self.assertEqual(self.stream.rows[0]['prefix'][0]['content'], 'Standing purpose.')

    def test_restore_and_sleep_keep_history_and_new_row_frontier(self):
        self.step(incoming=[event('p1', 'An actual parent turn.')])
        self.step()
        receipt = dict(status='COMPLETE', optimizer_steps=16,
            new_row_sha256=[row['source_sha256'] for row in self.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a'*64, optimizer='b'*64, rng='c'*64))
        before_history = self.stream.history.checkpoint()
        checkpoint = self.stream.commit_sleep(receipt, self.record)
        self.assertEqual(self.stream.history.checkpoint(), before_history)
        self.assertEqual(self.stream.pending_rows(), [])
        self.assertFalse(self.stream.sleep_due)
        self.stream = ContinualStream.restore(checkpoint, expected_sha256=checkpoint['sha256'])
        self.step()
        self.assertIn('Child passage 1.', str(self.prompts[-1]))
        self.assertEqual(len(self.stream.pending_rows()), 1)
        self.assertEqual(self.stream.rows[-1]['segment'], 2)
        self.assertEqual(self.stream.rows[-1]['model_state_sha256'], digest(receipt['checkpoint_sha256']))
        self.assertEqual(self.stream.rows[0]['model_state_sha256'], 'f'*64)

    def test_sleep_cannot_admit_wrong_rows_or_missing_optimizer_state(self):
        self.step()
        receipt = dict(status='COMPLETE', optimizer_steps=16,
            new_row_sha256=['d'*64], checkpoint_sha256=dict(adapter='a'*64))
        with self.assertRaisesRegex(ValueError, 'sleep_exact_new_child_frontier'):
            self.stream.commit_sleep(receipt, self.record)
        receipt['new_row_sha256'] = [row['source_sha256'] for row in self.stream.pending_rows()]
        with self.assertRaisesRegex(ValueError, 'full_learning_state_receipt'):
            self.stream.commit_sleep(receipt, self.record)
        self.assertEqual(self.stream.sleep_frontier, 0)

    def test_bound_snapshot_tamper_is_rejected(self):
        self.step()
        checkpoint = self.stream.checkpoint()
        trusted_sha256 = checkpoint['sha256']
        checkpoint['state']['rows'][0]['target'] = 'Changed after generation.'
        checkpoint['sha256'] = digest(checkpoint['state'])
        with self.assertRaisesRegex(ValueError, 'bound_stream_checkpoint'):
            ContinualStream.restore(checkpoint, expected_sha256=trusted_sha256)


if __name__ == '__main__':
    unittest.main()
