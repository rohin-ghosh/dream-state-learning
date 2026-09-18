from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receiving_collision_repair import response_named_tick


def attempt_fixture(state):
    return 'parent_%012d' % state['request_count']


def formatted_attempt_fixture(state):
    return f"parent_{state['request_count']:012d}"


class ResponseClockAttemptTests(unittest.TestCase):
    def test_completed_response_does_not_collide_with_earlier_pending_request(self):
        naming = response_named_tick(attempt_fixture)
        first = naming(dict(request_count=147, response_count=146))
        second = naming(dict(request_count=147, response_count=147))
        self.assertNotEqual(first, second)
        self.assertEqual(first, 'parent_000000000147_response_000000000146')

    def test_identical_source_keeps_identical_name_not_attempt_number(self):
        naming = response_named_tick(attempt_fixture)
        state = dict(request_count=147, response_count=147)
        self.assertEqual(naming(state), naming(state))

    def test_actual_formatted_attempt_name_preserves_response_clock(self):
        naming = response_named_tick(formatted_attempt_fixture)
        self.assertEqual(naming(dict(request_count=147, response_count=146)),
            'parent_000000000147_response_000000000146')
        self.assertNotEqual(naming(dict(request_count=147, response_count=146)),
            naming(dict(request_count=147, response_count=147)))


if __name__ == '__main__':
    unittest.main()
