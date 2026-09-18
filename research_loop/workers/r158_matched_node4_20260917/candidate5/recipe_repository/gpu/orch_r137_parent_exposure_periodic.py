"""Pinned R137 audit-only observer replacement; fixed scan budget and full errors."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import traceback


BUDGET = 512 * 1024 * 1024
POLICY = 'R137_PERIODIC_EXPOSURE_FIXED512_FULL_ERRORS_V1'
ADDED_KEYS = {'repair_policy', 'snapshot_max_bytes', 'diagnostic_path', 'diagnostic_sha256',
              'monitor_path', 'monitor_sha256', 'monitor_output', 'cpu_gate', 'cpu_gate_sha256',
              'predecessor', 'baseline_measurements', 'approval'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path = Path(path)
    partial = path.with_name(path.name + '.partial')
    with partial.open('xb') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def config_delta(old, new):
    require(set(new) == set(old) | ADDED_KEYS, 'only_approved_monitor_fields')
    original = {key: new[key] for key in old}
    original['helper_path'] = old['helper_path']
    require(original == old, 'original_monitor_semantics_unchanged')
    require(new['helper_path'] != old['helper_path'] and sha(new['helper_path']) == old['helper_sha256'], 'byte_identical_cumulative_helper_copy')
    require(new['repair_policy'] == POLICY and type(new['snapshot_max_bytes']) is int
            and new['snapshot_max_bytes'] == BUDGET, 'explicit_fixed512_no_automatic_increase')
    require(bool(new['approval'].strip()), 'Main_approved_monitor_repair')
    require(set(new['baseline_measurements']) == {item['label'] for item in old['items']}, 'same_lineages_and_baselines')


def identity(pid):
    root = Path('/proc') / str(pid)
    fields = (root / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, uid=root.stat().st_uid, parent=int(fields[1]), start_ticks=fields[19],
                argv=[os.fsdecode(part) for part in (root / 'cmdline').read_bytes().split(b'\0') if part],
                cwd=str((root / 'cwd').resolve()))


def observer_exited(expected):
    try:
        fields = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()
    except FileNotFoundError:
        return True
    return fields[0] == 'Z' and fields[19] == expected['start_ticks']


def childless_single_thread(pid):
    tasks = list((Path('/proc') / str(pid) / 'task').iterdir())
    return len(tasks) == 1 and not (tasks[0] / 'children').read_text().strip()


def idle(pid):
    root = Path('/proc') / str(pid)
    return ((root / 'stat').read_text().rsplit(') ', 1)[1].split()[0] == 'S'
            and (root / 'wchan').read_text().strip() == 'hrtimer_nanosleep' and childless_single_thread(pid))


def paused_clean(pid):
    root = Path('/proc') / str(pid)
    if (root / 'stat').read_text().rsplit(') ', 1)[1].split()[0] not in ('T', 't') or not childless_single_thread(pid):
        return False
    for path in (root / 'fdinfo').iterdir():
        if int(path.name) <= 2:
            continue
        flags = next(line.split()[1] for line in path.read_text().splitlines() if line.startswith('flags:'))
        if int(flags, 8) & os.O_ACCMODE:
            return False
    return True


def pause_if_idle(expected, descriptor):
    require(identity(expected['pid']) == expected, 'exact_observer_identity_before_pause')
    if not idle(expected['pid']):
        return False
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    try:
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            require(identity(expected['pid']) == expected, 'exact_paused_observer_identity')
            if paused_clean(expected['pid']):
                return True
            time.sleep(.01)
    except BaseException:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        raise
    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    return False


def validate(config_path):
    config = read(config_path)
    previous = config['predecessor']
    require(sha(previous['config_path']) == previous['config_sha256'], 'original_monitor_config_pin')
    old = read(previous['config_path'])
    config_delta(old, config)
    require(Path(config['monitor_path']).resolve() == Path(__file__).resolve()
            and sha(__file__) == config['monitor_sha256'], 'exact_new_monitor_source')
    require(sha(config['diagnostic_path']) == config['diagnostic_sha256'], 'exact_diagnostic_source')
    require(sha(config['cpu_gate']) == config['cpu_gate_sha256'], 'CPU_gate_receipt_pin')
    gate = read(config['cpu_gate'])
    require(gate['status'] == 'PASS' and gate['monitor_sha256'] == config['monitor_sha256']
            and gate['diagnostic_sha256'] == config['diagnostic_sha256']
            and sha(gate['log_path']) == gate['log_sha256'], 'tested_exact_monitor_bytes')
    require(sha(Path(previous['output']) / 'STARTED.json') == previous['started_sha256'], 'old_monitor_started_pin')
    started = read(Path(previous['output']) / 'STARTED.json')
    expected = previous['identity']
    require(started['pid'] == expected['pid'] and started['config_sha256'] == previous['config_sha256']
            and expected['uid'] == os.getuid() and expected['argv'] == ['python3', '-B', old['helper_path'],
                '--monitor-config', previous['config_path'], '--output', previous['output']], 'only_identified_old_audit_observer')
    require(sha(previous['audit_manifest']) == previous['audit_manifest_sha256'], 'historical_audit_prefix_pin')
    for item in config['items']:
        reference = config['baseline_measurements'][item['label']]
        require(sha(reference['path']) == reference['sha256'], 'baseline_measurement_pin')
        first = read(item['segments'][0]['parent_config'])
        require(reference['baseline'] == first.get('start_after_response_count', 0), 'original_parent_baseline')
    return config


def load_diagnostic(config):
    spec = importlib.util.spec_from_file_location('pinned_exposure_diagnostic', config['diagnostic_path'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(config_path):
    config = validate(config_path)
    output = Path(config_path).parent / 'PREPARE'
    output.mkdir()
    diagnostic = load_diagnostic(config)
    helper, monitor = diagnostic.frozen_runtime(config, output)
    original = monitor.remote
    try:
        for item in config['items']:
            directory = output / item['label']
            directory.mkdir()
            transport = diagnostic.OneShotTransport(directory, diagnostic.ROOTS[item['label']], config['remote_source'], max_bytes=BUDGET)
            monitor.remote = transport
            try:
                helper.cumulative_sample(item, config)
            except diagnostic.PreparedLocally:
                require(transport.executions == 0, 'no_remote_during_prepare')
            else:
                raise ValueError('expected_local_only_preparation')
    finally:
        monitor.remote = original
    receipt = dict(status='PREPARED_LOCAL_ONLY', config_sha256=sha(config_path), monitor_sha256=sha(__file__),
                   observed_unix=time.time(), remote_calls=0, parent_child_signals=0)
    write(Path(config_path).parent / 'PREPARED.json', receipt)
    return receipt


def sample_once(helper, monitor, diagnostic, config, item, directory, previous):
    directory.mkdir()
    transport = diagnostic.OneShotTransport(directory, diagnostic.ROOTS[item['label']], config['remote_source'],
        execute=True, clearance=config['approval'], max_bytes=BUDGET)
    original = monitor.remote
    monitor.remote = transport
    try:
        reference = config['baseline_measurements'][item['label']]
        require(sha(reference['path']) == reference['sha256'], 'immutable_baseline_during_periodic_pass')
        row = helper.cumulative_sample(item, config)
        require(transport.executions == 1, 'one_snapshot_per_lane_per_pass')
        historical = diagnostic.compare_historical(read(reference['path']), row, reference['baseline'])
        recent = diagnostic.compare_historical(previous, row, reference['baseline'])
        write(directory / 'COMPARISONS.json', dict(original_baseline=historical, previous_success=recent))
        write(directory / 'MEASUREMENT.json', row)
        return row
    except Exception as error:
        (directory / 'TRACEBACK.txt').write_text(traceback.format_exc())
        return dict(branch=item['label'], error=type(error).__name__, error_message=str(error),
            observed_unix=time.time(), diagnostic_directory=str(directory), traceback_sha256=sha(directory / 'TRACEBACK.txt'),
            transport_sha256=sha(directory / 'TRANSPORT.json') if (directory / 'TRANSPORT.json').exists() else None,
            measurement_available=False)
    finally:
        monitor.remote = original


def sleep_duration(config, observed):
    return min(config['interval_seconds'], max(0, config['stop_after_unix'] - observed))


def run(config_path):
    config = validate(config_path)
    namespace = Path(config_path).parent
    lock = (namespace / 'MONITOR.lock').open('a')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    retired = read(namespace / 'RETIRED.json')
    require(retired['config_sha256'] == sha(config_path)
            and retired['identity'] == config['predecessor']['identity'], 'exact_predecessor_retirement_receipt')
    require(observer_exited(retired['identity']), 'old_monitor_exited_before_successor')
    output = Path(config['monitor_output'])
    output.mkdir()
    diagnostic = load_diagnostic(config)
    helper, monitor = diagnostic.frozen_runtime(config, output)
    previous = {label: read(reference['path']) for label, reference in config['baseline_measurements'].items()}
    write(output / 'STARTED.json', dict(pid=os.getpid(), identity=identity(os.getpid()), started_unix=time.time(),
        config_sha256=sha(config_path), repair_policy=POLICY, retired_sha256=sha(namespace / 'RETIRED.json')))
    last_notebook = 0
    while time.time() < config['stop_after_unix']:
        require(sha(config_path) == retired['config_sha256'], 'running_config_immutable')
        pass_directory = output / ('PASS_' + str(time.time_ns()))
        pass_directory.mkdir()
        rows = []
        for item in config['items']:
            row = sample_once(helper, monitor, diagnostic, config, item, pass_directory / item['label'], previous[item['label']])
            rows.append(row)
            if 'error' not in row:
                previous[item['label']] = row
        observed = time.time()
        receipt = output / ('AUDIT_' + str(time.time_ns()) + '.json')
        write(receipt, dict(observed_unix=observed, rows=rows, diagnostic_directory=str(pass_directory), repair_policy=POLICY))
        if observed - last_notebook >= 1800:
            text = monitor.status_text(rows, observed).replace('R137 exposure monitor', 'R137 repaired cumulative latency monitor')
            text += 'Old + new publication union; original baselines and historical misses retained. '
            text += 'Fixed512MiB audit budget; strict exposure matching unchanged. '
            text += 'Audit: `' + str(receipt) + '`, SHA256 `' + sha(receipt) + '`.\n'
            descriptor = os.open(config['notebook'], os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC)
            try:
                raw = text.encode()
                require(os.write(descriptor, raw) == len(raw), 'complete_notebook_append')
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            last_notebook = observed
        time.sleep(sleep_duration(config, time.time()))
    write(output / 'FINISHED.json', dict(finished_unix=time.time(), stop_after_unix=config['stop_after_unix']))
    lock.close()


def handoff(config_path):
    config = validate(config_path)
    namespace = Path(config_path).parent
    prepared = read(namespace / 'PREPARED.json')
    require(prepared['config_sha256'] == sha(config_path) and prepared['monitor_sha256'] == sha(__file__), 'staged_before_pause')
    diagnostic = load_diagnostic(config)
    diagnostic.verify_local_source(Path(config['monitor_source']), read(Path(config['monitor_source']) / 'CPU_AND_SOURCE.json'))
    expected = config['predecessor']['identity']
    require(identity(expected['pid']) == expected, 'exact_old_monitor_before_pidfd')
    (namespace / 'HANDOFF_ONCE').mkdir()
    descriptor = os.pidfd_open(expected['pid'])
    paused = False
    try:
        require(identity(expected['pid']) == expected, 'exact_old_monitor_after_pidfd')
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            paused = pause_if_idle(expected, descriptor)
            if paused:
                break
            time.sleep(.1)
        require(paused, 'bounded_idle_wait_no_observer_retirement')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        paused = False
        require(bool(select.select([descriptor], [], [], 5)[0]), 'old_monitor_pidfd_exit_no_KILL')
        prefix = read(config['predecessor']['audit_manifest'])
        require(all(sha(path) == digest for path, digest in prefix.items()), 'every_prior_audit_preserved')
        write(namespace / 'RETIRED.json', dict(identity=expected, config_sha256=sha(config_path), retired_unix=time.time(),
            scope='ONLY_OLD_CUMULATIVE_AUDIT_MONITOR', idle_sleep_childless_single_thread=True,
            extra_writable_fds_at_pause=False, old_audits_preserved=len(prefix), parent_child_signals=0))
    finally:
        if paused:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)
    command = [sys.executable, '-B', str(Path(__file__).resolve()), '--action', 'run', '--config', str(config_path)]
    with (namespace / 'MONITOR.log').open('xb') as log:
        successor = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            cwd=namespace, start_new_session=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
    receipt = dict(pid=successor.pid, identity=identity(successor.pid), command=command, launched_unix=time.time(),
                   config_sha256=sha(config_path), retired_sha256=sha(namespace / 'RETIRED.json'))
    write(namespace / 'LAUNCHED.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--action', choices=('prepare', 'handoff', 'run'), required=True)
    arguments = parser.parse_args()
    result = {'prepare': prepare, 'handoff': handoff, 'run': run}[arguments.action](arguments.config)
    print(json.dumps(result, sort_keys=True))
