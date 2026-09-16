import ast
import importlib.util
import os
from pathlib import Path
import hashlib
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('broker_repair',os.environ.get('R139_BROKER_FILE',str(REPO/'gpu/orch_r139_route_resume_broker.py')))
broker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker)


class BrokerTests(unittest.TestCase):
    def source(self):
        return Path(os.environ.get('R139_ORIGINAL_BROKER',REPO/'gpu/orch_r139_route_astra_broker.py')).read_text()

    def test_only_actual_attempt3_actor_receipt(self):
        result = broker.broker_source(self.source())
        ast.parse(result)
        self.assertNotIn('orch_r139_F1_astra_handoff_20260916_attempt2',result)
        self.assertNotIn('R139_INDEPENDENT_ACTOR_READY.json',result)
        self.assertEqual(result.count('R139B_INDEPENDENT_ACTOR_READY.json'),2)

    def test_exact_check_and_dispatch_both_rebound(self):
        result = broker.broker_source(self.source())
        self.assertIn("root/'R139B_INDEPENDENT_ACTOR_READY.json'",result)
        self.assertIn("Path(prior.ROOT)/'R139B_INDEPENDENT_ACTOR_READY.json'",result)
        self.assertIn("stage/'handoff.py'",result)

    def test_future_only_gate_unchanged(self):
        original = ast.parse(self.source())
        patched = ast.parse(broker.broker_source(self.source()))
        for name in ('gate','validate_consumer','saved_boundary_snapshot'):
            before = next(node for node in original.body if isinstance(node,ast.FunctionDef) and node.name==name)
            after = next(node for node in patched.body if isinstance(node,ast.FunctionDef) and node.name==name)
            self.assertEqual(ast.dump(before),ast.dump(after))

    def test_unknown_source_rejected(self):
        with self.assertRaises(ValueError):broker.broker_source('unknown')

    def test_json_reference_string_paths_are_hashable(self):
        source = broker.broker_source(self.source())
        line = next(line for line in source.splitlines() if line.startswith('digest=lambda'))
        namespace = dict(hashlib=hashlib, Path=Path)
        exec(line, namespace)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_bytes(b'{}')
            self.assertEqual(namespace['digest'](str(path)), hashlib.sha256(b'{}').hexdigest())
            self.assertEqual(namespace['digest'](path), namespace['digest'](str(path)))


if __name__=='__main__':
    unittest.main()
