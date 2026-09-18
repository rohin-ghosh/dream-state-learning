import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

from gpu import orch_r120_route_life as life


class RouteLeaseContinuationTests(unittest.TestCase):
    def test_preimported_package_loads_frozen_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source/'gpu').mkdir()
            (source/'gpu/orch_r120_fixture_dependency.py').write_text('VALUE = 17\n')
            (source/'gpu/orch_r111_route_recovery.py').write_text(
                'from gpu import orch_r120_fixture_dependency\nVALUE = orch_r120_fixture_dependency.VALUE\n')
            runtime = life.load_runtime(source,'node1_7',source)
            self.assertEqual(runtime.VALUE,17)

    def test_partial_charged_cycle_never_regenerated(self):
        self.assertEqual(life.resume_cycle([{'cycle':40}],39,256),41)

    def test_empty_reservations_follow_checkpoint(self):
        self.assertEqual(life.resume_cycle([],39,256),40)

    def test_no_silent_new_cohort(self):
        with self.assertRaises(ValueError):life.resume_cycle([{'cycle':256}],255,256)

    def test_report_cut_not_new_lease(self):
        ready=dict(lease_end_unix=200000,lease_margin_seconds=21600,hard_deadline_unix=10)
        result=life.lease_bounds(ready,100000)
        self.assertEqual(result['hard_deadline_unix'],178400)
        self.assertEqual(result['native_deadline_unix'],178280)
        self.assertEqual(ready['hard_deadline_unix'],10)

    def test_expired_lease_rejected(self):
        with self.assertRaises(ValueError):life.lease_bounds(dict(lease_end_unix=100,lease_margin_seconds=10),100)

    def test_destination_binding_preserves_learning_mode(self):
        policy=SimpleNamespace(LANES={'node1_7':dict(host='node1',physical=7,uuid='GPU-old',learned=False)},DEVICES={'node1_7':'GPU-old'})
        runtime=SimpleNamespace(old=SimpleNamespace(policy=policy))
        life.apply_relocation(runtime,dict(lane='node1_7',target_physical=0,target_wrapper='gpu/a40r_ssh.sh',target_uuid='GPU-new'),'node1_7')
        self.assertEqual(policy.DEVICES['node1_7'],'GPU-new')
        self.assertFalse(policy.LANES['node1_7']['learned'])

    def test_no_unallocated_slot(self):
        with self.assertRaises(ValueError):
            life.apply_relocation(None,dict(lane='node1_7',target_physical=7),'node1_7')


if __name__=='__main__':unittest.main()
