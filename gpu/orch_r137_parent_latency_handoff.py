"""Bounded, pidfd-only operational handoff and cumulative strict monitoring."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


MODULE = 'gpu.orch_r133_programme_parent'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def identity(spec):
    process = Path('/proc') / str(spec['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(int(fields[19]) == spec['start_ticks'], 'exact_start_ticks')
    command = (process / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
    expected = ['python3', '-B', '-m', MODULE, '--config', spec['old_config'],
                '--repository', spec['repository'], '--output', spec['old_output']]
    require(command == [value.encode() for value in expected], 'exact_parent_command')
    require((process / 'cwd').resolve() == Path(spec['old_source']).resolve(), 'exact_parent_source')
    require(sha(spec['old_config']) == spec['old_config_sha256'], 'pinned_old_config')
    started = Path(spec['old_output']) / 'STARTED.json'
    require(sha(started) == spec['old_started_sha256'], 'pinned_old_started')
    require(read(started)['pid'] == spec['pid'], 'recorded_parent_pid')
    return fields[0]


def reservation(output, config):
    require(config.get('schedule_on') == 'request', 'request_clock_only')
    cursor = config.get('start_after_request_count', 0)
    responses = config.get('start_after_response_count', 0)
    receipts = []
    for directory in sorted(Path(output).glob('parent_*')):
        require(directory.is_dir() and not directory.is_symlink(), 'regular_call_directory')
        source_path, result_path = directory / 'SOURCE.json', directory / 'RESULT.json'
        require(source_path.is_file() and result_path.is_file(), 'unfinished_parent_call')
        source, result = read(source_path), read(result_path)
        count = source['request_count']
        require(type(count) is int and count > cursor, 'strict_source_reservations')
        require(result.get('schedule_on') == 'request' and result.get('schedule_count') == count,
                'result_matches_source_reservation')
        require(result.get('source_response_count') == source['response_count']
                and result.get('source_head_sha256') == source['head_sha256'], 'result_matches_source_head')
        require(result.get('branch') == config['branch']
                and result.get('programme') == config['programme'], 'same_parent_result')
        require(result.get('status') in ('PUBLISHED', 'SILENT', 'MISSING')
                and result.get('finished_unix', 0) >= result.get('started_unix', float('inf')),
                'terminal_result_required')
        if result['status'] == 'PUBLISHED':
            require(bool(result.get('inbox_publication')), 'published_receipt_required')
        cursor = count
        responses = max(responses, source['response_count'])
        receipts.append(dict(directory=str(directory), request_count=count, status=result['status'],
                             source_sha256=sha(source_path), result_sha256=sha(result_path)))
    return dict(request_cursor=cursor, response_cursor=responses, receipts=receipts)


def successor_config(spec, state):
    config = read(spec['old_config'])
    config.update(poll_interval_seconds=0.25, start_after_request_count=state['request_cursor'],
                  start_after_response_count=state['response_cursor'],
                  predecessor_output=spec['old_output'],
                  predecessor_started_sha256=spec['old_started_sha256'])
    require(config.get('minimum_duration_seconds', 0) >= 3600, 'preserve_persistent_minimum')
    require(time.time() + config['minimum_duration_seconds'] < config['hard_end_unix'], 'unchanged_wall_room')
    return config


def paused_reservation(spec, descriptor):
    identity(spec)
    stopped = False
    try:
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        stopped = True
        deadline = time.monotonic() + 2
        while identity(spec) != 'T':
            require(time.monotonic() < deadline, 'pause_timeout')
            time.sleep(0.01)
        tasks = list((Path('/proc') / str(spec['pid']) / 'task').iterdir())
        require(len(tasks) == 1, 'single_parent_thread')
        require(not (tasks[0] / 'children').read_text().strip(), 'active_parent_subprocess')
        state = reservation(spec['old_output'], read(spec['old_config']))
        identity(spec)
        return state
    except BaseException:
        if stopped:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        raise


def handoff(spec):
    identity(spec)
    for key in ('new_output', 'new_config', 'new_log', 'receipt'):
        require(not Path(spec[key]).exists(), 'fresh_' + key)
    manifest = read(spec['source_receipt'])
    require(sha(spec['source_receipt']) == spec['source_receipt_sha256'], 'pinned_freeze_receipt')
    for relative, digest in manifest['files'].items():
        require(sha(Path(spec['new_source']) / relative) == digest, 'frozen_source_bytes')
    process = Path('/proc') / str(spec['pid'])
    environment = dict(os.fsdecode(entry).split('=', 1) for entry in
                       (process / 'environ').read_bytes().split(b'\0') if entry)
    environment.update(PYTHONPATH=spec['new_source'], PYTHONDONTWRITEBYTECODE='1')
    descriptor = os.pidfd_open(spec['pid'])
    paused = False
    retired = False
    try:
        deadline = time.monotonic() + spec.get('idle_wait_seconds', 90)
        while True:
            try:
                state = paused_reservation(spec, descriptor)
                paused = True
                break
            except ValueError as error:
                if str(error) not in ('active_parent_subprocess', 'unfinished_parent_call'):
                    raise
                require(time.monotonic() < deadline, 'bounded_idle_wait_exhausted_parent_resumed')
                time.sleep(0.5)
        config = successor_config(spec, state)
        write(spec['new_config'], config)
        Path(spec['new_config']).chmod(0o444)
        validation = subprocess.run(['python3', '-B', '-c',
            'import json,sys; from gpu.orch_r133_programme_parent import validate,resume_cursor; '
            'config=validate(json.load(open(sys.argv[1]))); resume_cursor(config)', spec['new_config']],
            cwd=spec['new_source'], env=environment, capture_output=True, timeout=10)
        require(validation.returncode == 0, 'frozen_successor_validation')
        require(reservation(spec['old_output'], read(spec['old_config'])) == state, 'stable_paused_reservation')
        identity(spec)
        with Path(spec['new_log']).open('xb') as log:
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            paused = False
            require(bool(select.select([descriptor], [], [], 3)[0]), 'parent_exit_not_verified')
            retired = True
            retired_unix = time.time()
            successor = subprocess.Popen(['python3', '-B', '-m', MODULE, '--config', spec['new_config'],
                '--repository', spec['repository'], '--output', spec['new_output']],
                cwd=spec['new_source'], env=environment, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(spec=spec, reservation=state, new_pid=successor.pid,
                       retired_unix=retired_unix, spawned_unix=time.time(), child_signals=False,
                       new_config_sha256=sha(spec['new_config']), no_reserved_requests_replayed=True)
        write(spec['receipt'], receipt)
        deadline = time.monotonic() + 10
        while not (Path(spec['new_output']) / 'STARTED.json').exists():
            require(successor.poll() is None, 'successor_exited_inspect_log')
            require(time.monotonic() < deadline, 'successor_start_timeout')
            time.sleep(0.05)
        require(read(Path(spec['new_output']) / 'STARTED.json')['pid'] == successor.pid, 'successor_started_identity')
        return receipt
    finally:
        if paused and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def cumulative_sample(item, config):
    from gpu.orch_r137_parent_monitor import boundary_coverage, parent_alive, publications_from_results, remote
    publications, segments = [], []
    first = read(item['segments'][0]['parent_config'])
    for segment in item['segments']:
        parent = read(segment['parent_config'])
        require(all(parent[key] == first[key] for key in ('branch', 'programme', 'node', 'root')),
                'same_monitored_lineage')
        require(sha(segment['parent_config']) == segment['config_sha256'], 'immutable_segment_config')
        output = Path(segment['parent_output'])
        publications.extend(publications_from_results(output, programme=parent['programme'], branch=parent['branch']))
        statuses = {}
        for path in output.glob('parent_*/RESULT.json'):
            status = read(path)['status']
            statuses[status] = statuses.get(status, 0) + 1
        segments.append(dict(**segment, parent_alive=parent_alive(output), call_statuses=statuses,
                             parent_started_unix=read(output / 'STARTED.json')['started_unix']))
    script = ('import json,hashlib; from pathlib import Path; '
        'from gpu.orch_r137_parent_exposure import snapshot; '
        'assert hashlib.sha256(Path(' + repr(config['remote_source'] + '/CPU_AND_SOURCE.json')
        + ').read_bytes()).hexdigest()==' + repr(config['remote_source_receipt_sha256']) + '; '
        'state=snapshot(' + repr(first['root']) + ',publications=' + repr(publications) + '); '
        'state.pop("events");state.pop("latest_request");print(json.dumps(state))')
    state = remote(config['repository'], dict(first, source_root=config['remote_source']), script)
    require(state['coverage_basis'] == 'verified_parent_REQUEST_exposure_not_registration', 'strict_exposure_only')
    coverage = boundary_coverage(state, first.get('start_after_response_count', 0))
    coverage['coverage_basis'] = state['coverage_basis']
    statuses = {}
    for segment in segments:
        for status, count in segment['call_statuses'].items():
            statuses[status] = statuses.get(status, 0) + count
    return dict(branch=first['branch'], parent_alive=segments[-1]['parent_alive'],
                parent_started_unix=segments[0]['parent_started_unix'], observed_unix=time.time(),
                coverage=coverage, call_statuses=statuses, segments=segments,
                request_count=state['request_count'], response_count=state['response_count'],
                verified_exposures=len(state['parent_exposures']), snapshot_state=state,
                publications=publications, historical_monitor_output=config['historical_monitor_output'],
                coverage_scope='union_old_and_new_publications_original_baseline_no_reset')


def monitor(config_path, output):
    from gpu.orch_r137_parent_monitor import status_text
    config = read(config_path)
    require(config['schema'] == 'R137_PARENT_LATENCY_MONITOR_V1'
            and 10 <= config['interval_seconds'] <= 300, 'bounded_monitor')
    output = Path(output)
    output.mkdir(exist_ok=False)
    write(output / 'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(), config_sha256=sha(config_path)))
    last_notebook = 0
    while time.time() < config['stop_after_unix']:
        rows = []
        for item in config['items']:
            try:
                rows.append(cumulative_sample(item, config))
            except Exception as error:
                rows.append(dict(branch=item['label'], error=type(error).__name__, observed_unix=time.time()))
        observed = time.time()
        receipt = output / ('AUDIT_' + str(time.time_ns()) + '.json')
        write(receipt, dict(observed_unix=observed, rows=rows))
        if observed - last_notebook >= 1800:
            text = status_text(rows, observed).replace('R137 exposure monitor', 'R137 cumulative latency monitor')
            text += 'Old + new publication union; original baselines and historical misses retained. '
            text += 'Audit: `' + str(receipt) + '`, SHA256 `' + sha(receipt) + '`.\n'
            descriptor = os.open(config['notebook'], os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC)
            try:
                raw = text.encode()
                require(os.write(descriptor, raw) == len(raw), 'complete_notebook_append')
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            last_notebook = observed
        time.sleep(min(config['interval_seconds'], max(0, config['stop_after_unix'] - time.time())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path)
    parser.add_argument('--monitor-config', type=Path)
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    if arguments.spec and not arguments.monitor_config:
        print(json.dumps(handoff(read(arguments.spec)), sort_keys=True))
    elif arguments.monitor_config and arguments.output and not arguments.spec:
        monitor(arguments.monitor_config, arguments.output)
    else:
        parser.error('choose handoff --spec OR --monitor-config with --output')
