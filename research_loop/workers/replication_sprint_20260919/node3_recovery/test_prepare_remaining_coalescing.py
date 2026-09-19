import json
from pathlib import Path
import unittest

import prepare_remaining_coalescing as subject


class RemainingBatchTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.assessment = json.loads((root / 'HARDLINK_ELIGIBLE_PATHS.json').read_bytes())
        self.canary = json.loads((root / 'HARDLINK_CANARY_PROPOSAL.json').read_bytes())
        self.completion = json.loads((root / 'CANARY_EXECUTION_VERIFIED.json').read_bytes())

    def invoke(self):
        return subject.partition_remaining(self.assessment, self.canary, self.completion)

    def test_exact_remaining_coverage_with_disjoint_bounded_paths(self):
        chunks = self.invoke()
        self.assertEqual(sum(len(chunk) for chunk in chunks), 1656)
        self.assertTrue(all(sum(len(subject.group_paths(group)) for group in chunk) <= 40 for chunk in chunks))
        self.assertEqual(sum(group['potential_allocated_bytes_freed'] for chunk in chunks for group in chunk),
            35262947328)

    def test_no_incomplete_canary_accepted(self):
        self.completion['status'] = 'INTERRUPTED'
        with self.assertRaisesRegex(ValueError, 'verified_canary_completion_required'):
            self.invoke()

    def test_missing_verified_path_stops_proposal(self):
        self.completion['result']['verified_paths'].pop()
        with self.assertRaisesRegex(ValueError, 'all_nine_canary_paths'):
            self.invoke()

    def test_wrong_canary_not_silently_subtracted(self):
        self.canary['max_paths'] = 10
        with self.assertRaisesRegex(ValueError, 'exact_authorized_canary'):
            self.invoke()


if __name__ == '__main__':
    unittest.main()
