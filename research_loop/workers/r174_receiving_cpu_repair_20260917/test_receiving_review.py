"""Independent local artifact/fence checks; never invoke a receiving wrapper."""

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import mock

import pytest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREVIOUS = HERE.with_name('r173_actual_replay_cpu_20260917')
PINS = {
    'receiving_cpu.py': '6ebeeed6786b2194f874cd1a66a3164b0c302a1054d0fed8f36b48e9cd09b2f2',
    'run_once.py': '9fcb4d27ba7c9a7aa1b1b7df1fa3d70e5f93bb117d5ccbd59f53c338c2c837f8',
    'test_receiving_repair.py': '362ec5d7feaf162d30756b477f1ccc8433b52eba9896d16eadf021f6d98d955e',
    'SCOPE.md': 'be2f1a30f0baa7861aeb9b84109c0eb492741ae8108ecccc5a9dbb5da5a84da2',
    'ACTUAL_RECEIVING_CPU.json': 'd14cda179688a3d145ea1ae5e8039c4e5c4dd3f530ded4d28ac523051a2e28dd',
}
R175 = HERE.with_name('r175_receiving_ldconfig_20260917')
R175_PINS = {
    'receiving_cpu.py': 'a4314df92c8aa5c75156d3085bc7c5d698152d6f15a9c93ba5d53193fd8da38c',
    'run_once.py': 'f325353770964800a0d714ffad5cd9619c03b61e74452f01dc6a2011e257dabf',
    'SCOPE.md': '6d793fbaab2cd3aa7ab0a8a2e4197f1d7f5e1e8363508efb347c327beb269caa',
    'ACTUAL_RECEIVING_CPU.json': '8f60e4ae3d9e21766b46f816822852285b2f757a0cb952089184d38f1df9b1b3',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


@pytest.fixture
def launcher():
    for name, checksum in PINS.items():
        assert digest(HERE.joinpath(name).read_bytes()) == checksum
    path = HERE / 'run_once.py'
    specification = importlib.util.spec_from_file_location('independent_r174_launcher', path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


@pytest.fixture
def evidence(launcher):
    return read_json(HERE / 'ACTUAL_RECEIVING_CPU.json')


@pytest.fixture
def r175_launcher():
    for name, checksum in R175_PINS.items():
        assert digest(R175.joinpath(name).read_bytes()) == checksum
    path = R175 / 'run_once.py'
    specification = importlib.util.spec_from_file_location('independent_r175_launcher', path)
    module = importlib.util.module_from_spec(specification)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def test_R175_full_transport_and_payload_integrity(r175_launcher, monkeypatch):
    monkeypatch.setitem(globals(), 'HERE', R175)
    monkeypatch.setitem(globals(), 'PINS', R175_PINS)
    test_consumed_receipt_transport_and_payload_integrity(
        r175_launcher, read_json(R175 / 'ACTUAL_RECEIVING_CPU.json'))


def test_R175_all_runtime_pins_and_all_bound_reads(r175_launcher):
    receipt = read_json(R175 / 'ACTUAL_RECEIVING_CPU.json')
    test_all_1857_runtime_pins_and_all_bounded_reads_match_consumed_baseline(r175_launcher, receipt)
    assert receipt['candidate_source_sha256'] == read_json(HERE / 'ACTUAL_RECEIVING_CPU.json')['candidate_source_sha256']


def test_R175_every_executed_and_loaded_origin(r175_launcher):
    test_every_executed_and_loaded_origin_is_runtime_or_explicit_negative_support(
        r175_launcher, read_json(R175 / 'ACTUAL_RECEIVING_CPU.json'))


def test_R175_every_original_assertion_method_and_exact_outcome(r175_launcher):
    test_all_test_assertions_and_methods_preserved_except_exact_path_expressions(
        r175_launcher, read_json(R175 / 'ACTUAL_RECEIVING_CPU.json'))


def test_R175_positive_is_receiving_only_and_does_not_rewrite_R174(r175_launcher):
    receipt = read_json(R175 / 'ACTUAL_RECEIVING_CPU.json')
    assert receipt['schema'] == 'R175_ACTUAL_RECEIVING_CPU_V1'
    assert receipt['status'] == 'CPU_TESTS_PASS_NOT_ADMISSION'
    for field in ('success', 'evidence_rebind_eligible', 'test_suite_success', 'source_unchanged_after_tests'):
        assert receipt[field] is True
    assert receipt['tests_run'] == 85 and receipt['failures'] == receipt['errors'] == 0
    assert receipt['skipped'] == receipt['denied_runtime_operations'] == []
    assert not any(receipt.get(field) for field in ('failure', 'failure_type', 'traceback'))
    assert receipt['attempt_limit'] == 1
    for field in ('retry_permitted', 'full_source_approval', 'evaluator_admission',
                  'saved_state_ownership_established', 'saved_handoff_created', 'operational_GO_created',
                  'test_assertions_changed', 'numerical_tolerances_changed', 'startup_copied'):
        assert receipt[field] is False
    assert receipt['base_r174_receipt_sha256'] == digest(HERE.joinpath('ACTUAL_RECEIVING_CPU.json').read_bytes()) == PINS['ACTUAL_RECEIVING_CPU.json']
    assert receipt['base_r174_runner_sha256'] == PINS['receiving_cpu.py']
    assert receipt['torch']['imported'] is True and receipt['torch']['cuda_initialized'] is False
    assert receipt['torch']['real_torch_test'] == [dict(status='PASS', test=(
        'tests.test_orch_r168_targeted_replay.TargetedReplayTests.'
        'test_actual_torch_CPU_applies_exact_baseline_then_four_extra_updates'))]
    for field, value in dict(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1').items():
        assert receipt['environment'][field] == value


def test_R175_single_probe_exact_bytes_environment_and_readonly_wrapper(r175_launcher):
    receiving = r175_launcher.receiving
    receipt = read_json(R175 / 'ACTUAL_RECEIVING_CPU.json')
    references = [dict(requested_path=name, **reference, uid=0, mode='0o755')
                  for name, reference in receiving.LDCONFIG_EXECUTABLES.items()]
    assert receipt['allowed_runtime_probes'] == [dict(event='subprocess.Popen', executable='/sbin/ldconfig',
        command=['/sbin/ldconfig', '-p'], cwd=None, environment=dict(LANG='C', LC_ALL='C', PATH='/usr/bin:/bin'),
        binary_references=references, purpose='READ_ONLY_LIBRARY_CACHE_PRINT')]
    inspection = read_json(R175 / 'LDCONFIG_WRAPPER_INSPECTION.json')
    preflight = read_json(R175 / 'LDCONFIG_PREFLIGHT.json')
    assert inspection['binary_executed'] is preflight['binary_executed'] is False
    assert inspection['remote_writes'] is preflight['remote_writes'] is False
    assert digest(inspection['script_text'].encode()) == inspection['script_sha256'] == references[0]['sha256']
    assert preflight['sha256'] == references[0]['sha256']
    assert preflight['canonical_path'] == inspection['script_path'] == references[0]['path']
    assert len(inspection['script_text'].encode()) == preflight['bytes'] == 387
    assert inspection['script_text'].startswith('#!/bin/sh\n\nif  test $# = 0')
    assert inspection['script_text'].endswith('exec /sbin/ldconfig.real "$@"\n')
    assert inspection['target']['elf'] is True and inspection['target']['bytes'] == 1051280
    for field in ('sha256', 'path', 'uid', 'mode'):
        assert inspection['target'][field] == references[1][field]
    for stem in ('LDCONFIG_PREFLIGHT', 'LDCONFIG_WRAPPER_INSPECTION'):
        assert R175.joinpath(stem + '.json').read_bytes() == R175.joinpath(stem + '_STDOUT.txt').read_bytes()
        assert R175.joinpath(stem + '_STDERR.txt').read_bytes() == b''


@pytest.mark.parametrize('command', [['/usr/bin/gcc', '-Wl,-t', '-o', '/tmp/probe', '-ldl'],
                                   ['ld', '-t', '-o', '/dev/null', '-ldl'],
                                   ['/sbin/ldconfig'], ['/sbin/ldconfig', '-p', '-v']])
def test_R175_still_denies_compilers_linkers_and_other_ldconfig_argv(r175_launcher, tmp_path, monkeypatch, command):
    receiving = r175_launcher.receiving
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = receiving.RuntimeFence(tmp_path, {})
    token = fence.ldconfig_context.set(True)
    try:
        with pytest.raises(PermissionError):
            fence.audit('subprocess.Popen', (command[0], command, None, dict(receiving.LDCONFIG_ENVIRONMENT)))
    finally:
        fence.ldconfig_context.reset(token)
    assert fence.allowed_runtime_probes == []


def test_consumed_receipt_transport_and_payload_integrity(launcher, evidence):
    raw = HERE.joinpath('ACTUAL_RECEIVING_CPU.json').read_bytes()
    assert raw == HERE.joinpath('WRAPPER_STDOUT.txt').read_bytes()
    wrapper = read_json(HERE / 'WRAPPER_RESULT.json')
    assert wrapper['stdout_sha256'] == digest(raw)
    assert wrapper['stderr_sha256'] == digest(HERE.joinpath('WRAPPER_STDERR.txt').read_bytes())
    assert HERE.joinpath('WRAPPER_STDERR.txt').read_bytes() == b''
    assert wrapper['returncode'] == 0 and wrapper['retry_permitted'] is False
    marker = read_json(HERE / 'ATTEMPT_STARTED.json')
    manifest = read_json(HERE / 'PAYLOAD_MANIFEST.json')
    payload = launcher.payload()
    assert marker['payload_sha256'] == digest(launcher.receiving.encoded(payload))
    assert manifest['payload_sha256'] == marker['payload_sha256']
    assert marker['runner_sha256'] == manifest['runner_sha256'] == PINS['receiving_cpu.py']
    assert evidence['runner_ref'] == dict(path=launcher.receiving.SCRATCH + '/receiving_cpu.py',
                                         sha256=PINS['receiving_cpu.py'])
    assert marker['command'] == launcher.command()[-1]
    assert marker['scratch'] == evidence['scratch'] == launcher.receiving.SCRATCH
    assert set(launcher.receiving.unpack_payload(payload)) == set(manifest['files'])
    assert len(manifest['files']) == 10


def test_all_1857_runtime_pins_and_all_bounded_reads_match_consumed_baseline(launcher, evidence):
    receiving = launcher.receiving
    previous = read_json(PREVIOUS / 'ACTUAL_RECEIVING_CPU.json')
    expected = evidence['candidate_source_sha256']
    assert expected == previous['candidate_source_sha256']
    assert len(expected) == 1857
    assert evidence['old_python_files_copied'] == 1854
    assert evidence['added_python_files'] == receiving.HELPERS
    assert evidence['candidate_source_manifest_sha256'] == digest(receiving.encoded(expected))
    assert expected[receiving.NATIVE_PATH] == receiving.NATIVE_SHA256
    assert expected['organism_v6/orch_r125_plain_context.py'] == receiving.PLAIN_SHA256
    assert not set(expected).intersection(receiving.TEST_SUPPORT)
    assert all(name.endswith('.py') and not Path(name).is_absolute() and '..' not in Path(name).parts
               for name in expected)
    source_reads = {str(Path(receiving.OLD_SOURCE) / name): checksum for name, checksum in expected.items()
                    if name not in receiving.HELPERS}
    expected_reads = dict(source_reads)
    for reference in (evidence['old_guard_ref'], evidence['old_plan_ref']):
        expected_reads[reference['path']] = reference['sha256']
    actual_reads = evidence['receiving_bound_reads']
    assert len(actual_reads) == len(expected_reads) == 1856
    assert {entry['path']: entry['sha256'] for entry in actual_reads} == expected_reads
    assert all(0 <= entry['bytes'] <= receiving.MAX_FILE_BYTES for entry in actual_reads)
    assert sum(entry['bytes'] for entry in actual_reads) == evidence['operational_bytes_read'] == 23293408
    assert evidence['operational_bytes_read'] <= receiving.MAX_OPERATIONAL_BYTES
    assert evidence['source_unchanged_after_tests'] is True and evidence['startup_copied'] is False
    assert evidence['old_guard_ref'] == dict(path=receiving.OLD_GUARD, sha256=receiving.GUARD_SHA256)
    assert evidence['old_plan_ref'] == previous['old_plan_ref']


def test_every_executed_and_loaded_origin_is_runtime_or_explicit_negative_support(launcher, evidence):
    receiving = launcher.receiving
    source = Path(evidence['candidate_source_root'])
    assert source == Path(receiving.SCRATCH) / 'source'
    support = Path(receiving.SCRATCH) / 'test_support'
    expected = evidence['candidate_source_sha256']
    executed = evidence['executed_project_files']
    assert len(executed) == 38
    for name, record in executed.items():
        assert record['path'] == str(source / name)
        assert record['sha256'] == expected[name] and record['executions'] >= 1
        assert name not in receiving.TEST_SUPPORT
    assert receiving.NATIVE_PATH in executed
    for name, reference in evidence['runtime_dependencies'].items():
        assert name in receiving.DEPENDENCIES
        relative = name.replace('.', '/') + '.py'
        assert reference == dict(path=str(source / relative), sha256=expected[relative])
        assert relative in executed
    assert set(evidence['runtime_dependencies']) == set(receiving.DEPENDENCIES)
    assert set(evidence['negative_test_support']) == set(evidence['test_support_executed']) == set(receiving.TEST_SUPPORT)
    for name, checksum in receiving.TEST_SUPPORT.items():
        assert evidence['negative_test_support'][name] == dict(path=str(support / name),
            sha256=checksum, runtime_candidate_member=False)
        assert evidence['test_support_executed'][name] == dict(path=str(support / name),
            sha256=checksum, role='NEGATIVE_TEST_SUPPORT_NOT_RUNTIME')
    support_modules = set()
    for name, reference in evidence['loaded_project_modules'].items():
        path = Path(reference['path'])
        if path.is_relative_to(source):
            relative = str(path.relative_to(source))
            assert reference['sha256'] == expected[relative]
            assert relative in executed
        else:
            assert path.is_relative_to(support)
            relative = str(path.relative_to(support))
            assert relative == name.replace('.', '/') + '.py'
            assert reference['sha256'] == receiving.TEST_SUPPORT[relative]
            support_modules.add(relative)
    assert support_modules == set(receiving.TEST_SUPPORT)


def test_all_test_assertions_and_methods_preserved_except_exact_path_expressions(launcher, evidence):
    receiving = launcher.receiving
    source = Path(evidence['candidate_source_root'])
    fixtures = Path(receiving.SCRATCH) / 'harness/fixtures'
    test_ids = set()
    for name, checksum in receiving.TESTS.items():
        raw = REPO.joinpath(name).read_bytes()
        assert digest(raw) == checksum == evidence['tests'][name]['original_sha256']
        adapted, changes = receiving.adapt_test(name, raw, source, fixtures)
        assert digest(adapted) == evidence['tests'][name]['adapted_sha256']
        assert changes == evidence['tests'][name]['path_only_changes']
        expected_path = Path(receiving.SCRATCH) / 'harness' / name
        assert evidence['tests'][name]['adapted_path'] == str(expected_path)
        mappings = {}
        if name.endswith('_native.py'):
            mappings = {
                "Path(__file__).resolve().parents[1] / 'research_loop/workers/r168_replay_candidates_20260917'":
                    'Path(' + repr(str(fixtures)) + ')',
                "FIXTURES / 'NATIVE_cdb542.py'": 'Path(' + repr(str(source / receiving.NATIVE_PATH)) + ')',
            }
        elif name.endswith('_driver.py'):
            mappings = {"Path(__file__).resolve().parents[1] / 'gpu/orch_r125_continual_guard.py'":
                        'Path(' + repr(str(source / 'gpu/orch_r125_continual_guard.py')) + ')'}
        nodes = {ast.dump(ast.parse(original, mode='eval').body): ast.parse(replacement, mode='eval').body
                 for original, replacement in mappings.items()}

        class PathExpressionsOnly(ast.NodeTransformer):
            def visit(self, node):
                replacement = nodes.get(ast.dump(node))
                return deepcopy(replacement) if replacement is not None else super().visit(node)

        tree = ast.parse(raw)
        for definition in tree.body:
            if isinstance(definition, ast.ClassDef):
                for method in definition.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                        test_ids.add(name[:-3].replace('/', '.') + '.' + definition.name + '.' + method.name)
        assert ast.dump(ast.parse(adapted)) == ast.dump(PathExpressionsOnly().visit(tree))
    outcomes = evidence['outcomes']
    assert {entry['test'] for entry in outcomes} == test_ids
    assert len(outcomes) == len(test_ids) == evidence['tests_run'] == 85
    assert all(entry['status'] == 'PASS' for entry in outcomes)
    for suffix in ('test_actual_suffix_helper_still_rejects_EXTRA_and_unknown_kinds',
                   'test_suffix_patched_source_is_refused_not_silently_run'):
        assert any(identifier.endswith('.' + suffix) for identifier in test_ids)


def test_successful_tiny_CPU_math_does_not_override_failed_fence_or_claim_boundaries(evidence):
    assert evidence['test_suite_success'] is True
    assert evidence['failures'] == evidence['errors'] == 0
    assert evidence['skipped'] == []
    assert evidence['torch']['imported'] is True and evidence['torch']['cuda_initialized'] is False
    assert [entry['status'] for entry in evidence['torch']['real_torch_test']] == ['PASS']
    assert evidence['status'] == 'FAILED_NO_RETRY'
    assert evidence['failure'] == 'no_forbidden_runtime_operations'
    assert evidence['failure_type'] == 'ValueError'
    for field in ('success', 'evidence_rebind_eligible', 'retry_permitted', 'operational_GO_created',
                  'saved_handoff_created', 'full_source_approval', 'saved_state_ownership_established',
                  'evaluator_admission', 'numerical_tolerances_changed', 'test_assertions_changed'):
        assert evidence[field] is False
    assert evidence['original_test_methods_removed'] == 0
    assert evidence['allowed_runtime_probes'] == []
    denials = evidence['denied_runtime_operations']
    commands = [entry['command'] for entry in denials if isinstance(entry, dict)]
    assert commands == [['/sbin/ldconfig', '-p'], ['/usr/bin/gcc', '-Wl,-t', '-o',
        evidence['scratch'] + '/tmp/tmp1zwirrtm', '-ldl'], ['ld', '-t', '-o', '/dev/null', '-ldl']]
    assert len(denials) == 6
    assert denials[1::2] == ['process_signal_or_network:subprocess.Popen'] * 3


def test_failed_receipt_with_zero_wrapper_status_stays_failed_and_attempt_consumed(launcher, tmp_path):
    invocation = mock.Mock(return_value=SimpleNamespace(returncode=0,
        stdout=HERE.joinpath('ACTUAL_RECEIVING_CPU.json').read_bytes(), stderr=b''))
    assert launcher.run_once(output=tmp_path, invoke=invocation) == 1
    assert read_json(tmp_path / 'ACTUAL_RECEIVING_CPU.json')['evidence_rebind_eligible'] is False
    with pytest.raises(FileExistsError):
        launcher.run_once(output=tmp_path, invoke=invocation)
    invocation.assert_called_once()


def test_old_R173_stdout_cannot_be_substituted_for_R174_receipt(launcher, tmp_path):
    invocation = mock.Mock(return_value=SimpleNamespace(returncode=0,
        stdout=PREVIOUS.joinpath('ACTUAL_RECEIVING_CPU.json').read_bytes(), stderr=b''))
    with pytest.raises(ValueError, match='actual_receiving_receipt'):
        launcher.run_once(output=tmp_path, invoke=invocation)
    assert tmp_path.joinpath('ATTEMPT_STARTED.json').is_file()
    assert not tmp_path.joinpath('ACTUAL_RECEIVING_CPU.json').exists()
    invocation.assert_called_once()


@pytest.mark.parametrize('command', [['/sbin/ldconfig', '-p'], ['/usr/bin/gcc', '-Wl,-t', '-o', '/tmp/probe', '-ldl'],
                                   ['ld', '-t', '-o', '/dev/null', '-ldl']])
def test_three_observed_requests_are_denied_and_environment_is_not_logged(launcher, tmp_path, monkeypatch, command):
    monkeypatch.setenv('PATH', '/usr/bin:/bin')
    fence = launcher.receiving.RuntimeFence(tmp_path, {})
    with pytest.raises(PermissionError, match='process_signal_or_network:subprocess.Popen'):
        fence.audit('subprocess.Popen', (command[0], command, None,
            dict(PATH='/usr/bin:/bin', REVIEW_PRIVATE_SENTINEL='not-for-the-log')))
    assert fence.allowed_runtime_probes == []
    assert 'not-for-the-log' not in json.dumps(fence.denied)


@pytest.mark.parametrize('path', ['/root/private_life/COMMIT.json', '/proc/1/maps', '/proc/1/stat', '/proc/1/status',
                                  '/proc/self/environ', '/dev/nvidia0'])
def test_exceptions_do_not_admit_foreign_files_processes_credentials_or_GPU(launcher, tmp_path, path):
    fence = launcher.receiving.RuntimeFence(tmp_path, {})
    with pytest.raises(PermissionError):
        fence.audit('open', (path, 'r', os.O_RDONLY))


def test_real_audit_hook_blocks_observed_child_requests_before_spawn(launcher, tmp_path):
    script = '''
import importlib.util,json,os,subprocess,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('isolated_fence',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def must_not_spawn(*arguments,**keywords):
    raise AssertionError('audit_did_not_block_before_process_creation')
subprocess._fork_exec=must_not_spawn
os.posix_spawn=must_not_spawn
scratch=Path(sys.argv[2]);os.chdir(scratch)
fence=module.RuntimeFence(scratch,{})
fence.install()
for command in (['/sbin/ldconfig','-p'],['/usr/bin/gcc','-Wl,-t','-o',str(scratch/'probe'),'-ldl'],
                ['ld','-t','-o','/dev/null','-ldl']):
    try:
        subprocess.run(command,check=False)
    except PermissionError:
        pass
    else:
        raise AssertionError('forbidden_child_was_not_denied')
print(json.dumps(dict(denials=fence.denied,allowed=fence.allowed_runtime_probes)))
'''
    completed = subprocess.run([sys.executable, '-B', '-c', script, str(HERE / 'receiving_cpu.py'), str(tmp_path)],
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PATH='/usr/bin:/bin'),
        capture_output=True, text=True, check=False, timeout=10)
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt['allowed'] == [] and len(receipt['denials']) == 6
    assert not tmp_path.joinpath('probe').exists()
