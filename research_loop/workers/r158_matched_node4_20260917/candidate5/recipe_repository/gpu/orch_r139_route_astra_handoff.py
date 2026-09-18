"""Exact-state route consumer handoff; new parent model, no logical-life reset."""

import argparse
from collections import Counter
from copy import deepcopy
import fcntl
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1')
SOURCE = Path('/localhome/local-rohing/orch_r121_route_independent_20260915_v2/source')
PLAN = 'R121_INDEPENDENT_PLAN_V2.json'
PLAN_SHA = '9a5537780508ac451125d9bc4afde85a45a021fb762498efdf05c070513b884e'
RUN_SHA = 'd1b0de12edc1ad45bbc1b3d20def7f0084198310ef0a7c9ee2db3f6bc6095673'
MODEL = 'openai/openai/gpt-6-astra'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'bound_file_changed')
    return read(reference['path'])


def identity(pid):
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], cmdline_sha256=sha(proc / 'cmdline'))


def load_native():
    require(sha(ROOT / PLAN) == PLAN_SHA, 'original_plan_changed')
    require(sha(SOURCE / 'gpu/orch_r121_route_independent.py') == RUN_SHA, 'frozen_native_source_changed')
    sys.path.insert(0, str(SOURCE))
    native = importlib.import_module('gpu.orch_r121_route_independent')
    require(Path(native.__file__).resolve() == SOURCE / 'gpu/orch_r121_route_independent.py',
        'exact_loaded_frozen_native')
    return native


def no_future_charges(rows, cycle, sleeps):
    return all(row.get('cycle', cycle) <= cycle and row.get('sleep', sleeps) <= sleeps for row in rows)


def reconstruct_context(root, first_cycle, last_cycle):
    root = Path(root)
    parent_history, head_settings, consumed = [], {}, set()
    initial = root / 'PENDING_TRIPLE.json'
    if initial.exists():
        pending = read(initial)
        if pending and pending['intervention']['status'] == 'COMPLETE':
            parent_history.append(pending['intervention']['parent_text'])
    for cycle in range(first_cycle, last_cycle + 1):
        calls = sorted((root / f'cycle_{cycle:04d}').glob('CALL_*.json'))
        require(bool(calls), 'missing_completed_cycle_calls')
        for path in calls:
            call = read(path)
            require('response' in call and 'finished_unix' in call, 'unfinished_native_call')
            for identifier in call['parent_delivery_ids']:
                require(identifier not in consumed, 'duplicate_parent_consumption')
                consumed.add(identifier)
                arrival = read(root / 'R121_PARENT_DELIVERY' / (identifier + '.applied.json'))
                if arrival['status'] == 'COMPLETE':
                    parent_history.append(arrival['parent_text'])
                if arrival.get('head_settings', {}).get('status') == 'BOUND_REQUESTED_SETTINGS':
                    head_settings = arrival['head_settings']
            require(call.get('head_settings', {}) == head_settings, 'reconstructed_head_state_mismatch')
        parent_history = parent_history[-2:]
    return dict(parent_history=parent_history, head_settings=head_settings,
        consumed_parent_ids=sorted(consumed))


