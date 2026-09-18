"""Exact legacy R133 parent-only custody; no learner signals or policy changes."""

import argparse
import ast
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
INDEX = REPOSITORY / 'research_loop/workers/r167_parent_policy_candidates_20260917/R154_ATTENTION_V2/INDEX.json'
INDEX_SHA = 'ad3e80d1a29fe7187fa2b77d30fa3397a5b8d38f7b845ec9a865f3182c24f4ba'
POLICY_SHA = '2874e7eb436459c207f48c218a267e86e3877d270aba830e3e465c1db382deee'
BRANCHES = ('NODE3_4_CREATIVE_FREE_SPARSE2', 'NODE3_7_CREATIVE_SELECT_SPARSE3',
    'NODE3_3_BRAIN_GUIDED_SPARSE2', 'CREATIVE_REREAD_SPARSE2_EXPLORATORY_EDITORIAL',
    'SUPPORT_PERSISTENT', 'BRAIN_PERSISTENT', 'RUN1_R138_SPARSE3', 'PILOT_R138_SPARSE2')
SOURCE_HASHES = ('c39f8dc61a01fccf7502f8d0b8a15b6cfdb5253f92f2b898fd63d3e6e41e8147',
    'cc5599a8308c35c044720d4d8c9d988a5fcfdae25daa71cbc9b2c1f46de6658e')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path, limit=16 * 1024 * 1024):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'bounded_regular_input')
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
    current = os.stat(path, follow_symlinks=False)
    require(len(raw) == before.st_size and len({(item.st_dev, item.st_ino, item.st_size,
        item.st_mtime_ns, item.st_ctime_ns) for item in (before, after, current)}) == 1, 'input_changed')
    return raw


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    return dict(path=str(Path(path).absolute()), sha256=digest(read(path)))


def bound(reference):
    raw = read(reference['path'])
    require(digest(raw) == reference['sha256'], 'exact_input_pin')
    return raw


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    root = Path('/proc') / str(pid)
    first = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    raw = (root / 'cmdline').read_bytes()
    second = (root / 'stat').read_text().rsplit(')', 1)[1].split()
    require(first[19] == second[19] and len(raw) < 65536, 'stable_parent_identity')
    return dict(pid=pid, start_ticks=first[19], argv=raw.rstrip(b'\0').decode().split('\0'),
        state=second[0], cwd=str((root / 'cwd').resolve()), uid=root.stat().st_uid)


def verify_identity(binding, observed):
    require(binding['branch'] in BRANCHES, 'scoped_branch_only')
    expected = binding['parent']
    require(all(observed[key] == expected[key] for key in ('pid', 'start_ticks', 'argv', 'cwd', 'uid')),
        'exact_parent_identity')
    require(observed['state'] not in ('Z', 'X'), 'parent_live')
    argv = observed['argv']
    if binding['branch'] in ('RUN1_R138_SPARSE3', 'PILOT_R138_SPARSE2'):
        require(binding['original_source']['path'] in argv and 'R157_AST_EQUIVALENCE' in binding,
            'exact_protected_wrapper')
    else:
        require('-m' in argv and argv[argv.index('-m') + 1] == 'gpu.orch_r133_programme_parent',
            'programme_parent_only')
    require(argv[argv.index('--config') + 1] == binding['original_config']['path']
        and argv[argv.index('--output') + 1] == binding['old_output'], 'exact_parent_paths')


def equivalent(original, wrapper):
    def functions(raw):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(raw).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    source, old = functions(original), functions(wrapper)
    require(set(source) <= set(old), 'all_original_functions_present')
    mismatches = [name for name in source if source[name] != old[name]]
    require(mismatches == ['serve'], 'only_protected_serve_differs')
    return dict(equal_functions=sorted(set(source) - {'serve'}), differing_functions=mismatches)


def ledger(output, config):
    root = Path(output)
    started_raw = read(root / 'STARTED.json')
    started = json.loads(started_raw)
    require(started['branch'] == config['branch'] and started['programme'] == config['programme'],
        'same_predecessor_branch')
    clock = 'request_count' if config.get('schedule_on') == 'request' else 'response_count'
    cursor = config.get('start_after_' + clock, 0)
    attempts = sorted(root.glob('parent_*'))
    require(len(attempts) <= 10000, 'bounded_attempts')
    pins, pending, statuses = {}, [], {}
    total = 0
    for directory in attempts:
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt')
        source_raw, result_raw = read(directory / 'SOURCE.json'), read(directory / 'RESULT.json')
        source, result = json.loads(source_raw), json.loads(result_raw)
        require(result['status'] in ('PUBLISHED', 'SILENT'), 'uncertain_result_defer')
        require(result['branch'] == config['branch'] and result['programme'] == config['programme']
            and result['source_head_sha256'] == source['head_sha256']
            and result['source_response_count'] == source['response_count']
            and result['schedule_count'] == source[clock]
            and result['finished_unix'] >= result['started_unix'], 'settled_bound_result')
        intent = json.loads(read(directory / 'DISPATCH_INTENT.json'))
        require(intent['source_sha256'] == digest(source_raw)
            and intent['schedule_count'] == source[clock], 'reserved_source_binding')
        require(type(source[clock]) is int and source[clock] >= cursor, 'monotonic_reserved_cursor')
        cursor = source[clock]
        statuses[result['status']] = statuses.get(result['status'], 0) + 1
        if result['status'] == 'PUBLISHED':
            publication = result['inbox_publication']
            require(publication['path'] == config['root'] + '/stream/inbox/' + publication['id'] + '.json'
                and len(publication['sha256']) == 64, 'exact_publication_root')
            if not (directory / 'DELIVERED.json').exists():
                pending.append(publication['id'])
        files = list(directory.iterdir())
        require(len(files) <= 128, 'bounded_attempt_files')
        for path in files:
            raw = read(path)
            total += len(raw)
            require(total <= 512 * 1024 * 1024, 'bounded_ledger')
            pins[str(path.relative_to(root))] = digest(raw)
    return dict(clock=clock, reserved=cursor, started_sha256=digest(started_raw),
        files=pins, pending_inbox_ids=pending, attempts=len(attempts), statuses=statuses)


