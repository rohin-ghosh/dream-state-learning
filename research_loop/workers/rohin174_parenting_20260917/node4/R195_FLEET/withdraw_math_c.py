"""After COMPLETE54, close parenting, preserve pending messages, resume to57."""

import fcntl
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import uuid

from math_c import HOME, SOURCE, PYTHON, WALL, host, read, require, sha, write


def records():
    return [read(path) for path in sorted((HOME / 'life/stream/records').glob('[0-9]' * 20 + '.json'))]


def run():
    host()
    started = time.time()
    deadline = min(WALL - 120, started + 4 * 3600)
    write(HOME / 'WITHDRAWAL_WAITER.json', dict(pid=os.getpid(), started_unix=started,
        deadline_unix=deadline, guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57]))
    while time.time() < deadline:
        if (HOME / 'control/EXIT.json').exists():
            break
        time.sleep(3)
    require(time.time() < deadline and read(HOME / 'control/EXIT.json')['exit_code'] == 0,
            'guided_native_completed_successfully_no_retry')
    chain = records()
    completions = {record['document']['cycle']: record for record in chain if record['kind'] == 'SLEEP_COMPLETE'}
    require(set(completions) == {52, 53, 54} and all(record['document']['status'] == 'COMPLETE'
        for record in completions.values()), 'exact_three_guided_COMPLETE_cycles')
    require(chain[-1]['kind'] == 'TERMINAL' and chain[-1]['document']['completed_sleeps'] == 54,
            'saved_phase_terminal_no_extra_generation')
    with (HOME / 'PARENT_PUBLICATION.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        write(HOME / 'PARENT_WITHDRAWAL_CLOSED.json', dict(cycle=54, closed_unix=time.time(),
            terminal_sha256=chain[-1]['sha256'], reason='Fixed three guided then three withdrawn; no success criterion'))
        registered = {record['document']['message']['id'] for record in chain if record['kind'] == 'INBOX'}
        requests = [record['document'] for record in chain if record['kind'] == 'REQUEST']
        quarantine = HOME / 'withdrawn_pending_parent_preserved'
        quarantine.mkdir()
        moved, rendered = [], []
        for path in (HOME / 'life/stream/inbox').glob('*.json'):
            message = read(path)
            if message['actor'] != 'parent' or message['speaker'] != 'Astra':
                continue
            visible = any(request.get('render_receipt', {}).get('all_history_tokens_masked') is True
                and any(message['text'] in item.get('content', '') for item in request['messages']) for request in requests)
            if message['id'] in registered:
                require(visible, 'registered_unrendered_parent_requires_exact_context_reconciliation')
                rendered.append(dict(id=message['id'], sha256=sha(path)))
                continue
            original = str(path)
            digest = sha(path)
            path.rename(quarantine / path.name)
            partial = path.with_suffix('.partial')
            if partial.exists():
                partial.rename(quarantine / partial.name)
            moved.append(dict(id=message['id'], original=original, preserved=str(quarantine / path.name), sha256=digest))
        write(HOME / 'PARENT_WITHDRAWAL_RECONCILED.json', dict(cycle=54, pending_preserved_not_deleted=moved,
            registered_parents_already_rendered=rendered, no_pending_parent_replay=True, observed_unix=time.time()))
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import NativeChild, digest
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    with StreamJournal(HOME / 'life/stream', create=False) as journal:
        checkpoint = journal.latest_checkpoint()
        state = ContinualStream.restore(checkpoint['document'], expected_sha256=checkpoint['expected_sha256'])
        require(state.pending is None and state.sleep_frontier == len(state.rows)
            and len(state.sleep_receipts) == 54, 'same_saved_COMPLETE54_state')
        model = read(HOME / 'life/checkpoints/sleep_000054/COMMIT.json')
        NativeChild.verify_checkpoint(model)
        require(digest(model['checkpoint_sha256']) == state.model_state_sha256, 'exact_saved_optimizer_RNG_adapter')
    control = HOME / 'withdrawn/control'
    control.mkdir(parents=True)
    plan = read(HOME / 'control/PLAN.json')
    plan['max_sleeps'] = 57
    write(control / 'PLAN.json', plan)
    allocation = read(HOME / 'control/ALLOCATION.json')
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), declared_unix=time.time(),
        builder_entry='Main fixed R201/R202 screen: three parent-withdrawn complete cycles after three guided')
    write(control / 'ALLOCATION.json', allocation)
    guard = read(HOME / 'control/GUARD.json')
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        attempt_dir=str(control))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=SOURCE, env=environment, check=True, timeout=60)
    bridge = read(HOME / 'BRIDGE.json')
    bridge.update(socket=str(HOME / 'cpu2.sock'), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'))
    (HOME / 'BRIDGE.json').rename(HOME / 'BRIDGE_GUIDED_COMPLETE.json')
    write(HOME / 'BRIDGE.json', bridge)
    write(HOME / 'withdrawn/BRIDGE.json', bridge)
    with (HOME / 'withdrawn/BRIDGE.log').open('x') as log:
        process = subprocess.Popen([str(PYTHON), '-B', str(HOME / 'math_c_bridge.py'),
            '--config', str(HOME / 'withdrawn/BRIDGE.json')], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    bridge_deadline = time.monotonic() + 15
    while time.monotonic() < bridge_deadline and not list((HOME / 'withdrawn/bridge_receipts').glob('READY_*.json')):
        require(process.poll() is None, 'withdrawn_CPU_bridge_alive')
        time.sleep(.1)
    require(list((HOME / 'withdrawn/bridge_receipts').glob('READY_*.json')), 'withdrawn_CPU_bridge_ready')
    command = [str(PYTHON), '-B', '-m', 'gpu.orch_r188_node4_rehome_containment',
        'contained-supervise', '--config', str(control / 'GUARD.json')]
    with (control / 'SUPERVISOR.log').open('x') as log:
        supervisor = subprocess.Popen(command, cwd=SOURCE, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(HOME / 'WITHDRAWN_DISPATCHED.json', dict(supervisor_pid=supervisor.pid, bridge_pid=process.pid,
        started_unix=time.time(), state_sha256=checkpoint['expected_sha256'], optimizer_steps=model['optimizer_steps'],
        complete54_preserved=True, source_unchanged=True, max_sleeps=57, no_parent_publications=True))
    while time.time() < deadline and not (control / 'EXIT.json').exists():
        require(supervisor.poll() is None, 'withdrawn_supervisor_exited_see_log_no_retry')
        time.sleep(5)
    require((control / 'EXIT.json').exists() and read(control / 'EXIT.json')['exit_code'] == 0,
            'withdrawn_screen_completed_no_retry')
    final = {record['document']['cycle']: record for record in records() if record['kind'] == 'SLEEP_COMPLETE'}
    require(set(final) == {52, 53, 54, 55, 56, 57}, 'fixed_six_complete_cycles')
    write(HOME / 'SCREEN_COMPLETE.json', dict(status='THREE_GUIDED_THREE_WITHDRAWN_COMPLETE',
        completed_unix=time.time(), cycles={str(cycle): record['sha256'] for cycle, record in final.items()},
        comparison_confound='MATH-C R202 structured THINK plus parentC, not parent-style-only'))


if __name__ == '__main__':
    try:
        run()
    except BaseException as error:
        write(HOME / ('WITHDRAWAL_ERROR_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
            reason=str(error), observed_unix=time.time(), no_implicit_retry=True))
        raise
