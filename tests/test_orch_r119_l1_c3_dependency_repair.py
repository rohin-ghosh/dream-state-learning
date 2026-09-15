import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from gpu.orch_r119_l1_c3_dependency_repair import restore


class DependencyTests(unittest.TestCase):
    def test_exact_bytes_only_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';target=root/'nested/target'
            held=dict(split='HELD',events=[]);source.write_text(json.dumps(dict(held=held)))
            file_sha=hashlib.sha256(source.read_bytes()).hexdigest()
            held_sha=hashlib.sha256(json.dumps(held,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            for hashes in [('wrong',held_sha),(file_sha,'wrong')]:
                with self.assertRaises(AssertionError):restore(source,target,*hashes)
                self.assertFalse(target.exists())
            restore(source,target,file_sha,held_sha)
            self.assertEqual(source.read_bytes(),target.read_bytes())
            with self.assertRaises(AssertionError):restore(source,target,file_sha,held_sha)


if __name__=='__main__':unittest.main()
