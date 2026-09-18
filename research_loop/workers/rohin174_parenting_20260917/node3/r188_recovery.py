"""R188 authorized partial-sleep rollback, retaining the full original live tree."""

import argparse
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import statistics
import subprocess
import time
import uuid

import r181_boundary as base
import r181_journal_boundary as journal


WAITERS = {0: 1477138, 1: 1477139, 2: 1477140, 3: 1477141, 4: 1477142, 7: 1477143}
AUTHORITY = 'Rohin188: explicitly authorized rollback/discard of partial sleeps with ETA over15min; not unbroken exact continuation'


def prefix_file(name, saved_index):
    matched = re.fullmatch(r'(\d{20})(?:\.intent)?\.json', name)
    return matched is not None and int(matched[1]) <= saved_index


def suffix_counts(records, saved):
    suffix = [record for record in records if record['index'] > saved['index']]
    base.require(not any(record['kind'] == 'SLEEP_COMPLETE' for record in suffix), 'newer_saved_boundary_use_exact_waiter')
    updates = [record['document']['optimizer_step'] for record in suffix if record['kind'] == 'UPDATE']
    first = saved['document']['total_optimizer_steps'] + 1
    base.require(updates == list(range(first, first + len(updates))), 'consecutive_logged_discarded_updates')
    return dict(logged_discarded_updates=len(updates), unknown_inflight_update='UNKNOWN_NOT_COUNTED',
        discarded_records=len(suffix), discarded_REQUEST=sum(record['kind'] == 'REQUEST' for record in suffix),
        discarded_RESPONSE=sum(record['kind'] == 'RESPONSE' for record in suffix),
        last_logged_step=updates[-1] if updates else first - 1)


def records_after(root, index):
    paths = sorted(path for path in (root / 'stream/records').glob('*.json')
        if path.stem.isdigit() and len(path.stem) == 20 and int(path.stem) >= index)
    return [base.read(path) for path in paths]


def terminate(expected):
    fields = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(') ', 1)[1].split()
    base.require(fields[19] == str(expected['ticks']), 'same_process_start_ticks')
    if fields[0] in ('Z', 'X'):
        return
    descriptor = os.pidfd_open(expected['pid'])
    try:
        if select.select([descriptor], [], [], 0)[0]:
            return
        try:
            base.exact(expected)
        except PermissionError:
            base.require(bool(select.select([descriptor], [], [], 20)[0]), 'inaccessible_process_must_actually_exit')
            return
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        base.require(bool(select.select([descriptor], [], [], 20)[0]), 'exact_owned_process_exit')
    finally:
        os.close(descriptor)


