from copy import deepcopy
import unittest

from summarize import summarize


class SummaryTests(unittest.TestCase):
    def cell(self, seed=1, scene='scene', stage='THINK'):
        return {'seed': seed, 'contest_id': scene, 'events': [{
            'stage': stage, 'generated_tokens': 10, 'truncated': False,
            'raw_child_output': 'A caption.', 'judgments': [{
                'caption_sha256': 'caption', 'cached': False, 'rank': 10,
                'accepted': True, 'status': 'new_pixel'}]}]}

    def test_replayed_result_is_not_new(self):
        cell = self.cell()
        cell['events'].append(deepcopy(cell['events'][0]))
        result = summarize([cell])
        self.assertEqual(result['generation_events'], 2)
        self.assertEqual(result['new_pixels_seed_local_sum'], 1)

    def test_novelty_resets_between_seeds(self):
        self.assertEqual(summarize([self.cell(1), self.cell(2)])['new_pixels_seed_local_sum'], 2)

    def test_caption_identity_includes_scene(self):
        self.assertEqual(summarize([self.cell(scene='first'), self.cell(scene='second')])['new_pixels_seed_local_sum'], 2)

    def test_first_origin_is_not_moved_to_act(self):
        cell = self.cell()
        later = deepcopy(cell['events'][0])
        later['stage'] = 'ACT'
        cell['events'].append(later)
        self.assertEqual(summarize([cell])['new_pixels_by_first_counted_stage'], {'THINK': 1})

    def test_cached_outcome_is_not_a_discovery(self):
        cell = self.cell()
        cell['events'][0]['judgments'][0]['cached'] = True
        self.assertEqual(summarize([cell])['new_pixels_seed_local_sum'], 0)

    def test_language_is_description_not_filter(self):
        cell = self.cell()
        cell['events'][0]['raw_child_output'] = 'A caption 中文.'
        result = summarize([cell])
        self.assertEqual(result['CJK_characters'], 2)
        self.assertEqual(result['new_pixels_seed_local_sum'], 1)


if __name__ == '__main__':
    unittest.main()
