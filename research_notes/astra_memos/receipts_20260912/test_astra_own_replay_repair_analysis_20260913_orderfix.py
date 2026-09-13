"""Frozen fixture suite plus candidate-order compatibility; no outcomes read."""
import ast
import unittest
from pathlib import Path

import astra_own_replay_repair_analysis_20260913_orderfix as fixed
import test_astra_own_replay_repair_analysis_20260913 as fixtures


class OrderingRegression(unittest.TestCase):
    def test_only_one_line_changed(self):
        original = Path('/tmp/astra_own_replay_repair_analysis_20260913.py').read_text()
        self.assertEqual(fixed.digest('/tmp/astra_own_replay_repair_analysis_20260913.py'),
                         'ba039742485f8292e7caf9d728f0b5c9b1c3a0ca03a52ff39b8d4b14814a84cb')
        self.assertEqual(Path(fixed.__file__).read_text(), original.replace(
            '        for checksum, raw in candidates.items():',
            '        for checksum, raw in sorted(candidates.items()):'))

    def test_unsorted_candidates_match_frozen_native_function(self):
        rows = [dict(row_id=str(index), target_sha256=checksum*64, raw_target='same',
                     input_messages=[], paraphrase_input_messages=[])
                for index, checksum in enumerate(('f', '1', '9'))]
        calls = [dict(panel=panel, row_id=row['row_id'], messages=[])
                 for panel in ('exact', 'paraphrase') for row in rows]
        def score(*args, **kwargs):
            return dict(score=dict(content_correct=True, production_eligible=True))
        class Memory:
            score_readback = staticmethod(score)
        namespace = fixed.extract('/tmp/'+fixed.PINS['runner'][0], fixed.PINS['runner'][1],
                                  {'constant_diagnostic'}, {})
        bound = dict(dataset=dict(rows=rows), memory=Memory, capture={}, kwargs={})
        expected = namespace['constant_diagnostic'](bound, {})
        actual = fixed.constants(dict(rows=rows), calls, score, {}, None)
        self.assertEqual(expected, actual)
        self.assertEqual(actual['variants']['exact']['tied_best_target_sha256'],
                         ['1'*64, '9'*64, 'f'*64])


def load_tests(loader, tests, pattern):
    fixtures.analysis = fixed
    tests.addTests(loader.loadTestsFromTestCase(fixtures.ReducerTests))
    return tests


if __name__ == '__main__':
    unittest.main()