def snapshot(root, original, cycle):
    root = Path(root)
    output = root / f'cycle_{cycle:04d}'
    complete = read(output / 'COMPLETE.json')
    checkpoint_path = output / 'checkpoint/CHECKPOINT.json'
    checkpoint = read(checkpoint_path)
    require(checkpoint['complete'] and checkpoint['cycle'] == cycle == complete['cycle'], 'completed_cycle_binding')
    require(checkpoint['sleeps'] == complete['sleeps'], 'sleep_cursor_binding')
    require(read(output / 'SLEEP.json')['checkpoint_sha256'] == sha(checkpoint_path)
        == read(root / 'OWN_CARRY.json')['checkpoint_sha256'], 'reflection_checkpoint_binding')
    state_path = checkpoint_path.parent / 'optimizer_rng.pt'
    require(sha(state_path) == checkpoint['optimizer_rng_sha256'], 'exact_optimizer_rng')
    for name, expected in checkpoint['adapter']['files']:
        require(Path(name).name == name and sha(Path(checkpoint['adapter']['path']) / name) == expected,
            'adapter_file_changed')
    rows = [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines() if line.strip()]
    require(no_future_charges(rows, cycle, checkpoint['sleeps']), 'already_charged_next_cycle')
    future = [path for path in root.glob('cycle_*') if int(path.name.split('_')[1]) > cycle]
    require(len(future) <= 1, 'multiple_future_cycles')
    empty_start = None
    if future:
        require(future[0].name == f'cycle_{cycle+1:04d}' and
            {path.name for path in future[0].iterdir()} == {'START.json'}, 'only_uncharged_START_adoptable')
        empty_start = ref(future[0] / 'START.json')
    history = bound(original['history'])
    metrics = dict(original['inherited_metrics'])
    preserved = {str(root / PLAN): sha(root / PLAN), str(root / 'OWN_CARRY.json'): sha(root / 'OWN_CARRY.json'),
        str(root / 'RESERVATIONS.jsonl'): sha(root / 'RESERVATIONS.jsonl'),
        str(checkpoint_path): sha(checkpoint_path), str(state_path): sha(state_path)}
    for number in range(original['next_cycle'], cycle + 1):
        folder = root / f'cycle_{number:04d}'
        require(read(folder / 'COMPLETE.json')['cycle'] == number, 'uncommitted_history')
        addition = read(folder / 'ROWS.json')
        for row in addition:
            require(sha(row['source_call_path']) == row['source_call_sha256'], 'rehearsal_capture_changed')
        history.extend(addition)
        sleep = read(folder / 'SLEEP.json')
        metrics['optimizer_steps'] += sleep['updates']
        metrics['child_token_exposures'] += sleep['child_token_exposure_including_eos']
        metrics['anchor_token_exposures'] += sleep['anchor_token_exposure_including_eos']
        for name in ('ROWS.json', 'SLEEP.json', 'COMPLETE.json'):
            preserved[str(folder / name)] = sha(folder / name)
    context = reconstruct_context(root, original['next_cycle'], cycle)
    for path in (root / 'R121_PARENT_DELIVERY').glob('*.applied.json'):
        arrival = read(path)
        if arrival['id'] not in context['consumed_parent_ids']:
            require(arrival['status'] == 'MISSING', 'unrecorded_parent_context_before_pause')
        preserved[str(path)] = sha(path)
    if empty_start:
        preserved[empty_start['path']] = empty_start['sha256']
    return dict(schema='R139_EXACT_ROUTE_BOUNDARY_V1', root=str(root), completed_cycle=cycle,
        next_cycle=cycle+1, sleeps=checkpoint['sleeps'], checkpoint=ref(checkpoint_path),
        optimizer_rng=ref(state_path), adapter=checkpoint['adapter'], history=history,
        context=context, metrics=metrics, empty_successor_start=empty_start,
        preserved=preserved, ledger_counts=dict(Counter(row['kind'] for row in rows)),
        parent_high_water=sum(row['kind'] == 'PARENT' for row in rows), observed_unix=time.time(),
        logical_life_reset=False, historical_requests_replayed=False)


def resume_source(source):
    replacements = {
        "require(not (root/'R121_INDEPENDENT_ACTOR_READY.json').exists(), 'one_attempt_no_automatic_restart')":
            "require(not (root/'R139_INDEPENDENT_ACTOR_READY.json').exists(), 'one_prospective_handoff')",
        "history = read(root/'R121_HISTORY.json')": "history = read(plan['history']['path'])",
        "root/'R121_INDEPENDENT_ANCHOR_INVENTORY.json'": "root/'R139_INDEPENDENT_ANCHOR_INVENTORY.json'",
        "root/'R121_INDEPENDENT_ACTOR_READY.json'": "root/'R139_INDEPENDENT_ACTOR_READY.json'",
        "parent_history = []\n    head_settings = {}":
            "parent_history = deepcopy(plan['restored_context']['parent_history'])\n    head_settings = deepcopy(plan['restored_context']['head_settings'])",
        "    if pending and pending['intervention']['status'] == 'COMPLETE':\n        parent_history.append(pending['intervention']['parent_text'])\n": "",
        "require(not output.exists(), 'never_replay_started_cycle')":
            "require(not output.exists() or adoptable_start(output, plan), 'never_replay_started_cycle')",
        "mode='EXPLICIT_INDEPENDENT_FORK_OF_COMMITTED_GEN1'": "mode='R139_SAME_LOGICAL_LIFE_ASTRA_SEGMENT'",
    }
    for before, after in replacements.items():
        require(source.count(before) == 1, 'exact_resume_source_seam:' + before[:70])
        source = source.replace(before, after, 1)
    return source


def adoptable_start(output, plan):
    reference = plan['adopt_start']
    return bool(reference and str(output / 'START.json') == reference['path'] and
        {path.name for path in output.iterdir()} == {'START.json'} and sha(reference['path']) == reference['sha256'])


def verify_stage(stage):
    stage = Path(stage)
    manifest = read(stage / 'READY.json')
    require(manifest['root'] == str(ROOT) and manifest['source_sha256'] == sha(__file__), 'immutable_handoff_source')
    require(manifest['original_plan_sha256'] == sha(ROOT / PLAN) == PLAN_SHA, 'original_plan_preserved')
    return manifest


