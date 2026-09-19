"""CPU tests for preserving every durable row across a declared sleep restart."""

from copy import deepcopy
import unittest

from restart_contract import ROW_POLICY, digest, prepare


def seal_record(index, kind, document, previous_sha256='0' * 64):
    result = dict(index=index, journal_id='a' * 32, kind=kind, document=document,
        previous_sha256=previous_sha256)
    result['sha256'] = digest(result)
    return result


def saved(state):
    return dict(state=state, sha256=digest(state))


class RestartContractTests(unittest.TestCase):
    def setUp(self):
        experiment = dict(base='frozen', adapter='private')
        checkpoint = dict(checkpoint_sha256=dict(adapter='a' * 64,
            optimizer='b' * 64, rng='b' * 64), optimizer_steps=48,
            experiment=experiment)
        prior = dict(pending=None, rows=[dict(source_sha256='old', target='original')],
            sleep_frontier=1, sleep_receipts=[dict(cycle=1, status='COMPLETE')],
            model_state_sha256=digest(checkpoint['checkpoint_sha256']),
            experiment=experiment, deadline_unix=100000,
            history=dict(working_state='before'))
        self.complete = seal_record(10, 'SLEEP_COMPLETE', dict(status='COMPLETE', cycle=1,
            checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'],
            total_optimizer_steps=48, resume_state=saved(prior)))
        current = deepcopy(prior)
        current['rows'].extend(dict(source_sha256='new' + str(index), target=text)
            for index, text in enumerate(('I will think.', '中文', 'print("claim")')))
        current['pending'] = 'sleep:' + digest(['new0', 'new1', 'new2'])
        current['history'] = dict(working_state='latest', parent='unanswered input')
        self.pending = seal_record(20, 'SLEEP_REQUEST', dict(cycle=2, resume_state=saved(current)))
        self.recipe = seal_record(21, 'SLEEP_RECIPE', dict(new_presentations=16,
            new_rows=3, selected_old_rows=0, policy='R181_NEW_ONLY_V1',
            learn_row_policy=ROW_POLICY, active_semantic_filters=[],
            semantic_row_exclusion=False), self.pending['sha256'])
        self.eligibility = seal_record(22, 'TARGET_ELIGIBILITY', dict(
            new_row_sha256=['new0', 'new1', 'new2'], rehearsal_row_sha256=[],
            excluded=[], raw_modified=False, learn_row_policy=ROW_POLICY,
            active_semantic_filters=[], semantic_row_exclusion=False), self.recipe['sha256'])
        self.updates = []
        previous = self.eligibility
        for index in range(4):
            previous = seal_record(23 + index, 'UPDATE', dict(optimizer_step=49 + index,
                source_sha256='new' + str(index % 3), losses=[], finished_unix=index),
                previous['sha256'])
            self.updates.append(previous)
        self.head = deepcopy(self.updates[-1])
        self.options = dict(life='C0', new_presentations=16, row_policy=ROW_POLICY,
            hard_end_unix=100000)

    def contract(self):
        return prepare(self.complete, self.pending, self.updates, recipe=self.recipe,
            eligibility=self.eligibility, head=self.head, **self.options)

    def reseal_updates(self):
        previous = self.eligibility
        for position, record in enumerate(self.updates):
            previous = seal_record(record['index'], record['kind'], record['document'],
                previous['sha256'])
            self.updates[position] = previous
        self.head = deepcopy(self.updates[-1])

    def reseal_pending(self):
        document = self.pending['document']
        document['resume_state'] = saved(document['resume_state']['state'])
        self.pending = seal_record(20, 'SLEEP_REQUEST', document)

    def test_preserves_every_pending_row_and_exact_state_without_mutating_inputs(self):
        before = deepcopy((self.complete, self.pending, self.updates))
        result = self.contract()
        contract = result['contract']
        self.assertEqual(contract['preserved_state'], self.pending['document']['resume_state'])
        self.assertEqual(contract['pending_rows'], 3)
        self.assertEqual(contract['retained_rows'], 4)
        self.assertEqual(result['sha256'], digest(contract))
        self.assertEqual((self.complete, self.pending, self.updates), before)
        contract['preserved_state']['state']['history']['working_state'] = 'changed copy'
        self.assertEqual((self.complete, self.pending, self.updates), before)

    def test_does_not_authorize_launch_or_claim_resident_rng_continuity(self):
        contract = self.contract()['contract']
        self.assertFalse(contract['execution_authorized'])
        self.assertFalse(contract['exact_resident_continuity_claimed'])
        self.assertFalse(contract['historical_generation_or_tool_reexecution'])
        self.assertTrue(contract['extra_recovery_compute_must_be_recorded_separately'])
        self.assertEqual(contract['rng_origin'], 'DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE')

    def test_other_life_refused(self):
        self.options['life'] = 'frozen sibling'
        with self.assertRaisesRegex(ValueError, 'only_named'):
            self.contract()

    def test_corrupt_record_refused(self):
        self.pending['document']['cycle'] = 20
        with self.assertRaisesRegex(ValueError, 'record_integrity'):
            self.contract()

    def test_corrupt_state_refused_even_inside_resealed_record(self):
        self.pending['document']['resume_state']['state']['pending'] = None
        self.pending = seal_record(20, 'SLEEP_REQUEST', self.pending['document'])
        with self.assertRaisesRegex(ValueError, 'saved_state_integrity'):
            self.contract()

    def test_dropping_or_replacing_old_rows_refused(self):
        self.pending['document']['resume_state']['state']['rows'][0]['target'] = 'replacement'
        self.reseal_pending()
        with self.assertRaisesRegex(ValueError, 'historical_rows_unchanged'):
            self.contract()

    def test_new_row_drop_refused(self):
        self.pending['document']['resume_state']['state']['rows'].pop()
        self.reseal_pending()
        with self.assertRaisesRegex(ValueError, 'pending_sleep_rows_binding'):
            self.contract()

    def test_clearing_pending_refused(self):
        self.pending['document']['resume_state']['state']['pending'] = None
        self.reseal_pending()
        with self.assertRaisesRegex(ValueError, 'pending_sleep_rows_binding'):
            self.contract()

    def test_uncommitted_checkpoint_model_refused(self):
        self.pending['document']['resume_state']['state']['model_state_sha256'] = 'new state'
        self.reseal_pending()
        with self.assertRaisesRegex(ValueError, 'same_durable_model_state'):
            self.contract()

    def test_updated_receipt_frontier_refused(self):
        self.pending['document']['resume_state']['state']['sleep_receipts'].append(dict(cycle=2))
        self.reseal_pending()
        with self.assertRaisesRegex(ValueError, 'no_uncommitted_sleep_promoted'):
            self.contract()

    def test_changed_deadline_refused(self):
        self.options['hard_end_unix'] += 100
        with self.assertRaisesRegex(ValueError, 'deadline_unchanged'):
            self.contract()

    def test_wrong_update_step_refused(self):
        document = self.updates[0]['document']
        document['optimizer_step'] += 2
        self.reseal_updates()
        with self.assertRaisesRegex(ValueError, 'recorded_optimizer_step_sequence'):
            self.contract()

    def test_update_of_other_row_refused(self):
        document = self.updates[0]['document']
        document['source_sha256'] = 'old'
        self.reseal_updates()
        with self.assertRaisesRegex(ValueError, 'pending_rows_only'):
            self.contract()

    def test_zero_updates_and_changed_row_policy_refused(self):
        self.updates.clear()
        with self.assertRaisesRegex(ValueError, 'interrupted_training_receipt_count'):
            self.contract()
        self.options['row_policy'] = 'exclude CJK'
        with self.assertRaisesRegex(ValueError, 'all_authentic_child_rows_required'):
            self.contract()

    def test_reduced_dose_cannot_replace_original_recipe(self):
        self.options['new_presentations'] = 2
        with self.assertRaisesRegex(ValueError, 'original_recorded_recipe_required'):
            self.contract()

    def test_trailing_update_omission_refused_against_original_head(self):
        self.updates = self.updates[:1]
        with self.assertRaisesRegex(ValueError, 'complete_update_suffix'):
            self.contract()

    def test_middle_update_omission_refused(self):
        self.updates.pop(1)
        with self.assertRaisesRegex(ValueError, 'contiguous_authenticated_sleep_tail'):
            self.contract()

    def test_wrong_recipe_chain_refused(self):
        self.recipe = seal_record(21, 'SLEEP_RECIPE', self.recipe['document'], 'f' * 64)
        with self.assertRaisesRegex(ValueError, 'contiguous_authenticated_sleep_tail'):
            self.contract()


if __name__ == '__main__':
    unittest.main()
