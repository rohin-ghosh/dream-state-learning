import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock


specification = importlib.util.spec_from_file_location('r207_vision_service', Path(__file__).with_name('service.py'))
service = importlib.util.module_from_spec(specification)
sys.modules[specification.name] = service
specification.loader.exec_module(service)


class ServiceTests(unittest.TestCase):
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