def prepare(stage):
    stage = Path(stage)
    native = load_native()
    original = native.verify(ROOT)
    compile(resume_source(inspect.getsource(native.run)), '<r139_resume>', 'exec')
    actor = identity(read(ROOT / 'R121_INDEPENDENT_ACTOR_READY.json')['pid'])
    argv = (Path('/proc') / str(actor['pid']) / 'cmdline').read_bytes().split(b'\0')
    require(argv[-6:] == [b'-m', b'gpu.orch_r121_route_independent', b'run', b'--root', str(ROOT).encode(), b''],
        'exact_owned_original_actor')
    write(stage / 'READY.json', dict(schema='R139_ROUTE_READY_V1', root=str(ROOT),
        original_plan_sha256=PLAN_SHA, original_native_sha256=RUN_SHA, source_sha256=sha(__file__),
        actor=actor, provider=MODEL, hard_end_unix=original['bounds']['hard_end_unix'],
        prepared_unix=time.time(), new_model_calls=0, child_signals=0))
    return dict(status='CPU_SOURCE_READY', actor=actor, ready=ref(stage / 'READY.json'))


def authorize(stage):
    manifest = verify_stage(stage)
    permission = read(Path(stage) / 'GO.json')
    require(permission.get('authorized') is True and permission.get('ready_sha256') == sha(Path(stage) / 'READY.json')
        and permission.get('published_commit') and permission.get('logical_life_reset') is False,
        'published_exact_saved_state_handoff_required')
    require(time.time() < permission['expires_unix'] <= manifest['hard_end_unix'], 'handoff_authority_expired')
    return manifest, permission


