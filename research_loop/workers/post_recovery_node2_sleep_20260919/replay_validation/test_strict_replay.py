"""Synthetic comparison only: no model, optimizer, journal scan or native imports."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import strict_replay as replay


def fixture(update_count=3, optimizer_steps=10):
    journal = 'synthetic-journal'
    previous = '0' * 64
    index = 100
    def envelope(kind, document):
        nonlocal previous, index
        value = dict(schema=replay.JOURNAL_SCHEMA, journal_id=journal, index=index,
            kind=kind, document=deepcopy(document), previous_sha256=previous)
        value['sha256'] = replay.digest(value)
        previous = value['sha256']
        index += 1
        return dict(record=value, intent=dict(schema=value['schema'], journal_id=journal, index=value['index'],
            previous_sha256=value['previous_sha256'], record_sha256=value['sha256']))
    def saved(state):
        return dict(state=deepcopy(state), sha256=replay.digest(state))
    checkpoint = dict(optimizer_steps=optimizer_steps, base_sha256=replay.digest('base'),
        adapter_state_sha256=replay.digest('actual_adapter'),
        checkpoint_sha256=dict(adapter=replay.digest('adapter_files'), optimizer=replay.digest('optimizer_rng'),
            rng=replay.digest('optimizer_rng')))
    model = replay.digest(checkpoint['checkpoint_sha256'])
    rows = [dict(source_sha256=replay.digest('old_row'), token_ids=[9], target='old', prefix=[], model_state_sha256=model)]
    state = dict(rows=deepcopy(rows), sleep_frontier=1, pending=None, model_state_sha256=model,
        history=dict(working_state={'retained': 'exact private fixture'}, events=[]))
    complete = envelope('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=5, checkpoint=checkpoint,
        checkpoint_sha256=checkpoint['checkpoint_sha256'], resume_state=saved(state)))
    decoder = dict(temperature=0.7, top_p=0.9, repetition_penalty=1.0, no_repeat_ngram_size=0)
    generations, generated = [], []
    for offset in range(3):
        request = dict(schema=replay.STREAM_SCHEMA, split='TRAIN', messages=[dict(role='user', content=f'fixture {offset}')],
            segment=offset + 1, prompt_tokens=10, max_new_tokens=8, deadline_unix=1789927200,
            started_unix=1000.0 + offset, history_sha256=replay.digest(state['history']),
            render_receipt=dict(token_count=10, all_history_tokens_masked=True),
            model_state_sha256=model, parent_wait_seconds=0, retry_allowed=False)
        request_sha = replay.digest(request)
        state.update(rows=deepcopy(rows), pending=request_sha)
        request['resume_state'] = saved(state)
        response = dict(raw=f'actual fixture {offset}', token_ids=[10 + offset, 20, 2], terminal=True, truncated=False,
            prompt_tokens=10, prompt_token_ids_sha256=replay.digest([1] * 10),
            adapter_state_sha256=checkpoint['adapter_state_sha256'], base_sha256=checkpoint['base_sha256'], decoder=decoder)
        receipt = dict(schema=replay.STREAM_SCHEMA, request_sha256=request_sha, response=response,
            finished_unix=1010.0 + offset, raw_saved_before_validation=True)
        generations.append(dict(request=envelope('REQUEST', request), response=envelope('RESPONSE', receipt)))
        generated.append(dict(request=deepcopy(request), model_response=deepcopy(response)))
        rows.append(dict(source_sha256=replay.digest(receipt), model_state_sha256=model, target=response['raw'],
            token_ids=response['token_ids'], prefix=request['messages']))
    state.update(rows=deepcopy(rows), pending='sleep:' + replay.digest([row['source_sha256'] for row in rows[1:]]))
    sleep = [envelope('SLEEP_REQUEST', dict(cycle=6, resume_state=saved(state))),
        envelope('SLEEP_RECIPE', dict(new_presentations=16, selected_old_rows=0, anchor_lambda=0.25)),
        envelope('TARGET_ELIGIBILITY', dict(new_row_sha256=[row['source_sha256'] for row in rows[1:]],
            rehearsal_row_sha256=[], raw_modified=False))]
    updates = []
    for offset in range(update_count):
        updates.append(envelope('UPDATE', dict(optimizer_step=optimizer_steps + offset + 1,
            source_sha256=rows[1 + offset % 3]['source_sha256'], finished_unix=2000.0 + offset,
            losses=[dict(kind='NEW', mean_loss=0.125, objective_weight=0.75, target_tokens=3)] +
                [dict(kind='ANCHOR:' + family, mean_loss=0.0625, objective_weight=0.0625, target_tokens=2)
                    for family in ('code', 'concise_answer', 'math', 'simulated_tools')])))
    reference = dict(schema=replay.CASE_SCHEMA, life_id='synthetic', journal_id=journal,
        source_pins={'fixture_native.py': replay.digest('source')}, decoder=decoder,
        complete=complete, generations=generations, sleep_inputs=sleep, updates=updates)
    observed = dict(binding=dict(source_pins_sha256=replay.digest(reference['source_pins']),
        checkpoint_reference_sha256=model), generations=generated,
        sleep_inputs=[dict(kind=item['record']['kind'], document=deepcopy(item['record']['document'])) for item in sleep],
        updates=[dict(deepcopy(item['record']['document']), finished_unix=3000.0 + offset)
            for offset, item in enumerate(updates)])
    return reference, observed


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.reference, self.observed = fixture()
        self.pin = replay.digest(self.reference)

    def validate(self):
        return replay.validate_replay(self.reference, self.observed, reference_sha256=self.pin)

    def test_match_is_only_behavioral_consistency_and_preserves_inputs(self):
        before = deepcopy((self.reference, self.observed))
        result = self.validate()
        self.assertEqual(result['status'], 'MATCHED_LOGGED_RECEIPTS_ONLY')
        self.assertEqual(result['matched_generation_receipts'], 3)
        self.assertEqual(result['matched_UPDATE_receipts'], 3)
        for name in ('exact_resident_continuity_claimed', 'optimizer_state_equivalence_proven',
                'RNG_state_equivalence_proven', 'unlogged_rng_calls_excluded', 'recovery_authorized',
                'checkpoint_binary_verification_performed', 'full_journal_verified', 'pending_sleep_reconciled'):
            self.assertIs(result[name], False)
        self.assertEqual((self.reference, self.observed), before)

    def test_only_UPDATE_finished_unix_is_excluded_and_differences_are_reported(self):
        result = self.validate()
        self.assertEqual(result['intentionally_excluded_UPDATE_fields'], ['finished_unix'])
        self.assertEqual(result['UPDATE_timing_comparisons'][0], dict(optimizer_step=11,
            original_finished_unix=2000.0, replay_finished_unix=3000.0, timing_differs=True))

    def test_no_mutable_reference_or_source_override(self):
        self.reference['source_pins']['fixture_native.py'] = replay.digest('changed')
        with self.assertRaisesRegex(replay.ReplayDivergence, 'pinned_reference'):
            self.validate()

    def test_declared_replay_source_and_checkpoint_must_match(self):
        for name in self.observed['binding']:
            with self.subTest(name=name):
                altered = deepcopy(self.observed)
                altered['binding'][name] = 'f' * 64
                with self.assertRaisesRegex(replay.ReplayDivergence, 'declared_source_or_checkpoint'):
                    replay.validate_replay(self.reference, altered, reference_sha256=self.pin)

    def test_generation_tokens_raw_prompt_model_and_decoder_are_all_exact(self):
        replacements = dict(raw='same tokens but altered text', token_ids=[11, 20, 2], terminal=False,
            truncated=True, prompt_tokens=11, prompt_token_ids_sha256='f' * 64,
            adapter_state_sha256='e' * 64, base_sha256='d' * 64, decoder={})
        for key, value in replacements.items():
            with self.subTest(key=key):
                altered = deepcopy(self.observed)
                altered['generations'][0]['model_response'][key] = value
                with self.assertRaisesRegex(replay.ReplayDivergence, 'generation_token'):
                    replay.validate_replay(self.reference, altered, reference_sha256=self.pin)

    def test_request_time_history_state_and_flags_are_not_normalized(self):
        for key, value in dict(started_unix=5000.0, messages=[], history_sha256='f' * 64,
                retry_allowed=True, resume_state={}).items():
            with self.subTest(key=key):
                altered = deepcopy(self.observed)
                altered['generations'][0]['request'][key] = value
                with self.assertRaisesRegex(replay.ReplayDivergence, 'logical_REQUEST'):
                    replay.validate_replay(self.reference, altered, reference_sha256=self.pin)

    def test_generation_failure_precedes_any_UPDATE_validation(self):
        self.observed['generations'][0]['model_response']['raw'] = 'divergent'
        with patch.object(replay, 'compare_update', side_effect=AssertionError('must_not_reach_training')) as compare:
            with self.assertRaises(replay.ReplayDivergence):
                self.validate()
            compare.assert_not_called()

    def test_missing_extra_or_reordered_generations_refuse(self):
        for altered in (self.observed['generations'][:-1], self.observed['generations'] * 2,
                list(reversed(self.observed['generations']))):
            with self.subTest(count=len(altered)):
                observed = deepcopy(self.observed)
                observed['generations'] = altered
                with self.assertRaises(replay.ReplayDivergence):
                    replay.validate_replay(self.reference, observed, reference_sha256=self.pin)

    def test_loss_has_no_tolerance_and_every_ordered_component_is_compared(self):
        for key, value in dict(mean_loss=0.12500000000000003, objective_weight=0.7500000000000001,
                target_tokens=4, kind='REHEARSAL').items():
            with self.subTest(key=key):
                altered = deepcopy(self.observed)
                altered['updates'][0]['losses'][0][key] = value
                with self.assertRaisesRegex(replay.ReplayDivergence, 'UPDATE_behavioral'):
                    replay.validate_replay(self.reference, altered, reference_sha256=self.pin)

    def test_loss_order_source_and_optimizer_count_refuse(self):
        for key, value in dict(losses=list(reversed(self.observed['updates'][0]['losses'])),
                source_sha256='f' * 64, optimizer_step=12).items():
            with self.subTest(key=key):
                altered = deepcopy(self.observed)
                altered['updates'][0][key] = value
                with self.assertRaises(replay.ReplayDivergence):
                    replay.validate_replay(self.reference, altered, reference_sha256=self.pin)

    def test_unknown_UPDATE_or_loss_fields_refuse_even_when_matching_on_both_sides(self):
        original = deepcopy(self.reference['updates'][0]['record']['document'])
        for location in ('update', 'loss'):
            changed = deepcopy(original)
            (changed if location == 'update' else changed['losses'][0])['ignored_new_field'] = 1
            with self.assertRaises(replay.ReplayDivergence):
                replay.compare_update(changed, changed, 11)

    def test_nonfinite_boolean_and_float_step_types_refuse(self):
        for key, value in (('finished_unix', float('nan')), ('finished_unix', True),
                ('optimizer_step', True), ('optimizer_step', 11.0)):
            changed = deepcopy(self.observed['updates'][0])
            changed[key] = value
            with self.assertRaises(replay.ReplayDivergence):
                replay.compare_update(self.reference['updates'][0]['record']['document'], changed, 11)
        changed = deepcopy(self.observed['updates'][0])
        changed['losses'][0]['mean_loss'] = float('inf')
        with self.assertRaises(replay.ReplayDivergence):
            replay.compare_update(self.reference['updates'][0]['record']['document'], changed, 11)
        with self.assertRaisesRegex(replay.ReplayDivergence, 'typed_expected'):
            replay.compare_update(self.reference['updates'][0]['record']['document'], changed, True)

    def test_actual_node2_loss_shapes_are_supported_not_tensor_state_receipts(self):
        path = Path(__file__).parent / 'source_evidence_1789790199409689539/RECEIPT.json'
        evidence = json.loads(path.read_bytes())
        for life in evidence['lives']:
            original = life['selected_records'][-1]['update_document']
            replay.validate_update(original)
            result = replay.compare_update(original, dict(original, finished_unix=original['finished_unix'] + 60),
                original['optimizer_step'])
            self.assertTrue(result['timing_differs'])
            self.assertEqual(set(original), replay.UPDATE_KEYS)

    def test_downloaded_source_evidence_remains_exact(self):
        folder = Path(__file__).parent / 'source_evidence_1789790199409689539'
        raw = (folder / 'RECEIPT.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            '782e1a4f110d1a15ac4c6462cfe5b81cc23997896bb3365d7e45c1f63f054fd7')
        evidence = json.loads(raw)
        self.assertEqual([life['life'] for life in evidence['lives']], ['C0', 'Astra7'])
        for life in evidence['lives']:
            self.assertEqual(len(life['source_files']), 10)
            self.assertEqual([entry['kind'] for entry in life['selected_records']],
                ['REQUEST', 'RESPONSE', 'UPDATE'])
            for source in life['source_files']:
                with self.subTest(life=life['life'], source=source['relative_path']):
                    preimage = folder / life['life'] / source['relative_path']
                    self.assertEqual(hashlib.sha256(preimage.read_bytes()).hexdigest(), source['sha256'])

    def test_C0_and_Astra7_prefix_counts_are_not_deduplicated_or_new_checkpoints(self):
        for steps, count, expected in ((8412, 48, 8460), (9644, 29, 9673)):
            reference, observed = fixture(count, steps)
            result = replay.validate_replay(reference, observed, reference_sha256=replay.digest(reference))
            self.assertEqual(result['matched_UPDATE_receipts'], count)
            self.assertEqual(result['last_matched_optimizer_step'], expected)
            self.assertEqual(result['saved_optimizer_steps'], steps)
            self.assertEqual(len(result['preserved_new_row_sha256']), 3)
            self.assertFalse(result['exact_resident_continuity_claimed'])

    def test_short_extra_or_reordered_UPDATE_prefix_refuses(self):
        for updates in (self.observed['updates'][:-1], self.observed['updates'] * 2,
                list(reversed(self.observed['updates']))):
            observed = deepcopy(self.observed)
            observed['updates'] = updates
            with self.assertRaises(replay.ReplayDivergence):
                replay.validate_replay(self.reference, observed, reference_sha256=self.pin)

    def test_every_sleep_input_and_new_row_is_preserved(self):
        for position in range(3):
            observed = deepcopy(self.observed)
            observed['sleep_inputs'][position]['document'] = {}
            with self.assertRaisesRegex(replay.ReplayDivergence, 'sleep_input'):
                replay.validate_replay(self.reference, observed, reference_sha256=self.pin)

    def test_original_record_and_intent_corruption_refuse(self):
        for part in ('record', 'intent'):
            reference = deepcopy(self.reference)
            reference['updates'][0][part]['index'] += 1
            with self.assertRaises(replay.ReplayDivergence):
                replay.validate_replay(reference, self.observed, reference_sha256=replay.digest(reference))

    def test_snapshot_hash_corruption_refuses_even_with_resealed_record(self):
        reference = deepcopy(self.reference)
        pair = reference['generations'][0]['request']
        pair['record']['document']['resume_state']['state']['rows'] = []
        pair['record']['sha256'] = replay.digest({key: value for key, value in pair['record'].items() if key != 'sha256'})
        pair['intent']['record_sha256'] = pair['record']['sha256']
        with self.assertRaises(replay.ReplayDivergence):
            replay.validate_replay(reference, self.observed, reference_sha256=replay.digest(reference))

    def test_partial_or_rng_coverage_claim_fields_are_not_accepted(self):
        observed = deepcopy(self.observed)
        observed['generations'][0]['model_response']['interruption'] = {'cause': 'console'}
        with self.assertRaises(replay.ReplayDivergence):
            replay.validate_replay(self.reference, observed, reference_sha256=self.pin)
        self.observed['RNG_state_proven'] = True
        with self.assertRaises(replay.ReplayDivergence):
            self.validate()

    def test_malformed_types_duplicate_JSON_and_cycles_refuse(self):
        with self.assertRaises(replay.ReplayDivergence):
            replay.validate_replay({}, {}, reference_sha256='a' * 64)
        with self.assertRaises(replay.ReplayDivergence):
            replay.canonical({'tokens': (1, 2)})
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(replay.ReplayDivergence):
            replay.canonical(cycle)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'duplicate.json'
            path.write_text('{"step":1,"step":2}')
            with self.assertRaisesRegex(replay.ReplayDivergence, 'duplicate'):
                replay.load_bounded(path)

    def test_cli_compares_only_supplied_files_and_never_rewrites_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            reference_path = Path(temporary) / 'reference.json'
            observed_path = Path(temporary) / 'observed.json'
            reference_path.write_bytes(replay.canonical(self.reference))
            observed_path.write_bytes(replay.canonical(self.observed))
            before = (reference_path.read_bytes(), observed_path.read_bytes())
            command = [sys.executable, '-B', str(Path(replay.__file__)), '--reference', str(reference_path),
                '--reference-sha256', self.pin, '--observed', str(observed_path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(result.returncode, 0, result.stderr)
            verdict = json.loads(result.stdout)
            self.assertFalse(verdict['exact_resident_continuity_claimed'])
            self.assertEqual(verdict['observed_sha256'], replay.digest(self.observed))
            self.assertEqual((reference_path.read_bytes(), observed_path.read_bytes()), before)
            observed = deepcopy(self.observed)
            observed['updates'][0]['losses'][0]['mean_loss'] += 0.000000001
            observed_path.write_bytes(replay.canonical(observed))
            result = subprocess.run(command, capture_output=True, text=True, timeout=10,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
            self.assertEqual(reference_path.read_bytes(), before[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
