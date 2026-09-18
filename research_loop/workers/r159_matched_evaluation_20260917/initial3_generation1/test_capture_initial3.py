import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import time
import unittest


spec = importlib.util.spec_from_file_location('capture', Path(__file__).with_name('capture_initial3.py'))
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.checkpoint = self.root / 'arm/checkpoints/initial'
        (self.checkpoint / 'adapter').mkdir(parents=True)
        (self.checkpoint / 'COMMIT.json').write_bytes(b'commit')
        (self.checkpoint / 'adapter/data').write_bytes(b'adapter')
        (self.checkpoint / 'optimizer_rng.pt').write_bytes(b'NEVER_COPY')
        self.commits = dict(arm=hashlib.sha256(b'commit').hexdigest())
        self.adapters = dict(data=hashlib.sha256(b'adapter').hexdigest())

    def run_capture(self, **options):
        output = io.BytesIO()
        result = capture.capture(self.root, self.commits, self.adapters, output,
            end=time.time()+60, **options)
        return result, output.getvalue()

    def test_exact_allowlist(self):
        result, raw = self.run_capture()
        self.assertEqual(result, dict(bytes=13, files=2))
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            self.assertEqual(set(archive.getnames()), {'arm/checkpoints/initial/COMMIT.json',
                'arm/checkpoints/initial/adapter/data'})
        self.assertNotIn(b'NEVER_COPY', raw)

    def test_limit(self):
        with self.assertRaises(ValueError):
            self.run_capture(limit=12)

    def test_changed_hash(self):
        (self.checkpoint / 'adapter/data').write_bytes(b'wrong')
        with self.assertRaises(ValueError):
            self.run_capture()

    def test_link(self):
        (self.checkpoint / 'adapter/data').unlink()
        (self.checkpoint / 'adapter/data').symlink_to(self.checkpoint / 'optimizer_rng.pt')
        with self.assertRaises(ValueError):
            self.run_capture()

    def test_expired(self):
        with self.assertRaises(ValueError):
            capture.capture(self.root, self.commits, self.adapters, io.BytesIO(), end=0)


if __name__ == '__main__':
    unittest.main()
