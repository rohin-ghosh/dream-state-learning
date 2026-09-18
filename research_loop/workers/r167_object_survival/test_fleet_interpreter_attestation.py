import tempfile
import unittest
from pathlib import Path

from gpu import orch_r167_fleet_eval as evaluator


class InterpreterAttestationTests(unittest.TestCase):
    def test_virtualenv_target_bytes_remain_pinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            target = root / 'python-real'
            target.write_bytes(b'original interpreter')
            link = root / 'python'
            link.symlink_to(target)
            expected = evaluator.protocol.sha(target)
            self.assertEqual(evaluator.interpreter_sha(link), expected)
            with self.assertRaisesRegex(ValueError, 'symlink_forbidden'):
                evaluator.protocol.sha(link)
            target.write_bytes(b'changed interpreter')
            self.assertNotEqual(evaluator.interpreter_sha(link), expected)

    def test_broken_interpreter_link_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            link = root / 'python'
            link.symlink_to(root / 'missing')
            with self.assertRaises(FileNotFoundError):
                evaluator.interpreter_sha(link)


if __name__ == '__main__':
    unittest.main()
