"""R188 explicit lossy rollback: retire only bound NODE5 C2 at a retained UPDATE."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import socket
import time


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def retained_update(path, journal_id, initial_steps):
    record = read(path)
    require(record['kind'] == 'UPDATE' and record['journal_id'] == journal_id, 'same_life_retained_UPDATE')
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}), 'UPDATE_hash')
    intent = read(path.with_name(path.stem + '.intent.json'))
    require(intent['record_sha256'] == record['sha256'] and intent['index'] == record['index']
        and intent['previous_sha256'] == record['previous_sha256'], 'retained_UPDATE_intent')
    step = record['document']['optimizer_step']
    require(type(step) is int and step >= initial_steps, 'rollback_step_monotonic')
    return dict(index=record['index'], record_sha256=record['sha256'], file=ref(path),
        optimizer_step=step, restored_optimizer_step=initial_steps, discarded_recorded_updates=step-initial_steps,
        possible_unlogged_inflight_update='UNKNOWN_SEPARATE_FROM_RECORDED_COUNT',
        retained_finished_unix=record['document']['finished_unix'])


def latest(records):
    return max(records.glob('[0-9]' * 20 + '.json'))


def exited(descriptor, seconds):
    return bool(select.select([descriptor], [], [], seconds)[0])


def terminate(descriptor):
    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
    try:
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
    except ProcessLookupError:
        pass
    require(exited(descriptor, 20), 'exact_process_not_exited_no_repeat_stop')


def main(waiter, output):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'NODE5_only')
    require(not output.exists() and output.parent == Path('/localhome/local-rohing')
        and output.name.startswith('orch_r153_r188_C2_'), 'fresh_owned_R188_control')
    spec = importlib.util.spec_from_file_location('saved', waiter / 'saved_primitives.py')
    saved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(saved)
    ready = read(waiter / 'READY.json')
    pair = ready['pair']
    require(pair['actor']['pid'] == 1626817 and pair['actor']['start_ticks'] == '20440733', 'exact_original_C2')
    saved.same(pair['actor'])
    actor = pair['actor']
    for expected in pair.values():
        saved.same(expected)
    config_path = Path(actor['argv'][actor['argv'].index('--config') + 1])
    config = read(config_path)
    plan = read(config['plan_path'])
    root = Path(plan['root'])
    require(str(root) == '/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life'
        and plan['rehearsal_presentations'] == 1, 'original_C2_old_recipe_only')
    checkpoint = root / 'checkpoints/sleep_000041/optimizer_rng.pt'
    require(ref(checkpoint)['sha256'] == '6ea6fa9ffdfe806308293f1e08749b6cfea08f1bf1cae07f6a86608af1db80df', 'complete41_optimizer_RNG')
    require(not (root / 'checkpoints/sleep_000042').exists(), 'sleep42_not_already_saved')
    records = root / 'stream/records'
    initial = latest(records)
    started_waiter = read(waiter / 'OPERATOR_STARTED.json')['identity']
    waiter_owner = saved.identity(started_waiter['pid'])
    for key in ('pid','start_ticks','uid','argv','cwd','boot_id','group','cgroup'):
        require(waiter_owner[key] == started_waiter[key], 'exact_waiter_' + key)
    require(waiter_owner['parent'] in (started_waiter['parent'], 1), 'only_passive_waiter_reparent')
    require(ref(waiter / 'rollout_operator.py') == ready['operator'], 'bound_waiter_source')
    effects = ('ACTUAL_BOUNDARY_READY.json','CONTROLLER_STOP_INTENT.json','OWNER_RETIRED.json','attempt','EXECUTION_FAILED.json')
    require(not any((waiter / name).exists() for name in effects), 'waiter_not_crossing')
    output.mkdir(mode=0o700)
    write(output / 'R188_AUTHORITY.json', dict(directive='R188 explicit original-C2 rollback to complete41; discard partial42 with loss accounting; preserve old root and inputs',
        label='SAME_LIFE_RECOVERY_NOT_UNBROKEN_INFLIGHT_CONTINUATION', original_root=str(root),
        root_inode=root.stat().st_ino, pair=pair, waiter=waiter_owner, config=ref(config_path),
        checkpoint=ref(checkpoint), observed_unix=time.time(), no_old_root_replay=True))
    waiter_fd = os.pidfd_open(waiter_owner['pid'])
    with saved.pause_watchdog(waiter_fd, 60):
        saved.pause_exact(waiter_owner, waiter_fd)
        require(not saved.live_children(waiter_owner['pid']), 'quiet_CPU_waiter')
        require(not any((waiter / name).exists() for name in effects), 'waiter_still_preboundary')
        saved.same(pair['actor'])
        write(output / 'WAITER_STOP_INTENT.json', dict(identity=waiter_owner, native_signals=0, observed_unix=time.time()))
        terminate(waiter_fd)
        write(output / 'WAITER_EXITED.json', dict(pid=waiter_owner['pid'], observed_unix=time.time(), native_signals=0))
    os.close(waiter_fd)
    deadline = time.monotonic() + 100
    while True:
        saved.same(pair['actor'])
        require(not (root / 'checkpoints/sleep_000042').exists(), 'new_complete_boundary_no_rollback')
        path = latest(records)
        if path.name > initial.name and read(path)['kind'] == 'UPDATE':
            retained_update(path, '260be8b8710a42559b291797c6e14983', 4428)
            break
        require(time.monotonic() < deadline, 'no_next_retained_UPDATE_original_left_running')
        time.sleep(.2)
    actor_fd = os.pidfd_open(pair['actor']['pid'])
    supervisor_fd = os.pidfd_open(pair['supervisor']['pid'])
    timer_fd = os.pidfd_open(pair['timer']['pid'])
    with saved.pause_watchdog(actor_fd, 60):
        saved.pause_exact(pair['actor'], actor_fd)
        require(not (root / 'checkpoints/sleep_000042').exists(), 'no_saved42_after_pause')
        proof = retained_update(latest(records), '260be8b8710a42559b291797c6e14983', 4428)
        proof.update(pair=pair, old_root=str(root), old_root_preserved_in_place=True,
            original_journal_inbox_suffix_untouched=True, rollback_label='R188_LOSS_LABELLED_SAME_LIFE',
            observed_unix=time.time(), exact_stop_signal='pidfd_SIGTERM_no_group_signal')
        write(output / 'NATIVE_STOP_INTENT.json', proof)
        terminate(actor_fd)
        write(output / 'NATIVE_EXITED.json', dict(pid=pair['actor']['pid'], observed_unix=time.time()))
    if not exited(supervisor_fd, 15):
        saved.same(pair['supervisor'])
        write(output / 'SUPERVISOR_STOP_INTENT.json', dict(identity=pair['supervisor'], observed_unix=time.time()))
        terminate(supervisor_fd)
    require(exited(timer_fd, 10) and exited(supervisor_fd, 1), 'bound_native_timer_supervisor_exited')
    for descriptor in (actor_fd, supervisor_fd, timer_fd):
        os.close(descriptor)
    proof['stopped_unix'] = time.time()
    proof['native_timer_supervisor_exited'] = True
    write(output / 'STOPPED.json', proof)
    print(json.dumps(dict(output=str(output), receipt=ref(output / 'STOPPED.json'),
        discarded_recorded_updates=proof['discarded_recorded_updates'], stopped_unix=proof['stopped_unix'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--waiter', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.waiter, args.output)
