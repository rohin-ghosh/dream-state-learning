"""Exact three-parent node4 extension; no child or source mutation."""

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import legacy_takeover as legacy
from legacy_takeover import (HERE, REPOSITORY, INDEX, INDEX_SHA, SOURCE_HASHES, Operations,
    bound, digest, gate_window, identity, ledger, read, ref, require, successor_config, write)

COVERAGE = HERE / 'COVERAGE_20260917T0845Z.json'
COVERAGE_SHA = 'ed6996c2d442c103c7b05c1162b8ac60af3e0aba000ff8178cf1375e57b24e34'
SLOTS = {
    'r137_raw3_sparse3_free_socratic_seed1': ('gpu.orch_r136_node4_parent', 1399872, 2941297),
    'r137_kernel4_sparse2_free_coach': ('gpu.orch_r136_node4_parent', 716608, 3496993),
    'R158_MATCHED': ('gpu.orch_r133_programme_parent', 3603888, 530635),
}


def verify_identity(binding, observed):
    require(binding['branch'] in SLOTS and binding['node'] == 'a40r', 'exact_three_parent_scope')
    entrypoint, old_pid, native_pid = SLOTS[binding['branch']]
    require(binding['parent']['pid'] == old_pid and binding['native']['pid'] == native_pid,
        'only_authorized_original_parent_native')
    coverage = json.loads(bound(dict(path=str(COVERAGE), sha256=COVERAGE_SHA)))
    originals = [row for row in coverage['still_original_live_parented']
        if row['parent']['identity']['pid'] == old_pid]
    require(len(originals) == 1 and originals[0]['parent']['fields']['root'] == binding['root'],
        'exact_approved_live_root')
    require(all(binding['parent'][key] == originals[0]['parent']['identity'][key]
        for key in ('pid', 'start_ticks', 'argv', 'uid', 'cwd')), 'original_coverage_identity')
    require(all(observed[key] == binding['parent'][key]
        for key in ('pid', 'start_ticks', 'argv', 'uid', 'cwd')), 'exact_parent_identity')
    argv = observed['argv']
    require(observed['state'] not in ('Z', 'X') and '-m' in argv
        and argv[argv.index('-m') + 1] == entrypoint and binding['entrypoint'] == entrypoint
        and argv[argv.index('--config') + 1] == binding['original_config']['path']
        and argv[argv.index('--output') + 1] == binding['old_output'], 'exact_parent_runner')


def native_check(binding):
    result = subprocess.run(['bash', str(REPOSITORY / 'gpu/a40r_ssh.sh'), 'python3 -'],
        input=read(HERE / 'coverage_native_metadata.py'), capture_output=True, timeout=45)
    require(result.returncode == 0, 'native_census_failed')
    census = json.loads(result.stdout)
    require(census['hostname'] == '[REDACTED_HOST]', 'exact_node4_host')
    matches = [row for row in census['processes'] if 'native' in row['phases']
        and row['state'] not in ('Z', 'X') and any(document['fields'].get('root') == binding['root']
            for document in row['documents'])]
    require(len(matches) == 1 and all(matches[0][key] == binding['native'][key]
        for key in ('pid', 'start_ticks', 'argv_sha256', 'documents', 'entrypoints', 'phases')),
        'exact_live_native_required')
    return census


