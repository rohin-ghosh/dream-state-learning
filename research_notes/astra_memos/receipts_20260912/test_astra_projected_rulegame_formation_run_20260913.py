"""CPU-only projected runtime checks; original fixtures are reused, never edited."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path(os.environ.get('ASTRA_SOURCE_ROOT', '/data/home/rohing/dream-state'))
if not SOURCE.is_absolute():
    raise ValueError('ASTRA_SOURCE_ROOT must be absolute')
SOURCE = SOURCE.resolve(strict=True)
sys.path[:0] = [str(SOURCE), '/tmp']
DRIVER = Path('/tmp/astra_projected_rulegame_formation_run_20260913.py')
FINAL_ROLE_SHA = '2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945'
FINAL_PROJECTION_SHA = '47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19'


def load(name, filename):
    specification = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


legacy = load('projected_original_runtime_tests', '/tmp/test_astra_born_rulegame_formation_run_20260912.py')
run = load('projected_runtime_under_test', DRIVER)
legacy.run, legacy.DRIVER, legacy.SOURCE = run, DRIVER, SOURCE
LOADED_DRIVER_SHA = run.digest(DRIVER)


def receipt_for(normalized):
    return dict(status='PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING', repository='Qwen/Qwen2.5-7B-Instruct',
                revision='a09a35458c702b33eeacc393d103063234e8bc28',
                model=normalized['pin']['child_identity']['model_input'], file_count=14,
                files={name: {'sha256': pin} for name, pin in normalized['pin']['model_files'].items()})


class PublicBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='projected_public_binding_cpu_')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.filename = self.directory/'public_receipt.json'
        self.normalized = dict(pin=dict(child_identity={'model_input': str(self.directory/'model')},
            model_files={f'file-{index:02d}.json': hashlib.sha256(f'fixture-{index}'.encode()).hexdigest() for index in range(14)}))
        self.receipt = receipt_for(self.normalized)
        self.seal(self.receipt)
        self.location = patch.object(run, 'PUBLIC_RECEIPT', self.filename)
        self.location.start()
        self.addCleanup(self.location.stop)

    def seal(self, receipt):
        self.filename.write_text(json.dumps(receipt, sort_keys=True, allow_nan=False))
        self.expected = run.digest(self.filename)

    def bind(self, normalized=None):
        with patch.object(run, 'PUBLIC_SHA', self.expected):
            return run.public_binding(normalized or self.normalized)

    def test_real_public_binding_accepts_exact_fourteen_file_map(self):
        result = self.bind()
        self.assertEqual(result['receipt'], self.receipt)
        self.assertEqual(result['receipt_sha256'], self.expected)
        self.assertTrue(result['historical_labels_preserved'])
        self.assertFalse(result['clean_ancestry_claim'])

    def test_public_receipt_byte_change_rejected_before_content(self):
        self.filename.write_bytes(self.filename.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            self.bind()

    def test_pinned_wrong_public_repository_revision_status_or_model_rejected(self):
        for field, value in (('repository', 'other/model'), ('revision', '0'*40), ('status', 'PENDING'), ('model', '/different')):
            with self.subTest(field=field):
                self.seal(dict(self.receipt, **{field: value}))
                with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                    self.bind()

    def test_missing_extra_wrong_count_and_file_hash_rejected(self):
        variants = []
        missing = deepcopy(self.receipt)
        missing['files'].pop('file-00.json')
        variants.append(missing)
        extra = deepcopy(self.receipt)
        extra['files']['extra.json'] = {'sha256': '0'*64}
        variants.extend((extra, dict(self.receipt, file_count=13)))
        changed = deepcopy(self.receipt)
        changed['files']['file-00.json']['sha256'] = '0'*64
        variants.append(changed)
        for index, receipt in enumerate(variants):
            with self.subTest(index=index):
                self.seal(receipt)
                with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                    self.bind()

    def test_normalized_model_map_and_local_path_must_join_receipt(self):
        for field in ('model_files', 'child_identity'):
            normalized = deepcopy(self.normalized)
            normalized['pin'][field] = {} if field == 'model_files' else {'model_input': '/different'}
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.bind(normalized)

    def test_missing_public_receipt_rejected(self):
        self.filename.unlink()
        with self.assertRaises(FileNotFoundError):
            self.bind()


class FormationTests(legacy.FormationTests):
    @classmethod
    def setUpClass(cls):
        if run.ROLE_SHA != FINAL_ROLE_SHA or run.digest(SOURCE/'organism_v6/born_rulegame_formation.py') != FINAL_ROLE_SHA:
            raise RuntimeError('Main-authorized final role pin changed; source-dependent acceptance withheld')
        if run.digest(SOURCE/'organism_v6/rulegame_action_projection.py') != FINAL_PROJECTION_SHA:
            raise RuntimeError('Main-authorized projection pin changed')
        super().setUpClass()

    def setUp(self):
        original_setup = legacy.frozen_tests.PipelineTests.setUp
        def model_with_fourteen_files(fixture):
            original_setup(fixture)
            for index in range(11):
                run.write_json(fixture.model/f'public_fixture_{index:02d}.json', {'CPU_ONLY': index})
        with patch.object(legacy.frozen_tests.PipelineTests, 'setUp', model_with_fourteen_files):
            super().setUp()
        self.public_receipt = self.rootdir/'public_receipt.json'
        self.assertEqual(len(self.normalized['pin']['model_files']), 14)
        run.write_json(self.public_receipt, receipt_for(self.normalized))
        self.stack.enter_context(patch.object(run, 'PUBLIC_RECEIPT', self.public_receipt))
        self.stack.enter_context(patch.object(run, 'PUBLIC_SHA', run.digest(self.public_receipt)))

    def prepare(self, child_mode='AUTH', **kwargs):
        root = self.rootdir/('formation' if child_mode == 'AUTH' else 'formation_OFF')
        prepared = run.prepare(SOURCE, run.ROLE_SHA, self.upstream_root, self.upstream_pin,
            self.upstream_release['validation'], self.upstream_release['validation_sha256'],
            root, '2', self.fixture.deadline, self.fixture.lease, child_mode=child_mode, **kwargs)
        return root, prepared['plan_sha256'], run.read(root/'plan.json')

    def test_wrong_or_missing_role_source_preserves_failed_prepare(self):
        with self.assertRaises(ValueError):
            run.prepare(SOURCE, '0'*64, self.upstream_root, self.upstream_pin, self.upstream_release['validation'],
                self.upstream_release['validation_sha256'], self.rootdir/'bad', '2', self.fixture.deadline,
                self.fixture.lease, child_mode='AUTH')
        self.assertTrue((self.rootdir/'bad/prepare_failure.json').exists())
        with self.assertRaises(FileNotFoundError):
            run.source_api(self.rootdir, run.ROLE_SHA)

    def test_auth_off_same_birth_and_requests_with_correct_routes(self):
        captures = {}
        plans = {}
        for mode in ('AUTH', 'OFF'):
            root, pin, plan = self.prepare(mode)
            run.checked_plan(root, pin)
            captures[mode], receipt = self.capture(root, pin, plan)
            plans[mode] = plan
            self.assertEqual(plan['interface'], self.role.projection.INTERFACE)
            self.assertEqual(plan['binding']['child_mode'], mode)
            self.assertIn(str(SOURCE/'organism_v6/rulegame_action_projection.py'), plan['source_hashes'])
            for row in captures[mode]['calls']:
                off = mode == 'OFF' or row['request']['role'] == 'parent'
                self.assertEqual(row['envelope']['lora_request'] is None, off)
                if off:
                    self.assertIsNone(row['identity']['adapter_input'])
                    self.assertEqual(row['identity']['adapter_files'], {})
            self.assertFalse(receipt['retained_learning'])
        self.assertEqual(plans['AUTH']['normalized'], plans['OFF']['normalized'])
        self.assertEqual(plans['AUTH']['public_model_binding'], plans['OFF']['public_model_binding'])
        self.assertEqual([row['request'] for row in captures['AUTH']['calls']], [row['request'] for row in captures['OFF']['calls']])
        self.assertNotEqual(plans['AUTH']['binding_sha256'], plans['OFF']['binding_sha256'])

    def test_off_capture_collection_and_release(self):
        root, pin, plan = self.prepare('OFF')
        self.capture(root, pin, plan)
        collected = run.collect(**self.launch(root, pin, plan))
        released = run.verified_release(root, pin, collected['validation'], collected['validation_sha256'])
        self.assertEqual(released['binding']['child_mode'], 'OFF')
        self.assertTrue(released['release']['phase_complete'])

    def test_resealed_mode_interface_or_public_binding_mismatch_rejected(self):
        root, pin, plan = self.prepare()
        variants = [dict(plan, child_mode='OFF', child='OFF'), dict(plan, interface='interaction_v3')]
        changed = deepcopy(plan)
        changed['public_model_binding']['clean_ancestry_claim'] = True
        variants.append(changed)
        for index, changed in enumerate(variants):
            with self.subTest(index=index):
                (root/'plan.json').write_text(json.dumps(changed, sort_keys=True, allow_nan=False))
                changed_pin = run.digest(root/'plan.json')
                (root/'plan.sha256.json').write_text(json.dumps({'sha256': changed_pin}))
                with self.assertRaises(ValueError):
                    run.checked_plan(root, changed_pin)

    def test_public_receipt_drift_rejected_after_prepare(self):
        root, pin, plan = self.prepare()
        self.public_receipt.write_bytes(self.public_receipt.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            run.read_plan(root, pin)

    def test_invalid_mode_rejected_before_output_creation(self):
        with self.assertRaisesRegex(ValueError, 'child mode'):
            self.prepare('DERANGED')
        self.assertFalse((self.rootdir/'formation_OFF').exists())

    def test_controller_cap_cannot_be_extended(self):
        with self.assertRaises(ValueError):
            self.prepare(controller_seconds=901)
        self.assertTrue((self.rootdir/'formation/prepare_failure.json').exists())


class CLITests(legacy.CLITests):
    def test_prepare_dispatch(self):
        values = dict(source='/source', role_sha256='role', fit_root='/fit', fit_plan_sha256='fitpin', fit_release='/released',
            fit_release_sha256='releasepin', out='/out', device='2', deadline='end', lease_end='lease', child_mode='OFF')
        arguments = ['prepare']+[value for key, content in values.items() for value in ('--'+key.replace('_', '-'), content)]
        self.dispatch(arguments, 'prepare', dict(values, controller_seconds=900))


if __name__ == '__main__':
    print('CPU-only projected driver SHA256:', LOADED_DRIVER_SHA, flush=True)
    unittest.main(verbosity=2)
