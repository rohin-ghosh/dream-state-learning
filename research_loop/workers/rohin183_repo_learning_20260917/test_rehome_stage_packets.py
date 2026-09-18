import unittest

from research_loop.workers.rohin183_repo_learning_20260917 import rehome_stage_packets as stage


class StagingTests(unittest.TestCase):
    def document(self):
        return dict(physical=1, status='PERSISTENT_LOCAL_PACKET_VERIFIED',
            archive_paths_verified=True, gzip_crc_verified=True, archive_sha256='a' * 64,
            archive=str(stage.PACKETS / 'physical1.tar.gz'))

    def test_assigned_verified_archive(self):
        stage.validate(1, self.document())

    def test_other_owner_rejected(self):
        with self.assertRaisesRegex(ValueError, 'only_assigned'):
            stage.validate(0, self.document())

    def test_changed_path_rejected(self):
        document = self.document()
        document['archive'] = '/tmp/other.tar.gz'
        with self.assertRaisesRegex(ValueError, 'exact_archive_path'):
            stage.validate(1, document)

    def test_unverified_rejected(self):
        for key, value in (('status', 'PARTIAL'), ('archive_paths_verified', False),
                           ('gzip_crc_verified', False), ('archive_sha256', 'x')):
            with self.subTest(key=key):
                document = self.document()
                document[key] = value
                with self.assertRaises(ValueError):
                    stage.validate(1, document)


if __name__ == '__main__':
    unittest.main()
