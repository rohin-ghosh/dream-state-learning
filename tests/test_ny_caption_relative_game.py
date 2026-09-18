import unittest

from gpu.ny_caption_game import Contest, DevelopmentManifest
from gpu.ny_caption_game import RelativeJudgeResult
from gpu.ny_caption_pixels import PixelConfig
from gpu.ny_caption_relative_game import RelativeRankJudge, build_game, reference_bindings


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

    def test_relevance_can_reject_high_rank_without_falsifying_it(self):
        result = RelativeJudgeResult(-1, 1, 64, 8, relevance_score=-0.3, relevance_threshold=0)
        self.assertFalse(result.accepted)
        self.assertEqual(result.rank, 1)
        self.assertEqual(result.raw_score, -1)
        with self.assertRaises(ValueError):
            RelativeJudgeResult(-1, 1, 64, 8, relevance_score=0.3)

    def test_only_released_development_handles_resolve(self):
        manifest = DevelopmentManifest(tuple(Contest(f'image-{index}', f'Scene {index}', f'image-{index}',
                                                    'agent_development') for index in range(3)))
        source = dict(pools=dict(agent_development=['0', '1', '2', 'unreleased']))
        mapping = dict(schema='R177_GAME_IMAGE_RELEASE_MAP_V1', mode='DEVELOPMENT',
                       contests=[dict(image=f'image-{index}', contest_id=str(index), split='agent_development')
                                 for index in range(3)])
        self.assertEqual(reference_bindings(source, manifest, mapping)['image-0'], '0')
        mapping['contests'][0]['contest_id'] = 'locked'
        with self.assertRaises(ValueError):
            reference_bindings(source, manifest, mapping)

    def test_relevance_rejection_survives_game_snapshot(self):
        class SceneEncoder(Encoder):
            def __call__(self, text):
                return [0.0, 1.0] if text == 'Novel language joke' else [1.0, 0.0]
        manifest = DevelopmentManifest(tuple(Contest(str(index), f'Scene {index}', f'image-{index}',
                                                    'agent_development') for index in range(3)))
        arguments = (manifest, Scalar(), {f'Scene {index}': [-4, -3, -2] for index in range(3)},
                     PixelConfig('synthetic', 'v1', 0.5, 0.6, 0.7), SceneEncoder())
        game = build_game(*arguments, top_k=1, relevance_threshold=0.5)
        result = game.submit_caption('0', 'Novel language joke')
        self.assertTrue(result['ok'])
        self.assertEqual(result['rank'], 1)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['rejection_reason'], 'relevance_gate')
        restored = build_game(*arguments, top_k=1, relevance_threshold=0.5)
        restored.restore(game.snapshot())
        self.assertEqual(restored.snapshot(), game.snapshot())


if __name__ == '__main__':
    unittest.main()
