"""CPU-only retirement regression; no remote processes or journals."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import replace_waiter


class ReplaceWaiterTests(unittest.TestCase):
    def test_every_handoff_effect_prevents_replacement(self):
        for name in replace_waiter.EFFECTS:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / name).touch()
                with self.assertRaisesRegex(ValueError, 'already_advanced'):
                    replace_waiter.before_handoff(root)

    def test_empty_wait_has_no_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            replace_waiter.before_handoff(Path(directory))

    @unittest.skipUnless(hasattr(os, 'pidfd_open'), 'Linux pidfd required')
    def test_exact_stopped_cpu_process_exits_without_signalling_neighbor(self):
        command = [sys.executable, '-B', '-c', 'import time; time.sleep(60)']
        target = subprocess.Popen(command, start_new_session=True)
        neighbor = subprocess.Popen(command, start_new_session=True)
        descriptor = os.pidfd_open(target.pid)
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            replace_waiter.terminate_once(descriptor)
            self.assertEqual(target.wait(timeout=5), -signal.SIGTERM)
            self.assertIsNone(neighbor.poll())
        finally:
            os.close(descriptor)
            for process in (target, neighbor):
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
