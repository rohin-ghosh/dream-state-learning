from copy import deepcopy
import unittest
import xml.etree.ElementTree as xml

import plot_movement


def fixture():
    curve = [dict(cumulative_generated_tokens=512, actual_response_tokens=512,
        cumulative_new_pixels=1, marginal_new_pixels=1),
        dict(cumulative_generated_tokens=1024, actual_response_tokens=512,
        cumulative_new_pixels=2, marginal_new_pixels=1)]
    return dict(scenes=1, per_scene_seed_budget=1024, seeds=[23201,23202],
        conditions=[dict(condition=name, generated_tokens=2048, probe_optimizer_updates=0,
            new_pixel_events=4, seed_curves={str(seed):deepcopy(curve) for seed in (23201,23202)})
            for name in plot_movement.STYLES])


class MovementPlotTests(unittest.TestCase):
    def test_extension_requires_matching_judge_battery_and_no_parent(self):
        data = fixture()
        primary = deepcopy(data)
        primary['conditions'] = primary['conditions'][:3]
        primary['judge'] = dict(panel_sha256='a'*64, rule_sha256='b'*64)
        primary['freshness'] = dict(scenes_sha256='c'*64, selected_contests=['development'], eligible=True)
        c0 = deepcopy(primary)
        c0['conditions'] = [deepcopy(data['conditions'][3])]
        fresh_condition = data['conditions'][4]
        fresh = dict(judge=deepcopy(primary['judge']), freshness=deepcopy(primary['freshness']),
            status='COMPLETE', optimizer_updates=0, parent_tokens=0, source_context_used=False,
            whole_generation_tokens_charged_before_credit=True, actual_tokens_by_stage={'ACT':2048},
            generated_tokens=2048, new_pixel_events=4, accepted_new_scores=4,
            seed_curves={seed:[dict(cumulative_generated_tokens=row['cumulative_generated_tokens'],
                cumulative_new_pixel_events=row['cumulative_new_pixels'], response_receipt_sha256='d'*64)
                for row in curve] for seed,curve in fresh_condition['seed_curves'].items()})
        combined = plot_movement.combine(primary,c0,fresh)
        self.assertEqual(len(combined['conditions']),5)
        for field,value in (('parent_tokens',1),('source_context_used',True),('status','RUNNING')):
            bad = deepcopy(fresh)
            bad[field] = value
            with self.assertRaises(ValueError):
                plot_movement.combine(primary,c0,bad)
        bad = deepcopy(fresh)
        bad['judge']['panel_sha256'] = 'e'*64
        with self.assertRaises(ValueError):
            plot_movement.combine(primary,c0,bad)

    def test_five_conditions_and_distinct_seed_panels(self):
        content = plot_movement.render(fixture())
        xml.fromstring(content)
        for label, color, dash in plot_movement.STYLES.values():
            self.assertIn(label, content)
        self.assertIn('Paired seed 23201', content)
        self.assertIn('Paired seed 23202', content)
        self.assertIn('separate branches', content)
        self.assertIn(' H ', content)
        self.assertIn(' V ', content)

    def test_budget_or_optimizer_mismatch_rejected(self):
        for key,value in (('generated_tokens',2000),('probe_optimizer_updates',1)):
            data = fixture()
            data['conditions'][0][key] = value
            with self.assertRaises(ValueError):
                plot_movement.checked_curves(data)

    def test_early_credit_and_wrong_total_rejected(self):
        for key,value in (('cumulative_generated_tokens',511),('marginal_new_pixels',5)):
            data = fixture()
            data['conditions'][0]['seed_curves']['23201'][0][key] = value
            with self.assertRaises(ValueError):
                plot_movement.checked_curves(data)

    def test_missing_or_duplicate_condition_rejected(self):
        data = fixture()
        data['conditions'].pop()
        with self.assertRaises(ValueError):
            plot_movement.checked_curves(data)
        data = fixture()
        data['conditions'].append(deepcopy(data['conditions'][0]))
        with self.assertRaises(ValueError):
            plot_movement.checked_curves(data)


if __name__ == '__main__':
    unittest.main()
