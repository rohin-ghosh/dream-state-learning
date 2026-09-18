import ast
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from gpu import orch_r139_route_astra_handoff as handoff


def put(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document))


class BoundaryTests(unittest.TestCase):
    def test_future_experience_charge_rejected(self):
        self.assertFalse(handoff.no_future_charges([dict(kind='NATIVE', cycle=4)], 3, 3))

    def test_future_readout_charge_rejected(self):
        self.assertFalse(handoff.no_future_charges([dict(kind='NATIVE', sleep=4)], 3, 3))

    def test_same_cycle_readouts_allowed(self):
        self.assertTrue(handoff.no_future_charges([dict(kind='NATIVE', sleep=3), dict(kind='PARENT', cycle=3)], 3, 3))

    def test_only_uncharged_start_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root/'START.json', dict(cycle=4))
            plan = dict(adopt_start=handoff.ref(root/'START.json'))
            self.assertTrue(handoff.adoptable_start(root, plan))
            put(root/'CALL_000001.json', {})
            self.assertFalse(handoff.adoptable_start(root, plan))

    def test_adopt_start_requires_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root/'START.json', dict(cycle=4))
            plan = dict(adopt_start=handoff.ref(root/'START.json'))
            put(root/'START.json', dict(cycle=5))
            self.assertFalse(handoff.adoptable_start(root, plan))

    def test_parent_context_reconstructed_without_new_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root/'PENDING_TRIPLE.json', dict(intervention=dict(status='COMPLETE', parent_text='initial')))
            head = dict(status='BOUND_REQUESTED_SETTINGS', test='bound')
            for number in range(1, 4):
                identifier = str(number)
                put(root/'R121_PARENT_DELIVERY'/f'{identifier}.applied.json',
                    dict(id=identifier, status='COMPLETE', parent_text=f'parent{number}', head_settings=head))
                put(root/'cycle_0008'/f'CALL_{number:06d}.json',
                    dict(response={}, finished_unix=1, parent_delivery_ids=[identifier], head_settings=head))
            actual = handoff.reconstruct_context(root, 8, 8)
            self.assertEqual(actual['parent_history'], ['parent2', 'parent3'])
            self.assertEqual(actual['head_settings'], head)

    def test_head_state_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            put(root/'cycle_0008/CALL_000001.json',
                dict(response={}, finished_unix=1, parent_delivery_ids=[], head_settings={'unknown': True}))
            with self.assertRaisesRegex(ValueError, 'reconstructed_head_state_mismatch'):
                handoff.reconstruct_context(root, 8, 8)

    def test_frozen_resume_source_compiles(self):
        path = Path(__file__).resolve().parents[1]/'gpu/orch_r121_route_independent.py'
        source = path.read_text()
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
        text = ast.get_source_segment(source, function)
        transformed = handoff.resume_source(text)
        compile(transformed, '<test_resume>', 'exec')
        self.assertIn('R139_INDEPENDENT_ACTOR_READY', transformed)
        self.assertIn("optimizer.load_state_dict(state['optimizer'])", transformed)
        self.assertIn("engine.torch.cuda.set_rng_state_all(state['cuda_rng'])", transformed)
        self.assertIn('history.extend(rows)', transformed)

    def test_unknown_source_seam_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact_resume_source_seam'):
            handoff.resume_source('def run(root):\n    pass\n')

    def test_exclusive_receipt_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'receipt.json'
            handoff.write(path, {'first': True})
            with self.assertRaises(FileExistsError):
                handoff.write(path, {'first': False})
            self.assertEqual(handoff.read(path), {'first': True})


if __name__ == '__main__':
    unittest.main()
