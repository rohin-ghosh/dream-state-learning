from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from gpu import orch_math_feedback_uptake_r119_old_readmit as subject


class PremodelAdmissionTests(unittest.TestCase):
    def test_exact_departed_holder_no_native(self):
        with tempfile.TemporaryDirectory() as directory:
            report = dict(clear=False, blocking_reasons=['open_device_pid:123'],
                processes=[dict(pid=123, identity_consistent=True)])
            result = subject.proof(report, Path(directory), exists=lambda pid: False)
            self.assertTrue(result['old_report_not_cleared'])
            for mutate in ('live', 'additional', 'identity', 'native'):
                changed = deepcopy(report)
                if mutate == 'additional':
                    changed['blocking_reasons'].append('foreign_uuid')
                if mutate == 'identity':
                    changed['processes'][0]['identity_consistent'] = False
                if mutate == 'native':
                    (Path(directory) / 'LAUNCH.json').write_text('{}')
                with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                    subject.proof(changed, Path(directory), exists=lambda pid: mutate == 'live')


if __name__ == '__main__':
    unittest.main()
