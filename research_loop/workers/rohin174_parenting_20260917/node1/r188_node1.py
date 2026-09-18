"""R188 loss-labelled recovery of only NODE1's two old-rehearsal lives."""

from copy import deepcopy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shutil
import signal
import statistics
import subprocess
import sys
import time
import uuid

from recover_support_identity import helpers, read, require, sha, write, PYTHON, BASE
import support_identity_repair as repair


LABELS = {2: 'teach_replay', 3: 'teach_perception'}
COMPLETE = {2: (5120, '1b774bcf225db0011979c73fa018e7d2dcb198da83ff3d4e01ba0b795ff3410a'),
            3: (5363, 'db0385aa3fc46ea626622358fbbf643e59899dab229c083f042cdcfdbbfad5ba')}
AUTHORITY = 'R188 authorized partial-old-sleep discard above15min ETA; loss-labelled recovery, not unbroken continuation'


def record_paths(root):
    return sorted(path for path in (root / 'stream/records').iterdir() if re.fullmatch(r'\d{20}\.json', path.name))


def suffix_counts(records, complete):
    suffix = [record for record in records if record['index'] > complete['index']]
    require(not any(record['kind'] == 'SLEEP_COMPLETE' for record in suffix), 'new_complete_use_exact_waiter')
    steps = [record['document']['optimizer_step'] for record in suffix if record['kind'] == 'UPDATE']
    first = complete['document']['total_optimizer_steps'] + 1
    require(steps == list(range(first, first + len(steps))), 'consecutive_logged_updates')
    return dict(logged_discarded_updates=len(steps), unknown_inflight_update='UNKNOWN_NOT_COUNTED',
        discarded_records=len(suffix), discarded_REQUEST=sum(record['kind'] == 'REQUEST' for record in suffix),
        discarded_RESPONSE=sum(record['kind'] == 'RESPONSE' for record in suffix),
        last_logged_step=steps[-1] if steps else first - 1)


def prefix_name(name, boundary):
    match = re.fullmatch(r'(\d{20})(?:\.intent)?\.json', name)
    require(match is not None, 'recognized_record_or_intent_only')
    return int(match[1]) <= boundary


def classify(base, physical):
    require(physical in LABELS, 'never_frozen_or_new_only_target')
    lane = BASE / 'lanes' / ('lane' + str(physical))
    request = read(lane / 'STAGED.json')
    old_guard = Path(request['original_guard']['path'])
    require(sha(old_guard) == request['original_guard']['sha256'], 'bound_original_guard')
    config = read(old_guard)
    plan = read(config['plan_path'])
    root = Path(plan['root'])
    require(root == Path('/localhome/local-rohing/orch_r136_a100_' + LABELS[physical] + '_20260916_attempt1/run1')
        and plan['rehearsal_presentations'] == 1, 'only_named_old_full_recipe')
    require(not any((lane / name).exists() for name in ('BOUNDARY.json', 'RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json')), 'no_competing_boundary_transition')
    pair = request['processes']
    for expected in pair.values():
        require(base.identity(expected['pid']) == expected, 'exact_original_owned_process')
    records = [read(path) for path in record_paths(root) if int(path.stem) >= COMPLETE[physical][0]]
    complete = records[0]
    require(complete['sha256'] == COMPLETE[physical][1] and complete['kind'] == 'SLEEP_COMPLETE', 'exact_last_complete')
    counts = suffix_counts(records, complete)
    target = next(record['document'] for record in reversed(records) if record['kind'] == 'TARGET_ELIGIBILITY')
    updates = [record['document']['finished_unix'] for record in records if record['kind'] == 'UPDATE']
    require(len(updates) >= 3, 'measured_update_intervals')
    recent = updates[-11:]
    interval = statistics.median([after - before for before, after in zip(recent, recent[1:])])
    total = 16 * len(target['new_row_sha256']) + len(target['rehearsal_row_sha256'])
    eta = (total - counts['logged_discarded_updates']) * interval
    checkpoint = root / 'checkpoints' / ('sleep_%06d' % complete['document']['cycle']) / 'COMMIT.json'
    require(checkpoint.is_file(), 'last_complete_checkpoint_exists')
    return dict(lane=lane, request=request, config=config, plan=plan, root=root, pair=pair, complete=complete,
        records=records, counts=counts, eta_seconds=eta, interval_seconds=interval, planned_updates=total,
        checkpoint_sha256=sha(checkpoint), checkpoint=checkpoint)


