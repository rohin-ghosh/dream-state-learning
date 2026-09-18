import copy
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location('p3_movement_verify_feedback', Path(__file__).with_name('verify_feedback.py'))
feedback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(feedback)


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.response = dict(kind='RESPONSE', index=42, sha256='own-response',
            document=dict(response=dict(raw='own unchanged output')))
        self.result = dict(origin=dict(kind='TRAIN_CHILD_RESPONSE', record_index=42,
            record_sha256='own-response'), raw_act='own unchanged output', unix=1,
            report=dict(ok=False, error='scene_not_unambiguously_identified',
                format_metrics=dict(recovered_count=0), feedback=[]))

    def test_no_judgment_not_reported_as_rejection(self):
        original = copy.deepcopy(self.result)
        projected = feedback.projected_result(self.result, self.response)
        self.assertEqual([], projected['feedback'])
        self.assertEqual('scene_not_unambiguously_identified', projected['error'])
        self.assertNotIn('raw_act', projected)
        self.assertEqual(original, self.result)

    def test_wrong_origin_rejected(self):
        for key, value in (('record_index', 43), ('record_sha256', 'other')):
            with self.subTest(key=key):
                result = copy.deepcopy(self.result)
                result['origin'][key] = value
                with self.assertRaisesRegex(ValueError, 'exact_result_origin'):
                    feedback.projected_result(result, self.response)

    def test_other_source_kind_rejected(self):
        self.result['origin']['kind'] = 'REFERENCE_PANEL'
        with self.assertRaisesRegex(ValueError, 'own_TRAIN_RESPONSE'):
            feedback.projected_result(self.result, self.response)

    def test_raw_mutation_rejected(self):
        self.result['raw_act'] += ' normalized'
        with self.assertRaisesRegex(ValueError, 'unaltered_raw_ACT'):
            feedback.projected_result(self.result, self.response)


if __name__ == '__main__':
    unittest.main()
