"""R167 exact A100 parent custody using Main's isolated startup-only adapter."""

import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import legacy_takeover as legacy


ADAPTER_PATH = legacy.REPOSITORY / 'research_loop/workers/r167_a100_parent_rollout/resume_source.py'
ADAPTER_SHA = '6d10737d00bd15db078c5b10ee0ea93ac36de4ce9f65b1207dfdca170443c01b'
SPEC = importlib.util.spec_from_file_location('main_a100_adapter', ADAPTER_PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)
ALLOWED = ('a100_6_classroom_creative', 'a100_3_teach_perception', 'a100_5_classroom_brain',
    'a100_7_classroom_support', 'a100_2_teach_replay', 'a100_4_teach_parenting')


def ledger(output, config, source_sha256):
    legacy.require(source_sha256 == adapter.SOURCE_SHA256, 'actual_cursorless_controlflow')
    root = Path(output)
    started = json.loads(legacy.read(root / 'STARTED.json'))
    legacy.require(started['branch'] == config['branch'] and started['programme'] == config['programme'],
        'same_original_parent')
    directories = sorted(root.glob('parent_*'))
    legacy.require(len(directories) <= 10000, 'bounded_attempts')
    reserved, total = 0, 0
    files, statuses, pending = {}, {}, []
    for directory in directories:
        legacy.require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt')
        source = json.loads(legacy.read(directory / 'SOURCE.json'))
        result = json.loads(legacy.read(directory / 'RESULT.json'))
        legacy.require(result['branch'] == config['branch'] and result['programme'] == config['programme']
            and result['source_response_count'] == source['response_count']
            and result['source_head_sha256'] == source['head_sha256']
            and result['finished_unix'] >= result['started_unix'], 'bound_finished_legacy_result')
        if result['status'] not in ('PUBLISHED', 'SILENT'):
            legacy.require(result['status'] == 'MISSING'
                and result.get('error_code') == 'parent_call_or_delivery_failed'
                and isinstance(result.get('error_type'), str) and bool(result['error_type'])
                and not any(key in result for key in ('sent_unix', 'inbox_publication', 'response')),
                'uncertain_publication_defer')
        legacy.require(type(source['response_count']) is int and source['response_count'] >= reserved,
            'monotonic_reserved_source')
        reserved = source['response_count']
        statuses[result['status']] = statuses.get(result['status'], 0) + 1
        if result['status'] == 'PUBLISHED':
            publication = result['inbox_publication']
            legacy.require(publication['path'] == config['root'] + '/stream/inbox/' + publication['id'] + '.json'
                and len(publication['sha256']) == 64, 'same_root_publication')
            if not (directory / 'DELIVERED.json').exists():
                pending.append(publication['id'])
        entries = list(directory.iterdir())
        legacy.require(len(entries) <= 128, 'bounded_attempt_files')
        for path in entries:
            raw = legacy.read(path)
            total += len(raw)
            legacy.require(total <= 512 * 1024 * 1024, 'bounded_parent_ledger')
            files[str(path.relative_to(root))] = legacy.digest(raw)
    return dict(reserved_response_count=reserved, started_sha256=legacy.ref(root / 'STARTED.json')['sha256'],
        files=files, pending_inbox_ids=pending, statuses=statuses, attempts=len(directories),
        legacy_no_dispatch_intent=True)


def verify(binding, observed):
    legacy.require(binding['branch'] in ALLOWED and binding['node'] == 'a100'
        and binding['original_source']['sha256'] == adapter.SOURCE_SHA256, 'exact_A100_parent_scope')
    legacy.require(all(observed[key] == binding['parent'][key]
        for key in ('pid', 'start_ticks', 'argv', 'cwd', 'uid')), 'exact_parent_identity')
    argv = observed['argv']
    legacy.require(observed['state'] not in ('Z', 'X') and '-m' in argv
        and argv[argv.index('-m') + 1] == 'gpu.orch_r133_programme_parent'
        and argv[argv.index('--config') + 1] == binding['original_config']['path']
        and argv[argv.index('--output') + 1] == binding['old_output'], 'original_programme_parent_only')


def wait_quiet(binding, deadline, operations=None):
    operations = operations or legacy.Operations()
    while time.time() < deadline:
        verify(binding, operations.identity(binding['parent']['pid']))
        tasks = list((Path('/proc') / str(binding['parent']['pid']) / 'task').iterdir())
        legacy.require(0 < len(tasks) <= 128, 'bounded_parent_tasks')
        if all(not (task / 'children').read_text().strip() for task in tasks):
            return
        time.sleep(0.05)
    raise ValueError('quiet_window_not_observed_no_signal')


