from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from gpu import orch_r120_route_final_custody as custody
from gpu import orch_r120_route_clock as lease


class CompletedFinalCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.complete = self.save('COMPLETE.json', dict(scope='FINAL'))
        self.selection = self.save('FINAL_SELECTION.json', dict(generation=1))
        self.terminal_value = dict(success=True, returncode=0, no_replay=True, parent_calls=0,
            optimizer_steps=0, native_calls=16, complete=self.complete, selected=self.selection)
        self.terminal = self.save('FINISHED.json', self.terminal_value)
        self.evidence = dict(complete=self.complete, selection=self.selection, terminal=self.terminal)

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return custody.reference(path)

    def test_original_complete_success_and_hashes(self):
        self.assertEqual(custody.validate_completed(self.evidence)['native_calls'], 16)
        (self.root / 'COMPLETE.json').write_text('changed')
        with self.assertRaises(ValueError):
            custody.validate_completed(self.evidence)

    def test_failed_or_retried_or_trained_evaluation_rejected(self):
        for update in (dict(success=False), dict(returncode=1), dict(no_replay=False),
                       dict(parent_calls=1), dict(optimizer_steps=1), dict(native_calls=49)):
            evidence = dict(self.evidence, terminal=self.save('test-terminal.json', dict(self.terminal_value, **update)))
            with self.assertRaises(ValueError):
                custody.validate_completed(evidence)

    def test_final_selection_cannot_change(self):
        evidence = dict(self.evidence, selection=self.save('other-selection.json', dict(generation=2)))
        with self.assertRaisesRegex(ValueError, 'selection_join'):
            custody.validate_completed(evidence)

    def test_actual_CPU_custodian_start_and_terminal_exit(self):
        import time
        source = custody.reference(custody.__file__)
        plan = dict(physical=0, shared_learner=dict(branch='F1'), bounds=dict(hard_end_unix=time.time()+30),
            source_files={source['path']:source['sha256']},
            lease_continuation=dict(completed_final=self.evidence, policy=dict(path='/policy',sha256='policy')))
        self.save('R118_PARALLEL_PLAN.json',plan)
        process, binding = custody.start(self.root, plan, custody.identity(os.getpid()), sys.executable)
        try:
            document = custody.checked(binding['evidence'])
            self.assertEqual(document['role'], 'COMPLETED_FINAL_CUSTODIAN_NO_EVALUATION')
            self.assertTrue(document['never_dispatch'])
            self.assertEqual(document['evaluation_calls'], 0)
            self.assertTrue(custody.alive(binding['identity']))
            environment = (Path('/proc')/str(process.pid)/'environ').read_bytes().split(b'\0')
            self.assertIn(b'CUDA_VISIBLE_DEVICES=', environment)
            supervision = lease.supervision(self.root, plan, custody.identity(os.getpid()),
                custody.identity(os.getpid()), source, binding)
            self.assertEqual(supervision['final_identity_bindings'], [binding])
            from gpu import orch_r118_parallel_consolidation as backend
            certificate = dict(identity=custody.identity(os.getpid()), retained_supervision=supervision,
                launch_device=dict(kind='cpu', physical=0, cuda_visible_devices=''))
            backend.validate_launch_participant(certificate, 'F1', 'CPU_FIXTURE')
            self.save('R118_PARALLEL_GUARD_TERMINAL.json',dict(returncode=0))
            self.assertEqual(process.wait(timeout=6),0)
            self.assertFalse(custody.alive(binding['identity']))
            self.assertEqual(custody.checked(custody.reference(
                self.root/'R120_COMPLETED_FINAL_CUSTODY/EXITED.json'))['evaluation_calls'],0)
        finally:
            if process.poll() is None:
                self.save('R118_PARALLEL_GUARD_TERMINAL.json',dict(returncode=0))
                process.wait(timeout=6)

    def test_stale_guardian_not_rebound(self):
        guardian = custody.identity(os.getpid())
        guardian['start_ticks'] -= 1
        with self.assertRaisesRegex(ValueError, 'exact_guardian_identity'):
            custody.start(self.root, {}, guardian, sys.executable)


if __name__ == '__main__':
    unittest.main()
