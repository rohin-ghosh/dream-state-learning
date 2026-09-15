from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_r119_l1_resume as runtime


class ContinuationNamespaceTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(prior_version='/native/prior', prior_plan_sha256='PLAN.json',
                           source_sha256=Path(runtime.__file__).name,
                           experience_source_sha256=Path(runtime.experience.__file__).name,
                           lease_end_unix=100000, hard_deadline_unix=78400,
                           slots={'FULL': 0, 'CONTROL': 1}, uuid_by_index=['full', 'control'],
                           model_dir='/native/frozen_base')
        self.plan = dict(train_slots={'FULL': 5, 'CONTROL': 6}, eligible_sha256='ELIGIBLE.json',
                         lifetime=dict(started_unix=100), cohort_id='IMMUTABLE_C2_B002')
        self.prepared = dict(encoded_sha256='ENCODED.json')

    def namespace(self):
        documents = {'CONTINUATION.json': self.config, 'PLAN.json': self.plan,
                     'PREPARED.json': self.prepared}
        with patch.object(runtime.trainer, 'read', side_effect=lambda path: documents[Path(path).name]), \
                patch.object(runtime.trainer, 'sha', side_effect=lambda path: Path(path).name), \
                patch.object(runtime.time, 'time', return_value=1000):
            return runtime.namespace(Path('/native/new'))

    def test_original_train_and_readout_bytecode_shared_context(self):
        config, plan, context = self.namespace()
        self.assertIs(context['train'].__code__, runtime.experience.train.__code__)
        self.assertIs(context['readout'].__code__, runtime.experience.readout.__code__)
        self.assertIs(context['train'].__globals__, context['readout'].__globals__)
        self.assertEqual(context['ROOT'], Path('/native/new'))
        self.assertEqual(context['SLOTS'], {'FULL': 0, 'CONTROL': 1})
        self.assertEqual(plan['cohort_id'], self.plan['cohort_id'])
        self.assertEqual(plan['lifetime']['started_unix'], 100)
        self.assertEqual(self.plan['train_slots'], {'FULL': 5, 'CONTROL': 6})

    def test_wrong_original_topology_rejected(self):
        self.plan['train_slots'] = {'FULL': [0, 1, 2], 'CONTROL': [3, 4]}
        with self.assertRaises(AssertionError):
            self.namespace()

    def test_wrong_destination_slot_rejected(self):
        self.config['slots']['CONTROL'] = 2
        with self.assertRaises(AssertionError):
            self.namespace()

    def test_lease_margin_not_extended(self):
        self.config['hard_deadline_unix'] += 1
        with self.assertRaises(AssertionError):
            self.namespace()

    def test_changed_encoded_cohort_rejected(self):
        self.prepared['encoded_sha256'] = 'different_encoded_hash'
        with self.assertRaises(AssertionError):
            self.namespace()


if __name__ == '__main__':
    unittest.main()
