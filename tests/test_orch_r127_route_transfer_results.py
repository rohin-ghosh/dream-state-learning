from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r127_route_transfer as producer
from gpu import orch_r127_route_transfer_results as results
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_route_parent_campaign as policy


class DiskFixture:
    def __init__(self, temporary, *, truncate_source=False):
        self.home = Path(temporary).resolve()
        self.root, self.bundle, self.source = (self.home / name for name in ('run', 'bundle', 'source'))
        self.plan_path = self.home / 'PLAN.json'
        self.root.mkdir()
        self.sequence = 0
        self.truncate_source = truncate_source
        self.calls = {condition: [] for condition in results.STAGES}
        self.cohort = producer.fresh_cohort(set())
        self.write(self.bundle / 'COHORT.json', self.cohort)
        source_files = {}
        for name in results.HISTORICAL_RUNTIME + ('gpu/orch_r127_route_transfer.py',):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('CPU-only frozen source fixture: ' + name)
            source_files[str(path)] = self.sha(path)
        initial = self.identity('SEED', 0)
        self.conditions = dict(SEED=dict(arm='SEED', cycle=0, updates=0, adapter=deepcopy(initial)))
        history = {}
        for arm in ('GUIDED', 'UNPARENTED'):
            previous = initial
            history[arm] = []
            total = 0
            for cycle in range(1, 7):
                identity = self.identity(arm, cycle)
                updates = 112 if arm == 'GUIDED' else 56
                total += updates
                receipt = dict(status='COMPLETE', arm=arm, cycle=cycle, phase='sleep',
                               input_adapter=previous, output_adapter=identity, updates=updates)
                path = self.bundle / f'history/{arm}/C{cycle}.json'
                self.write(path, receipt)
                origin = dict(path=f'/unavailable/history/{arm}/cycle{cycle}/sleep/COMPLETE.json', sha256=self.sha(path))
                history[arm].append(dict(origin=origin, copied=str(path.relative_to(self.bundle)), updates=updates))
                if cycle in (2, 4, 6):
                    self.conditions[f'{arm}_C{cycle}'] = dict(arm=arm, cycle=cycle, updates=total,
                                                            adapter=identity, original_sleep=origin)
                previous = identity
        for condition, entry in self.conditions.items():
            identity = entry['adapter']
            entry['original_adapter_path'] = identity['path']
            relative = f'conditions/{condition}/adapter'
            adapter_file = self.bundle / relative / 'adapter_model.safetensors'
            adapter_file.parent.mkdir(parents=True)
            adapter_file.write_bytes(self.adapter_bytes(entry['arm'], entry['cycle']))
            entry['adapter'] = dict(identity, path=relative)
        exported = dict(schema=results.SCHEMA, conditions=self.conditions, history=history,
            files={str(path.relative_to(self.bundle)): self.sha(path) for path in self.bundle.rglob('*') if path.is_file()},
            original_source_files={name: source_files[str(self.source / name)] for name in results.HISTORICAL_RUNTIME},
            cohort_sha256=self.sha(self.bundle / 'COHORT.json'),
            selection='FIXED_C2_C4_C6_NOT_SELECTED_ON_TRANSFER_OUTCOMES')
        self.write(self.bundle / 'EXPORT.json', exported)
        self.plan = dict(schema=results.SCHEMA, wrapper='ovx', physical=7, parent_calls=0,
            optimizer_steps=0, training_rows=0, max_native_calls=1472, response_cap=512,
            source_files=source_files, output=str(self.root), bundle=str(self.bundle), source_root=str(self.source),
            export_sha256=self.sha(self.bundle / 'EXPORT.json'), created_unix=0, hard_end_unix=1, lease_end_unix=2)
        self.write(self.plan_path, self.plan)
        self.write(self.root / 'START.json', dict(pid=9000, plan=self.ref(self.plan_path)))
        self.stage_start('SOURCE', 9100)
        store = {}
        for index, world in enumerate(self.cohort['worlds']):
            replies = []
            for edge_index, edge in enumerate(world['edges']):
                if edge_index == 0:
                    replies.extend(['ROUTE ' + edge['port'], guided.rich.hop.micro._event(edge)])
                else:
                    replies.append('PRIVATE_FAILED_SOURCE_TEXT')
            replies = iter(replies)
            collection = policy.runtime(world['master'])['collect_world'](
                world, lambda messages: self.generate('SOURCE', messages, next(replies)))
            self.write(self.root / f'SOURCE/WORLD_{index:02d}.json', collection)
            for record in collection['records']:
                if record['accepted']:
                    store[record['edge']['event']] = record['event']['raw']
        self.write(self.root / 'SOURCE/STORE.json', dict(store=store, source_store_sha256=results.digest(store),
            worlds=16, offered_events=64, accepted_events=len(store), complete_worlds=0, trainingAllowed=False))
        self.finish('SOURCE', [])
        for ordinal, condition in enumerate(producer.CONDITIONS, 1):
            self.stage_start(condition, 9100 + ordinal)
            paths = []
            for index, row in enumerate(self.cohort['tasks']):
                replies = iter(['READ EVENT ' + row['task']['events'][0], 'PRIVATE_FAILED_EVAL_TEXT'])
                episode = guided.episode(self.cohort['worlds'][row['world_index']], row['task'],
                    lambda messages: self.generate(condition, messages, next(replies)),
                    store, parent=None, rich_contract=False)
                episode.update(condition=condition, world_id=row['world_id'], task_id=row['task_id'],
                    task_sha256=row['task_sha256'], initial_prompt_sha256=row['initial_prompt_sha256'],
                    checkpoint_state_sha256=self.conditions[condition]['adapter']['state_sha256'],
                    source_store_sha256=results.digest(store), trainingAllowed=False, split='DEV_DIAGNOSTIC')
                path = self.root / condition / f'EPISODE_{index:02d}.json'
                self.write(path, episode)
                paths.append(self.ref(path))
            self.finish(condition, paths)
        self.write(self.root / 'TERMINAL.json', dict(status='COMPLETE',
            results=[self.read(self.root / f'{condition}_EXIT.json') for condition in results.STAGES],
            parent_calls=0, optimizer_steps=0, training_rows=0))

    def adapter_bytes(self, arm, cycle):
        return f'CPU fixture only, never a tensor: {arm}-{cycle}'.encode()

    def identity(self, arm, cycle):
        data = self.adapter_bytes(arm, cycle)
        return dict(path=f'/unavailable/checkpoints/{arm}-{cycle}',
            state_sha256=results.SEED if arm == 'SEED' else results.digest([arm, cycle]),
            base_sha256=results.BASE, files=[['adapter_model.safetensors', hashlib.sha256(data).hexdigest()]])

    def absolute_identity(self, condition):
        identity = self.conditions['SEED' if condition == 'SOURCE' else condition]['adapter']
        return dict(identity, path=str(self.bundle / identity['path']))

    def stage_start(self, condition, pid):
        identity = self.absolute_identity(condition)
        self.write(self.root / condition / 'LOADED.json', dict(condition=condition, adapter=identity,
            parent_free=True, fresh_process=True, optimizer_steps=0, process=['cpu-fixture-boot', pid, 1000]))
        self.write(self.root / condition / 'BINDING.json', dict(adapter=identity, plan_sha256=self.sha(self.plan_path),
            parent_present=False, fresh_process=True, phase='sealed_readout', cycle=0))
        self.write(self.root / f'{condition}_LAUNCH.json', dict(condition=condition, pid=pid))

    def generate(self, condition, messages, raw):
        self.sequence += 1
        name = f'CALL_{self.sequence:05d}.json'
        claim = self.root / 'claims' / name
        self.write(claim, dict(condition=condition, messages_sha256=results.digest(messages),
            cap=512, trainingAllowed=False, no_retry=True))
        response = dict(messages=deepcopy(messages), raw=raw, token_ids=[1, 2],
                        prompt_tokens=10, terminal=True, truncated=False)
        if self.truncate_source and condition == 'SOURCE' and raw == 'PRIVATE_FAILED_SOURCE_TEXT':
            response.update(terminal=False, truncated=True)
        path = self.root / condition / 'calls' / name
        self.write(path, dict(condition=condition, messages=deepcopy(messages), response=response,
                              status='COMPLETE', claim=self.ref(claim)))
        self.calls[condition].append(self.ref(path))
        return response

    def finish(self, condition, episodes):
        self.write(self.root / condition / 'COMPLETE.json', dict(status='COMPLETE', condition=condition,
            adapter=self.absolute_identity(condition), unchanged=True, parent_calls=0, optimizer_steps=0,
            training_rows=0, calls=self.calls[condition], episodes=episodes, store=self.ref(self.root / 'SOURCE/STORE.json')))
        self.write(self.root / f'{condition}_EXIT.json', dict(condition=condition, returncode=0, complete=True, no_retry=True))

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')

    def read(self, path):
        return json.loads(path.read_text())

    def sha(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def ref(self, path):
        return dict(path=str(path), sha256=self.sha(path))

    def rebind_call(self, condition, path):
        complete_path = self.root / condition / 'COMPLETE.json'
        complete = self.read(complete_path)
        complete['calls'] = [self.ref(Path(reference['path'])) for reference in complete['calls']]
        self.write(complete_path, complete)


class TransferResultsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = DiskFixture(self.temporary.name)

    def reduce(self, output=None):
        return results.reduce(self.fixture.plan_path, output, bootstrap_samples=100)

    def assert_incomplete(self, result, stage=None, code=None):
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertIsNone(result['analysis'])
        self.assertEqual(set(result['stages']), set(results.STAGES))
        if stage is not None:
            self.assertEqual(result['stages'][stage]['status'], 'INCOMPLETE')
            if code is not None:
                self.assertEqual(result['stages'][stage]['error'], code)

    def test_expired_plan_reduces_all_seven_with_sparse_source_and_no_raw_output(self):
        target = self.fixture.home / 'RESULTS.json'
        result = self.reduce(target)
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertTrue(result['source_ready'])
        self.assertEqual(result['store_size'], 16)
        self.assertEqual(result['source']['complete_worlds'], 0)
        self.assertEqual(result['source']['offered_events'], 64)
        self.assertEqual(len(result['analysis']['conditions']), 7)
        self.assertEqual(len(result['analysis']['comparisons']), 9)
        self.assertEqual(result['analysis']['conditions']['GUIDED_C2']['worlds'], 16)
        encoded = target.read_text()
        for forbidden in ('PRIVATE_FAILED_SOURCE_TEXT', 'PRIVATE_FAILED_EVAL_TEXT', 'Use the public task',
                          '"raw"', '"messages"', '"captures"', '"token_ids"'):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(json.loads(encoded), result)
        with self.assertRaises(FileExistsError):
            self.reduce(target)

    def test_missing_condition_withholds_compare_and_reports_other_stages(self):
        path = self.fixture.root / 'GUIDED_C4/COMPLETE.json'
        path.unlink()
        with patch.object(results.descriptive, 'compare') as compare:
            result = self.reduce()
        compare.assert_not_called()
        self.assert_incomplete(result, 'GUIDED_C4')
        self.assertEqual(result['stages']['UNPARENTED_C6']['status'], 'VERIFIED')
        self.assertEqual(result['stages']['GUIDED_C4']['episodes_seen'], 32)

    def test_missing_exit_is_incomplete_even_when_complete_exists(self):
        (self.fixture.root / 'SEED_EXIT.json').unlink()
        self.assert_incomplete(self.reduce(), 'SEED', 'missing_file')

    def test_nonzero_exit_and_false_unchanged_never_produce_contrasts(self):
        path = self.fixture.root / 'GUIDED_C2_EXIT.json'
        receipt = self.fixture.read(path)
        receipt['returncode'] = 1
        self.fixture.write(path, receipt)
        path = self.fixture.root / 'GUIDED_C4/COMPLETE.json'
        complete = self.fixture.read(path)
        complete['unchanged'] = False
        self.fixture.write(path, complete)
        result = self.reduce()
        self.assert_incomplete(result, 'GUIDED_C2', 'failed_or_incomplete_exit')
        self.assert_incomplete(result, 'GUIDED_C4', 'complete_identity_or_state_mismatch')

    def test_failed_inference_cannot_hide_under_successful_complete(self):
        path = Path(self.fixture.calls['SEED'][0]['path'])
        call = self.fixture.read(path)
        call['status'] = 'FAILED'
        self.fixture.write(path, call)
        self.fixture.rebind_call('SEED', path)
        self.assert_incomplete(self.reduce(), 'SEED', 'failed_or_wrong_condition_inference')

    def test_source_failed_inference_prevents_source_ready(self):
        path = Path(self.fixture.calls['SOURCE'][0]['path'])
        call = self.fixture.read(path)
        call['status'] = 'FAILED'
        self.fixture.write(path, call)
        self.fixture.rebind_call('SOURCE', path)
        result = self.reduce()
        self.assert_incomplete(result, 'SOURCE', 'failed_or_wrong_condition_inference')
        self.assertFalse(result['source_ready'])

    def test_loaded_actual_checkpoint_mismatch(self):
        path = self.fixture.root / 'GUIDED_C2/LOADED.json'
        loaded = self.fixture.read(path)
        loaded['adapter']['state_sha256'] = results.SEED
        self.fixture.write(path, loaded)
        self.assert_incomplete(self.reduce(), 'GUIDED_C2', 'loaded_identity_or_state_mismatch')

    def test_plan_source_or_export_file_drift(self):
        path = self.fixture.source / 'gpu/orch_r127_route_transfer.py'
        path.write_text('drift')
        result = self.reduce()
        self.assert_incomplete(result)
        self.assertIn('file_hash_mismatch', result['errors'])

    def test_checkpoint_file_bytes_verified_without_loading_model(self):
        path = self.fixture.bundle / 'conditions/GUIDED_C2/adapter/adapter_model.safetensors'
        path.write_bytes(b'drift')
        result = self.reduce()
        self.assert_incomplete(result)
        self.assertIn('file_hash_mismatch', result['errors'])

    def test_store_content_hash_is_recomputed(self):
        path = self.fixture.root / 'SOURCE/STORE.json'
        stored = self.fixture.read(path)
        stored['store'][next(iter(stored['store']))] = 'FABRICATED_RAW'
        self.fixture.write(path, stored)
        for condition in results.STAGES:
            complete_path = self.fixture.root / condition / 'COMPLETE.json'
            complete = self.fixture.read(complete_path)
            complete['store'] = self.fixture.ref(path)
            self.fixture.write(complete_path, complete)
        self.assert_incomplete(self.reduce(), 'SOURCE', 'source_store_content_hash_mismatch')

    def test_store_reconstructed_from_accepted_source_records_not_attestation(self):
        path = self.fixture.root / 'SOURCE/STORE.json'
        stored = self.fixture.read(path)
        stored['store'][next(iter(stored['store']))] = 'FABRICATED_RAW'
        stored['source_store_sha256'] = results.digest(stored['store'])
        self.fixture.write(path, stored)
        complete_path = self.fixture.root / 'SOURCE/COMPLETE.json'
        complete = self.fixture.read(complete_path)
        complete['store'] = self.fixture.ref(path)
        self.fixture.write(complete_path, complete)
        self.assert_incomplete(self.reduce(), 'SOURCE', 'source_store_reconstruction_mismatch')

    def test_call_ref_hash_checked(self):
        path = Path(self.fixture.calls['SEED'][0]['path'])
        call = self.fixture.read(path)
        call['response']['token_ids'] = [99]
        self.fixture.write(path, call)
        self.assert_incomplete(self.reduce(), 'SEED', 'file_hash_mismatch')

    def test_full_response_join_includes_token_ids_not_just_raw_text(self):
        path = Path(self.fixture.calls['SEED'][0]['path'])
        call = self.fixture.read(path)
        call['response']['token_ids'] = [99]
        self.fixture.write(path, call)
        self.fixture.rebind_call('SEED', path)
        self.assert_incomplete(self.reduce(), 'SEED', 'capture_call_full_response_mismatch')

    def test_claim_prompt_hash_checked(self):
        path = Path(self.fixture.calls['SEED'][0]['path'])
        call = self.fixture.read(path)
        claim_path = Path(call['claim']['path'])
        claim = self.fixture.read(claim_path)
        claim['messages_sha256'] = '0' * 64
        self.fixture.write(claim_path, claim)
        call['claim'] = self.fixture.ref(claim_path)
        self.fixture.write(path, call)
        self.fixture.rebind_call('SEED', path)
        self.assert_incomplete(self.reduce(), 'SEED', 'call_claim_mismatch')

    def test_hashref_path_escape_not_read(self):
        complete_path = self.fixture.root / 'SEED/COMPLETE.json'
        complete = self.fixture.read(complete_path)
        complete['store']['path'] = str(self.fixture.home / 'FINAL.json')
        self.fixture.write(complete_path, complete)
        self.assert_incomplete(self.reduce(), 'SEED', 'hashref_path_mismatch')

    def test_extra_claim_without_capture_prevents_complete(self):
        path = self.fixture.root / 'claims' / f'CALL_{self.fixture.sequence + 1:05d}.json'
        self.fixture.write(path, dict(condition='SEED'))
        result = self.reduce()
        self.assert_incomplete(result)
        self.assertIn('uncharged_or_unjoined_calls', result['errors'])

    def test_missing_episode_or_extra_call_is_not_filtered(self):
        (self.fixture.root / 'SEED/EPISODE_00.json').unlink()
        self.fixture.write(self.fixture.root / 'GUIDED_C2/calls/CALL_99999.json', {})
        result = self.reduce()
        self.assert_incomplete(result, 'SEED', 'episode_panel_incomplete')
        self.assert_incomplete(result, 'GUIDED_C2', 'call_manifest_count_mismatch')

    def test_source_world_not_filtered(self):
        (self.fixture.root / 'SOURCE/WORLD_00.json').unlink()
        self.assert_incomplete(self.reduce(), 'SOURCE', 'source_world_panel_mismatch')

    def test_fresh_process_identity_cannot_be_reused(self):
        seed_loaded = self.fixture.read(self.fixture.root / 'SEED/LOADED.json')
        loaded_path = self.fixture.root / 'GUIDED_C2/LOADED.json'
        loaded = self.fixture.read(loaded_path)
        loaded['process'] = seed_loaded['process']
        self.fixture.write(loaded_path, loaded)
        launch_path = self.fixture.root / 'GUIDED_C2_LAUNCH.json'
        self.fixture.write(launch_path, dict(condition='GUIDED_C2', pid=loaded['process'][1]))
        self.assert_incomplete(self.reduce(), 'GUIDED_C2', 'evaluation_process_reused')

    def test_mutation_during_reduction_withholds_already_computed_analysis(self):
        original = results.descriptive.compare

        def changing_compare(*args, **kwargs):
            value = original(*args, **kwargs)
            path = self.fixture.root / 'SEED/LOADED.json'
            path.write_text(path.read_text() + ' ')
            return value

        with patch.object(results.descriptive, 'compare', side_effect=changing_compare):
            result = self.reduce()
        self.assert_incomplete(result)
        self.assertIn('file_hash_mismatch', result['errors'])

    def test_null_expected_hash_is_not_treated_as_unbound(self):
        plan = self.fixture.read(self.fixture.plan_path)
        plan['export_sha256'] = None
        self.fixture.write(self.fixture.plan_path, plan)
        result = self.reduce()
        self.assert_incomplete(result)
        self.assertIn('invalid_file_hash', result['errors'])

    def test_episode_byte_hash_and_condition_store_hash_are_required(self):
        path = self.fixture.root / 'SEED/EPISODE_00.json'
        path.write_text(path.read_text() + ' ')
        complete_path = self.fixture.root / 'GUIDED_C2/COMPLETE.json'
        complete = self.fixture.read(complete_path)
        complete['store']['sha256'] = '0' * 64
        self.fixture.write(complete_path, complete)
        result = self.reduce()
        self.assert_incomplete(result, 'SEED', 'file_hash_mismatch')
        self.assert_incomplete(result, 'GUIDED_C2', 'file_hash_mismatch')

    def test_not_started_stage_has_explicit_progress_status(self):
        (self.fixture.root / 'UNPARENTED_C6').rename(self.fixture.home / 'not_published_stage')
        (self.fixture.root / 'UNPARENTED_C6_EXIT.json').rename(self.fixture.home / 'not_published_exit.json')
        result = self.reduce()
        self.assert_incomplete(result)
        self.assertEqual(result['stages']['UNPARENTED_C6']['status'], 'NOT_STARTED')
        self.assertEqual(result['stages']['UNPARENTED_C6']['calls_seen'], 0)

    def test_symlinked_receipt_is_rejected_before_following_it(self):
        path = self.fixture.root / 'SEED/BINDING.json'
        outside = self.fixture.home / 'outside.json'
        path.rename(outside)
        path.symlink_to(outside)
        self.assert_incomplete(self.reduce(), 'SEED', 'symlink_or_path_escape')

    def test_malformed_json_never_echoes_private_input(self):
        path = self.fixture.root / 'SEED/LOADED.json'
        path.write_text('PRIVATE_INVALID_JSON_SECRET')
        result = self.reduce()
        self.assert_incomplete(result, 'SEED', 'invalid_json')
        self.assertNotIn('PRIVATE_INVALID_JSON_SECRET', json.dumps(result))

    def test_truncated_source_generation_is_unavailable_not_failed_inference(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.fixture = DiskFixture(temporary, truncate_source=True)
            result = self.reduce()
        self.assertEqual(result['status'], 'COMPLETE', result)
        self.assertTrue(result['source_ready'])
        self.assertEqual(result['store_size'], 16)
        self.assertEqual(result['source']['complete_worlds'], 0)


if __name__ == '__main__':
    unittest.main()
