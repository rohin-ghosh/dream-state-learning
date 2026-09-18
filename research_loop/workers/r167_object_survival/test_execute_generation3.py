import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('operator_r167', Path(__file__).with_name('execute_generation3.py'))
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


class OperatorTests(unittest.TestCase):
    def test_exact_full_schedule_no_score_selection(self):
        jobs = [dict(key=f'{milestone}_{condition}', physical=physical) for milestone in operator.ORDER
                for physical, condition in enumerate(('LORA_ON', 'LORA_OFF'))]
        for physical in (0, 1):
            selected = operator.jobs_for_slot(dict(jobs=jobs), physical)
            self.assertEqual(len(selected), 19)
            self.assertEqual([int(job['key'].split('_')[0]) for job in selected], [8, 25, *range(9, 25), 0])
        with self.assertRaises(AssertionError):
            operator.jobs_for_slot(dict(jobs=jobs[1:]), 0)

    def test_full_identity_release_required_before_next(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operation = root / 'control'
            job = dict(key='8_LORA_ON')
            directory = operation / 'launches' / job['key']
            attempt = root / 'attempts' / job['key']
            directory.mkdir(parents=True)
            (attempt / 'sealed').mkdir(parents=True)
            (root / 'ledger').mkdir()
            with patch.object(operator, 'ROOT', root), patch.object(operator, 'OPERATION', operation):
                sidecar = SimpleNamespace(gone=lambda identity: identity['gone'])
                self.assertFalse(operator.released_terminal(job, sidecar))
                operator.write(directory / 'DISPOSITION.json', dict(status='METADATA_ONLY'))
                operator.write(root / 'ledger' / '8_LORA_ON.COMPLETE.json', {})
                operator.write(directory / 'WRAPPER.json', dict(identity={'gone': True}))
                operator.write(attempt / 'LAUNCH.json', dict(identity={'gone': True}))
                operator.write(attempt / 'sealed' / 'PROCESS.json', dict(identity={'gone': True}))
                self.assertTrue(operator.released_terminal(job, sidecar))
                sidecar.gone = lambda identity: False
                self.assertFalse(operator.released_terminal(job, sidecar))


if __name__ == '__main__':
    unittest.main()
