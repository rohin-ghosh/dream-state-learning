import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


specification = importlib.util.spec_from_file_location('repair_tested', '/tmp/astra_additive_replay_collection_repair_20260913.py')
repair = importlib.util.module_from_spec(specification)
specification.loader.exec_module(repair)
candidate = repair.load_runner()
memory = candidate.runtime()


class RepairTests(unittest.TestCase):
    def test_actual_frozen_scorer_seam_and_inputs_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            call = dict(call_id='held0', panel='held', row_id='old-event')
            memory.write(root / 'calls.json', [call])
            response = dict(text='raw-child', finish_reason='stop', actual_prompt_token_ids=[1, 2], output_token_ids=[3], started=1, ended=2)
            output = root / 'run' / 'ADDITIVE_readout'
            output.mkdir(parents=True)
            memory.write(output / 'held0.response.json', response)
            row = dict(row_id='old-event')
            scorer = SimpleNamespace(score_row=Mock(return_value=dict(content_correct=True)))
            helper = SimpleNamespace(validate_score=Mock())
            bound = dict(material=dict(pair_data='not-a-scorer'), old_bound=dict(material=scorer), helper=helper,
                         retention=dict(evaluation=dict(held=[row], canary=[])))
            plan = dict(root=str(root))
            original_material = copy.deepcopy(bound['material'])
            with self.assertRaises(AttributeError):
                memory.score_calls(plan, bound, 'ADDITIVE')
            result = repair.score_cells(memory, plan, bound, ['ADDITIVE'])
            self.assertEqual(result['ADDITIVE']['held'][0]['raw'], 'raw-child')
            scorer.score_row.assert_called_once_with(row, 'raw-child', 'stop')
            helper.validate_score.assert_called_once_with(dict(content_correct=True), 'stop')
            self.assertEqual(bound['material'], original_material)
            self.assertEqual(memory.read(output / 'held0.response.json'), response)

    def test_missing_original_module_rejected(self):
        with self.assertRaises(ValueError):
            repair.score_cells(memory, {}, dict(material={}, old_bound=dict(material={})), ['ADDITIVE'])

    def fixture(self, directory):
        root = Path(directory) / 'root'
        root.mkdir()
        original = Path(str(root) + '_collected')
        original.mkdir()
        launcher = Path(str(root) + '.launcher')
        launcher.mkdir()
        memory.write(Path(str(root) + '.collection_claim.json'), dict(out=str(original), plan_sha256='plan', retry=False))
        memory.write(original / 'collection_failure.json', dict(error=repair.ERROR, error_type='AttributeError', retry=False, time=1))
        for name, value in (('controller_exit.json', 0), ('collector_exit.json', 1), ('exit.json', 1)):
            memory.write(launcher / name, dict(returncode=value))
        return root, original, launcher

    def test_exact_failed_attempt_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root, original, launcher = self.fixture(directory)
            result = repair.failed_collection(memory, root, 'plan')
            self.assertEqual(len(result), 5)
            memory.write(original / 'scores.json', {})
            with self.assertRaises(ValueError):
                repair.failed_collection(memory, root, 'plan')

    def test_native_failure_and_boolean_exit_rejected(self):
        for value in (1, False):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root, original, launcher = self.fixture(directory)
                (launcher / 'controller_exit.json').write_text(json.dumps(dict(returncode=value)))
                with self.assertRaises(ValueError):
                    repair.failed_collection(memory, root, 'plan')

    def test_unrelated_failure_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, original, launcher = self.fixture(directory)
            path = original / 'collection_failure.json'
            bad = memory.read(path)
            bad['error'] = 'unrelated failure'
            path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                repair.failed_collection(memory, root, 'plan')

    def test_source_has_no_process_or_original_collector_call(self):
        import ast
        tree = ast.parse(Path(repair.__file__).read_text())
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)}
        self.assertTrue({'Popen', 'worker', 'controller', 'collect', 'run_training'}.isdisjoint(attributes))


if __name__ == '__main__':
    unittest.main(verbosity=2)
