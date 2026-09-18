import unittest

from observe import count_events


class CounterTests(unittest.TestCase):
    def event(self, cached=False):
        return dict(actual_generated_tokens=128, origin=dict(stage='ACT'), score=dict(results=[
            dict(caption_sha256='same', result=dict(rank=12, accepted=True, status='new_pixel', cached=cached))]))

    def test_cached_duplicates_do_not_create_discovery_and_seeds_stay_separate(self):
        counts = count_events([('scene', 23201, [self.event(), self.event(cached=True)]),
            ('scene', 23202, [self.event()])])
        self.assertEqual(counts['23201']['generated_tokens'], 256)
        self.assertEqual(counts['23201']['distinct_accepted'], 1)
        self.assertEqual(counts['23201']['new_pixels'], 1)
        self.assertEqual(counts['23202']['new_pixels'], 1)

    def test_every_generated_token_counts_even_with_no_scored_string(self):
        event = self.event()
        event['score']['results'] = []
        counts = count_events([('scene', 23201, [event])])['23201']
        self.assertEqual(counts['generated_tokens'], 128)
        self.assertEqual(counts['acts_without_scored_strings'], 1)
        self.assertEqual(counts['distinct_scored'], 0)


if __name__ == '__main__':
    unittest.main()
