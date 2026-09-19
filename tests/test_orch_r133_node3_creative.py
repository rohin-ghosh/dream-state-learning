import ast
from copy import deepcopy
import inspect
from pathlib import Path
import unittest

from gpu import orch_r133_node3_creative as creative


class CreativeTests(unittest.TestCase):
    def setUp(self):
        self.base = ('### Your situation\nFactual orientation.\n### Learning and memory\nOld learning.\n'
                     '### Working with Rohin\nCollaborate.\n### Resources and initial orientation\nOld resources.')

    def test_only_assigned_device(self):
        self.assertEqual(creative.PHYSICAL, 1)
        self.assertEqual(creative.GPU_UUID, 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821')

    def test_exact_variant_and_seed(self):
        result = creative.variant_template({'seed': 17})
        self.assertEqual(result['seed'], 0)
        self.assertEqual(result['presleep_variant'], 'reread_select')
        self.assertEqual(result['compaction_invitation'], creative.native.PRESLEEP_INVITATIONS['reread_select'])

    def test_template_not_mutated(self):
        original = {'decoder': {'temperature': 0.7}, 'context_limit': 16384}
        before = deepcopy(original)
        result = creative.variant_template(original)
        result['decoder']['temperature'] = 0
        self.assertEqual(original, before)

    def test_resume_and_extension_rejected(self):
        for field in ('authorized_wall_extension', 'preupdate_recovery'):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'fresh_template_only'):
                creative.variant_template({field: {}})

    def test_factual_startup_matches_replay(self):
        text = creative.startup(self.base, '/source', '/workspace')
        for expected in ('reread_select', '16 times', '0.25', 'rank-8', '16,384', '512',
                         'physical1', '18:00 UTC', 'six-hour', 'Creative-writing seminar'):
            self.assertIn(expected, text)
        self.assertNotIn('Old learning', text)
        self.assertNotIn('Old resources', text)
        self.assertLess(len(text.encode()), 16384)

    def test_unknown_orientation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'known_R127_orientation'):
            creative.startup('unknown', '/source', '/workspace')

    def test_programme_distinct_style_and_async_cadence(self):
        self.assertIn('exploratory/editorial', creative.PROGRAMME)
        self.assertIn('two additional observed responses', creative.PROGRAMME)
        self.assertIn('No sealed evaluation', creative.PROGRAMME)

    def test_wrong_frozen_CPU_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, 'specified_frozen_CPU_receipt'):
            creative.verify_overlay('/unused', {'passed': True, 'tests': 495})

    def test_seed_precedes_adapter_creation(self):
        tree = ast.parse(inspect.getsource(creative.native))
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                      and node.name == 'initialize_adapter')
        calls = [(node.lineno, ast.unparse(node.func)) for node in ast.walk(method)
                 if isinstance(node, ast.Call)]
        seed = next(line for line, name in calls if name == 'self.seed_rng')
        lora = next(line for line, name in calls if name == 'peft.get_peft_model')
        self.assertLess(seed, lora)

    def test_stager_contains_no_launch_or_signal(self):
        tree = ast.parse(Path(creative.__file__).read_text())
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertFalse(calls & {'subprocess.run', 'subprocess.Popen', 'os.kill', 'os.killpg'})


if __name__ == '__main__':
    unittest.main()
