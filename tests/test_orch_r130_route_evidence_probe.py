from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r130_route_evidence_probe as probe


def export_fixture():
    exported = dict(schema='R127_CANONICAL_FRESH_TRANSFER_V1',
        selection='FIXED_C2_C4_C6_NOT_SELECTED_ON_TRANSFER_OUTCOMES', conditions={}, files={})
    for condition in probe.CONDITIONS:
        folder = f'conditions/{condition}/adapter'
        file_hash = hashlib.sha256(b'CPU fixture: not tensor data').hexdigest()
        exported['files'][folder + '/adapter_model.safetensors'] = file_hash
        exported['conditions'][condition] = dict(cycle=0 if condition == 'SEED' else 6,
            arm='SEED' if condition == 'SEED' else condition.split('_')[0],
            updates={'SEED': 0, 'GUIDED_C6': 424, 'UNPARENTED_C6': 536}[condition],
            adapter=dict(path=folder, state_sha256=probe.SEED_SHA if condition == 'SEED' else probe.digest(condition),
                         base_sha256=probe.BASE_SHA, files=[['adapter_model.safetensors', file_hash]]))
    return exported


def public_oracle(messages):
    content = messages[1]['content']
    lines = content.splitlines()
    current = next(line[8:] for line in lines if line.startswith('CURRENT '))
    goal = next(line[5:] for line in lines if line.startswith('GOAL '))
    ports = next(line[6:].split(',') for line in lines if line.startswith('PORTS '))
    events = [probe.rich.hop.micro.parse_event_line(line + '\n') for line in lines if line.startswith('EVENT ')]
    anchor = next(event for event in events if event['source'] == current)
    branch = next(event for event in events if event['source'] == anchor['destination'])
    port = anchor['port'] if branch['destination'] == goal else next(port for port in ports if port != anchor['port'])
    return 'ROUTE ' + port


def response(messages, raw):
    return dict(messages=deepcopy(messages), raw=raw, terminal=True, truncated=False,
                prompt_tokens=100, token_ids=[1, 2, 0])


class EvidenceProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = probe.make_manifest(export_fixture(), ['N_PRIOR'])

    def setUp(self):
        self.manifest = deepcopy(self.original)

    def evaluate(self, condition='SEED', actor=public_oracle):
        emissions = []

        def generate(messages, *, max_new_tokens):
            self.assertEqual(max_new_tokens, 512)
            return response(messages, actor(messages))

        records = probe.evaluate_condition(self.manifest, condition, generate,
            lambda name, value: emissions.append((name, deepcopy(value))))
        return records, emissions

    def groups(self, actor=public_oracle):
        return {condition: self.evaluate(condition, actor)[0] for condition in probe.CONDITIONS}

    def test_fresh_reproducible_sixteen_pairs_and_fixed_terminal_checkpoints(self):
        self.assertEqual(self.manifest, probe.make_manifest(export_fixture(), ['N_PRIOR']))
        self.assertEqual(len(self.manifest['pairs']), 16)
        self.assertEqual(set(self.manifest['conditions']), {'SEED', 'GUIDED_C6', 'UNPARENTED_C6'})
        self.assertEqual(self.manifest['max_native_calls'], 96)
        self.assertEqual(self.manifest['source_native_calls'], 0)
        self.assertEqual(self.manifest['conditions']['GUIDED_C6']['updates'], 424)
        self.assertEqual(self.manifest['conditions']['UNPARENTED_C6']['updates'], 536)

    def test_every_pair_changes_one_GOT_value_and_environment_gold_flips(self):
        for pair in self.manifest['pairs']:
            checked = probe.validate_pair(pair)
            self.assertNotEqual(checked['actions']['A'], checked['actions']['B'])
            left, right = (checked['messages'][variant][1]['content'].split() for variant in probe.VARIANTS)
            differences = [index for index, values in enumerate(zip(left, right)) if values[0] != values[1]]
            self.assertEqual(len(differences), 1)
            self.assertEqual(left[differences[0] - 1], 'GOT')
            for variant in probe.VARIANTS:
                self.assertEqual(public_oracle(checked['messages'][variant]), checked['actions'][variant])

    def test_original_canonical_scorer_confirms_gold_two_route_path(self):
        for pair in self.manifest['pairs']:
            for variant in probe.VARIANTS:
                world = pair['worlds'][variant]
                gold = probe.gold_action(world, pair['task'])
                first = probe.transition(world, pair['task']['node'], gold.split()[1])
                edge = next(edge for edge in world['edges'] if edge['node'] == first['destination'])
                second = probe.transition(world, first['destination'], edge['port'])
                self.assertTrue(probe.rich.readout.score(world, pair['task'], dict(routes=[first, second], correct=True)))

    def test_hidden_complement_is_necessary_not_silent_record_corruption(self):
        pair = self.manifest['pairs'][0]
        pair['worlds']['B']['edges'][1]['outcome'] = pair['worlds']['A']['edges'][1]['outcome']
        with self.assertRaisesRegex(ValueError, 'root_bijection'):
            probe.validate_pair(pair)

    def test_unavailable_and_wrong_world_evidence_rejected(self):
        for field, value in (('available', False), ('world_sha256', '0' * 64), ('provenance', 'CHILD_MEMORY')):
            pair = deepcopy(self.manifest['pairs'][0])
            pair['records']['A'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'unavailable_or_mismatched'):
                probe.validate_pair(pair)

    def test_record_destination_and_receipt_must_match_environment(self):
        pair = self.manifest['pairs'][0]
        record = pair['records']['A'][0]
        record['raw'] = pair['records']['B'][0]['raw']
        with self.assertRaisesRegex(ValueError, 'environment_grounded'):
            probe.validate_pair(pair)
        pair = deepcopy(self.original['pairs'][0])
        pair['records']['A'][0]['receipt'] = 'MEMORY UNAVAILABLE'
        with self.assertRaisesRegex(ValueError, 'receipt_not_environment_grounded'):
            probe.validate_pair(pair)

    def test_unavailable_wire_and_missing_record_rejected(self):
        pair = self.manifest['pairs'][0]
        pair['records']['A'][0]['raw'] = 'MEMORY UNAVAILABLE'
        with self.assertRaises(ValueError):
            probe.validate_pair(pair)
        pair = deepcopy(self.original['pairs'][0])
        pair['records']['B'].pop()
        with self.assertRaisesRegex(ValueError, 'exact_three'):
            probe.validate_pair(pair)

    def test_no_labels_checkpoint_or_variant_markers_in_public_prompt(self):
        for pair in self.manifest['pairs']:
            for variant in probe.VARIANTS:
                messages = probe.render(pair['task'], pair['records'][variant])
                encoded = json.dumps(messages)
                for forbidden in ('GUIDED', 'UNPARENTED', 'SEED', 'gold_action', 'correct', 'variant',
                                  'pair_id', 'checkpoint', 'updates', 'world_sha256', probe.PREFIX):
                    self.assertNotIn(forbidden, encoded)
        pair = self.manifest['pairs'][0]
        pair['task']['gold_action'] = 'ROUTE bad'
        with self.assertRaisesRegex(ValueError, 'matched_public_task'):
            probe.validate_pair(pair)

    def test_display_position_and_variant_order_are_counterbalanced(self):
        first_targets, first_variants = [], []
        for pair in self.manifest['pairs']:
            checked = probe.validate_pair(pair)
            first_targets.append(checked['actions']['A'] == 'ROUTE ' + pair['task']['ports'][0])
            first_variants.append(pair['order'][0])
        self.assertEqual(sum(first_targets), 8)
        self.assertEqual(first_variants.count('A'), 8)
        self.assertEqual(first_variants.count('B'), 8)

    def test_namespace_collision_and_duplicate_pair_rejected(self):
        identifier = self.manifest['pairs'][0]['task']['node']
        with self.assertRaisesRegex(ValueError, 'namespace_collision'):
            probe.build_pairs([identifier])
        self.manifest['pairs'][-1] = deepcopy(self.manifest['pairs'][0])
        with self.assertRaisesRegex(ValueError, 'sixteen_pair'):
            probe.validate_manifest(self.manifest)

    def test_evaluation_only_flags_fail_before_actor_called(self):
        for field in ('trainingAllowed', 'optimizer_steps', 'parent_calls', 'training_rows'):
            manifest = deepcopy(self.original)
            manifest[field] = True if field == 'trainingAllowed' else 1
            generate = Mock()
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.evaluate_condition(manifest, 'SEED', generate, Mock())
            generate.assert_not_called()

    def test_changed_base_or_checkpoint_selection_rejected(self):
        self.manifest['conditions']['GUIDED_C6']['adapter']['base_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'checkpoint_identity'):
            probe.validate_manifest(self.manifest)
        exported = export_fixture()
        exported['conditions']['GUIDED_C6']['cycle'] = 4
        with self.assertRaisesRegex(ValueError, 'terminal_checkpoint'):
            probe.make_manifest(exported, [])

    def test_one_call_per_variant_and_no_training_artifact_names(self):
        records, emissions = self.evaluate()
        self.assertEqual(len(records), 32)
        self.assertEqual(len(emissions), 64)
        self.assertEqual([name for name, unused in emissions][::2], [f'CLAIM_{index:03d}.json' for index in range(1, 33)])
        self.assertTrue(all(not item['trainingAllowed'] and not item['parent_present'] for item in records))
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name, value in emissions:
                probe.write_new(folder / name, value)
            self.assertEqual({path.suffix for path in folder.iterdir()}, {'.json'})
            for name in ('TRAIN.json', 'ROWS.json', 'SLEEP.json', 'adapter_model.safetensors', 'optimizer.pt'):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'no_TRAIN'):
                    probe.write_new(folder / name, {})
                self.assertFalse((folder / name).exists())

    def test_logical_call_cannot_be_replayed_into_same_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            actor = Mock(side_effect=lambda messages, **unused: response(messages, public_oracle(messages)))
            emit = lambda name, value: probe.write_new(folder / name, value)
            probe.evaluate_condition(self.manifest, 'SEED', actor, emit)
            self.assertEqual(actor.call_count, 32)
            with self.assertRaises(FileExistsError):
                probe.evaluate_condition(self.manifest, 'SEED', actor, emit)
            self.assertEqual(actor.call_count, 32)

    def test_failed_inference_preserved_without_retry(self):
        actor = Mock(side_effect=RuntimeError('CPU simulated failure'))
        emissions = []
        with self.assertRaises(RuntimeError):
            probe.evaluate_condition(self.manifest, 'SEED', actor,
                lambda name, value: emissions.append((name, deepcopy(value))))
        self.assertEqual(actor.call_count, 1)
        self.assertEqual([name for name, unused in emissions], ['CLAIM_001.json', 'CALL_001.json'])
        self.assertEqual(emissions[-1][1]['status'], 'FAILED')

    def test_mismatched_native_response_preserved_but_not_retried(self):
        returned = response([], 'ROUTE wrong_prompt')
        actor = Mock(return_value=returned)
        emissions = []
        with self.assertRaisesRegex(ValueError, 'native_response_prompt_mismatch'):
            probe.evaluate_condition(self.manifest, 'SEED', actor,
                lambda name, value: emissions.append((name, deepcopy(value))))
        self.assertEqual(actor.call_count, 1)
        self.assertEqual(emissions[-1][1]['response'], returned)
        self.assertEqual(emissions[-1][1]['status'], 'FAILED')

    def test_empty_LoRA_files_and_nonzero_seed_dose_rejected(self):
        self.manifest['conditions']['GUIDED_C6']['adapter']['files'] = []
        with self.assertRaisesRegex(ValueError, 'checkpoint_identity'):
            probe.validate_manifest(self.manifest)
        self.manifest = deepcopy(self.original)
        self.manifest['conditions']['SEED']['updates'] = 1
        with self.assertRaisesRegex(ValueError, 'fixed_seed'):
            probe.validate_manifest(self.manifest)

    def test_public_evidence_oracle_succeeds_and_uncertainty_unit_is_pair_world(self):
        result = probe.reduce_records(self.manifest, self.groups(), bootstrap_samples=100)
        self.assertEqual(result['status'], 'COMPLETE')
        for summary in result['conditions'].values():
            self.assertEqual(summary['correct_first_actions'], 32)
            self.assertEqual(summary['pair_counts']['both_correct'], 16)
            self.assertEqual(summary['pair_counts']['valid_action_switch'], 16)
        paired = result['comparisons']['GUIDED_C6_minus_SEED']['both_correct']
        self.assertEqual(paired['paired_worlds'], 16)
        self.assertEqual(paired['ci95'], [0, 0])
        self.assertFalse(result['causal_parenting_claim'])

    def test_fixed_first_port_has_no_correct_pairs(self):
        def first_port(messages):
            line = next(line for line in messages[1]['content'].splitlines() if line.startswith('PORTS '))
            return 'ROUTE ' + line[6:].split(',')[0]

        result = probe.reduce_records(self.manifest, self.groups(first_port), bootstrap_samples=100)
        for summary in result['conditions'].values():
            self.assertEqual(summary['correct_first_actions'], 16)
            self.assertEqual(summary['pair_counts']['both_correct'], 0)
            self.assertEqual(summary['pair_counts']['valid_action_switch'], 0)

    def test_copying_anchor_port_does_not_pass_content_aligned_pair_metric(self):
        def copy_anchor(messages):
            lines = messages[1]['content'].splitlines()
            current = next(line[8:] for line in lines if line.startswith('CURRENT '))
            events = [probe.rich.hop.micro.parse_event_line(line + '\n') for line in lines if line.startswith('EVENT ')]
            return 'ROUTE ' + next(event['port'] for event in events if event['source'] == current)

        result = probe.reduce_records(self.manifest, self.groups(copy_anchor), bootstrap_samples=100)
        self.assertEqual(result['conditions']['SEED']['pair_counts']['both_correct'], 0)
        self.assertEqual(result['conditions']['SEED']['correct_first_actions'], 16)

    def test_content_sensitive_but_wrong_direction_is_not_success(self):
        def opposite(messages):
            oracle_port = public_oracle(messages).split()[1]
            ports = next(line[6:].split(',') for line in messages[1]['content'].splitlines() if line.startswith('PORTS '))
            return 'ROUTE ' + next(port for port in ports if port != oracle_port)

        result = probe.reduce_records(self.manifest, self.groups(opposite), bootstrap_samples=100)
        summary = result['conditions']['SEED']
        self.assertEqual(summary['pair_counts']['valid_action_switch'], 16)
        self.assertEqual(summary['pair_counts']['both_wrong'], 16)
        self.assertEqual(summary['pair_counts']['both_correct'], 0)

    def test_READ_or_invalid_output_cannot_score_as_content_use(self):
        result = probe.reduce_records(self.manifest, self.groups(lambda messages: 'READ EVENT not_an_action'), bootstrap_samples=100)
        self.assertEqual(result['conditions']['SEED']['valid_actions'], 0)
        self.assertEqual(result['conditions']['SEED']['pair_counts']['any_invalid'], 16)
        self.assertEqual(result['conditions']['SEED']['pair_counts']['both_correct'], 0)

    def test_partial_conditions_withhold_comparisons(self):
        records, unused = self.evaluate()
        result = probe.reduce_records(self.manifest, {'SEED': records}, bootstrap_samples=100)
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertIsNone(result['comparisons'])

    def test_mismatched_decoder_prompt_pair_and_response_rejected(self):
        original = self.groups()
        for change in ('decoder', 'pair_id', 'messages', 'response'):
            groups = deepcopy(original)
            row = groups['SEED'][0]
            if change == 'decoder':
                row['decoder']['max_new_tokens'] = 100
            elif change == 'pair_id':
                row['pair_id'] = 'other'
            elif change == 'messages':
                row['messages'][0]['content'] = 'choose label'
            else:
                row['response']['messages'] = []
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'record_binding'):
                probe.reduce_records(self.manifest, groups, bootstrap_samples=100)

    def test_missing_token_counts_not_imputed_and_truncation_invalid(self):
        groups = self.groups()
        for condition, rows in groups.items():
            rows[0]['response'].pop('prompt_tokens')
            rows[0]['response'].update(terminal=False, truncated=True)
        result = probe.reduce_records(self.manifest, groups, bootstrap_samples=100)
        summary = result['conditions']['SEED']
        self.assertIsNone(summary['telemetry']['prompt_tokens']['total'])
        self.assertEqual(summary['telemetry']['prompt_tokens']['missing_calls'], 1)
        self.assertEqual(summary['pair_counts']['any_invalid'], 1)
        self.assertEqual(summary['pair_counts']['both_correct'], 15)

    def test_native_stage_cpu_mock_writes_only_readout_and_checks_unchanged(self):
        from gpu import orch_guided_native as native

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exported = export_fixture()
            source_root = Path(probe.__file__).resolve().parents[1]
            exported['original_source_files'] = {name: probe.sha(source_root / name)
                                                for name in probe.HISTORICAL_ENGINE_CONTRACTS}
            for entry in exported['conditions'].values():
                folder = root / entry['adapter']['path']
                folder.mkdir(parents=True)
                (folder / 'adapter_model.safetensors').write_bytes(b'CPU fixture: not tensor data')
            export_path, exclusion_path = root / 'EXPORT.json', root / 'EXCLUSIONS.json'
            export_path.write_text(json.dumps(exported))
            exclusion_path.write_text(json.dumps(['N_PRIOR']))
            manifest = probe.prepare(export_path, exclusion_path, root / 'manifest')
            plan = dict(schema=probe.SCHEMA, manifest=probe.reference(root / 'manifest/MANIFEST.json'),
                trainingAllowed=False, optimizer_steps=0, parent_calls=0, training_rows=0,
                hard_end_unix=time.time() + 60, lease_end_unix=time.time() + 86400,
                output=str(root / 'evaluation'), model_dir=str(root / 'unused_model'), gpu_uuid='GPU-cpu-fixture',
                source_root=str(source_root), source_files={name: probe.sha(source_root / name) for name in probe.SOURCE_CLOSURE})
            plan_path = root / 'PLAN.json'
            plan_path.write_text(json.dumps(plan))
            observed = []

            def load(binding, **unused):
                actor = SimpleNamespace(optimizer=None, observed=binding.adapter, process=['CPU', 123, 456],
                    engine=SimpleNamespace(generate=lambda messages, **kwargs: response(messages, public_oracle(messages))),
                    verify_unchanged=Mock())
                observed.append(actor)
                return actor

            environment = dict(CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
            with patch.object(native, 'load_stage', side_effect=load), patch.dict(os.environ, environment):
                probe.stage(plan_path, 'SEED')
            complete = probe.read(root / 'evaluation/SEED/COMPLETE.json')
            self.assertTrue(complete['unchanged'])
            self.assertEqual(complete['calls'], 32)
            self.assertEqual(complete['optimizer_steps'], 0)
            self.assertEqual(complete['parent_calls'], 0)
            self.assertFalse(complete['trainingAllowed'])
            self.assertEqual(complete['manifest_sha256'], probe.digest(manifest))
            observed[0].verify_unchanged.assert_called_once_with()
            self.assertFalse(any('TRAIN' in path.name or 'SLEEP' in path.name for path in (root / 'evaluation').rglob('*')))


class EvidenceProbeSourcePinsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / 'snapshot'
        self.extra = 'gpu/astra_experienced_event_cue_collect.py'
        self.pins = {}
        for name in probe.SOURCE_CLOSURE + (self.extra,):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('CPU source-pin fixture: ' + name)
            self.pins[name] = probe.sha(path)
        self.historical = {name: self.pins[name] for name in probe.HISTORICAL_ENGINE_CONTRACTS}

    def validate(self):
        return probe.validate_source_files(self.root, self.pins, self.historical)

    def test_full_superset_source_manifest_accepted(self):
        self.assertNotIn(self.extra, probe.SOURCE_CLOSURE)
        self.assertEqual(self.validate(), self.root)

    def test_extra_transitive_source_drift_rejected(self):
        (self.root / self.extra).write_text('changed transitive helper')
        with self.assertRaisesRegex(ValueError, 'source_closure_drift:' + self.extra):
            self.validate()

    def test_extra_source_missing_or_null_pin_rejected(self):
        self.pins[self.extra] = None
        with self.assertRaisesRegex(ValueError, 'source_closure_drift'):
            self.validate()
        (self.root / self.extra).unlink()
        with self.assertRaisesRegex(ValueError, 'source_symlink_escape_or_missing_file'):
            self.validate()

    def test_minimum_source_closure_still_required(self):
        del self.pins['gpu/orch_guided_native.py']
        with self.assertRaisesRegex(ValueError, 'minimum_closure'):
            self.validate()

    def test_absolute_traversal_and_aliased_source_names_rejected(self):
        for name in ('../outside.py', '/tmp/outside.py', 'gpu/../outside.py',
                     './outside.py', 'gpu//outside.py'):
            with self.subTest(name=name):
                pins = dict(self.pins, **{name: '0' * 64})
                with self.assertRaisesRegex(ValueError, 'source_path_escape_or_alias'):
                    probe.validate_source_files(self.root, pins, self.historical)

    def test_extra_symlink_source_rejected_even_with_matching_bytes(self):
        path = self.root / self.extra
        outside = self.root.parent / 'outside.py'
        path.rename(outside)
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'source_symlink_escape_or_missing_file'):
            self.validate()

    def test_repinning_modern_engine_cannot_override_R127_export(self):
        name = 'gpu/astra_experienced_event_cue_sleep.py'
        path = self.root / name
        path.write_text('modern engine dependency with changed behavior')
        self.pins[name] = probe.sha(path)
        with self.assertRaisesRegex(ValueError, 'historical_engine_contract_drift:' + name):
            self.validate()

    def test_historical_engine_hash_cannot_be_missing(self):
        del self.historical['gpu/astra_experienced_event_microloop.py']
        with self.assertRaisesRegex(ValueError, 'R127_historical_engine_hash_required'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
