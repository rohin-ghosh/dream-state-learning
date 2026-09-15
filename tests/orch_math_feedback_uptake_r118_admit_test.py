import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import Mock,patch

from gpu import orch_math_feedback_uptake_r118_shared_admit as admit


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def test_fresh_scan_not_filtered_previous_failure_preserved(self):
        reports=[dict(clear=False,blocking_reasons=['process_identity_drift:3159'],scanner_euid=0),
            dict(clear=True,blocking_reasons=[],scanner_euid=0)]
        call=Mock(side_effect=[SimpleNamespace(stdout=json.dumps(report)) for report in reports])
        result=admit.scan_until_clear(self.root,self.root,time.time()+60,scan_call=call,pause=lambda unused:None)
        self.assertTrue(result['clear'])
        self.assertEqual(call.call_count,2)
        self.assertEqual(admit.run.shared.read(self.root/'ADMISSION_000.json'),reports[0])
        self.assertEqual(call.call_args.args[0][:4],['sudo','-n','env','CUDA_VISIBLE_DEVICES='])

    def test_any_blocker_or_nonroot_is_never_accepted(self):
        report=dict(clear=True,blocking_reasons=['actual_owner'],scanner_euid=0)
        call=Mock(return_value=SimpleNamespace(stdout=json.dumps(report)))
        with self.assertRaisesRegex(ValueError,'never_clear'):
            admit.scan_until_clear(self.root,self.root,time.time()+60,scan_call=call,pause=lambda unused:None)
        self.assertEqual(call.call_count,60)

    def test_existing_native_launch_never_replayed(self):
        (self.root/'SHARED_LAUNCH.json').write_text('{}')
        with patch.object(admit.run,'activation',return_value={}):
            with self.assertRaisesRegex(ValueError,'no_shared_native_relaunch'):admit.pristine(self.root)

    def test_deadline_prevents_any_scan(self):
        call=Mock()
        with self.assertRaisesRegex(ValueError,'bounded_admission'):
            admit.scan_until_clear(self.root,self.root,time.time()-1,scan_call=call)
        call.assert_not_called()


if __name__=='__main__':unittest.main()
