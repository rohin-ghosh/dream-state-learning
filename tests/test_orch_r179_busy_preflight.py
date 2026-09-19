"""Proven non-GPU argv drift is diagnostic, never a clear-device receipt."""

from copy import deepcopy
import unittest

from gpu import orch_r179_busy_preflight as preflight


class BusyPreflightTests(unittest.TestCase):
    def setUp(self):
        identity = dict(pid=42, uid=0, start_ticks='123', boot_id='boot')
        self.report = dict(scanner_euid=0, clear=False,
            gpu=dict(uuid='GPU-target', memory_used_mib=20000),
            compute_processes=[dict(pid=99, gpu_uuid='GPU-target')],
            processes=[dict(identity, command_sha256='a'*64, target_device_open=False,
                cvd=None, pinned_identity=dict(identity, command_sha256='b'*64))],
            blocking_reasons=['active_compute_pid:99', 'open_device_pid:99', 'process_identity_drift:42'])
        self.samples = {42: [dict(identity, executable_identity=[1, 2], visibility_complete=True,
            target_open=False, cvd=None, command_sha256=letter*64) for letter in ('a', 'b', 'b')]}

    def test_argv_only_classification_does_not_clear_a_busy_GPU(self):
        original = deepcopy(self.report)
        result = preflight.annotate(self.report, self.samples)
        self.assertEqual(self.report, original)
        self.assertEqual({key: value for key, value in result.items() if key != 'r179_preflight_evidence'}, original)
        evidence = result['r179_preflight_evidence']
        self.assertEqual(evidence['eligible_non_gpu_argv_only_pids'], [42])
        self.assertFalse(evidence['admission_receipt'])
        self.assertFalse(result['clear'])
        self.assertEqual(result['blocking_reasons'], original['blocking_reasons'])

    def test_any_kernel_or_executable_identity_change_rejects_classification(self):
        for field in ('pid', 'uid', 'start_ticks', 'boot_id', 'executable_identity'):
            samples = deepcopy(self.samples)
            samples[42][-1][field] = 'changed'
            with self.subTest(field=field):
                self.assertEqual(preflight.classify_argv_only(self.report, samples), [])

    def test_any_GPU_visibility_or_incomplete_visibility_rejects(self):
        for field, value in (('target_open', True), ('cvd', 'GPU-target'), ('visibility_complete', False)):
            samples = deepcopy(self.samples)
            samples[42][1][field] = value
            with self.subTest(field=field):
                self.assertEqual(preflight.classify_argv_only(self.report, samples), [])

    def test_GPU_owner_or_other_compute_process_is_not_exempted(self):
        for field, value in (('target_device_open', True), ('cvd', '0')):
            report = deepcopy(self.report)
            report['processes'][0][field] = value
            self.assertEqual(preflight.classify_argv_only(report, self.samples), [])
        report = deepcopy(self.report)
        report['compute_processes'].append(dict(pid=42, gpu_uuid='GPU-other'))
        self.assertEqual(preflight.classify_argv_only(report, self.samples), [])

    def test_missing_samples_or_kernel_binding_fails_closed(self):
        samples = deepcopy(self.samples)
        samples[42].pop()
        self.assertEqual(preflight.classify_argv_only(self.report, samples), [])
        report = deepcopy(self.report)
        del report['processes'][0]['pinned_identity']['boot_id']
        self.assertEqual(preflight.classify_argv_only(report, self.samples), [])
        samples = deepcopy(self.samples)
        del samples[42][0]['executable_identity']
        self.assertEqual(preflight.classify_argv_only(self.report, samples), [])

    def test_stable_argv_or_nonprivileged_report_is_not_exempted(self):
        samples = deepcopy(self.samples)
        for sample in samples[42]:
            sample['command_sha256'] = 'a'*64
        self.assertEqual(preflight.classify_argv_only(self.report, samples), [])
        self.assertEqual(preflight.classify_argv_only(dict(self.report, scanner_euid=1000), self.samples), [])


if __name__ == '__main__':
    unittest.main()