def stop_restore(folder):
    physical = int(folder.name.removeprefix('physical'))
    old = base.HERE / 'r181' / folder.name
    spec = base.read(old / 'LIVE_HANDOFF.json')
    root = Path(spec['backing_root'])
    base.require(not (old / 'BOUNDARY.json').exists(), 'no_existing_boundary_handoff')
    base.require(time.time() < base.HARD_END - 300, 'inside_unchanged_recovery_window')
    records = records_after(root, spec['saved']['index'])
    saved = records[0]
    base.require(saved['sha256'] == spec['saved']['sha256'], 'pinned_latest_complete')
    base.saved_state(saved)
    updates = [record['document']['finished_unix'] for record in records if record['kind'] == 'UPDATE']
    eligibility = next(record['document'] for record in reversed(records) if record['kind'] == 'TARGET_ELIGIBILITY')
    schedule = 16 * len(eligibility['new_row_sha256']) + len(eligibility['rehearsal_row_sha256'])
    interval = statistics.median([after-before for before, after in zip(updates[-21:-1], updates[-20:])])
    eta = (schedule - len(updates)) * interval
    base.require(eta > 900, 'ETA_at_most15min_keep_exact_waiter')
    folder.mkdir(parents=True, exist_ok=False)
    base.write(folder / 'AUTHORITY.json', dict(directive=AUTHORITY, physical=physical,
        observed_unix=time.time(), eta_seconds=eta, hard_end_unix=base.HARD_END, machine_ceiling_unix=1789689600))
    waiter = base.identity(WAITERS[physical])
    base.require(waiter['argv'] == [base.PYTHON, '-B', str(Path(journal.__file__).resolve()),
        'wait', '--physical', str(physical)], 'exact_superseded_boundary_waiter')
    terminate(waiter)
    base.require(not (old / 'BOUNDARY.json').exists(), 'waiter_retired_without_claim')
    base.write(folder / 'WAITER_RETIRED.json', dict(identity=waiter, observed_unix=time.time()))
    observed = base.head(root)
    deadline = time.monotonic() + 130
    while time.monotonic() < deadline:
        head = base.head(root)
        if head['index'] > observed['index'] and head['kind'] == 'UPDATE':
            break
        time.sleep(.1)
    else:
        raise ValueError('next_logged_UPDATE_not_seen_no_native_stop')
    actor = base.exact(spec['identity'])
    timer = base.identity(actor['parent'])
    supervisor = base.identity(timer['parent'])
    base.require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
        and actor['cgroup'] == timer['cgroup'] == supervisor['cgroup'], 'exact_original_service_topology')
    descriptor = os.pidfd_open(actor['pid'])
    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
    os.close(descriptor)
    for unused in range(500):
        tasks = list((Path('/proc') / str(actor['pid']) / 'task').iterdir())
        if all((task / 'stat').read_text().rsplit(') ', 1)[1].split()[0] in ('T', 't') for task in tasks):
            break
        time.sleep(.01)
    else:
        raise ValueError('native_stop_threads_unconfirmed')
    terminal = base.head(root)
    base.require(terminal['kind'] == 'UPDATE', 'stop_on_actual_logged_UPDATE')
    records = records_after(root, saved['index'])
    counts = suffix_counts(records, saved)
    checkpoint = root / 'checkpoints' / ('sleep_%06d' % saved['document']['cycle']) / 'COMMIT.json'
    commit = base.read(checkpoint)
    mapped = lambda value: root / Path(value).relative_to(spec['plan']['root'])
    base.require(base.sha(mapped(commit['optimizer_rng_path'])) == commit['checkpoint_sha256']['optimizer']
        == commit['checkpoint_sha256']['rng'], 'actual_saved_optimizer_RNG')
    adapter = {path.name: base.sha(path) for path in mapped(commit['adapter_path']).iterdir() if path.is_file()}
    base.require(adapter == commit['adapter_files'], 'actual_saved_adapter')
    base.write(folder / 'STOP_INTENT.json', dict(actors=[actor, timer, supervisor],
        terminal=terminal, counts=counts, observed_unix=time.time()))
    for process in (actor, timer, supervisor):
        try:
            terminate(process)
        except FileNotFoundError:
            pass
    return finish_recovery(folder, spec, saved, terminal, counts, [actor, timer, supervisor])


