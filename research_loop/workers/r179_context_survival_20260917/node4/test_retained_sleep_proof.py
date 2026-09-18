"""Synthetic CPU regressions; these fixtures are not runtime survival receipts."""

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('node4_retained_proof', Path(__file__).with_name('retained_sleep_proof.py'))
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)


def history(events):
    document = dict(events=events, operations=[])
    return dict(document, state_sha256=proof.digest(document))


def envelope(state):
    return dict(state=state, sha256=proof.digest(state))


class RetainedProofTests(unittest.TestCase):
    def setUp(self):
        self.messages = [dict(role='user', content='synthetic retained conditioning')]
        presleep_history = history([dict(event_id='synthetic-before', actor='parent')])
        rows = [dict(source_sha256='synthetic-own-response')]
        before = dict(context_limit=16384, segment_tokens=512, history=presleep_history, rows=rows,
            sleep_frontier=0, sleep_receipts=[], pending='sleep:' + proof.digest(['synthetic-own-response']),
            model_state_sha256='before-model', deadline_unix=1789754400)
        self.retained = dict(schema='R179_CONTEXT_SURVIVES_SLEEP_V1', cycle=41,
            action='RETAIN_CONTEXT_ACROSS_SLEEP', threshold_tokens=12288, visible_prompt_tokens=25,
            context_limit=16384, history_sha256_before=presleep_history['state_sha256'],
            history_sha256_after=presleep_history['state_sha256'], visible_frontier_before=0,
            raw_event_count=1, targets_rewritten=False, optimizer_recipe_changed=False)
        self.requested = dict(cycle=41, resume_state=envelope(before))
        checkpoint = dict(adapter='adapter-bytes', optimizer='optimizer-bytes', rng='optimizer-bytes')
        receipt = dict(cycle=41, status='COMPLETE', optimizer_steps=4,
            new_row_sha256=['synthetic-own-response'], checkpoint_sha256=checkpoint)
        after = deepcopy(before)
        after.update(pending=None, sleep_frontier=1, sleep_receipts=[deepcopy(receipt)], model_state_sha256=proof.digest(checkpoint))
        self.completed = dict(receipt, resume_state=envelope(after))
        post = deepcopy(after)
        self.post_request = dict(messages=self.messages, model_state_sha256=after['model_state_sha256'],
            history_sha256=proof.digest(post['history']), deadline_unix=1789754400, prompt_tokens=25,
            render_receipt=dict(all_history_tokens_masked=True))
        post['pending'] = proof.digest(self.post_request)
        self.post_request['resume_state'] = envelope(post)
        self.response = dict(request_sha256=post['pending'], response=dict(raw='synthetic own answer', token_ids=[7]))
        generated = deepcopy(post)
        generated['pending'] = None
        generated['rows'].append(dict(prefix=self.messages, source_sha256=proof.digest(self.response),
            prefix_loss=False, target_loss=True))
        self.committed = dict(source_sha256=proof.digest(self.response), state=envelope(generated))

    def verify(self, render=None):
        return proof.verify_cycle(self.retained, self.requested, self.completed, self.post_request,
            self.response, self.committed, render or (lambda state, count: self.messages))

    def test_complete_chain_requires_actual_request_response_commit(self):
        receipt = self.verify()
        self.assertEqual(receipt['cycle'], 41)
        self.assertFalse(receipt['retained_learning_claim'])
        self.assertFalse(receipt['tokenizer_independently_recomputed'])
        self.assertEqual(receipt['actual_prompt_messages_sha256'], proof.digest(self.messages))

    def test_corrupted_snapshot_hash_blocks(self):
        self.completed['resume_state']['sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'envelope_hash'):
            self.verify()

    def test_threshold_or_changed_recipe_cannot_claim_retention(self):
        for field, value in (('visible_prompt_tokens', 12288), ('threshold_tokens', 13000),
                             ('targets_rewritten', True), ('history_sha256_after', 'different')):
            with self.subTest(field=field):
                before = deepcopy(self.retained)
                self.retained[field] = value
                with self.assertRaises(ValueError):
                    self.verify()
                self.retained = before

    def test_completed_sleep_must_preserve_history_exactly(self):
        state = self.completed['resume_state']['state']
        state['history'] = history([])
        self.completed['resume_state'] = envelope(state)
        with self.assertRaisesRegex(ValueError, 'preserved_history_rows'):
            self.verify()

    def test_post_sleep_eviction_is_not_full_context_proof(self):
        state = self.post_request['resume_state']['state']
        state['history'] = history([])
        self.post_request['resume_state'] = envelope(state)
        with self.assertRaisesRegex(ValueError, 'retained_context_visible'):
            self.verify()

    def test_response_binding_and_mask_change_block(self):
        self.response['request_sha256'] = 'another-request'
        with self.assertRaisesRegex(ValueError, 'request_response_binding'):
            self.verify()
        self.setUp()
        state = self.committed['state']['state']
        state['rows'][-1]['prefix_loss'] = True
        self.committed['state'] = envelope(state)
        with self.assertRaisesRegex(ValueError, 'loss_masks'):
            self.verify()

    def test_different_render_cannot_claim_actual_prompt(self):
        with self.assertRaisesRegex(ValueError, 'canonical_postsleep_history_render'):
            self.verify(lambda state, count: [])

    def test_same_cycle_and_positive_training_required(self):
        for field, value in (('cycle', 40), ('optimizer_steps', 0), ('status', 'INTERRUPTED')):
            with self.subTest(field=field):
                previous = deepcopy(self.completed)
                self.completed[field] = value
                with self.assertRaises(ValueError):
                    self.verify()
                self.completed = previous

    def test_incomplete_records_wait_instead_of_inventing_proof(self):
        records = [dict(kind=kind, document=document) for kind, document in (
            ('CONTEXT_RETAINED', self.retained), ('SLEEP_REQUEST', self.requested),
            ('SLEEP_COMPLETE', self.completed), ('REQUEST', self.post_request),
            ('RESPONSE', self.response), ('COMMITTED', self.committed))]
        for length in range(len(records)):
            self.assertIsNone(proof.candidate(records[:length]))
        self.assertEqual(proof.candidate(records), tuple(records))

    def test_before_load_reads_no_journal_or_model(self):
        lane = proof.BASE / 'orch_r179_node4_CPU_fixture' / 'lane0'
        actor = dict(pid=123, start_ticks='456')
        request = dict(physical=0, source_root=str(lane / 'source'),
            old_plan=dict(root=str(proof.BASE / proof.LIVES[0] / 'run1')), processes=dict(actor=actor))
        helpers = SimpleNamespace(read=lambda path: request, identity=lambda pid: actor)
        with patch.object(Path, 'exists', return_value=False):
            self.assertEqual(proof.inspect(lane, helpers)['status'], 'WAITING_FOR_ACTUAL_R179_LOAD')

    def test_dead_or_changed_owner_is_not_reported_as_healthy(self):
        expected = dict(pid=123, start_ticks='456')
        self.assertFalse(proof.identity_live(expected, SimpleNamespace(identity=lambda pid: dict(pid=123, start_ticks='457'))))
        with patch.object(Path, 'exists', return_value=False):
            lane = proof.BASE / 'orch_r179_node4_CPU_fixture' / 'lane0'
            request = dict(physical=0, source_root=str(lane / 'source'), processes=dict(actor=expected),
                old_plan=dict(root=str(proof.BASE / proof.LIVES[0] / 'run1')))
            result = proof.inspect(lane, SimpleNamespace(read=lambda path: request, identity=lambda pid: {}))
            self.assertEqual(result['status'], 'ORIGINAL_OWNER_REQUIRES_REVALIDATION_OR_RECOVERY')
            self.assertTrue(result['recovery_or_owner_revalidation_needed'])

    def test_readonly_wall_bounded_monitor_rejects_unbounded_requests(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            for seconds in (-1, 86401, True):
                with self.subTest(seconds=seconds), self.assertRaisesRegex(ValueError, 'bounded_readonly'):
                    proof.watch(Path('/unused'), seconds)

    def test_retired_recovery_loading_is_not_a_dead_child(self):
        lane = proof.BASE / 'orch_r179_node4_CPU_fixture' / 'lane3'
        request = dict(physical=3, source_root=str(lane / 'source'), processes=dict(actor={'pid': 123}),
            old_plan=dict(root=str(proof.BASE / proof.LIVES[3] / 'run1')))
        helpers = SimpleNamespace(read=lambda path: request, identity=lambda pid: {})
        with patch.object(Path, 'exists', lambda path: path.name in ('RETIRED.json', 'DISPATCHED.json')):
            result = proof.inspect(lane, helpers)
        self.assertEqual(result['status'], 'PLANNED_HANDOFF_WAITING_FOR_LOAD')
        self.assertFalse(result['recovery_or_owner_revalidation_needed'])

    def test_proved_postretirement_guard_failure_is_not_an_expired_watcher(self):
        lane = proof.BASE / 'orch_r179_node4_CPU_fixture' / 'lane3'
        request = dict(physical=3, source_root=str(lane / 'source'), processes=dict(actor={'pid': 123}),
            old_plan=dict(root=str(proof.BASE / proof.LIVES[3] / 'run1')))
        helpers = SimpleNamespace(read=lambda path: request if path.name == 'STAGED.json'
            else {'retirement_started': True}, identity=lambda pid: {})
        with patch.object(Path, 'exists', lambda path: path.name == 'RETIREMENT_STARTED.json'), \
             patch.object(Path, 'glob', return_value=[lane / 'ERROR_CPU.json']):
            result = proof.inspect(lane, helpers)
        self.assertTrue(result['recovery_or_owner_revalidation_needed'])

    def test_explicit_pre_native_recovery_failure_is_reported(self):
        lane = proof.BASE / 'orch_r179_node4_CPU_fixture' / 'lane3'
        request = dict(physical=3, source_root=str(lane / 'source'), processes=dict(actor={'pid': 123}),
            old_plan=dict(root=str(proof.BASE / proof.LIVES[3] / 'run1')))
        helpers = SimpleNamespace(read=lambda path: request, identity=lambda pid: {})
        with patch.object(Path, 'exists', lambda path: path.name in ('RETIRED.json', 'RECOVERY_FAILED_BEFORE_NATIVE.json')):
            self.assertTrue(proof.inspect(lane, helpers)['recovery_or_owner_revalidation_needed'])

    def test_other_lives_rejected_before_helper_or_journal_read(self):
        for path in ('/tmp/lane0', '/localhome/local-rohing/unscoped/lane0',
                     '/localhome/local-rohing/orch_r179_node4_CPU_fixture/lane2'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'four_scoped'):
                proof.load_helpers(Path(path))


@unittest.skipUnless(os.environ.get('R179_ACTUAL_SOURCE'), 'receiving-source-only canonical rendering test')
class ActualSourceRenderingTests(unittest.TestCase):
    def test_canonical_render_from_actual_pinned_source_without_model(self):
        source = Path(os.environ['R179_ACTUAL_SOURCE'])
        sys.path.insert(0, str(source))
        from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
        history = TrainHistory(system_prompt='Synthetic CPU purpose', birth_prompt='Synthetic CPU birth')
        history.append(TrainEvent(event_id='synthetic-parent', actor='parent', split='TRAIN', phase='experience',
            episode_id='fixture', source_id='CPU_FIXTURE', source_sha256=proof.digest('synthetic-parent'),
            origin='TRAIN_COLLECTION', text='Synthetic conditioning retained in the prompt.'))
        state = dict(history=history.checkpoint(), context_limit=16384, segment_tokens=512)
        expected = history.render(lambda messages: 25, 15872).messages
        self.assertEqual(proof.canonical_messages(source, state, 25), expected)


if __name__ == '__main__':
    unittest.main()
