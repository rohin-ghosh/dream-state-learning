import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('resume_off', Path(__file__).with_name('resume_unused_off.py'))
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


class ResumeTests(unittest.TestCase):
    def test_only_unused_GO_keys(self):
        jobs = [dict(key=f'{milestone}_LORA_OFF', physical=1) for milestone in (8, 25, *range(9, 25), 0)]
        completed = {'8_LORA_OFF', '25_LORA_OFF'}
        selected = resume.remaining_jobs(dict(approved=jobs), completed, completed)
        self.assertEqual(len(selected), 17)
        self.assertEqual(selected[0]['key'], '9_LORA_OFF')
        with self.assertRaises(AssertionError):
            resume.remaining_jobs(dict(approved=jobs), completed, completed | {'9_LORA_OFF'})
        with self.assertRaises(AssertionError):
            resume.remaining_jobs(dict(approved=jobs), {'8_LORA_OFF'}, completed)

    def test_lookup_race_requires_fresh_absence(self):
        def missing(identity):
            raise ProcessLookupError()
        sidecar = SimpleNamespace(gone=missing)
        with patch.object(Path, 'exists', return_value=False):
            self.assertTrue(resume.gone(sidecar, {'pid': 987654}))
        with patch.object(Path, 'exists', return_value=True):
            self.assertFalse(resume.gone(sidecar, {'pid': 987654}))


if __name__ == '__main__':
    unittest.main()
