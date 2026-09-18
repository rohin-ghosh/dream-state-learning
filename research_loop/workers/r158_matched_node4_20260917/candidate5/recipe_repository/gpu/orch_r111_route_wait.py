"""Prospective WAIT600 route successor; immutable old plans and requests stay intact."""

import argparse
from copy import deepcopy
import fcntl
import inspect
import os
from pathlib import Path
import subprocess
import sys
import time
from types import FunctionType

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_pair as original


require, read, sha = boundary.require, boundary.read, boundary.sha
MODULE = 'gpu.orch_r111_route_wait'


def prepare(root, era_path, request_path, tests_receipt):
    root, request_path, tests_receipt = map(Path, (root, request_path, tests_receipt))
    plan = original.verify(root)
    request = read(request_path)
    require(request['root'] == str(root.resolve()) and request['purpose'] == 'WAIT600_TRANSPORT',
            'exact_transport_handoff_request')
    tests = read(tests_receipt)
    sources = {str(Path(__file__).resolve()): sha(__file__),
               str(Path(boundary.__file__).resolve()): sha(boundary.__file__)}
    require(tests.get('passed') is True and tests.get('source_files') == sources, 'CPU_source_bound')
    require(plan['physical'] == 0 and plan['provider'] == 'claude-fable-5-1', 'F1_only_wait_era')
    era = dict(schema='R118_ROUTE_WAIT600_V1', root=str(root.resolve()),
        original_plan=boundary.reference(root / 'PLAN.json'), original_wait_seconds=plan['parent_wait_seconds'],
        parent_wait_seconds=600, provider_reserve_seconds=30, parent_effort='max', head_effort='max',
        bounds=plan['bounds'], handoff_request=boundary.reference(request_path), source_files=sources,
        tests_receipt=boundary.reference(tests_receipt), declared_unix=time.time(),
        scientific_label='F1_WAIT600_TIMING_ERA_NOT_PARENT_MODEL_ONLY_MATCH',
        refusal_policy='PRESERVE_MISSING_NO_REPLAY_NO_REPHRASE_NO_EFFORT_BYPASS',
        interpretation='TRANSPORT_BUDGET_CHANGE_NOT_A_REFUSAL_REPAIR', no_quota_reset=True)
    boundary.write_new(era_path, era)
    return era


def verify_era(root, era_path, released=False):
    root, era_path = Path(root).resolve(strict=True), Path(era_path).resolve(strict=True)
    era, plan = read(era_path), original.verify(root)
    require(era['schema'] == 'R118_ROUTE_WAIT600_V1' and era['root'] == str(root), 'exact_era_root')
    require(era['original_plan'] == boundary.reference(root / 'PLAN.json'), 'original_plan_not_mutated')
    require(era['bounds'] == plan['bounds'] and era['parent_wait_seconds'] == 600
            and era['provider_reserve_seconds'] == 30, 'same_caps_new_wait_only')
    require(era['parent_effort'] == era['head_effort'] == 'max', 'no_effort_reduction')
    require(plan['physical'] == 0 and plan['provider'] == 'claude-fable-5-1', 'F1_only')
    for path, expected in era['source_files'].items():
        require(sha(path) == expected, 'immutable_successor_source')
    require(era['source_files'].get(str(Path(__file__).resolve())) == sha(__file__), 'executing_era_source')
    tests = read(era['tests_receipt']['path'])
    require(sha(era['tests_receipt']['path']) == era['tests_receipt']['sha256']
            and tests.get('passed') is True and tests['source_files'] == era['source_files'], 'CPU_era_binding')
    request_path = Path(era['handoff_request']['path'])
    require(sha(request_path) == era['handoff_request']['sha256'], 'handoff_request_binding')
    if released:
        receipt = read(request_path.parent / 'RELEASED.json')
        require(receipt['status'] == 'RELEASED' and receipt['original_plan'] == era['original_plan'], 'released_predecessor')
        saved_path = Path(receipt['boundary']['path'])
        require(sha(saved_path) == receipt['boundary']['sha256'], 'boundary_receipt_binding')
        saved = read(saved_path)
        require(saved['request'] == era['handoff_request'], 'exact_release_for_era')
        for field in ('checkpoint', 'optimizer', 'carry', 'ledger'):
            require(sha(saved[field]['path']) == saved[field]['sha256'], 'preserved_at_launch:' + field)
    return era


