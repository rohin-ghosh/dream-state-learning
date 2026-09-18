import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


specification = importlib.util.spec_from_file_location('r207_vision_service', Path(__file__).with_name('service.py'))
service = importlib.util.module_from_spec(specification)
sys.modules[specification.name] = service
specification.loader.exec_module(service)


class ServiceTests(unittest.TestCase):
    def test_unix_socket_path_bound_precedes_model_loading(self):
        self.assertLess(len(str(service.comparator_socket(service.HOME / 'runtime_combined')).encode()), 108)
        with self.assertRaisesRegex(service.vision.VisionError, 'bounded_unix_socket_path_before_model_load'):
            service.comparator_socket('/' + 'x' * 108)

    def test_exact_labeled_fields_preserve_numbers_and_uncertainty(self):
        raw = 'humor_probabilities: 0.2, 0.3, 0.5\nscene_fit_probability: 0.8\nuncertainty: Provisional opinion.'
        self.assertEqual(service.comparator_result(raw), dict(humor_probabilities=[0.2, 0.3, 0.5],
            scene_fit_probability=0.8, uncertainty='Provisional opinion.'))

    def test_labeled_fields_reject_missing_extra_nonfinite_or_unnormalized(self):
        raw = 'humor_probabilities: 0.2, 0.3, 0.5\nscene_fit_probability: 0.8\nuncertainty: Uncertain.'
        for modified in (raw.rsplit('\n', 1)[0], raw + '\naccepted: true', raw.replace('0.8', 'NaN'),
                         raw.replace('0.8', '1.1'), raw.replace('0.5', '0.2'), raw.replace('Uncertain.', '')):
            with self.subTest(modified=modified), self.assertRaises(service.vision.VisionError):
                service.comparator_result(modified)

    def test_actual_first_malformed_json_is_not_repaired(self):
        raw = ('```json\n{"humor_probabilities": [0.1, 0.3, 0.6], "scene_fit_probability": 0.8, '
            '"uncertainty": "The scene is humorous due to the unexpected and exaggerated depiction '
            'of financial concerns, but}\n```')
        with self.assertRaisesRegex(service.vision.VisionError, 'invalid_json_no_repair'):
            service.comparator_result(raw)

    def test_failed_schema_keeps_raw_generation_and_does_not_call_mock_real(self):
        with tempfile.TemporaryDirectory() as temporary:
            backend = Mock(kind='mock_provider_not_actual', loaded_provenance={})
            backend.count_tokens.return_value = 3
            backend.generate_prompt.return_value = service.vision.Generation('{"unfinished":', 100, 8, 'eos', 1, 2, 3)
            packet = Mock()
            packet.verified_image.return_value = SimpleNamespace(sha256='b' * 64), Mock()
            provider = service.Comparator(packet, backend, temporary)
            with self.assertRaises(service.vision.VisionError):
                provider.inspect(dict(case_key='a' * 64, image='released', caption='Candidate data.'))
            receipts = list((Path(temporary) / 'private_receipts').glob('*.json'))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(receipt['raw_output'], '{"unfinished":')
            self.assertEqual(receipt['generated_tokens'], 8)
            self.assertFalse(receipt['model_called'])
            self.assertEqual(receipt['generation_ms'], 2)

    def test_exact_blind_output_has_no_acceptance_threshold(self):
        output = dict(humor_probabilities=[0.2, 0.3, 0.5], scene_fit_probability=0.8, uncertainty='Provisional opinion.')
        self.assertEqual(service.comparator_result(json.dumps(output)), output)
        self.assertEqual(service.comparator_result('```json\n' + json.dumps(output) + '\n```'), output)
        self.assertNotIn('tau', output)

    def test_no_probability_repair_extra_fields_or_nonfinite_values(self):
        baseline = dict(humor_probabilities=[0.2, 0.3, 0.5], scene_fit_probability=0.8, uncertainty='Uncertain.')
        for change in (dict(humor_probabilities=[0.2, 0.2, 0.2]), dict(scene_fit_probability=True),
                       dict(scene_fit_probability=float('nan')), dict(uncertainty=''), dict(accepted=True)):
            with self.subTest(change=change), self.assertRaises(service.vision.VisionError):
                service.comparator_result(json.dumps(dict(baseline, **change)))

    def test_origin_labels_and_private_judge_fields_rejected_before_model(self):
        backend, packet = Mock(), Mock()
        provider = service.Comparator.__new__(service.Comparator)
        provider.backend, provider.packet = backend, packet
        base = dict(case_key='a' * 64, image='development_handle', caption='Candidate data.')
        for field in ('origin', 'lane', 'judge_score', 'panel', 'history', 'split'):
            with self.subTest(field=field), self.assertRaises(service.vision.VisionError):
                provider.inspect(dict(base, **{field: 'forbidden'}))
        backend.generate_prompt.assert_not_called()
        packet.verified_image.assert_not_called()

    def test_only_assigned_two_slots_and_conservative_finite_wall(self):
        self.assertEqual({value[0] for value in service.DEVICES.values()}, {0, 1} if service.NODE4 else {4, 5})
        self.assertEqual(service.HARD_END, 1789754400 if service.NODE4 else 1789725600)
        self.assertEqual(service.MINORS, {'vision': 3, 'comparator': 2, 'combined': 2} if service.NODE4 else {'vision': 5, 'comparator': 4})
        self.assertIn('blind', service.COMPARATOR_PROMPT)
        self.assertNotIn('tau', service.COMPARATOR_PROMPT)

    def test_combined_role_reuses_comparator_gpu_without_new_allocation(self):
        if service.NODE4:
            self.assertEqual(service.DEVICES['combined'], service.DEVICES['comparator'])
            self.assertEqual(service.MINORS['combined'], service.MINORS['comparator'])
        else:
            self.assertNotIn('combined', service.DEVICES)


if __name__ == '__main__':
    unittest.main()
