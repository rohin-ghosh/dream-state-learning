"""No native calls: reject kernel/exec/FD/CVD changes and preserve all evidence."""

from copy import deepcopy
import unittest
from gpu import orch_math_feedback_uptake_r118_argv_admission as repair


def fixture():
    identity = dict(pid=3159, uid=0, start_ticks='2046', boot_id='boot', command_sha256='first')
    samples = [dict(identity, command_sha256=command, executable_identity=[1, 2],
        target_open=False, visibility_complete=True, cvd=None) for command in ('first', 'second', 'first')]
    process = dict(identity, pinned_identity=deepcopy(identity), target_device_open=False, cvd=None)
    report = dict(scanner_euid=0, gpu=dict(uuid='GPU-target', memory_used_mib=1), compute_processes=[],
        processes=[process], blocking_reasons=['process_identity_drift:3159', 'minor_scan_identity_changed:3159'], clear=False)
    return report, {3159:samples}


class ArgvAdmissionTests(unittest.TestCase):
    def test_live_argv_only_has_three_complete_stable_samples(self):
        report, samples = fixture()
        before = deepcopy(report)
        result = repair.reconcile(report, samples)
        self.assertTrue(result['clear'])
        self.assertEqual(report, before)
        self.assertEqual(result['argv_original_report'], before)
        self.assertEqual(result['identity_observations']['3159'], samples[3159])
        self.assertEqual(result['gpu']['memory_used_mib'], 1)

    def test_reuse_exec_fd_cvd_visibility_changes_never_cleared(self):
        for key, value in [('pid',42), ('uid',1), ('start_ticks','other'), ('boot_id','other'),
                ('executable_identity',[1,3]), ('executable_identity',None),
                ('target_open',True), ('cvd','GPU-target'), ('visibility_complete',False)]:
            with self.subTest(key=key, value=value):
                report, samples = fixture()
                samples[3159][1][key] = value
                self.assertFalse(repair.reconcile(report, samples)['clear'])

    def test_insufficient_samples_or_no_actual_argv_change_rejected(self):
        report, samples = fixture()
        self.assertFalse(repair.reconcile(report, {3159:samples[3159][:2]})['clear'])
        for sample in samples[3159]:
            sample['command_sha256'] = 'same'
        self.assertFalse(repair.reconcile(report, samples)['clear'])

    def test_foreign_gpu_unknown_or_unexplained_memory_still_blocks(self):
        for reason in ('open_device_pid:3159','reserved_cvd_pid:3159','device_not_idle',
                'unknown_process_visibility:3159','process_identity_drift:2664384'):
            report, samples = fixture()
            report['blocking_reasons'].append(reason)
            result = repair.reconcile(report,samples)
            self.assertFalse(result['clear'])
            self.assertIn(reason,result['blocking_reasons'])
        report, samples = fixture()
        report['gpu']['memory_used_mib'] = 2
        self.assertFalse(repair.reconcile(report,samples)['clear'])

    def test_original_fd_cvd_compute_and_pinned_identity_required(self):
        for change in ('fd','cvd','compute','pinned'):
            report, samples = fixture()
            if change == 'fd': report['processes'][0]['target_device_open'] = True
            if change == 'cvd': report['processes'][0]['cvd'] = '1'
            if change == 'compute': report['compute_processes'] = [dict(pid=3159,gpu_uuid='GPU-other')]
            if change == 'pinned': report['processes'][0]['pinned_identity']['start_ticks'] = 'new'
            self.assertFalse(repair.reconcile(report,samples)['clear'])


if __name__ == '__main__':
    unittest.main()
