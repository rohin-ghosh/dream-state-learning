from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r125_runtime_scan as repair


class SamplingTests(unittest.TestCase):
    def test_subprocess_rebinding_preserves_launch_interface(self):
        callback=lambda:None
        api=repair.subprocess_api(callback)
        self.assertIs(api.run,callback)
        for name in ('Popen','DEVNULL','STDOUT','TimeoutExpired'):
            self.assertIs(getattr(api,name),getattr(repair.subprocess,name))

    def test_fresh_samples_capture_kernel_exe_visibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exe').write_bytes(b'exe');(root/'environ').write_bytes(b'CUDA_VISIBLE_DEVICES=\0');(root/'fd').mkdir()
            identity=dict(pid=1,uid=1,start_ticks='1',boot_id='boot',command_sha256='a')
            samples=repair.extra_samples(root,'/dev/nvidia5',lambda _:identity)
            self.assertEqual(len(samples),2)
            self.assertTrue(all(sample['visibility_complete'] and not sample['target_open'] for sample in samples))

    def test_fd_transition_observed_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exe').write_bytes(b'exe');(root/'environ').write_bytes(b'');(root/'fd').mkdir();(root/'fd/1').symlink_to('/dev/nvidia5')
            identity=dict(pid=1,uid=1,start_ticks='1',boot_id='boot',command_sha256='a')
            self.assertTrue(all(sample['target_open'] for sample in repair.extra_samples(root,'/dev/nvidia5',lambda _:identity)))

    def test_pid_reuse_or_exec_during_sample_is_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'exe').write_bytes(b'exe');(root/'environ').write_bytes(b'');(root/'fd').mkdir()
            first=dict(pid=1,uid=1,start_ticks='1',boot_id='boot',command_sha256='a')
            second=dict(first,start_ticks='2')
            reader=iter([first,second,first,second])
            self.assertTrue(all(not sample['visibility_complete'] for sample in repair.extra_samples(root,'/dev/nvidia5',lambda _:next(reader))))

    def test_reconciler_still_rejects_exec_CVD_or_FD_changes(self):
        identity=dict(pid=1,uid=1,start_ticks='1',boot_id='boot')
        samples=[dict(identity,command_sha256=str(index),visibility_complete=True,target_open=False,cvd=None,executable_identity=[1,2]) for index in range(3)]
        report=dict(scanner_euid=0,gpu=dict(memory_used_mib=1,uuid='GPU-test'),compute_processes=[],processes=[dict(identity,cvd=None,target_device_open=False,pinned_identity=identity)],blocking_reasons=['process_identity_drift:1'],clear=False)
        self.assertTrue(repair.argv.reconcile(report,{1:samples})['clear'])
        for key,value in (('executable_identity',[1,3]),('cvd','5'),('target_open',True),('start_ticks','2'),('visibility_complete',False)):
            changed=deepcopy(samples);changed[1][key]=value
            with self.subTest(key=key):
                self.assertFalse(repair.argv.reconcile(report,{1:changed})['clear'])
