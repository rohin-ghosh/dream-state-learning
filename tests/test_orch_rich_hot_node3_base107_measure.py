"""Window arithmetic and no semantic promotion from mechanical throughput."""

import unittest

from gpu.orch_rich_hot_node3_base107_measure import window_counts


def row(start, end, raw='Reasoning.\nROUTE port', tokens=10):
    return dict(started_unix=start, finished_unix=end,
                response=dict(raw=raw), generated_tokens=tokens)


class WindowTests(unittest.TestCase):
    def test_exact_window_required(self):
        with self.assertRaises(ValueError):
            window_counts([], 0, 599)

    def test_start_exclusive_end_inclusive(self):
        result = window_counts([row(0, 100), row(100, 700), row(700, 701)], 100, 700)
        self.assertEqual(result['completed_raw_rows'], 1)
        self.assertEqual(result['raw_rows_per_hour'], 6)

    def test_command_rows_separate_from_prose(self):
        result = window_counts([row(110, 120, 'READ EVENT address'), row(120, 130)], 100, 700)
        self.assertEqual(result['raw_command_only_rows'], 1)
        self.assertEqual(result['prose_rows'], 1)
        self.assertIsNone(result['semantic_qualified_rows'])
        self.assertIsNone(result['qualified_rows_per_hour'])

    def test_crossing_and_tokens_are_completion_attributed(self):
        result = window_counts([row(90, 110, tokens=600)], 100, 700)
        self.assertEqual(result['crossed_start_boundary_rows'], 1)
        self.assertEqual(result['completion_attributed_tokens_per_second'], 1)

    def test_exact_duplicates_are_not_semantic_review(self):
        result = window_counts([row(110, 120), row(130, 140)], 100, 700)
        self.assertEqual(result['exact_duplicate_raw_rows'], 1)
        self.assertIsNone(result['semantic_qualified_rows'])


if __name__ == '__main__':
    unittest.main()
