from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import orch_r144_kernel4_recovery as recovery


def offending_row():
    tokens = [42] * 512
    for offset in (362, 372, 373):
        tokens[offset] = 151644
    return dict(source_sha256=recovery.OFFENDING, split='TRAIN', actor='child', prefix_loss=False,
        target_loss=True, token_ids=tokens, terminal=False, truncated=True,
        prefix=[{'role': 'user', 'content': 'unchanged parent context'}], target='original raw text')


class ExclusionTests(unittest.TestCase):
    def test_exact_row_only_and_input_unchanged(self):
        rows = [dict(offending_row(), source_sha256='a'*64), offending_row()]
        before = deepcopy(rows)
        original = Mock(side_effect=lambda values, context: (values, []))
        accepted, excluded = recovery.eligible_rows(rows, {}, original)
        self.assertEqual(accepted, rows[:1])
        self.assertEqual(rows, before)
        self.assertEqual(excluded, [dict(source_sha256=recovery.OFFENDING, reason=recovery.REASON)])
        original.assert_called_once_with(rows[:1], {})

    def test_same_exclusion_applies_in_rehearsal(self):
        accepted, excluded = recovery.eligible_rows([offending_row()], {}, lambda rows, context: (rows, []))
        self.assertEqual(accepted, [])
        self.assertEqual(len(excluded), 1)

    def test_other_special_token_rows_are_not_silently_filtered(self):
        row = dict(offending_row(), source_sha256='f'*64)
        accepted, excluded = recovery.eligible_rows([row], {}, lambda rows, context: (rows, []))
        self.assertEqual(accepted, [row])
        self.assertEqual(excluded, [])

    def test_mutated_offending_token_positions_rejected(self):
        row = offending_row()
        row['token_ids'][362] = 42
        with self.assertRaisesRegex(ValueError, 'exact_offending_generated_delimiters'):
            recovery.eligible_rows([row], {}, lambda rows, context: (rows, []))

    def test_parent_or_held_or_loss_mask_mutation_rejected(self):
        for changed in ({'actor': 'parent'}, {'split': 'HELD'}, {'prefix_loss': True}, {'target_loss': False}):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'exact_child_exclusion_provenance'):
                recovery.eligible_rows([dict(offending_row(), **changed)], {}, lambda rows, context: (rows, []))

    def test_unrelated_original_exception_propagates(self):
        with self.assertRaisesRegex(RuntimeError, 'unrelated'):
            recovery.eligible_rows([], {}, Mock(side_effect=RuntimeError('unrelated')))

    def test_corrected_eligibility_changes_only_one_target(self):
        before = dict(new_row_sha256=['a', 'b', recovery.OFFENDING], rehearsal_row_sha256=['c'],
            excluded=[], raw_modified=False, version='original')
        after = recovery.corrected_eligibility(before)
        self.assertEqual(before['new_row_sha256'], ['a', 'b', recovery.OFFENDING])
        self.assertEqual(after['new_row_sha256'], ['a', 'b'])
        self.assertEqual(after['rehearsal_row_sha256'], ['c'])
        self.assertFalse(after['raw_modified'])
        self.assertEqual(after['excluded'][0]['cohort'], 'NEW')


class ReplayTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.destination = root/'recovery'
        self.records = [{'kind': 'METADATA', 'document': {}} for unused in range(1598)]
        outputs = []
        for number, index in enumerate((1585, 1588, 1592)):
            self.records[index]['document'] = dict(messages=[{'role': 'user', 'content': str(number)}],
                max_new_tokens=512, deadline_unix=10**12)
            response = {'raw': str(number), 'token_ids': [number]}
            self.records[index+1]['document'] = dict(response=response)
            outputs.append(response)
        directory = root/'stream'/'records'
        directory.mkdir(parents=True)
        for index in range(1583, 1598):
            for suffix in ('.json', '.intent.json'):
                (directory/(f'{index:020d}'+suffix)).write_text('{}')
        self.journal = SimpleNamespace(root=directory.parent, _mutex=threading.RLock())
        self.snapshot = dict(sha256='original', state={'history': ['unchanged'], 'carry': ['unchanged'], 'pending': 'sleep19'})
        self.stream = SimpleNamespace(checkpoint=lambda: deepcopy(self.snapshot))
        self.child = SimpleNamespace(plan={'hard_end_unix': 10**12}, optimizer_steps=1323,
            adapter_hash=lambda: 'saved_adapter', generate=Mock(side_effect=outputs),
            engine=SimpleNamespace(verify_base=Mock()), torch=object())
        evidence = {'run1/checkpoints/sleep_000018/COMMIT.json': json.dumps({'adapter_state_sha256': 'saved_adapter'}).encode()}
        for name, replacement in [('RECOVERY', self.destination), ('verify_manifest', Mock()),
                ('runtime_environment', Mock(return_value={})), ('pinned_evidence', Mock(return_value=evidence)),
                ('verify_runtime', Mock(return_value='original_recipe')), ('bind', Mock(return_value=self.records)),
                ('restore', Mock(return_value='optimizer')), ('rng', Mock(return_value={'rng': 'saved'})),
                ('optimizer_fingerprint', Mock(return_value='optimizer'))]:
            patcher = patch.object(recovery, name, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_three_exact_replays_preserve_state_and_zero_learning(self):
        result = recovery.recover_rng(self.child, self.stream, self.journal, {}, {})
        self.assertEqual(result['matched_generations'], 3)
        self.assertEqual(result['optimizer_steps'], 1323)
        self.assertEqual(result['optimizer_updates'], 0)
        self.assertTrue(result['pending_unchanged'])
        self.assertEqual(self.child.generate.call_count, 3)
        self.assertFalse(result['original_postgeneration_rng_snapshot_available'])
        self.assertTrue((self.destination/'GENERATIONS_VERIFIED.json').exists())

    def test_replay_mismatch_fails_without_claiming_completion(self):
        self.child.generate.side_effect = [{'raw': 'wrong'}]
        with self.assertRaisesRegex(ValueError, 'exact_generation_match:0'):
            recovery.recover_rng(self.child, self.stream, self.journal, {}, {})
        self.assertTrue((self.destination/'FAILED.json').exists())
        self.assertFalse((self.destination/'GENERATIONS_VERIFIED.json').exists())

    def test_pending_history_mutation_fails(self):
        def generate(*args, **kwargs):
            self.snapshot['state']['carry'] = ['changed']
            return {'raw': '0', 'token_ids': [0]}
        self.child.generate.side_effect = generate
        with self.assertRaisesRegex(ValueError, 'no_replay_history_plan_mutation'):
            recovery.recover_rng(self.child, self.stream, self.journal, {}, {})


class OriginalAdmissionTests(unittest.TestCase):
    def test_original_guard_and_scan_are_not_replaced(self):
        from gpu import orch_r125_continual_guard as original
        adapted = recovery.adapted_supervisor()
        self.assertIs(adapted.__globals__['validate'], original.validate)
        self.assertIs(adapted.__globals__['subprocess'], original.subprocess)
        constants = adapted.__code__.co_consts
        self.assertIn('gpu.orch_r125_continual_guard', constants)
        self.assertIn('gpu.orch_r144_kernel4_recovery', constants)

    def test_only_owned_UUID_inherited(self):
        torch = SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: 1))
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': recovery.GPU_UUID}, clear=True):
            self.assertTrue(recovery.runtime_environment(torch, ('CUDA_VISIBLE_DEVICES='+recovery.GPU_UUID).encode())['proc_environ_verified'])
            with self.assertRaisesRegex(ValueError, 'inherited_original_GPU_UUID'):
                recovery.runtime_environment(torch, b'CUDA_VISIBLE_DEVICES=0')


if __name__ == '__main__':
    unittest.main()
