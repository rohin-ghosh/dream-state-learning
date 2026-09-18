import ast
from pathlib import Path
import unittest

from c4_readmission import BOUNDARY_SHA, eligible, execute


class ReceivingReadmissionTests(unittest.TestCase):
    def test_once_marker_precedes_scan_and_native_dispatch(self):
        candidate = Path(__file__).with_name('c4_readmission_v2.py')
        source = candidate if candidate.exists() else Path(execute.__code__.co_filename)
        tree = ast.parse(source.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'execute')
        marker = next(node for node in ast.walk(function) if isinstance(node, ast.Call)
                      and ast.unparse(node) == "(attempt / 'DISPATCH_ONCE').mkdir()")
        scan = next(node for node in ast.walk(function) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == 'check_output')
        launch = next(node for node in ast.walk(function) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute) and node.func.attr == 'run')
        self.assertLess(marker.lineno, scan.lineno)
        self.assertLess(scan.lineno, launch.lineno)

    def inputs(self):
        return (dict(reason='original_privileged_clear_admission', retired=True, terminated=True),
                dict(clear=False, scanner_euid=0, blocking_reasons=['process_identity_drift:1590413']),
                dict(cycle=36, record=dict(sha256=BOUNDARY_SHA, kind='SLEEP_COMPLETE')), [], [])

    def test_exact_eligibility(self):
        eligible(*self.inputs())

    def test_any_native_dispatch_refuses(self):
        for name in ('LAUNCH.json', 'NATIVE.log', 'NATIVE_EXIT.json',
                     'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json'):
            with self.subTest(name=name):
                failure, admission, boundary, names, owners = self.inputs()
                with self.assertRaisesRegex(ValueError, 'no_prior_native'):
                    eligible(failure, admission, boundary, [name], owners)

    def test_boundary_identity(self):
        failure, admission, boundary, names, owners = self.inputs()
        boundary['record']['sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'same_sleep36'):
            eligible(failure, admission, boundary, names, owners)

    def test_other_blocker(self):
        failure, admission, boundary, names, owners = self.inputs()
        admission['blocking_reasons'].append('foreign_device_owner')
        with self.assertRaisesRegex(ValueError, 'exact_preserved'):
            eligible(failure, admission, boundary, names, owners)

    def test_live_owner(self):
        failure, admission, boundary, names, owners = self.inputs()
        with self.assertRaisesRegex(ValueError, 'owner_still_present'):
            eligible(failure, admission, boundary, names, ['actor'])


if __name__ == '__main__':
    unittest.main()