def cpu_preflight(binding, config_path):
    script = """
import hashlib, importlib, json, sys, tempfile
from pathlib import Path
runner = importlib.import_module(sys.argv[2])
parent = importlib.import_module('gpu.orch_r133_programme_parent')
config = json.load(open(sys.argv[1]))
runner.validate(config)
cursor = parent.resume_cursor(config)
def forbidden(*args, **kwargs):
    raise AssertionError('provider_or_publication_forbidden')
parent.strong = forbidden
parent.publish = forbidden
if hasattr(parent, 'transport_preflight'):
    parent.transport_preflight = lambda *args: {'CPU': 'NO_REMOTE_CALL'}
parent.snapshot = lambda *args: dict(record_count=0, response_count=0, request_count=0,
    consumed_inbox={}, boundaries=[], parent_consumptions=[])
with tempfile.TemporaryDirectory() as temporary:
    output = Path(temporary) / 'parent'
    runner.serve(Path(sys.argv[1]), Path(sys.argv[3]), output, once=True)
    started = json.loads((output / 'STARTED.json').read_text())
    assert not list(output.glob('parent_*'))
imports = [dict(path=str(Path(module.__file__).resolve()),
    sha256=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest())
    for name, module in sorted(sys.modules.items())
    if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None)]
print(json.dumps(dict(cursor=cursor, model=parent.STRONG, imports=imports,
    actual_startup=True, provider_calls=0, publications=0)))
"""
    result = subprocess.run([binding['python'], '-B', '-c', script, str(config_path),
        binding['entrypoint'], str(REPOSITORY)], cwd=binding['successor_cwd'],
        env=dict(os.environ, PYTHONPATH=binding['successor_cwd'], PYTHONDONTWRITEBYTECODE='1'),
        capture_output=True, timeout=20)
    require(result.returncode == 0, 'actual_runner_CPU_preflight_failed:' + result.stderr.decode()[-1500:])
    return json.loads(result.stdout)


