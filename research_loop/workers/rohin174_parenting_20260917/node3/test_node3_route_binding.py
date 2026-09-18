import unittest

from node3_route_binding import canonical_route


class RouteTests(unittest.TestCase):
    def test_preserve_working_v1_path(self):
        self.assertEqual(canonical_route('https://[REDACTED_HOST]/v1/responses'),
                         'https://[REDACTED_HOST]/v1/responses')

    def test_correct_only_missing_v1(self):
        self.assertEqual(canonical_route('https://[REDACTED_HOST]/responses'),
                         'https://[REDACTED_HOST]/v1/responses')

    def test_reject_unknown_host_path_and_query(self):
        for url in ('https://[REDACTED_HOST]/responses', 'https://[REDACTED_HOST]/v2/responses',
                    'https://[REDACTED_HOST]/v1/responses?token=not-a-real-token'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_route(url)


if __name__ == '__main__':
    unittest.main()
