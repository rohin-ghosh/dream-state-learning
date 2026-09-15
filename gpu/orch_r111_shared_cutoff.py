"""Independent, score-blind lifecycle guard for the two owned shared route actors."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import sys
import time


BRANCHES = ('F1', 'F2', 'F3', 'F4', 'A1', 'A2', 'A3', 'A4')
OWNED = {'F1': (0, 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a'),
         'A1': (4, 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d')}
MODULE = 'gpu.orch_r111_route_pair_shared'
DRAIN = 1789490700
CUTOFF = 1789491300
FINAL = 1789491600


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def bound(reference):
    require(sha(reference['path']) == reference['sha256'], 'artifact_binding')
    return read(reference['path'])


def write(path, value, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                command_sha256=sha(directory / 'cmdline'), ppid=int(fields[1]))


def alive(expected):
    try:
        observed = identity(expected['pid'])
        state = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        return all(observed[key] == value for key, value in expected.items() if key != 'ppid') and state != 'Z'
    except (FileNotFoundError, ProcessLookupError):
        return False


def host_binding():
    material = Path('/etc/machine-id').read_bytes() + Path('/proc/sys/kernel/random/boot_id').read_bytes()
    return hashlib.sha256(material).hexdigest()


def route_process(pid, spec, phase):
    observed = identity(pid)
    arguments = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
    if phase == 'readout':
        marker = arguments.index(b'-m')
        require(arguments[marker:marker + 5] == [b'-m', MODULE.encode(), b'readout', b'--root', spec['root'].encode()],
                'exact_owned_readout_command')
        suffix = arguments[marker + 5:-1]
        require(len(suffix) == 6 and suffix[::2] == [b'--sleep-index', b'--checkpoint', b'--scope'],
                'exact_owned_readout_options')
        require(suffix[1].isdigit() and suffix[5] in (b'dev', b'open', b'final') and
                Path(suffix[3].decode()).resolve().is_relative_to(Path(spec['root']).resolve()),
                'owned_readout_checkpoint_and_scope')
    else:
        require(arguments[-6:] == [b'-m', MODULE.encode(), phase.encode(), b'--root', spec['root'].encode(), b''],
                'exact_owned_route_command')
    environment = dict(item.split(b'=', 1) for item in
                       (Path('/proc') / str(pid) / 'environ').read_bytes().split(b'\0') if b'=' in item)
    require(observed['uid'] == spec['uid'] == os.getuid(), 'owned_uid_only')
    require(environment.get(b'CUDA_VISIBLE_DEVICES') == spec['uuid'].encode(), 'owned_UUID_CVD')
    require(environment.get(b'PYTHONPATH', b'').split(b':')[0] == spec['source_root'].encode(),
            'exact_frozen_route_source')
    return observed


def mapping(physical, uuid):
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
        '--format=csv,noheader,nounits'], text=True, timeout=15).splitlines()
    require([str(physical), uuid] in [[part.strip() for part in row.split(',')] for row in rows],
            'physical_UUID')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1, 'kernel_minor_UUID')
    device = (Path('/dev') / ('nvidia' + str(matches[0]))).stat()
    require(stat.S_ISCHR(device.st_mode) and os.minor(device.st_rdev) == matches[0], 'kernel_device')
    return dict(physical=physical, uuid=uuid, kernel_minor=matches[0])


def common_snapshot(common):
    common = Path(common)
    state = read(common / 'STATE.json')
    folder = common / f"generation_{state['generation']:06d}"
    return dict(state=state, present=[branch for branch in BRANCHES if (folder / (branch + '.json')).exists()],
                sleep_started=(folder / 'sleep/START.json').exists(),
                sleep_complete=(folder / 'sleep/COMPLETE.json').exists())


def checkpoint_evidence(common):
    snapshot = common_snapshot(common)
    checkpoint = snapshot['state']['checkpoint']
    require(sha(checkpoint['path']) == checkpoint['path_sha256'] and
            sha(checkpoint['optimizer_path']) == checkpoint['optimizer_path_sha256'], 'committed_checkpoint_bytes')
    folder = Path(common) / f"generation_{snapshot['state']['generation']:06d}" / 'sleep'
    return dict(**snapshot, checked_unix=time.time(), artifacts={name: ref(folder / name)
        for name in ('START.json', 'UPDATES.jsonl', 'ENCODING.json', 'COMPLETE.json') if (folder / name).exists()},
        no_state_rewrite=True, incomplete_updates_not_committed=bool(snapshot['sleep_started'] and not snapshot['sleep_complete']))


def serial_workload(common, snapshot, now, memory):
    generation = snapshot['state']['generation']
    folder = Path(common) / f'generation_{generation:06d}' / 'sleep'
    result = dict(generation=generation, observed_unix=now, started=snapshot['sleep_started'],
                  completed_updates=0, seconds_per_update=None, measurement='UNKNOWN_NOT_STARTED')
    if not snapshot['sleep_started']:
        return result
    start = read(folder / 'START.json')
    result.update(started_unix=start['started_unix'], submitted_new_rows=start['row_count'],
                  submitted_history_rows=start['rehearsal_rows'], measurement='AWAITING_TIMED_UPDATE_WINDOW')
    if (folder / 'ENCODING.json').exists():
        encoded = read(folder / 'ENCODING.json')
        result.update(encoded_new_rows=encoded['new'], encoded_history_rows=encoded['old'],
                      rejected_rows=len(encoded['rejected']), scheduled_updates=16 * encoded['new'] + encoded['old'])
    path = folder / 'UPDATES.jsonl'
    updates = []
    if path.exists():
        lines = path.read_bytes().splitlines(keepends=True)
        updates = [json.loads(line) for line in lines if line.endswith(b'\n')]
    if updates:
        result['completed_updates'] = updates[-1]['step']
        result['child_token_exposures'] = updates[-1]['child_token_exposures']
        result['anchor_token_exposures'] = updates[-1]['anchor_token_exposures']
        key = 'serial_window_' + str(generation)
        memory.setdefault(key, dict(observed_unix=now, step=updates[-1]['step']))
        previous = memory[key]
        elapsed, steps = now - previous['observed_unix'], updates[-1]['step'] - previous['step']
        if elapsed >= 30 and steps > 0:
            result.update(seconds_per_update=elapsed / steps, observed_interval_seconds=elapsed,
                          observed_interval_updates=steps, measurement='TIMED_STEP_COUNT_DELTA_NOT_ROW_TIMESTAMPS')
    if 'scheduled_updates' in result:
        result['remaining_scheduled_updates'] = max(0, result['scheduled_updates'] - result['completed_updates'])
    return result


def prepare(common, directory):
    common, directory = Path(common).resolve(strict=True), Path(directory).resolve()
    initialized = read(common / 'INITIALIZED.json')
    adoption = read(common / 'ADOPTION.json')
    config = read(common / 'CONFIG.json')
    require(set(config['branches']) == set(initialized['bindings']) == set(BRANCHES), 'eight_branches')
    require(time.time() < DRAIN, 'prepare_before_scheduled_drain')
    peers, routes = {}, {}
    for branch in BRANCHES:
        root = Path(config['branches'][branch]['root']).resolve(strict=True)
        ready = bound(adoption['readiness'][branch])
        require(ready['root'] == str(root), 'peer_root_binding')
        family = {'1': 'route', '2': 'math', '3': 'code', '4': 'grid'}[branch[1]]
        terminal = 'TERMINAL.json' if family == 'route' else 'SHARED_TERMINAL.json'
        loaded = {'route': 'ACTOR_READY.json', 'math': 'SHARED_MODEL_LOADED.json',
                  'code': 'SHARED_ACTOR_READY.json', 'grid': 'SHARED_LOADED.json'}[family]
        era = None
        if family == 'grid':
            era = ref(root / 'shared_repair_v1/READY.json')
            repaired = bound(era)
            require(repaired['terminal_filename'] == 'R118_SHARED_REPAIR_TERMINAL.json', 'actual_grid_repair_terminal')
            terminal, loaded = repaired['terminal_filename'], 'shared_repair_v1/LOADED.json'
        peers[branch] = dict(root=str(root), family=family, bounds=adoption['branch_bounds'][branch],
                             readiness=adoption['readiness'][branch], terminal=terminal, loaded=loaded, era=era)
        if branch not in OWNED:
            continue
        physical, uuid = OWNED[branch]
        require(str(root) == f'/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_{physical}_attempt1', 'owned_root')
        plan = read(root / 'PLAN.json')
        require(plan['physical'] == physical and plan['uuid'] == uuid and
                plan['bounds'] == adoption['branch_bounds'][branch] and plan['parent_wait_seconds'] == 120,
                'unchanged_original_route_bounds')
        require(plan['shared_learner'] == initialized['bindings'][branch], 'actual_initialized_route')
        spec = dict(root=str(root), uid=os.getuid(), uuid=uuid, source_root=ready['successor_source'],
                    plan=ref(root / 'PLAN.json'), bounds=plan['bounds'], mapping=mapping(physical, uuid))
        actor = route_process(read(root / 'ACTOR_READY.json')['pid'], spec, 'run')
        spec.update(supervisor=route_process(actor['ppid'], spec, 'supervise'), initial_actor=actor)
        routes[branch] = spec
    result = dict(schema='R118_ROUTE_CUTOFF_V1', authorization='R118_USER_1238_NONMATERIAL_LIFECYCLE_REPAIR',
        source=ref(Path(__file__).resolve()), common=str(common), directory=str(directory), host_sha256=host_binding(),
        immutable={name: ref(common / name) for name in ('CONFIG.json', 'ADOPTION.json', 'INITIALIZED.json')},
        peers=peers, routes=routes, created_unix=time.time(), drain_unix=DRAIN, train_cutoff_unix=CUTOFF,
        freeze_unix=CUTOFF - 60, controller_end_unix=CUTOFF, final_unix=FINAL, poll_seconds=5,
        crash_grace_seconds=300, no_progress_alarm_seconds=600, no_new_quota=True,
        no_parent_wait_change=True, signals_only=['F1', 'A1'], initial_checkpoint=checkpoint_evidence(common))
    write(directory / 'CONTROL.json', result)
    return ref(directory / 'CONTROL.json')


def counts(peer, cache):
    root, family = Path(peer['root']), peer['family']
    if family == 'math':
        value = read(root / 'COUNTERS.json')
        return dict(native=value['native'], parent=value['parent'])
    if family == 'code':
        entries = cache.setdefault(str(root), {})
        for path in (root / 'reservations').glob('*.json'):
            if path.name not in entries:
                entries[path.name] = read(path)['kind']
        result = Counter(entries.values())
    else:
        ledger = root / ('RESERVATIONS.jsonl' if family == 'route' else 'LEDGER.jsonl')
        result = Counter(json.loads(line)['kind'] for line in ledger.read_text().splitlines() if line.strip())
    return dict(native=result['NATIVE'], parent=result['PARENT'])


def peer_observation(peer, cache):
    root = Path(peer['root'])
    terminal = root / peer['terminal']
    loaded = root / peer['loaded']
    native = None
    if loaded.exists():
        record = read(loaded)
        process = record.get('process', {})
        pid = record.get('pid') or (process.get('pid') if isinstance(process, dict) else process[1])
        if pid and (Path('/proc') / str(pid)).exists():
            native = identity(pid)
            arguments = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
            require(str(root).encode() in arguments and native['uid'] == os.getuid(), 'peer_native_root_UID')
            if isinstance(process, list):
                require([native['boot_id'], native['pid'], int(native['start_ticks'])] == process, 'peer_native_start')
            elif process:
                require(all(str(native[key]) == str(value) for key, value in process.items() if key in native), 'peer_native_identity')
            if not alive(native):
                native = None
    pattern = {'route': 'cycle_*/COMPLETE.json', 'math': 'cycle*/COMPLETE.json',
               'code': 'cycles/C*_COMPLETE.json', 'grid': 'cycles/*/CYCLE_COMPLETE.json'}[peer['family']]
    completed = sorted(root.glob(pattern))
    completed_cycle = read(completed[-1]).get('cycle', 0) if completed else 0
    return dict(counts=counts(peer, cache), native=native, completed_cycle=completed_cycle,
                terminal=ref(terminal) if terminal.exists() else None, observed_unix=time.time())


def classify(peer, observation, now, missing_since, branch):
    bounds = peer['bounds']
    deadlines = [bounds[key] for key in ('train_end_unix', 'native_end_unix', 'hard_end_unix', 'hard_deadline_unix') if key in bounds]
    if deadlines and now >= min(deadlines):
        return 'ORIGINAL_CLOCK_BOUND'
    if bounds.get('cycles') is not None and observation.get('completed_cycle', 0) >= bounds['cycles']:
        return 'ORIGINAL_CYCLE_CAP'
    for kind, names in [('native', ('native_calls', 'native_cap', 'max_native_calls')),
                        ('parent', ('parent_calls', 'parent_cap', 'max_parent_calls'))]:
        maximum = next((bounds[name] for name in names if name in bounds), None)
        if maximum is not None and observation['counts'][kind] is not None and observation['counts'][kind] >= maximum:
            return 'ORIGINAL_' + kind.upper() + '_CAP'
    if observation['terminal']:
        return 'ACTUAL_ERA_TERMINAL'
    if observation['native'] is None:
        missing_since.setdefault(branch, now)
        return 'NATIVE_ABSENCE' if now - missing_since[branch] >= 300 else None
    missing_since.pop(branch, None)
    return None


def decision(control, snapshot, observations, now, memory):
    if now >= control['freeze_unix']:
        return dict(action='STOP', reason='COMMON_TRAIN_DEADLINE', interrupted_allowed=True)
    reasons = {}
    for branch, peer in control['peers'].items():
        if branch not in observations:
            continue
        reason = classify(peer, observations[branch], now, memory.setdefault('missing_since', {}), branch)
        if reason:
            reasons[branch] = reason
    missing = set(BRANCHES) - set(snapshot['present'])
    unavailable = {branch: reason for branch, reason in reasons.items() if branch in missing}
    if unavailable and not snapshot['sleep_started']:
        return dict(action='STOP', reason='PEER_CANNOT_COMPLETE_BARRIER', peers=unavailable,
                    generation=snapshot['state']['generation'], interrupted_allowed=True)
    if reasons or now >= control['drain_unix']:
        memory.setdefault('drain_generation', snapshot['state']['generation'])
        memory.setdefault('drain_reason', reasons or {'schedule': '1645_DRAIN_REVIEW'})
    if 'drain_generation' in memory:
        if snapshot['state']['generation'] > memory['drain_generation']:
            return dict(action='DRAIN_STOP', reason='COMMITTED_GENERATION_DRAIN', interrupted_allowed=False)
        return dict(action='DRAIN', reason=memory['drain_reason'], target_generation=memory['drain_generation'] + 1)
    return dict(action='MONITOR', reason='HEALTHY_OR_BOUNDED_RECOVERY')


def route_tree(spec):
    supervisor = spec['supervisor']
    require(alive(supervisor), 'original_supervisor_identity')
    require(route_process(supervisor['pid'], spec, 'supervise') == supervisor, 'same_supervisor')
    owned = [dict(role='supervisor', identity=supervisor)]
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            observed = identity(int(directory.name))
            if observed['ppid'] == supervisor['pid']:
                require(route_process(observed['pid'], spec, 'run') == observed, 'owned_actor_child')
                owned.append(dict(role='actor', identity=observed))
        except (FileNotFoundError, ProcessLookupError):
            continue
    require(len(owned) <= 2, 'one_actor_per_supervisor')
    actor_ids = {item['identity']['pid'] for item in owned if item['role'] == 'actor'}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            observed = identity(int(directory.name))
            if observed['ppid'] in actor_ids:
                owned.append(dict(role='readout', identity=route_process(observed['pid'], spec, 'readout')))
        except (FileNotFoundError, ProcessLookupError):
            continue
    return owned


def signal_bound(descriptor, expected, signum):
    require(alive(expected), 'identity_before_signal')
    signal.pidfd_send_signal(descriptor, signum)


def exited(descriptor, timeout=0):
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    return bool(poller.poll(max(0, int(timeout * 1000))))


def wait_stopped(descriptor, expected):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if exited(descriptor):
            return
        require(alive(expected), 'identity_while_freezing')
        state = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        if state in ('T', 't'):
            return
        time.sleep(.01)
    raise ValueError('owned_freeze_not_observed')


def terminate_tree(spec, output, reason, grace_seconds=20):
    output = Path(output)
    require(sha(spec['plan']['path']) == spec['plan']['sha256'], 'unchanged_route_PLAN')
    orphan_targets = []
    if not alive(spec['supervisor']):
        candidates = [dict(role='actor', identity=spec['initial_actor'])]
        for path in output.parent.glob('attempt_*/PINNED_STOP.json'):
            saved = read(path)
            require(saved['processes'][0]['identity'] == spec['supervisor'], 'recorded_stop_supervisor')
            candidates.extend(saved['processes'][1:])
        live_path = output.parent / 'LIVE_IDENTITIES.json'
        if live_path.exists():
            saved = read(live_path)
            require(saved['processes'][0]['identity'] == spec['supervisor'], 'recorded_live_supervisor')
            candidates.extend(saved['processes'][1:])
        seen = set()
        for candidate in candidates:
            if candidate['identity']['pid'] not in seen and alive(candidate['identity']):
                current = route_process(candidate['identity']['pid'], spec,
                                        'readout' if candidate['role'] == 'readout' else 'run')
                require(all(current[key] == value for key, value in candidate['identity'].items() if key != 'ppid'),
                        'recorded_orphan_identity')
                orphan_targets.append(candidate)
                seen.add(candidate['identity']['pid'])
        for path in Path(spec['root']).glob('actor_attempt_*.json'):
            pid = read(path)['pid']
            if (Path('/proc') / str(pid)).exists():
                try:
                    candidate = route_process(pid, spec, 'run')
                except (FileNotFoundError, ProcessLookupError, ValueError):
                    continue
                require(not alive(candidate) or pid in seen, 'newer_orphan_actor_needs_identity_review')
        if not orphan_targets:
            return dict(status='PREDECESSOR_ALREADY_EXITED', checked_unix=time.time(), signals=[])
    handles, stopped, sent = [], [], []
    try:
        if orphan_targets:
            targets = [dict(role='supervisor', identity=spec['supervisor'])] + orphan_targets
        else:
            supervisor = spec['supervisor']
            descriptor = os.pidfd_open(supervisor['pid'])
            handles.append((descriptor, dict(role='supervisor', identity=supervisor)))
            signal_bound(descriptor, supervisor, signal.SIGSTOP)
            stopped.append((descriptor, supervisor))
            wait_stopped(descriptor, supervisor)
            targets = route_tree(spec)
        for target in targets[1:]:
            descriptor = os.pidfd_open(target['identity']['pid'])
            handles.append((descriptor, target))
            signal_bound(descriptor, target['identity'], signal.SIGSTOP)
            stopped.append((descriptor, target['identity']))
            wait_stopped(descriptor, target['identity'])
        if not orphan_targets:
            known = {target['identity']['pid'] for unused, target in handles}
            for target in route_tree(spec):
                if target['identity']['pid'] not in known:
                    require(target['role'] == 'readout', 'only_late_owned_readout_child')
                    descriptor = os.pidfd_open(target['identity']['pid'])
                    handles.append((descriptor, target))
                    signal_bound(descriptor, target['identity'], signal.SIGSTOP)
                    stopped.append((descriptor, target['identity']))
                    wait_stopped(descriptor, target['identity'])
                    targets.append(target)
        write(output / 'PINNED_STOP.json', dict(reason=reason, processes=targets, frozen_unix=time.time()))
        for descriptor, target in handles:
            if not exited(descriptor):
                signal_bound(descriptor, target['identity'], signal.SIGTERM)
                try:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                except ProcessLookupError:
                    pass
                sent.append(dict(pid=target['identity']['pid'], signal='SIGTERM', unix=time.time()))
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline and any(not exited(descriptor) for descriptor, unused in handles):
            time.sleep(.05)
        for descriptor, target in handles:
            if not exited(descriptor):
                signal_bound(descriptor, target['identity'], signal.SIGKILL)
                sent.append(dict(pid=target['identity']['pid'], signal='SIGKILL_AFTER_BOUNDED_GRACE', unix=time.time()))
        all_exited = all(exited(descriptor, 5) for descriptor, unused in handles)
        return dict(status='RELEASED' if all_exited else 'EXIT_UNCONFIRMED', processes=targets, signals=sent,
                    released_unix=time.time() if all_exited else None, no_fake_terminal=True, reason=reason)
    finally:
        for descriptor, expected in stopped:
            if not exited(descriptor) and alive(expected):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        for descriptor, unused in handles:
            os.close(descriptor)


def stop_routes(control, reason, trigger=None):
    directory = Path(control['directory'])
    with (directory / 'STOP.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        snapshot = common_snapshot(control['common']) if trigger is not None or reason == 'COMMITTED_GENERATION_DRAIN' else None
        if trigger is not None and trigger['reason'] == 'PEER_CANNOT_COMPLETE_BARRIER':
            if (snapshot['state']['generation'] != trigger['generation'] or snapshot['sleep_started'] or
                    not (set(trigger['peers']) - set(snapshot['present']))):
                return False
        if reason == 'COMMITTED_GENERATION_DRAIN' and snapshot['sleep_started']:
            return False
        def finish_branch(branch):
            spec = control['routes'][branch]
            destination = directory / branch
            if (destination / 'DISPOSITION.json').exists():
                return branch, read(destination / 'DISPOSITION.json')
            destination.mkdir(exist_ok=True)
            attempt = destination / ('attempt_' + str(time.time_ns()))
            attempt.mkdir()
            receipt = terminate_tree(spec, attempt, reason)
            write(destination / 'DISPOSITION.json', receipt)
            return branch, receipt
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = dict(executor.map(finish_branch, ('F1', 'A1')))
        require(all(item['status'] in ('RELEASED', 'PREDECESSOR_ALREADY_EXITED') for item in receipts.values()),
                'all_owned_exits_confirmed')
        write(directory / 'CHECKPOINT_AFTER_STOP.json', checkpoint_evidence(control['common']))
        write(directory / 'COMPLETED.json', dict(finished_unix=time.time(), reason=reason,
            peers_not_signalled=True, no_final_run=True, no_caps_or_STATE_changed=True,
            latest_checkpoint=ref(directory / 'CHECKPOINT_AFTER_STOP.json')))
        return True


def validate(control):
    require(control['schema'] == 'R118_ROUTE_CUTOFF_V1' and control['signals_only'] == ['F1', 'A1'], 'scope')
    require(set(control['routes']) == set(OWNED), 'only_owned_routes')
    require(control['host_sha256'] == host_binding(), 'hashed_host_binding')
    require(control['drain_unix'] == DRAIN and control['train_cutoff_unix'] == CUTOFF and
            control['freeze_unix'] == CUTOFF - 60 and control['controller_end_unix'] == CUTOFF, 'fixed_common_clock')
    for reference in control['immutable'].values():
        bound(reference)
    require(sha(control['source']['path']) == control['source']['sha256'], 'immutable_controller_source')
    for branch, spec in control['routes'].items():
        physical, uuid = OWNED[branch]
        require(spec['mapping']['physical'] == physical and spec['uuid'] == uuid and
                spec['root'] == f'/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_{physical}_attempt1', 'exact_route_allocation')


def run(control_path, expected_sha, mode):
    control = bound(dict(path=str(control_path), sha256=expected_sha))
    validate(control)
    directory = Path(control['directory'])
    with (directory / (mode + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write(directory / (mode + '_STARTED.json'), dict(identity=identity(os.getpid()), mode=mode,
            control=ref(control_path), started_unix=time.time(), healthy_lanes_not_stopped=True))
        memory, cache = {}, {}
        while not (directory / 'COMPLETED.json').exists():
            now = time.time()
            if now < control['freeze_unix']:
                for branch, spec in control['routes'].items():
                    try:
                        write(directory / branch / 'LIVE_IDENTITIES.json',
                              dict(processes=route_tree(spec), observed_unix=now), replace=True)
                    except (OSError, ValueError):
                        pass
            if now >= control['freeze_unix']:
                try:
                    if stop_routes(control, 'COMMON_TRAIN_DEADLINE'):
                        break
                except (OSError, ValueError, KeyError) as error:
                    write(directory / (mode + '_STOP_ERROR.json'), dict(error_type=type(error).__name__,
                        reason=str(error), observed_unix=time.time(), not_claimed_released=True), replace=True)
            elif mode == 'monitor':
                try:
                    snapshot = common_snapshot(control['common'])
                    observations, errors = {}, {}
                    for branch, peer in control['peers'].items():
                        try:
                            observations[branch] = peer_observation(peer, cache)
                        except (OSError, ValueError, KeyError) as error:
                            errors[branch] = type(error).__name__
                            observations[branch] = dict(native=None, counts=dict(native=None, parent=None),
                                                       terminal=None, completed_cycle=0, counters_unknown=True)
                    action = decision(control, snapshot, observations, now, memory)
                    serial = serial_workload(control['common'], snapshot, now, memory)
                    progress = dict(generation=snapshot['state']['generation'],
                        counts={branch: item['counts'] for branch, item in observations.items()},
                        submitted=snapshot['present'])
                    update_path = Path(control['common']) / f"generation_{snapshot['state']['generation']:06d}/sleep/UPDATES.jsonl"
                    progress['update_mtime_ns'] = update_path.stat().st_mtime_ns if update_path.exists() else None
                    if progress != memory.get('last_progress'):
                        memory.update(last_progress=progress, last_progress_unix=now)
                    alarm = now - memory.get('last_progress_unix', now) >= control['no_progress_alarm_seconds']
                    write(directory / 'STATUS.json', dict(observed_unix=now, decision=action, peers=observations,
                        observation_errors=errors, memory=memory, common=snapshot,
                        serial_workload=serial, no_observed_progress_alarm=alarm, no_semantic_or_score_fields=True), replace=True)
                    if action['action'] in ('STOP', 'DRAIN_STOP'):
                        if stop_routes(control, action['reason'], trigger=action):
                            break
                except (OSError, ValueError, KeyError) as error:
                    write(directory / 'MONITOR_ERROR.json', dict(error_type=type(error).__name__,
                        observed_unix=time.time(), independent_deadline_fuse_still_required=True), replace=True)
            if time.time() >= control['controller_end_unix']:
                write(directory / (mode + '_DEADLINE_FAILURE.json'), dict(observed_unix=time.time(),
                    stopped=False, needs_immediate_owner_inspection=True))
                break
            time.sleep(min(control['poll_seconds'], max(.05, control['freeze_unix'] - time.time())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'monitor', 'fuse'))
    parser.add_argument('--common', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--control', type=Path)
    parser.add_argument('--control-sha256')
    args = parser.parse_args()
    if args.mode == 'prepare':
        print(json.dumps(prepare(args.common, args.directory)))
    else:
        run(args.control, args.control_sha256, args.mode)


if __name__ == '__main__':
    main()
