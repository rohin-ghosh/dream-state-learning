from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import boundary
from boundary import (Refusal, digest, normalize_source_only_plan, plan_metadata_binding,
    read_boundary, recheck_consumed_wall_receipt, required_plan_metadata_receipts, verify_source_only_plans)
from coordinator import coordinate, validate_prepared, verify_receiver_plan
from test_boundary import JournalFixture, append_record, inputs, intents_for, records_for, selected
from test_coordinator import FakeOperations


def metadata_inputs(*, wall=True, tail=True):
    binding, prepared, authority = inputs()
    original = records_for(binding)
    prior = deepcopy(original[0]['document'])
    prior['resume_state']['state']['deadline_unix'] = 8000
    prior['resume_state']['sha256'] = digest(prior['resume_state']['state'])
    records = []
    append_record(records, binding, 'SLEEP_COMPLETE', prior)
    authorization = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1', previous_deadline_unix=8000,
        previous_stream_sha256=prior['resume_state']['sha256'], new_deadline_unix=10000,
        lease_end_unix=20000, safety_margin_seconds=120)
    consumed = append_record(records, binding, 'WALL_EXTENDED', dict(schema='R131_WALL_EXTENDED_V1',
        authorization=authorization, plan_sha256=digest('historically_admitted_plan'),
        state=deepcopy(original[0]['document']['resume_state'])))
    append_record(records, binding, 'SLEEP_COMPLETE', deepcopy(original[0]['document']))
    append_record(records, binding, 'R184_LEARN_COMPLETE', deepcopy(original[1]['document']))
    candidate = selected(binding, records)
    if wall:
        prepared['old_plan']['authorized_wall_extension'] = authorization
    if tail:
        selection = dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=binding['journal_root'],
            journal_id=binding['journal_id'], complete_index=0, complete_sha256=records[0]['sha256'],
            life_id='same-life', max_tail_records=2048, max_tail_bytes=1024 * 1024**2,
            sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)],
            persist_complete_anchors=True)
        for plan in (prepared['old_plan'], prepared['new_plan']):
            plan['think_act_learn'] = dict(trial_id='same-life', controls='unchanged')
            plan['checkpoint_tail_recovery'] = deepcopy(selection)
        prepared['new_plan']['checkpoint_tail_recovery'].update(complete_index=candidate['complete_index'],
            complete_sha256=candidate['complete_sha256'])
    return binding, prepared, authority, records, candidate, consumed


def receipts_for(binding, prepared, candidate, consumed, *, plan=None):
    plan = prepared['new_plan'] if plan is None else plan
    stamp = plan_metadata_binding(binding, candidate, prepared['old_plan'], plan)
    receipts = {}
    if prepared['old_plan'].get('authorized_wall_extension') is not None:
        receipts['consumed_wall_extension'] = dict(binding=stamp, durable=True, record=deepcopy(consumed),
            intent=intents_for([consumed])[consumed['index']])
    if 'checkpoint_tail_recovery' in plan:
        receipts['checkpoint_tail_recovery'] = dict(binding=stamp, durable=True,
            selection_sha256=digest(plan['checkpoint_tail_recovery']),
            restored_state_sha256=candidate['resume_state']['sha256'], head_index=candidate['head_index'],
            head_sha256=candidate['head_sha256'], pending=None, historical_body_replay=False,
            sidecars_verified=True, inbox_preserved=True, reader_source_pins_sha256=digest(prepared['new_source_pins']),
            cpu_receipt_sha256=digest('bound_receiving_reader_CPU_receipt'))
    return receipts


