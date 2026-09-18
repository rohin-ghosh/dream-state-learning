import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import tarfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('receiver', HERE / 'r188_receive.py')
receiver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(receiver)


class ReceiverTests(unittest.TestCase):
    def test_exact_scope_and_preserved_plan(self):
        original = dict(source_root='/old/source', root='/logical/root', physical=3,
            gpu_uuid='old', hard_end_unix=10, lease_end_unix=20, new_presentations=16,
            rehearsal_presentations=0, segment_tokens=512, decoder={'test': 'unchanged'},
            startup_context=dict(path='/old/source/STARTUP.md', sha256='same', version='same'))
        saved = dict(sha256='a' * 64, state=dict(pending=None, sleep_frontier=1, rows=[{}], deadline_unix=10))
        lease = dict(hard_end_unix=100, lease_end_unix=300, safety_margin_seconds=200)
        for physical, target in receiver.TARGETS.items():
            with self.subTest(physical=physical):
                result = receiver.bind_plan(original, Path('/new/source'), saved, lease, physical)
                self.assertEqual(result['physical'], target)
                self.assertEqual(result['root'], original['root'])
                self.assertEqual(result['segment_tokens'], 512)
                self.assertEqual(result['decoder'], original['decoder'])
                self.assertEqual(result['authorized_wall_extension']['previous_stream_sha256'], 'a' * 64)
        for physical in (1, 4, 5, 6, 7):
            with self.assertRaises(ValueError):
                receiver.bind_plan(original, Path('/new'), saved, lease, physical)
        pending = deepcopy(saved)
        pending['state']['pending'] = 'sleep:test'
        with self.assertRaises(ValueError):
            receiver.bind_plan(original, Path('/new'), pending, lease, 0)

    def test_containment_keeps_reviewed_guard_and_device_checks(self):
        reference = (HERE.parents[3] / 'gpu/orch_r137_node4_containment.py').read_text()
        result = receiver.containment(reference)
        originals = {node.name: node for node in ast.parse(reference).body if isinstance(node, ast.FunctionDef)}
        changed = {node.name: node for node in ast.parse(result).body if isinstance(node, ast.FunctionDef)}
        for name in ('verify_device_containment', 'device_containment_command', 'device_minor',
                'contained_native', 'scan', 'require_host'):
            self.assertEqual(ast.dump(originals[name]), ast.dump(changed[name]), name)
        self.assertIn(receiver.MODULE, result)
        with self.assertRaises(ValueError):
            receiver.containment(reference + '\n')

    def test_archive_rejects_escape_device_and_external_link(self):
        class Archive:
            def __init__(self, member):
                self.member = member

            def getmembers(self):
                return [self.member]

        safe = tarfile.TarInfo('physical0/root/checkpoint')
        receiver.safe_members(Archive(safe), 'physical0/')
        root = tarfile.TarInfo('physical0')
        root.type = tarfile.DIRTYPE
        receiver.safe_members(Archive(root), 'physical0/')
        for name, kind, link in [('physical0/../escape', tarfile.REGTYPE, ''),
                ('/absolute', tarfile.REGTYPE, ''), ('physical0/device', tarfile.CHRTYPE, ''),
                ('physical0/link', tarfile.LNKTYPE, 'physical3/root'),
                ('physical0/link', tarfile.SYMTYPE, 'root')]:
            member = tarfile.TarInfo(name)
            member.type, member.linkname = kind, link
            with self.subTest(name=name, kind=kind), self.assertRaises(ValueError):
                receiver.safe_members(Archive(member), 'physical0/')


if __name__ == '__main__':
    unittest.main()