def finish_recovery(folder, spec, saved, terminal, counts, actors):
    physical = spec['physical']
    old = base.HERE / 'r181' / folder.name
    root = Path(spec['backing_root'])
    checkpoint = root / 'checkpoints' / ('sleep_%06d' % saved['document']['cycle']) / 'COMMIT.json'
    base.require(base.head(root)['sha256'] == terminal['sha256'], 'stopped_terminal_unchanged')
    stopped = dict(status='ACTUAL_R188_STOPPED_WITH_AUTHORIZED_LOSS', physical=physical,
        observed_unix=time.time(), actors=actors, terminal=terminal,
        saved_index=saved['index'], saved_cycle=saved['document']['cycle'],
        saved_record_sha256=saved['sha256'], checkpoint_file_sha256=base.sha(checkpoint),
        counts=counts, unbroken_exact_continuation=False, authority=AUTHORITY)
    base.write(folder / 'STOPPED.json', stopped)
    print(json.dumps(dict(status=stopped['status'], physical=physical, counts=counts)), flush=True)
    archive = folder / 'ARCHIVED_LIVE_ROOT'
    root.rename(archive)
    (root / 'stream/records').mkdir(parents=True)
    shutil.copy2(archive / 'stream/JOURNAL.json', root / 'stream/JOURNAL.json')
    shutil.copy2(archive / 'stream/WRITER.lock', root / 'stream/WRITER.lock')
    shutil.copytree(archive / 'stream/inbox', root / 'stream/inbox')
    for path in (archive / 'stream/records').glob('*.json'):
        if prefix_file(path.name, saved['index']):
            shutil.copy2(path, root / 'stream/records' / path.name)
    subprocess.run(['cp', '-a', '--reflink=auto', str(archive / 'checkpoints'), str(root / 'checkpoints')], check=True)
    shutil.copytree(archive / 'readouts', root / 'readouts', copy_function=os.link)
    base.require(base.head(root)['sha256'] == saved['sha256'], 'exact_saved_journal_prefix_restored')
    base.require(base.sha(root / checkpoint.relative_to(archive if checkpoint.is_relative_to(archive) else root))
        == stopped['checkpoint_file_sha256'], 'saved_checkpoint_bytes_unchanged')
    inbox = lambda directory: {path.name: base.sha(path) for path in directory.glob('*.json')}
    base.require(inbox(root / 'stream/inbox') == inbox(archive / 'stream/inbox'), 'all_actual_inboxes_preserved')
    base.write(folder / 'RESTORED.json', dict(status='EXACT_CHECKPOINT_AFTER_EXPLICIT_ROLLBACK',
        archive=str(archive), live_root=str(root), saved_index=saved['index'], saved_cycle=saved['document']['cycle'],
        preserved_inbox_files=inbox(root / 'stream/inbox'), counts=counts, observed_unix=time.time(),
        all_original_live_root_preserved=True, readout_contents_read=False,
        readout_files_metadata_hardlinked=True, unbroken_exact_continuation=False))
    for name in ('new_native.py', 'new_journal.py', 'PLAN.json', 'LIVE_HANDOFF.json'):
        shutil.copy2(old / name, folder / name)
    allocation = dict(base.read(old / 'ALLOCATION.json'), r188_authority=AUTHORITY, declared_unix=time.time())
    base.write(folder / 'ALLOCATION.json', allocation)
    config = base.read(old / 'GUARD.json')
    config.update(plan_path=str(folder / 'PLAN.json'), plan_sha256=base.sha(folder / 'PLAN.json'),
        attempt_dir=str(folder), allocation_path=str(folder / 'ALLOCATION.json'),
        allocation_sha256=base.sha(folder / 'ALLOCATION.json'),
        device_containment=dict(config['device_containment'], unit='orch-r188-node3-' + uuid.uuid4().hex))
    base.write(folder / 'GUARD.json', config)
    checked = subprocess.run(command(folder, 'cpu', cpu=True), capture_output=True, text=True, timeout=90)
    base.require(checked.returncode == 0, 'unchanged_R181_cache_receiving_guard:' + checked.stderr[-700:])
    base.write(folder / 'SOURCE_BOUND.json', dict(status='PASS', output=checked.stdout, observed_unix=time.time()))
    return launch(folder, spec)


