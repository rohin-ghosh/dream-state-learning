import ast
import unittest
from unittest.mock import Mock

import preflight


class PreflightTests(unittest.TestCase):
    def test_remote_process_census_splits_actual_proc_nuls(self):
        assignment = next(node for node in ast.walk(ast.parse(preflight.REMOTE))
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'args' for target in node.targets))
        directory = Mock()
        directory.joinpath.return_value.read_bytes.return_value = b'python3\0-B\0p3_retry_parent.py\0'
        args = eval(compile(ast.Expression(assignment.value), 'remote_census_test', 'eval'), {'directory': directory})
        self.assertEqual(args, ['python3', '-B', 'p3_retry_parent.py'])


if __name__ == '__main__':
    unittest.main()
