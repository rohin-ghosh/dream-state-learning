"""CPU fixtures only; native entrypoint exercised with an offline mocked tokenizer."""
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path.cwd()))
import astra_birth_protocol_overlay_20260913 as overlay


class Tokenizer:
    eos_token_id, pad_token_id = 900000000, 900000001

    def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
        assert tokenize is False and add_generation_prompt is True
        assert len(messages) == 1 and messages[0]['role'] == 'user'
        return 'USER:\n'+messages[0]['content']+'\nASSISTANT:\n'

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return [100+int(hashlib.sha256(token.encode()).hexdigest()[:7], 16)
                for token in re.findall(r'[A-Za-z_]+|[0-9]+|[^\w\s]', text)]


class UnequalTokenizer(Tokenizer):
    def encode(self, text, *, add_special_tokens):
        tokens = super().encode(text, add_special_tokens=add_special_tokens)
        return tokens+[777] if text.startswith('USER:') and 'pair-0-side-0' in text else tokens


@contextmanager
def native_fixture(tokenizer=None):
    directory = '/virtual/overlay-tokenizer'
    blobs = {'config.json': b'{"model_type":"qwen2"}', 'tokenizer.json': b'{"fixture":true}', 'tokenizer_config.json': b'{}'}
    pins = {name: hashlib.sha256(data).hexdigest() for name, data in blobs.items()}
    read, exists, resolve = Path.read_bytes, Path.exists, Path.resolve

    def read_bytes(path):
        return blobs[path.name] if str(path).startswith(directory+'/') else read(path)

    def path_exists(path):
        return path.name in blobs if str(path).startswith(directory+'/') else exists(path)

    def path_resolve(path, *args, **kwargs):
        return path if str(path) == directory else resolve(path, *args, **kwargs)

    loader = MagicMock(return_value=tokenizer or Tokenizer())
    with patch.object(Path, 'read_bytes', read_bytes), patch.object(Path, 'exists', path_exists), \
         patch.object(Path, 'resolve', path_resolve), \
         patch.dict(sys.modules, {'transformers': SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=loader))}):
        yield directory, pins, blobs, loader


class OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = overlay.build_candidate()
        cls.original = overlay.birth.build_candidate(root=0)
        cls.probe = overlay._probe()
        cls.fixed = cls.probe.build_candidate()
        cls.report = overlay.audit_tokenizer(cls.candidate, Tokenizer())

    def test_json_determinism_and_new_schema(self):
        self.assertEqual(json.loads(json.dumps(self.candidate, allow_nan=False)), overlay.build_candidate())
        self.assertNotEqual(self.candidate['schema'], self.original['schema'])
        self.assertEqual(overlay.audit_candidate(self.candidate)['updates'], 128)
        self.assertFalse(self.candidate['partition']['selected_from_live_outputs'])

    def test_exact_replacement_indices_and_240_background(self):
        expected = {8*(4*pair)+slot+(pair % 2) for pair in range(8) for slot in (4, 6)}
        self.assertEqual({row['index'] for row in self.candidate['replacements']}, expected)
        for arm in overlay.ARMS:
            rows = self.candidate['train'][arm]
            self.assertEqual(sum(row == self.original['train']['AUTH'][index] for index, row in enumerate(rows)), 240)
            for index in set(range(256))-expected:
                self.assertEqual(rows[index], self.original['train']['AUTH'][index])

    def test_conditional_auth_in_both_arms_and_anchor_balance(self):
        for arm in overlay.ARMS:
            rows = self.candidate['train'][arm]
            for index, original in enumerate(self.original['train']['AUTH']):
                if original['operation'] in overlay.birth.CONDITIONAL:
                    self.assertEqual(rows[index], original)
                    self.assertNotEqual(rows[index]['response'], self.original['train']['DERANGED'][index]['response'])
            counts = Counter(row['operation'] for row in rows)
            self.assertEqual(counts, dict(PROSPECT=64, REVISE=64, ADDITION=56, COPY=56,
                PROTOCOL_TRY=8, PROTOCOL_RECORD=4, PROTOCOL_QUIZ=2, PROTOCOL_REVEAL=2))
            for operation in ('ADDITION', 'COPY'):
                self.assertEqual(Counter(row['template'] for row in rows if row['operation'] == operation), {0: 28, 1: 28})

    def test_actual_deranged_mapping_and_14_nontrivial_targets(self):
        auth, deranged = (self.candidate['train'][arm] for arm in overlay.ARMS)
        self.assertEqual(sum(left['response'] != right['response'] for left, right in zip(auth, deranged)), 14)
        for index, row in enumerate(deranged):
            self.assertEqual(row['response'], auth[self.candidate['swap'][index]]['response'])
            self.assertEqual({key: value for key, value in row.items() if key != 'response'},
                             {key: value for key, value in auth[index].items() if key != 'response'})
        for offset in range(0, 256, 8):
            self.assertEqual(Counter(row['response'] for row in auth[offset:offset+8]),
                             Counter(row['response'] for row in deranged[offset:offset+8]))

    def test_all_raw_auth_controls_and_intended_negative_controls(self):
        for entry in self.candidate['replacements']:
            case, index = entry['bridge_case'], entry['index']
            self.assertTrue(self.probe.validate_output(case, case['auth_example_target'])['instruction_compliant'])
            result = self.probe.validate_output(case, self.candidate['train'][overlay.ARMS[1]][index]['response'])
            self.assertEqual(result['public_contract_correct'], entry['pair'] == 7)

    def test_all_fixed_probe_tuples_excluded(self):
        excluded = {tuple(row['public']['values']) for row in self.fixed['cases'] if 'values' in row['public']}
        excluded.update(tuple(values) for row in self.fixed['cases'] for values in row['source'].get('revealed_triples', []))
        self.assertEqual(excluded, set(map(tuple, self.candidate['partition']['excluded_probe_tuples'])))
        fixed_ids = {row['source'].get('eid') for row in self.fixed['cases']}
        fixed_quizzes = [row['source']['revealed_triples'] for row in self.fixed['cases'] if 'revealed_triples' in row['source']]
        for entry in self.candidate['replacements']:
            case = entry['bridge_case']
            if 'values' in case['public']:
                self.assertNotIn(tuple(case['public']['values']), excluded)
            source = case['source']
            if 'eid' in source:
                self.assertNotIn(source['eid'], fixed_ids)
            if 'revealed_triples' in source:
                self.assertFalse(set(map(tuple, source['revealed_triples'])) & excluded)
                self.assertNotIn(source['revealed_triples'], fixed_quizzes)
            self.assertNotIn(case['context'], {row['context'] for row in self.fixed['cases']})

    def test_fixed_source_selection_not_model_outcomes(self):
        cases = [entry['bridge_case'] for entry in self.candidate['replacements']]
        self.assertEqual([case['public']['values'] for case in cases[:8:2]], [[0, 0, index] for index in range(4)])
        self.assertEqual(cases[8]['public']['values'], [0, 0, 5])
        self.assertEqual(cases[10]['public']['values'], [0, 7, 9])
        used = set(overlay._exclusions(self.fixed))
        available = [values for values in itertools.product(range(10), repeat=3) if values not in used]
        used.update(available[:4])
        for position, rules in ((8, (6, 7)), (10, (8, 9))):
            expected = next(values for values in available if values not in used and
                overlay.rulegame.RULES[rules[0]][1](*values) != overlay.rulegame.RULES[rules[1]][1](*values))
            self.assertEqual(tuple(cases[position]['public']['values']), expected)
            used.add(expected)

    def test_generator_truth_full_source_and_quiz_multiplicity(self):
        for entry in self.candidate['replacements']:
            source = entry['bridge_case']['source']
            self.assertIn(source['rule_index'], (None, 6, 7, 8, 9))
            if 'eid' not in source:
                continue
            game = overlay.rulegame.RuleGame()
            reward, outcome = game.evaluate(SimpleNamespace(eid=source['eid']), source['action'])
            self.assertEqual((reward, outcome), (source['reward'], source['outcome']))
            if source['action'].startswith('TRY'):
                values = entry['bridge_case']['public']['values']
                truth = (values[0]*values[1]*values[2]) % 2 == 0 if source['rule_index'] == 6 else \
                    max(values)-min(values) <= 4 if source['rule_index'] == 7 else \
                    values[0] >= max(values) if source['rule_index'] == 8 else sum(values) > 15
                self.assertEqual(outcome, f'the box says: {truth} for ({",".join(map(str, values))})')
            else:
                self.assertEqual(source['revealed_triples'], [list(values) for values in game.quiz_triples(source['eid'])])
        quiz = self.candidate['replacements'][13]['bridge_case']['source']['revealed_triples']
        self.assertEqual(len(quiz), 6)
        self.assertLess(len(set(map(tuple, quiz))), 6)

    def test_wrong_and_null_predictions_are_not_repaired(self):
        cases = [entry['bridge_case'] for entry in self.candidate['replacements'][8:12]]
        targets = [json.loads(case['auth_example_target']) for case in cases]
        self.assertEqual([target['predicted'] for target in targets], [True, True, None, None])
        self.assertEqual([target['observed'] for target in targets], [True, False, False, True])
        self.assertEqual([target['relation'] for target in targets], ['matched', 'mismatched', 'unavailable', 'unavailable'])
        for case, target in zip(cases[1:], targets[1:]):
            repaired = dict(target, predicted=target['observed'], relation='matched')
            self.assertFalse(self.probe.validate_output(case, json.dumps(repaired))['public_contract_correct'])

    def test_source_metadata_hidden_and_public_only_validation(self):
        source_ids = {record['id'] for record in self.candidate['source_records']}
        for row in self.candidate['train'][overlay.ARMS[0]]+self.candidate['dev']:
            self.assertTrue(set(row['source_event_ids']) <= source_ids)
            self.assertTrue(all(identifier not in row['context'] for identifier in row['source_event_ids']))
        with patch.object(overlay.rulegame.RuleGame, 'evaluate', side_effect=AssertionError('no hidden truth during checking')):
            for entry in self.candidate['replacements']:
                case = entry['bridge_case']
                self.assertNotRegex(case['context'], r'rule[0-9]+/|prod_even|range_le4|sum_gt15|first_largest')
                self.assertTrue(self.probe.validate_output(case, case['auth_example_target'])['public_contract_correct'])

    def test_original_dev_and_frozen_probe_unchanged(self):
        self.assertEqual(self.candidate['dev'], self.original['dev'])
        self.assertEqual(self.candidate['dev_twins'], self.original['twins']['dev'])
        self.assertEqual(self.candidate['fixed_probe_sha256'], self.probe.digest(self.fixed))
        self.assertEqual(self.candidate['fixed_probe_call_map_sha256'], self.probe.digest(self.probe.call_map(self.fixed)))
        self.assertEqual(self.probe.digest(self.fixed), '9c680f2010cd11b0116517383281764432f4351628f23059b1c9ee69a283e300')
        self.assertEqual(self.candidate['partition']['excluded_rules'], list(range(6)))
        self.assertTrue(all('Quiz reveal still needed' in entry['bridge_case']['context'] for entry in self.candidate['replacements'][:8]))

    def test_candidate_tampering_rejected(self):
        changes = (lambda value: value['train'][overlay.ARMS[0]].pop(),
                   lambda value: value['train'][overlay.ARMS[1]][0].update(response='wrong'),
                   lambda value: value['swap'].__setitem__(4, 4),
                   lambda value: value['replacements'][0]['bridge_case']['public'].update(values=[2, 5, 8]),
                   lambda value: value['partition'].update(excluded_probe_tuples=[]),
                   lambda value: value['dev'].pop(),
                   lambda value: value['source_records'].pop())
        for change in changes:
            candidate = deepcopy(self.candidate)
            change(candidate)
            with self.assertRaises(ValueError):
                overlay.audit_candidate(candidate)

    def test_source_pin_and_old_schema_rejection(self):
        with patch.object(overlay, 'PROBE_SHA', '0'*64):
            with self.assertRaises(ValueError):
                overlay.build_candidate()
        with patch.dict(overlay.FROZEN, {'birth_conditional_corpus.py': '0'*64}):
            with self.assertRaises(ValueError):
                overlay.build_candidate()
        with self.assertRaises((ValueError, KeyError)):
            overlay.audit_candidate(self.original)
        with self.assertRaises(ValueError):
            overlay.train_items(self.candidate, 'AUTH')

    def test_export_spans_metadata_and_unchanged_background_items(self):
        original_items = overlay.birth.train_items(self.original, 'AUTH')
        replacements = {entry['index'] for entry in self.candidate['replacements']}
        for arm in overlay.ARMS:
            items = overlay.train_items(self.candidate, arm)
            self.assertEqual(len(items), 256)
            for index, item in enumerate(items):
                self.assertEqual([span[1] for span in item['spans']], [False, True])
                self.assertEqual(item['spans'][0][0], self.candidate['train'][arm][index]['context'])
                self.assertEqual(item['spans'][1][0], self.candidate['train'][arm][index]['response'])
                if index not in replacements:
                    self.assertEqual(item, original_items[index])
            items[0]['meta']['source_event_ids'].append('mutation')
            self.assertNotIn('mutation', self.candidate['train'][arm][0]['source_event_ids'])

    def test_fixed_recipe_and_dose_disclosures(self):
        recipe = overlay.training_recipe()
        self.assertEqual(recipe, overlay.birth.training_recipe(learning_rate=1e-4, seed=0, epochs=4))
        self.assertEqual((recipe['rank'], recipe['alpha'], recipe['dropout'], recipe['batch_size']), (8, 16, .05, 8))
        self.assertEqual(self.candidate['dose']['anchor_presentations_per_family'], 224)
        self.assertEqual(self.candidate['dose']['prior_anchor_presentations_per_family'], 256)
        for key, value in (('seed', 1), ('epochs', 5), ('lr', 2e-4), ('pack', True), ('max_len', 1024)):
            with self.assertRaises(ValueError):
                overlay.audit_tokenizer(self.candidate, Tokenizer(), recipe=dict(recipe, **{key: value}))

    def test_actual_v3_masks_eos_and_native_target_swaps(self):
        report = self.report
        self.assertTrue(report['paired_exposure_equal'])
        self.assertFalse(report['native'])
        self.assertFalse(report['ready_for_native_export'])
        for arm in overlay.ARMS:
            for row in report['rows'][arm]:
                prefix, target_count = row['prefix_ids'], row['target_tokens']
                self.assertEqual(row['labels'][:len(prefix)], [-100]*len(prefix))
                self.assertEqual(row['labels'][len(prefix):], row['input_ids'][len(prefix):])
                self.assertEqual(row['labels'][-1], Tokenizer.eos_token_id)
                self.assertEqual(row['labels'].count(Tokenizer.eos_token_id), 1)
                self.assertEqual(target_count, len(row['input_ids'])-len(prefix))
                self.assertLessEqual(row['input_tokens'], 512)
        for index, swapped in enumerate(self.candidate['swap']):
            labels = lambda row: [token for token in row['labels'] if token != -100]
            self.assertEqual(labels(report['rows'][overlay.ARMS[0]][swapped]), labels(report['rows'][overlay.ARMS[1]][index]))

    def test_actual_v3_group_shuffle_collator_and_costs(self):
        report, tokenizer = self.report, Tokenizer()
        self.assertEqual(len(report['optimizer_update_rows']), 128)
        for arm in overlay.ARMS:
            items = overlay.trainer.normalize_items(report['corpora'][arm])
            segments = [overlay.trainer.encode_item_segments(item, tokenizer, 512, False, True, index, overflow='truncate')[0]
                        for index, item in enumerate(items)]
            updates = []
            for epoch in range(4):
                packs = overlay.trainer.epoch_order(overlay.trainer.pack_by_group(segments, 512, False), 0, epoch, True)
                self.assertEqual(set(pack[0].item_index for pack in packs), set(range(256)))
                for offset in range(0, 256, 8):
                    selected = packs[offset:offset+8]
                    batch = overlay.trainer.collate(selected, tokenizer.pad_token_id)
                    indices = [pack[0].item_index for pack in selected]
                    updates.append(indices)
                    cost = report['group_costs'][arm][len(updates)-1]
                    self.assertEqual(cost['row_indices'], indices)
                    self.assertEqual(cost['input_tokens'], batch['n_tokens'])
                    self.assertEqual(cost['target_tokens'], sum(token != -100 for labels in batch['labels'] for token in labels))
                    self.assertEqual(cost['padded_input_tokens'], sum(map(len, batch['input_ids'])))
                    self.assertEqual(cost['padding_tokens'], cost['padded_input_tokens']-cost['input_tokens'])
                    self.assertEqual(cost['eos_tokens'], 8)
            self.assertEqual(updates, report['optimizer_update_rows'])
            for key, value in report['totals'][arm].items():
                self.assertEqual(value, sum(cost[key] for cost in report['group_costs'][arm]))
            self.assertEqual(report['totals'][arm]['eos_tokens'], 1024)
        self.assertEqual(report['totals'][overlay.ARMS[0]], report['totals'][overlay.ARMS[1]])
        json.dumps(report, allow_nan=False)

    def test_token_exposure_mismatch_reported_without_changing_rows(self):
        report = overlay.audit_tokenizer(self.candidate, UnequalTokenizer())
        self.assertFalse(report['paired_exposure_equal'])
        self.assertTrue(report['exposure_mismatches'])
        self.assertEqual(report['candidate_sha256'], overlay.digest(self.candidate))
        self.assertFalse(report['ready_for_native_export'])

    def test_overflow_special_tokens_and_bad_collator_rejected(self):
        tokenizer = Tokenizer()
        tokenizer.encode = lambda text, **kwargs: [10]*513
        with self.assertRaisesRegex(ValueError, 'overflow'):
            overlay.audit_tokenizer(self.candidate, tokenizer)
        tokenizer = Tokenizer()
        tokenizer.pad_token_id = tokenizer.eos_token_id
        with self.assertRaisesRegex(ValueError, 'distinct EOS/PAD'):
            overlay.audit_tokenizer(self.candidate, tokenizer)
        tokenizer = Tokenizer()
        tokenizer.encode = lambda text, **kwargs: [tokenizer.eos_token_id]
        with self.assertRaisesRegex(ValueError, 'special target'):
            overlay.audit_tokenizer(self.candidate, tokenizer)
        collate = overlay.trainer.collate
        def wrong_collate(packs, pad):
            result = collate(packs, pad)
            result['labels'][0][0] = 7
            return result
        with patch.object(overlay.trainer, 'collate', wrong_collate):
            with self.assertRaisesRegex(ValueError, 'collator mask'):
                overlay.audit_tokenizer(self.candidate, Tokenizer())

    def test_actual_encoder_missing_split_or_mask_rejected(self):
        encode = overlay.trainer.encode_item_segments
        for problem in ('missing', 'split', 'mask'):
            def wrong_encode(*args, **kwargs):
                result = encode(*args, **kwargs)
                if problem == 'missing':
                    return []
                if problem == 'split':
                    return result+deepcopy(result)
                result[0].labels[0] = 7
                return result
            with patch.object(overlay.trainer, 'encode_item_segments', wrong_encode):
                with self.assertRaises(ValueError):
                    overlay.audit_tokenizer(self.candidate, Tokenizer())

    def test_native_wrapper_offline_pins_and_export_with_mock_only(self):
        with native_fixture() as (directory, pins, blobs, loader):
            report = overlay.audit_native(self.candidate, directory, pins)
            loader.assert_called_once_with(directory, local_files_only=True, trust_remote_code=False)
            self.assertEqual(report['status'], 'NATIVE_OVERLAY_TOKEN_MATCH_VERIFIED')
            for arm in overlay.ARMS:
                exported = overlay.export_native(self.candidate, report, arm)
                self.assertEqual(exported, {'corpus': report['corpora'][arm]})
                exported['corpus'][0]['spans'][1][0] = 'changed'
                self.assertNotEqual(exported['corpus'], report['corpora'][arm])

    def test_native_missing_wrong_pins_and_model_config_fail_before_load(self):
        with native_fixture() as (directory, pins, blobs, loader):
            for changed in ({}, dict(pins, **{'tokenizer.json': '0'*64}), dict(pins, **{'../escape': '0'*64})):
                with self.assertRaises(ValueError):
                    overlay.audit_native(self.candidate, directory, changed)
            blobs['config.json'] = b'{"model_type":"wrong"}'
            pins['config.json'] = hashlib.sha256(blobs['config.json']).hexdigest()
            with self.assertRaisesRegex(ValueError, 'Qwen2'):
                overlay.audit_native(self.candidate, directory, pins)
            loader.assert_not_called()

    def test_native_external_template_and_changed_pin_rejected(self):
        with native_fixture() as (directory, pins, blobs, loader):
            blobs['chat_templates'] = b'unsupported'
            with self.assertRaisesRegex(ValueError, 'external chat_templates'):
                overlay.audit_native(self.candidate, directory, pins)
            del blobs['chat_templates']
            def changed(*args, **kwargs):
                blobs['tokenizer.json'] = b'changed-after-validation'
                return Tokenizer()
            loader.side_effect = changed
            with self.assertRaisesRegex(ValueError, 'tokenizer changed'):
                overlay.audit_native(self.candidate, directory, pins)

    def test_native_exposure_mismatch_is_not_exportable(self):
        with native_fixture(UnequalTokenizer()) as (directory, pins, blobs, loader):
            report = overlay.audit_native(self.candidate, directory, pins)
            self.assertEqual(report['status'], 'NATIVE_OVERLAY_EXPOSURE_MISMATCH_NOT_READY')
            self.assertTrue(report['native'])
            self.assertFalse(report['ready_for_native_export'])
            with self.assertRaises(ValueError):
                overlay.export_native(self.candidate, report, overlay.ARMS[0])

    def test_callback_old_schema_and_partial_exports_rejected(self):
        with self.assertRaises(ValueError):
            overlay.export_native(self.candidate, self.report, overlay.ARMS[0])
        with native_fixture() as (directory, pins, blobs, loader):
            report = overlay.audit_native(self.candidate, directory, pins)
            for mutate in (lambda value: value.update(schema='birth-conditional-crossed-v1'),
                           lambda value: value['corpora'][overlay.ARMS[0]].pop(),
                           lambda value: value['corpora'][overlay.ARMS[0]][0]['spans'][1].__setitem__(0, 'wrong')):
                changed = deepcopy(report)
                mutate(changed)
                with self.assertRaises(ValueError):
                    overlay.export_native(self.candidate, changed, overlay.ARMS[0])


if __name__ == '__main__':
    unittest.main()
