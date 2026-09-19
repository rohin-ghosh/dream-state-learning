from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from gpu.orch_r144_node3_target_stage import HELPER, NATIVE, closure, relocate_plan, sha, sha_bytes, stage_lane


class TargetStageTests(unittest.TestCase):
    def test_only_source_and_startup_paths_move(self):
        plan = dict(source_root='/old/source', root='/life', hard_end_unix=123,
                    startup_context=dict(path='/old/source/context/STARTUP.md', sha256='same'),
                    birth_prompt='The source is /old/source', seed=7)
        original = deepcopy(plan)
        result = relocate_plan(plan, Path('/new/source'))
        self.assertEqual(plan, original)
        self.assertEqual(result['startup_context']['path'], '/new/source/context/STARTUP.md')
        self.assertEqual(result['birth_prompt'], original['birth_prompt'])
        self.assertEqual(result['root'], '/life')
        self.assertEqual(result['hard_end_unix'], 123)

    def test_startup_must_be_inside_original_source(self):
        with self.assertRaises(ValueError):
            relocate_plan(dict(source_root='/old', startup_context=dict(path='/foreign/x')), Path('/new'))

    def test_plan_without_startup(self):
        self.assertEqual(relocate_plan(dict(source_root='/old', seed=3), Path('/new')),
                         dict(source_root='/new', seed=3))

    def test_closure_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'original.py').write_text('VALUE = 1\n')
            (root / 'alias.py').symlink_to(root / 'original.py')
            with self.assertRaisesRegex(ValueError, 'source_symlink_rejected'):
                closure(root)

    def test_closure_hashes_all_python_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'original.py').write_text('VALUE = 1\n')
            (root / 'context.md').write_text('unchanged')
            self.assertEqual(list(closure(root)), ['original.py'])

    def test_read_only_original_copy_patched_without_original_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'original'
            (source / 'gpu').mkdir(parents=True)
            (source / NATIVE).write_text('ORIGINAL\n')
            (source / NATIVE).chmod(0o444)
            (source / 'gpu').chmod(0o555)
            (root / 'helper.py').write_text('POLICY = 1\n')
            (root / 'plan.json').write_text(json.dumps(dict(source_root=str(source), root='/life')))
            config = dict(attempt_dir='/old/control', source_pins=closure(source), resume=False)
            (root / 'guard.json').write_text(json.dumps(config))
            lane = dict(source_root=str(source), guard_path=str(root / 'guard.json'),
                guard_sha256=sha(root / 'guard.json'), source_pins=closure(source),
                patched_native_sha256=sha_bytes(b'PATCHED\n'), plan_path=str(root / 'plan.json'),
                physical=3, non_sleep_ast_sha256='same', recovery_guard_keys=[])
            with patch('gpu.orch_r144_node3_target_stage.patch_source', return_value='PATCHED\n'):
                result = stage_lane(lane, root / 'new', root / 'helper.py')
            self.assertEqual((source / NATIVE).read_text(), 'ORIGINAL\n')
            self.assertEqual((root / 'new/source' / NATIVE).read_text(), 'PATCHED\n')
            self.assertEqual((root / 'new/source' / HELPER).read_text(), 'POLICY = 1\n')
            self.assertEqual((root / 'new/source' / NATIVE).stat().st_mode & 0o777, 0o444)
            self.assertEqual((root / 'new/source/gpu').stat().st_mode & 0o777, 0o555)
            self.assertIsNone(result['effective_boundary'])


if __name__ == '__main__':
    unittest.main()
