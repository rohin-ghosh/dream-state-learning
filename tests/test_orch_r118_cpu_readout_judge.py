import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r118_cpu_readout_judge as batch


class ReadoutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ids = ['DEV-' + str(index) for index in range(8)]
        batch.write(self.root / 'COHORT.json', dict(held=[dict(id=identifier) for identifier in self.ids]))
        batch.write(self.root / 'SEALED_FINAL.json', dict(secret='FINAL_MUST_NOT_LEAK'))
        self.checkpoint = self.root / 'checkpoint.json'
        batch.write(self.checkpoint, dict(private='PRIVATE_CHECKPOINT'))
        for cycle in (0, 1):
            directory = self.root / f'readout_{cycle:04d}'
            batch.write(directory / 'COMPLETE.json', dict(fresh_process=True, context_free=True,
                parent_calls=0, held_tasks=8, oracle='HIDDEN_VERDICT'))
            batch.write(directory / 'LAUNCH.json', dict(parent_free=True, checkpoint=str(self.checkpoint)))
            batch.write(directory / 'LOADED.json', dict(parent_free=True, checkpoint_sha256=batch.sha(self.checkpoint)))
            batch.write(directory / 'PROCESS_RESULT.json', dict(status='COMPLETE'))
            caches = []
            for index, task_id in enumerate(self.ids):
                response = dict(raw='READ EVENT X', token_ids=[10, 11, 12], input_truncated=False,
                    full_prompt_prefix_verified=True, truncated=False,
                    messages=[dict(role='system', content='PRIVATE_SYSTEM'),
                        dict(role='user', content='Public task'), dict(role='tool', content='Visible feedback')])
                batch.write(directory / f'CALL_{index:06d}.json', dict(task_id=task_id, condition='LORA_ON',
                    parent_free=True, status='COMPLETE', response=response))
                caches.append([response])
            batch.write(directory / 'HELD.json', dict(scope='dev', selection=False, ids=self.ids,
                cached_responses=caches, records=[dict(correct='ORACLE_SECRET')]))

    def replace(self, path, **updates):
        value = batch.read(path)
        value.update(updates)
        path.write_text(json.dumps(value))

    def test_complete_inventory_blind_payload_and_native_counts(self):
        rows = batch.collect(self.root, [0, 1])
        self.assertEqual(len(rows), 16)
        for row in rows:
            request = json.dumps(row['request'])
            for secret in ('FINAL_MUST_NOT_LEAK', 'HIDDEN_VERDICT', 'ORACLE_SECRET', 'PRIVATE_CHECKPOINT', 'PRIVATE_SYSTEM'):
                self.assertNotIn(secret, request)
            self.assertIn('Visible feedback', request)
            self.assertEqual(row['private_provenance']['child_token_ids'], 3)
            self.assertFalse(row['private_provenance']['training_buffer'])

    def test_complete_marker_without_successful_process_rejected(self):
        self.replace(self.root / 'readout_0001/PROCESS_RESULT.json', status='CRASHED_READOUT_CONTINUE_LIFE')
        with self.assertRaisesRegex(ValueError, 'process_completed'):
            batch.collect(self.root, [1])

    def test_missing_call_not_silently_skipped(self):
        (self.root / 'readout_0000/CALL_000001.json').unlink()
        with self.assertRaisesRegex(ValueError, 'match_native_capture'):
            batch.collect(self.root, [0])

    def test_wrong_checkpoint_rejected(self):
        self.replace(self.root / 'readout_0000/LOADED.json', checkpoint_sha256='wrong')
        with self.assertRaisesRegex(ValueError, 'exact_saved_checkpoint'):
            batch.collect(self.root, [0])

    def test_final_scope_rejected_without_reading_sealed_file(self):
        self.replace(self.root / 'readout_0000/HELD.json', scope='final')
        with self.assertRaisesRegex(ValueError, 'DEV_only'):
            batch.collect(self.root, [0])

    def test_changed_cache_rejected(self):
        path = self.root / 'readout_0000/HELD.json'
        held = batch.read(path)
        held['cached_responses'][0][0]['raw'] = 'fabricated extra reasoning'
        path.write_text(json.dumps(held))
        with self.assertRaisesRegex(ValueError, 'match_native_capture'):
            batch.collect(self.root, [0])

    def test_reordered_held_ids_rejected(self):
        self.replace(self.root / 'readout_0000/HELD.json', ids=list(reversed(self.ids)))
        with self.assertRaisesRegex(ValueError, 'DEV_only'):
            batch.collect(self.root, [0])

    def test_missing_prefix_is_not_eligible(self):
        path = self.root / 'readout_0000/HELD.json'
        held = batch.read(path)
        held['cached_responses'][0][0]['input_truncated'] = True
        path.write_text(json.dumps(held))
        with self.assertRaisesRegex(ValueError, 'complete_causal_prefix'):
            batch.collect(self.root, [0])

    def test_unknown_annotation_and_bound_not_negative(self):
        document = dict(kind='held', task_text='Public', child_text='READ EVENT X')
        for raw, terminated in (('{}', True), ('not-json', True), ('{}', False)):
            result = batch.interpret(document, raw, terminated)
            self.assertEqual(result['status'], 'UNRESOLVED')
            self.assertIsNone(result['shifts'])

    def test_actual_schema_valid_annotation(self):
        document = dict(kind='held', task_text='Public', child_text='READ EVENT X')
        annotation = dict(status='COMPLETE', reason='', sentences=[dict(index=0, label='MAIN',
            legacy_template_check=False, evidence='A command')], shift_sentence_indices=[], classes=[])
        result = batch.interpret(document, json.dumps(annotation), True)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['departures_and_returns'], 0)

    def test_cpu_scope_explicit_and_no_overwrite(self):
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': '0'}):
            with self.assertRaisesRegex(ValueError, 'no_visible_GPU'):
                batch.cpu_environment()
        with patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES': ''}):
            batch.cpu_environment()
        with self.assertRaises(FileExistsError):
            batch.write(self.checkpoint, {})

    def test_duplicate_or_unbounded_cycles_rejected(self):
        for cycles in ([], [0, 0], list(range(9)), [-1], [True]):
            with self.assertRaises(ValueError):
                batch.collect(self.root, cycles)


if __name__ == '__main__':
    unittest.main()
