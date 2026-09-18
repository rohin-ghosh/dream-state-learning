"""CPU failure/replay/scope regressions for the one exact retired-lane recovery."""

from copy import deepcopy
from pathlib import Path
import unittest

import recover_lane3_preload as recovery


def fixture():
    return dict(physical=3, root=str(recovery.LIFE), gpu_uuid=recovery.GPU_UUID, wall=recovery.WALL,
        resume=True, minor=0, retired=True, old_owners_alive=[], supervisor_alive=False,
        post_admission_artifacts=[], loaded_receipt=False,
        admission=dict(clear=False, scanner_euid=0, blocking_reasons=list(recovery.EXPECTED_BLOCKERS),
                       gpu=dict(uuid=recovery.GPU_UUID)),
        log='ValueError: unchanged_global_exclusive_admission\n',
        saved_evidence=dict(cycle=40, optimizer_steps=4260), boundary_evidence=dict(cycle=40, optimizer_steps=4260),
        readout_preserved=True, record_inventory_preserved=True)


class RecoveryTests(unittest.TestCase):
    def test_exact_preload_failure(self):
        recovery.validate_failure(fixture())

    def test_other_devices_and_lives_are_rejected(self):
        for key, value in [('physical', 6), ('physical', 5), ('physical', 0), ('root', '/other/run1'),
                           ('gpu_uuid', 'GPU-other'), ('minor', 5), ('wall', recovery.WALL+1), ('resume', False)]:
            with self.subTest(key=key, value=value):
                facts = fixture()
                facts[key] = value
                with self.assertRaises(ValueError):
                    recovery.validate_failure(facts)

    def test_live_owners_or_supervisor_forbid_recovery(self):
        for key, value in [('old_owners_alive', [1]), ('supervisor_alive', True), ('retired', False)]:
            facts = fixture()
            facts[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.validate_failure(facts)

    def test_any_native_progress_or_dispatch_forbids_replay(self):
        for artifact in recovery.AFTER_ADMISSION:
            facts = fixture()
            facts['post_admission_artifacts'] = [artifact]
            with self.subTest(artifact=artifact), self.assertRaises(ValueError):
                recovery.validate_failure(facts)
        facts = fixture()
        facts['loaded_receipt'] = True
        with self.assertRaises(ValueError):
            recovery.validate_failure(facts)

    def test_exact_state_and_readout_required(self):
        for key, value in [('saved_evidence', dict(cycle=39, optimizer_steps=4260)),
                           ('record_inventory_preserved', False), ('readout_preserved', False)]:
            facts = fixture()
            facts[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.validate_failure(facts)

    def test_no_forged_clear_or_different_failure(self):
        for change in ({'clear': True}, {'scanner_euid': 2524}, {'blocking_reasons': []},
                       {'blocking_reasons': ['active_compute_pid:1']}, {'gpu': dict(uuid='GPU-other')}):
            facts = fixture()
            facts['admission'].update(change)
            before = deepcopy(facts)
            with self.subTest(change=change), self.assertRaises(ValueError):
                recovery.validate_failure(facts)
            self.assertEqual(facts, before)
        facts = fixture()
        facts['log'] = 'ValueError: native CUDA failure'
        with self.assertRaises(ValueError):
            recovery.validate_failure(facts)

    def test_config_keeps_wall_resume_scope_and_all_unknown_guards(self):
        previous = dict(resume=True, hard_end_unix=recovery.WALL, preserved_guard={'threshold': 5},
            device_containment=dict(unit='old', minor=0, uid=2524, gid=2524),
            lease_path='existing', lease_sha256='exact')
        before = deepcopy(previous)
        result = recovery.make_guard(previous, Path('/new/control'), Path('/new/source'), 'plan', 'allocation',
                                     {'gpu/native.py': 'same', 'metadata.json': 'same'})
        self.assertEqual(previous, before)
        self.assertEqual(result['preserved_guard'], previous['preserved_guard'])
        self.assertEqual(result['hard_end_unix'], recovery.WALL)
        self.assertEqual(result['device_containment']['minor'], 0)
        self.assertNotEqual(result['device_containment']['unit'], previous['device_containment']['unit'])
        self.assertEqual(result['lease_sha256'], 'exact')
        self.assertEqual(result['source_pins'], {'gpu/native.py': 'same'})


if __name__ == '__main__':
    unittest.main()
