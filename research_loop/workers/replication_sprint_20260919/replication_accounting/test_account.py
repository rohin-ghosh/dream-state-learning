"""Synthetic CPU regression fixtures; none are scientific observations."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

import account
import export_public


def envelope(value):
    return dict(payload=deepcopy(value), projection_sha256=account.digest(value),
        source_object_sha256=account.digest(value), sha256=account.digest(value), bytes=1, path='synthetic')


def refresh(reference):
    reference['projection_sha256'] = account.digest(reference['payload'])


def basic_plan():
    return dict(root='/synthetic', arms=['base', 'c2sleep51', 'c2sleep117'], seeds=[23301, 23302],
        scenes=['scene1', 'scene2', 'scene3'], tokens_per_cell=1024,
        diagnostic_epoch_sha256=account.digest('diagnostic'), judge_epoch_sha256=account.digest('judge'),
        judge_adapter_sha256=account.digest('judge_adapter'))


def make_cell(plan, scene='scene1', seed=23301):
    events = []
    position = 0
    for index, tokens in enumerate((128, 256, 128, 256, 128, 128)):
        stage = 'THINK' if index % 2 == 0 else 'ACT'
        results = []
        if stage == 'ACT':
            results.append(dict(caption_sha256=account.digest((scene, seed, 'caption')),
                result=dict(rank=20, accepted=True, status='new_pixel', pixel_id='pixel-000001',
                    replayed=index != 1, top_k=50, reference_count=64)))
        events.append(dict(origin=dict(stage=stage, request_sha256=account.digest(('request', index)),
            response_sha256=account.digest(('response', index)), generated_tokens_before=position,
            generated_tokens_after=position + tokens), actual_generated_tokens=tokens,
            requested_max_new_tokens=tokens, score=dict(results=results,
                judge_epoch_sha256=plan['judge_epoch_sha256'], diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'])))
        position += tokens
    return dict(status=account.COMPLETE, budget=1024, generated_tokens=1024,
        no_updates=True, parent_tokens=0, learn_or_other_reply_tokens=0,
        diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'], contest_id=scene, seed=seed, events=events)


def make_fixture():
    plan = basic_plan()
    epoch = dict(judge_epoch_sha256=plan['judge_epoch_sha256'], sampling_seeds=plan['seeds'])
    plan['diagnostic_epoch_sha256'] = account.digest(epoch)
    declarations, jobs, prepared_jobs, block_jobs = [], [], [], []
    rows = []
    for arm in plan['arms']:
        base_sha = account.digest('base')
        adapter_sha = None if arm == 'base' else account.digest(arm)
        source_age = None if arm == 'base' else dict(absolute_sleep=51 if arm == 'c2sleep51' else 117,
            base_sha256=base_sha, adapter_state_sha256=adapter_sha)
        checkpoint = dict(base_sha256=base_sha, adapter_state_sha256=adapter_sha, source_age=source_age)
        identity = dict(arm=arm, checkpoint=checkpoint)
        job_id = account.digest(identity)
        declaration = dict(arm=arm, job_id=job_id, identity=identity)
        declarations.append(declaration)
        parameters = dict(base_sha256=base_sha, adapter_state_sha256=adapter_sha,
            decoder=dict(temperature=0.8), tokenizer_backend_sha256=account.digest('tokenizer'),
            chat_template_sha256=account.digest('template'), library_versions=dict(torch='synthetic'),
            all_parameters_frozen=True, optimizer_created=False)
        config = dict(job_id=job_id, job_identity=identity, seeds=plan['seeds'],
            expected_scene_ids=plan['scenes'], diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'],
            token_budget=6144, scenes=3, parent_tokens=0, training_updates=0, source_context_loaded=False,
            source_checkpoint=source_age, plain_base=arm == 'base', condition=arm,
            original_parameter_identity=parameters, judge_rank=8, judge_step=15625,
            adapter_sha256=plan['judge_adapter_sha256'])
        common = dict(diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'],
            judge_epoch_sha256=plan['judge_epoch_sha256'], source_age=source_age, condition=arm, parent_tokens=0)
        loaded = dict(common, snapshot_context_used=False, source_parent_text_loaded=False, identity=parameters)
        cells = [dict(contest_id=scene, seed=seed, result=envelope(make_cell(plan, scene, seed)))
            for scene in plan['scenes'] for seed in plan['seeds']]
        complete = dict(common, unchanged_identity=parameters, training_updates=0, actual_generated_tokens=6144,
            cells=[dict(contest_id=cell['contest_id'], seed=cell['seed'],
                source_object_sha256=cell['result']['source_object_sha256']) for cell in cells])
        verification = dict(arm=arm, job_id=job_id, loaded_sha256=account.digest(loaded), complete_sha256=account.digest(complete))
        verification['unit_states'] = {role: dict(ExecMainStatus='0', Result='success', SubState='exited')
            for role in ('player', 'judge')}
        jobs.append(dict(arm=arm, job_id=job_id, config=envelope(config), loaded=envelope(loaded),
            complete=envelope(complete), completion_verified=envelope(verification), cells=cells))
        prepared_jobs.append(dict(job_id=job_id, config_sha256=account.digest(config)))
        block_jobs.append(verification)
        for seed in plan['seeds']:
            metrics = dict(generated_tokens=3072, think_events=9, act_attempts=9, distinct_scored=3,
                distinct_accepted=3, new_pixels=3, acts_without_results=0, rankless_outcomes=0,
                rankless_by_status={}, accept_rate=1.0)
            cell_metrics = dict(metrics, generated_tokens=1024, think_events=3, act_attempts=3,
                distinct_scored=1, distinct_accepted=1, new_pixels=1)
            rows.append(dict(arm=arm, seed=seed, status='COMPLETE', complete_cells_only=metrics,
                actual_generated_tokens=3072, missing_cells=0, incomplete_present_cells=0,
                cells=[dict(contest_id=cell['contest_id'], status=account.COMPLETE,
                    sha256=cell['result']['sha256'], path='synthetic', metrics=cell_metrics)
                    for cell in cells if cell['seed'] == seed]))
    registry = dict(root=plan['root'], diagnostic_epoch=epoch, diagnostic_epoch_sha256=account.digest(epoch),
        expected_scene_ids=plan['scenes'], jobs=declarations)
    freeze = dict(files={'report_sampling.py': account.digest('runtime')})
    plan.update(registry_sha256=account.digest(registry), source_freeze_sha256=account.digest(freeze),
        preregistration_sha256=account.digest('preregistration'))
    prepared = dict(registry_sha256=plan['registry_sha256'], source_freeze_sha256=plan['source_freeze_sha256'], jobs=prepared_jobs)
    block = dict(status='COMPLETE_THREE_SOURCE_SAMPLING_DIAGNOSTIC',
        diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'], jobs=block_jobs)
    snapshot = dict(root=plan['root'], captured_utc='synthetic', jobs=jobs,
        documents={'REGISTRY.json': envelope(registry), 'PREPARED.json': envelope(prepared),
            'SOURCE_FREEZE.json': envelope(freeze), 'PREREGISTRATION.md': {'sha256': plan['preregistration_sha256']},
            'BLOCK_COMPLETE.json': envelope(block)}, runtime_files={'report_sampling.py': {'sha256': account.digest('runtime')}},
        runtime_report=dict(returncode=0, payload=dict(diagnostic_epoch_sha256=plan['diagnostic_epoch_sha256'],
            judge_epoch_sha256=plan['judge_epoch_sha256'], rows=rows)))
    return snapshot, plan


class CellTests(unittest.TestCase):
    def setUp(self):
        self.plan = basic_plan()
        self.cell = make_cell(self.plan)

    def metrics(self):
        return account.cell_metrics(self.cell, self.plan)

    def test_replayed_new_pixel_is_counted_once(self):
        result = self.metrics()
        self.assertEqual((result['distinct_scored'], result['distinct_accepted'], result['new_pixels']), (1, 1, 1))
        self.assertEqual(result['diagnostics']['returned_new_pixel_statuses'], 3)
        self.assertEqual(result['diagnostics']['replayed_returns'], 2)

    def test_cached_outcomes_are_not_new_discoveries(self):
        for index in (3, 5):
            self.cell['events'][index]['score']['results'][0]['result'].update(cached=True, replayed=False)
        self.assertEqual(self.metrics()['new_pixels'], 1)

    def test_identical_status_without_replay_flag_still_deduplicates(self):
        for index in (1, 3, 5):
            del self.cell['events'][index]['score']['results'][0]['result']['replayed']
        self.assertEqual((self.metrics()['new_pixels'], self.metrics()['distinct_scored']), (1, 1))

    def test_cache_before_original_resolves_once(self):
        for index in (1, 3, 5):
            self.cell['events'][index]['score']['results'][0]['result']['replayed'] = index != 5
        self.assertEqual(self.metrics()['new_pixels'], 1)

    def test_orphan_replay_is_unknown_not_new(self):
        self.cell['events'][1]['score']['results'][0]['result']['replayed'] = True
        with self.assertRaisesRegex(account.EvidenceError, 'orphan'):
            self.metrics()

    def test_duplicate_event_not_tokens_or_attempts(self):
        self.cell['events'].insert(2, deepcopy(self.cell['events'][1]))
        metrics = self.metrics()
        self.assertEqual((metrics['generated_tokens'], metrics['act_attempts']), (1024, 3))
        self.assertEqual(metrics['diagnostics']['duplicate_events'], 1)

    def test_conflicting_event_rejected(self):
        clone = deepcopy(self.cell['events'][1])
        clone['score']['results'][0]['result']['rank'] = 1
        self.cell['events'].append(clone)
        with self.assertRaisesRegex(account.EvidenceError, 'conflicting_duplicate_event'):
            self.metrics()

    def test_genuine_generation_with_same_text_still_counts_tokens(self):
        self.assertEqual((self.metrics()['generated_tokens'], self.metrics()['act_attempts']), (1024, 3))

    def test_rankless_then_scored_retry_counts_scored_once(self):
        self.cell['events'][1]['score']['results'][0]['result'] = dict(status='error', error=dict(code='provider_error'))
        self.cell['events'][3]['score']['results'][0]['result']['replayed'] = False
        metrics = self.metrics()
        self.assertEqual((metrics['distinct_scored'], metrics['new_pixels'], metrics['rankless_outcomes']), (1, 1, 0))
        self.assertEqual(metrics['diagnostics']['rankless_fresh_attempts'], 1)

    def test_relevance_failure_not_accepted_despite_rank(self):
        for index in (1, 3, 5):
            self.cell['events'][index]['score']['results'][0]['result'].update(accepted=False, status='rejected', pixel_id=None)
        metrics = self.metrics()
        self.assertEqual((metrics['distinct_scored'], metrics['distinct_accepted'], metrics['new_pixels']), (1, 0, 0))

    def test_missing_acceptance_not_inferred_from_rank(self):
        for index in (1, 3, 5):
            del self.cell['events'][index]['score']['results'][0]['result']['accepted']
        with self.assertRaisesRegex(account.EvidenceError, 'explicit'):
            self.metrics()

    def test_conflicting_scored_outcome(self):
        self.cell['events'][3]['score']['results'][0]['result'].update(rank=19, replayed=False)
        with self.assertRaisesRegex(account.EvidenceError, 'conflicting_scored'):
            self.metrics()

    def test_conflicting_replayed_outcome(self):
        self.cell['events'][3]['score']['results'][0]['result']['rank'] = 19
        with self.assertRaisesRegex(account.EvidenceError, 'conflicting_cached_or_replayed'):
            self.metrics()

    def test_duplicate_pixel_id_for_different_caption_rejected(self):
        extra = deepcopy(self.cell['events'][1]['score']['results'][0])
        extra['caption_sha256'] = account.digest('other_caption')
        self.cell['events'][1]['score']['results'].append(extra)
        with self.assertRaisesRegex(account.EvidenceError, 'pixel_id_reused'):
            self.metrics()

    def test_rankless_errors_not_no_caption(self):
        for index in (1, 3, 5):
            self.cell['events'][index]['score']['results'][0]['result'] = dict(status='error', error=dict(code='provider_error'))
        metrics = self.metrics()
        self.assertEqual((metrics['rankless_outcomes'], metrics['acts_without_results']), (1, 0))
        self.assertEqual(metrics['rankless_by_status'], {'error': 1})
        self.assertEqual(metrics['returned_error_codes'], {'provider_error': 3})

    def test_no_caption_is_separate(self):
        for event in self.cell['events']:
            event['score']['results'] = []
        self.assertEqual(self.metrics()['acts_without_results'], 3)

    def test_mixed_epoch_rejected(self):
        self.cell['events'][0]['score']['judge_epoch_sha256'] = account.digest('different')
        with self.assertRaisesRegex(account.EvidenceError, 'mixed_score_epoch'):
            self.metrics()

    def test_overlapping_token_ranges_rejected(self):
        self.cell['events'][1]['origin']['generated_tokens_before'] = 0
        with self.assertRaisesRegex(account.EvidenceError, 'token_range'):
            self.metrics()

    def test_complete_shortfall_rejected(self):
        self.cell['generated_tokens'] = 1000
        with self.assertRaisesRegex(account.EvidenceError, 'shortfall'):
            self.metrics()

    def test_partial_receipt_retains_observed_tokens(self):
        self.cell.update(status='INCOMPLETE_ZERO_TOKEN_GENERATION', generated_tokens=384,
            events=self.cell['events'][:2])
        self.assertEqual((self.metrics()['generated_tokens'], self.metrics()['new_pixels']), (384, 1))

    def test_bool_not_token_integer(self):
        self.cell['events'][0]['actual_generated_tokens'] = True
        with self.assertRaisesRegex(account.EvidenceError, 'token'):
            self.metrics()


class BlockTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.plan = make_fixture()

    def audit(self):
        return account.audit(self.snapshot, self.plan)

    def test_complete_block_reconciles(self):
        report = self.audit()
        self.assertEqual((report['block_status'], report['actual_generated_tokens']), ('COMPLETE', 18432))
        self.assertEqual(report['runtime_reconciliation']['status'], 'MATCH')
        self.assertEqual(report['runtime_reconciliation']['comparisons'], 240)
        self.assertEqual(len(report['cells']), 18)
        self.assertEqual([row['sign'] for row in report['contrasts']], ['tie'] * 6)

    def test_scene_seed_arm_scoping(self):
        report = self.audit()
        self.assertEqual([arm['metrics']['new_pixels'] for arm in report['arms']], [6, 6, 6])

    def test_missing_cell_not_zero_filled(self):
        self.snapshot['jobs'][0]['cells'][0]['result'] = None
        report = self.audit()
        self.assertIsNone(report['actual_generated_tokens'])
        self.assertIsNone(report['seeds'][0]['metrics'])
        self.assertEqual(report['seeds'][0]['complete_cells_only']['generated_tokens'], 2048)
        self.assertEqual(report['seeds'][0]['missing_cells'], 1)
        self.assertEqual(report['contrasts'][0]['sign'], 'UNKNOWN')

    def test_partial_cell_not_promoted(self):
        reference = self.snapshot['jobs'][0]['cells'][0]['result']
        reference['payload'].update(status='INCOMPLETE_ZERO_TOKEN_GENERATION', generated_tokens=384,
            events=reference['payload']['events'][:2])
        refresh(reference)
        report = self.audit()
        self.assertEqual(report['seeds'][0]['partial_cells'], 1)
        self.assertEqual(report['seeds'][0]['observed_valid_cells_only']['generated_tokens'], 2432)
        self.assertIsNone(report['arms'][0]['metrics'])

    def test_duplicate_cell_not_counted_twice(self):
        self.snapshot['jobs'][0]['cells'].append(deepcopy(self.snapshot['jobs'][0]['cells'][0]))
        report = self.audit()
        self.assertEqual(report['arms'][0]['duplicate_cell_copies'], 1)
        self.assertEqual(report['arms'][0]['metrics']['generated_tokens'], 6144)

    def test_conflicting_cell_copies_not_arbitrarily_selected(self):
        copy = deepcopy(self.snapshot['jobs'][0]['cells'][0])
        copy['result']['sha256'] = account.digest('different')
        self.snapshot['jobs'][0]['cells'].append(copy)
        with self.assertRaisesRegex(account.EvidenceError, 'conflicting_duplicate_record'):
            self.audit()

    def test_tampered_projection_invalidates_cell(self):
        self.snapshot['jobs'][0]['cells'][0]['result']['payload']['generated_tokens'] = 2
        report = self.audit()
        self.assertEqual(report['cells'][0]['status'], 'INVALID_EVIDENCE')
        self.assertEqual(report['cells'][0]['issue'], 'projection_hash_mismatch')

    def test_wrong_loaded_source_is_unknown(self):
        loaded = self.snapshot['jobs'][1]['loaded']
        loaded['payload']['source_age']['absolute_sleep'] = 117
        refresh(loaded)
        report = self.audit()
        self.assertEqual(report['arms'][1]['provenance']['status'], 'UNKNOWN')
        self.assertEqual(report['contrasts'][0]['sign'], 'UNKNOWN')

    def test_changed_post_weights_is_unknown(self):
        complete = self.snapshot['jobs'][1]['complete']
        complete['payload']['unchanged_identity']['adapter_state_sha256'] = account.digest('changed')
        refresh(complete)
        self.assertIn('weight_identity_changed', self.audit()['arms'][1]['provenance']['reason'])

    def test_result_complete_copy_mismatch(self):
        complete = self.snapshot['jobs'][0]['complete']
        complete['payload']['cells'][0]['source_object_sha256'] = account.digest('different')
        refresh(complete)
        self.assertEqual(self.audit()['arms'][0]['provenance']['reason'], 'result_complete_content_mismatch')

    def test_missing_loaded_receipt_not_verified(self):
        self.snapshot['jobs'][0]['loaded'] = None
        self.assertEqual(self.audit()['arms'][0]['provenance']['status'], 'UNKNOWN')

    def test_parent_free_flags_checked(self):
        loaded = self.snapshot['jobs'][0]['loaded']
        loaded['payload']['parent_tokens'] = 1
        refresh(loaded)
        self.assertEqual(self.audit()['arms'][0]['provenance']['reason'], 'parent_assistance_present')

    def test_runtime_discrepancy_exposed(self):
        self.snapshot['runtime_report']['payload']['rows'][0]['complete_cells_only']['new_pixels'] = 999
        report = self.audit()
        self.assertEqual(report['runtime_reconciliation']['status'], 'DIFFERENCE')
        self.assertEqual(report['runtime_reconciliation']['discrepancies'][0]['independent'], 3)

    def test_unsuccessful_role_exit_invalidates_completion(self):
        verification = self.snapshot['jobs'][0]['completion_verified']
        verification['payload']['unit_states']['judge']['ExecMainStatus'] = '1'
        refresh(verification)
        self.assertEqual(self.audit()['arms'][0]['provenance']['reason'], 'model_roles_not_successfully_exited')

    def test_runtime_missing_scene_detected(self):
        self.snapshot['runtime_report']['payload']['rows'][0]['cells'].pop()
        self.assertEqual(self.audit()['runtime_reconciliation']['status'], 'DIFFERENCE')

    def test_runtime_report_unavailable_not_match(self):
        self.snapshot['runtime_report'] = dict(returncode=1, payload=None)
        self.assertEqual(self.audit()['runtime_reconciliation']['status'], 'UNKNOWN')

    def test_no_block_receipt_not_claimed_complete(self):
        self.snapshot['documents']['BLOCK_COMPLETE.json'] = None
        self.assertEqual(self.audit()['block_status'], 'UNKNOWN')

    def test_predeclared_registry_binding(self):
        self.snapshot['documents']['REGISTRY.json']['sha256'] = account.digest('other')
        with self.assertRaisesRegex(account.EvidenceError, 'registry_changed'):
            self.audit()

    def test_all_markdown_cells_present(self):
        markdown = account.markdown(self.audit())
        self.assertEqual(markdown.count('| COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET |'), 18)
        self.assertIn('NOT independent training replication', markdown)


class ExportTests(unittest.TestCase):
    def test_projection_omits_caption_and_scalar_score(self):
        cell = make_cell(basic_plan())
        outcome = cell['events'][1]['score']['results'][0]['result']
        outcome.update(matching_caption='synthetic private text', raw_score=987.123,
            nearest_similarity=0.8)
        cell['events'][1]['score']['feedback'] = 'private text'
        projected = export_public.project_cell(cell)
        text = str(projected)
        self.assertNotIn('private text', text)
        self.assertNotIn('987.123', text)
        self.assertIn('caption_sha256', text)

    def test_complete_projection_binds_full_result_hash(self):
        cell = make_cell(basic_plan())
        result = export_public.project_complete(dict(cells=[cell]))
        self.assertEqual(result['cells'][0]['source_object_sha256'], account.digest(cell))
        self.assertNotIn('events', str(result))


class AuthenticSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).parent
        path = root / 'PUBLIC_SNAPSHOT_1429.json'
        if not path.exists():
            raise unittest.SkipTest('authentic public snapshot not collected yet')
        cls.snapshot = json.loads(path.read_text())
        cls.plan = json.loads((root / 'PLAN.json').read_text())
        cls.report = account.audit(cls.snapshot, cls.plan)

    def test_all_authentic_cells_complete_and_bound(self):
        self.assertEqual(self.report['block_status'], 'COMPLETE')
        self.assertEqual(self.report['actual_generated_tokens'], 18432)
        self.assertEqual(len(self.report['cells']), 18)
        self.assertTrue(all(arm['provenance']['status'] == 'VERIFIED_RECORDED_PROVENANCE'
            for arm in self.report['arms']))

    def test_all_authentic_seeds_and_signs(self):
        self.assertEqual([(row['metrics']['distinct_scored'], row['metrics']['distinct_accepted'],
            row['metrics']['new_pixels']) for row in self.report['seeds']],
            [(55, 42, 23), (50, 39, 25), (67, 44, 28), (84, 35, 29), (74, 37, 15), (94, 44, 23)])
        self.assertEqual([row['delta_new_pixels'] for row in self.report['contrasts']], [5, -8, 13, 4, -2, 6])

    def test_authentic_replay_inflation_not_carried_into_new_pixels(self):
        self.assertEqual([arm['metrics']['diagnostics']['replayed_returns'] for arm in self.report['arms']], [78, 10, 11])
        self.assertEqual([arm['metrics']['diagnostics']['returned_new_pixel_statuses'] for arm in self.report['arms']], [92, 61, 39])
        self.assertEqual([arm['metrics']['new_pixels'] for arm in self.report['arms']], [48, 57, 38])

    def test_authentic_runtime_report_matches(self):
        self.assertEqual(self.report['runtime_reconciliation'], dict(status='MATCH', comparisons=240, discrepancies=[]))


if __name__ == '__main__':
    unittest.main()
