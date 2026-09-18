import ast
from datetime import datetime, timezone
from pathlib import Path
import unittest

from gpu import orch_math_feedback_uptake_node5_prepare as preparation


class Node5PreparationTests(unittest.TestCase):
    def setUp(self):
        self.plan = preparation.make_plan(Path(__file__).resolve().parents[1])

    def test_unknown_native_identity_never_becomes_ready(self):
        self.assertFalse(self.plan['launch_ready'])
        self.assertFalse(self.plan['trust_bypass'])
        self.assertIsNone(self.plan['host_sha256'])
        self.assertEqual([lane['physical'] for lane in self.plan['lanes']], [2, 3])
        self.assertTrue(all(lane['uuid'] is None and lane['kernel_minor'] is None for lane in self.plan['lanes']))
        self.assertEqual((self.plan['native_calls'], self.plan['parent_calls']), (0, 0))

    def test_explicit_new_caps_and_unchanged_hard_end(self):
        self.assertEqual(self.plan['additional_native_cap'], 3072)
        self.assertEqual(self.plan['additional_parent_cap'], 1056)
        self.assertEqual(self.plan['additional_gpu_hours'], 16)
        self.assertEqual(self.plan['hard_deadline_unix'], datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc).timestamp())
        self.assertLessEqual(self.plan['hard_deadline_unix'], self.plan['lease_end_unix'] - 21600)
        self.assertEqual(self.plan['hard_deadline_unix'] - self.plan['native_deadline_unix'], 180)

    def test_no_connections_or_model_calls_in_preparation(self):
        tree = ast.parse(Path(preparation.__file__).read_text())
        imports = {item.name for node in ast.walk(tree) if isinstance(node, ast.Import) for item in node.names}
        self.assertFalse(imports & {'subprocess', 'socket', 'paramiko', 'torch', 'transformers'})
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {'generate', 'Popen', 'connect', 'from_pretrained', 'system'})

    def test_reuses_exact_principles_and_does_not_block_originals(self):
        self.assertEqual(self.plan['principles_sha256'], 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d')
        self.assertEqual(len(self.plan['reused_source_hashes']), 5)
        self.assertTrue(self.plan['original_lanes_unchanged'])
        self.assertTrue(self.plan['original_lanes_do_not_wait_for_node5'])
        self.assertIsNone(self.plan['optimizer'])
        self.assertEqual(self.plan['new_baseline_controls'], 0)


if __name__ == '__main__':
    unittest.main()
