from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_r118_shared_handoff as handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        for name in ('CONFIG.json','ACTIVATION.json','COUNTERS.json','BROKER_CONFIG.json','LAUNCH.json','SHARED_CLIENT_READY.json'):
            handoff.shared.write(self.root/name,dict(original=name))
        files={'carry':'cycle009/BOUNDARY.json','complete':'cycle009/COMPLETE.json',
            'readout':'readouts/cycle_009/COMPLETE.json','counters_file':'COUNTERS.json'}
        for key,name in files.items():
            if key!='counters_file':handoff.shared.write(self.root/name,dict(original=name))
        handoff.shared.write(self.root/'reservations/native_0001.json',dict(count=1))
        self.saved=dict(cycle=9,next_cycle=10,counters=dict(native=268,parent=54),empty_successor=None,
            reservations={'native_0001.json':'test'},**{key:handoff.ready.reference(self.root/name) for key,name in files.items()})

    def released(self):
        handoff.shared.write(self.root/'shared_handoff_r118/release/RELEASED.json',dict(actor={'pid':12},supervisor={'pid':13}))

    def test_no_actual_release_no_certificate(self):
        with self.assertRaises(FileNotFoundError):handoff.publish(self.root)
        self.assertFalse((self.root/'R118_SHARED_HANDOFF_BRANCH.json').exists())

    def test_certificate_exact_schema_and_relative_preserved_hashes(self):
        self.released()
        with patch.object(handoff.boundary,'verify_release',return_value=self.saved):
            result=handoff.publish(self.root)
        self.assertEqual(result['next_cycle'],10)
        self.assertEqual(result['bounds']['cycles'],43)
        self.assertEqual(result['counters'],dict(native=268,parent=54))
        self.assertTrue(all(not Path(name).is_absolute() for name in result['preserved_files']))
        self.assertIn('reservations/native_0001.json',result['preserved_files'])
        self.assertEqual(result['preserved_files']['CONFIG.json'],handoff.shared.sha(self.root/'CONFIG.json'))

    def test_publish_idempotent_and_never_silently_rewrites(self):
        self.released()
        with patch.object(handoff.boundary,'verify_release',return_value=self.saved):
            first=handoff.publish(self.root)
            self.assertEqual(first,handoff.publish(self.root))
            handoff.shared.write(self.root/'CONFIG.json',dict(changed=True),replace=True)
            with self.assertRaisesRegex(ValueError,'immutable_branch_handoff'):handoff.publish(self.root)

    def test_verification_failure_blocks_publication(self):
        self.released()
        with patch.object(handoff.boundary,'verify_release',side_effect=ValueError('old actor alive')):
            with self.assertRaisesRegex(ValueError,'old actor alive'):handoff.publish(self.root)
        self.assertFalse((self.root/'R118_SHARED_HANDOFF_BRANCH.json').exists())


if __name__=='__main__':unittest.main()
