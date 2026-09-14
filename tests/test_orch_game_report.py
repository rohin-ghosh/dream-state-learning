from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import orch_game_report as report
from organism_v6 import orch_game_screen as screen


class ReductionTests(unittest.TestCase):
    def test_sign_threshold_is_not_just_positive_gap(self):
        for rich_only, expected in [(4, False), (5, True)]:
            episodes = []
            for index in range(16):
                for arm in ('RICH', 'TERSE'):
                    success = index < 8 if arm == 'RICH' else rich_only <= index < 8
                    episodes.append(dict(instance=dict(id=str(index)), arm=arm, success=success, turns=[]))
            result = screen.summarize(episodes, list(map(str, range(16))))
            self.assertEqual(result['outcome_pool_pass'], expected)

    def test_reducer_does_not_summarize_incomplete_run(self):
        bank = Path('research_notes/analysis/orch_game_20260914_attempt1/FROZEN_BANK.json')
        with TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                report.reduce(Path(root), bank)


if __name__ == '__main__':
    unittest.main()
