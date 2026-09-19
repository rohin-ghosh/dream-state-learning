"""Regression checks for publisher restoration without touching native execution."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import parent_service as service
import remote_io
import verify_following_act
import report
import register_supervisor


def record(index, kind, document):
    return dict(index=index, sha256=str(index) * 8, kind=kind, document=document)


def example():
    publication = dict(id='fresh', sha256='inbox-sha')
    delivery = dict(receipt=dict(publication=publication, provider_response_sha256='provider-sha'),
                    text='Concrete task.', parent_process=dict(pid=123, start_ticks='456'))
    state = dict(events=[dict(cycle=10)], deliveries=[delivery], native=dict(pid=493500),
                 request=None, response=None, committed=None, act_stage=None)
    records = [
        record(11, 'INBOX', dict(message=dict(id='fresh', text='Concrete task.'), source_sha256='inbox-sha')),
        record(12, 'REQUEST', dict(messages=[dict(role='user', content='Astra: Concrete task.')],
                                   parent_provenance=[dict(event_id='parent:inbox:fresh', source_sha256='inbox-sha')],
                                   pending_sha256='pending-sha', started_unix=100, segment=22)),
        record(13, 'RESPONSE', dict(request_sha256='pending-sha', finished_unix=110,
                                    response=dict(raw='Actual child content, including errors.'))),
        record(14, 'COMMITTED', dict(source_sha256='source-sha', segment=22)),
        record(15, 'R184_STAGE', dict(stage='ACT', source_sha256='source-sha', segment=22)),
        record(16, 'R184_ACT', dict(source_sha256='source-sha',
                                    origin=dict(record_index=13, record_sha256='13' * 8))),
    ]
    return state, records


class RecoveryTests(unittest.TestCase):
    def test_canonical_unicode_hash_matches_original(self):
        document = dict(raw='21 - 鸟 - 13')
        expected = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                              allow_nan=False).encode()).hexdigest()
        self.assertEqual(remote_io.digest(document), expected)

    def test_all_authentic_act_content_retained(self):
        original = record(1, 'RESPONSE', dict(request_sha256='pending', finished_unix=1,
                                               response=dict(raw='incorrect 鸟 21 - 13 = 12')))
        self.assertEqual(remote_io.project(original)['document']['response']['raw'],
                         original['document']['response']['raw'])

    def test_nonparent_documents_not_exposed(self):
        self.assertNotIn('document', remote_io.project(record(1, 'SEALED_SCORE', dict(score=123))))
        self.assertNotIn('document', remote_io.project(record(2, 'SLEEP_COMPLETE', dict(secret='not parent input'))))

    def test_exact_inbox_request_act_receipt(self):
        state, records = example()
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            service.consume(state, records, Path(temporary))
            receipt = service.read(Path(temporary) / 'DELIVERY_fresh.json')
        self.assertEqual(receipt['inbox']['index'], 11)
        self.assertEqual(receipt['first_render']['index'], 12)
        self.assertEqual(receipt['act']['event']['index'], 16)
        self.assertFalse(receipt['causal_improvement_claim'])
        self.assertEqual(state['events'][-1]['response']['document']['response']['raw'],
                         'Actual child content, including errors.')

    def test_publication_alone_is_not_delivery(self):
        state, records = example()
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            service.consume(state, records[:1], Path(temporary))
            self.assertFalse(list(Path(temporary).glob('DELIVERY_*.json')))

    def test_request_without_matching_source_is_not_rendered(self):
        state, records = example()
        records[1]['document']['parent_provenance'][0]['source_sha256'] = 'wrong'
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            service.consume(state, records, Path(temporary))
            self.assertFalse(list(Path(temporary).glob('DELIVERY_*.json')))

    def test_wrong_response_pending_rejected(self):
        state, records = example()
        records[2]['document']['request_sha256'] = 'other'
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            with self.assertRaisesRegex(ValueError, 'ACT_response_request_binding'):
                service.consume(state, records, Path(temporary))

    def test_wrong_act_origin_rejected(self):
        state, records = example()
        records[-1]['document']['origin']['record_sha256'] = 'other'
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            with self.assertRaisesRegex(ValueError, 'ACT_origin_binding'):
                service.consume(state, records, Path(temporary))

    def test_partial_batch_keeps_exact_act_binding(self):
        state, records = example()
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            service.consume(state, records[:4], Path(temporary))
            state = json.loads(json.dumps(state))
            service.consume(state, records[4:], Path(temporary))
            self.assertTrue((Path(temporary) / 'DELIVERY_fresh.json').exists())

    def test_seed_reuses_old_evidence_without_opening_replay(self):
        for arm in ('learner', 'frozen'):
            state = service.seed(arm)
            self.assertEqual(state['next_index'], state['events'][-1]['stage_record']['index'] + 1)
            self.assertTrue(state['first_turn'])
            self.assertEqual(state['deliveries'], [])
            self.assertEqual(state['stage'], 0)

    def test_curriculum_spacing_unchanged(self):
        state = dict(first_turn=False, stage=3, last_parent_cycle=4,
                     events=[dict(cycle=5, response=dict(document=dict(response=dict(raw='result'))))])
        self.assertFalse(service.turn_due(state))
        state['events'][-1]['cycle'] = 6
        self.assertTrue(service.turn_due(state))
        state['stage'] = 5
        self.assertFalse(service.turn_due(state))

    def test_binding_failure_is_not_retried_as_transport(self):
        self.assertTrue(issubclass(service.BindingError, RuntimeError))
        self.assertEqual(service.read_error('{"fatal":"ValueError","reason":"native_identity_changed"}'),
                         'ValueError:native_identity_changed')

    def test_remote_binding_rejects_pid_reuse(self):
        native = dict(pid=493500, start_ticks='10070880')
        with patch.object(remote_io, 'identity', return_value=(Path('/unused'), native)):
            with self.assertRaisesRegex(ValueError, 'fresh_native_binding_changed'):
                remote_io.execute(dict(arm='learner', action='bind', native=dict(pid=493500, start_ticks='wrong')))

    def test_explicit_429_has_bounded_backoff(self):
        error = urllib.error.HTTPError('provider', 429, 'throttled', {}, None)
        self.assertTrue(service.provider_failure(error, 0)['retry_permitted'])
        self.assertEqual([service.provider_failure(error, previous)['retry_seconds'] for previous in range(4)],
                         [1, 2, 4, 8])
        self.assertFalse(service.provider_failure(error, 4)['retry_permitted'])

    def test_timeout_never_implicitly_redispatches(self):
        self.assertFalse(service.provider_failure(TimeoutError(), 0)['retry_permitted'])
        self.assertFalse(service.provider_failure(ValueError('invalid result'), 0)['retry_permitted'])
        error = urllib.error.HTTPError('provider', 503, 'unknown', {}, None)
        self.assertFalse(service.provider_failure(error, 0)['retry_permitted'])

    def test_incomplete_provider_attempt_blocks_resume(self):
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            root = Path(temporary)
            turn = root / 'turn_1'
            turn.mkdir()
            service.write(turn / 'DISPATCH.json', dict(attempts=1))
            self.assertEqual(service.unresolved_provider_attempts(root), [str(turn)])
            service.write(turn / 'http_error_response.txt', dict(error=dict(code='429')))
            self.assertEqual(service.unresolved_provider_attempts(root), [])

    def test_read_only_transport_stops_after_five_truthful_errors(self):
        with tempfile.TemporaryDirectory(dir=service.HERE) as temporary:
            root = Path(temporary)
            responses = [dict(native=dict(pid=493500, start_ticks='10070880'))] + [TimeoutError()] * 5
            with patch.object(service, 'HERE', root), patch.object(service, 'sha', return_value='source'), \
                    patch.object(service, 'source_parent'), patch.object(service.time, 'sleep'), \
                    patch('builtins.print'), \
                    patch.dict(os.environ, {'NVIDIA_API_KEY': 'test-not-a-credential'}), \
                    patch.object(service, 'remote', side_effect=responses) as transport:
                service.run('learner')
            directory = root / 'private/learner'
            status = service.read(directory / 'STATUS.json')
            self.assertEqual(status['health'], 'BLOCKED_TRANSPORT')
            self.assertEqual(status['failures'], 5)
            self.assertEqual(len(list(directory.glob('ERROR_*.json'))), 5)
            self.assertEqual(transport.call_count, 6)
            self.assertTrue(service.read(directory / 'STATE.json')['transport_blocked'])

    def test_following_act_distinguishes_compaction_from_direct_render(self):
        state, records = example()
        delivery = state['deliveries'][0]
        delivery['inbox'] = service.ref(records[0])
        first_request = deepcopy(records[1])
        first_request['index'] = 11.5
        records[1]['document']['messages'] = [dict(role='user', content='ACT after compaction')]
        proof = verify_following_act.verify([first_request] + records[1:], delivery, state['native'])
        self.assertTrue(proof['initial_request_exact_text_and_source_bound'])
        self.assertFalse(proof['ACT_request_contains_parent_text'])
        self.assertFalse(proof['retention_claim'])
        self.assertEqual(proof['act']['event']['index'], 16)

    def test_following_act_never_substitutes_publication_for_render(self):
        state, records = example()
        delivery = state['deliveries'][0]
        delivery['inbox'] = service.ref(records[0])
        records[1]['document']['messages'] = []
        with self.assertRaisesRegex(ValueError, 'following_ACT_not_yet_observed'):
            verify_following_act.verify(records[1:], delivery, state['native'])

    def test_following_act_rejects_wrong_origin(self):
        state, records = example()
        delivery = state['deliveries'][0]
        delivery['inbox'] = service.ref(records[0])
        records[-1]['document']['origin']['record_index'] = 999
        with self.assertRaisesRegex(ValueError, 'following_ACT_origin_binding'):
            verify_following_act.verify(records[1:], delivery, state['native'])

    def test_public_summary_separates_current_parent_author_and_exposure(self):
        process = dict(pid=345405, start_ticks='792480', boot_id='boot', started_utc='now',
                       argv=['python3', 'parent_service.py'], lock='PUBLISHER.lock')
        publication = dict(id='first', queued_utc='before', inbox=dict(index=3619),
                           rendered_request=dict(index=3629), act=dict(response=dict(index=3639)),
                           ACT_request_contains_parent_text=False, model='same-model',
                           provider_response_sha256='provider', proof='receipt.json', proof_sha256='proof',
                           publication_author_process=dict(pid=326039, start_ticks='754385'),
                           publication_author_is_current_parent=False)
        summary = report.public_summary(dict(arm='frozen', process_receipt=process, publications=[publication],
            parent_alive_bound=True, publisher_lock_held=True, native=dict(pid=471737),
            counts=dict(following_ACT=1, ACT_prompt_exposed=0)), 'now')
        self.assertEqual(summary['restoration_status'], 'RESTORED_FOLLOWING_ACT_PROVEN')
        self.assertTrue(summary['following_ACT_proven'])
        self.assertFalse(summary['ACT_prompt_exposure'])
        self.assertEqual(summary['current_live_parent']['pid'], 345405)
        self.assertEqual(summary['publication_author_process']['pid'], 326039)

    def test_registration_never_shortens_requested_lease_for_supervisor_cap(self):
        requested = dict(name='pair-curriculum-frozen', enabled=True, until_unix=1790791200)
        def reject(entry):
            raise ValueError('finite_existing_fleet_horizon_required')
        registered, reason = register_supervisor.registration_entry(requested, reject)
        self.assertEqual(registered['until_unix'], 1790791200)
        self.assertFalse(registered['enabled'])
        self.assertTrue(registered['requested_enabled'])
        self.assertEqual(reason, 'finite_existing_fleet_horizon_required')

    def test_registration_does_not_hide_other_validation_errors(self):
        def reject(entry):
            raise ValueError('source_digest_changed_requires_owner_update')
        with self.assertRaisesRegex(ValueError, 'source_digest_changed_requires_owner_update'):
            register_supervisor.registration_entry(dict(enabled=True), reject)

    def test_enable_keeps_exact_existing_service_and_horizon(self):
        requested = service.read(service.HERE / 'supervisor_entries/pair-curriculum-frozen.json')
        previous = dict(requested, enabled=False,
                        registration_status='OWNER_REGISTERED_PENDING_SUPERVISOR_HORIZON')
        self.assertTrue(register_supervisor.permitted_enable(previous, requested))
        changed = deepcopy(requested)
        changed['until_unix'] += 1
        self.assertFalse(register_supervisor.permitted_enable(previous, changed))
        changed = deepcopy(requested)
        changed['argv'][-1] = 'learner'
        self.assertFalse(register_supervisor.permitted_enable(previous, changed))

    def test_future_rebind_contract_is_inert_and_not_an_activation(self):
        contract = service.read(service.HERE / 'PARENT_REBIND_CONTRACT.json')
        self.assertFalse(contract['activation_enabled'])
        self.assertFalse(contract['actual_rebind_performed'])
        self.assertFalse(contract['delivery_fence_applied_now'])
        self.assertIsNone(contract['parent_dependency_receipt'])
        self.assertEqual(contract['pre_handoff_dependency_schema'], 'PAIR_RETENTION_PARENT_DEPENDENCIES_V1')
        self.assertFalse(contract['mandatory_invariants']['automatic_pid_adoption'])
        self.assertTrue(contract['mandatory_invariants']['pre_handoff_dependency_proof_required_and_rechecked_after_LOADED'])
        self.assertIsNone(contract['new_native_identity'])
        self.assertIsNone(contract['receiver_loaded_receipt'])
        self.assertIsNone(contract['activation_transaction_id'])
        self.assertTrue(contract['current_runtime_must_keep_rejecting_changed_natives'])
        self.assertEqual(contract['absolute_parent_deadline_unix'], 1790791200)

    def test_future_contract_preserves_ledger_and_current_native_bindings(self):
        contract = service.read(service.HERE / 'PARENT_REBIND_CONTRACT.json')
        for field in ('deliveries', 'stage', 'next_index', 'previous_sha256', 'pending_turn',
                      'provider_inflight', 'provider_blocked', 'publication_blocked', 'first_turn'):
            self.assertIn(field, contract['preserve_parent_state'])
        self.assertEqual(remote_io.TARGETS['learner'][1:3], (493500, '10070880'))
        self.assertEqual(remote_io.TARGETS['frozen'][1:3], (471737, '9987073'))
        for arm in ('learner', 'frozen'):
            manifest = service.read(service.HERE / 'supervisor_entries' / ('pair-curriculum-' + arm + '.json'))
            self.assertEqual(manifest['entrypoint_sha256'], service.sha(service.HERE / 'parent_service.py'))


if __name__ == '__main__':
    unittest.main()
