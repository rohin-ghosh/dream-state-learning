from copy import deepcopy
import unittest
import xml.etree.ElementTree as xml

import plot_age_probe as subject


def fixture():
    curve = [dict(cumulative_generated_tokens=512, actual_response_tokens=512,
                  cumulative_new_pixels=1, marginal_new_pixels=1),
             dict(cumulative_generated_tokens=1024, actual_response_tokens=512,
                  cumulative_new_pixels=2, marginal_new_pixels=1)]
    return dict(scenes=1, per_scene_seed_budget=1024, seeds=[23201, 23202],
        conditions=[dict(condition=name, generated_tokens=2048, probe_optimizer_updates=0,
                         new_pixel_events=4, seed_curves={str(seed): deepcopy(curve) for seed in (23201, 23202)})
                    for name in subject.STYLES])


class PlotTests(unittest.TestCase):
    def test_svg_uses_step_credit_and_separate_seed_panels(self):
        content = subject.render(fixture(), 'a' * 64)
        xml.fromstring(content)
        self.assertIn('Paired seed 23201', content)
        self.assertIn('Paired seed 23202', content)
        self.assertIn(' H ', content)
        self.assertIn(' V ', content)
        self.assertIn('not global unique-idea counts', content)

    def test_unmatched_budget_or_updates_fail(self):
        for field, value in (('generated_tokens', 2000), ('probe_optimizer_updates', 1)):
            document = fixture()
            document['conditions'][0][field] = value
            with self.assertRaises(ValueError):
                subject.checked_curves(document)

    def test_early_score_credit_or_inconsistent_sum_fails(self):
        document = fixture()
        document['conditions'][0]['seed_curves']['23201'][0]['cumulative_generated_tokens'] = 511
        with self.assertRaises(ValueError):
            subject.checked_curves(document)
        document = fixture()
        document['conditions'][0]['new_pixel_events'] = 5
        with self.assertRaises(ValueError):
            subject.checked_curves(document)


if __name__ == '__main__':
    unittest.main()
