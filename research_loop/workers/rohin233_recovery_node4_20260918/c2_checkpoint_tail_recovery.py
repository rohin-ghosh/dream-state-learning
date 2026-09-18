"""Authorized C2 COMPLETE+tail receiving preflight and exact-incarnation replacement."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time

from deadline_resume import boundary, digest, identity, read, require, sha, write
from r227_plan import proposed_plan


BASE = Path('/localhome/local-rohing')
OLD = BASE / 'orch_r233_C2_deadline_20260918'
TARGET = BASE / 'orch_r233_C2_checkpoint_tail_20260918'
SOURCE = TARGET / 'source'
CONTROL = TARGET / 'control'
PYTHON = str(BASE / 'v2/venv/bin/python')
PID = 829798
START = '29168595'
JOURNAL = '260be8b8710a42559b291797c6e14983'
COMPLETE = '9c59fe6c59a01948b6ffe894aaa681010346ccc671c2f774a10fe7399a49080f'
OLD_GUARD = '5f8a471647972138f7429d6cafd962241a5363ca1c4f0fa447bfbadcb2de1ded'
PORTS = {'gpu/orch_r125_continual_native.py', 'gpu/orch_r125_stream_journal.py',
    'gpu/orch_r184_think_act_learn.py', 'organism_v6/orch_r125_plain_context.py',
    'organism_v6/orch_r227_learning_policy.py', 'gpu/checkpoint_tail_runtime.py'}


def exact_actor(old):
    actual = identity(PID)
    require(actual['start_ticks'] == START and actual['uid'] == 2524
        and actual['cwd'] == old['source_root'] and actual['argv'] == [PYTHON, '-B', '-m',
        'gpu.orch_r125_continual_guard', 'native', '--config', str(OLD / 'control/GUARD.json')]
        and actual['cgroup'] == '0::/system.slice/orch-r188-node5-c2-child-5f8a471647972138.service',
        'exact_replaying_native_identity')
    return actual


def exact_boundary(plan):
    complete, saved, tail = boundary(plan['root'], JOURNAL)
    require(complete['index'] == 11502 and complete['sha256'] == COMPLETE
        and tail == [{'index':11503, 'kind':'R184_LEARN_COMPLETE',
            'sha256':read(Path(plan['root']) / 'stream/records/00000000000000011503.json')['sha256']}],
        'same_unadvanced_complete_and_tail_no_NEW_LOAD')
    return complete, saved, tail


def readonly_scan(root, selection):
    from gpu.orch_r125_stream_journal import StreamJournal
    from gpu.checkpoint_tail_runtime import scan

    class ReadOnlyJournal(StreamJournal):
        @staticmethod
        def _publish(*arguments, **keywords):
            raise AssertionError('receiving_preflight_never_writes_journal')

        def record(self, *arguments, **keywords):
            raise AssertionError('receiving_preflight_never_records')

    journal = object.__new__(ReadOnlyJournal)
    journal.root = Path(root).absolute()
    journal.inbox = journal.root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = False
    journal._failed = False
    journal._checkpoint_tail = selection
    started = time.monotonic()
    try:
        journal._root_fd = journal._open(journal.root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        state = scan(journal, selection)
        require(state['request'] is None and state['response'] is None
            and state['sleep_request'] is None, 'receiving_idle_tail')
        return dict(journal.checkpoint_tail_receipt, elapsed_seconds=time.monotonic()-started,
            read_only=True, writer_lock_acquired=False, journal_writes=0)
    finally:
        journal.close()


def preflight():
    require(not (CONTROL / 'PREFLIGHT.json').exists(), 'receiving_preflight_once')
    require(sha(OLD / 'control/GUARD.json') == OLD_GUARD, 'same_old_guard')
    guard = read(OLD / 'control/GUARD.json')
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'same_old_plan')
    old = read(guard['plan_path'])
    actor = exact_actor(old)
    complete, saved, tail = exact_boundary(old)
    pins = {str(path.relative_to(SOURCE)):sha(path) for path in SOURCE.rglob('*.py')}
    delta = {name for name in set(pins) | set(guard['source_pins'])
        if pins.get(name) != guard['source_pins'].get(name)}
    require(delta <= PORTS and 'gpu/checkpoint_tail_runtime.py' in delta, 'only_tested_source_delta')
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_native as native
    native.NativeChild.verify_checkpoint(complete['document']['checkpoint'])
    import torch
    payload = torch.load(complete['document']['checkpoint']['optimizer_rng_path'],
        map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == 7756 and payload['optimizer']['state']
        and all(name in payload for name in ('cpu_rng','cuda_rng','python_rng'))
        and not torch.cuda.is_initialized(), 'exact_full_optimizer_RNG_CPU_only')
    plan, policy = proposed_plan(old, str(SOURCE))
    plan['authorized_wall_extension'] = deepcopy(old['authorized_wall_extension'])
    plan['checkpoint_tail_recovery'] = dict(policy='R233_PINNED_COMPLETE_TAIL_V1',
        root=str(Path(plan['root']) / 'stream'), journal_id=JOURNAL, complete_index=11502,
        complete_sha256=COMPLETE, life_id=plan['think_act_learn']['trial_id'],
        max_tail_records=2048, max_tail_bytes=1024*1024*1024,
        sidecars=[dict(name='correction_ledger.json',kind='R197_CORRECTION_CYCLE',required=True)],
        persist_complete_anchors=True)
    native.validate_plan(plan)
    stream = native.ContinualStream.restore(saved, expected_sha256=saved['sha256'])
    native.prepare_wall_extension(plan, stream, resume=True, plan_sha256=digest(plan))
    scan_receipt = readonly_scan(Path(plan['root']) / 'stream', plan['checkpoint_tail_recovery'])
    exact_actor(old)
    require(exact_boundary(old) == (complete, saved, tail), 'unchanged_after_receiving_scan')
    write(CONTROL / 'PLAN.json', plan)
    write(CONTROL / 'PREFLIGHT.json', dict(passed=True, observed_unix=time.time(),
        source_pins=pins, changed_source=sorted(delta), scan=scan_receipt,
        old_actor=actor, old_guard_sha256=OLD_GUARD, old_plan_sha256=guard['plan_sha256'],
        complete_index=11502, complete_sha256=COMPLETE, saved_state_sha256=saved['sha256'],
        optimizer_steps=7756, checkpoint=complete['document']['checkpoint'],
        policy_change=policy, prospective_learning_policy=plan['learn_row_policy'],
        semantic_filters=[], historical_annotations_preserved=True,
        full_AdamW_Python_CPU_CUDA_RNG=True, signals=[], hard_end_unix=plan['hard_end_unix']))
    print(json.dumps(dict(status='RECEIVING_CPU_PASSED_NOT_DISPATCHED',scan=scan_receipt)), flush=True)


def prepare(commit):
    require(len(commit) == 40 and all(value in '0123456789abcdef' for value in commit), 'published_commit')
    proof = read(CONTROL / 'PREFLIGHT.json')
    old_guard = read(OLD / 'control/GUARD.json')
    old = read(old_guard['plan_path'])
    exact_actor(old)
    exact_boundary(old)
    plan = read(CONTROL / 'PLAN.json')
    write(CONTROL / 'CPU.json', proof)
    write(CONTROL / 'LEASE.json', read(old_guard['lease_path']))
    allocation = read(old_guard['allocation_path'])
    allocation.update(plan_sha256=sha(CONTROL/'PLAN.json'), cpu_receipt_path=str(CONTROL/'CPU.json'),
        cpu_receipt_sha256=sha(CONTROL/'CPU.json'), declared_unix=time.time(), builder_entry_pushed=True,
        builder_entry_commit=commit, builder_entry='R233 checkpoint+tail non-material receiving repair; R227 no semantic exclusions')
    write(CONTROL/'ALLOCATION.json', allocation)
    guard = deepcopy(old_guard)
    guard.update(plan_path=str(CONTROL/'PLAN.json'), plan_sha256=sha(CONTROL/'PLAN.json'),
        source_pins=proof['source_pins'], lease_path=str(CONTROL/'LEASE.json'),
        lease_sha256=sha(CONTROL/'LEASE.json'), allocation_path=str(CONTROL/'ALLOCATION.json'),
        allocation_sha256=sha(CONTROL/'ALLOCATION.json'), attempt_dir=str(CONTROL), resume=True)
    write(CONTROL/'GUARD.json',guard)
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL/'GUARD.json')
    write(CONTROL/'RECEIVING_CPU.json',dict(passed=True,source_pins=proof['source_pins'],
        preflight_sha256=sha(CONTROL/'PREFLIGHT.json'),builder_commit=commit))
    write(CONTROL/'READY.json',dict(status='READY_NOT_DISPATCHED',guard_sha256=sha(CONTROL/'GUARD.json'),
        observed_unix=time.time(),complete_index=11502,complete_sha256=COMPLETE))
    print(json.dumps(read(CONTROL/'READY.json')),flush=True)


def replace():
    require(not (CONTROL/'REPLAY_TERMINATION.json').exists(), 'single_explicit_replacement')
    old_guard = read(OLD/'control/GUARD.json')
    old = read(old_guard['plan_path'])
    plan = read(CONTROL/'PLAN.json')
    ready = read(CONTROL/'READY.json')
    require(ready['guard_sha256'] == sha(CONTROL/'GUARD.json'), 'same_ready_guard')
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL/'GUARD.json')
    actor = exact_actor(old)
    exact_boundary(old)
    descriptor = os.pidfd_open(PID)
    try:
        require(exact_actor(old) == actor, 'same_native_after_pidfd_open')
        exact_boundary(old)
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        write(CONTROL/'REPLAY_TERMINATION.json',dict(actor=actor,signal='SIGTERM',
            sent_unix=time.time(),reason='user_authorized_replace_unloaded_CPU_replay_with_same_COMPLETE_tail',
            journal_preserved_in_place=True))
        poller = select.poll()
        poller.register(descriptor,select.POLLIN)
        require(bool(poller.poll(30000)), 'old_replay_exit_before_dispatch')
    finally:
        os.close(descriptor)
    exact_boundary(old)
    config = read(OLD/'BRIDGE.json')
    config.update(guard_path=str(CONTROL/'GUARD.json'),guard_sha256=sha(CONTROL/'GUARD.json'),
        cpu_source=str(SOURCE),native_source=str(SOURCE),socket=str(CONTROL/'cpu.sock'),
        stop_unix=plan['hard_end_unix'],first_new_record=11503)
    write(TARGET/'BRIDGE.json',config)
    bridge_script = Path(old['source_root']).parent/'math_bridge.py'
    with (CONTROL/'BRIDGE.log').open('x') as output:
        bridge = subprocess.Popen([PYTHON,'-B',str(bridge_script),'--config',str(TARGET/'BRIDGE.json')],
            stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    until = time.monotonic()+25
    while not list((TARGET/'bridge_receipts').glob('READY_*.json')):
        require(bridge.poll() is None and time.monotonic()<until,'new_math_bridge_ready')
        time.sleep(.2)
    with (CONTROL/'SUPERVISOR.log').open('x') as output:
        supervisor = subprocess.Popen([PYTHON,'-B','-m','gpu.r188_node5_confinement','dispatch',
            '--config',str(CONTROL/'GUARD.json')],cwd=SOURCE,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(SOURCE),PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    write(CONTROL/'DISPATCHED.json',dict(pid=supervisor.pid,dispatched_unix=time.time(),
        status='DISPATCHED_NOT_YET_LOADED',hard_end_unix=plan['hard_end_unix'],
        native_signals=[dict(pid=PID,start_ticks=START,signal='SIGTERM')]))
    print(json.dumps(read(CONTROL/'DISPATCHED.json')),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('preflight','prepare','replace'))
    parser.add_argument('--commit')
    arguments = parser.parse_args()
    if arguments.mode == 'preflight':
        preflight()
    elif arguments.mode == 'prepare':
        prepare(arguments.commit)
    else:
        replace()
