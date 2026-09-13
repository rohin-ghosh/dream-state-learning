"""Main-operated, one-pass collection from an explicitly pinned Level1 roster."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


RUNTIME = Path('/tmp/astra_level1_skill_run_20260913.py')
RUNTIME_SHA256 = '6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e'
NODES = ('node1', 'node2', 'a100')
COLLECT_SECONDS = 180


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def read(path, expected=None):
    raw = Path(path).read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    require(expected is None or checksum == expected, 'file pin differs: ' + str(path))
    value = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda value: require(False, 'nonfinite JSON'))
    return value, checksum


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')


def occupied(path):
    return os.path.lexists(path)


def controller_present(pid):
    require(type(pid) is int and pid > 1, 'invalid original controller PID')
    try:
        (Path('/proc') / str(pid)).stat()
        return True
    except FileNotFoundError:
        return False


def check_node(roster, node):
    prechecks, _ = read(roster['prechecks']['path'], roster['prechecks']['sha256'])
    expected = prechecks[node]
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == expected['host_boot_id'] and
            os.getuid() == expected['uid'], 'selected node boot/user identity differs')


def load_roster(roster_path, roster_sha256, node, batch_dir):
    require(node in NODES, 'node must be node1/node2/a100')
    require(type(roster_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', roster_sha256) is not None,
            'explicit lowercase full roster SHA256 required')
    roster_path = Path(roster_path).resolve(strict=True)
    batch = Path(batch_dir)
    require(batch.is_absolute() and batch.parent == roster_path.parent and batch.resolve() == batch and
            not batch.is_symlink() and batch.is_dir(), 'use an exact existing batch directory immediately under the explicit roster directory')
    roster, _ = read(roster_path, roster_sha256)
    require(digest(RUNTIME) == RUNTIME_SHA256, 'frozen runtime pin differs')
    started, _ = read(batch / 'started.json')
    require(started['roster_sha256'] == roster_sha256 and started['roster'] == str(roster_path), 'batch/roster pin or path differs')
    require(started['node'] == node and started['batch_name'] == batch.name, 'batch/node or name binding differs')
    require(started['runtime'] == str(RUNTIME) and started['runtime_sha256'] == RUNTIME_SHA256, 'batch/runtime binding differs')
    entries = roster['entries']
    require(type(entries) is list and entries and len({entry['name'] for entry in entries}) == len(entries) and
            len({entry['root'] for entry in entries}) == len(entries), 'unique nonempty roster cells required')
    for entry in entries:
        require(entry['node'] in NODES and type(entry['name']) is str and
                re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', entry['name']) is not None,
                'invalid roster node or cell path component')
    selected = [entry for entry in entries if entry['node'] == node]
    require(selected, 'roster has no cells for selected node')
    require(all(type(entry['gpu_index']) is int and entry['gpu_index'] >= 0 and
                type(entry['gpu_uuid']) is str and entry['gpu_uuid'] for entry in selected) and
            len({entry['gpu_index'] for entry in selected}) == len(selected) and
            len({entry['gpu_uuid'] for entry in selected}) == len(selected), 'selected GPU allocations must be unique and typed')
    check_node(roster, node)
    return selected, batch


def collect_cell(entry, batch):
    root = Path(entry['root'])
    require(root.is_absolute() and not root.is_symlink(), 'absolute original root required')
    out = root.with_name(root.name + '_collected')
    claim = root.with_name(root.name + '.collection_claim.json')
    attempt = root.with_name(root.name + '_collection_driver')
    result = dict(node=entry['node'], name=entry['name'], root=str(root), out=str(out))
    for path in (claim, out, attempt):
        if occupied(path):
            return dict(result, status='claimed', reason='existing claim/output/driver attempt; never retry', existing=str(path))
    if occupied(root / 'controller_failure.json'):
        return dict(result, status='failed', reason='controller_failure.json exists; incomplete work is never scored')
    launch_path = batch / entry['name'] / 'launched.json'
    if not launch_path.exists():
        if occupied(batch / entry['name'] / 'failure.json'):
            return dict(result, status='failed', reason='batch launch failure; no launched receipt')
        return dict(result, status='pending', reason='no launched receipt')
    launch, _ = read(launch_path)
    require(all(launch[key] == entry[key] for key in ('node', 'name', 'root', 'gpu_index', 'gpu_uuid')),
            'launch/roster identity differs')
    require(launch['pid'] == launch['identity']['pid'] == launch['pgid'], 'controller launch identity differs')
    result['pid'] = launch['pid']
    if controller_present(launch['pid']):
        return dict(result, status='pending', reason='original controller PID still present (including zombie/reused PID)')
    complete_path = root / 'capture_complete.json'
    if not complete_path.exists():
        return dict(result, status='pending', reason='controller absent but no capture_complete.json; not success')
    complete, completion_pin = read(complete_path)
    plan_pin = launch['plan_sha256']
    require(complete['plan_sha256'] == plan_pin and type(complete['calls']) is int and
            complete['calls'] == 120 and complete['scored'] is False, 'capture completion/launch plan binding differs')
    plan, _ = read(root / 'plan.json', plan_pin)
    require(all(plan[key] == entry[key] for key in ('root', 'gpu_index', 'gpu_uuid')) and
            plan['spec_sha256'] == entry['spec']['sha256'] and plan['self_sha256'] == RUNTIME_SHA256,
            'prepared plan/roster/runtime binding differs')
    controller, _ = read(root / 'controller_started.json')
    require(controller['plan_sha256'] == plan_pin, 'controller claim/plan differs')
    interpreter = Path(plan['python'])
    require(interpreter.is_absolute() and digest(interpreter) == plan['python_sha256'], 'pinned interpreter differs')
    require(launch['command'] == [str(interpreter), '-B', str(RUNTIME), 'controller', '--root', str(root),
                                  '--plan-sha256', plan_pin, '--allow-gpu'], 'original controller command differs')
    require(digest(RUNTIME) == RUNTIME_SHA256, 'frozen runtime pin differs')
    command = [str(interpreter), '-B', str(RUNTIME), 'collect', '--root', str(root), '--plan-sha256', plan_pin,
               '--completion-sha256', completion_pin, '--out', str(out)]
    try:
        attempt.mkdir()
    except FileExistsError:
        return dict(result, status='claimed', reason='another helper owns the collection attempt')
    result.update(plan_sha256=plan_pin, completion_sha256=completion_pin, logs=str(attempt))
    try:
        write(attempt / 'attempt.json', dict(command=command, timeout_seconds=COLLECT_SECONDS, time=time.time(), retry=False))
        require(not occupied(claim) and not occupied(out), 'another collector claimed this root')
        require(not occupied(root / 'controller_failure.json') and not controller_present(launch['pid']),
                'readiness changed before collection')
        with (attempt / 'stdout.log').open('xb') as stdout, (attempt / 'stderr.log').open('xb') as stderr:
            process = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                                     start_new_session=True, timeout=COLLECT_SECONDS, check=False)
        require(process.returncode == 0, f'native collect exited nonzero: {process.returncode}; inspect external logs')
        receipt, _ = read(out / 'collection.json')
        require(receipt['completion_sha256'] == completion_pin and digest(out / 'scores.json') == receipt['scores_sha256'],
                'native collection receipt/output pin differs')
        result.update(status='collected', scores_sha256=receipt['scores_sha256'])
    except Exception as error:
        result.update(status='error', error_type=type(error).__name__, error=str(error), retry=False)
    write(attempt / 'result.json', result)
    return result


def run(roster_path, roster_sha256, node, batch_dir):
    entries, batch = load_roster(roster_path, roster_sha256, node, batch_dir)
    results = []
    for entry in entries:
        try:
            result = collect_cell(entry, batch)
        except Exception as error:
            result = dict(node=node, name=entry['name'], root=entry['root'], status='error',
                          error_type=type(error).__name__, error=str(error))
        results.append(result)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    return 1 if any(result['status'] in ('failed', 'error') for result in results) else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roster', type=Path, required=True)
    parser.add_argument('--roster-sha256', required=True)
    parser.add_argument('--node', choices=NODES, required=True)
    parser.add_argument('--batch-dir', required=True)
    args = parser.parse_args(argv)
    try:
        return run(args.roster, args.roster_sha256, args.node, args.batch_dir)
    except Exception as error:
        print(json.dumps(dict(status='error', error_type=type(error).__name__, error=str(error))), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