def release(stage):
    stage = Path(stage)
    manifest, permission = authorize(stage)
    native = load_native()
    original = native.verify(ROOT)
    require(identity(manifest['actor']['pid']) == manifest['actor'], 'actor_identity_changed')
    descriptor = os.pidfd_open(manifest['actor']['pid'])
    stopped, released = False, False
    try:
        with (stage / 'CONTROLLER.lock').open('a') as controller:
            fcntl.flock(controller, fcntl.LOCK_EX | fcntl.LOCK_NB)
            write(stage / 'ARMED.json', dict(ready=ref(stage / 'READY.json'), authorization=ref(stage / 'GO.json'),
                armed_unix=time.time()))
            while time.time() < permission['expires_unix']:
                sleeps = sorted(ROOT.glob('cycle_*/SLEEP.json'))
                if not sleeps:
                    time.sleep(.05)
                    continue
                folder = sleeps[-1].parent
                saved = read(sleeps[-1])
                cycle = int(folder.name.split('_')[1])
                ready = all(any((native.readout_directory(ROOT, saved['sleeps'], scope) / name).exists()
                    for name in ('COMPLETE.json', 'PROCESS_RESULT.json')) for scope in ('dev', 'open'))
                if not ready:
                    time.sleep(.05)
                    continue
                with (ROOT / 'RESERVATIONS.jsonl').open('r') as ledger:
                    try:
                        fcntl.flock(ledger, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        continue
                    charges = [json.loads(line) for line in ledger if line.strip()]
                    if not no_future_charges(charges, cycle, saved['sleeps']):
                        time.sleep(.05)
                        continue
                    deadline = min(permission['expires_unix'], time.time()+30)
                    while not (folder / 'COMPLETE.json').exists() and time.time() < deadline:
                        time.sleep(.02)
                    if not (folder / 'COMPLETE.json').exists():
                        continue
                    require(identity(manifest['actor']['pid']) == manifest['actor'], 'identity_before_pause')
                    signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
                    stopped = True
                    for attempt in range(100):
                        state = (Path('/proc') / str(manifest['actor']['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
                        if state == 'T':
                            break
                        time.sleep(.01)
                    require(state == 'T', 'paused_actor_required')
                    children = Path('/proc') / str(manifest['actor']['pid']) / 'task' / str(manifest['actor']['pid']) / 'children'
                    require(not children.read_text().strip(), 'readout_child_not_yet_reaped')
                    document = snapshot(ROOT, original, cycle)
                    write(stage / 'BOUNDARY.json', document)
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                    stopped = False
                    require(bool(select.select([descriptor], [], [], 30)[0]), 'old_actor_exit_not_verified')
                    require(sha(ROOT / 'RESERVATIONS.jsonl') == document['preserved'][str(ROOT / 'RESERVATIONS.jsonl')],
                        'charge_during_retirement')
                    released = True
                    write(stage / 'RELEASED.json', dict(status='RELEASED', boundary=ref(stage / 'BOUNDARY.json'),
                        actor=manifest['actor'], released_unix=time.time(), no_force_kill=True,
                        old_signal_crash_receipt_expected=True, logical_life_reset=False))
                    return dict(status='RELEASED', next_cycle=document['next_cycle'],
                        sleeps=document['sleeps'], checkpoint=document['checkpoint'], release=ref(stage / 'RELEASED.json'))
            write(stage / 'EXPIRED.json', dict(released=False, observed_unix=time.time()))
            return dict(status='EXPIRED_NOT_RELEASED')
    finally:
        if stopped and not released:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def resume(stage):
    stage = Path(stage)
    verify_stage(stage)
    release_receipt = read(stage / 'RELEASED.json')
    boundary = bound(release_receipt['boundary'])
    for path, expected in boundary['preserved'].items():
        require(sha(path) == expected, 'boundary_data_changed_before_resume')
    native = load_native()
    original = native.verify(ROOT, gpu=True)
    checkpoint = bound(boundary['checkpoint'])
    require(sha(boundary['optimizer_rng']['path']) == checkpoint['optimizer_rng_sha256'], 'restored_optimizer_rng')
    history_path = stage / 'HISTORY.json'
    write(history_path, boundary['history'])
    plan = deepcopy(original)
    plan.pop('parent_model_substitution', None)
    plan.update(provider=MODEL, next_cycle=boundary['next_cycle'], inherited_sleeps=boundary['sleeps'],
        inherited_metrics=boundary['metrics'], history=ref(history_path),
        restored_context=boundary['context'], adopt_start=boundary['empty_successor_start'],
        fork_checkpoint=dict(path=boundary['checkpoint']['path'], path_sha256=boundary['checkpoint']['sha256'],
            optimizer_path=boundary['optimizer_rng']['path'], optimizer_path_sha256=boundary['optimizer_rng']['sha256']),
        predecessor_plan=ref(ROOT / PLAN), provider_segment='R139_PROSPECTIVE_ASTRA', logical_life_reset=False)
    write(stage / 'RESUME_PLAN.json', plan)

    def saved_verify(root, gpu=False):
        native.verify(root, gpu=gpu)
        return deepcopy(plan)

    def preserved_write(path, document):
        if plan['adopt_start'] and str(path) == plan['adopt_start']['path']:
            require(sha(path) == plan['adopt_start']['sha256'], 'empty_start_preserved')
            write(stage / 'ADOPTED_UNCHARGED_START.json', dict(original=plan['adopt_start'],
                successor_process=os.getpid(), adopted_unix=time.time(), no_old_call_replayed=True))
            return
        return native.write(path, document)

    namespace = dict(native.run.__globals__, verify=saved_verify, write=preserved_write, adoptable_start=adoptable_start)
    exec(compile(resume_source(inspect.getsource(native.run)), __file__+':exact_saved_resume', 'exec'), namespace)
    namespace['run'](ROOT)


def supervise(stage, python):
    stage = Path(stage)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_supervisor_required')
    authorize(stage)
    result = release(stage)
    if result['status'] != 'RELEASED':
        return result
    native = load_native()
    plan = native.verify(ROOT)
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(SOURCE), 'python3', '-B', '-m', 'gpu.orch_r121_route_launch', 'scan', '--root', str(ROOT)]
    scan = subprocess.run(command, capture_output=True, text=True, timeout=120)
    write(stage / 'ADMISSION_PROCESS.json', dict(returncode=scan.returncode, stdout=scan.stdout, stderr=scan.stderr))
    require(scan.returncode == 0, 'same_slot_privileged_scan_failed')
    report = json.loads(scan.stdout)
    require(report['clear'] and time.time()-report['scanned_unix'] < 30, 'fresh_same_slot_clear')
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['uuid'], PYTHONPATH=str(SOURCE),
        PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    command = ['timeout', '--signal=TERM', '--kill-after=30', str(int(plan['bounds']['hard_end_unix']-time.time())),
        python, '-B', str(Path(__file__).resolve()), 'resume', '--stage', str(stage)]
    with (stage / 'NATIVE.log').open('x') as stream:
        process = subprocess.Popen(command, env=environment, cwd=SOURCE, stdout=stream,
            stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(pid=process.pid, launched_unix=time.time(), physical=plan['physical'],
        checkpoint=read(stage / 'BOUNDARY.json')['checkpoint'], release=ref(stage / 'RELEASED.json'),
        admission=ref(stage / 'ADMISSION_PROCESS.json'), command=command, logical_life_reset=False)
    write(stage / 'LAUNCH.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'release', 'resume', 'supervise'))
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--python')
    arguments = parser.parse_args()
    if arguments.action == 'supervise':
        require(arguments.python is not None, 'native_python_required')
        result = supervise(arguments.stage, arguments.python)
    else:
        result = {'prepare': prepare, 'release': release, 'resume': resume}[arguments.action](arguments.stage)
    if result is not None:
        print(json.dumps(result, sort_keys=True))
