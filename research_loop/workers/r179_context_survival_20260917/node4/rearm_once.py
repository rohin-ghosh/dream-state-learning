"""One explicitly authorized clean-expiry rearm; never signal or replay a life."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time


BASE = Path('/localhome/local-rohing')
HELPERS_SHA = '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270'
CONSUMED = ('RETIREMENT_STARTED.json', 'RETIRED.json', 'DISPATCHED.json', 'LOADED_RECEIPT.json', 'HANDOFF_COMPLETE.json')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def scoped_lane(lane):
    require(lane.parent.parent == BASE and lane.parent.name.startswith('orch_r179_node4_')
            and lane.name in ('lane0', 'lane1', 'lane3', 'lane4'), 'only_four_existing_NODE4_lives')
    return int(lane.name[-1])


def clean_rearm_allowed(consumed, watcher_alive, clean_expiry, owners_match, sources_match):
    if consumed or watcher_alive:
        return False
    require(clean_expiry, 'no_rearm_after_error_or_unexplained_watcher_exit')
    require(owners_match and sources_match, 'no_rearm_after_owner_or_source_change')
    return True


def helper_module(bundle):
    path = bundle / 'r144_helpers.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == HELPERS_SHA, 'exact_existing_readonly_primitives')
    spec = importlib.util.spec_from_file_location('r179_rearm_helpers', path)
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    return helpers


def active_identity(pid, helpers):
    try:
        state = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[0]
        return None if state in ('Z', 'X') else helpers.identity(pid)
    except (FileNotFoundError, ProcessLookupError):
        return None


def watch(lane, watcher_pid, watcher_start_ticks, seconds):
    physical = scoped_lane(lane)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_rearm_supervision')
    require(type(seconds) is int and 1 <= seconds <= 5400, 'bounded_90_minute_supervision')
    helpers = helper_module(lane.parent)
    request = helpers.read(lane / 'STAGED.json')
    command = [str(helpers.PYTHON), '-B', str(lane.parent / 'node4_rollout.py'), 'handoff',
        '--bundle', str(lane.parent), '--physical', str(physical), '--wait-seconds', '5400']
    watcher = active_identity(watcher_pid, helpers)
    require(watcher is not None and watcher['argv'] == command and watcher['start_ticks'] == watcher_start_ticks
            and watcher['uid'] == request['processes']['actor']['uid'], 'exact_current_authorized_waiter')
    require(request['physical'] == physical and request['source_root'] == str(lane / 'source'), 'same_prepared_lane')
    initial_expiries = {path.name for path in lane.glob('WAIT_EXPIRED_*.json')}
    deadline = min(time.monotonic() + seconds, time.monotonic() + request['old_plan']['hard_end_unix'] - time.time() - 180)
    print(json.dumps(dict(status='WAITING_FOR_ONE_CLEAN_EXPIRY_ONLY', physical=physical, watcher=watcher,
        max_supervision_seconds=seconds, max_new_boundary_wait_seconds=5400, signals_sent=0,
        journal_writes=0, model_calls=0, observed_unix=time.time()), sort_keys=True), flush=True)
    while time.monotonic() < deadline:
        consumed = any((lane / name).exists() for name in CONSUMED)
        if consumed:
            return dict(status='NO_REARM_HANDOFF_ALREADY_CONSUMED', physical=physical)
        if active_identity(watcher_pid, helpers) == watcher:
            time.sleep(min(10, max(0, deadline - time.monotonic())))
            continue
        expiries = sorted(path for path in lane.glob('WAIT_EXPIRED_*.json') if path.name not in initial_expiries)
        errors = sorted(lane.glob('ERROR_*.json'))
        clean_expiry = bool(expiries) and helpers.read(expiries[-1])['status'] == 'NO_RETIREMENT'
        clean_expiry = clean_expiry and (not errors or expiries[-1].stat().st_mtime_ns > errors[-1].stat().st_mtime_ns)
        current_owners = {name: active_identity(process['pid'], helpers) for name, process in request['processes'].items()}
        source_proof = helpers.read(lane / 'SOURCE_PROOF.json')
        sources_match = (helpers.sha(lane / 'SOURCE_PROOF.json') == request['source_proof_sha256']
            and helpers.inventory_files(source_proof['old_source']) == source_proof['old_inventory']
            and helpers.inventory_files(source_proof['new_source']) == source_proof['new_inventory']
            and helpers.sha(lane.parent / 'node4_rollout.py') == request['operator_sha256'])
        require(clean_rearm_allowed(consumed, False, clean_expiry, current_owners == request['processes'], sources_match),
                'clean_expiry_rearm_required')
        require(not any((lane / name).exists() for name in CONSUMED), 'never_rearm_consumed_native_or_readout')
        stamp = str(time.time_ns())
        prefix = lane.parent / f'HANDOFF_{physical}_CLEAN_REARM_{stamp}'
        intent = dict(physical=physical, predecessor_watcher=watcher, original_owners=current_owners,
            clean_expiry_path=str(expiries[-1]), clean_expiry_sha256=helpers.sha(expiries[-1]),
            operator_sha256=request['operator_sha256'], source_proof_sha256=request['source_proof_sha256'],
            command=command, maximum_new_boundary_wait_seconds=5400,
            full_original_handoff_CPU_device_source_owner_preflight_gate_reexecuted_by_child=True,
            no_source_changes=True, no_native_or_readout_replay=True, observed_unix=time.time())
        helpers.write(prefix.with_suffix('.intent.json'), intent)
        with prefix.with_suffix('.log').open('x') as output:
            process = subprocess.Popen(command, cwd=BASE, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        with prefix.with_suffix('.pid').open('x') as output:
            output.write(str(process.pid) + '\n')
        receipt = dict(status='ONE_CLEAN_EXPIRY_REARM_DISPATCHED_NOT_A_NATIVE_LOAD', physical=physical,
            new_operator_pid=process.pid, pid_marker=str(prefix.with_suffix('.pid')),
            intent_sha256=helpers.sha(prefix.with_suffix('.intent.json')), signals_sent=0,
            journal_writes=0, model_calls=0, observed_unix=time.time())
        helpers.write(prefix.with_suffix('.receipt.json'), receipt)
        return receipt
    return dict(status='NO_REARM_SUPERVISION_BOUND_REACHED', physical=physical, observed_unix=time.time())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane', type=Path, required=True)
    parser.add_argument('--watcher-pid', type=int, required=True)
    parser.add_argument('--watcher-start-ticks', required=True)
    parser.add_argument('--seconds', type=int, default=5400)
    args = parser.parse_args()
    print(json.dumps(watch(args.lane.resolve(), args.watcher_pid, args.watcher_start_ticks, args.seconds), sort_keys=True), flush=True)