def resumed_cycle(root, attempts, era):
    request = Path(era['handoff_request']['path'])
    saved = read(request.parent / 'BOUNDARY.json')
    empty = saved['empty_successor_start']
    latest = max([read(path)['cycle'] for path in attempts], default=0)
    if empty is not None and str(root / f'cycle_{latest:04d}' / 'START.json') == empty['path']:
        folder = Path(empty['path']).parent
        if {path.name for path in folder.iterdir()} == {'START.json'}:
            require(sha(empty['path']) == empty['sha256'], 'preserved_empty_START_bytes')
            return latest
    return latest + 1


def prepare_cycle(output, era):
    if output.exists():
        saved = read(Path(era['handoff_request']['path']).parent / 'BOUNDARY.json')
        empty = saved['empty_successor_start']
        require(empty is not None and str(output / 'START.json') == empty['path']
                and {path.name for path in output.iterdir()} == {'START.json'}
                and sha(output / 'START.json') == empty['sha256'], 'only_verified_empty_cycle_resume')
    else:
        output.mkdir(exist_ok=False)


def cycle_write(path, value):
    if path.name == 'START.json' and path.exists():
        boundary.write_new(path.parent / ('RESUMED_START_' + str(time.time_ns()) + '.json'), value)
    else:
        original.write(path, value)


def cooperative_boundary(root, cycle, era_path):
    marker = root / 'STOP_AFTER_CYCLE.json'
    if not marker.exists():
        return False
    request = read(marker)
    require(request.get('era_sha256') == sha(era_path) and request.get('stop') is True,
            'exact_successor_stop_marker')
    if request.get('purpose') == 'SHARED_ADOPTION':
        require(request.get('all_eight_ready') is True and request.get('common_handoff_coordinated') is True,
                'shared_handoff_coordinated')
    else:
        require(request.get('purpose') == 'OWNED_HANDOFF', 'known_stop_purpose')
    boundary.write_new(root / 'WAIT600_CYCLE_STOPPED.json', dict(cycle=cycle, stopped_unix=time.time(),
        era=boundary.reference(era_path), marker=boundary.reference(marker),
        complete=boundary.reference(root / f'cycle_{cycle:04d}' / 'COMPLETE.json'),
        ledger=boundary.reference(root / 'RESERVATIONS.jsonl'), no_quota_reset=True))
    return True


def runtime(root, era_path):
    era = verify_era(root, era_path)
    era_reference = boundary.reference(era_path)
    namespace = dict(original.__dict__)

    def reserve(root, kind, detail):
        return original.reserve(root, kind, dict(detail, transport_era=era_reference))

    parent_namespace = dict(original.__dict__, reserve=reserve)
    parent_function = FunctionType(original.parent_call.__code__, parent_namespace)

    def parent_call(root, plan, *arguments):
        effective = deepcopy(plan)
        effective['parent_wait_seconds'] = era['parent_wait_seconds']
        return parent_function(root, effective, *arguments)

    namespace.update(parent_call=parent_call, reserve=reserve, write=cycle_write,
        resumed_cycle=lambda root, attempts: resumed_cycle(root, attempts, era),
        prepare_cycle=lambda output: prepare_cycle(output, era), transport_era=era_reference,
        cooperative_boundary=lambda root, cycle: cooperative_boundary(root, cycle, era_path))
    source = inspect.getsource(original.run)
    replacements = [
        ('next_cycle = max([read(path)[\'cycle\'] for path in attempts], default=0)+1',
         'next_cycle = resumed_cycle(root, attempts)'),
        ('output.mkdir(exist_ok=False)', 'prepare_cycle(output)'),
        ("call = dict(task_id=task_entry['id'], phase=phase, started_unix=time.time(), messages=actual)",
         "call = dict(task_id=task_entry['id'], phase=phase, started_unix=time.time(), messages=actual, transport_era=transport_era)"),
        ("            parent_history = [pending['intervention']['parent_text']] if pending and pending['intervention']['status']=='COMPLETE' else []",
         "            if cooperative_boundary(root, cycle):\n                return\n"
         "            parent_history = [pending['intervention']['parent_text']] if pending and pending['intervention']['status']=='COMPLETE' else []")]
    for before, after in replacements:
        require(source.count(before) == 1, 'exact_source_bound_successor_transform')
        source = source.replace(before, after, 1)
    exec(compile(source, __file__ + ':prospective_run', 'exec'), namespace)
    return namespace['run']


