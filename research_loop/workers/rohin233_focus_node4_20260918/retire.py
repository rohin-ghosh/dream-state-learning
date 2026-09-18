"""Exact named R233 retirement using the existing R144 complete-state verifier."""

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import signal
import socket
import sys
import time

from inventory import BASE, HOST_SHA, digest, identity, metadata, read

WALL = 1789754400
HELPERS = Path('/localhome/local-rohing/orch_r179_node4_r181journal_20260917t2220z/r144_helpers.py')
HELPERS_SHA = '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270'
OUTPUT = Path('/localhome/local-rohing/orch_r233_focus_node4_20260918')
IDENTITY_FIELDS = ('pid', 'start_ticks', 'uid', 'argv', 'cwd', 'cgroup', 'boot_id', 'group')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def scope(binding):
    physical = binding['physical']
    require(physical in (0, 1, 2, 5, 6), 'R233_named_roots_only_keep_P3_P7_kernel4')
    expected = BASE / ('MATH_C' if physical == 6 else f'SCALE_physical{physical}') / 'life'
    require(binding['root'] == str(expected) and binding['backing_root'] == str(expected.resolve()), 'exact_root_backing_not_alias')
    require(physical != 6 or binding.get('classroom_disposition') == 'NO_PROVEN_CROSS_NODE_THINK_ROUTE_RETIRE', 'explicit_MATH_C_disposition')
    return expected


def same_process(expected):
    try:
        actual = identity(expected['pid'])
    except (FileNotFoundError, ProcessLookupError):
        return False
    return all(actual[key] == expected[key] for key in IDENTITY_FIELDS)


def records(root):
    return sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))


def closed(root, journal_id, allow_terminal=False):
    paths = records(root)
    if not paths:
        return None
    selected = None
    for path in reversed(paths[-6:]):
        header = metadata(path)
        if header['kind'] == 'SLEEP_COMPLETE':
            selected = path
            break
        if header['kind'] not in (('R184_LEARN_COMPLETE', 'TERMINAL') if allow_terminal else ('R184_LEARN_COMPLETE',)):
            return None
    if selected is None:
        return None
    complete = read(selected)
    require(complete['journal_id'] == journal_id and complete['sha256'] == digest({key: value for key, value in complete.items() if key != 'sha256'}), 'canonical_same_life_complete')
    require(complete['document']['status'] == 'COMPLETE', 'actual_complete')
    previous = complete
    suffix = []
    for path in paths:
        if int(path.stem) <= complete['index']:
            continue
        row = read(path)
        require(row['sha256'] == digest({key: value for key, value in row.items() if key != 'sha256'})
            and row['journal_id'] == journal_id and row['index'] == previous['index'] + 1
            and row['previous_sha256'] == previous['sha256'], 'exact_post_complete_chain')
        if row['kind'] == 'R184_LEARN_COMPLETE':
            require(row['document']['cycle'] == complete['document']['cycle']
                and row['document']['checkpoint'] == complete['document']['checkpoint'], 'same_checkpoint_receipt')
        else:
            require(allow_terminal and row['kind'] == 'TERMINAL', 'no_post_complete_child_work')
        suffix.append({key: row[key] for key in ('index', 'kind', 'sha256')})
        previous = row
    return dict(complete=complete, head=metadata(paths[-1]), paths=paths, suffix=suffix)


def readout(binding, boundary):
    native = binding['native']
    process = Path('/proc', str(native['pid']))
    try:
        children = (process / 'task' / str(native['pid']) / 'children').read_text().split()
        wait = (process / 'wchan').read_text().strip()
        if len(children) != 1 or not ('wait' in wait or wait == 'hrtimer_nanosleep'):
            return None
        child = identity(int(children[0]))
        child.pop('state', None)
    except (FileNotFoundError, ProcessLookupError):
        return None
    checkpoint = str(Path(boundary['complete']['document']['checkpoint']['adapter_path']).parent / 'COMMIT.json')
    prefix = [native['argv'][0], '-B', '-m', 'gpu.orch_r125_continual_readout',
        '--plan', binding['plan_path'], '--checkpoint', checkpoint, '--output']
    if child['argv'][:len(prefix)] != prefix or child['cwd'] != native['cwd'] or child['uid'] != native['uid']:
        return None
    if child['cgroup'] != native['cgroup'] or child['boot_id'] != native['boot_id']:
        return None
    return child


def verifier(binding):
    require(sha(HELPERS) == HELPERS_SHA, 'unchanged_existing_R144_verifier')
    specification = importlib.util.spec_from_file_location('r233_existing_helpers', HELPERS)
    helpers = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helpers)
    config, plan, original = helpers.originals(Path(binding['guard']))
    require(sha(binding['guard']) == binding['guard_sha256'] and plan['root'] == binding['root']
        and plan['source_root'] == binding['source'] and plan['physical'] == binding['physical']
        and plan['hard_end_unix'] == WALL and config['plan_path'] == binding['plan_path'], 'original_full_guard_plan_identity')
    return helpers, plan, original


def saved_evidence(root, boundary, helpers, plan, original):
    before = helpers.records
    prefix = [path for path in boundary['paths'] if int(path.stem) <= boundary['complete']['index']]
    helpers.records = lambda unused: prefix
    try:
        saved = helpers.sleep_boundary(root)
    finally:
        helpers.records = before
    require(saved is not None, 'strict_saved_boundary')
    return saved, helpers.saved_evidence(plan, saved, original)