@contextmanager
def quiesce(binding, operations=None):
    operations = operations or legacy.Operations()
    observed = operations.identity(binding['parent']['pid'])
    verify(binding, observed)
    legacy.require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    descriptor = operations.open(observed['pid'])
    stopped = False
    try:
        verify(binding, operations.identity(observed['pid']))
        operations.signal(descriptor, signal.SIGSTOP)
        stopped = True
        for attempt in range(100):
            if operations.identity(observed['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        operations.childless_stopped(observed['pid'])
        verify(binding, operations.identity(observed['pid']))
        yield descriptor, operations
    finally:
        if stopped:
            try:
                operations.signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        operations.close(descriptor)


def receiving_cpu(binding, directory):
    script = '''import json,runpy,sys,tempfile
from pathlib import Path
source,config_path,repository,cursor=sys.argv[1:]
namespace=runpy.run_path(source,run_name='r167_cpu_only')
namespace['serve'].__globals__['snapshot']=lambda *args:dict(response_count=int(cursor),consumed_inbox={})
def forbidden(*args,**kwargs): raise AssertionError('provider_or_publication_forbidden')
namespace['serve'].__globals__['strong']=forbidden
namespace['serve'].__globals__['publish']=forbidden
with tempfile.TemporaryDirectory() as temporary:
 output=Path(temporary)/'parent'
 namespace['serve'](Path(config_path),Path(repository),output,once=True)
 assert (output/'STARTED.json').exists() and not list(output.glob('parent_*'))
print(json.dumps(dict(status='PASS',original_imported_source=True,provider_calls=0,reserved_cursor=int(cursor))))
'''
    result = subprocess.run([binding['python'], '-B', '-c', script,
        str(directory / 'PARENT.py'), str(directory / 'CONFIG.json'), str(legacy.REPOSITORY),
        str(binding['resume_binding']['reserved_response_count'])], cwd=binding['parent']['cwd'],
        env=dict(os.environ, PYTHONPATH=binding['parent']['cwd'], PYTHONDONTWRITEBYTECODE='1'),
        capture_output=True, timeout=15)
    legacy.require(result.returncode == 0, 'actual_generated_source_CPU_failed')
    return json.loads(result.stdout)


def execute(go_path, go_sha):
    go = json.loads(legacy.bound(dict(path=str(go_path), sha256=go_sha)))
    legacy.gate_window(go, time.time())
    binding = json.loads(legacy.bound(go['binding']))
    home = legacy.HERE / binding['candidate']
    legacy.require(Path(go['binding']['path']).resolve() == home / 'BINDING.json', 'fixed_candidate')
    legacy.require(legacy.ref(__file__)['sha256'] == go['operator_sha256'], 'tested_A100_operator')
    cpu = json.loads(legacy.bound(go['cpu_gate']))
    legacy.require(cpu['status'] == 'PASS' and cpu['operator_sha256'] == go['operator_sha256'], 'CPU_gate')
    for pin in binding['pins']:
        legacy.bound(pin)
    legacy.require(bool(os.environ.get('NVIDIA_API_KEY')), 'existing_provider_environment')
    native = legacy.native_check(binding)
    legacy.write(home / 'EXECUTION_INTENT.json', dict(go=legacy.ref(go_path), native=native,
        observed_unix=time.time()))
    with (home / 'OPERATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        legacy.require(not (home / 'PARENT_TERMINATION_ONCE.json').exists(), 'no_termination_retry')
        try:
            wait_quiet(binding, min(time.time() + 30, go['expires_unix']))
            with quiesce(binding) as (descriptor, operations):
                for pin in binding['pins']:
                    legacy.bound(pin)
                old = json.loads(legacy.bound(binding['original_config']))
                previous = ledger(binding['old_output'], old, binding['original_source']['sha256'])
                legacy.require(previous['reserved_response_count'] == binding['resume_binding']['reserved_response_count']
                    and previous['started_sha256'] == binding['resume_binding']['started_sha256'],
                    'reserved_cursor_advanced_defer')
                legacy.write(home / 'PREDECESSOR.json', previous)
                legacy.require(not (home / 'parent').exists(), 'fresh_output')
                legacy.gate_window(go, time.time())
                operations.childless_stopped(binding['parent']['pid'])
                legacy.write(home / 'PARENT_TERMINATION_ONCE.json', dict(go_sha256=go_sha,
                    parent=binding['parent'], observed_unix=time.time()))
                operations.signal(descriptor, signal.SIGTERM)
                operations.signal(descriptor, signal.SIGCONT)
                legacy.require(operations.exited(descriptor), 'exit_unconfirmed_no_successor')
                legacy.write(home / 'PREDECESSOR_EXIT.json', dict(observed_unix=time.time(),
                    pid=binding['parent']['pid'], pidfd_exit_confirmed=True))
            for name, expected in previous['files'].items():
                legacy.require(legacy.digest(legacy.read(Path(binding['old_output']) / name)) == expected,
                    'original_attempts_preserved')
            command = [binding['python'], '-B', str(home / 'PARENT.py'), '--config', str(home / 'CONFIG.json'),
                '--repository', str(legacy.REPOSITORY), '--output', str(home / 'parent')]
            with (home / 'PARENT.log').open('xb') as log:
                process = subprocess.Popen(command, cwd=binding['parent']['cwd'],
                    env=dict(os.environ, PYTHONPATH=binding['parent']['cwd'], PYTHONDONTWRITEBYTECODE='1'),
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            legacy.write(home / 'SPAWNED.json', dict(pid=process.pid, command=command, observed_unix=time.time()))
            for attempt in range(50):
                if (home / 'parent/STARTED.json').exists() or process.poll() is not None:
                    break
                time.sleep(0.1)
            legacy.require(process.poll() is None and (home / 'parent/STARTED.json').exists(), 'successor_start_failed')
            started = json.loads(legacy.read(home / 'parent/STARTED.json'))
            legacy.require(started['pid'] == process.pid and started['config_sha256'] == legacy.ref(home / 'CONFIG.json')['sha256'],
                'actual_successor_receipt')
            legacy.write(home / 'RUNNING.json', dict(parent=legacy.identity(process.pid),
                started=legacy.ref(home / 'parent/STARTED.json'), observed_unix=time.time(),
                previous_pending_ids=previous['pending_inbox_ids']))
        except BaseException as error:
            legacy.write(home / 'REFUSAL.json', dict(error_type=type(error).__name__, reason=str(error),
                observed_unix=time.time(), termination_latch=(home / 'PARENT_TERMINATION_ONCE.json').exists()))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--go-sha256', required=True)
    arguments = parser.parse_args()
    execute(arguments.go, arguments.go_sha256)