class MetadataPlanTests(unittest.TestCase):
    def setUp(self):
        (self.binding, self.prepared, self.authority, self.records,
            self.candidate, self.consumed) = metadata_inputs()
        self.receipts = receipts_for(self.binding, self.prepared, self.candidate, self.consumed)

    def verify(self, *, new=None, candidate=None, receipts=None):
        return verify_source_only_plans(self.prepared['old_plan'], self.prepared['new_plan'] if new is None else new,
            binding=self.binding, candidate=self.candidate if candidate is None else candidate,
            receipts=self.receipts if receipts is None else receipts)

    def test_consumed_authorization_and_current_anchor_normalize_without_mutation(self):
        before = deepcopy((self.prepared, self.candidate, self.receipts))
        normalized = normalize_source_only_plan(self.prepared['old_plan'], self.prepared['new_plan'],
            binding=self.binding, candidate=self.candidate, receipts=self.receipts)
        self.assertEqual(normalized, self.prepared['old_plan'])
        self.assertEqual(self.verify(), digest(self.prepared['old_plan']))
        self.assertEqual((self.prepared, self.candidate, self.receipts), before)
        self.assertNotIn('authorized_wall_extension', self.prepared['new_plan'])
        self.assertEqual(self.prepared['new_plan']['checkpoint_tail_recovery']['complete_index'], 2)

    def test_structural_template_preflight_is_not_adoption_permission(self):
        self.assertEqual(required_plan_metadata_receipts(self.prepared['old_plan'], self.prepared['new_plan']),
            ('consumed_wall_extension', 'checkpoint_tail_recovery'))
        validate_prepared(self.binding, self.prepared, self.authority)
        with self.assertRaisesRegex(Refusal, 'required_plan_metadata_receipts'):
            verify_source_only_plans(self.prepared['old_plan'], self.prepared['new_plan'])
        with self.assertRaisesRegex(Refusal, 'candidate_and_life'):
            verify_source_only_plans(self.prepared['old_plan'], self.prepared['new_plan'], receipts=self.receipts)

    def test_wall_removal_or_tail_reanchor_can_be_used_independently(self):
        for wall, tail in ((True, False), (False, True)):
            binding, prepared, _, _, candidate, consumed = metadata_inputs(wall=wall, tail=tail)
            with self.subTest(wall=wall, tail=tail):
                verify_source_only_plans(prepared['old_plan'], prepared['new_plan'], binding=binding,
                    candidate=candidate, receipts=receipts_for(binding, prepared, candidate, consumed))

    def test_keeping_or_replacing_consumed_wall_authorization_refuses(self):
        for value in (self.prepared['old_plan']['authorized_wall_extension'], None, {}):
            with self.subTest(value=value), self.assertRaisesRegex(Refusal, 'must_be_removed'):
                self.verify(new=dict(self.prepared['new_plan'], authorized_wall_extension=value))

    def test_ancient_previous_stream_hash_is_evidence_not_reapplied(self):
        self.assertNotEqual(self.prepared['old_plan']['authorized_wall_extension']['previous_stream_sha256'],
            self.candidate['resume_state']['sha256'])
        self.verify()

    def test_metadata_binding_preserves_guard_mapped_retained_plan_identity(self):
        for plan in (self.prepared['old_plan'], self.prepared['new_plan']):
            plan['root'] = '/absent/retained/C2/identity'
        self.receipts = receipts_for(self.binding, self.prepared, self.candidate, self.consumed)
        self.verify()
        stamp = self.receipts['consumed_wall_extension']['binding']
        self.assertEqual(stamp['retained_plan_root'], '/absent/retained/C2/identity')
        self.assertEqual(stamp['journal_root'], self.binding['journal_root'])

    def test_missing_extra_or_nondurable_receipts_refuse(self):
        for name in self.receipts:
            missing = deepcopy(self.receipts)
            del missing[name]
            with self.assertRaisesRegex(Refusal, 'required_plan_metadata_receipts'):
                self.verify(receipts=missing)
            changed = deepcopy(self.receipts)
            changed[name]['durable'] = False
            with self.assertRaisesRegex(Refusal, 'durable_plan_metadata_receipt'):
                self.verify(receipts=changed)
        with self.assertRaisesRegex(Refusal, 'required_plan_metadata_receipts'):
            self.verify(receipts=dict(self.receipts, unrelated={}))

    def test_proof_is_bound_to_life_plan_journal_pair_and_state(self):
        for key in self.receipts['consumed_wall_extension']['binding']:
            changed = deepcopy(self.receipts)
            changed['consumed_wall_extension']['binding'][key] = 'wrong'
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'durable_plan_metadata_receipt'):
                self.verify(receipts=changed)

    def test_pending_missing_learn_or_missing_intents_candidate_refuses(self):
        for mutation in ('pending', 'learn', 'intent'):
            changed = deepcopy(self.candidate)
            if mutation == 'pending':
                changed['resume_state']['state']['pending'] = 'REQUEST'
            elif mutation == 'learn':
                changed['records'].pop()
                changed['record_intents'].pop()
            else:
                changed['record_intents'] = []
            with self.subTest(mutation=mutation), self.assertRaises(Refusal):
                self.verify(candidate=changed)

    def test_corrupt_or_different_consumed_wall_record_refuses(self):
        for field, value in (('sha256', '0' * 64), ('kind', 'NOTE'), ('journal_id', 'b' * 32)):
            changed = deepcopy(self.receipts)
            record = changed['consumed_wall_extension']['record']
            record[field] = value
            if field != 'sha256':
                record['sha256'] = digest({key: item for key, item in record.items() if key != 'sha256'})
                changed['consumed_wall_extension']['intent'] = intents_for([record])[record['index']]
            with self.subTest(field=field), self.assertRaises(Refusal):
                self.verify(receipts=changed)
        changed = deepcopy(self.receipts)
        changed['consumed_wall_extension']['intent']['record_sha256'] = '0' * 64
        with self.assertRaisesRegex(Refusal, 'durable_record_intent_pair'):
            self.verify(receipts=changed)

    def test_consumed_wall_prior_stream_sha_must_prove_deadline_only_transition(self):
        changed = deepcopy(self.receipts)
        receipt = changed['consumed_wall_extension']
        saved = receipt['record']['document']['state']
        saved['state']['rows'][0]['source_sha256'] = digest('substituted-row')
        saved['sha256'] = digest(saved['state'])
        record = receipt['record']
        record['sha256'] = digest({key: value for key, value in record.items() if key != 'sha256'})
        receipt['intent'] = intents_for([record])[record['index']]
        with self.assertRaisesRegex(Refusal, 'exact_prior_state_no_other_changes'):
            self.verify(receipts=changed)

    def test_changed_deadline_rows_prompts_controls_or_recipe_refuse(self):
        for key, value in (('hard_end_unix', 10001), ('targets', ['EVAL']), ('learn_row_policy', 'different'),
                ('system_prompt', 'new'), ('birth_prompt', 'new'), ('root', '/different/life'),
                ('think_act_learn', dict(trial_id='same-life', controls='different'))):
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'source_only_plan_no_deadline'):
                self.verify(new=dict(self.prepared['new_plan'], **{key: value}))

    def test_tail_reader_bounds_sidecars_life_and_policy_cannot_change(self):
        for key, value in (('max_tail_records', 4096), ('max_tail_bytes', 1), ('sidecars', []),
                ('persist_complete_anchors', False), ('life_id', 'different'), ('root', '/other/stream'),
                ('policy', 'full_replay'), ('journal_id', 'b' * 32)):
            changed = deepcopy(self.prepared['new_plan'])
            changed['checkpoint_tail_recovery'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(Refusal, 'source_only_plan_no_deadline'):
                self.verify(new=changed)
        changed = deepcopy(self.prepared['new_plan'])
        del changed['checkpoint_tail_recovery']
        with self.assertRaisesRegex(Refusal, 'reader_must_remain_enabled'):
            self.verify(new=changed)

    def test_stale_wrong_or_arbitrary_anchor_refuses_even_with_rebound_receipt(self):
        for key, value in (('complete_index', 0), ('complete_index', 999), ('complete_sha256', '0' * 64)):
            changed = deepcopy(self.prepared['new_plan'])
            changed['checkpoint_tail_recovery'][key] = value
            receipts = receipts_for(self.binding, self.prepared, self.candidate, self.consumed, plan=changed)
            with self.subTest(key=key, value=value), self.assertRaisesRegex(Refusal, 'reanchored_to_selected_COMPLETE'):
                self.verify(new=changed, receipts=receipts)

    def test_tail_scan_must_preserve_state_inbox_sidecars_and_avoid_replay(self):
        for key, value in (('restored_state_sha256', '0' * 64), ('selection_sha256', '0' * 64),
                ('head_index', 999), ('head_sha256', '0' * 64), ('pending', 'REQUEST'),
                ('historical_body_replay', True), ('sidecars_verified', False), ('inbox_preserved', False),
                ('cpu_receipt_sha256', ''), ('reader_source_pins_sha256', '')):
            changed = deepcopy(self.receipts)
            changed['checkpoint_tail_recovery'][key] = value
            with self.subTest(key=key), self.assertRaises(Refusal):
                self.verify(receipts=changed)

    def test_extra_inbox_does_not_invalidate_exact_pair_receipts(self):
        records = deepcopy(self.records)
        append_record(records, self.binding, 'INBOX', dict(message=dict(id='arriving', text='retain',
            split='TRAIN', actor='parent'), source_id='/life/stream/inbox/new.json', source_sha256=digest('new')))
        self.verify(candidate=selected(self.binding, records))

    def test_exact_allowlist_supports_authorized_tested_reader_additions(self):
        for name in ('gpu/checkpoint_tail_runtime.py', 'gpu/checkpoint_tail_trusted.py'):
            self.prepared['new_source_pins'][name] = digest(name)
            self.authority['approved_source_changes'][name] = dict(before=None, after=digest(name))
        validate_prepared(self.binding, self.prepared, self.authority)
        unauthorized = deepcopy(self.prepared)
        unauthorized['new_source_pins']['gpu/extra.py'] = digest('unapproved')
        with self.assertRaisesRegex(Refusal, 'approved_source_delta'):
            validate_prepared(self.binding, unauthorized, self.authority)
        untested = dict(self.prepared, cpu_passed=False)
        with self.assertRaisesRegex(Refusal, 'CPU_and_continuity'):
            validate_prepared(self.binding, untested, self.authority)

    def test_allowlist_has_no_fixed_source_file_count(self):
        self.prepared['new_source_pins'] = deepcopy(self.prepared['old_source_pins'])
        name = next(iter(self.prepared['new_source_pins']))
        self.prepared['new_source_pins'][name] = digest('one_authorized_patch')
        self.authority['approved_source_changes'] = {name: dict(before=self.prepared['old_source_pins'][name],
            after=self.prepared['new_source_pins'][name])}
        validate_prepared(self.binding, self.prepared, self.authority)

    def test_receiver_cannot_substitute_other_source_root_or_reader_receipt(self):
        receiver = dict(plan=deepcopy(self.prepared['new_plan']), plan_sha256=digest(self.prepared['new_plan']),
            plan_metadata_receipts=deepcopy(self.receipts))
        verify_receiver_plan(self.binding, self.prepared, receiver, self.candidate)
        receiver['plan_metadata_receipts']['checkpoint_tail_recovery']['reader_source_pins_sha256'] = 'f' * 64
        with self.assertRaisesRegex(Refusal, 'CPU_receipt_for_exact_receiving_sources'):
            verify_receiver_plan(self.binding, self.prepared, receiver, self.candidate)
        receiver['plan']['source_root'] = '/unapproved/source'
        with self.assertRaisesRegex(Refusal, 'approved_template'):
            verify_receiver_plan(self.binding, self.prepared, receiver, self.candidate)

    def test_race_reanchors_new_receiving_plan_on_same_handle(self):
        fresh = deepcopy(self.records)
        append_record(fresh, self.binding, 'SLEEP_COMPLETE', deepcopy(self.records[-2]['document']))
        append_record(fresh, self.binding, 'R184_LEARN_COMPLETE', deepcopy(self.records[-1]['document']))
        next_candidate = selected(self.binding, fresh)
        operations = FakeOperations(self.binding, [self.candidate, None, next_candidate,
            next_candidate, next_candidate, next_candidate])
        original = operations.prepare_receiver

        def prepare(candidate, prepared, proof):
            receiver = original(candidate, prepared, proof)
            plan = deepcopy(prepared['new_plan'])
            plan['checkpoint_tail_recovery'].update(complete_index=candidate['complete_index'],
                complete_sha256=candidate['complete_sha256'])
            receiver.update(plan=plan, plan_sha256=digest(plan),
                plan_metadata_receipts=receipts_for(self.binding, prepared, candidate, self.consumed, plan=plan))
            return receiver

        operations.prepare_receiver = prepare
        token = coordinate(self.binding, self.prepared, self.authority, operations, max_attempts=2)
        self.assertEqual(token['receiver']['plan']['checkpoint_tail_recovery']['complete_index'], 4)
        self.assertNotIn('authorized_wall_extension', token['receiver']['plan'])
        self.assertEqual(operations.names().count('open'), 1)
        self.assertEqual(operations.names().count('resume'), 1)
        self.assertEqual(operations.names().count('commit'), 1)
        self.assertEqual(self.prepared['new_plan']['checkpoint_tail_recovery']['complete_index'], 2)

    def test_bad_metadata_evidence_never_reserves_or_commits(self):
        operations = FakeOperations(self.binding, [self.candidate])
        original = operations.prepare_receiver

        def prepare(candidate, prepared, proof):
            receiver = original(candidate, prepared, proof)
            receiver.update(plan=prepared['new_plan'], plan_sha256=digest(prepared['new_plan']), plan_metadata_receipts={})
            return receiver

        operations.prepare_receiver = prepare
        with self.assertRaisesRegex(Refusal, 'required_plan_metadata_receipts'):
            coordinate(self.binding, self.prepared, self.authority, operations)
        self.assertNotIn('stop', operations.names())
        self.assertNotIn('commit', operations.names())

    def test_wall_receipt_recheck_only_reads_manifest_and_one_record_pair(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            fixture = JournalFixture(directory)
            fixture.records = deepcopy(self.records)
            fixture.publish()
            binding = dict(self.binding, journal_root=str(fixture.root))
            candidate = read_boundary(binding)
            prepared = deepcopy(self.prepared)
            receipts = receipts_for(binding, prepared, candidate, self.consumed)
            original = boundary.read
            opened = []

            def bounded_read(path, **kwargs):
                opened.append(Path(path).name)
                return original(path, **kwargs)

            before = {str(path): path.read_bytes() for path in fixture.root.rglob('*') if path.is_file()}
            with patch.object(boundary, 'read', side_effect=bounded_read), \
                    patch.object(boundary.os, 'listdir', side_effect=AssertionError('no prefix enumeration')):
                recheck_consumed_wall_receipt(binding, receipts)
            self.assertEqual(set(opened), {'JOURNAL.json', '00000000000000000001.json',
                '00000000000000000001.intent.json'})
            self.assertEqual(before, {str(path): path.read_bytes() for path in fixture.root.rglob('*') if path.is_file()})
            path = fixture.root / 'records' / '00000000000000000001.intent.json'
            fixture.write(path, {})
            with self.assertRaisesRegex(Refusal, 'original_record_and_intent'):
                recheck_consumed_wall_receipt(binding, receipts)


if __name__ == '__main__':
    unittest.main()
