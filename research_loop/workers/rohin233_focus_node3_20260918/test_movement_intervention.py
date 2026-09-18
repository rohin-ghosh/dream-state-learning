import unittest
from pathlib import Path
from unittest.mock import patch

import movement_intervention as intervention


class MovementInterventionTests(unittest.TestCase):
    def test_distinct_plain_interventions(self):
        self.assertEqual(len(set(intervention.TEXTS.values())), 3)
        for text in intervention.TEXTS.values():
            self.assertTrue(text.isascii())
            self.assertLess(len(text), 2200)

    def test_unknown_alias_rejected(self):
        with self.assertRaises(ValueError):
            intervention.source(Path('/fixture'), 'p32')

    def test_exact_act_source_required(self):
        name = 'r213_math_a'
        index, digest, act_index = intervention.SOURCES[name]
        response = dict(kind='RESPONSE', sha256=digest, document=dict(response=dict(raw='synthetic')))
        act = dict(kind='R184_ACT', sha256='a' * 64, document=dict(origin=dict(kind='TRAIN_CHILD_RESPONSE',
            record_index=index, record_sha256=digest)))
        with patch('movement_intervention.record', side_effect=[response, act]):
            self.assertEqual(intervention.source(Path('/fixture'), name)['act']['index'], act_index)
        act['document']['origin']['record_index'] += 1
        with patch('movement_intervention.record', side_effect=[response, act]):
            with self.assertRaises(ValueError):
                intervention.source(Path('/fixture'), name)


if __name__ == '__main__':
    unittest.main()
