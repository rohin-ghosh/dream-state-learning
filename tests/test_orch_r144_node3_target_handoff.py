from copy import deepcopy
import fcntl
import os
import tempfile
import unittest

from gpu.orch_r144_node3_target_handoff import BASE, OTHER_ROOTS, OTHER_UUIDS, claim_boundary, direct_command, guard_delta, lane_scope, plan_delta, readmission_guard, verify_legacy_state


class TargetHandoffTests(unittest.TestCase):
    def setUp(self):
        self.plan = dict(source_root='/old', root='/life', hard_end_unix=100, seed=0,
                         context_limit=16384, rehearsal_presentations=1, startup_context=dict(path='/old/STARTUP.md', sha256='same'))
        self.new_plan = deepcopy(self.plan)
        self.new_plan.update(source_root='/new', startup_context=dict(path='/new/STARTUP.md', sha256='same'))
        self.guard = dict(plan_path='/old/PLAN', plan_sha256='old', source_pins={'native.py': 'old'},
            attempt_dir='/old/control', resume=False, allocation_path='/old/ALLOCATION', allocation_sha256='old',
            lease_path='/lease', lease_sha256='same', device_containment=dict(unit='old', uid=2524, gid=2524, minor=3))
        self.new_guard = deepcopy(self.guard)
        self.new_guard.update(plan_path='/new/PLAN', plan_sha256='new', source_pins={'native.py': 'new'},
            attempt_dir='/new/control', resume=True, allocation_path='/new/ALLOCATION', allocation_sha256='new')
        self.new_guard['device_containment']['unit'] = 'new'

    def test_exact_plan_relocation(self):
        plan_delta(self.plan, self.new_plan)

    def test_rejects_training_and_life_changes(self):
        for key, value in [('root', '/other'), ('hard_end_unix', 200), ('seed', 2),
                           ('context_limit', 8192), ('rehearsal_presentations', 0)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                plan_delta(self.plan, dict(self.new_plan, **{key: value}))

    def test_rejects_startup_bytes_or_path_change(self):
        for change in (dict(path='/other/STARTUP.md', sha256='same'), dict(path='/new/STARTUP.md', sha256='changed')):
            with self.assertRaises(ValueError):
                plan_delta(self.plan, dict(self.new_plan, startup_context=change))

    def test_exact_guard_rebinding(self):
        guard_delta(self.guard, self.new_guard)

    def test_no_foreign_device_or_identity_change(self):
        for key, value in [('minor', 4), ('uid', 0), ('gid', 0)]:
            changed = deepcopy(self.new_guard)
            changed['device_containment'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                guard_delta(self.guard, changed)

    def test_no_lease_change(self):
        with self.assertRaises(ValueError):
            guard_delta(self.guard, dict(self.new_guard, lease_sha256='changed'))

    def test_no_reset_or_attempt_reuse(self):
        for changes in (dict(resume=False), dict(attempt_dir=self.guard['attempt_dir'])):
            with self.assertRaises(ValueError):
                guard_delta(self.guard, dict(self.new_guard, **changes))

    def test_no_containment_unit_reuse(self):
        changed = deepcopy(self.new_guard)
        changed['device_containment']['unit'] = self.guard['device_containment']['unit']
        with self.assertRaises(ValueError):
            guard_delta(self.guard, changed)

    def test_direct_command_strict_clean_env_exact_device(self):
        for physical in (0, 2):
            plan = dict(physical=physical, gpu_uuid=OTHER_UUIDS[physical], source_root='/new/source')
            policy = dict(minor=physical, uid=2524, gid=2524, unit='orch-r144-native-' + 'a' * 32)
            command = direct_command(plan, policy, ['python', '-B', 'native'], 60)
            self.assertIn('--property=DevicePolicy=strict', command)
            self.assertIn('--property=NoNewPrivileges=yes', command)
            self.assertIn('--property=CapabilityBoundingSet=', command)
            self.assertEqual(command[command.index('/usr/bin/env') + 1], '-i')
            allowed = [value for value in command if value.startswith('--property=DeviceAllow=/dev/nvidia')]
            self.assertEqual(allowed, [f'--property=DeviceAllow=/dev/nvidia{physical} rw',
                                      '--property=DeviceAllow=/dev/nvidiactl rw', '--property=DeviceAllow=/dev/nvidia-uvm rw'])

    def test_direct_command_rejects_foreign_or_root(self):
        plan = dict(physical=0, gpu_uuid=OTHER_UUIDS[0], source_root='/new')
        policy = dict(minor=0, uid=2524, gid=2524, unit='orch-r144-native-' + 'a' * 32)
        for changes in (dict(minor=2), dict(uid=0), dict(gid=0), dict(minor=False), dict(unit='other')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                direct_command(plan, dict(policy, **changes), ['native'], 60)
        with self.assertRaises(ValueError):
            direct_command(dict(plan, gpu_uuid=OTHER_UUIDS[2]), policy, ['native'], 60)

    def test_exact_legacy_roots_and_excludes_recovery(self):
        for physical, (namespace, suffix) in OTHER_ROOTS.items():
            plan = dict(physical=physical, gpu_uuid=OTHER_UUIDS[physical],
                        root=str(BASE / namespace / 'run1'), source_root=str(BASE / namespace / suffix))
            self.assertEqual(lane_scope(plan), physical)
            for changes in (dict(root='/other/run1'), dict(source_root='/other/source'), dict(preupdate_recovery=True)):
                with self.assertRaises(ValueError):
                    lane_scope(dict(plan, **changes))
        for physical in (5, 6, True):
            with self.assertRaises(ValueError):
                lane_scope(dict(physical=physical))

    def test_new_direct_policy_cannot_broaden(self):
        old = deepcopy(self.guard)
        old.pop('device_containment')
        new = deepcopy(self.new_guard)
        new['device_containment'] = dict(minor=0, uid=2524, gid=2524, unit='orch-r144-native-' + 'a' * 32)
        guard_delta(old, new)
        for changes in (dict(minor=1), dict(uid=0), dict(allow_foreign=True)):
            invalid = deepcopy(new)
            invalid['device_containment'].update(changes)
            with self.assertRaises(ValueError):
                guard_delta(old, invalid)

    def test_only_one_boundary_owner_while_other_waiters_stay_live(self):
        with tempfile.NamedTemporaryFile() as lock_file:
            first = os.open(lock_file.name, os.O_RDWR)
            second = os.open(lock_file.name, os.O_RDWR)
            try:
                self.assertTrue(claim_boundary(first))
                self.assertFalse(claim_boundary(second))
                fcntl.flock(first, fcntl.LOCK_UN)
                self.assertTrue(claim_boundary(second))
            finally:
                os.close(first)
                os.close(second)

    def test_exact_legacy_saved_protocol(self):
        plan = dict(physical=0, seed=0, context_limit=16384, segment_tokens=512, segments_per_sleep=2,
                    hard_end_unix=123, system_prompt='system', birth_prompt='birth', presentation_version='plain')
        state = dict(context_limit=16384, segment_tokens=512, segments_per_sleep=2, deadline_unix=123,
                     pending=None, sleep_frontier=1, rows=[{}], sleep_receipts=[dict(status='COMPLETE')],
                     history=dict(system_prompt='system', birth_prompt='birth'),
                     presentation=dict(version='plain', system_prompt='system', birth_prompt='birth'))
        verify_legacy_state(plan, state, {})
        for changes in (dict(pending='sleep:pending'), dict(sleep_frontier=0), dict(experiment=None),
                        dict(context_limit=8192), dict(deadline_unix=124), dict(sleep_receipts=[]),
                        dict(presentation=dict(version='plain', system_prompt='other', birth_prompt='birth'))):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                verify_legacy_state(plan, dict(state, **changes), {})
        for changes in (dict(physical=5), dict(seed=1), dict(presleep_variant='no_distillation')):
            with self.assertRaises(ValueError):
                verify_legacy_state(dict(plan, **changes), state, {})
        with self.assertRaises(ValueError):
            verify_legacy_state(plan, state, dict(experiment=None))

    def test_readmission_changes_only_attempt_and_unit(self):
        for physical, prefix in ((0, 'orch-r144-native-'), (1, 'orch-r136-native-'), (3, 'orch-r133-node3-')):
            original = deepcopy(self.new_guard)
            actual = readmission_guard(original, dict(physical=physical), '/fresh/control')
            self.assertEqual(original, self.new_guard)
            self.assertTrue(actual['device_containment']['unit'].startswith(prefix))
            actual['device_containment']['unit'] = original['device_containment']['unit']
            actual['attempt_dir'] = original['attempt_dir']
            self.assertEqual(actual, original)

    def test_readmission_rejects_reset_and_attempt_reuse(self):
        with self.assertRaises(ValueError):
            readmission_guard(dict(self.new_guard, resume=False), dict(physical=2), '/fresh')
        with self.assertRaises(ValueError):
            readmission_guard(self.new_guard, dict(physical=2), self.new_guard['attempt_dir'])


if __name__ == '__main__':
    unittest.main()
