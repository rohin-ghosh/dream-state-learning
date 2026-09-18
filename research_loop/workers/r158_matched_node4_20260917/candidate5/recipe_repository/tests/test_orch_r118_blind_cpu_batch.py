from copy import deepcopy
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r118_blind_cpu_batch as batch
from tests import test_orch_r118_cpu_readout_judge as fixtures


class ScriptedBackend:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def step(self, **arguments):
        self.calls.append(deepcopy(arguments))
        result = next(self.outputs)
        if isinstance(result, Exception):
            raise result
        return result


class BlindBatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contract = batch.decoder_contract('a'*64, 4, 8, 32, 10,
            versions={'torch':'fixture', 'transformers':'fixture'}, eos_token_ids=[2], pad_token_id=2)
        self.document = dict(kind='held', task_text='Public task.', child_text='I read the record.')
        self.item = self.item_for(self.document)

    def item_for(self, document):
        return dict(document=deepcopy(document), request=batch.judge.request(document),
            private_provenance=dict(parent_free=True, training_buffer=False,
                task_id='PRIVATE_TASK', checkpoint_sha256='PRIVATE_CHECKPOINT', outcome='PRIVATE_OUTCOME'))

    def decode(self, rows, caps, outputs, **options):
        backend = ScriptedBackend(outputs)
        arguments = dict(eos_token_ids=[2], pad_token_id=2, context_limit=32, deadline=10, clock=lambda:0)
        arguments.update(options)
        result = batch.decode_batch(rows, caps, backend, **arguments)
        return result, backend

    def annotation(self):
        return dict(status='COMPLETE', reason='', sentences=[dict(index=0, label='MAIN',
            legacy_template_check=False, evidence='record')], shift_sentence_indices=[], classes=[])

    def test_tokenizer_explicit_flat_return_before_dispatch(self):
        tokenizer = Mock()
        tokenizer.apply_chat_template.side_effect = lambda messages, **options: (
            [17, 23, 29] if options.get('return_dict') is False else {'input_ids': [17, 23, 29]})
        request = {'messages': [{'role': 'user', 'content': 'Synthetic visible observation.'}]}
        self.assertEqual(batch.tokenize_request(tokenizer, request), [17, 23, 29])
        tokenizer.apply_chat_template.assert_called_once_with(request['messages'], tokenize=True,
            add_generation_prompt=True, truncation=False, return_dict=False)

    def test_tokenizer_rejects_wrong_shape_without_coercion(self):
        for returned in ({'input_ids': [17]}, [[17]], [], [True], [17.0], [-1], ['17']):
            with self.subTest(returned=returned):
                tokenizer = Mock()
                tokenizer.apply_chat_template.return_value = returned
                with self.assertRaisesRegex(ValueError, 'exact_flat_token_list_before_claim'):
                    batch.tokenize_request(tokenizer, {'messages': []})

    def cache(self, group, *, termination='eos', tokens=None):
        path = self.root / 'prior/cache' / group['key']
        batch.write(path / 'CLAIM.json', dict(key=group['key'], request=group['request'], contract=group['contract']))
        raw = json.dumps(self.annotation())
        result = batch.original.interpret(group['document'], raw, True) if termination == 'eos' else batch.unresolved(termination)
        response = dict(key=group['key'], raw=raw, token_ids=[8, 2] if tokens is None else tokens,
            termination=termination, result=result)
        batch.write(path / 'RESPONSE.json', response)
        batch.write(path / 'RESULT.json', dict(response_sha256=batch.sha(path / 'RESPONSE.json')))
        batch.write(self.root / 'prior/TERMINAL.json', dict(status='COMPLETE'))
        return path

    def test_56_members_21_inputs_without_loss_or_private_visibility(self):
        items = []
        for index in range(56):
            item = self.item_for(dict(self.document, child_text=f'Observation {index%21}.'))
            item['private_provenance'].update(cycle=index//8, task_id=f'PRIVATE_TASK_{index}')
            items.append(item)
        groups = batch.group_documents(items, self.contract)
        self.assertEqual(len(groups), 21)
        self.assertEqual(sum(len(group['members']) for group in groups), 56)
        for group in groups:
            visible = json.dumps(group['request'])
            for secret in ('PRIVATE_TASK', 'PRIVATE_CHECKPOINT', 'PRIVATE_OUTCOME'):
                self.assertNotIn(secret, visible)
        results = {group['key']:dict(result=batch.unresolved('fixture')) for group in groups}
        rows = batch.expand_rows(groups, results)
        self.assertEqual([row['index'] for row in rows], list(range(56)))
        self.assertEqual([row['private_provenance'] for row in rows], [item['private_provenance'] for item in items])
        self.assertTrue(all(row['annotation']['result']['shifts'] is None for row in rows))

    def test_original_collect_reuses_actual_DEV_provenance_and_blind_schema(self):
        fixture = fixtures.ReadoutTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        documents = batch.original.collect(fixture.root, [0, 1])
        groups = batch.group_documents(documents, self.contract)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]['members']), 16)
        visible = json.dumps(groups[0]['request'])
        for secret in ('FINAL_MUST_NOT_LEAK', 'HIDDEN_VERDICT', 'ORACLE_SECRET', 'PRIVATE_SYSTEM'):
            self.assertNotIn(secret, visible)
        self.assertIn('Visible feedback', visible)

    def test_FINAL_rejected_by_unchanged_collector(self):
        fixture = fixtures.ReadoutTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.replace(fixture.root / 'readout_0000/HELD.json', scope='final')
        with self.assertRaisesRegex(ValueError, 'DEV_only'):
            batch.original.collect(fixture.root, [0])

    def test_extra_outcome_or_parent_keys_cannot_enter_blind_request(self):
        for field in ('parent_text', 'outcome', 'FINAL'):
            item = deepcopy(self.item)
            item['document'][field] = 'PRIVATE'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'allowlist'):
                batch.group_documents([item], self.contract)

    def test_wrong_request_or_training_provenance_rejected(self):
        item = deepcopy(self.item)
        item['request']['messages'][1]['content'] += 'injection'
        with self.assertRaisesRegex(ValueError, 'exact_blind_request'):
            batch.group_documents([item], self.contract)
        item = deepcopy(self.item)
        item['private_provenance']['training_buffer'] = True
        with self.assertRaisesRegex(ValueError, 'parent_free_annotation'):
            batch.group_documents([item], self.contract)

    def test_full_request_model_and_decoder_all_change_cache_key(self):
        key = batch.group_documents([self.item], self.contract)[0]['key']
        for field, value in [('model_manifest_sha256', 'b'*64), ('batch_size', 2),
                ('max_new_tokens', 7), ('versions', {'torch':'other', 'transformers':'fixture'})]:
            contract = dict(self.contract, **{field:value})
            self.assertNotEqual(batch.group_documents([self.item], contract)[0]['key'], key)
        item = self.item_for(dict(self.document, task_text='Different public context.'))
        self.assertNotEqual(batch.group_documents([item], self.contract)[0]['key'], key)

    def test_left_padding_mask_positions_do_not_depend_on_PAD_equals_EOS(self):
        padded = batch.left_pad([[10, 2, 11], [12]], 2)
        self.assertEqual(padded['input_ids'], [[10, 2, 11], [2, 2, 12]])
        self.assertEqual(padded['attention_mask'], [[1, 1, 1], [0, 0, 1]])
        self.assertEqual(padded['position_ids'], [[0, 1, 2], [0, 0, 0]])

    def test_EOS_finished_sequence_masked_while_other_continues(self):
        result, backend = self.decode([[10, 11], [12]], [4, 4], [[90, 2], [2, 99]])
        self.assertEqual(result, [dict(token_ids=[90, 2], termination='eos'), dict(token_ids=[2], termination='eos')])
        self.assertEqual(backend.calls[0]['input_ids'], [[10, 11], [2, 12]])
        self.assertEqual(backend.calls[0]['attention_mask'], [[1, 1], [0, 1]])
        self.assertTrue(backend.calls[0]['prefill'])
        self.assertEqual(backend.calls[1]['input_ids'], [[90], [2]])
        self.assertEqual(backend.calls[1]['attention_mask'], [[1, 1, 1], [0, 1, 0]])
        self.assertEqual(backend.calls[1]['position_ids'], [[2], [0]])
        self.assertFalse(backend.calls[1]['prefill'])

    def test_multiple_EOS_ids_no_extra_tokens_after_individual_finish(self):
        result, backend = self.decode([[1], [3]], [4, 4], [[99, 8], [50, 2]], eos_token_ids=[2, 99])
        self.assertEqual([row['token_ids'] for row in result], [[99], [8, 2]])
        self.assertEqual(len(backend.calls), 2)

    def test_per_sequence_cap_not_longest_batch_cap(self):
        result, backend = self.decode([[1], [3]], [1, 3], [[7, 8], [9, 2]])
        self.assertEqual(result[0], dict(token_ids=[7], termination='output_cap'))
        self.assertEqual(result[1], dict(token_ids=[8, 2], termination='eos'))
        self.assertEqual(backend.calls[1]['attention_mask'][0], [1, 0])

    def test_even_EOS_at_exact_cap_is_conservatively_UNRESOLVED(self):
        result, unused = self.decode([[1]], [1], [[2]])
        self.assertEqual(result[0]['termination'], 'output_cap')
        tokenizer = SimpleNamespace(decode=lambda *args, **kwargs:json.dumps(self.annotation()))
        classified = batch.classify(self.document, result[0], tokenizer)
        self.assertEqual(classified['result'], batch.unresolved('output_cap'))
        self.assertEqual(classified['token_ids'], [2])

    def test_input_overlimit_preserved_not_cropped_or_forwarded(self):
        result, backend = self.decode([[1]*30, [4]], [4, 4], [[2]])
        self.assertEqual(result[0], dict(token_ids=[], termination='input_context_bound'))
        self.assertEqual(backend.calls[0]['input_ids'], [[4]])
        self.assertEqual(result[1]['termination'], 'eos')

    def test_all_inputs_overlimit_no_forward(self):
        result, backend = self.decode([[1]*30], [4], [])
        self.assertFalse(backend.calls)
        self.assertEqual(result[0]['termination'], 'input_context_bound')

    def test_padded_cache_width_also_bounded(self):
        result, backend = self.decode([[1]*5, [4]], [1, 5], [], context_limit=6)
        self.assertFalse(backend.calls)
        self.assertTrue(all(row['termination'] == 'padded_batch_context_bound' for row in result))

    def test_deadline_before_forward_has_no_call(self):
        result, backend = self.decode([[1]], [4], [], clock=lambda:10)
        self.assertFalse(backend.calls)
        self.assertEqual(result[0]['termination'], 'deadline')

    def test_forward_crossing_deadline_retains_token_but_not_success(self):
        ticks = iter([0, 11])
        result, unused = self.decode([[1]], [4], [[2]], clock=lambda:next(ticks))
        self.assertEqual(result[0], dict(token_ids=[2], termination='deadline'))

    def test_forward_exception_keeps_partial_tokens_no_retry(self):
        result, backend = self.decode([[1]], [4], [[7], RuntimeError('fixture')])
        self.assertEqual(len(backend.calls), 2)
        self.assertEqual(result[0]['token_ids'], [7])
        self.assertEqual(result[0]['termination'], 'backend_error')
        self.assertEqual(result[0]['error_type'], 'RuntimeError')

    def test_progress_token_journal_callback_has_only_actual_emissions(self):
        events = []
        result, unused = self.decode([[1], [3]], [4, 4], [[2, 8], [9, 2]], on_step=events.append)
        self.assertEqual(events, [[dict(index=0, token_id=2, termination='eos'),
            dict(index=1, token_id=8, termination=None)], [dict(index=1, token_id=2, termination='eos')]])
        self.assertEqual(result[0]['token_ids'], [2])

    def test_torch_adapter_passes_explicit_CPU_mask_positions_and_cache(self):
        class Logits:
            device = SimpleNamespace(type='cpu')

            def __getitem__(self, key):
                return self

            def argmax(self, dim):
                self.dimension = dim
                return self

            def tolist(self):
                return [7, 2]

        tensor_calls = []
        def tensor(values, **kwargs):
            tensor_calls.append(dict(values=deepcopy(values), **kwargs))
            return values
        fake_torch = SimpleNamespace(tensor=tensor, long='int64', inference_mode=nullcontext,
            arange=lambda start, end, **kwargs:list(range(start, end)))
        cache = object()
        model = Mock(return_value=SimpleNamespace(logits=Logits(), past_key_values=cache))
        backend = batch.TorchGreedy(model, fake_torch)
        backend.step(**batch.left_pad([[10, 11], [12]], 2), prefill=True)
        first = model.call_args.kwargs
        self.assertEqual(first['cache_position'], [0, 1])
        self.assertIsNone(first['past_key_values'])
        self.assertEqual(first['attention_mask'], [[1, 1], [0, 1]])
        backend.step([[7], [2]], [[1, 1, 1], [0, 1, 0]], [[2], [0]], prefill=False)
        following = model.call_args.kwargs
        self.assertIs(following['past_key_values'], cache)
        self.assertEqual(following['cache_position'], [2])
        self.assertEqual(following['position_ids'], [[2], [0]])
        self.assertTrue(all(call['device'] == 'cpu' and call['dtype'] == 'int64' for call in tensor_calls))
        backend.step(**batch.left_pad([[10, 11], [12]], 2), prefill=True)
        self.assertIsNone(model.call_args.kwargs['past_key_values'])
        self.assertEqual(model.call_args.kwargs['cache_position'], [0, 1])

    def test_malformed_backend_output_not_silent_row_misalignment(self):
        result, unused = self.decode([[1], [3]], [4, 4], [[2]])
        self.assertTrue(all(row['termination'] == 'backend_error' for row in result))

    def test_empty_or_boolean_token_inputs_rejected(self):
        for rows in ([], [[]], [[True]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                batch.left_pad(rows, 2)

    def test_decoder_allocation_bounds(self):
        for count in (0, 5, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                batch.decoder_contract('a'*64, count, 8, 32, 10,
                    versions={'torch':'x', 'transformers':'x'}, eos_token_ids=[2], pad_token_id=2)
        self.assertEqual(self.contract['threads'], 16)
        self.assertEqual(self.contract['device'], 'cpu')
        self.assertFalse(self.contract['do_sample'])

    def test_schema_reuses_Main_UNRESOLVED_without_zero(self):
        for termination in ('deadline', 'output_cap', 'input_context_bound', 'backend_error'):
            tokenizer = SimpleNamespace(decode=lambda *args, **kwargs:json.dumps(self.annotation()))
            result = batch.classify(self.document, dict(token_ids=[8], termination=termination), tokenizer)
            self.assertIsNone(result['result']['departures_and_returns'])
            self.assertIsNone(result['result']['shifts'])
        tokenizer = SimpleNamespace(decode=lambda *args, **kwargs:'malformed')
        result = batch.classify(self.document, dict(token_ids=[8, 2], termination='eos'), tokenizer)
        self.assertEqual(result['result']['status'], 'UNRESOLVED')

    def test_exact_completed_cache_reused_without_model(self):
        group = batch.group_documents([self.item], self.contract)[0]
        path = self.cache(group)
        before = batch.sha(path / 'RESPONSE.json')
        result = batch.cached_result(group, batch.prior_attempts([self.root / 'prior']))
        self.assertEqual(result['disposition'], 'EXACT_CACHE')
        self.assertEqual(result['result']['status'], 'COMPLETE')
        self.assertEqual(batch.sha(path / 'RESPONSE.json'), before)

    def test_exact_UNRESOLVED_cache_stays_UNRESOLVED_no_second_attempt(self):
        group = batch.group_documents([self.item], self.contract)[0]
        self.cache(group, termination='deadline')
        result = batch.cached_result(group, batch.prior_attempts([self.root / 'prior']))
        self.assertEqual(result['disposition'], 'EXACT_CACHE')
        self.assertIsNone(result['result']['shifts'])

    def test_completed_legacy_or_decoder_mismatch_is_not_replayed(self):
        group = batch.group_documents([self.item], self.contract)[0]
        self.cache(group)
        other = batch.group_documents([self.item], dict(self.contract, batch_size=2))[0]
        result = batch.cached_result(other, batch.prior_attempts([self.root / 'prior']))
        self.assertEqual(result['disposition'], 'PRIOR_ATTEMPT_BLOCKED')
        self.assertEqual(len(result['prior_responses']), 1)
        self.assertIsNone(result['result']['shifts'])
        legacy = self.root / 'legacy'
        batch.write(legacy / 'TERMINAL.json', dict(status='COMPLETE'))
        batch.write(legacy / 'call_0000/REQUEST.json', group['request'])
        batch.write(legacy / 'call_0000/RESPONSE.json', dict(result={'status':'COMPLETE'}))
        self.assertEqual(batch.cached_result(group, batch.prior_attempts([legacy]))['disposition'], 'PRIOR_ATTEMPT_BLOCKED')

    def test_inflight_prior_run_forbidden_and_missing_result_not_replayed(self):
        group = batch.group_documents([self.item], self.contract)[0]
        prior = self.root / 'prior'
        batch.write(prior / 'cache' / group['key'] / 'CLAIM.json',
            dict(key=group['key'], request=group['request'], contract=group['contract']))
        with self.assertRaisesRegex(ValueError, 'prior_run_must_be_terminal'):
            batch.prior_attempts([prior])
        batch.write(prior / 'TERMINAL.json', dict(status='WALL_BOUND'))
        self.assertEqual(batch.cached_result(group, batch.prior_attempts([prior]))['disposition'], 'PRIOR_ATTEMPT_BLOCKED')

    def test_terminal_does_not_override_live_process_or_unverifiable_pid(self):
        prior = self.root / 'prior'
        batch.write(prior / 'TERMINAL.json', dict(status='COMPLETE'))
        batch.write(prior / 'STARTED.json', dict(pid=1248873))
        for error, message in ((None, 'prior_process_still_present'),
                (PermissionError(), 'prior_process_release_unverified')):
            with patch.object(batch.os, 'kill', side_effect=error), self.assertRaisesRegex(ValueError, message):
                batch.select_successor([self.item], [prior])
        with patch.object(batch.os, 'kill', side_effect=ProcessLookupError()) as probe:
            self.assertEqual(batch.select_successor([self.item], [prior])['never_attempted_inputs'], 1)
        probe.assert_called_with(1248873, 0)

    def test_terminal_does_not_override_held_runner_or_guard_lock(self):
        prior = self.root / 'prior'
        batch.write(prior / 'TERMINAL.json', dict(status='COMPLETE'))
        for name in ('RUNNER.lock', 'GUARD.lock'):
            with self.subTest(name=name):
                path = prior / name
                with path.open('w') as lock:
                    batch.fcntl.flock(lock, batch.fcntl.LOCK_EX | batch.fcntl.LOCK_NB)
                    with self.assertRaisesRegex(ValueError, 'prior_runner_lock_not_released'):
                        batch.select_successor([self.item], [prior])

    def test_successor_preserves_ten_complete_two_unresolved_and_all_charges(self):
        prior = self.root / 'legacy'
        batch.write(prior / 'TERMINAL.json', dict(status='WALL_BOUND'))
        batch.write(prior / 'PLAN.json', dict(decoder='original_unbatched'))
        items = []
        for index in range(14):
            item = self.item_for(dict(self.document, child_text=f'Observation {index}.'))
            items.extend([item, deepcopy(item)])
            if index < 13:
                path = prior / f'call_{index:04d}'
                batch.write(path / 'REQUEST.json', item['request'])
                if index < 12:
                    result = dict(status='COMPLETE', shifts=0) if index < 10 else batch.unresolved('deadline')
                    batch.write(path / 'RESPONSE.json', dict(result=result))
        before = batch.prior_inventory(prior)
        selection = batch.select_successor(items, [prior])
        self.assertEqual(selection['member_rows'], 28)
        self.assertEqual(selection['never_attempted_inputs'], 1)
        self.assertEqual(selection['previously_attempted_inputs'], 13)
        retained = [entry for row in selection['groups'] for entry in row['prior_attempts']]
        statuses = [entry['original_result']['status'] for entry in retained if 'original_result' in entry]
        self.assertEqual(statuses.count('COMPLETE'), 10)
        self.assertEqual(statuses.count('UNRESOLVED'), 2)
        self.assertEqual(retained[-1]['status'], 'CHARGED_WITHOUT_RESPONSE')
        self.assertTrue(all(entry['contract_kind'] == 'LEGACY_UNBATCHED' for entry in retained))
        self.assertTrue(all('PLAN.json' in entry['source_bindings'] for entry in retained))
        self.assertEqual(batch.prior_inventory(prior), before)

    def test_legacy_duplicate_keeps_original_annotation_separate_not_batch_equivalence(self):
        prior = self.root / 'legacy'
        batch.write(prior / 'TERMINAL.json', dict(status='COMPLETE'))
        batch.write(prior / 'call_0000/REQUEST.json', self.item['request'])
        old_result = dict(status='COMPLETE', shifts=7)
        batch.write(prior / 'call_0000/RESPONSE.json', dict(result=old_result))
        groups = batch.group_documents([self.item, deepcopy(self.item)], self.contract)
        result = batch.cached_result(groups[0], batch.prior_attempts([prior]))
        self.assertEqual(result['disposition'], 'PRIOR_ATTEMPT_BLOCKED')
        self.assertEqual(result['preserved_prior_annotations'][0]['original_result'], old_result)
        self.assertEqual(len(batch.expand_rows(groups, {groups[0]['key']:result})), 2)
        self.assertIsNone(result['result']['shifts'])

    def test_fresh_only_scope_excludes_all_legacy_members_and_preserves_original_indices(self):
        prior = self.root / 'legacy'
        batch.write(prior / 'TERMINAL.json', dict(status='WALL_BOUND'))
        items = []
        for index in range(56):
            identity = index % 21
            item = self.item_for(dict(self.document, child_text=f'Observation {identity}.'))
            items.append(item)
            if index < 11:
                batch.write(prior / f'call_{index:04d}/REQUEST.json', item['request'])
        selection = batch.select_successor(items, [prior])
        groups = batch.execution_groups(items, self.contract, selection, never_attempted_only=True)
        self.assertEqual(len(groups), 10)
        self.assertTrue(all(not batch.cached_result(group, batch.prior_attempts([prior])) for group in groups))
        results = {group['key']:dict(result=batch.unresolved('not_launched')) for group in groups}
        rows = batch.expand_rows(groups, results)
        expected = [index for index in range(56) if index % 21 >= 11]
        self.assertEqual([row['index'] for row in rows], expected)
        self.assertEqual(len(batch.execution_groups(items, self.contract, selection,
            never_attempted_only=False)), 21)

    def test_changed_cached_response_hash_fails_without_regeneration(self):
        group = batch.group_documents([self.item], self.contract)[0]
        path = self.cache(group)
        (path / 'RESPONSE.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'cached_response_hash'):
            batch.cached_result(group, batch.prior_attempts([self.root / 'prior']))

    def test_prior_inventory_binds_complete_results_and_reservations(self):
        group = batch.group_documents([self.item], self.contract)[0]
        path = self.cache(group)
        before = batch.prior_inventory(self.root / 'prior')
        self.assertIn('TERMINAL.json', before)
        self.assertEqual(len(before), 4)
        (path / 'CLAIM.json').write_text('{}')
        self.assertNotEqual(batch.prior_inventory(self.root / 'prior'), before)

    def test_cache_requires_actual_EOS_not_just_valid_JSON(self):
        group = batch.group_documents([self.item], self.contract)[0]
        self.cache(group, tokens=[8, 9])
        with self.assertRaisesRegex(ValueError, 'cached_actual_EOS'):
            batch.cached_result(group, batch.prior_attempts([self.root / 'prior']))

    def test_raw_runtime_refuses_VM_or_GPU_visibility(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':'0'}):
            with self.assertRaisesRegex(ValueError, 'no_visible_GPU'):
                batch.node_environment(self.root)
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':''}):
            with self.assertRaisesRegex(ValueError, 'node_local_raw_only'):
                batch.node_environment(self.root)

    def test_run_needs_new_published_allocation_before_model_import(self):
        batch.write(self.root / 'PLAN.json', dict(schema=batch.SCHEMA, source_files=batch.source_pins(), deadline_unix=100))
        batch.write(self.root / 'PUBLICATION.json', dict(authorized=False))
        with patch.object(batch, 'node_environment'), self.assertRaisesRegex(ValueError, 'published_allocation'):
            batch.run(self.root)
        self.assertFalse((self.root / 'STARTED.json').exists())

    def test_prepare_preserves_main_inventory_prior_hashes_and_absolute_scope(self):
        fixture = fixtures.ReadoutTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        prior = self.root / 'old'
        batch.write(prior / 'TERMINAL.json', dict(status='WALL_BOUND'))
        batch.write(prior / 'call_0000/REQUEST.json', self.item['request'])
        model = self.root / batch.original.REVISION
        model.mkdir()
        for index in range(8):
            (model / f'model-{index}.safetensors').write_bytes(b'FIXTURE_NOT_MODEL')
        manifest = self.root / 'source.json'
        batch.write(manifest, batch.source_pins())
        target = self.root / 'future'
        prior_hash = batch.sha(prior / 'TERMINAL.json')
        with patch.object(batch, 'node_environment'), patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':''}), \
                patch.object(batch.time, 'time', return_value=75):
            batch.prepare(target, fixture.root, [0, 1], model, manifest, 100, prior_roots=[prior],
                never_attempted_only=True)
        plan = batch.read(target / 'PLAN.json')
        self.assertEqual(plan['deadline_unix'], 100)
        self.assertEqual(plan['batch_size'], 4)
        self.assertEqual(plan['threads'], 16)
        self.assertTrue(plan['never_attempted_only'])
        execution = batch.read(target / 'EXECUTION_SELECTION.json')
        self.assertEqual(execution['unique_inputs'], plan['max_new_calls'])
        self.assertFalse(execution['legacy_annotations_inherited'])
        self.assertEqual(plan['prior_bindings'][str(prior)], batch.prior_inventory(prior))
        self.assertEqual(batch.sha(prior / 'TERMINAL.json'), prior_hash)
        self.assertEqual(len(batch.read(target / 'inputs/DOCUMENTS.json')), 16)
        self.assertFalse((target / 'STARTED.json').exists())
        self.assertFalse((target / 'PUBLICATION.json').exists())

    def test_prepare_cannot_omit_historical_run_accounting(self):
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=75):
            with self.assertRaisesRegex(ValueError, 'prior_run_inventory_required'):
                batch.prepare(self.root / 'future', None, [0], None, None, 100)

    def test_future_run_with_fake_model_preserves_rows_and_exact_cache_no_replay(self):
        fixture = fixtures.ReadoutTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        prior = self.root / 'legacy'
        batch.write(prior / 'TERMINAL.json', dict(status='COMPLETE'))
        batch.write(prior / 'call_0000/REQUEST.json', self.item['request'])
        model_dir = self.root / batch.original.REVISION
        model_dir.mkdir()
        for index in range(8):
            (model_dir / f'model-{index}.safetensors').write_bytes(b'FAKE_TEST_SHARD')
        source_manifest = self.root / 'source.json'
        batch.write(source_manifest, batch.source_pins())
        annotation_raw = json.dumps(self.annotation())

        class Logits:
            device = SimpleNamespace(type='cpu')

            def __init__(self, token):
                self.token = token

            def __getitem__(self, key):
                return self

            def argmax(self, dim):
                return self

            def tolist(self):
                return [self.token]

        parameter = SimpleNamespace(device=SimpleNamespace(type='cpu'), requires_grad=False, _version=0)
        calls = []
        class Model:
            generation_config = SimpleNamespace(eos_token_id=[2])
            config = SimpleNamespace(max_position_embeddings=16384)

            def requires_grad_(self, value):
                parameter.requires_grad = value

            def eval(self):
                return self

            def parameters(self):
                return [parameter]

            def named_parameters(self):
                return [('fixture', parameter)]

            def __call__(self, **kwargs):
                calls.append(deepcopy(kwargs))
                return SimpleNamespace(logits=Logits(8 if len(calls)%2 else 2), past_key_values='cache')

        fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda:False),
            set_num_threads=Mock(), set_num_interop_threads=Mock(), get_num_threads=lambda:16,
            bfloat16='bf16', long='int64', inference_mode=nullcontext,
            tensor=lambda values, **kwargs:values,
            arange=lambda start, end, **kwargs:list(range(start, end)))
        tokenizer = SimpleNamespace(pad_token_id=2, apply_chat_template=lambda *args, **kwargs:[10, 11],
            decode=lambda *args, **kwargs:annotation_raw)
        model_loader = Mock(return_value=Model())
        fake_transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=tokenizer)),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=model_loader))
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=75), \
                patch.object(batch.os, 'kill', side_effect=ProcessLookupError()), \
                patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':''}), \
                patch.dict(sys.modules, {'torch':fake_torch, 'transformers':fake_transformers}), \
                patch.object(batch.importlib.metadata, 'version', return_value='fixture'):
            for name, prior_roots in [('first', [prior]), ('cached', [self.root / 'first']),
                    ('cached_again', [self.root / 'cached'])]:
                target = self.root / name
                batch.prepare(target, fixture.root, [0, 1], model_dir, source_manifest, 100, prior_roots=prior_roots)
                batch.write(target / 'PUBLICATION.json', dict(authorized=True,
                    plan_sha256=batch.sha(target / 'PLAN.json'), deadline_unix=100,
                    max_new_calls=1 if name == 'first' else 0))
                batch.write(target / 'GUARD_STARTED.json', dict(deadline_unix=100))
                with patch.dict(os.environ, {'ORCH_R118_CPU_GUARD_SHA256':batch.sha(target / 'GUARD_STARTED.json')}):
                    batch.run(target)
                rows = batch.read(target / 'ROWS.json')
                self.assertEqual(len(rows), 16)
                self.assertTrue(all(row['annotation']['result']['status'] == 'COMPLETE' for row in rows),
                    (name, rows[0]['annotation'], calls))
                terminal = batch.read(target / 'TERMINAL.json')
                self.assertEqual(terminal['new_charged_calls'], 1 if name == 'first' else 0)
                self.assertEqual(terminal['unique_blind_inputs'], 1)
                self.assertEqual(len(calls), 2)
            self.assertEqual(tokenizer.padding_side, 'left')
            self.assertEqual(model_loader.call_args.kwargs['device_map'], {'':'cpu'})
            self.assertTrue(model_loader.call_args.kwargs['local_files_only'])
            self.assertFalse(model_loader.call_args.kwargs['trust_remote_code'])
            fake_torch.set_num_threads.assert_called_with(16)
        self.assertTrue((self.root / 'first/batch_0000.tokens.jsonl').exists())
        self.assertFalse(list((self.root / 'cached').glob('cache/*/CLAIM.json')))

    def test_guard_uses_remaining_absolute_deadline_not_fresh_budget(self):
        batch.write(self.root / 'PLAN.json', dict(deadline_unix=100))
        batch.write(self.root / 'PUBLICATION.json', dict(authorized=True,
            plan_sha256=batch.sha(self.root / 'PLAN.json'), deadline_unix=100))
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=75), \
                patch.object(batch.subprocess, 'run', return_value=SimpleNamespace(returncode=124)) as dispatch:
            self.assertEqual(batch.run_bounded(self.root), 124)
        command = dispatch.call_args.args[0]
        self.assertIn('25s', command)
        self.assertIn('--kill-after=5s', command)
        self.assertEqual(batch.read(self.root / 'TERMINAL.json')['status'], 'WALL_BOUND')
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=101):
            with self.assertRaisesRegex(ValueError, 'finite_remaining_wall'):
                batch.run_bounded(self.root)

    def test_guard_never_replays_started_root(self):
        batch.write(self.root / 'PLAN.json', dict(deadline_unix=100))
        batch.write(self.root / 'PUBLICATION.json', dict(authorized=True,
            plan_sha256=batch.sha(self.root / 'PLAN.json'), deadline_unix=100))
        batch.write(self.root / 'STARTED.json', dict(pid=1248873))
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=75), \
                patch.object(batch.subprocess, 'run') as dispatch:
            with self.assertRaisesRegex(ValueError, 'no_automatic_annotation_replay'):
                batch.run_bounded(self.root)
        dispatch.assert_not_called()

    def test_future_preparation_deadline_does_not_extend_execution_wall(self):
        deadline = batch.original.MAX_SECONDS + 500
        batch.write(self.root / 'PLAN.json', dict(deadline_unix=deadline))
        batch.write(self.root / 'PUBLICATION.json', dict(authorized=True,
            plan_sha256=batch.sha(self.root / 'PLAN.json'), deadline_unix=deadline))
        with patch.object(batch, 'node_environment'), patch.object(batch.time, 'time', return_value=0), \
                patch.object(batch.subprocess, 'run', return_value=SimpleNamespace(returncode=124)) as dispatch:
            batch.run_bounded(self.root)
        self.assertIn(f'{batch.original.MAX_SECONDS}s', dispatch.call_args.args[0])
        self.assertEqual(batch.read(self.root / 'GUARD_STARTED.json')['deadline_unix'], deadline)


if __name__ == '__main__':
    unittest.main()
