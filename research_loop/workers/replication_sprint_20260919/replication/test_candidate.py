"""CPU-only regression tests; no GPU, services, SSH or model dependencies."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

import construct_candidate as candidate
from inspect_originals import reduce_cells
import sampling_cells


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECEIPT = json.loads((HERE / 'ORIGINALS_RECEIPT.json').read_bytes())
NOW = RECEIPT['observed_unix']


class Backend:
    def __init__(self, empty=False):
        self.seeds = []
        self.requests = []
        self.empty = empty

    def seed(self, seed):
        self.seeds.append(seed)

    def generate(self, messages, max_new_tokens):
        self.requests.append(deepcopy(messages))
        return dict(messages=deepcopy(messages), raw='A candidate caption.',
            token_ids=[] if self.empty else [17] * max_new_tokens,
            prompt_tokens=10, terminal=False, truncated=True)


class CandidateTests(unittest.TestCase):
    def build(self, receipt=None, seeds=(23301, 23302), block='c2', now=NOW):
        return candidate.build(receipt or RECEIPT, seeds, block, now)

    def test_original_pair_is_complete_without_replay(self):
        result = candidate.align_original_pair(RECEIPT)
        self.assertEqual(result['learner']['per_seed']['23201']['new_pixels'], 0)
        self.assertEqual(result['learner']['per_seed']['23202']['new_pixels'], 11)
        self.assertEqual(result['sibling']['per_seed']['23201']['new_pixels'], 14)
        self.assertEqual(result['sibling']['per_seed']['23202']['new_pixels'], 14)

    def test_never_mix_original_and_adopted_judges(self):
        changed = deepcopy(RECEIPT)
        changed['rows']['original_learner24'] = changed['rows']['adopted_learner24']
        with self.assertRaisesRegex(ValueError, 'original_pair_same_protocol'):
            candidate.align_original_pair(changed)

    def test_new_sampling_epoch_preserves_protocol(self):
        original = deepcopy(RECEIPT)
        result = self.build()
        self.assertEqual(result['sampling_epoch']['sampling_seeds'], [23301, 23302])
        self.assertEqual(result['sampling_epoch']['judge_epoch_sha256'], candidate.ADOPTED_EPOCH)
        self.assertEqual(result['runtime_estimate']['generated_tokens'], 18432)
        self.assertEqual(RECEIPT, original)

    def test_pair_replication_is_two_sources(self):
        result = self.build(block='pair24')
        self.assertEqual(list(result['configs']), list(candidate.BLOCKS['pair24']))
        self.assertEqual(result['runtime_estimate']['generated_tokens'], 12288)

    def test_duplicate_historic_or_noninteger_seeds_rejected(self):
        for seeds in ((23201, 23301), (23301, 23301), (23301,), (True, 23301), (-1, 23302), (2**32, 23302)):
            with self.subTest(seeds=seeds), self.assertRaises(ValueError):
                self.build(seeds=seeds)

    def test_no_forged_new_runtime_or_guard(self):
        result = self.build()
        self.assertIsNone(result['launch_intent'])
        self.assertIsNone(result['capsule'])
        self.assertFalse(result['execution_allowed'])
        self.assertFalse(result['consumed_guard_reused'])
        for config in result['configs'].values():
            self.assertNotIn('deadline_unix', config)
            self.assertNotIn('root', config)
            self.assertNotIn('guard', config)
            self.assertTrue(config['receive_verification_required'])

    def test_seed_changes_get_different_epoch_identity(self):
        self.assertNotEqual(self.build()['sampling_epoch_sha256'],
            self.build(seeds=(23303, 23304))['sampling_epoch_sha256'])

    def test_time_does_not_change_scientific_epoch(self):
        self.assertEqual(self.build()['sampling_epoch_sha256'],
            self.build(now=NOW + 100)['sampling_epoch_sha256'])

    def test_existing_lease_not_extended(self):
        end = RECEIPT['queue']['policy']['lease_end_unix']
        with self.assertRaisesRegex(ValueError, 'existing_host_lease'):
            self.build(now=end - 60)
        self.assertEqual(self.build()['resource_policy']['lease_end_unix'], end)

    def test_c2_keeps_stricter_original_preparation_bound(self):
        self.assertEqual(self.build()['effective_hard_end_unix'], candidate.C2_PREPARATION_BOUND)
        with self.assertRaisesRegex(ValueError, 'existing_host_lease_and_source_bound'):
            self.build(now=candidate.C2_PREPARATION_BOUND - 60)

    def test_changed_judge_or_source_rejected(self):
        for field in ('source_manifest_sha256', 'adapter_sha256', 'primary_config_sha256'):
            changed = deepcopy(RECEIPT)
            changed['rows']['c2sleep51']['config'][field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(changed)

    def test_changed_scene_panel_extractor_or_decoder_rejected(self):
        for field in candidate.INVARIANT_FILES:
            changed = deepcopy(RECEIPT)
            changed['rows']['c2sleep51']['files'][field]['sha256'] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(changed)
        changed = deepcopy(RECEIPT)
        changed['rows']['c2sleep51']['identity']['decoder']['temperature'] = 0.5
        with self.assertRaises(ValueError):
            self.build(changed)
        changed = deepcopy(RECEIPT)
        changed['rows']['c2sleep51']['source_closure']['extractor.py'] = 'changed'
        with self.assertRaises(ValueError):
            self.build(changed)

    def test_context_or_learning_not_admitted(self):
        for field, value in (('parent_tokens', 1), ('training_updates', 1), ('source_context_loaded', True)):
            changed = deepcopy(RECEIPT)
            changed['rows']['c2sleep117']['config'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(changed)

    def test_partial_budget_or_mismatched_checkpoint_rejected(self):
        changed = deepcopy(RECEIPT)
        changed['rows']['c2sleep51']['cell_budgets'][0]['generated_tokens'] = 512
        with self.assertRaises(ValueError):
            self.build(changed)
        changed = deepcopy(RECEIPT)
        changed['rows']['c2sleep51']['source_age']['adapter_state_sha256'] = 'changed'
        with self.assertRaises(ValueError):
            self.build(changed)

    def test_reducer_deduplicates_by_scene_and_seed(self):
        scored = dict(caption_sha256='synthetic-caption', result=dict(rank=25, accepted=True, status='new_pixel'))
        event = dict(origin=dict(stage='ACT'), score=dict(results=[scored, scored]))
        cells = [dict(contest_id='synthetic-scene', seed=seed, generated_tokens=12, events=[event, event])
            for seed in (11, 12)]
        reduced = reduce_cells(cells)
        for row in reduced.values():
            self.assertEqual(row['new_pixels'], 1)
            self.assertEqual(row['distinct_accepted'], 1)


class SamplingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = RECEIPT['rows']['base']['source_closure'][candidate.CONTRACT]
        cls.contract = sampling_cells.load_contract(REPO, cls.expected)

    def setUp(self):
        self.plan = candidate.build(RECEIPT, (23301, 23302), 'c2', NOW)
        self.scenes = [dict(contest_id='synthetic_' + str(index), canonical_scene='Test scene.')
            for index in range(3)]
        self.scored = []

    def score(self, contest, seed, raw, stage, origin):
        self.scored.append((contest, seed, stage, origin))
        return dict(feedback='No caption was scored. Continue with a caption.', results=[])

    def run_cells(self, backend):
        return sampling_cells.run_cells(self.contract, backend, self.scenes, self.plan,
            self.score, lambda *args: None)

    def test_exact_six_cell_order_and_token_budget(self):
        backend = Backend()
        result = self.run_cells(backend)
        self.assertEqual(result['actual_generated_tokens'], 6144)
        self.assertEqual(backend.seeds, [23301, 23302] * 3)
        self.assertEqual(len(result['cells']), 6)
        self.assertTrue(all(row['generated_tokens'] == 1024 for row in result['cells']))
        self.assertEqual([row['seed'] for row in result['cells']], [23301, 23302] * 3)

    def test_feedback_and_think_act_structure_unchanged(self):
        backend = Backend()
        self.run_cells(backend)
        self.assertEqual([item[2] for item in self.scored[:4]], ['THINK', 'ACT', 'THINK', 'ACT'])
        self.assertIn('Tool feedback:', backend.requests[1][-2]['content'])
        self.assertTrue(all(request[0]['content'] == self.contract.SYSTEM for request in backend.requests))

    def test_private_panel_fields_rejected(self):
        self.scenes[0]['selected'] = ['synthetic-private-panel']
        with self.assertRaisesRegex(ValueError, 'scene_only'):
            self.run_cells(Backend())

    def test_zero_token_failure_not_retried(self):
        backend = Backend(empty=True)
        result = self.run_cells(backend)
        self.assertEqual(result['status'], 'INCOMPLETE_NOT_ZERO_NO_RETRY')
        self.assertEqual(backend.seeds, [23301])

    def test_protocol_source_hash_must_match(self):
        with self.assertRaisesRegex(ValueError, 'original_contract_bytes'):
            sampling_cells.load_contract(REPO, 'synthetic-wrong-hash')

    def test_changed_epoch_rejected(self):
        self.plan['sampling_epoch']['sampling_seeds'] = [23201, 23202]
        with self.assertRaisesRegex(ValueError, 'sampling_epoch_binding'):
            self.run_cells(Backend())


if __name__ == '__main__':
    unittest.main()