def stage(base, physical):
    facts = classify(base, physical)
    output = BASE / 'r188' / ('lane' + str(physical))
    if facts['eta_seconds'] <= 900:
        print(json.dumps(dict(status='EXACT_WAIT_ETA_AT_MOST15MIN', physical=physical, eta_seconds=facts['eta_seconds'])))
        return
    output.mkdir(parents=True)
    old_config = read(facts['lane'] / 'control/GUARD.json')
    plan = read(old_config['plan_path'])
    original = Path(plan['source_root'])
    require(plan['rehearsal_presentations'] == 0 and plan['root'] == str(facts['root']), 'already_prepared_R181_same_life')
    before = base.inventory_files(original)
    require({name: value for name, value in before.items() if name.endswith('.py')} == old_config['source_pins'], 'prepared_source_pins')
    source = output / 'source'
    shutil.copytree(original, source)
    for relative, expected in repair.ORIGINAL_HASHES.items():
        path = source / relative
        require(sha(path) == expected, 'exact_scanner_repair_source')
        mode = path.stat().st_mode & 0o777
        path.chmod(mode | 0o200)
        path.write_text(repair.patch(relative, path.read_text()))
        path.chmod(mode)
    after = base.inventory_files(source)
    require(set(before) == set(after) and {name for name in before if before[name] != after[name]} == set(repair.ORIGINAL_HASHES), 'scanner_only_prepared_source_delta')
    control = output / 'control'
    control.mkdir()
    write(control / 'PLAN.json', base.relocated_plan(plan, source))
    allocation = read(old_config['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), r188_authority=AUTHORITY, declared_unix=time.time())
    write(control / 'ALLOCATION.json', allocation)
    config = deepcopy(old_config)
    config.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        source_pins={name: value for name, value in after.items() if name.endswith('.py')})
    config['device_containment']['unit'] = 'orch-r188-node1-' + uuid.uuid4().hex
    write(control / 'GUARD.json', config)
    env = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    checked = subprocess.run([PYTHON, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate;import sys;validate(sys.argv[1])', str(control / 'GUARD.json')], cwd=source, env=env, capture_output=True, text=True, timeout=90)
    require(checked.returncode == 0, 'actual_receiving_guard:' + checked.stderr[-500:])
    write(output / 'PREPARED.json', dict(authority=AUTHORITY, physical=physical, observed_unix=time.time(),
        original_root=str(facts['root']), eta_seconds=facts['eta_seconds'], counts=facts['counts'], pair=facts['pair'],
        complete_index=facts['complete']['index'], complete_sha256=facts['complete']['sha256'],
        checkpoint_sha256=facts['checkpoint_sha256'], guard_sha256=sha(control / 'GUARD.json'),
        source_pins=config['source_pins'], operator_sha256=sha(__file__), exact_inflight_continuation=False))
    print(json.dumps(dict(status='PREPARED_R188_LOSS_LABELLED', physical=physical, eta_seconds=facts['eta_seconds'])), flush=True)


def terminate(base, expected, descriptor):
    require(base.identity(expected['pid']) == expected, 'exact_owner_before_stop')
    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    require(bool(select.select([descriptor], [], [], 25)[0]), 'exact_process_exit')


def run(base, physical):
    output = BASE / 'r188' / ('lane' + str(physical))
    prepared = read(output / 'PREPARED.json')
    require(prepared['operator_sha256'] == sha(__file__), 'prepared_operator_unchanged')
    require(sha(output / 'control/GUARD.json') == prepared['guard_sha256'], 'prepared_guard_unchanged')
    require({name: value for name, value in base.inventory_files(output / 'source').items() if name.endswith('.py')}
        == prepared['source_pins'], 'prepared_source_before_any_signal')
    facts = classify(base, physical)
    if facts['eta_seconds'] <= 900:
        write(output / 'EXACT_WAIT.json', dict(eta_seconds=facts['eta_seconds'], observed_unix=time.time(), signals_sent=0))
        print(json.dumps(dict(status='EXACT_WAIT_ETA_AT_MOST15MIN', physical=physical, eta_seconds=facts['eta_seconds'])))
        return
    require(facts['checkpoint_sha256'] == prepared['checkpoint_sha256'], 'saved_checkpoint_unchanged')
    waiter = base.identity(read(facts['lane'] / 'ARMED.json')['operator_pid'])
    require(waiter['uid'] == 1395 and 'r181_journal_operator.py' in ' '.join(waiter['argv'])
        and waiter['argv'][-1] == '14400', 'exact_superseded_CPU_waiter')
    write(output / 'STOP_AUTHORITY.json', dict(authority=AUTHORITY, observed_unix=time.time(), eta_seconds=facts['eta_seconds'],
        pair=facts['pair'], waiter=waiter, exact_inflight_continuation=False))
    waiter_fd = os.pidfd_open(waiter['pid'])
    try:
        base.pause_exact(waiter, waiter_fd)
        classify(base, physical)
        terminate(base, waiter, waiter_fd)
    finally:
        if not select.select([waiter_fd], [], [], 0)[0]:
            signal.pidfd_send_signal(waiter_fd, signal.SIGCONT)
        os.close(waiter_fd)
    lock = os.open(BASE / ('lane' + str(physical) + '.lock'), os.O_RDWR | os.O_NOFOLLOW)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    descriptors = {name: os.pidfd_open(expected['pid']) for name, expected in facts['pair'].items()}
    paused = []
    try:
        for name in ('supervisor', 'timer', 'actor'):
            base.pause_exact(facts['pair'][name], descriptors[name])
            paused.append(name)
        settled = classify(base, physical)
        require(settled['eta_seconds'] > 900, 'fresh_ETA_still_over15min')
        require(not Path('/proc', str(facts['pair']['actor']['pid']), 'task', str(facts['pair']['actor']['pid']), 'children').read_text().split(), 'no_live_readout_child')
        require(settled['records'][-1]['kind'] == 'UPDATE', 'actual_logged_update_prefix')
        write(output / 'SETTLED_LOSS.json', dict(counts=settled['counts'], head_index=settled['records'][-1]['index'],
            head_sha256=settled['records'][-1]['sha256'], complete_index=prepared['complete_index'],
            checkpoint_sha256=settled['checkpoint_sha256'], all_original_history_preserved=True,
            exact_inflight_continuation=False, observed_unix=time.time()))
        for name in ('actor', 'timer', 'supervisor'):
            if not select.select([descriptors[name]], [], [], 0)[0]:
                terminate(base, facts['pair'][name], descriptors[name])
            paused.remove(name)
        write(output / 'STOPPED.json', dict(pair=facts['pair'], counts=settled['counts'], observed_unix=time.time()))
        root, archive = facts['root'], output / 'FULL_OLD_ROOT'
        root.rename(archive)
        (root / 'stream/records').mkdir(parents=True)
        for name in ('JOURNAL.json', 'WRITER.lock'):
            shutil.copy2(archive / 'stream' / name, root / 'stream' / name)
        shutil.copytree(archive / 'stream/inbox', root / 'stream/inbox')
        for path in (archive / 'stream/records').iterdir():
            if prefix_name(path.name, prepared['complete_index']):
                shutil.copy2(path, root / 'stream/records' / path.name)
        for path in archive.iterdir():
            if path.name == 'stream':
                continue
            if path.is_dir():
                shutil.copytree(path, root / path.name, copy_function=os.link if path.name == 'readouts' else shutil.copy2)
            else:
                shutil.copy2(path, root / path.name)
        require(sha(root / facts['checkpoint'].relative_to(root)) == prepared['checkpoint_sha256'], 'checkpoint_restored_exact')
        source = output / 'source'
        env = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
        code = 'from gpu.orch_r125_stream_journal import StreamJournal;import sys; journal=StreamJournal(sys.argv[1]); assert journal.latest_checkpoint()["expected_sha256"]==sys.argv[2]; journal.close();print("FULL_PREFIX_WITH_INTENTS_PASS")'
        result = subprocess.run([PYTHON, '-B', '-c', code, str(root / 'stream'), facts['complete']['document']['resume_state']['sha256']], cwd=source, env=env, capture_output=True, text=True, timeout=120)
        require(result.returncode == 0, 'restored_full_journal:' + result.stderr[-1000:])
        write(output / 'RESTORED.json', dict(authority=AUTHORITY, original_archive=str(archive), active_root=str(root),
            complete_index=prepared['complete_index'], complete_sha256=prepared['complete_sha256'], counts=settled['counts'],
            prefix_and_all_intents_validated=True, readout_contents_read=False, exact_inflight_continuation=False, observed_unix=time.time()))
        with (output / 'SUPERVISOR.log').open('xb') as log:
            process = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_r136_node1_launcher', 'contained-supervise', '--config', str(output / 'control/GUARD.json')], cwd=source, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(output / 'DISPATCHED.json', dict(supervisor_pid=process.pid, observed_unix=time.time(), no_retry=True))
        print(json.dumps(dict(status='LOSS_LABELLED_RESTORED_DISPATCHED_NOT_LOADED', physical=physical, counts=settled['counts'], supervisor_pid=process.pid)), flush=True)
    finally:
        base.resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(lock)


if __name__ == '__main__':
    require(os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'node1_CPU_operator_only')
    {'stage': stage, 'run': run}[sys.argv[1]](helpers(), int(sys.argv[2]))
