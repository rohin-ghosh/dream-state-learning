from copy import deepcopy
import json
from pathlib import Path
import unittest

import prepare_coalescing_canary as subject


class CanaryProposalTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.assessment = json.loads((root / 'HARDLINK_ELIGIBLE_PATHS.json').read_bytes())
        self.copy_receipt = json.loads((root / 'ARCHIVE_COPY_VERIFIED.json').read_bytes())
        self.restore_receipt = json.loads((root / 'ARCHIVE_FULL_RESTORE_VERIFIED.json').read_bytes())

    def invoke(self):
        return subject.select_canary(self.assessment, self.copy_receipt, self.restore_receipt)

    def test_exact_real_proposal_is_bounded_without_altering_assessment(self):
        before = deepcopy(self.assessment)
        selected = self.invoke()
        self.assertEqual(len(selected), 3)
        self.assertEqual(sum(group['potential_allocated_bytes_freed'] for group in selected), 17088512)
        self.assertEqual(self.assessment, before)
        self.assertTrue(all(group['mutation_authorized'] is False for group in selected))

    def test_stream_only_verification_does_not_qualify(self):
        self.restore_receipt['status'] = 'ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED'
        with self.assertRaisesRegex(ValueError, 'full_filesystem_restore_required'):
            self.invoke()

    def test_different_manifest_fails(self):
        self.assessment['manifest_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_reviewed_source_manifest'):
            self.invoke()

    def test_different_archive_fails(self):
        self.copy_receipt['archive_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'exact_verified_archive_copy'):
            self.invoke()

    def test_incomplete_member_count_fails(self):
        self.restore_receipt['members'] -= 1
        with self.assertRaisesRegex(ValueError, 'full_filesystem_restore_required'):
            self.invoke()

    def test_changed_destination_fails(self):
        self.restore_receipt['root'] = '/unreviewed'
        with self.assertRaisesRegex(ValueError, 'full_filesystem_restore_required'):
            self.invoke()


if __name__ == '__main__':
    unittest.main()
