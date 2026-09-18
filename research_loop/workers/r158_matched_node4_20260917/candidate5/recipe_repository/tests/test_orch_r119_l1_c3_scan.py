from copy import deepcopy
import unittest
from gpu import orch_math_feedback_uptake_r118_argv_admission as existing
from gpu.orch_r119_l1_c3_scan import strict_reconcile


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        identity=dict(pid=4583,uid=0,start_ticks='1821',boot_id='boot')
        self.samples=[dict(identity,command_sha256=str(index),visibility_complete=True,target_open=False,
            cvd=None,executable_identity=[1,2]) for index in range(3)]
        self.report=dict(scanner_euid=0,gpu=dict(memory_used_mib=0,uuid='GPU-owned'),compute_processes=[],
            processes=[dict(identity,cvd=None,target_device_open=False,pinned_identity=identity)],
            blocking_reasons=['process_identity_drift:4583'],clear=False)

    def test_only_stable_complete_three_observations_can_clear(self):
        self.assertTrue(strict_reconcile(existing.reconcile,self.report,{4583:self.samples})['clear'])
        self.assertFalse(strict_reconcile(existing.reconcile,self.report,{4583:self.samples[:2]})['clear'])

    def test_exec_kernel_unknown_and_FD_never_waived(self):
        for key,value in [('executable_identity',[1,3]),('start_ticks','1822'),('uid',9),
                          ('boot_id','new'),('target_open',True),('visibility_complete',False)]:
            samples=deepcopy(self.samples);samples[1][key]=value
            with self.subTest(key=key):self.assertFalse(strict_reconcile(existing.reconcile,self.report,{4583:samples})['clear'])

    def test_changed_CVD_even_empty_variants_rejected(self):
        for value in ('','-1','GPU-owned'):
            samples=deepcopy(self.samples);samples[1]['cvd']=value
            self.assertFalse(strict_reconcile(existing.reconcile,self.report,{4583:samples})['clear'])

    def test_nonzero_memory_or_compute_never_waived(self):
        report=deepcopy(self.report);report['gpu']['memory_used_mib']=1
        self.assertFalse(strict_reconcile(existing.reconcile,report,{4583:self.samples})['clear'])
        report=deepcopy(self.report);report['compute_processes']=[dict(gpu_uuid='GPU-owned',pid=4583)]
        self.assertFalse(strict_reconcile(existing.reconcile,report,{4583:self.samples})['clear'])

    def test_unknown_blocker_and_incomplete_visibility_retained(self):
        report=deepcopy(self.report);report['blocking_reasons'].append('unknown_minor_process_visibility:99:OSError')
        self.assertFalse(strict_reconcile(existing.reconcile,report,{4583:self.samples})['clear'])


if __name__=='__main__':unittest.main()
