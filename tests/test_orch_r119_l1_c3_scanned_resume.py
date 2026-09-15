import inspect
import unittest
from gpu import orch_r119_l1_c3_consumer as original
from gpu.orch_r119_l1_c3_scanned_resume import modern_handoff_source


class ModernHandoffTests(unittest.TestCase):
    def test_safe_boundary_and_exit_requirements_preserved(self):
        source=modern_handoff_source(inspect.getsource(original.handoff))
        compile(source,'fixture','exec')
        for exact in ("heartbeat.get('condition') != 'OFF'",'completed_exit(',
                      'readout_proof(trainer,phase_root,arm,segment,checkpoint)',
                      "'next_train_already_started'",'signal.SIGSTOP','signal.SIGTERM',
                      "trainer.sha(checkpoint/'optimizer.pt')","trainer.sha(checkpoint/'rank0.pt')"):
            self.assertIn(exact,source)
        self.assertIn("existing_C3_continuation_only",source)
        self.assertNotIn("previous/'CONTINUATION.json'",source)

    def test_unknown_source_layout_rejected(self):
        with self.assertRaises(AssertionError):modern_handoff_source('def handoff(): pass')


if __name__=='__main__':unittest.main()
