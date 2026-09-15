from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
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

    def test_existing_config_requires_identical_bytes_without_overwrite(self):
        config={'example':'unchanged'}
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'REFERENCE.json'
            fast.transport.write(path,config)
            store=Mock()
            store.exists.return_value=True
            store.hash.return_value=fast.transport.sha(path)
            fast.publish_config(store,config,temporary)
            store.copy.assert_not_called()

    def test_changed_existing_config_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=Mock()
            store.exists.return_value=True
            store.hash.return_value='0'*64
            with self.assertRaisesRegex(ValueError,'existing_identical'):
                fast.publish_config(store,{'example':'changed'},temporary)
            store.copy.assert_not_called()


if __name__=='__main__': unittest.main()
