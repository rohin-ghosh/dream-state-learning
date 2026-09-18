import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_rich_hot_node2_exhaustion_v3 as run
from gpu import orch_rich_hot_node2_exhaustion_v3_guard as guard
from organism_v6 import orch_rich_hot_node2_exhaustion_v3 as policy


class ExhaustionTests(unittest.TestCase):
    def document(self):
        return policy.prior.cohort([dict(question=f'Unseen task {index}', answer='#### 42') for index in range(12)],
                                   dict(tasks=[], excluded_ids=[], excluded_question_hashes=[]))

    def test_pair_same_tasks_guidance_and_no_methods_supplied(self):
        document = self.document()
        for position in range(0, 24, 2):
            left, right = policy.task_at(document, 0, position, 0), policy.task_at(document, 0, position + 1, 1)
            self.assertEqual(left, right)
            if left['family'] != 'route':
                self.assertEqual(policy.messages(left, 0), policy.messages(right, 1))
                self.assertNotIn('Steering degree', policy.messages(left, 0)[0]['content'])
        self.assertEqual(policy.guidance(0), policy.guidance(1))
        self.assertEqual(policy.STEERING[0], '')
        for shard in range(2, 8):
            self.assertIn(f'Steering degree{shard // 2}', policy.guidance(shard))

    def test_claims_repetition_and_rejections_are_not_oracle_admission(self):
        task = dict(family='math', payload=dict(gold='42'))
        sentence = 'This is a deliberately repeated long sentence with at least twelve words to exercise the repetition screen.'
        response = dict(raw='APPROACH 1: direct\nAPPROACH 2: reject an alternative\n' + '\n'.join([sentence] * 3) + '\nFINAL: 42',
                        terminal=True, truncated=False, token_ids=[1] * 100 + [2])
        result = policy.outcome(task, response)
        self.assertTrue(result['correct'])
        self.assertEqual(result['claimed_approach_count'], 2)
        self.assertIsNone(result['audited_semantic_worked_methods'])
        self.assertTrue(result['repetition_failure_screen'])
        self.assertEqual(result['repeated_long_sentence_count'], 2)
        self.assertFalse(result['admitted'])
        self.assertFalse(result['trainingAllowed'])

    def test_second_pass_remaining_context_and_global_caps(self):
        self.assertEqual(policy.effective_budget(512), 16384)
        self.assertEqual(policy.effective_budget(17000), 15768)
        for invalid in (0, 32768, 32769):
            with self.assertRaises(ValueError):
                policy.effective_budget(invalid)
        self.assertEqual(policy.remaining_cap([8000] * 8, [0] * 8, 0), 192)
        self.assertEqual(policy.remaining_cap([8192] * 8, [0] * 8, 1), 0)

    def test_reservation_includes_old_usage_source_and_effective_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, old, derived = [Path(temporary) / name for name in ('new', 'old', 'derived')]
            for directory in (root, old, derived):
                (directory / 'reservations').mkdir(parents=True)
            (root / 'LIFETIME.json').write_text('{"native_deadline_unix":9999999999}')
            (old / 'reservations/1_prior.json').write_text('{}')
            prepared = dict(identities={'1': {'state_sha256': '37ec'}}, source_sha256='source', checkpoint_commit_sha256='checkpoint')
            task = dict(id='V3-B000-P01', family='code', source_task_id='ledger_001', repeated_train_source=False)
            with patch.object(run, 'ROOT', root), patch.object(run, 'FLOOR', old), patch.object(run, 'DERIVED', derived):
                row = run.reserve(prepared, 1, task, 'final_0', [], 17000)
                self.assertEqual(row['historical_reserved_before'], 1)
                self.assertEqual(row['generator_identity'], prepared['identities']['1'])
                self.assertEqual(row['max_new_tokens'], 15768)
                self.assertEqual(row['target_max_new_tokens'], 16384)
                self.assertEqual(row['prompt_version'], policy.VERSION)
                self.assertFalse(row['trainingAllowed'])
                self.assertEqual(json.loads((root / 'reservations/1_V3-B000-P01_final_0.json').read_text()), row)

    def test_unresolved_request_blocks_closed_boundary_even_after_zombie(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'shard0').mkdir()
            (root / 'reservations').mkdir()
            (root / 'LAUNCH_0.json').write_text('{"identity":{"pid":123}}')
            (root / 'shard0/AFTER.json').write_text('{"unchanged":true}')
            (root / 'shard0/TERMINAL.json').write_text('{"status":"BOUNDED_STOP"}')
            (root / 'reservations/0_task_final.json').write_text('{"index":0,"task_id":"task","stage":"final"}')
            with patch.object(guard, 'process_state', return_value='Z'):
                self.assertFalse(guard.closed(root, 0))
                (root / 'shard0/task_final.json').write_text('{"index":0}')
                self.assertTrue(guard.closed(root, 0))
            with patch.object(guard, 'process_state', return_value='R'):
                self.assertFalse(guard.closed(root, 0))

    def test_signal_requires_exact_identity_and_never_signals_zombie(self):
        with patch.object(guard, 'process_state', return_value='Z'), patch.object(guard.os, 'pidfd_open') as opener:
            self.assertFalse(guard.signal_exact({'pid': 123}, 2))
            opener.assert_not_called()
        with patch.object(guard, 'process_state', side_effect=ValueError('exact_owned_identity_required')):
            with self.assertRaises(ValueError):
                guard.signal_exact({'pid': 123}, 2)


if __name__ == '__main__':
    unittest.main()
