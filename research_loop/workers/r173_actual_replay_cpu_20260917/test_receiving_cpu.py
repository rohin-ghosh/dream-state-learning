"""Fixture-local checks for staging, path adaptation and one-attempt custody."""

import ast
import base64
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


OWNED = Path(__file__).resolve().parent
specification = importlib.util.spec_from_file_location('r173_run_once', OWNED / 'run_once.py')
launcher = importlib.util.module_from_spec(specification)
specification.loader.exec_module(launcher)
receiving = launcher.receiving


class ReceivingCpuTests(unittest.TestCase):
    def pins(self):
        return {receiving.NATIVE_PATH: receiving.NATIVE_SHA256,
                'gpu/orch_r125_continual_guard.py': receiving.ORIGINAL_GUARD_SHA256,
                'organism_v6/orch_r125_plain_context.py': receiving.PLAIN_SHA256}

    def test_source_delta_is_exact_old_python_plus_three_no_suffix(self):
        receiving.validate_pins(self.pins())
        for extra in receiving.SUFFIX_FILES | set(receiving.HELPERS):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                receiving.validate_pins(dict(self.pins(), **{extra: 'a' * 64}))

    def test_unknown_hash_wrong_plain_context_and_path_escape_rejected(self):
        for name, value in [('gpu/extra.py', '?'), ('../other.py', 'a' * 64),
                            ('/absolute.py', 'a' * 64), ('gpu//file.py', 'a' * 64),
                            ('README.md', 'a' * 64),
                            ('organism_v6/orch_r125_plain_context.py', 'd' * 64)]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                receiving.validate_pins(dict(self.pins(), **{name: value}))

    def test_payload_pins_and_whitelist_fail_closed(self):
        bundle = launcher.payload()
        self.assertEqual(len(receiving.unpack_payload(bundle)), 8)
        bundle['files']['gpu/not_reviewed.py'] = base64.b64encode(b'').decode()
        with self.assertRaisesRegex(ValueError, 'exact_payload_whitelist'):
            receiving.unpack_payload(bundle)
        bundle = launcher.payload()
        bundle['files'][receiving.FIXTURE] = base64.b64encode(b'{}').decode()
        with self.assertRaisesRegex(ValueError, 'payload_pin'):
            receiving.unpack_payload(bundle)

    def test_path_only_adaptation_preserves_assertions_and_all_tests(self):
        bundle = receiving.unpack_payload(launcher.payload())
        source, fixtures = Path('/candidate/source'), Path('/candidate/harness/fixtures')
        for name in receiving.TESTS:
            original = bundle[name]
            adapted, changes = receiving.adapt_test(name, original, source, fixtures)
            reversed_text = adapted.decode()
            for change in reversed(changes):
                reversed_text = reversed_text.replace(change['replacement'], change['original'])
            self.assertEqual(reversed_text.encode(), original)
            self.assertEqual(sum(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(original))),
                             sum(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(adapted))))
        native = bundle['tests/test_orch_r168_targeted_replay_native.py']
        with self.assertRaisesRegex(ValueError, 'exact_path_adaptation_count'):
            receiving.adapt_test('tests/test_orch_r168_targeted_replay_native.py',
                                native.replace(b'NATIVE_cdb542.py', b'changed.py'), source, fixtures)

    def test_bound_reader_rejects_changed_bytes_symlink_and_unknown_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory).resolve() / 'original.py'
            source.write_bytes(b'original\n')
            checksum = receiving.sha(source.read_bytes())
            reader = receiving.BoundReader()
            self.assertEqual(reader.read(source, checksum), b'original\n')
            source.write_bytes(b'changed\n')
            with self.assertRaisesRegex(ValueError, 'source_hash_mismatch'):
                reader.read(source, checksum)
            link = Path(directory).resolve() / 'link.py'
            link.symlink_to(source)
            with self.assertRaisesRegex(ValueError, 'no_symlink'):
                reader.read(link, checksum)
            with self.assertRaisesRegex(ValueError, 'known_full_read_hash'):
                reader.read(source, 'UNKNOWN')

    def test_create_only_and_inventory_reject_extra_files_or_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            path = source / 'gpu/code.py'
            receiving.write_once(path, b'original')
            with self.assertRaises(FileExistsError):
                receiving.write_once(path, b'overwrite')
            pins = {'gpu/code.py': receiving.sha(b'original')}
            self.assertEqual(receiving.inventory(source, pins), pins)
            (source / 'unvetted.txt').write_bytes(b'no')
            with self.assertRaisesRegex(ValueError, 'candidate_exact_whitelist'):
                receiving.inventory(source, pins)

    def test_missing_candidate_dependency_never_uses_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / 'gpu').mkdir()
            finder = receiving.CandidateImports(source, {})
            with self.assertRaisesRegex(ModuleNotFoundError, 'not_in_actual_guard'):
                finder.find_spec('gpu.orch_r145_suffix_boundary', [str(source / 'gpu')])
            with self.assertRaisesRegex(ImportError, 'forbids_model_provider'):
                finder.find_spec('transformers')

    def test_runtime_fence_allows_candidate_not_life_data_or_writes(self):
        fence = receiving.RuntimeFence(Path('/candidate'), {})
        fence.check_file(Path('/candidate/source/gpu/code.py'), False)
        fence.check_file(Path('/candidate/tmp/fixture/GO.json'), True)
        for path, writing in [('/localhome/local-rohing/live/stream/record.json', False),
                              ('/localhome/local-rohing/evaluation/data.json', False),
                              ('/candidate/source/gpu/code.py', True),
                              ('/dev/nvidia0', False)]:
            with self.subTest(path=path), self.assertRaises(PermissionError):
                fence.check_file(Path(path), writing)
        for event in ('subprocess.Popen', 'os.kill', 'socket.connect'):
            with self.subTest(event=event), self.assertRaises(PermissionError):
                fence.audit(event, ())

    def test_failed_wrapper_consumes_latch_and_second_call_never_invokes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(launcher, 'payload', return_value={'runner_sha256': 'a' * 64}), \
                    patch.object(launcher, 'command', return_value=['sanctioned', 'CPU']):
                calls = []

                def fail(*arguments, **keywords):
                    calls.append(arguments)
                    raise OSError('fixture_wrapper_failure')

                with self.assertRaisesRegex(OSError, 'fixture_wrapper_failure'):
                    launcher.run_once(output, fail)
                with self.assertRaises(FileExistsError):
                    launcher.run_once(output, fail)
                self.assertEqual(len(calls), 1)
                self.assertTrue((output / 'WRAPPER_FAILURE.json').is_file())

    def test_only_sanctioned_wrapper_and_CPU_interpreter_command(self):
        arguments = launcher.command()
        self.assertEqual(arguments[:2], ['bash', str(launcher.REPO / 'gpu/ovx2_ssh.sh')])
        self.assertIn('CUDA_VISIBLE_DEVICES= ', arguments[2])
        self.assertIn('/localhome/local-rohing/v2/venv/bin/python -I -B', arguments[2])
        self.assertEqual(receiving.SCRATCH, '/localhome/local-rohing/orch_r173_actual_replay_cpu_20260917_attempt1')

    def test_fence_in_isolated_local_process_allows_dirfd_and_receipt(self):
        program = '''
import importlib.util, os, pathlib, tempfile
specification = importlib.util.spec_from_file_location('receiving', RUNNER)
receiving = importlib.util.module_from_spec(specification)
specification.loader.exec_module(receiving)
with tempfile.TemporaryDirectory() as directory:
    scratch = pathlib.Path(directory).resolve()
    (scratch / 'tmp').mkdir()
    fence = receiving.RuntimeFence(scratch, {})
    fence.install()
    descriptor = os.open(scratch / 'tmp', os.O_RDONLY | os.O_DIRECTORY)
    output = os.open('fixture.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, dir_fd=descriptor)
    os.write(output, b'{}')
    os.close(output)
    os.close(descriptor)
    receiving.write_once(scratch / 'RECEIVING_CPU.json', b'{}')
    assert not fence.denied
    print('LOCAL_FIXTURE_FENCE_OK', flush=True)
    os._exit(0)
'''.replace('RUNNER', repr(str(OWNED / 'receiving_cpu.py')))
        result = subprocess.run([sys.executable, '-I', '-B', '-c', program],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('LOCAL_FIXTURE_FENCE_OK', result.stdout)


if __name__ == '__main__':
    unittest.main()
