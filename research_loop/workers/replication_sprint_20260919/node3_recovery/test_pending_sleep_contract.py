from copy import deepcopy
import hashlib
import json
import unittest

import pending_sleep_contract as contract


class PendingSleepContractTests(unittest.TestCase):
    def fixture(self, caption=False, update_count=2):
        life = ('r213_r226_caption_observation_fork' if caption else 'r213_math_b_fork')
        physical, gpu_uuid = contract.ORIGINAL_GPUS[life]
        plan = dict(physical=physical, gpu_uuid=gpu_uuid, hard_end_unix=contract.HARD_END,
            lease_end_unix=contract.HARD_END + 21600, new_presentations=16,
            rehearsal_presentations=0, learn_row_policy=contract.ROW_POLICY,
            think_act_learn=dict(learn_row_policy=contract.ROW_POLICY),
            authorized_wall_extension=dict(preserved_original_field=True))
        checkpoint = dict(checkpoint_sha256=dict(adapter='a' * 64,
            optimizer='b' * 64, rng='b' * 64), optimizer_steps=100,
            experiment=dict(name='original experiment'))
        old_row = dict(source_sha256='old', target='original authentic row')
        prior = dict(rows=[old_row], sleep_frontier=1, pending=None,
            model_state_sha256=contract.digest(checkpoint['checkpoint_sha256']),
            sleep_receipts=[dict(cycle=1)], experiment=checkpoint['experiment'],
            history=dict(working_state=dict(entries=['do not lose this']),
                events=['old context']), deadline_unix=contract.HARD_END)
        sources = [f'row_{index}' for index in range(5 if caption else 3)]
        current = deepcopy(prior)
        current['rows'] += [dict(source_sha256=source, target=f'authentic {source}')
            for source in sources]
        current['pending'] = 'sleep:' + contract.digest(sources)
        current['history']['events'].append('new context must survive')
        complete = self.record('SLEEP_COMPLETE', 10, 'prefix', dict(status='COMPLETE',
            cycle=1, checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'],
            total_optimizer_steps=100, resume_state=self.state(prior)))
        pending = self.record('SLEEP_REQUEST', 20, 'intervening-original-tail',
            dict(cycle=2, resume_state=self.state(current)))
        recipe = dict(policy='R181_NEW_ONLY_V1', new_presentations=16,
            new_rows=len(sources), selected_old_rows=0,
            learn_row_policy=contract.ROW_POLICY, active_semantic_filters=[],
            semantic_row_exclusion=False)
        eligibility = dict(learn_row_policy=contract.ROW_POLICY, active_semantic_filters=[],
            semantic_row_exclusion=False, new_row_sha256=sources,
            rehearsal_row_sha256=[], excluded=[], raw_modified=False)
        documents = []
        if caption:
            documents.append(('R227_TARGET_METRICS', dict(diagnostics_only=True)))
        documents += [('SLEEP_RECIPE', recipe), ('TARGET_ELIGIBILITY', eligibility)]
        documents += [('UPDATE', dict(optimizer_step=101 + index,
            source_sha256=sources[index % len(sources)])) for index in range(update_count)]
        suffix = []
        previous = pending
        for kind, document in documents:
            previous = self.record(kind, previous['index'] + 1, previous['sha256'], document)
            suffix.append(previous)
        return dict(complete=complete, pending=pending, suffix=suffix, life=life, plan=plan)

    @staticmethod
    def state(value):
        return dict(state=value, sha256=contract.digest(value))

    @staticmethod
    def record(kind, index, previous, document):
        result = dict(kind=kind, index=index, previous_sha256=previous,
            journal_id='original-journal', document=document)
        result['sha256'] = contract.digest(result)
        return result

    @staticmethod
    def reseal(record):
        record['sha256'] = contract.digest({key: value for key, value in record.items()
            if key != 'sha256'})

    def reseal_suffix(self, fixture):
        previous = fixture['pending']
        for record in fixture['suffix']:
            record['previous_sha256'] = previous['sha256']
            self.reseal(record)
            previous = record

    def change_state(self, fixture, name, update):
        record = fixture[name]
        state = record['document']['resume_state']['state']
        update(state)
        record['document']['resume_state'] = self.state(state)
        self.reseal(record)
        if name == 'pending':
            self.reseal_suffix(fixture)

    def prepare(self, fixture):
        plan_bytes = json.dumps(fixture['plan'], sort_keys=True).encode()
        return contract.prepare(fixture['complete'], fixture['pending'], fixture['suffix'],
            life=fixture['life'], plan_bytes=plan_bytes,
            expected_plan_sha256=hashlib.sha256(plan_bytes).hexdigest())

    def test_math_restarts_all_48_updates_not_remaining(self):
        result = self.prepare(self.fixture(update_count=8))['contract']
        self.assertEqual((result['recorded_unsaved_updates'],
            result['recovery_requires_full_new_updates'], result['recovery_optimizer_end']), (8, 48, 148))
        self.assertFalse(result['execution_authorized'])
        self.assertFalse(result['exact_resident_continuity_claimed'])

    def test_caption_restarts_all_80_updates_and_preserves_diagnostics(self):
        result = self.prepare(self.fixture(caption=True, update_count=77))['contract']
        self.assertEqual(result['recovery_requires_full_new_updates'], 80)
        self.assertEqual(result['recorded_unsaved_updates'], 77)
        self.assertEqual(len(result['diagnostic_records']), 1)

    def test_finished_compute_without_checkpoint_is_not_a_complete(self):
        result = self.prepare(self.fixture(update_count=48))['contract']
        self.assertEqual(result['recovery_requires_full_new_updates'], 48)
        self.assertIn('NOT_UNSAVED', result['rng_origin'])

    def test_inputs_rows_history_working_state_are_unchanged(self):
        fixture = self.fixture(caption=True)
        original = deepcopy(fixture)
        result = self.prepare(fixture)
        self.assertEqual(fixture, original)
        self.assertEqual(result['contract']['preserved_state'],
            fixture['pending']['document']['resume_state'])
        self.assertEqual(result['sha256'], contract.digest(result['contract']))

    def test_math_a_pending_generation_is_not_sleep_recovery(self):
        fixture = self.fixture()
        fixture['life'] = 'r213_math_a'
        with self.assertRaisesRegex(ValueError, 'only_seven'):
            self.prepare(fixture)

    def test_unrelated_life_is_rejected(self):
        fixture = self.fixture()
        fixture['life'] = 'C0'
        with self.assertRaisesRegex(ValueError, 'only_seven'):
            self.prepare(fixture)

    def test_original_gpu_cannot_change(self):
        fixture = self.fixture()
        fixture['plan']['physical'] = 0
        with self.assertRaisesRegex(ValueError, 'same_original_physical_gpu'):
            self.prepare(fixture)

    def test_original_deadline_cannot_change(self):
        fixture = self.fixture()
        fixture['plan']['hard_end_unix'] += 1
        with self.assertRaisesRegex(ValueError, 'same_original_wall_and_lease'):
            self.prepare(fixture)

    def test_parent_row_exclusion_cannot_be_reintroduced(self):
        fixture = self.fixture()
        fixture['plan']['learn_row_policy'] = 'new_filter'
        with self.assertRaisesRegex(ValueError, 'all_authentic_child_rows'):
            self.prepare(fixture)

    def test_plan_bytes_must_match_external_original_pin(self):
        fixture = self.fixture()
        with self.assertRaisesRegex(ValueError, 'original_plan_bytes_required'):
            contract.prepare(fixture['complete'], fixture['pending'], fixture['suffix'],
                life=fixture['life'], plan_bytes=json.dumps(fixture['plan']).encode(),
                expected_plan_sha256='0' * 64)

    def test_missing_update_breaks_chain(self):
        fixture = self.fixture(update_count=3)
        del fixture['suffix'][-2]
        with self.assertRaisesRegex(ValueError, 'contiguous_authenticated_sleep_suffix'):
            self.prepare(fixture)

    def test_tampered_record_is_rejected(self):
        fixture = self.fixture()
        fixture['suffix'][-1]['document']['optimizer_step'] += 1
        with self.assertRaisesRegex(ValueError, 'record_integrity'):
            self.prepare(fixture)

    def test_saved_state_digest_must_match(self):
        fixture = self.fixture()
        fixture['pending']['document']['resume_state']['state']['history'] = {}
        self.reseal(fixture['pending'])
        with self.assertRaisesRegex(ValueError, 'saved_state_integrity'):
            self.prepare(fixture)

    def test_cannot_drop_historical_rows(self):
        fixture = self.fixture()
        self.change_state(fixture, 'pending', lambda state:
            state['rows'].__setitem__(0, dict(source_sha256='replacement')))
        with self.assertRaisesRegex(ValueError, 'historical_rows_unchanged'):
            self.prepare(fixture)

    def test_cannot_drop_pending_rows(self):
        fixture = self.fixture()
        self.change_state(fixture, 'pending', lambda state: state['rows'].pop())
        with self.assertRaisesRegex(ValueError, 'original_pending_row_count'):
            self.prepare(fixture)

    def test_cannot_advance_sleep_frontier(self):
        fixture = self.fixture()
        self.change_state(fixture, 'pending', lambda state:
            state.__setitem__('sleep_frontier', len(state['rows'])))
        with self.assertRaisesRegex(ValueError, 'durable_sleep_frontier'):
            self.prepare(fixture)

    def test_cannot_adopt_unsaved_optimizer_counter(self):
        fixture = self.fixture()
        fixture['complete']['document']['checkpoint']['optimizer_steps'] = 102
        self.reseal(fixture['complete'])
        with self.assertRaisesRegex(ValueError, 'committed_checkpoint_binding'):
            self.prepare(fixture)

    def test_cannot_adopt_partial_model_state(self):
        fixture = self.fixture()
        self.change_state(fixture, 'pending', lambda state:
            state.__setitem__('model_state_sha256', 'partial-checkpoint'))
        with self.assertRaisesRegex(ValueError, 'durable_not_unsaved_model_state'):
            self.prepare(fixture)

    def test_same_journal_required(self):
        fixture = self.fixture()
        fixture['pending']['journal_id'] = 'other-life'
        self.reseal(fixture['pending'])
        with self.assertRaisesRegex(ValueError, 'same_ordered_journal'):
            self.prepare(fixture)

    def test_original_budget_cannot_grow(self):
        fixture = self.fixture(update_count=49)
        with self.assertRaisesRegex(ValueError, 'original_presentation_budget'):
            self.prepare(fixture)

    def test_targets_cannot_exclude_child_rows(self):
        fixture = self.fixture()
        fixture['suffix'][1]['document']['excluded'] = ['row_0']
        self.reseal_suffix(fixture)
        with self.assertRaisesRegex(ValueError, 'targets_preserve_all_pending_rows'):
            self.prepare(fixture)

    def test_no_filter_even_if_targets_list_retained(self):
        fixture = self.fixture()
        fixture['suffix'][0]['document']['active_semantic_filters'] = ['CJK']
        self.reseal_suffix(fixture)
        with self.assertRaisesRegex(ValueError, 'no_row_filters'):
            self.prepare(fixture)

    def test_no_historical_generation_can_be_in_sleep_suffix(self):
        fixture = self.fixture()
        fixture['suffix'][-1]['kind'] = 'RESPONSE'
        self.reseal_suffix(fixture)
        with self.assertRaisesRegex(ValueError, 'wrong_record_kind'):
            self.prepare(fixture)


if __name__ == '__main__':
    unittest.main()