def launch(root, era_path):
    verify_era(root, era_path, released=True)
    require(not (root / 'WAIT600_DISPATCH.json').exists(), 'single_era_dispatch')
    namespace = dict(original.__dict__, era_path=str(era_path.resolve()))
    source = inspect.getsource(original.launch)
    before = "'gpu.orch_r111_route_pair',\n            'supervise', '--root', str(root)]"
    after = "'gpu.orch_r111_route_wait',\n            'supervise', '--root', str(root), '--era', era_path]"
    require(source.count(before) == 1, 'exact_launch_command_transform')
    source = source.replace(before, after, 1)
    exec(compile(source, __file__ + ':strict_recovery_launch', 'exec'), namespace)
    result = namespace['launch'](root, recovery=True)
    boundary.write_new(root / 'WAIT600_DISPATCH.json', dict(result, era=boundary.reference(era_path)))
    return result


def supervise(root, era_path):
    era = verify_era(root, era_path)
    original.verify(root, gpu=True)
    with (root / 'SUPERVISOR_LOCK').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while time.time() < era['bounds']['hard_end_unix']:
            if (root / 'WAIT600_CYCLE_STOPPED.json').exists() or (root / 'TERMINAL.json').exists():
                return
            attempt = max((int(path.stem.split('_')[-1]) for path in root.glob('actor_attempt_*.json')), default=0) + 1
            with (root / f'actor_attempt_{attempt:04d}.log').open('x') as stream:
                process = subprocess.Popen([sys.executable, '-B', '-m', MODULE, 'run',
                    '--root', str(root), '--era', str(era_path)], stdout=stream, stderr=subprocess.STDOUT)
                boundary.write_new(root / f'actor_attempt_{attempt:04d}.json', dict(pid=process.pid,
                    launched_unix=time.time(), same_owned_life=True, no_quota_reset=True, era=boundary.reference(era_path)))
                try:
                    process.wait(timeout=max(.1, era['bounds']['hard_end_unix'] - time.time()))
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=30)
                    return
            if (root / 'WAIT600_CYCLE_STOPPED.json').exists() or (root / 'TERMINAL.json').exists():
                return
            command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH=' + str(Path(original.__file__).resolve().parents[1]), 'python3', '-B',
                '-m', 'gpu.orch_r111_route_pair', 'scan', '--root', str(root)]
            report = original.json.loads(subprocess.check_output(command, text=True, timeout=100))
            require(report['clear'], 'fresh_recovery_admission_no_waiver')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'launch', 'supervise', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--era', type=Path, required=True)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--tests-receipt', type=Path)
    arguments = parser.parse_args()
    if arguments.phase == 'prepare':
        result = prepare(arguments.root, arguments.era, arguments.request, arguments.tests_receipt)
        print(original.json.dumps(result, sort_keys=True))
    elif arguments.phase == 'launch':
        print(original.json.dumps(launch(arguments.root, arguments.era), sort_keys=True))
    elif arguments.phase == 'supervise':
        supervise(arguments.root, arguments.era)
    else:
        runtime(arguments.root, arguments.era)(arguments.root)


if __name__ == '__main__':
    main()
