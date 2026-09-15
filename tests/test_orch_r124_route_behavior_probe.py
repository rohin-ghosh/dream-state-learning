import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from gpu import orch_r124_route_behavior_probe as probe


class PublicProbeTests(unittest.TestCase):
    def cohort(self):
        return dict(held=[dict(id=f'DEV{index}', task=dict(node='HERE', goal='THERE',
            ports=['PORT'], events=['EVENT']), world={'secret': 'HIDDEN_WORLD_KEY'}) for index in range(8)],
            train=[dict(id='TRAIN_ONLY', private='TRAIN_PRIVATE')], store={'EVENT': 'PUBLIC_RECORD'})

    def test_public_prompts_only_use_public_observation_and_actual_record(self):
        prompts = probe.public_prompts(self.cohort(), lambda *args: 'PUBLIC_OBSERVATION')
        self.assertEqual(len(prompts), 32)
        encoded = json.dumps(prompts)
        self.assertNotIn('HIDDEN_WORLD_KEY', encoded)
        self.assertNotIn('TRAIN_PRIVATE', encoded)
        self.assertNotIn('TRAIN_ONLY', encoded)
        self.assertEqual(sum(row['context'] == 'PUBLIC_RECORD' for row in prompts), 16)
        self.assertTrue(all(row['messages_sha256'] == probe.digest(row['messages']) for row in prompts))
        self.assertTrue(all([message['role'] for message in row['messages']] == ['system', 'user']
                            for row in prompts))
        self.assertTrue(all(row['trainingAllowed'] is False for row in prompts))

    def test_missing_public_record_rejected_not_invented(self):
        cohort = self.cohort()
        cohort['store'] = {}
        with self.assertRaisesRegex(ValueError, 'actual_public_record'):
            probe.public_prompts(cohort, lambda *args: 'PUBLIC')

    def test_train_overlap_rejected(self):
        cohort = self.cohort()
        cohort['train'].append(dict(id='DEV0'))
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            probe.public_prompts(cohort, lambda *args: 'PUBLIC')

    def checkpoint(self, root, cycle, sleeps=None, complete=True):
        path = root / f'cycle_{cycle:04d}' / 'checkpoint' / 'CHECKPOINT.json'
        probe.write(path, dict(cycle=cycle, sleeps=cycle if sleeps is None else sleeps,
            complete=complete, saved_unix=cycle * 100,
            adapter=dict(base_sha256=probe.BASE_SHA)))
        probe.write(path.parent.parent / 'SLEEP.json', dict(checkpoint_sha256=probe.sha(path)))
        return path

    def test_latest_consecutive_durable_pair_not_selected_by_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.checkpoint(root, 10)
            before = self.checkpoint(root, 11)
            after = self.checkpoint(root, 12)
            self.checkpoint(root, 13, complete=False)
            result = probe.select_checkpoints(root)
            self.assertEqual(result, dict(BEFORE=before, AFTER=after))

    def test_nonconsecutive_pair_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.checkpoint(root, 10)
            self.checkpoint(root, 12)
            with self.assertRaisesRegex(ValueError, 'consecutive'):
                probe.select_checkpoints(root)

    def test_multi_sleep_difference_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.checkpoint(root, 10)
            self.checkpoint(root, 11, sleeps=12)
            with self.assertRaisesRegex(ValueError, 'one_sleep'):
                probe.select_checkpoints(root)

    def test_raw_rationale_and_action_retained(self):
        tokenizer = Mock()
        tokenizer.encode.side_effect = lambda text, **kwargs: text.split()
        response = dict(raw='The record is still unread.\nREAD EVENT E1', token_ids=list(range(12)),
                        terminal=True, truncated=False)
        original = json.dumps(response)
        result = probe.metrics(response, tokenizer)
        self.assertEqual(result['rationale_tokens'], 5)
        self.assertEqual(result['action'], 'READ EVENT E1')
        self.assertEqual(result['generated_tokens'], 12)
        self.assertEqual(json.dumps(response), original)
        self.assertEqual(result['retained_improvement'], 'UNPROVEN')

    def test_protocol_only_is_zero_rationale_not_missing_capture(self):
        tokenizer = Mock()
        tokenizer.encode.side_effect = lambda text, **kwargs: text.split()
        result = probe.metrics(dict(raw='ROUTE P1', token_ids=[1, 2, 3], terminal=True,
                                    truncated=False), tokenizer)
        self.assertEqual(result['rationale_tokens'], 0)
        self.assertTrue(result['valid_final_action'])

    def test_no_overwrite_of_failed_or_complete_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'CALL.json'
            probe.write(path, dict(status='FAILED'))
            with self.assertRaises(FileExistsError):
                probe.write(path, dict(status='COMPLETE'))
            self.assertEqual(probe.read(path)['status'], 'FAILED')

    def test_configuration_is_diagnostic_not_causal_control(self):
        self.assertEqual(probe.CONDITIONS, ('BEFORE', 'AFTER', 'AFTER_LORA_OFF'))
        self.assertNotIn('UNPARENTED', probe.CONDITIONS)
        self.assertEqual(probe.CAP, 512)
        self.assertEqual(probe.BATCH, 4)
        self.assertIn('Briefly explain', probe.EXPLANATION)
        self.assertNotIn('explain', probe.MINIMAL)


if __name__ == '__main__':
    unittest.main()
