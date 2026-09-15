import inspect
import unittest
from gpu.orch_r119_l1_c3_readout_repair import remaining_readout_source
from gpu import orch_r109_l1_train as trainer


class ResumeReadoutTests(unittest.TestCase):
    def test_only_completed_capability_calls_removed(self):
        source=inspect.getsource(trainer.readout)
        result=remaining_readout_source(source)
        begin=source.index('        for task in capability.tasks():')
        end=source.index("        held=read(ROOT/'input/prior/LEGACY_READOUT.json')['held']",begin)
        expected=source[:begin]+source[end:]
        result=result.replace("base_and_adapter_unchanged=True,base_and_adapter_unchanged_scope='REPAIR_PROCESS_ONLY',inherited_capability_postcheck_missing=True,preserved_capability_calls=32,new_capability_calls=0,finished_unix=",'base_and_adapter_unchanged=True,finished_unix=')
        self.assertEqual(result.replace('    calls=preserved_capabilities','    calls=[]'),expected)
        self.assertEqual(result.count('loaded.engine.generate('),1)
        self.assertIn('loaded.verify_unchanged()',result)
        self.assertIn('behavior.collect_cases(held,generate,coached=False)',result)
        compile(result,'fixture','exec')

    def test_unknown_source_rejected(self):
        with self.assertRaises(ValueError):remaining_readout_source('def readout(): pass')


if __name__=='__main__':unittest.main()
