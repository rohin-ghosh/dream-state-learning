"""Reuse R181/R144 exact pidfd boundary preservation for node4 brain_guided6 only."""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

from math_c import HOME, SOURCE, OLD, OLD_ROOT, OLD_GUARD, HELPER_BUNDLE, GPU, PYTHON
from math_c import host, read, require, sha, write

RETIREMENT = HOME / 'retirement2'


def neighbor_observations(helpers):
    observations = {}
    for pid in (1742549, 1734752, 1565205, 1643508, 1995652, 1995650):
        try:
            observations[str(pid)] = helpers.identity(pid)
        except (FileNotFoundError, ProcessLookupError, ValueError) as error:
            observations[str(pid)] = dict(pid=pid, observation=type(error).__name__, signaled_by_operator=False)
    return observations

def module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


def prepare():
    host()
    rollout = module('existing_node4_rollout', HELPER_BUNDLE / 'node4_rollout.py')
    helpers = rollout.helper_module(HELPER_BUNDLE)
    strict_regular = helpers.regular

    def exact_alias(path):
        path = Path(path)
        if path == OLD_ROOT or OLD_ROOT in path.parents:
            require(OLD_ROOT.resolve() == OLD / 'run1', 'exact_R188_logical_backing_binding')
            expected = OLD / 'run1' / path.relative_to(OLD_ROOT)
            require(path.resolve() == expected, 'no_nested_alias_or_namespace_substitution')
            return strict_regular(expected)
        return strict_regular(path)

    helpers.regular = exact_alias
    config, plan, original = helpers.originals(OLD_GUARD)
    require(plan['root'] == str(OLD_ROOT) and plan['source_root'] == str(OLD / 'source')
            and plan['physical'] == 6 and plan['gpu_uuid'] == GPU, 'only_brain_guided6')
    actor = helpers.identity(2001674)
    require(actor['start_ticks'] == '25805852', 'Main_selected_native_identity')
    timer = helpers.identity(actor['parent'])
    supervisor = helpers.identity(timer['parent'])
    pair = dict(actor=actor, timer=timer, supervisor=supervisor)
    expected = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(OLD_GUARD)]
    require(actor['argv'] == expected and timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and timer['argv'][4:] == expected and actor['group'] == timer['group'] == timer['pid'],
            'exact_native_timeout_ancestry')
    require(supervisor['argv'] == [str(PYTHON), '-B', '-m', 'gpu.orch_r188_node4_rehome_containment',
            'contained-native', '--config', str(OLD_GUARD)], 'exact_receiving_supervisor')
    launch = read(Path(config['attempt_dir']) / 'LAUNCH.json')
    require(launch['pid'] == timer['pid'] and launch['parent_start_ticks'] == timer['start_ticks']
            and launch['guard_sha256'] == sha(OLD_GUARD) and launch['plan_sha256'] == config['plan_sha256'],
            'original_launch_identity_binding')
    for process in pair.values():
        require(process['uid'] == 2524 and process['cwd'] == str(OLD / 'source')
                and process['cgroup'] == actor['cgroup'] and process['boot_id'] == actor['boot_id']
                and 'CUDA_VISIBLE_DEVICES=' + GPU in process['environment'], 'owned_same_GPU_containment')
    require(actor['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service'
            and config['device_containment']['minor'] == 5, 'original_device_minor_not_physical_index')
    neighbors = neighbor_observations(helpers)
    return rollout, helpers, config, plan, original, pair, neighbors


def receiving_ready():
    ready = read(HOME / 'RECEIVING_READY.json')
    require(ready['status'] == 'CPU_TESTED_NOT_LIVE'
            and ready['guard_sha256'] == sha(HOME / 'control/GUARD.json')
            and read(HOME / 'PARENT_RETIRED.json')['status'] == 'EXACT_BRAIN_GUIDED_PARENT_EXITED',
            'receiving_checks_and_no_future_old_parent_writes')


def run(wait_seconds=1800, check_ready=None):
    (check_ready or receiving_ready)()
    rollout, helpers, config, plan, original, pair, neighbors = prepare()
    output = RETIREMENT
    output.mkdir()
    write(output / 'WAITING.json', dict(processes=pair, neighbors=neighbors,
        logical_root=str(OLD_ROOT), backing_root=str(OLD / 'run1'),
        status='WAITING_FRESH_COMPLETE_NO_SIGNALS', started_unix=time.time()))
    lock = (output / 'OPERATOR.lock').open('x')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    descriptors, paused = {}, []
    deadline = time.monotonic() + wait_seconds

    def interrupted(signum, frame):
        raise RuntimeError('operator_interrupted')

    for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(signum, interrupted)
    try:
        for name, identity in pair.items():
            require(helpers.identity(identity['pid']) == identity, 'identity_before_pidfd')
            descriptors[name] = os.pidfd_open(identity['pid'])
            require(helpers.identity(identity['pid']) == identity, 'identity_after_pidfd')
        while time.monotonic() < deadline:
            require(all(not select.select([descriptor], [], [], 0)[0] for descriptor in descriptors.values()),
                    'all_exact_owners_still_alive')
            saved = helpers.sleep_boundary(OLD_ROOT)
            if saved is None:
                time.sleep(.15)
                continue
            drained = helpers.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
            child = None if drained else rollout.active_readout_child(plan, saved, pair['actor'],
                config['plan_path'], original.native, helpers)
            if not (drained or child):
                time.sleep(.15)
                continue
            for name in ('supervisor', 'timer', 'actor'):
                paused.append(name)
                helpers.pause_exact(pair[name], descriptors[name])
            if helpers.sleep_boundary(OLD_ROOT) != saved:
                helpers.resume_paused(paused, descriptors)
                continue
            write(output / ('HELD_' + str(time.time_ns()) + '.json'), dict(cycle=saved['cycle'],
                record_sha256=saved['record_sha256'], exact_readout_child=child,
                already_drained=bool(drained), observed_unix=time.time(), retired=False))
            drain_deadline = min(deadline, time.monotonic() + 300)
            while time.monotonic() < drain_deadline and not drained:
                time.sleep(.25)
                drained = helpers.readout_drained(plan, saved, pair['actor']['pid'], config['plan_path'], original.native)
            if not drained:
                helpers.resume_paused(paused, descriptors)
                continue
            require(helpers.sleep_boundary(OLD_ROOT) == saved, 'same_held_COMPLETE_after_readout')
            evidence = rollout.saved_evidence(plan, saved, original, helpers)
            snapshot = output / 'stream_snapshot'
            shutil.copytree(OLD_ROOT.resolve() / 'stream', snapshot)
            helpers.verify_snapshot(snapshot, OLD_ROOT, saved['state_sha256'], original)
            require(helpers.sleep_boundary(OLD_ROOT) == saved, 'snapshot_same_COMPLETE')
            observed_neighbors = neighbor_observations(helpers)
            write(output / 'PRESERVED.json', dict(saved=evidence, snapshot=str(snapshot), readout=drained,
                whole_backing_namespace_preserved_in_place=str(OLD), symlink_unchanged=str(OLD_ROOT),
                optimizer_RNG_adapter_history_inboxes_preserved=True, observed_unix=time.time(),
                neighbors_observed=observed_neighbors, other_lives_signaled=False))
            for name in ('actor', 'timer', 'supervisor'):
                require(helpers.identity(pair[name]['pid']) == pair[name], 'exact_identity_before_TERM')
                signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'exact_owner_exited_without_KILL')
            paused.clear()
            with original.journal.StreamJournal(OLD_ROOT / 'stream', create=False) as journal:
                require(journal.latest_checkpoint()['expected_sha256'] == saved['state_sha256'], 'retired_exact_complete')
            observed_neighbors = neighbor_observations(helpers)
            write(output / 'RETIRED.json', dict(status='EXACT_COMPLETE_PRESERVED_RETIRED',
                cycle=saved['cycle'], saved=evidence, processes=pair, neighbors_observed=observed_neighbors,
                other_lives_signaled=False,
                preserved_sha256=sha(output / 'PRESERVED.json'), retired_unix=time.time()))
            print(json.dumps(read(output / 'RETIRED.json')), flush=True)
            return
        write(output / 'WAIT_EXPIRED.json', dict(status='NO_RETIREMENT', observed_unix=time.time()))
    except BaseException as error:
        write(output / ('ERROR_' + str(time.time_ns()) + '.json'), dict(error_type=type(error).__name__,
            error=str(error), observed_unix=time.time()))
        raise
    finally:
        helpers.resume_paused(paused, descriptors)
        for descriptor in descriptors.values():
            os.close(descriptor)


