import hashlib
import io
import tarfile
import unittest

import stage_c2_epoch4 as staging


class Epoch4StageTests(unittest.TestCase):
    @staticmethod
    def archive(name, kind=tarfile.REGTYPE):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as bundle:
            entry = tarfile.TarInfo(name)
            entry.type = kind
            bundle.addfile(entry, io.BytesIO())
        return stream.getvalue()

    def test_only_new_epoch4_literal_paths(self):
        raw = self.archive('C2/epoch4/EPOCH4_SOURCE.json')
        self.assertEqual(len(staging.validated_members(raw, hashlib.sha256(raw).hexdigest())), 1)
        for name, kind in (('C2/epoch3/EPOCH3_SOURCE.json', tarfile.REGTYPE),
                ('../escape', tarfile.REGTYPE), ('C2/epoch4/link', tarfile.SYMTYPE)):
            raw = self.archive(name, kind)
            with self.assertRaisesRegex(ValueError, 'only_unique_regular_epoch4_paths'):
                staging.validated_members(raw, hashlib.sha256(raw).hexdigest())

    def test_wrong_archive_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_prepared_archive'):
            staging.validated_members(self.archive('C2/epoch4/EPOCH4_SOURCE.json'), '0' * 64)


if __name__ == '__main__':
    unittest.main()
