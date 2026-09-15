from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from gpu import orch_r121_route_astra_fast as fast


class FastTests(unittest.TestCase):
    def test_actual_runner_low_short_timeout(self):
        function=fast.runner()
        self.assertIn('low',function.__code__.co_consts)
        self.assertIn(512,function.__code__.co_consts)
        self.assertIn(20,function.__code__.co_consts)
        self.assertNotIn(4096,function.__code__.co_consts)
        self.assertIs(function.__globals__['parse_strong'],fast.prior.parse)

    def test_evaluate_preserves_single_attempt_and_latency(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'RESULT.json'
            def actual_shape(*args,**kwargs):
                result=dict(status='MISSING',retry=False,provider_dispatched=False)
                fast.transport.write(path,result)
                return result
            with patch.object(fast.prior,'evaluate',side_effect=actual_shape) as evaluate:
                result=fast.evaluate({},Path(temporary),100,config={},launch={},prompt_root=None,principles_path=None)
            self.assertTrue((Path(temporary)/'FAST_RECEIPT.json').exists())
            self.assertNotIn('parent_effort',fast.transport.loads(path.read_text()))
        self.assertEqual(result['parent_effort'],'low')
        self.assertEqual(result['output_budget'],512)
        self.assertGreaterEqual(result['elapsed_seconds'],0)
        evaluate.assert_called_once()
        self.assertFalse(result['retry'])


if __name__=='__main__': unittest.main()