def launch():
    host()
    retired = read(RETIREMENT / 'RETIRED.json')
    require(retired['status'] == 'EXACT_COMPLETE_PRESERVED_RETIRED', 'selected_life_preserved_and_retired')
    require(not Path('/proc/2001674').exists(), 'old_native_exited')
    guard = HOME / 'control/GUARD.json'
    require(sha(guard) == read(HOME / 'RECEIVING_READY.json')['guard_sha256'], 'unchanged_receiving_guard')
    with (HOME / 'BRIDGE.log').open('x') as log:
        bridge = subprocess.Popen([str(PYTHON), '-B', str(HOME / 'math_c_bridge.py'),
            '--config', str(HOME / 'BRIDGE.json')], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not list((HOME / 'bridge_receipts').glob('READY_*.json')):
        require(bridge.poll() is None, 'CPU_bridge_start_failed')
        time.sleep(.1)
    require(list((HOME / 'bridge_receipts').glob('READY_*.json')), 'CPU_bridge_ready')
    command = [str(PYTHON), '-B', '-m', 'gpu.orch_r188_node4_rehome_containment',
               'contained-supervise', '--config', str(guard)]
    with (HOME / 'control/SUPERVISOR.log').open('x') as log:
        process = subprocess.Popen(command, cwd=SOURCE, env=dict(os.environ,
            CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1'),
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(HOME / 'DISPATCHED.json', dict(supervisor_pid=process.pid, bridge_pid=bridge.pid,
        command=command, started_unix=time.time(), old_cycle=retired['cycle']))


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        values = prepare()
        print(json.dumps(dict(processes=values[5], neighbors_unchanged=len(values[6]))))
    elif sys.argv[1] == 'retire':
        run()
    elif sys.argv[1] == 'launch':
        launch()
    elif sys.argv[1] == 'wait_launch':
        deadline = time.monotonic() + 1800
        while not (RETIREMENT / 'RETIRED.json').exists():
            require(time.monotonic() < deadline, 'bounded_launch_wait_expired')
            require(not list(RETIREMENT.glob('ERROR_*.json')), 'retirement_error_no_launch')
            time.sleep(1)
        launch()