@contextmanager
def quiesce(binding, operations=None):
    operations = operations or Operations()
    observed = operations.identity(binding['parent']['pid'])
    verify_identity(binding, observed)
    require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    if binding.get('quiet_window_wait_seconds') is not None:
        require(binding['quiet_window_wait_seconds'] == 30, 'bounded_quiet_wait_only')
        deadline = time.monotonic() + 30
        while not operations.children_absent(observed['pid']):
            require(time.monotonic() < deadline, 'quiet_window_not_observed_no_signal')
            verify_identity(binding, operations.identity(observed['pid']))
            time.sleep(0.05)
        verify_identity(binding, operations.identity(observed['pid']))
    descriptor = operations.open(observed['pid'])
    stopped = False
    try:
        verify_identity(binding, operations.identity(observed['pid']))
        operations.signal(descriptor, signal.SIGSTOP)
        stopped = True
        for attempt in range(100):
            if operations.identity(observed['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        operations.childless_stopped(observed['pid'])
        verify_identity(binding, operations.identity(observed['pid']))
        yield descriptor, operations
    finally:
        if stopped:
            try:
                operations.signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        operations.close(descriptor)


def execute(go_path, go_sha):
    go = json.loads(bound(dict(path=str(go_path), sha256=go_sha)))
    gate_window(go, time.time())
    binding = json.loads(bound(go['binding']))
    home = HERE / binding['candidate']
    require(Path(go['binding']['path']).resolve() == home / 'BINDING.json', 'fixed_candidate_binding')
    require(ref(__file__)['sha256'] == go['operator_sha256'], 'tested_operator_pin')
    cpu = json.loads(bound(go['cpu_gate']))
    require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == go['operator_sha256'], 'tested_CPU_gate')
    require(digest(read(INDEX)) == INDEX_SHA, 'exact_policy_index')
    if binding.get('previous_refusal'):
        refusal = json.loads(bound(binding['previous_refusal']))
        require(refusal['termination_latch'] is False, 'previous_attempt_never_terminated')
        previous_home = Path(binding['previous_refusal']['path']).parent
        require(not any((previous_home / name).exists() for name in
            ('PARENT_TERMINATION_ONCE.json', 'SPAWNED.json', 'RUNNING.json')), 'no_retry_of_terminated_parent')
    for reference in binding['pins']:
        bound(reference)
    old = json.loads(bound(binding['original_config']))
    candidate = json.loads(bound(binding['candidate_config']))
    require(old['branch'] == binding['branch'] and time.time() < old['hard_end_unix'], 'live_parent_wall')
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'existing_provider_environment_required')
    require(binding['successor_source']['sha256'] in SOURCE_HASHES, 'supported_unchanged_source')
    bound(binding['successor_source'])
    native = native_check(binding)
    write(home / 'EXECUTION_INTENT.json', dict(go=ref(go_path), native=native, observed_unix=time.time()))
    with (home / 'OPERATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (home / 'PARENT_TERMINATION_ONCE.json').exists(), 'no_termination_retry')
        try:
            with quiesce(binding) as (descriptor, operations):
                for reference in binding['pins']:
                    bound(reference)
                previous = ledger(binding['old_output'], old, binding['successor_source']['sha256'])
                config = successor_config(old, candidate, previous, binding['old_output'])
                require(not (home / 'parent').exists(), 'new_output_only')
                write(home / 'PREDECESSOR.json', previous)
                write(home / 'CONFIG.json', config)
                preflight = cpu_preflight(binding, home / 'CONFIG.json')
                require(preflight['cursor'] == previous['reserved'], 'original_cursor_exact')
                write(home / 'CPU_PREFLIGHT.json', preflight)
                command = [binding['python'], '-B', '-m', binding['entrypoint'],
                    '--config', str(home / 'CONFIG.json'), '--repository', str(REPOSITORY),
                    '--output', str(home / 'parent')]
                gate_window(go, time.time())
                operations.childless_stopped(binding['parent']['pid'])
                write(home / 'PARENT_TERMINATION_ONCE.json', dict(go_sha256=go_sha,
                    pid=binding['parent']['pid'], observed_unix=time.time(), command=command))
                operations.signal(descriptor, signal.SIGTERM)
                operations.signal(descriptor, signal.SIGCONT)
                require(operations.exited(descriptor), 'parent_exit_uncertain_no_successor')
                write(home / 'PREDECESSOR_EXIT.json', dict(pid=binding['parent']['pid'],
                    observed_unix=time.time(), pidfd_exit_confirmed=True))
            if binding.get('r157_lock'):
                with Path(binding['r157_lock']).open('r+') as prior_lock:
                    fcntl.flock(prior_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    write(home / 'R157_LOCK_RELEASED.json', dict(observed_unix=time.time()))
            for name, expected in previous['files'].items():
                require(digest(read(Path(binding['old_output']) / name)) == expected, 'old_attempts_preserved')
            for reference in binding['pins']:
                bound(reference)
            with (home / 'PARENT.log').open('xb') as log:
                process = subprocess.Popen(command, cwd=binding['successor_cwd'],
                    env=dict(os.environ, PYTHONPATH=binding['successor_cwd'], PYTHONDONTWRITEBYTECODE='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            write(home / 'SPAWNED.json', dict(pid=process.pid, observed_unix=time.time(), command=command))
            for attempt in range(50):
                if (home / 'parent/STARTED.json').exists() or process.poll() is not None:
                    break
                time.sleep(0.1)
            require(process.poll() is None and (home / 'parent/STARTED.json').exists(), 'successor_start_failed')
            started = json.loads(read(home / 'parent/STARTED.json'))
            require(started['pid'] == process.pid and started['config_sha256'] == ref(home / 'CONFIG.json')['sha256'],
                'actual_successor_receipt')
            write(home / 'RUNNING.json', dict(parent=identity(process.pid), started=ref(home / 'parent/STARTED.json'),
                observed_unix=time.time(), previous_pending_ids=previous['pending_inbox_ids']))
        except BaseException as error:
            write(home / 'REFUSAL.json', dict(error_type=type(error).__name__, reason=str(error),
                observed_unix=time.time(), termination_latch=(home / 'PARENT_TERMINATION_ONCE.json').exists()))
            raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--go-sha256', required=True)
    options = parser.parse_args()
    execute(options.go, options.go_sha256)