def retire(binding, wait_seconds):
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA and os.getuid() == 2524, 'owned_node4_only')
    require(time.time() + 180 < WALL and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_existing_wall')
    root = scope(binding)
    output = OUTPUT / f'physical{binding["physical"]}'
    output.mkdir()
    lock = (output / 'OPERATOR.lock').open('x')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    helpers, plan, original = verifier(binding)
    native = binding.get('native')
    require(native is None or same_process(native), 'same_native_incarnation_before_pidfd')
    descriptor = os.pidfd_open(native['pid']) if native else None
    baseline = binding['baseline_cycle']
    write(output / 'WAITING.json', dict(binding=binding, started_unix=time.time(), deadline_unix=min(WALL - 180, time.time() + wait_seconds),
        SIGSTOP_used=False, PAUSED_marker=False, native_signals=[]))
    deadline = min(time.time() + wait_seconds, WALL - 180)
    try:
        while time.time() < deadline:
            require(native is None or same_process(native), 'selected_native_remains_alive_until_boundary')
            boundary = closed(root, binding['journal_id'], allow_terminal=native is None)
            if boundary is None or (native and boundary['complete']['document']['cycle'] <= baseline):
                time.sleep(.2)
                continue
            child = readout(binding, boundary) if native else None
            if native and child is None:
                time.sleep(.2)
                continue
            saved, evidence = saved_evidence(root, boundary, helpers, plan, original)
            current = closed(root, binding['journal_id'], allow_terminal=native is None)
            if current is None or current['head'] != boundary['head'] or (native and (not same_process(native) or readout(binding, current) != child)):
                time.sleep(.2)
                continue
            proof = dict(saved=evidence, complete_index=boundary['complete']['index'], head=boundary['head'], suffix=boundary['suffix'],
                native=native, blocked_readout=child, root=str(root), backing_root=str(root.resolve()), verified_unix=time.time(),
                whole_namespace_preserved_in_place=True, SIGSTOP_used=False, PAUSED_marker=False, checkpoint_rollback=False)
            write(output / f'BOUNDARY_{boundary["complete"]["index"]}.json', proof)
            signaled = None
            if native:
                require(same_process(native) and readout(binding, boundary) == child
                    and metadata(records(root)[-1]) == boundary['head'], 'same_blocked_complete_immediately_before_TERM')
                signaled = time.time()
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                require(bool(select.select([descriptor], [], [], 20)[0]), 'exact_native_exit_observed_no_KILL')
                require(metadata(records(root)[-1]) == boundary['head'], 'no_learning_or_history_advance_after_saved_boundary')
                if same_process(child):
                    child_descriptor = os.pidfd_open(child['pid'])
                    try:
                        require(same_process(child), 'same_owned_readout_before_TERM')
                        signal.pidfd_send_signal(child_descriptor, signal.SIGTERM)
                        require(bool(select.select([child_descriptor], [], [], 20)[0]), 'owned_readout_exit_observed')
                    finally:
                        os.close(child_descriptor)
            else:
                historical = binding['historical_native']
                require(not same_process(historical), 'historical_native_already_exited')
            snapshot = output / 'stream_snapshot'
            shutil.copytree(root / 'stream', snapshot)
            helpers.verify_snapshot(snapshot, root, saved['state_sha256'], original)
            require(metadata(records(root)[-1]) == boundary['head'], 'retired_journal_stable_through_snapshot')
            file_hashes = {str(path.relative_to(snapshot)): sha(path) for path in snapshot.rglob('*') if path.is_file()}
            write(output / 'STREAM_MANIFEST.json', file_hashes)
            outcome = dict(status='EXACT_FRESH_COMPLETE_RETIRED' if native else 'ALREADY_ENDED_PRESERVED_NOT_NEWLY_SIGNALED',
                physical=binding['physical'], root=str(root), backing_root=str(root.resolve()), journal_id=binding['journal_id'],
                native=native or binding['historical_native'], previous_baseline_cycle=baseline, saved=evidence,
                head=boundary['head'], suffix=boundary['suffix'], signal='pidfd_SIGTERM' if native else None,
                signaled_unix=signaled, retirement_verified_unix=time.time(), stream_snapshot=str(snapshot),
                stream_manifest_sha256=sha(output / 'STREAM_MANIFEST.json'), snapshot_files=len(file_hashes),
                coherent_adapter_optimizer_RNG_history_inboxes=True, namespace_deleted=False,
                SIGSTOP_used=False, PAUSED_marker=False, other_lives_signaled=False,
                readout_interrupted_without_success_claim=child is not None)
            write(output / 'RETIRED.json', outcome)
            print(json.dumps(outcome), flush=True)
            return
        write(output / 'WAIT_EXPIRED.json', dict(status='NO_NATIVE_SIGNAL', expired_unix=time.time()))
        raise TimeoutError('no_fresh_closed_readout_boundary_observed')
    finally:
        if descriptor is not None:
            os.close(descriptor)
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--binding', required=True)
    parser.add_argument('--wait-seconds', type=int, default=900)
    options = parser.parse_args()
    try:
        retire(read(options.binding), options.wait_seconds)
    except Exception as error:
        print(json.dumps(dict(status='ERROR_NOT_RETIREMENT_PROOF', error_type=type(error).__name__, error=str(error))), flush=True)
        raise
