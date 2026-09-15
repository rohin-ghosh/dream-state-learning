import inspect
import unittest
from gpu.orch_r119_l1_gen7_continue import resumed_source
from gpu import orch_r109_l1_generation_v3 as original


class CursorTests(unittest.TestCase):
    def test_only_cursor_accounting_and_carry_hook_change(self):
        source=inspect.getsource(original.generate)
        resumed=resumed_source(source)
        restored=resumed.replace("    start_calls = inherited.get('original_segment_start_calls', inherited['calls'])\n    count = inherited['calls']","    start_calls = count = inherited['calls']")
        restored=restored.replace('\n    restore_carry(directory)','')
        self.assertEqual(source,restored)
        self.assertIn('count-start_calls < 16384-32',resumed)
        self.assertIn("inherited['position']+2",resumed)
        compile(resumed,'fixture','exec')

    def test_remaining_budget_and_next_cursor_no_reset(self):
        inherited=dict(calls=20286,original_segment_start_calls=15842,batch=292,position=15)
        start=inherited.get('original_segment_start_calls',inherited['calls'])
        self.assertEqual(16384-(inherited['calls']-start),11940)
        self.assertEqual((inherited['calls']+1,inherited['batch'],inherited['position']+2),(20287,292,17))

    def test_unknown_source_shape_rejected(self):
        with self.assertRaises(AssertionError):resumed_source('def generate(index): pass')


if __name__=='__main__':unittest.main()
