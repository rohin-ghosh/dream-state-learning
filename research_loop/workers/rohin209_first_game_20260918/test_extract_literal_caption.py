import unittest

from research_loop.workers.rohin209_first_game_20260918.extract_literal_caption import extract


class ExtractionTests(unittest.TestCase):
    def test_literal_content_and_offsets_unchanged(self):
        raw = '[{"contest_id":"released","text":"An unchanged caption")]'
        result, spans = extract(raw, {'released'})
        self.assertEqual(result['text'], 'An unchanged caption')
        start, end = spans['text_span']
        self.assertEqual(raw[start:end], '"An unchanged caption"')

    def test_does_not_salvage_ambiguous_truncated_or_extra_content(self):
        for raw in ('[{"contest_id":"released","text":"unfinished',
                    '[{"contest_id":"released","text":"hello"}] extra',
                    '[{"contest_id":"released","text":"hello","extra":"x")]'):
            with self.assertRaises(ValueError):
                extract(raw, {'released'})
        with self.assertRaises(ValueError):
            extract('[{"contest_id":"not-released","text":"hello")]', {'released'})


if __name__ == '__main__':
    unittest.main()
