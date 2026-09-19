from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from prepare_epoch2 import HERE, check_inputs, checksum, delta, locate, plan_template, prepare, relative_name, seal_source


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = dict(source_root='/retained/source', root='/retained/identity', physical=0,
            hard_end_unix=1790791200, lease_end_unix=1790812800,
            startup_context=dict(path='/retained/source/context/BIRTH.txt', sha256='a' * 64),
            authorized_wall_extension=dict(previous_stream_sha256='b' * 64),
            rows=['unchanged'], prompt='same', control='same')
        self.staged = dict(life='curriculum_learner', old_guard_sha256='guard',
            old_source_pins={'gpu/one.py': 'old'}, new_source_pins={'gpu/one.py': 'new'},
            changed={'gpu/one.py': dict(before='old', after='new')}, journal_id='journal',
            journal_root='/actual/copy/stream', native={'pid': 1}, new_source='/immutable/epoch1/source')
        self.observation = dict(life=self.staged['life'], guard_sha256='guard',
            source_pins=self.staged['old_source_pins'], journal_id='journal',
            journal_root='/actual/copy/stream', native={'pid': 1}, plan=self.plan,
            guard_metadata=dict(copy_raw='/actual/copy'))

    def test_plan_template_preserves_every_semantic_field_and_deadline(self):
        original = deepcopy(self.plan)
        result = plan_template(self.plan, '/immutable/epoch2/source')
        self.assertEqual(self.plan, original)
        self.assertNotIn('authorized_wall_extension', result)
        self.assertEqual(result['startup_context']['path'], '/immutable/epoch2/source/context/BIRTH.txt')
        for key in ('hard_end_unix', 'lease_end_unix', 'rows', 'prompt', 'control', 'root', 'physical'):
            self.assertEqual(result[key], original[key])

    def test_source_paths_cannot_escape(self):
        for name in ('../outside.py', '/absolute.py', 'gpu/../outside.py', './gpu/test.py', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                relative_name(name)

    def test_exact_preimage_hash_not_filename_or_similar_variant(self):
        first = self.root / 'first/module.py'
        second = self.root / 'second/module.py'
        first.parent.mkdir()
        second.parent.mkdir()
        first.write_bytes(b'wrong')
        second.write_bytes(b'exact')
        result = locate({'gpu/module.py': checksum(b'exact')}, [first, second])
        self.assertEqual(result['gpu/module.py']['content'], b'exact')
        with self.assertRaisesRegex(ValueError, 'missing_exact_source_preimage'):
            locate({'gpu/module.py': checksum(b'missing')}, [first, second])

    def test_preimage_symlink_is_not_trusted(self):
        original = self.root / 'original.py'
        original.write_bytes(b'exact')
        link = self.root / 'module.py'
        link.symlink_to(original)
        with self.assertRaisesRegex(ValueError, 'missing_exact_source_preimage'):
            locate({'gpu/module.py': checksum(b'exact')}, [link])

    def test_delta_records_new_files_and_changes_exactly(self):
        self.assertEqual(delta({'same': 'a', 'changed': 'b'}, {'same': 'a', 'changed': 'c', 'added': 'd'}),
            {'added': dict(before=None, after='d'), 'changed': dict(before='b', after='c')})

    def test_inventory_preserves_actual_copy_raw_and_logical_identity(self):
        check_inputs(self.staged, self.observation)
        self.observation['guard_metadata']['copy_raw'] = '/wrong'
        with self.assertRaisesRegex(ValueError, 'actual_copy_raw_journal_mapping'):
            check_inputs(self.staged, self.observation)

    def test_epoch1_receipt_delta_or_native_drift_refuses(self):
        changed = deepcopy(self.staged)
        changed['changed'] = {}
        with self.assertRaisesRegex(ValueError, 'epoch1_exact_delta'):
            check_inputs(changed, self.observation)
        changed = deepcopy(self.staged)
        changed['native']['pid'] += 1
        with self.assertRaisesRegex(ValueError, 'same_inventory_and_epoch1_binding'):
            check_inputs(changed, self.observation)

    def test_no_overwrite_existing_output_or_write_outside_worker(self):
        for output in (self.root, Path('/tmp/pair_epoch2_not_owned')):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'new_local_worker_output_only'):
                prepare(output)

    def test_startup_path_cannot_be_replaced_with_unrelated_asset(self):
        self.plan['startup_context']['path'] = '/somewhere/else.txt'
        with self.assertRaises(ValueError):
            plan_template(self.plan, '/immutable/epoch2/source')

    def test_sealed_source_is_read_only_without_changing_content(self):
        source = self.root / 'source'
        source.mkdir()
        module = source / 'module.py'
        module.write_bytes(b'unchanged = True\n')
        before = module.read_bytes()
        seal_source(source)
        self.assertEqual(source.stat().st_mode & 0o777, 0o555)
        self.assertEqual(module.stat().st_mode & 0o777, 0o444)
        self.assertEqual(module.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
