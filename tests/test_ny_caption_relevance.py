import unittest

from gpu.ny_caption_relevance import RelevanceGate, cosine, scene_text


class RelevanceTests(unittest.TestCase):
    def test_separate_scene_and_caption_vectors(self):
        vectors = {'room': [1, 0], 'room joke': [1, 0], 'ocean joke': [0, 1]}
        gate = RelevanceGate(vectors.__getitem__, 0.25)
        self.assertEqual(gate.score('{"canny":"room"}', 'room joke'), 1)
        self.assertEqual(gate.score('room', 'ocean joke'), 0)
        self.assertEqual(len(gate.scenes), 1)

    def test_invalid_vectors_and_unset_threshold_do_not_pass(self):
        for threshold in (None, float('nan'), 2, True):
            with self.assertRaises(ValueError):
                RelevanceGate(lambda text: [1], threshold)
        with self.assertRaises(ValueError):
            cosine([0], [0])
        with self.assertRaises(ValueError):
            cosine([1], [1, 0])

    def test_plain_scene_preserved(self):
        self.assertEqual(scene_text('A person in a room.'), 'A person in a room.')


if __name__ == '__main__':
    unittest.main()