def launch(folder, spec):
    physical = spec['physical']
    scan = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + spec['plan']['source_root'], base.PYTHON, '-B', '-m', 'gpu.orch_r125_continual_guard',
        'scan', '--config', spec['config_path']]
    scanned = subprocess.run(scan, capture_output=True, text=True, timeout=90, cwd=spec['plan']['source_root'])
    base.require(scanned.returncode == 0, 'fresh_actual_device_admission')
    admission = json.loads(scanned.stdout)
    base.require(admission['clear'] and not admission['blocking_reasons']
        and admission['gpu']['uuid'] == spec['plan']['gpu_uuid'], 'same_device_clear')
    base.write(folder / 'ADMISSION.json', admission)
    base.write(folder / 'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    (folder / 'DISPATCH_ONCE').mkdir(exist_ok=False)
    with (folder / 'SERVICE.log').open('x') as log:
        process = subprocess.Popen(command(folder, 'contained'), stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True)
    base.write(folder / 'DISPATCHED.json', dict(pid=process.pid, observed_unix=time.time(),
        status='R188_ROLLBACK_RECOVERY_DISPATCHED_NOT_YET_LOADED', unbroken_exact_continuation=False))
    print(json.dumps(dict(status='DISPATCHED_NOT_YET_LOADED', physical=physical, pid=process.pid)), flush=True)


def repair_pre_native_marker(folder):
    base.require(base.read(folder / 'EXIT.json')['exit_code'] == 1
        and 'actual_timeout_parent' in (folder / 'NATIVE.log').read_text(), 'documented_pre_native_marker_rejection')
    spec = base.read(folder / 'LIVE_HANDOFF.json')
    base.require(base.head(spec['backing_root'])['sha256'] == spec['saved']['sha256']
        and not (folder / 'DISPATCH_ONCE').exists(), 'no_LOADED_or_model_update_before_marker_repair')
    archive = folder / 'PRE_NATIVE_MARKER_REJECTION'
    archive.mkdir(exist_ok=False)
    for name in ('SERVICE.log', 'NATIVE.log', 'LAUNCH.json', 'EXIT.json', 'DISPATCHED.json',
            'ADMISSION.json', 'ADMISSION_TIME.json'):
        (folder / name).rename(archive / name)
    base.write(folder / 'MARKER_REPAIR.json', dict(reason='missing existing DISPATCH_ONCE directory',
        archived_operator_artifacts=str(archive), no_model_load_or_update=True, observed_unix=time.time()))
    return launch(folder, spec)


def repair_prefix_intents(folder):
    base.require(base.read(folder / 'EXIT.json')['exit_code'] == 1
        and 'incomplete_journal_tail' in (folder / 'NATIVE.log').read_text(), 'documented_preload_journal_rejection')
    spec = base.read(folder / 'LIVE_HANDOFF.json')
    root = Path(spec['backing_root'])
    base.require(base.head(root)['sha256'] == spec['saved']['sha256'], 'no_new_record_or_model_work')
    archive = folder / 'ARCHIVED_LIVE_ROOT/stream/records'
    copied = 0
    for path in archive.glob('*.intent.json'):
        if prefix_file(path.name, spec['saved']['index']):
            destination = root / 'stream/records' / path.name
            base.require(not destination.exists(), 'restore_missing_original_intent_only')
            shutil.copy2(path, destination)
            base.require(base.sha(path) == base.sha(destination), 'exact_original_intent_bytes')
            copied += 1
    base.require(copied == spec['saved']['index'] + 1, 'one_intent_per_retained_record')
    archive = folder / 'PRE_NATIVE_PREFIX_REJECTION'
    archive.mkdir(exist_ok=False)
    for name in ('SERVICE.log', 'NATIVE.log', 'LAUNCH.json', 'EXIT.json', 'DISPATCHED.json',
            'ADMISSION.json', 'ADMISSION_TIME.json', 'DISPATCH_ONCE'):
        (folder / name).rename(archive / name)
    return verify_prefix_and_launch(folder)


def cpu(folder):
    journal.cpu(folder)
    from gpu.orch_r125_stream_journal import StreamJournal
    spec = base.read(folder / 'LIVE_HANDOFF.json')
    plan = base.read(folder / 'PLAN.json')
    with StreamJournal(Path(plan['root']) / 'stream', create=False) as restored:
        state = restored.latest_checkpoint()
        base.require(state['expected_sha256'] == spec['saved']['state_sha256'], 'same_saved_state_after_strict_replay')
    print(json.dumps(dict(status='ACTUAL_BOUND_JOURNAL_REPLAY_PASS', saved_state_sha256=state['expected_sha256'])))


def verify_prefix_and_launch(folder):
    spec = base.read(folder / 'LIVE_HANDOFF.json')
    base.require(base.read(folder / 'PRE_NATIVE_PREFIX_REJECTION/EXIT.json')['exit_code'] == 1
        and base.head(spec['backing_root'])['sha256'] == spec['saved']['sha256']
        and not (folder / 'DISPATCH_ONCE').exists(), 'known_stopped_saved_prefix_not_unknown_launch')
    checked = subprocess.run(command(folder, 'cpu', cpu=True), capture_output=True, text=True, timeout=90)
    base.require(checked.returncode == 0, 'actual_strict_journal_replay:' + checked.stderr[-800:])
    base.write(folder / 'PREFIX_INTENTS_REPAIR.json', dict(original_companions_restored=spec['saved']['index'] + 1,
        strict_original_replay=checked.stdout.strip(), no_model_load_or_update=True, observed_unix=time.time()))
    return launch(folder, spec)


def reconcile_stopped(folder):
    old = base.HERE / 'r181' / folder.name
    spec = base.read(old / 'LIVE_HANDOFF.json')
    base.require(not (folder / 'ARCHIVED_LIVE_ROOT').exists() and not (folder / 'STOPPED.json').exists(),
        'only_known_prearchive_exit_check_failure')
    failure = base.read(folder / 'FAILED.json')
    base.require(failure['error_type'] == 'PermissionError', 'documented_exit_check_failure_only')
    actors = base.read(old / 'JOURNAL_WAIT_STARTED.json')['actors']
    for expected in actors:
        try:
            terminate(expected)
        except FileNotFoundError:
            pass
    records = records_after(Path(spec['backing_root']), spec['saved']['index'])
    saved, terminal = records[0], records[-1]
    base.require(saved['sha256'] == spec['saved']['sha256'] and terminal['kind'] == 'UPDATE',
        'same_saved_prefix_and_stopped_UPDATE')
    counts = suffix_counts(records, saved)
    base.write(folder / 'EXIT_RECONCILED.json', dict(original_failure=failure, actors=actors,
        all_three_exited=True, observed_unix=time.time(), no_new_stop_or_publication=True))
    return finish_recovery(folder, spec, saved, terminal, counts, actors)


def command(folder, action, *, cpu=False):
    result = journal.command(folder, action, cpu=cpu)
    result[result.index(str(Path(journal.__file__).resolve()))] = str(Path(__file__).resolve())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stop_restore', 'reconcile_stopped', 'repair_pre_native_marker', 'repair_prefix_intents', 'verify_prefix_and_launch', 'cpu', 'contained'))
    parser.add_argument('--physical', type=int, choices=tuple(WAITERS), required=True)
    options = parser.parse_args()
    base.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    base.cpu = cpu
    folder = base.HERE / 'r188' / ('physical' + str(options.physical))
    try:
        if options.action == 'cpu':
            cpu(folder)
        elif options.action == 'contained':
            base.contained(folder)
        elif options.action == 'reconcile_stopped':
            reconcile_stopped(folder)
        elif options.action == 'repair_pre_native_marker':
            repair_pre_native_marker(folder)
        elif options.action == 'repair_prefix_intents':
            repair_prefix_intents(folder)
        elif options.action == 'verify_prefix_and_launch':
            verify_prefix_and_launch(folder)
        else:
            stop_restore(folder)
    except BaseException as error:
        if folder.exists() and not (folder / 'FAILED.json').exists():
            base.write(folder / 'FAILED.json', dict(error_type=type(error).__name__, reason=str(error)[-1000:], observed_unix=time.time()))
        raise
