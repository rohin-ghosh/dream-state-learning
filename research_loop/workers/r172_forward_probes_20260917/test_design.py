from copy import deepcopy
import hashlib
import json
import unittest

import design


class RollingDesignTests(unittest.TestCase):
    def enrollment(self):
        return dict(life_id='life', custody_verified=True, frontier=30, frozen_unix=100,
            hard_end_unix=1000)

    def event(self, sleep=31):
        return dict(life_id='life', sleep=sleep, committed_unix=101,
            complete_commit_and_payload_verified=True, receiving_copy_verified=True)

    def signature(self):
        signature = {name: hashlib.sha256(name.encode()).hexdigest() for name in design.BASELINE_HASH_FIELDS}
        signature.update(node='node', source_root='/original/life', condition='LORA_ON',
            calls=3, max_new_tokens=512, original_initial_link_verified=True,
            zero_update_initial_verified=True, independent_birth_only_context=True,
            readonly_before_after_verified=True)
        return signature

    def receipt(self):
        return dict(status='COMPLETE', signature=self.signature(), receipt_hash_verified=True,
            custody_join_verified=True)

    def cell(self, life_id='life', sleep=31, condition='LORA_ON', ready=True):
        return dict(key=f'{life_id}:{sleep}:{condition}', life_id=life_id, sleep=sleep,
            condition=condition, ready=ready, ready_unix=101,
            capture_sha256=hashlib.sha256(f'{life_id}:{sleep}'.encode()).hexdigest(),
            kind='baseline' if sleep == 0 else 'forward')

    def test_resource_arithmetic(self):
        budget = design.resources()
        self.assertEqual(budget['forward_calls'], 24 * 3 * 2 * 3)
        self.assertEqual(budget['baseline_calls_ceiling'], 24 * 2 * 3)
        self.assertEqual(budget['call_cap'], budget['forward_calls'] + budget['baseline_calls_ceiling'])
        self.assertEqual(budget['token_cap'], budget['call_cap'] * 512)
        self.assertEqual(budget['gpu_slot_seconds_cap'], 2 * budget['max_active_window_seconds'])

    def test_read_allocations_fit_without_granting_authority(self):
        rows = [dict(life_id=f'life{index}', metadata=design.GIB, adapter=design.GIB // 2) for index in range(24)]
        self.assertEqual(design.read_allocation_feasibility(rows, 64 * 1024 ** 2),
            'FINITE_ALLOCATION_FITS_NOT_SOURCE_AUTHORITY')

    def test_discovery_not_hidden_outside_metadata_cap(self):
        rows = [dict(life_id=f'life{index}', metadata=2 * design.GIB, adapter=0) for index in range(16)]
        with self.assertRaisesRegex(ValueError, 'aggregate_metadata'):
            design.read_allocation_feasibility(rows, 1)

    def test_adapter_aggregate_and_per_life_caps(self):
        rows = [dict(life_id=f'life{index}', metadata=0, adapter=design.GIB) for index in range(17)]
        with self.assertRaisesRegex(ValueError, 'aggregate_adapter'):
            design.read_allocation_feasibility(rows, 0)
        with self.assertRaisesRegex(ValueError, 'per_life_per_kind'):
            design.read_allocation_feasibility([dict(life_id='large', metadata=2 * design.GIB + 1, adapter=0)], 0)

    def test_discovery_cap_and_duplicate_allocation(self):
        with self.assertRaisesRegex(ValueError, 'discovery_subcap'):
            design.read_allocation_feasibility([], 64 * 1024 ** 2 + 1)
        row = dict(life_id='same', metadata=0, adapter=0)
        with self.assertRaisesRegex(ValueError, 'unique_bounded'):
            design.read_allocation_feasibility([row, row], 0)

    def test_exact_baseline_reuse(self):
        self.assertEqual(design.baseline_decision(self.receipt(), self.signature()),
            dict(status='EXACT_BASELINE_REUSE', new_calls=0))

    def test_all_identity_fields_required(self):
        for field in design.BASELINE_FIELDS:
            with self.subTest(field=field):
                receipt = self.receipt()
                receipt['signature'].pop(field)
                self.assertEqual(design.baseline_decision(receipt, self.signature())['new_calls'], 3)

    def test_each_mismatch_costs_new_baseline(self):
        for field in design.BASELINE_FIELDS:
            with self.subTest(field=field):
                receipt = self.receipt()
                receipt['signature'][field] = 'different'
                self.assertEqual(design.baseline_decision(receipt, self.signature())['new_calls'], 3)

    def test_equal_but_invalid_baseline_is_not_reused(self):
        for field, value in [('base_sha256', 'not_a_hash'), ('calls', 2),
                ('max_new_tokens', 256), ('condition', 'OTHER'), ('zero_update_initial_verified', False)]:
            with self.subTest(field=field):
                signature = self.signature()
                signature[field] = value
                receipt = dict(self.receipt(), signature=signature)
                self.assertEqual(design.baseline_decision(receipt, signature)['new_calls'], 3)

    def test_unverified_or_absent_receipt_has_explicit_cost(self):
        for receipt in [None, dict(self.receipt(), receipt_hash_verified=False),
                dict(self.receipt(), custody_join_verified=False)]:
            self.assertEqual(design.baseline_decision(receipt, self.signature())['new_calls'], 3)

    def test_consumed_invalid_baseline_stays_missing(self):
        for status in ('REFUSED', 'FAILED', 'UNRESOLVED', 'INVALID'):
            result = design.baseline_decision(dict(status=status), self.signature())
            self.assertEqual(result['status'], 'MISSING_PRIOR_CONSUMED_NO_AUTOMATIC_RETRY')
            self.assertEqual(result['new_calls'], 0)

    def test_every_consecutive_sleep_no_selected_skip(self):
        for sleep in (31, 32, 33):
            self.assertTrue(design.eligible_sleep(self.enrollment(), self.event(sleep)))
        for sleep in (0, 29, 30, 34):
            self.assertFalse(design.eligible_sleep(self.enrollment(), self.event(sleep)))

    def test_no_historical_snapshot_frontier_enrollment(self):
        self.assertFalse(design.eligible_sleep(dict(self.enrollment(), frontier=None), self.event()))
        self.assertFalse(design.eligible_sleep(dict(self.enrollment(), custody_verified=False), self.event()))

    def test_prospective_commit_and_exact_capture_required(self):
        for changes in [dict(committed_unix=100), dict(committed_unix=1000),
                dict(receiving_copy_verified=False), dict(complete_commit_and_payload_verified=False),
                dict(life_id='other')]:
            self.assertFalse(design.eligible_sleep(self.enrollment(), dict(self.event(), **changes)))

    def test_forward_does_not_wait_for_fleet_initials(self):
        initial_jobs = [self.cell(f'other{index}', sleep=0) for index in range(23)]
        forward = self.cell()
        result = design.choose_ready([*initial_jobs, forward], set(), {}, 'LORA_ON')
        self.assertEqual(result, forward)

    def test_missing_peer_baseline_does_not_block(self):
        result = design.choose_ready([self.cell('peer', ready=False), self.cell()], set(), {}, 'LORA_ON')
        self.assertEqual(result['life_id'], 'life')

    def test_fairness_between_ready_lives(self):
        result = design.choose_ready([self.cell('busy'), self.cell('waiting')], set(), {'busy': 3}, 'LORA_ON')
        self.assertEqual(result['life_id'], 'waiting')

    def test_condition_separation_and_no_retry(self):
        on_cell = self.cell()
        off_cell = self.cell(condition='LORA_OFF')
        self.assertIsNone(design.choose_ready([on_cell, off_cell], {on_cell['key']}, {}, 'LORA_ON'))
        self.assertEqual(design.choose_ready([on_cell, off_cell], set(), {}, 'LORA_OFF'), off_cell)

    def test_duplicate_cell_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_condition_checkpoint'):
            design.choose_ready([self.cell(), self.cell()], set(), {}, 'LORA_ON')

    def test_no_implicit_release_or_authority(self):
        blockers = design.opening_prerequisites({})
        self.assertEqual(len(blockers), 8)
        evidence = {name: True for name in blockers}
        self.assertEqual(design.opening_prerequisites(evidence), [])
        evidence['both_old_controllers_terminal'] = False
        self.assertEqual(design.opening_prerequisites(evidence), ['both_old_controllers_terminal'])

    def test_wall_and_lease_are_not_sliding_extensions(self):
        start = design.OLD_END - 60
        self.assertEqual(design.campaign_end(start, design.ABSOLUTE_END + 21600), start + 14400)
        self.assertEqual(design.campaign_end(start, start + 21600 + 1000), start + 1000)
        with self.assertRaisesRegex(ValueError, 'window_missed'):
            design.campaign_end(design.LATEST_START + 1, design.ABSOLUTE_END + 21600)
        with self.assertRaisesRegex(ValueError, 'no_full_job'):
            design.campaign_end(start, start + 21600 + 915)

    def test_charge_before_call_failure_preserved_and_no_retry(self):
        ledger = design.reserve_simulation([], self.cell(), 100, 1016)
        self.assertEqual(ledger[0]['charged_calls'], 3)
        self.assertEqual(ledger[0]['charged_tokens'], 1536)
        ledger[0]['status'] = 'FAILED'
        before = deepcopy(ledger)
        with self.assertRaisesRegex(ValueError, 'no_retry'):
            design.reserve_simulation(ledger, self.cell(), 100, 1016)
        self.assertEqual(ledger, before)

    def test_exact_job_admission_margin(self):
        with self.assertRaisesRegex(ValueError, 'full_job'):
            design.reserve_simulation([], self.cell(), 100, 1015)

    def test_baseline_savings_cannot_expand_forward_quota(self):
        ledger = []
        for sleep in (31, 32, 33):
            for condition in design.CONDITIONS:
                ledger = design.reserve_simulation(ledger, self.cell(sleep=sleep, condition=condition), 100, 1016)
        with self.assertRaisesRegex(ValueError, 'per_life_quota'):
            design.reserve_simulation(ledger, self.cell(sleep=34), 100, 1016)

    def test_relabelled_failed_cell_cannot_retry(self):
        ledger = design.reserve_simulation([], self.cell(), 100, 1016)
        ledger[0]['status'] = 'FAILED'
        with self.assertRaisesRegex(ValueError, 'relabelled_consumed'):
            design.reserve_simulation(ledger, dict(self.cell(), key='new-label'), 100, 1016)

    def test_checkpoint_specific_pair_not_other_control(self):
        ledger = design.reserve_simulation([], self.cell(), 100, 1016)
        off_cell = self.cell(condition='LORA_OFF')
        off_cell['capture_sha256'] = hashlib.sha256(b'other checkpoint').hexdigest()
        with self.assertRaisesRegex(ValueError, 'exact_checkpoint_ON_OFF_pair'):
            design.reserve_simulation(ledger, off_cell, 100, 1016)

    def test_cannot_spend_baseline_allowance_on_forward_cell(self):
        with self.assertRaisesRegex(ValueError, 'baseline_forward_partition'):
            design.reserve_simulation([], dict(self.cell(), kind='baseline'), 100, 1016)

    def test_full_24_life_call_ceiling_is_finite(self):
        ledger = []
        for index in range(24):
            for sleep in (0, 31, 32, 33):
                for condition in design.CONDITIONS:
                    ledger = design.reserve_simulation(ledger, self.cell(f'life{index}', sleep, condition), 100, 1016)
        self.assertEqual(sum(row['charged_calls'] for row in ledger), 576)
        self.assertEqual(sum(row['charged_tokens'] for row in ledger), 294912)
        with self.assertRaisesRegex(ValueError, 'aggregate576'):
            design.reserve_simulation(ledger, self.cell('extra'), 100, 1016)


class PublicMetadataProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roster = json.loads((design.REPO / 'research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json').read_bytes())
        cls.instrument_source = (design.REPO / design.SOURCE_FILES[0]).read_text()

    def test_actual_24_not_21_or_22_and_no_frontier_inference(self):
        rows = design.project_roster(self.roster)
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(row['prior_registered'] for row in rows), 18)
        self.assertTrue(all(row['admitted_frontier'] is None and not row['fixed_cycles'] for row in rows))
        self.assertNotIn('R158_parented_learning', {row['life_id'] for row in rows})

    def test_exact_six_new_custody(self):
        rows = design.project_roster(self.roster)
        self.assertEqual({row['life_id'] for row in rows if not row['prior_registered']}, {
            'C5', 'repo_reader', 'KERNEL0_RESUMED_SPARSE2',
            'orch_r136_raw_unparented_a40r1_20260916_attempt1',
            'r137_raw3_sparse3_free_socratic_seed1', 'r137_kernel4_sparse2_free_coach'})

    def test_repo_reader_alias_never_substitutes_old_frontier(self):
        row = next(row for row in design.project_roster(self.roster) if row['life_id'] == 'repo_reader')
        self.assertIsNone(row['last_saved_metadata_only'])
        self.assertNotEqual(row['process_plan_root'], row['proposed_storage_root'])
        self.assertIn('PROCESS_ROOT_TO_RECOVERY_STORAGE_ALIAS', row['special_custody'])

    def test_duplicate_identity_is_not_an_extra_life(self):
        roster = deepcopy(self.roster)
        roster['rows'].append(deepcopy(roster['rows'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate_life'):
            design.project_roster(roster)

    def test_snapshot_unknown_cannot_be_replaced_by_summary_count(self):
        roster = deepcopy(self.roster)
        roster['rows'][0]['status'] = 'UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'exact_24'):
            design.project_roster(roster)

    def test_source_instrument_exact_and_no_imports_needed(self):
        instrument = design.frozen_instrument(self.instrument_source)
        self.assertEqual(instrument['prompts'], list(design.PROMPTS))
        self.assertEqual(instrument['max_new_tokens'], 512)
        self.assertFalse(instrument['train_content_read'])

    def test_changed_decoder_rejected(self):
        changed = self.instrument_source.replace('greedy_temperature_zero_no_sampling_repetition_penalty_1', 'sample')
        with self.assertRaisesRegex(ValueError, 'frozen_decoder'):
            design.frozen_instrument(changed)

    def test_changed_prompt_rejected(self):
        changed = self.instrument_source.replace('What have you been working on? Continue it.', 'Tell us the object.')
        with self.assertRaisesRegex(ValueError, 'frozen_three_prompts'):
            design.frozen_instrument(changed)


if __name__ == '__main__':
    unittest.main()
