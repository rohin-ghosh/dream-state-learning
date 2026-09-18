"""Exact-source raw3 auth refresh; no child signals or old-attempt writes."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tomllib


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
LEGACY = HERE.parent / 'r167_legacy_parent_rollout'
sys.path.insert(0, str(LEGACY))
import legacy_takeover as custody
import node4_rollout as original

MODEL = 'openai/openai/gpt-6-astra'
PREVIOUS = LEGACY / 'NODE4_1399872_attention_attempt1'
PARENT_SHA = 'c39f8dc61a01fccf7502f8d0b8a15b6cfdb5253f92f2b898fd63d3e6e41e8147'
ADAPTER_SHA = 'a908aa915805ac6d773dad680cd7addb051b5da51abb07da350b51983c1b66ad'
BRANCH = 'r137_raw3_sparse3_free_socratic_seed1'
ROOT = '/localhome/local-rohing/orch_r136_raw_parented_seed1_a40r3_20260916_attempt1/run1'


def verify(expected, observed):
    custody.require(expected['pid'] == 601818 and expected['start_ticks'] == '174199628',
                    'only_explicit_raw3_predecessor')
    custody.require(all(expected[key] == observed[key]
                        for key in ('pid', 'start_ticks', 'argv', 'cwd', 'uid')), 'exact_parent_identity')
    custody.require(observed['uid'] == os.getuid() and observed['state'] not in ('Z', 'X'), 'live_owned_parent')
    argv = observed['argv']
    custody.require(argv[argv.index('-m') + 1] == 'gpu.orch_r136_node4_parent'
                    and argv[argv.index('--config') + 1] == str(PREVIOUS / 'CONFIG.json')
                    and argv[argv.index('--output') + 1] == str(PREVIOUS / 'parent'), 'exact_raw3_runner')


def successor_config(config, ledger):
    custody.require(config['branch'] == BRANCH and config['root'] == ROOT
                    and config['node'] == 'a40r', 'exact_raw3_config')
    custody.require(config['hard_end_unix'] > time.time(), 'existing_wall_only')
    result = dict(config, predecessor_output=str(PREVIOUS / 'parent'),
                  predecessor_started_sha256=ledger['started_sha256'])
    result['start_after_' + ledger['clock']] = ledger['reserved']
    return result


def verify_files(ledger):
    for name, expected in ledger['files'].items():
        custody.require(custody.digest(custody.read(PREVIOUS / 'parent' / name)) == expected,
                        'all_old_attempt_bytes_preserved')
    custody.require(custody.ref(PREVIOUS / 'parent/STARTED.json')['sha256'] == ledger['started_sha256'],
                    'old_started_preserved')


@contextmanager
def paused(expected, operations=None):
    operations = operations or custody.Operations()
    observed = operations.identity(expected['pid'])
    verify(expected, observed)
    custody.require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    custody.require(operations.children_absent(expected['pid']), 'child_present_no_signal')
    descriptor = operations.open(expected['pid'])
    stopped = False
    try:
        verify(expected, operations.identity(expected['pid']))
        operations.signal(descriptor, signal.SIGSTOP)
        stopped = True
        for attempt in range(100):
            if operations.identity(expected['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        operations.childless_stopped(expected['pid'])
        verify(expected, operations.identity(expected['pid']))
        yield descriptor, operations
    finally:
        if stopped:
            try:
                operations.signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        operations.close(descriptor)


def inputs():
    prior = json.loads(custody.read(PREVIOUS / 'BINDING.json'))
    expected = json.loads(custody.read(PREVIOUS / 'RUNNING.json'))['parent']
    verify(expected, custody.identity(expected['pid']))
    config = json.loads(custody.read(PREVIOUS / 'CONFIG.json'))
    custody.require(config['parent_module_sha256'] == PARENT_SHA, 'exact_parent_source_contract')
    source_root = Path(expected['cwd'])
    custody.require(custody.ref(source_root / 'gpu/orch_r133_programme_parent.py')['sha256'] == PARENT_SHA,
                    'exact_original_parent_available')
    custody.require(custody.ref(source_root / 'gpu/orch_r136_node4_parent.py')['sha256'] == ADAPTER_SHA,
                    'exact_original_adapter_available')
    prior.update(parent=expected, old_output=str(PREVIOUS / 'parent'))
    return prior, expected, config


def prepare(home):
    home.mkdir(mode=0o700)
    binding, expected, config = inputs()
    native = original.native_check(binding)
    ledger = custody.ledger(PREVIOUS / 'parent', config, PARENT_SHA)
    custody.write(home / 'CONFIG.json', successor_config(config, ledger))
    preflight = original.cpu_preflight(binding, home / 'CONFIG.json')
    custody.require(preflight['cursor'] == ledger['reserved'] and preflight['model'] == MODEL,
                    'exact_CPU_cursor_and_canonical_model')
    pins = preflight['imports'] + [custody.ref(PREVIOUS / 'CONFIG.json'),
        custody.ref(config['principles_path']), custody.ref(config['programme_path']),
        custody.ref(__file__), custody.ref(original.__file__), custody.ref(custody.__file__),
        custody.ref(LEGACY / 'coverage_native_metadata.py'), custody.ref(REPOSITORY / 'gpu/a40r_ssh.sh')]
    custody.write(home / 'PREPARED.json', dict(binding=binding, expected=expected,
        config=custody.ref(home / 'CONFIG.json'), ledger=ledger, pins=pins,
        preflight=preflight, native=native, observed_unix=time.time(), no_signals=True))


def execute(home):
    gate = json.loads(custody.read(HERE / 'CPU_GATE.json'))
    custody.require(gate['status'] == 'PASS', 'CPU_gate_required')
    for reference in gate['pins']:
        custody.bound(reference)
    prepared = json.loads(custody.read(home / 'PREPARED.json'))
    for reference in prepared['pins']:
        custody.bound(reference)
    custody.bound(prepared['config'])
    custody.require(bool(os.environ.get('NVIDIA_API_KEY')), 'privately_sourced_credential_required')
    provider_config = tomllib.loads((Path.home() / '.codex/nvidia-astra.config.toml').read_text())
    custody.require(provider_config['model'] == MODEL, 'canonical_model_configuration_required')
    binding, expected, old = inputs()
    original.native_check(binding)
    custody.require(not (home / 'TERMINATION_ONCE.json').exists()
                    and not (home / 'parent').exists(), 'no_restart_or_termination_replay')
    command = [binding['python'], '-B', '-m', binding['entrypoint'], '--config', str(home / 'CONFIG.json'),
               '--repository', str(REPOSITORY), '--output', str(home / 'parent')]
    with (HERE / 'RAW3_OPERATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with paused(expected) as (descriptor, operations):
            ledger = custody.ledger(PREVIOUS / 'parent', old, PARENT_SHA)
            custody.require(ledger == prepared['ledger'], 'ledger_changed_prepare_fresh_attempt')
            for reference in prepared['pins']:
                custody.bound(reference)
            custody.bound(prepared['config'])
            custody.require(old['hard_end_unix'] > time.time(), 'no_deadline_extension')
            operations.childless_stopped(expected['pid'])
            custody.write(home / 'TERMINATION_ONCE.json', dict(parent=expected,
                authorization='USER_URGENT_NODE4_AUTH_REFRESH_20260917', observed_unix=time.time()))
            operations.signal(descriptor, signal.SIGTERM)
            operations.signal(descriptor, signal.SIGCONT)
            custody.require(operations.exited(descriptor), 'pidfd_exit_required_no_successor')
            custody.write(home / 'PREDECESSOR_EXIT.json', dict(pid=expected['pid'],
                pidfd_exit_confirmed=True, observed_unix=time.time()))
        verify_files(ledger)
        for reference in prepared['pins']:
            custody.bound(reference)
        environment = dict(os.environ, PYTHONPATH=binding['successor_cwd'], PYTHONDONTWRITEBYTECODE='1')
        with (home / 'PARENT.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=binding['successor_cwd'], env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        custody.write(home / 'SPAWNED.json', dict(pid=process.pid, command=command, observed_unix=time.time()))
        for attempt in range(100):
            if (home / 'parent/STARTED.json').exists() or process.poll() is not None:
                break
            time.sleep(0.1)
        custody.require(process.poll() is None, 'successor_live_required')
        started = json.loads(custody.read(home / 'parent/STARTED.json'))
        custody.require(started['pid'] == process.pid and started['model'] == MODEL
                        and started['config_sha256'] == prepared['config']['sha256'], 'bound_actual_startup')
        actual_environment = (Path('/proc') / str(process.pid) / 'environ').read_bytes().split(b'\0')
        inherited = b'NVIDIA_API_KEY='[REDACTED_SECRET]'NVIDIA_API_KEY'].encode() in actual_environment
        custody.require(inherited, 'new_credential_not_inherited')
        verify_files(ledger)
        custody.write(home / 'RUNNING.json', dict(parent=custody.identity(process.pid),
            started=custody.ref(home / 'parent/STARTED.json'), current_key_equality_verified=True,
            credential_values_recorded=False, model=MODEL, preserved_files=len(ledger['files']),
            pending_inbox_ids_untouched=ledger['pending_inbox_ids'], reserved_cursor=ledger['reserved'],
            no_child_signals=True, observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'execute'))
    parser.add_argument('--attempt', required=True)
    arguments = parser.parse_args()
    custody.require(arguments.attempt.isalnum(), 'simple_fresh_attempt_name')
    home = HERE / arguments.attempt
    try:
        (prepare if arguments.action == 'prepare' else execute)(home)
    except Exception as error:
        receipt = home / ('REFUSAL_' + str(time.time_ns()) + '.json')
        if home.exists():
            custody.write(receipt, dict(error_type=type(error).__name__,
                reason=str(error) if isinstance(error, ValueError) else 'operational_failure',
                termination_latched=(home / 'TERMINATION_ONCE.json').exists(), observed_unix=time.time()))
        print(json.dumps(dict(status='REFUSED', error_type=type(error).__name__, receipt=str(receipt))))
        raise SystemExit(1)
    print(json.dumps(dict(status=arguments.action.upper() + '_OK', attempt=str(home),
                         utc=datetime.now(timezone.utc).isoformat())))


if __name__ == '__main__':
    main()
