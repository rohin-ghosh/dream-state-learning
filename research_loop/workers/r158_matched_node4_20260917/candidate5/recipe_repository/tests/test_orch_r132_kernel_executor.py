"""CPU-only synthetic tests; no torch import, child execution or GPU access."""

import base64
import ast
import builtins
from copy import deepcopy
import datetime
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import zlib

import pytest

from gpu import orch_r132_kernel_executor as executor


def origin():
    return dict(kind='BUILDER_TEST', record_index=0, record_sha256='a' * 64)


def raw_request(source=executor.EXAMPLE_SOURCE):
    return json.dumps(executor.make_request(source, origin())).encode()


def write_json(path, document):
    raw = json.dumps(document, sort_keys=True).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def test_schema_is_available_without_runtime_or_GPU():
    environment = executor.environment_schema()
    assert environment['lengths'] == [1, 1024, 65537, 1048576]
    assert environment['requires_verified_gpu_gate'] is True
    assert 'def add_kernel(' in environment['entrypoint']
    assert environment['timing_origin'] == 'trusted_driver_cuda_events_not_child_reports'


def test_source_never_imported_compiled_or_executed_by_parser(monkeypatch):
    source = executor.EXAMPLE_SOURCE
    original_compile = builtins.compile

    def only_AST(*args, **kwargs):
        flags = args[3] if len(args) > 3 else kwargs.get('flags', 0)
        assert flags & ast.PyCF_ONLY_AST
        return original_compile(*args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError('source treated as executable')

    with monkeypatch.context() as guards:
        for name in ('eval', 'exec', 'open'):
            guards.setattr(builtins, name, forbidden)
        guards.setattr(builtins, 'compile', only_AST)
        guards.setattr(subprocess, 'Popen', forbidden)
        guards.setattr(builtins, '__import__', forbidden)
        request = executor.make_request(source, origin())
        parsed = executor.parse_request(json.dumps(request).encode())
    assert parsed == request
    assert parsed['source'] == source


@pytest.mark.parametrize('field', ['path', 'args', 'devices', 'gpu_uuid', 'environment', 'shapes', 'dtype', 'executable'])
def test_child_cannot_select_operator_controls(field):
    request = executor.make_request(executor.EXAMPLE_SOURCE, origin())
    request[field] = 'untrusted'
    with pytest.raises(ValueError, match='exact_request_fields'):
        executor.parse_request(json.dumps(request).encode())


@pytest.mark.parametrize('field', ['schema', 'task', 'source', 'source_sha256', 'origin', 'request_id'])
def test_missing_request_fields(field):
    request = executor.make_request(executor.EXAMPLE_SOURCE, origin())
    del request[field]
    with pytest.raises(ValueError):
        executor.parse_request(json.dumps(request).encode())


@pytest.mark.parametrize('field,value', [('task', 'other'), ('source', 'changed'),
    ('source_sha256', '0' * 64), ('request_id', '0' * 64)])
def test_source_task_hash_binding(field, value):
    request = executor.make_request(executor.EXAMPLE_SOURCE, origin())
    request[field] = value
    with pytest.raises(ValueError):
        executor.parse_request(json.dumps(request).encode())


@pytest.mark.parametrize('raw', [b'{"key":1,"key":2}', b'{"key":NaN}', b'[]', b'\xff', b' ' * 100001])
def test_malformed_request(raw):
    with pytest.raises(ValueError):
        executor.parse_request(raw)


def test_canonical_id_matches_independent_encoding():
    request = executor.make_request('# é\n' + executor.EXAMPLE_SOURCE, origin())
    content = {key: value for key, value in request.items() if key != 'request_id'}
    expected = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    assert request['request_id'] == expected


def test_fixed_profile_is_not_CVD_only_and_has_no_host_output_mount(tmp_path):
    command = executor.command(tmp_path / 'job', tmp_path / 'runtime', 'orch-r132-kernel-' + 'a' * 32)
    assert command[:3] == ['sudo', '-n', 'systemd-run']
    for setting in ('PrivateNetwork=yes', 'PrivateDevices=yes', 'NoNewPrivileges=yes',
        'DevicePolicy=strict', 'MemoryMax=4G', 'TasksMax=64', 'RuntimeMaxSec=90',
        'KillMode=control-group', 'MemorySwapMax=0', 'CPUQuota=200%', 'OOMPolicy=kill'):
        assert '--property=' + setting in command
    assert '--property=DeviceAllow=/dev/nvidia1 rw' in command
    assert '--property=DeviceAllow=/dev/nvidiactl rw' in command
    assert '--property=DeviceAllow=/dev/nvidia-uvm rw' in command
    assert not any('/dev/nvidia0 ' in argument or '/dev/nvidia2 ' in argument or '*' in argument for argument in command)
    assert '--property=BindPaths=/dev/nvidia1 /dev/nvidiactl /dev/nvidia-uvm' in command
    assert '/usr/bin/env' in command and '-i' in command
    assert command[-3:] == ['/usr/bin/python3', '-I', '/input/harness.py']
    assert '--property=PrivateTmp=no' in command
    assert '--property=TemporaryFileSystem=/work:rw,size=512M,mode=1777' in command
    assert '--property=InaccessiblePaths=/sys /run /tmp -/var/tmp' in command
    assert 'TMPDIR=/work/tmp' in command
    assert 'TRITON_LIBCUDA_PATH=/usr/lib/x86_64-linux-gnu' in command
    assert "'TRITON_LIBCUDA_PATH'" in executor.BOUNDARY_PROBE
    assert '--property=RestrictAddressFamilies=AF_UNIX' in command
    assert '--property=PrivateIPC=yes' in command
    assert '--property=PrivateNetwork=yes' in command
    assert not any('bwrap' in argument or '/output' in argument for argument in command)


@pytest.mark.parametrize('path', ['relative', '/tmp/../other', '/tmp/has space', '/tmp/a;id'])
def test_ambiguous_operator_paths_rejected(path):
    with pytest.raises(ValueError):
        executor.trusted_path(path)


def test_trusted_harness_has_real_compile_reference_and_synchronized_timing():
    compile(executor.HARNESS, '<trusted-harness>', 'exec')
    assert 'spec.loader.exec_module(candidate)' in executor.HARNESS
    assert 'torch.add(left, right, out=output)' in executor.HARNESS
    assert 'finish.synchronize()' in executor.HARNESS
    assert 'first_compile_seconds' in executor.HARNESS
    assert 'output.cpu().contiguous().numpy().tobytes()' in executor.HARNESS


def measurements():
    return dict(schema='R132_KERNEL_MEASUREMENTS_V1', status='MEASURED', first_compile_seconds=1.5,
        torch_version='synthetic-test', triton_version='synthetic-test',
        cases={str(size): dict(reference_ms=2.0, candidate_ms=1.0,
            output_zlib_base64=base64.b64encode(zlib.compress(executor.expected_output(size))).decode())
            for size in executor.LENGTHS})


def test_full_outputs_verified_independently_and_timing_not_certified():
    result = executor.validate_measurements(json.dumps(measurements()).encode())
    assert result['status'] == 'CORRECT'
    assert result['correctness_verified'] is True
    assert result['speedup_claim_authorized'] is False
    assert result['timing_is_child_reported'] is False
    assert result['timing_origin'] == 'TRUSTED_DRIVER_CUDA_EVENTS'
    assert all(case['reported_speedup'] == 2.0 for case in result['cases'].values())


def test_wrong_output_cannot_pass_self_reported_correctness():
    document = measurements()
    document['correct'] = True
    document['cases']['1']['output_zlib_base64'] = base64.b64encode(zlib.compress(b'\0' * 4)).decode()
    result = executor.validate_measurements(json.dumps(document).encode())
    assert result['status'] == 'INCORRECT'
    assert result['cases']['1']['reported_speedup'] is None


@pytest.mark.parametrize('value', [0, -1, True, '1', float('nan'), float('inf')])
def test_invalid_timing_rejected(value):
    document = measurements()
    document['cases']['1']['candidate_ms'] = value
    with pytest.raises(ValueError):
        executor.validate_measurements(json.dumps(document).encode())


@pytest.mark.parametrize('data', [b'x' * 5, b'x' * 1000000])
def test_compression_bomb_and_wrong_length_rejected(data):
    document = measurements()
    document['cases']['1']['output_zlib_base64'] = base64.b64encode(zlib.compress(data)).decode()
    with pytest.raises(ValueError, match='bounded_output'):
        executor.validate_measurements(json.dumps(document).encode())


def test_compile_error_remains_error_not_timing():
    result = executor.validate_measurements(json.dumps(dict(schema='R132_KERNEL_MEASUREMENTS_V1',
        status='ERROR', phase='candidate_compile_and_first_launch', error='synthetic compiler error')).encode())
    assert result['status'] == 'KERNEL_ERROR'
    assert result['correctness_verified'] is False
    assert result['speedups'] is None


def valid_gate(tmp_path, now=1000):
    identity = {'test_identity': 'not_live_evidence'}
    receipt = tmp_path / 'negative-receipt.json'
    checksum = write_json(receipt, dict(identity=identity, passed=True,
        checks={name: True for name in executor.GATE_CHECKS}))
    document = dict(schema='R132_GPU_CONFINEMENT_GATE_V1', passed=True, identity=identity,
        observed_unix=now, expires_unix=now+1000, checks={name: dict(passed=True,
            receipt_path=str(receipt), receipt_sha256=checksum) for name in executor.GATE_CHECKS})
    path = tmp_path / 'gate.json'
    write_json(path, document)
    return path, document, identity


def test_complete_bound_gate_and_artifacts_pass(tmp_path):
    path, document, identity = valid_gate(tmp_path)
    assert executor.validate_gate(path, identity, 1000) == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('change', [dict(schema='R125_CPU_CONFINEMENT_PROBE_V1'), dict(passed=False),
    dict(identity={}), dict(checks={}), dict(expires_unix=1100), dict(observed_unix=1001)])
def test_CPU_or_unbound_or_expired_gate_rejected(tmp_path, change):
    path, document, identity = valid_gate(tmp_path)
    document.update(change)
    write_json(path, document)
    with pytest.raises(ValueError):
        executor.validate_gate(path, identity, 1000)


def test_gate_boolean_without_raw_evidence_rejected(tmp_path):
    path, document, identity = valid_gate(tmp_path)
    (tmp_path / 'negative-receipt.json').write_text('{}')
    with pytest.raises(ValueError, match='receipt_hash'):
        executor.validate_gate(path, identity, 1000)


def admission(tmp_path, now=1789540000):
    lease = tmp_path / 'lease.json'
    checksum = write_json(lease, dict(conservative_lease_end_utc='2026-09-19T00:00:00+00:00', margin_seconds=21600))
    document = dict(schema='R132_KERNEL_ADMISSION_V1', main_authorized=True, census_clear=True,
        gpu_uuid=executor.GPU_UUID, device_minor=1, observed_unix=now, expires_unix=now+1000,
        hard_wall_unix=1789754400, lease_receipt_path=str(lease), lease_receipt_sha256=checksum)
    path = tmp_path / 'admission.json'
    write_json(path, document)
    return path, document, now


def test_admission_bound_to_real_lease_fields(tmp_path):
    path, document, now = admission(tmp_path)
    assert executor.validate_admission(path, now) == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('change', [dict(main_authorized=False), dict(census_clear=False),
    dict(device_minor=True), dict(device_minor=2), dict(gpu_uuid='other'),
    dict(hard_wall_unix=1789776000), dict(observed_unix=0), dict(lease_receipt_sha256='0'*64)])
def test_bad_custody_mapping_clock_or_lease_rejected(tmp_path, change):
    path, document, now = admission(tmp_path)
    document.update(change)
    write_json(path, document)
    with pytest.raises(ValueError):
        executor.validate_admission(path, now)


def test_editable_existing_venv_is_not_implicitly_approved(tmp_path):
    runtime = tmp_path / 'venv'
    runtime.mkdir()
    with pytest.raises(FileNotFoundError):
        executor.validate_runtime(runtime)


def test_missing_admission_prevents_runtime_or_process_launch(monkeypatch, tmp_path):
    monkeypatch.setattr(executor, 'LOCK_PATH', tmp_path/'GPU.lock')

    def forbidden(*args, **kwargs):
        raise AssertionError('must stop before runtime or GPU inspection')

    monkeypatch.setattr(executor, 'validate_runtime', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    with pytest.raises(FileNotFoundError):
        executor.run_request(raw_request(), spool=tmp_path/'spool', runtime_root=tmp_path/'runtime',
            gate_path=tmp_path/'gate', admission_path=tmp_path/'missing')
    assert not (tmp_path/'spool').exists()


def test_child_origin_cannot_be_asserted_by_request_alone(monkeypatch, tmp_path):
    monkeypatch.setattr(executor, 'LOCK_PATH', tmp_path/'GPU.lock')
    request = executor.make_request(executor.EXAMPLE_SOURCE, dict(origin(), kind='TRAIN_CHILD_RESPONSE'))
    with pytest.raises(ValueError, match='origin_verifier'):
        executor.run_request(json.dumps(request).encode(), spool=tmp_path/'spool', runtime_root=tmp_path/'runtime',
            gate_path=tmp_path/'gate', admission_path=tmp_path/'missing')


def test_owned_GPU_lock_prevents_parallel_jobs(monkeypatch, tmp_path):
    lock_path = tmp_path/'GPU.lock'
    lock_path.touch(mode=0o600)
    monkeypatch.setattr(executor, 'LOCK_PATH', lock_path)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            executor.run_request(raw_request(), spool=tmp_path/'spool', runtime_root=tmp_path/'runtime',
                gate_path=tmp_path/'gate', admission_path=tmp_path/'missing')


def test_never_stop_another_root(monkeypatch, tmp_path):
    calls = []

    def observe(arguments, **kwargs):
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, 'LoadState=loaded\nRootDirectory=/other\n', '')

    monkeypatch.setattr(subprocess, 'run', observe)
    with pytest.raises(ValueError, match='unowned'):
        executor.stop_owned('orch-r132-kernel-'+'a'*32, tmp_path)
    assert len(calls) == 1


def test_pseudo_file_with_zero_reported_size_is_read_bounded(monkeypatch):
    class PseudoPath:
        def open(self, mode):
            return io.BytesIO(b'kernel metadata')

    assert executor.read_pseudo(PseudoPath(), 32) == b'kernel metadata'
    with pytest.raises(ValueError, match='bounded_kernel'):
        executor.read_pseudo(PseudoPath(), 3)


def fake_dispatch(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(executor, 'LOCK_PATH', tmp_path/'GPU.lock')
    runtime = tmp_path/'runtime'
    runtime.mkdir()
    monkeypatch.setattr(executor, 'validate_admission', lambda *args: 'a' * 64)
    monkeypatch.setattr(executor, 'validate_runtime', lambda *args: 'b' * 64)
    monkeypatch.setattr(executor, 'device_identity', lambda: {'synthetic': True})
    monkeypatch.setattr(executor, 'policy_identity', lambda *args: {'synthetic_identity': True})
    monkeypatch.setattr(executor, 'validate_gate', lambda *args: 'c' * 64)
    process = subprocess.CompletedProcess([], 0)
    process.stdout, process.stderr = io.BytesIO(), io.BytesIO()
    process.wait = lambda **kwargs: 0
    process.kill = lambda: calls.append('kill-client')

    def run(arguments, **kwargs):
        calls.append('preflight')
        return subprocess.CompletedProcess(arguments, 1, 'LoadState=not-found\n', '')

    def popen(*args, **kwargs):
        calls.append('launch')
        return process

    document = measurements()
    monkeypatch.setattr(executor.subprocess, 'run', run)
    monkeypatch.setattr(executor.subprocess, 'Popen', popen)
    monkeypatch.setattr(executor, 'stop_owned', lambda *args: calls.append('stop'))
    monkeypatch.setattr(executor, 'capture', lambda *args, **kwargs: dict(
        stdout=json.dumps(document).encode(), stderr=b'', returncode=0,
        limit_reason=None, teardown_error=None))
    options = dict(spool=tmp_path/'spool', runtime_root=runtime,
        admission_path=tmp_path/'admission.json', gate_path=tmp_path/'gate.json')
    write_json(options['admission_path'], dict(observed_unix=time.time()+10))
    return options, process, calls


def test_mocked_dispatch_preserves_raw_receipts_and_no_replay(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)
    raw = raw_request()
    result = executor.run_request(raw, **options)
    root = options['spool']/executor.parse_request(raw)['request_id']
    assert result['status'] == 'CORRECT'
    assert result['origin']['child_generated'] is False
    assert result['gpu_context_teardown_verified'] is False
    assert result['requires_fresh_Main_census_before_next_job'] is True
    assert result['speedup_claim_authorized'] is False
    assert (root/'REQUEST.json').read_bytes() == raw
    assert (root/'STDERR.bin').read_bytes() == b''
    assert executor.validate_measurements((root/'STDOUT.bin').read_bytes())['correctness_verified'] is True
    assert json.loads((root/'RESULT.json').read_bytes()) == result
    assert (root/'input'/'candidate.py').stat().st_mode & 0o777 == 0o444
    assert process.stdout.closed and process.stderr.closed
    with pytest.raises(FileExistsError):
        executor.run_request(raw, **options)
    assert calls == ['preflight', 'launch', 'stop']


def test_stale_census_after_previous_job_blocks_another_request(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)
    executor.run_request(raw_request(), **options)
    write_json(options['admission_path'], dict(observed_unix=0))
    with pytest.raises(ValueError, match='new_Main_census'):
        executor.run_request(raw_request('# distinct request\n' + executor.EXAMPLE_SOURCE), **options)
    assert calls == ['preflight', 'launch', 'stop']


def test_gate_rejection_never_reaches_launch(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)

    def reject(*args):
        raise ValueError('unproven GPU gate')

    monkeypatch.setattr(executor, 'validate_gate', reject)
    with pytest.raises(ValueError, match='unproven GPU gate'):
        executor.run_request(raw_request(), **options)
    assert calls == []
    assert not options['spool'].exists()


def test_preflight_failure_never_stops_existing_unit(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(executor.subprocess, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess([], 0, 'LoadState=loaded\n', ''))
    result = executor.run_request(raw_request(), **options)
    assert result['status'] == 'DISPATCH_FAILED_NO_RETRY'
    assert result['launch_attempted'] is False
    assert calls == []


@pytest.mark.parametrize('reason', ['OUTPUT_LIMIT', 'TIMEOUT'])
def test_limits_keep_raw_partial_output_without_success(monkeypatch, tmp_path, reason):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)
    monkeypatch.setattr(executor, 'capture', lambda *args, **kwargs: dict(stdout=b'partial',
        stderr=b'partial-error', returncode=1, limit_reason=reason, teardown_error=None))
    result = executor.run_request(raw_request(), **options)
    assert result['status'] == reason
    root = options['spool']/result['request_id']
    assert (root/'STDOUT.bin').read_bytes() == b'partial'
    assert (root/'STDERR.bin').read_bytes() == b'partial-error'
    assert calls == ['preflight', 'launch', 'stop']


def test_capture_exception_has_owned_cleanup_and_error_receipt(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)

    def fail(*args, **kwargs):
        raise OSError('synthetic pipe failure')

    monkeypatch.setattr(executor, 'capture', fail)
    result = executor.run_request(raw_request(), **options)
    assert result['status'] == 'DISPATCH_FAILED_NO_RETRY'
    assert process.stdout.closed and process.stderr.closed
    assert calls == ['preflight', 'launch', 'stop']
    assert (options['spool']/result['request_id']/'RESULT.json').is_file()


def test_client_timeout_failure_still_preserves_receipt(monkeypatch, tmp_path):
    options, process, calls = fake_dispatch(monkeypatch, tmp_path)

    def wait(**kwargs):
        raise subprocess.TimeoutExpired('synthetic-client', 5)

    process.wait = wait
    result = executor.run_request(raw_request(), **options)
    assert result['status'] == 'TEARDOWN_UNVERIFIED'
    assert result['client_still_running'] is True
    assert calls == ['preflight', 'launch', 'stop', 'kill-client']
    assert (options['spool']/result['request_id']/'RESULT.json').is_file()


@pytest.mark.parametrize('source', [
    'import os\n' + executor.EXAMPLE_SOURCE,
    executor.EXAMPLE_SOURCE + '\nprint("forged measurements")\n',
    executor.EXAMPLE_SOURCE.replace('@triton.jit', '@triton.jit()'),
    executor.EXAMPLE_SOURCE.replace('@triton.jit', '@evil'),
    executor.EXAMPLE_SOURCE.replace('BLOCK: tl.constexpr', 'BLOCK: __import__("os")'),
    executor.EXAMPLE_SOURCE.replace('left, right, output,', 'left=print("bad"), right=None, output=None,'),
    executor.EXAMPLE_SOURCE.replace('result = ', 'import os\n    result = '),
    executor.EXAMPLE_SOURCE.replace('result = ', 'tl = evil\n    result = '),
    executor.EXAMPLE_SOURCE.replace('result = ', 'offsets = offsets + 1\n    result = '),
    executor.EXAMPLE_SOURCE.replace('result = ', 'mask = True\n    result = '),
    executor.EXAMPLE_SOURCE.replace('result = ', 'left = output\n    result = '),
    executor.EXAMPLE_SOURCE.replace('left + offsets', 'left + offsets + 1'),
    executor.EXAMPLE_SOURCE.replace('output + offsets', 'left + offsets'),
    executor.EXAMPLE_SOURCE.replace('mask=mask', 'mask=True'),
    executor.EXAMPLE_SOURCE.replace('mask=mask', '**mask'),
    executor.EXAMPLE_SOURCE.replace('mask=mask', 'mask=~mask'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', 'tl.__dict__["load"](left)'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', 'tl.inline_asm_elementwise("evil")'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', 'left.__class__'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', '__import__("torch").cuda.Event()'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', '(lambda: 1)()'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', '[item for item in range(10)]'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', '2 ** 65536'),
    executor.EXAMPLE_SOURCE.replace('tl.load(left + offsets, mask=mask)', '(result := 1)'),
    executor.EXAMPLE_SOURCE.replace('result = ', 'while True: pass\n    result = '),
    executor.EXAMPLE_SOURCE.replace('result = ', 'global tl\n    result = '),
    executor.EXAMPLE_SOURCE.replace('tl.store(output + offsets, result, mask=mask)', 'return result'),
    executor.EXAMPLE_SOURCE.replace('tl.store(output + offsets, result, mask=mask)', 'print(result)'),
])
def test_arbitrary_host_code_escapes_and_unbounded_memory_rejected(source):
    with pytest.raises(ValueError):
        executor.validate_kernel_source(source)


def test_bounded_kernel_canonicalization_preserves_ast():
    result = executor.validate_kernel_source(executor.EXAMPLE_SOURCE)
    again = executor.validate_kernel_source(result['canonical_source'])
    assert result['ast_sha256'] == again['ast_sha256']
    assert 'import ' not in result['canonical_source']
    assert 'launch(' not in result['canonical_source']


def test_trusted_driver_not_candidate_owns_launch_timing_and_output():
    assert 'candidate.launch' not in executor.HARNESS
    assert 'candidate.add_kernel[' in executor.HARNESS
    assert "'/input/kernel.py'" in executor.HARNESS
    assert "__builtins__={}" in executor.HARNESS
    assert "'/input/candidate.py'" not in executor.HARNESS


@pytest.mark.parametrize('raw', ['DeviceAllow=/dev/nvidia1 rw\nDeviceAllow=/dev/null rw\n',
    'DeviceAllow=/dev/nvidia1 rw /dev/null rw\n',
    'DeviceAllow=/dev/nvidia1 rw\n/dev/null rw\n'])
def test_repeated_or_multiline_device_allow_evidence_preserved(raw):
    properties, rules = executor.unit_properties(raw)
    assert set(rules) == {('/dev/nvidia1','rw'),('/dev/null','rw')}


@pytest.mark.parametrize('mode', list(executor.RESOURCE_PROBES))
def test_fixed_trusted_resource_probe_syntax(mode):
    compile(executor.RESOURCE_PROBES[mode], '<fixed-trusted-probe>', 'exec')


def test_boundary_probe_uses_only_assigned_and_nonphysical_fixture():
    source = executor.BOUNDARY_PROBE.replace('__OUTSIDE__', repr('/synthetic/canary')).replace('__PEER__', '1')
    compile(source, '<fixed-trusted-boundary>', 'exec')
    assert 'denied_gpu_fixture' in source
    assert "'/dev/nvidia1'" in source
    assert '/dev/nvidia0' not in source and '/dev/nvidia2' not in source
