"""Offline v4 regressions; simulated namespace/clock inputs, never namespace entry."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from source_port import candidates


WORKER = Path(__file__).resolve().parent
V3 = WORKER.parent
sys.path.insert(0, str(V3))
spec = importlib.util.spec_from_file_location('sealed_v3_tests', V3 / 'test_prefix_proof.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
legacy.WORKER = WORKER


def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ConsumerContextTests(legacy.PrefixTests):
    def setUp(self):
        super().setUp()
        self.virtual_clock = patch.object(self.helper, 'clock_ns',
            side_effect=lambda: time.time_ns() + 4_000_000_000)
        self.virtual_clock.start()
        self.addCleanup(self.virtual_clock.stop)

    def cross_authority(self):
        self.approve(self.proof, consumer_context_mode=self.helper.CROSS_NAMESPACE)
        document = dict(receiver=dict(prefix_consumer_context=self.helper.admission_clause(self.guard, self.authority)))
        self.admission_path = self.directory / 'original_admission.json'
        self.admission_path.write_bytes(self.helper.encoded(document))
        self.admission = dict(path=str(self.admission_path), sha256=raw_sha(self.admission_path),
            field_path=['receiver', 'prefix_consumer_context'])
        self.consumer = deepcopy(self.proof['binding']['environment'])
        self.consumer['mount_namespace']['ino'] += 17
        return self.admission

    def cross_scan(self, admission=None):
        with patch.object(self.helper, 'environment', return_value=self.consumer):
            return self.tail.scan(self.journal, self.selection, prefix_proof=self.authority,
                prefix_admission=self.admission if admission is None else admission)

    def test_cross_context_explicit_admission_same_objects_and_actual_receipt(self):
        self.complete()
        self.produce()
        self.cross_authority()
        self.assertEqual(self.cross_scan(), self.journal._state)
        context = self.journal.checkpoint_tail_receipt['prefix_proof']['consumer_context']
        self.assertEqual(context['producer_environment'], self.proof['binding']['environment'])
        self.assertEqual(context['consumer_environment'], self.consumer)
        self.assertEqual(context['admission'], self.admission)
        self.assertNotEqual(context['producer_environment']['mount_namespace'], context['consumer_environment']['mount_namespace'])

    def test_cross_context_mode_without_independent_admission_refuses(self):
        self.complete()
        self.produce()
        self.cross_authority()
        with patch.object(self.helper, 'environment', return_value=self.consumer):
            self.reject(self.scan, 'independent_original_admission_required')
        self.reject(lambda: self.cross_scan({}), 'independent_original_admission_required')

    def test_cross_context_admission_not_from_guard_or_child_fields(self):
        self.complete()
        self.produce()
        self.cross_authority()
        for reference in (
                dict(self.admission, sha256='0' * 64),
                dict(self.admission, field_path=['child_selected_context']),
                dict(path=str(self.guard_path), sha256=raw_sha(self.guard_path), field_path=['binding']),
                dict(path=str(self.proof_path), sha256=raw_sha(self.proof_path), field_path=['binding'])):
            with self.subTest(reference=reference):
                self.reject(lambda: self.cross_scan(reference))
        document = json.loads(self.admission_path.read_bytes())
        document['receiver']['prefix_consumer_context']['guard']['guard_sha256'] = '0' * 64
        self.admission_path.write_bytes(self.helper.encoded(document))
        self.admission['sha256'] = raw_sha(self.admission_path)
        self.reject(self.cross_scan, 'exact_original_admission_context_scope')

    def test_cross_context_cannot_change_kernel_boot(self):
        self.complete()
        self.produce()
        self.cross_authority()
        self.consumer['boot_id'] = '0' * 36
        self.reject(self.cross_scan, 'same_kernel_boot_required')

    def test_same_namespace_mode_still_default_and_rejects_different_namespace(self):
        self.complete()
        self.produce()
        self.assertEqual(self.guard['consumer_context_mode'], self.helper.SAME_NAMESPACE)
        changed = deepcopy(self.proof['binding']['environment'])
        changed['mount_namespace']['ino'] += 18
        with patch.object(self.helper, 'environment', return_value=changed):
            self.reject(self.scan, 'same_trusted_environment')

    def test_cross_context_every_prefix_record_and_intent_identity_is_rechecked(self):
        self.complete()
        self.produce()
        self.cross_authority()
        original = self.helper._pair
        for index in range(self.selection['complete_index'] + 1):
            for suffix in ('.json', '.intent.json'):
                with self.subTest(index=index, suffix=suffix):
                    def changed(journal, number):
                        pair = original(journal, number)
                        if number == index:
                            pair[suffix]['ino'] += 1
                        return pair
                    with patch.object(self.helper, '_pair', side_effect=changed):
                        self.reject(self.cross_scan, 'prefix_record_or_intent_changed')

    def test_cross_context_every_source_file_identity_is_rechecked(self):
        self.complete()
        self.produce()
        self.cross_authority()
        original = self.helper._recheck_path
        for target in self.proof['source_objects']['files']:
            with self.subTest(path=target['path']):
                def changed(snapshot):
                    if snapshot['path'] == target['path']:
                        altered = deepcopy(snapshot)
                        altered['identity']['ino'] += 1
                        return original(altered)
                    return original(snapshot)
                with patch.object(self.helper, '_recheck_path', side_effect=changed):
                    self.reject(self.cross_scan, 'external_file_changed')

    def test_cross_context_source_same_bytes_new_inode_and_directory_metadata_refuse(self):
        self.complete()
        self.produce()
        self.cross_authority()
        path = legacy.SOURCE / 'gpu/checkpoint_tail_runtime.py'
        replacement = self.directory / 'same_source_bytes'
        replacement.write_bytes(path.read_bytes())
        os.chmod(replacement, path.stat().st_mode)
        os.replace(replacement, path)
        self.reject(self.cross_scan, 'external_file_changed')
        self.produce()
        self.cross_authority()
        directory = legacy.SOURCE / 'gpu'
        before = directory.stat().st_mode
        os.chmod(directory, before ^ 0o100)
        os.chmod(directory, before)
        self.reject(self.cross_scan, 'immutable_source_directory_metadata_changed')

    def test_cross_context_omitted_source_snapshot_and_root_fingerprints_refuse(self):
        self.complete()
        self.produce()
        original = deepcopy(self.proof)
        for mutate in (
                lambda proof: proof['source_objects']['files'].pop(),
                lambda proof: proof['source_objects']['directories'].pop(),
                lambda proof: proof['locations']['root_chain'][-1].update(ino=0),
                lambda proof: proof['locations']['records'].update(dev=0),
                lambda proof: proof['locations']['inbox'].update(ino=0),
                lambda proof: proof['locations']['manifest'].update(ctime_ns=0),
                lambda proof: proof['locations']['writer_lock'].update(ino=0)):
            with self.subTest(mutation=mutate):
                self.proof = deepcopy(original)
                mutate(self.proof)
                self.cross_authority()
                self.reject(self.cross_scan)

    def test_cross_context_A_to_B_keeps_all_interval_and_tail_inbox(self):
        self.complete()
        self.produce()
        resume = self.advance_complete()
        self.approve(self.proof, **resume, consumer_context_mode=self.helper.CROSS_NAMESPACE)
        document = dict(receiver=dict(prefix_consumer_context=self.helper.admission_clause(self.guard, self.authority)))
        self.admission_path = self.directory / 'original_admission.json'
        self.admission_path.write_bytes(self.helper.encoded(document))
        self.admission = dict(path=str(self.admission_path), sha256=raw_sha(self.admission_path),
            field_path=['receiver', 'prefix_consumer_context'])
        self.consumer = deepcopy(self.proof['binding']['environment'])
        self.consumer['mount_namespace']['ino'] += 19
        self.assertEqual(self.cross_scan(), self.journal._state)
        self.assertEqual(set(self.cross_scan()['inbox']), {'first', 'between-completes', 'after-selected-complete'})

    def test_young_prefix_refuses_before_any_raw_prefix_hash(self):
        self.complete()
        identities = [identity for index in range(self.selection['complete_index'] + 1)
            for identity in self.helper._pair(self.journal, index).values()]
        now = max(identity['ctime_ns'] for identity in identities)
        with patch.object(self.helper, 'clock_ns', return_value=now), \
                patch.object(self.tail, 'hash_record') as hashed:
            self.reject(self.produce, 'immutable_file_too_young')
            hashed.assert_not_called()

    def test_same_quantum_same_size_restored_mtime_metadata_alias_refuses_young_proof(self):
        self.complete()
        pairs = {index: self.helper._pair(self.journal, index)
            for index in range(self.selection['complete_index'] + 1)}
        path = self.file()
        before = path.stat()
        raw = path.read_bytes()
        self.assertIn(b'System.', raw)
        path.write_bytes(raw.replace(b'System.', b'System!', 1))
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(path.stat().st_size, before.st_size)
        quantum = max(identity['ctime_ns'] for pair in pairs.values() for identity in pair.values())
        with patch.object(self.helper, '_pair', side_effect=lambda journal, index: deepcopy(pairs[index])), \
                patch.object(self.helper, 'clock_ns', return_value=quantum), \
                patch.object(self.tail, 'hash_record') as hashed:
            self.reject(self.produce, 'immutable_file_too_young')
            hashed.assert_not_called()

    def test_consumer_rejects_forged_young_seal_and_clock_rollback(self):
        self.complete()
        self.produce()
        self.proof['sealing_clock']['started_wall_ns'] = max(record['identities']['.json']['ctime_ns']
            for record in self.proof['records'])
        self.approve(self.proof)
        self.reject(self.scan, 'immutable_file_too_young')
        self.produce()
        with patch.object(self.helper, 'clock_ns', return_value=self.proof['sealing_clock']['started_wall_ns'] - 1):
            self.reject(self.scan, 'sealing_clock_rollback_or_future_proof')

    def test_quiet_window_cannot_be_lowered_by_guard_or_proof(self):
        self.complete()
        self.produce()
        self.proof['binding']['metadata_policy']['minimum_quiet_ns'] = 0
        self.approve(self.proof)
        self.reject(self.scan, 'exact_quiet_age_policy')

    def test_cli_producer_and_readonly_probe_no_writer_lock(self):
        original = self.complete
        def aged_complete(*args, **kwargs):
            selection = original(*args, **kwargs)
            time.sleep(3.2)
            return selection
        with patch.object(self, 'complete', side_effect=aged_complete):
            super().test_cli_producer_and_readonly_probe_no_writer_lock()


def candidate_source(original, destination):
    legacy.candidate_source(original, destination)
    generated = candidates()
    (destination / 'gpu/checkpoint_tail_runtime.py').write_bytes(generated['checkpoint_tail_runtime.candidate.py'])
    (destination / 'gpu/immutable_prefix_proof.py').write_bytes(generated['immutable_prefix_proof.py'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--mode', choices=('C2', 'learner', 'frozen'))
    parser.add_argument('--receipt', type=Path)
    arguments = parser.parse_args()
    if arguments.source is not None:
        legacy.SOURCE, legacy.MODE = arguments.source, arguments.mode
        sys.path.insert(0, str(arguments.source))
        started = time.monotonic()
        outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContextTests))
        print(json.dumps(dict(mode=arguments.mode, tests=outcome.testsRun, passed=outcome.wasSuccessful(),
            errors=len(outcome.errors), failures=len(outcome.failures), seconds=time.monotonic() - started)))
        sys.exit(not outcome.wasSuccessful())
    results = []
    failures = 0
    for mode in ('C2', 'learner', 'frozen'):
        with tempfile.TemporaryDirectory(prefix='v4-source-', dir=WORKER) as directory:
            source = Path(directory) / 'source'
            candidate_source(legacy.C2_SOURCE if mode == 'C2' else legacy.PAIR_SOURCE, source)
            result = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                '--source', str(source), '--mode', mode], env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                    PYTHONDONTWRITEBYTECODE='1', TMPDIR=directory), capture_output=True, text=True, timeout=180)
            print('V4_SYNTHETIC_MODE=' + mode, flush=True)
            print(result.stderr, end='')
            print(result.stdout, end='', flush=True)
            results.append(json.loads(result.stdout.splitlines()[-1]))
            failures += result.returncode != 0
            if mode == 'C2':
                result = subprocess.run([sys.executable, '-B', str(V3.parent /
                    'rohin233_recovery_node4_20260918/checkpoint_tail_tests.py')], env=dict(os.environ,
                        CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', TMPDIR=directory,
                        CHECKPOINT_TAIL_SOURCE=str(source)), capture_output=True, text=True, timeout=60)
                print('ORIGINAL_DEFAULT_SUITE\n' + result.stderr + result.stdout, flush=True)
                failures += result.returncode != 0
                default_passed = result.returncode == 0
    sealed_v3 = json.loads((V3 / 'SEALED_REVIEW_RECEIPT.json').read_bytes())
    v3_preserved = all(raw_sha(V3 / name) == expected for name, expected in sealed_v3['file_sha256'].items())
    failures += not v3_preserved
    if arguments.receipt:
        receipt = dict(schema='R233_CONSUMER_CONTEXT_V4_SYNTHETIC_RECEIPT_V1', created_unix=time.time(),
            matrices=results, synthetic_tests=sum(result['tests'] for result in results),
            original_default_18_tests_passed=default_passed, v3_hashes_preserved=v3_preserved, passed=not failures,
            simulated_consumer_namespaces=True, positive_unit_fixture_clock_offset_ns=4_000_000_000,
            real_quiet_age_CLI_tests=True, deterministic_young_metadata_alias_refusal_test=True,
            actual_node_or_native_actions=False, reservation_maximum_seconds=30,
            artifacts={name: raw_sha(WORKER / name) for name in ('source_port.py', 'context_extension.py',
                'immutable_prefix_proof.py', 'checkpoint_tail_runtime.candidate.py', 'prefix_cli.py', 'test_consumer_context.py')})
        with arguments.receipt.open('x') as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write('\n')
    sys.exit(bool(failures))
