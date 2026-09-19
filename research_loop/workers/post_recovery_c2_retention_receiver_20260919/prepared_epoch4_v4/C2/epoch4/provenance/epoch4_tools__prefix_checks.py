"""Isolated exact-source v4 prefix and C2 admission tests; never live evidence."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from manifest_checks import verify


TOOLS = Path(__file__).resolve().parent


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


context_cases = load('pinned_context_cases', TOOLS / 'context_cases.py')
cases = context_cases.legacy


class C2Cases(context_cases.ConsumerContextTests):
    def context(self, *, different=True):
        self.complete()
        self.produce()
        self.approve(self.proof, consumer_context_mode=self.helper.CROSS_NAMESPACE)
        self.admission_path = self.directory / 'admitted_CPU.json'
        self.admission_path.write_bytes(self.helper.encoded(dict(c2_prefix_context=
            self.helper.admission_clause(self.guard, self.authority))))
        self.admission = dict(path=str(self.admission_path), sha256=cases.raw_sha(self.admission_path),
            field_path=['c2_prefix_context'])
        consumer = deepcopy(self.proof['binding']['environment'])
        if different:
            consumer['mount_namespace']['ino'] += 1
        return consumer

    def cross_scan(self):
        return self.tail.scan(self.journal, self.selection, prefix_proof=self.authority,
            prefix_admission=self.admission)

    def chain(self):
        from gpu import c2_prefix_authority as api
        self.api = api
        self.plan = dict(physical=1, hard_end_unix=1789927200,
            gpu_uuid='GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c',
            think_act_learn=dict(trial_id='C2_R216_current_conversation_maintenance'),
            source_root=str(cases.SOURCE), root=str(self.directory))
        self.journal.close()
        self.root.rename(self.directory / 'stream')
        self.root = self.directory / 'stream'
        self.journal = self.base(self.root)
        self.addCleanup(self.journal.close)
        self.source['epoch'] = self.save('epoch', dict(schema='C2_PREFIX_SOURCE_EPOCH_V1', epoch_id='test-C2',
            source_root=str(cases.SOURCE), source_pins_sha256=api.digest(self.source['pins']), deadline_unix=1789927200))
        self.complete()
        self.produce()
        self.config = dict(copy_raw=self.plan['root'], resume=True, source_pins=self.source['pins'],
            plan_sha256='a' * 64, allocation_path='', allocation_sha256='')
        approved = dict(schema='C2_PREFIX_OPERATOR_AUTHORITY_V1', status='MAIN_APPROVED_IMMUTABLE_PREFIX',
            epoch_id='test-C2', life_binding_sha256='b' * 64, deadline_unix=1789927200, physical=1,
            source=self.source, proof=api.reference(self.proof_path), producer=api.reference(TOOLS / 'prefix_cli.py'),
            producer_receipt=self.save('producer', dict(status='CANDIDATE_NOT_AUTHORIZATION',
                proof_path=str(self.proof_path), proof_sha256=cases.raw_sha(self.proof_path),
                journal_writes=0, writer_lock_acquired=False)),
            selection_policy={key: value for key, value in self.selection.items()
                if key not in ('complete_index', 'complete_sha256')},
            max_advance_records=100, max_advance_bytes=10485760,
            confinement_sha256=api.confinement_digest(self.config),
            consumer_context_mode=api.CROSS, bounded_context_clause_derivation=True)
        self.approved = self.save('Main_authority', approved)
        selected = api.selection_guard(self.approved, self.plan, self.source['pins'], self.selection)
        self.binding = dict(schema='C2_PREFIX_SELECTION_BINDING_V1', authority=self.approved,
            selection_guard=self.save('selection_guard', selected), selection_sha256=api.digest(self.selection))
        original_cpu = dict(passed=True, source_pins=self.source['pins'], c2_prefix_authority=self.approved)
        self.cpu = api.receiving_cpu(original_cpu, self.approved, self.plan, self.source['pins'], self.selection, self.binding)
        self.cpu_ref = self.save('receiving_CPU', self.cpu)
        allocation = self.save('allocation', dict(plan_sha256=self.config['plan_sha256'],
            cpu_receipt_path=self.cpu_ref['path'], cpu_receipt_sha256=self.cpu_ref['sha256']))
        self.config.update(allocation_path=allocation['path'], allocation_sha256=allocation['sha256'])
        self.guard_ref = self.save('original_guard', self.config)
        self.token = dict(life_binding_sha256='b' * 64, epoch_id='test-C2', new_source_pins=self.source['pins'],
            deadline_unix=1789927200, receiver=dict(prefix_binding=self.binding, guard_path=self.guard_ref['path'],
                artifact_pins={self.guard_ref['path']: self.guard_ref['sha256']}))

    def save(self, name, document):
        path = self.directory / (name + '.json')
        path.write_bytes(self.helper.encoded(document))
        return dict(path=str(path), sha256=cases.raw_sha(path))

    def admitted(self):
        return self.api.admitted_prefix(self.config, self.plan, guard_path=self.guard_ref['path'])

    def arguments(self):
        return self.api.reader_arguments(self.plan, self.token, self.selection)

    def test_c2_explicit_cross_namespace_full_state_parity(self):
        consumer = self.context()
        expected = self.tail.scan(self.journal, self.selection)
        with patch.object(self.helper, 'environment', return_value=consumer):
            actual = self.cross_scan()
        self.assertEqual(self.helper.encoded(actual), self.helper.encoded(expected))
        context = self.journal.checkpoint_tail_receipt['prefix_proof']['consumer_context']
        self.assertEqual(context['consumer_environment'], consumer)
        self.assertNotEqual(context['producer_environment'], consumer)

    def test_c2_cross_requires_independent_exact_clause(self):
        consumer = self.context()
        with patch.object(self.helper, 'environment', return_value=consumer):
            self.reject(lambda: self.scan())
            self.admission['sha256'] = '0' * 64
            self.reject(self.cross_scan)

    def test_c2_cross_rejects_different_boot(self):
        consumer = self.context()
        consumer['boot_id'] = 'different-boot'
        with patch.object(self.helper, 'environment', return_value=consumer):
            self.reject(self.cross_scan, 'same_kernel_boot')

    def test_c2_cross_rejects_identical_byte_cloned_journal(self):
        consumer = self.context()
        self.journal.close()
        moved = self.directory / 'old-journal'
        self.root.rename(moved)
        shutil.copytree(moved, self.root)
        self.journal = self.base(self.root)
        self.addCleanup(self.journal.close)
        with patch.object(self.helper, 'environment', return_value=consumer):
            self.reject(self.cross_scan)

    def test_c2_cross_rechecks_every_intent_identity(self):
        consumer = self.context()
        path = self.file(intent=True)
        raw = path.read_bytes()
        path.unlink()
        path.write_bytes(raw)
        with patch.object(self.helper, 'environment', return_value=consumer):
            self.reject(self.cross_scan)

    def test_c2_cross_rechecks_immutable_source_directory(self):
        consumer = self.context()
        path = cases.SOURCE / 'gpu/temporary-non-source'
        path.touch()
        path.unlink()
        with patch.object(self.helper, 'environment', return_value=consumer):
            self.reject(self.cross_scan, 'directory_metadata_changed')

    def test_c2_same_namespace_default_unchanged(self):
        self.complete()
        self.produce()
        self.assertEqual(self.guard['consumer_context_mode'], self.helper.SAME_NAMESPACE)
        self.assertEqual(self.scan(), self.tail.scan(self.journal, self.selection))

    def test_c2_original_chain_allows_exact_bounded_clause(self):
        self.chain()
        with self.admitted():
            arguments = self.arguments()
            self.assertEqual(arguments['prefix_admission'], dict(self.cpu_ref, field_path=['c2_prefix_context']))
            consumer = deepcopy(self.proof['binding']['environment'])
            consumer['mount_namespace']['ino'] += 1
            with patch.object(self.helper, 'environment', return_value=consumer):
                self.tail.scan(self.journal, self.selection, **arguments)

    def test_c2_unadmitted_token_cannot_choose_mode(self):
        self.chain()
        self.reject(self.arguments, 'original_validated_admission_context')

    def test_c2_stripped_binding_has_no_slow_fallback(self):
        self.chain()
        self.token['receiver'].pop('prefix_binding')
        with self.admitted():
            self.reject(self.arguments, 'no_implicit_full_prefix_fallback')

    def test_c2_allocation_changed_during_consumption_refused(self):
        self.chain()
        with self.admitted():
            Path(self.config['allocation_path']).write_text('{}')
            self.reject(self.arguments, 'exact_unchanged_reference_bytes')

    def test_c2_CPU_changed_during_consumption_refused(self):
        self.chain()
        with self.admitted():
            Path(self.cpu_ref['path']).write_text('{}')
            self.reject(self.arguments, 'exact_unchanged_reference_bytes')

    def test_c2_copy_raw_deviation_refused(self):
        self.chain()
        self.config['copy_raw'] += '-clone'
        self.reject(lambda: self.api.load_authority(self.approved, self.plan, self.source['pins'], config=self.config),
            'original_confinement_and_uncloned_journal')

    def test_c2_unapproved_mode_edit_refused(self):
        self.chain()
        guard = self.api.document(self.binding['selection_guard'])
        guard['consumer_context_mode'] = self.api.SAME
        self.binding['selection_guard'] = self.save('wrong_mode', guard)
        with self.admitted():
            self.reject(self.arguments, 'only_Main_bounded_guard_derivation')

    def test_c2_guard_seam_after_original_admission(self):
        text = (cases.SOURCE / 'gpu/orch_r125_continual_guard.py').read_text()
        native = next(item for item in ast.parse(text).body if isinstance(item, ast.FunctionDef) and item.name == 'native_entry')
        body = ast.get_source_segment(text, native)
        self.assertLess(body.index("'fresh_clear_admission'"), body.index('with admitted_prefix'))
        self.assertLess(body.index("'native_GPU_binding'"), body.index('with admitted_prefix'))
        self.assertIn('guard_path=config_path', body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    arguments = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_tests')
    manifest = json.loads(arguments.manifest.read_bytes())
    verify(arguments.source, manifest)
    with tempfile.TemporaryDirectory(prefix='c2-prefix-source-') as temporary:
        source = Path(temporary) / 'source'
        shutil.copytree(arguments.source, source)
        for path in (source, *source.rglob('*')):
            path.chmod(0o755 if path.is_dir() else 0o644)
        (source / 'EPOCH.json').write_text('{"synthetic":true}\n')
        scratch_tools = Path(temporary) / 'tools'
        scratch_tools.mkdir()
        for name in ('prefix_cli.py', 'immutable_prefix_proof.py'):
            shutil.copyfile(TOOLS / name, scratch_tools / name)
        sys.path.insert(0, str(source))
        cases.SOURCE, cases.MODE, cases.WORKER = source, 'C2', scratch_tools
        context_cases.WORKER = scratch_tools
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(context_cases.ConsumerContextTests)
        for name in unittest.defaultTestLoader.getTestCaseNames(C2Cases):
            if name.startswith('test_c2_'):
                suite.addTest(C2Cases(name))
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        origins = {}
        for name, module in tuple(sys.modules.items()):
            if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
                path = Path(module.__file__).resolve()
                relative = str(path.relative_to(source))
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != manifest['new_source_pins'][relative]:
                    raise ValueError('test_source_bytes_drift:' + relative)
                origins[name] = dict(relative=relative, sha256=actual)
    verify(arguments.source, manifest)
    print(json.dumps(dict(passed=result.wasSuccessful(), tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), imported_source_modules=origins,
        isolated_exact_runtime_source=True, synthetic_only=True, native_startup_proven=False,
        positive_unit_fixture_clock_offset_ns=4000000000, real_quiet_age_CLI_test=True,
        total_reserved_30_seconds_proven=False, native_actions=[], GPU_calls=0), sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
