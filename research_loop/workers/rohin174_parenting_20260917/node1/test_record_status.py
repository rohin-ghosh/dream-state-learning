from pathlib import Path
import unittest

from record_status import latest_observation


class LatestObservationTests(unittest.TestCase):
    def test_newer_poll_from_older_observer_wins(self):
        older_observer_new_poll = Path('/EXPOSURE_OBSERVER_100/inbox_300.json')
        newer_once_old_poll = Path('/EXPOSURE_OBSERVER_200/inbox_210.json')
        self.assertEqual(latest_observation([older_observer_new_poll, newer_once_old_poll]), older_observer_new_poll)

    def test_empty_is_unknown(self):
        self.assertIsNone(latest_observation([]))

    def test_numeric_not_lexical_timestamp(self):
        self.assertEqual(latest_observation([Path('/poll/id_9.json'), Path('/poll/id_10.json')]), Path('/poll/id_10.json'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
