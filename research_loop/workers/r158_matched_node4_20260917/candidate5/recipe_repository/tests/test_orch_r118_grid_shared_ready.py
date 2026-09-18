from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_r118_grid_shared_ready as ready
from gpu import orch_r118_grid_shared_run as run


class ReadyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='r118_ready_test_')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root, self.source, self.old = (self.base / name for name in ('F4', 'source', 'old'))
        for path in (self.root, self.source, self.old):
            path.mkdir()
        for name in ready.SOURCE_FILES:
            path = self.source / name
            path.parent.mkdir(exist_ok=True)
            path.write_text('VALUE = 1\n')
        self.files = {name: ready.shared.sha(self.source / name) for name in ready.SOURCE_FILES}
        self.manifest = self.source / 'SOURCE_CLOSURE.json'
        ready.shared.write(self.manifest, dict(schema='R118_GRID_SHARED_SOURCE_CLOSURE_V1', root=str(self.source),
            entries=list(ready.SOURCE_FILES), files=self.files))
        self.tests = self.source / 'CPU_TESTS.json'
        ready.shared.write(self.tests, dict(source_files=self.files, passed=True, native_cpu=True,
            cuda_initialized=False, tests_failed=0, tests_skipped=0, tests_run=19,
            source_closure=dict(path=str(self.manifest), sha256=ready.shared.sha(self.manifest)),
            entrypoint=dict(module=run.MODULE, sha256=self.files['gpu/orch_r118_grid_shared_run.py'], help_exit_code=0)))
        (self.old / 'original.py').write_text('ORIGINAL = True\n')
        ready.shared.write(self.old / 'R115_SOURCE_SHA256.json', {'original.py': ready.shared.sha(self.old / 'original.py')})
        ready.shared.write(self.root / 'TRAIN.json', [dict(id='TRAIN' + str(index), split='TRAIN') for index in range(16)])
        ready.shared.write(self.root / 'DEV.json', [dict(id='DEV', split='DEV')])
        ready.shared.write(self.root / 'FINAL.json', [dict(id='FINAL', split='FINAL')])
        ready.shared.write(self.root / 'LEGACY_READOUT.json', dict(old_bank=[dict(event='old')], held=dict(cases=[dict(case_sha256='audit')])))
        self.config = dict(root=str(self.root), physical=3, life_id='F4_FABLE', base_sha256=run.grid.policy.game.BASE_SHA,
            hard_end_unix=run.grid.END, train_end_unix=run.grid.TRAIN_END,
            source_manifest_sha256=ready.shared.sha(self.old / 'R115_SOURCE_SHA256.json'),
            inputs={name: ready.shared.sha(self.root / name) for name in ('TRAIN.json', 'DEV.json', 'FINAL.json', 'LEGACY_READOUT.json')})
        ready.shared.write(self.root / 'CONFIG.json', self.config)
        (self.root / 'LEDGER.jsonl').write_text('existing immutable test ledger\n')
        ready.shared.write(self.root / 'CARRY.json', ['old own reflection'])

    def publish(self):
        return ready.publish(self.root, self.source, self.tests, predecessor_source=self.old)

    def change_tests(self, **fields):
        ready.shared.write(self.tests, dict(ready.shared.read(self.tests), **fields), replace=True)

    def test_v1_ready_without_common_initialization_or_live_mutations(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        with patch.object(run.client, 'prepare', side_effect=AssertionError('must not prepare common state')), patch.object(
                run.shared, 'initialize', side_effect=AssertionError('Main only')), patch.object(
                run.client, 'load_shared', side_effect=AssertionError('no GPU')):
            result = self.publish()
        self.assertEqual(result['schema'], 'R116_SHARED_CLIENT_READY_V1')
        self.assertEqual(result['branch'], 'F4')
        self.assertEqual(result['parent_wait_seconds'], 600)
        self.assertEqual(result['command_module'], run.MODULE)
        self.assertEqual(result['predecessor_plan_sha256'], ready.shared.sha(self.root / 'CONFIG.json'))
        self.assertEqual(result['excluded_ids'], ['AUDIT-audit', 'DEV', 'FINAL', 'OLD-old'])
        self.assertFalse(result['active_shared_client'])
        self.assertFalse(result['common_configuration_required_for_readiness'])
        self.assertTrue(result['ready_for_initialization'])
        for name, original in before.items():
            self.assertEqual((self.root / name).read_bytes(), original)
        self.assertEqual(set(path.name for path in self.root.iterdir()) - set(before), {'SHARED_CLIENT_READY.json'})

    def test_A4_remains_wait120(self):
        ready.shared.write(self.root / 'CONFIG.json', dict(self.config, physical=7, life_id='F4_ASTRA'), replace=True)
        result = self.publish()
        self.assertEqual(result['branch'], 'A4')
        self.assertEqual(result['inherited_bounds']['parent_wait_seconds'], 120)

    def test_no_overwrite_of_published_ready(self):
        self.publish()
        with self.assertRaisesRegex(ValueError, 'no_overwrite'):
            self.publish()

    def test_full_closure_missing_or_changed_file_rejected(self):
        path = self.source / ready.SOURCE_FILES[-1]
        path.write_text('VALUE = 2\n')
        with self.assertRaisesRegex(ValueError, 'closure_unchanged'):
            self.publish()

    def test_extra_unbound_source_rejected(self):
        (self.source / 'extra.py').write_text('EXTRA = True\n')
        with self.assertRaisesRegex(ValueError, 'closure_unchanged'):
            self.publish()

    def test_native_tests_must_all_pass_without_cuda_or_skips(self):
        original = ready.shared.read(self.tests)
        for field, value in (('passed', False), ('native_cpu', False), ('cuda_initialized', True),
                             ('tests_failed', 1), ('tests_skipped', 1), ('tests_run', 0)):
            ready.shared.write(self.tests, dict(original, **{field: value}), replace=True)
            with self.assertRaisesRegex(ValueError, 'bound_native_CPU'):
                self.publish()

    def test_executable_help_must_have_run_successfully(self):
        tests = ready.shared.read(self.tests)
        self.change_tests(entrypoint=dict(tests['entrypoint'], help_exit_code=1))
        with self.assertRaisesRegex(ValueError, 'executable_help'):
            self.publish()

    def test_original_input_and_source_remain_hash_bound(self):
        (self.root / 'TRAIN.json').write_text('[]')
        with self.assertRaisesRegex(ValueError, 'original_input'):
            self.publish()

    def test_held_overlap_rejected(self):
        ready.shared.write(self.root / 'DEV.json', [dict(id='TRAIN0', split='DEV')], replace=True)
        config = deepcopy(self.config)
        config['inputs']['DEV.json'] = ready.shared.sha(self.root / 'DEV.json')
        ready.shared.write(self.root / 'CONFIG.json', config, replace=True)
        with self.assertRaisesRegex(ValueError, 'held_excluded'):
            self.publish()

    def test_static_closure_follows_lazy_relative_and_package_imports(self):
        source = self.base / 'closure'
        (source / 'gpu').mkdir(parents=True)
        (source / 'gpu/__init__.py').write_text('')
        (source / 'gpu/main.py').write_text('from . import sibling\ndef later():\n    import gpu.lazy\n')
        (source / 'gpu/sibling.py').write_text('from gpu.lazy import VALUE\n')
        (source / 'gpu/lazy.py').write_text('VALUE = 1\n')
        closure = ready.source_closure(source, ['gpu/main.py'])
        self.assertEqual(set(closure), {'gpu/__init__.py', 'gpu/main.py', 'gpu/sibling.py', 'gpu/lazy.py'})

    def test_activation_contract_has_boundary_and_all_eight_requirement(self):
        result = self.publish()
        self.assertEqual(result['activation_sidecar'], 'SHARED_ACTIVATION.json')
        self.assertIn('all_eight_ready_and_safe', result['activation_fields'])
        self.assertIn('predecessor_identities', result['activation_fields'])
        self.assertIn('boundary', result['activation_fields'])
        self.assertIn('adoption_sha256', result['activation_binding_fields'])
        self.assertIn('SHARED_TERMINAL.json', result['broker_transition_note'])


if __name__ == '__main__':
    unittest.main()