def successor_config(old, candidate, previous, output):
    changed = {key for key in set(old) | set(candidate) if old.get(key) != candidate.get(key)}
    require(changed == {'principles_path', 'principles_sha256'}, 'principles_only_candidate')
    updated = dict(candidate, predecessor_output=output,
        predecessor_started_sha256=previous['started_sha256'])
    updated['start_after_' + previous['clock']] = previous['reserved']
    require(updated['hard_end_unix'] == old['hard_end_unix'], 'unchanged_wall')
    return updated


class Operations:
    identity = staticmethod(identity)
    open = staticmethod(os.pidfd_open)
    close = staticmethod(os.close)
    signal = staticmethod(signal.pidfd_send_signal)

    @staticmethod
    def childless_stopped(pid):
        tasks = list((Path('/proc') / str(pid) / 'task').iterdir())
        require(0 < len(tasks) <= 128, 'bounded_parent_tasks')
        for task in tasks:
            require((task / 'stat').read_text().rsplit(')', 1)[1].split()[0] in ('T', 't'),
                'all_parent_tasks_stopped')
            require(not (task / 'children').read_text().strip(), 'provider_or_publish_child_defer')

    @staticmethod
    def exited(descriptor):
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        return bool(poller.poll(5000))


@contextmanager
def quiesce(binding, operations=None):
    operations = operations or Operations()
    observed = operations.identity(binding['parent']['pid'])
    verify_identity(binding, observed)
    require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
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


def native_check(binding):
    result = subprocess.run(['bash', str(REPOSITORY / 'gpu' / (binding['node'] + '_ssh.sh')),
        'python3 -'], input=read(HERE / 'remote_metadata.py'), capture_output=True, timeout=45)
    require(result.returncode == 0, 'native_census_failed')
    census = json.loads(result.stdout)
    matches = [item for item in census['natives'] if any(plan.get('root') == binding['root']
        for plan in item['plans']) and item['state'] not in ('Z', 'X')]
    require(len(matches) == 1 and all(matches[0][key] == binding['native'][key]
        for key in ('pid', 'start_ticks', 'argv_sha256', 'plans')), 'exact_live_native_required')
    return census


def gate_window(go, now):
    require(go['approved_by'] == 'Main' and go['action'] == 'R167_EXACT_PARENT_ONLY_HANDOFF'
        and go['not_before_unix'] <= now < go['expires_unix']
        and 0 < go['expires_unix'] - go['not_before_unix'] <= 900, 'scoped_current_Main_GO')


def cpu_preflight(binding, config_path):
    script = ('import json; from gpu import orch_r133_programme_parent as parent; '
        'config=json.load(open(__import__("sys").argv[1])); parent.validate(config); '
        'print(json.dumps({"cursor":parent.resume_cursor(config),"model":parent.STRONG}))')
    result = subprocess.run([binding['python'], '-B', '-c', script, str(config_path)],
        cwd=binding['successor_cwd'], env=dict(os.environ, PYTHONPATH=binding['successor_cwd'],
            PYTHONDONTWRITEBYTECODE='1'), capture_output=True, timeout=15)
    require(result.returncode == 0, 'original_entrypoint_CPU_preflight_failed')
    return json.loads(result.stdout)


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
                previous = ledger(binding['old_output'], old)
                config = successor_config(old, candidate, previous, binding['old_output'])
                require(not (home / 'parent').exists(), 'new_output_only')
                write(home / 'PREDECESSOR.json', previous)
                write(home / 'CONFIG.json', config)
                preflight = cpu_preflight(binding, home / 'CONFIG.json')
                require(preflight['cursor'] == previous['reserved'], 'original_cursor_exact')
                write(home / 'CPU_PREFLIGHT.json', preflight)
                command = [binding['python'], '-B', '-m', 'gpu.orch_r133_programme_parent',
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
    args = parser.parse_args()
    execute(args.go, args.go_sha256)
