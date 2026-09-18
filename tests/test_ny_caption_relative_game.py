import unittest

from gpu.ny_caption_game import Contest, DevelopmentManifest
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_relative_game import RelativeRankJudge, build_game


class Scalar:
    def score(self, rows):
        return [-1.0 if row['caption'] == 'Novel language joke' else -10.0 for row in rows]

    class tokenizer:
        @staticmethod
        def encode(text, add_special_tokens=False):
            return text.split()


class Encoder:
    model_id = 'synthetic'
    revision = 'v1'

    def __call__(self, text):
        return [1.0, 0.0]


class RelativeGameTests(unittest.TestCase):
    def test_real_core_roundtrip_no_tau_or_fake_probability(self):
        manifest = DevelopmentManifest(tuple(Contest(str(index), f'Scene {index}', f'image-{index}',
                                                    'agent_development') for index in range(3)))
        pixels = PixelConfig('synthetic', 'v1', 0.5, 0.6, 0.7)
        game = build_game(manifest, Scalar(), {f'Scene {index}': [-4, -3, -2] for index in range(3)},
                          pixels, Encoder(), top_k=1)
        accepted = game.submit_caption('0', 'Novel language joke')
        self.assertTrue(accepted['ok'])
        self.assertTrue(accepted['accepted'])
        self.assertIsNone(accepted['q'])
        self.assertEqual(accepted['rank'], 1)
        rejected = game.submit_caption('0', 'Not a joke')
        self.assertTrue(rejected['ok'])
        self.assertFalse(rejected['accepted'])
        self.assertIsNone(rejected['q'])
        self.assertEqual(game.submit_caption('0', 'Novel language joke')['pixel_count'], 1)

    def test_unknown_scene_is_not_scored(self):
        judge = RelativeRankJudge(Scalar(), {'registered': [-2, -3]}, 1)
        with self.assertRaises(ValueError):
            judge('another contest', 'Novel language joke')


if __name__ == '__main__':
    unittest.main()
