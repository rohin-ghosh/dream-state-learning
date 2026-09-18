import inspect
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gpu import orch_r119_l1_gen7_r127_release as candidate


class RetargetTests(unittest.TestCase):
    def test_only_layout_and_old_attempt_recovery_precondition_changed(self):
        source=inspect.getsource(candidate.original.execute)
        changed=candidate.retarget(source)
        self.assertIn('boundary = handover.boundary_status(output)',changed)
        self.assertIn("snapshot = scan(7, Path(config['service_identity']))",changed)
        restored=changed.replace("    assert not (DEST / 'PRE_SIGNAL.json').exists(), 'new_one_shot_release_only'",
            "    assert read(HANDOVER / 'EXECUTOR_CANCELLED.json')['status'] == 'CANCELLED_PRE_RETIREMENT_SUPERVISOR_AND_NATIVE_CONTINUED'")
        for suffix in ("'START.json'","'HEARTBEAT.json'","('segment%04d' % heartbeat['segment'])"):
            restored=restored.replace('ROOT / '+suffix,"ROOT / 'gpu7' / "+suffix)
        self.assertEqual(restored,source)
        compile(changed,'fixture','exec')

    def test_current_own_command_without_legacy_index_and_stale_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            worker=root/'orch_r119_l1_gen7_continue.py'
            worker.write_text('import time; time.sleep(30)')
            candidate.original.write(root/'CURSOR_RESUME.json',dict(source_sha256=candidate.original.sha(worker)))
            child=subprocess.Popen([sys.executable,str(worker),'supervise','--root',str(root)])
            try:
                identity=candidate.original.identity(child.pid)
                descriptor=candidate.owned_descriptor(identity,root,'supervise','fixture_uuid')
                os.close(descriptor)
                with self.assertRaises(AssertionError):
                    candidate.owned_descriptor(dict(identity,start_ticks='stale'),root,'supervise','fixture_uuid')
                with self.assertRaises(AssertionError):
                    candidate.owned_descriptor(identity,root,'generate','fixture_uuid')
                self.assertIsNone(child.poll())
            finally:
                child.terminate();child.wait()


if __name__=='__main__':unittest.main()
