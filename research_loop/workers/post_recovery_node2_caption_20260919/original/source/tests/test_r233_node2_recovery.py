"""CPU-only scope, saved-state integrity and finite-wall regressions."""

from copy import deepcopy
import unittest

from gpu.r213_recovery_runtime import saved_state
from gpu.r233_node2_recovery import binding, bounded_command, supervisor_source, POLICY, TARGETS
from organism_v6.orch_r125_continual_stream import digest


class RecoveryTests(unittest.TestCase):
    def test_existing_prebound_scanner_is_preserved(self):
        source = """bound = child.read(attempt/'PRE_SERVICE_ADMISSION.json')
        child.require(bound['guard_sha256'] == child.sha(config_path)
            and 0 <= time.time()-bound['verified_unix'] <= 120, 'fresh_bound_privileged_preservice_scan')
        report = bound['report']
        command = ['gpu.orch_r125_continual_guard', 'gpu.orch_r125_continual_guard']"""
        actual = supervisor_source(source)
        self.assertIn('fresh_bound_privileged_preservice_scan', actual)
        self.assertIn("report = bound['report']", actual)
        self.assertEqual(actual.count("'gpu.r233_node2_recovery'"), 2)
        with self.assertRaises(ValueError):
            supervisor_source(source.replace('<= 120', '<= 999'))

    def plan(self):
        name, target = next(iter(TARGETS.items()))
        return dict(source_root='/synthetic/' + name + '/source_r233_recovery',
            physical=target[0], gpu_uuid=target[1], learn_row_policy=POLICY,
            think_act_learn=dict(learn_row_policy=POLICY), hard_end_unix=1000, lease_end_unix=2000)

    def test_only_original_targets_both_policies(self):
        plan = self.plan()
        self.assertEqual(binding(plan)[0], 4)
        for delta in ({'physical': 1}, {'gpu_uuid': 'GPU-other'}, {'learn_row_policy': None},
                {'think_act_learn': {}}, {'code_target_filter': 'legacy'},
                {'source_root': '/synthetic/unrelated/source'}):
            with self.subTest(delta=delta), self.assertRaises(ValueError):
                binding(dict(plan, **delta))

    def test_preserves_confinement_and_caps_existing_lease(self):
        command = ['systemd-run', '--property=RuntimeMaxSec=7200', '--property=DevicePolicy=strict',
            '--property=NoNewPrivileges=yes', '--property=DeviceAllow=/dev/nvidia4 rw']
        result = bounded_command(command, self.plan(), 100)
        self.assertEqual(result[1], '--property=RuntimeMaxSec=885')
        self.assertEqual(result[2:], command[2:])
        self.assertEqual(command[1], '--property=RuntimeMaxSec=7200')
        for now in (990, 1000):
            with self.assertRaises(ValueError):
                bounded_command(command, self.plan(), now)

    def test_saved_state_only_deadline_not_birth_or_tail(self):
        hashes = dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64)
        state = dict(deadline_unix=10, pending=None, rows=[dict(target='own')], sleep_frontier=1,
            model_state_sha256=digest(hashes), history=dict(working_state=dict(entries=['preserve'])))
        record = dict(kind='SLEEP_COMPLETE', document=dict(status='COMPLETE', checkpoint_sha256=hashes,
            checkpoint=dict(checkpoint_sha256=hashes), resume_state=dict(state=state, sha256=digest(state))))
        record['sha256'] = digest(record)
        before = deepcopy(record)
        restored = saved_state(record, 20)
        expected = deepcopy(state)
        expected['deadline_unix'] = 20
        self.assertEqual(restored['state'], expected)
        self.assertEqual(record, before)
        record['document']['resume_state']['state']['rows'][0]['target'] = 'fabricated'
        with self.assertRaises(ValueError):
            saved_state(record, 20)


if __name__ == '__main__':
    unittest.main()
