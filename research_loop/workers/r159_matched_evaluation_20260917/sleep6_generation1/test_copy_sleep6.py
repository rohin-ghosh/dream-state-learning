import io
from pathlib import Path
import tarfile
import unittest
from copy_sleep6 import archive_size, safe_member


class CopyTests(unittest.TestCase):
    def test_tar_size_matches(self):
        for sizes in ([0], [512, 513, 20], [10001, 1]):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as archive:
                for index,size in enumerate(sizes):
                    member = tarfile.TarInfo(str(index))
                    member.size = size
                    archive.addfile(member, io.BytesIO(b'x'*size))
            self.assertEqual(len(stream.getvalue()), archive_size(sizes))

    def test_no_escape(self):
        self.assertTrue(safe_member('parented_learning/checkpoints/sleep_000001/adapter/adapter_model.safetensors'))
        for value in ('/etc/passwd','../checkpoints/sleep_000001/COMMIT.json','a/b'):
            self.assertFalse(safe_member(value))


if __name__ == '__main__':
    unittest.main()
