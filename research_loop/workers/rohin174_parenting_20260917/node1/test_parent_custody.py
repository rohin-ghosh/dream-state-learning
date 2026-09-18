import copy
import os
import unittest
from unittest.mock import patch

from parent_custody import validate_owner, validate_pins


def fixture():
    parent = dict(pid=123, ticks='456', uid=os.getuid(), state='S', cwd='/source', argv_sha256='argv',
                  argv=['python3', '-B', '/repo/r169_parent_auth_refresh_20260917/refresh.py',
                        'serve', '--binding', '/repo/r169_parent_auth_refresh_20260917/parent_1/BINDING.json'])
    return dict(physical=2, old_parent=parent, old_parent_binding=dict(path=parent['argv'][-1]))


class CustodyTests(unittest.TestCase):
    def test_exact_parent_accepted(self):
        row = fixture()
        validate_owner(row, copy.deepcopy(row['old_parent']))

    def test_never_controls(self):
        for physical in (0, 1, 8):
            with self.subTest(physical=physical):
                row = fixture()
                row['physical'] = physical
                with self.assertRaisesRegex(ValueError, 'learning_parents_only'):
                    validate_owner(row, row['old_parent'])

    def test_pid_reuse_or_retarget_refused(self):
        for name, value in (('ticks', '789'), ('pid', 124), ('cwd', '/other'), ('argv_sha256', 'other')):
            with self.subTest(name=name):
                row = fixture()
                current = dict(row['old_parent'], **{name: value})
                with self.assertRaisesRegex(ValueError, 'exact_parent_owner'):
                    validate_owner(row, current)

    def test_native_entrypoint_refused(self):
        row = fixture()
        row['old_parent']['argv'][2] = 'gpu.orch_r125_continual_guard'
        with self.assertRaisesRegex(ValueError, 'r169_parent_only'):
            validate_owner(row, row['old_parent'])

    def test_different_binding_refused(self):
        row = fixture()
        row['old_parent_binding']['path'] = '/other/BINDING.json'
        with self.assertRaisesRegex(ValueError, 'binding_path'):
            validate_owner(row, row['old_parent'])

    def test_dead_parent_refused(self):
        row = fixture()
        current = dict(row['old_parent'], state='Z')
        with self.assertRaisesRegex(ValueError, 'live_parent_owner'):
            validate_owner(row, current)

    def test_admission_source_drift_refused(self):
        with patch('parent_custody.Reader.raw', return_value=b'changed'):
            with self.assertRaisesRegex(ValueError, 'admitted_parent_bytes'):
                validate_pins([dict(path='/source', sha256='0' * 64)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
