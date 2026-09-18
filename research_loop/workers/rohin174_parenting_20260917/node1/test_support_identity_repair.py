import ast
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import support_identity_repair as repair


ROOT = Path(__file__).resolve().parents[4]


def functions(source):
    tree = ast.parse(source)
    return ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef)], type_ignores=[])


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class IdentityRepairTests(unittest.TestCase):
    def setUp(self):
        self.before = dict(pid=42, uid=0, start_ticks='123', boot_id='boot', command_sha256='old', state='S')
        self.after = dict(self.before, command_sha256='new', state='R')
        self.scanner = repair.patch(repair.SCANNER, (ROOT / repair.SCANNER).read_text())
        self.minor = repair.patch(repair.MINOR, (ROOT / repair.MINOR).read_text())
        self.namespace = {}
        exec(compile(repair.IDENTITY_HELPER, '<actual-repair-helper>', 'exec'), self.namespace)

    def test_mutable_state_and_title_are_not_identity(self):
        self.assertTrue(self.namespace['same_process_identity'](self.before, self.after))

    def test_missing_or_changed_kernel_identity_rejected(self):
        for key in ('pid', 'uid', 'start_ticks', 'boot_id'):
            for missing in (False, True):
                with self.subTest(key=key, missing=missing):
                    changed = dict(self.after)
                    if missing:
                        del changed[key]
                    else:
                        changed[key] = 'different'
                    self.assertFalse(self.namespace['same_process_identity'](self.before, changed))

    def test_actual_full_scanner_preserves_foreign_blockers(self):
        identity = {key: value for key, value in self.after.items() if key != 'state'}
        before = {key: value for key, value in self.before.items() if key != 'state'}
        service = SimpleNamespace(read_text=lambda: json.dumps(dict(identity, pid=100)))
        proc = SimpleNamespace(glob=lambda pattern: [Path('/proc/42')])
        calls = []

        def sample(directory):
            if directory.name == '100':
                return dict(identity, pid=100)
            calls.append(True)
            return dict(before if len(calls) == 1 else identity)

        namespace = dict(json=json, os=SimpleNamespace(geteuid=lambda: 0),
            Path=lambda path: proc if path == '/proc' and not calls else Path(path),
            policy=SimpleNamespace(allocation=lambda index: None, HOST_SHA='host',
                DEVICES={7: 'GPU-owned'}, require=require),
            existing=SimpleNamespace(scan=lambda *args: dict(clear=False,
                blocking_reasons=['open_device_pid:99'], processes=[dict(self.after)])))
        exec(compile(functions(self.scanner), '<actual-patched-scanner>', 'exec'), namespace)
        namespace.update(identity=sample, host_identity=lambda: 'host', sha=lambda path: 'hash', __file__='scanner')
        namespace['existing'].__file__ = 'existing'
        report = namespace['scan'](7, service)
        self.assertEqual(report['blocking_reasons'], ['open_device_pid:99'])
        self.assertFalse(report['clear'])
        self.assertEqual(report['processes'][0]['pinned_identity']['command_sha256'], 'new')

    def test_gpu_fd_visibility_reservation_checks_unchanged(self):
        for source in ((ROOT / repair.MINOR).read_text(), self.minor):
            self.assertIn("opened |= os.readlink(descriptor) == target_device", source)
            self.assertIn("issues.append('open_device_pid:' + directory.name)", source)
            self.assertIn("issues.append('unknown_minor_process_visibility:'", source)
            self.assertIn("issues.append('kernel_uuid_minor_changed')", source)
        for source in ((ROOT / repair.SCANNER).read_text(), self.scanner):
            self.assertIn("issues.append('uuid_reservation:' + str(process_id))", source)
            self.assertIn("issues = list(snapshot['blocking_reasons'])", source)

    def test_only_scanner_comparisons_change(self):
        for relative, patched in ((repair.SCANNER, self.scanner), (repair.MINOR, self.minor)):
            before = ast.parse((ROOT / relative).read_text())
            after = ast.parse(patched)
            for node in before.body:
                if isinstance(node, ast.FunctionDef) and node.name != 'scan':
                    equivalent = next(item for item in after.body if isinstance(item, ast.FunctionDef) and item.name == node.name)
                    self.assertEqual(ast.dump(node), ast.dump(equivalent))

    def test_repeated_patch_rejected(self):
        for relative, source in ((repair.SCANNER, self.scanner), (repair.MINOR, self.minor)):
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                repair.patch(relative, source)


if __name__ == '__main__':
    unittest.main()
