"""Live CPU custody of completed FINAL evidence; no evaluator or model dispatch."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROLE = 'COMPLETED_FINAL_CUSTODIAN_NO_EVALUATION'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def checked(pointer):
    require(reference(pointer['path']) == pointer, 'bound_custody_evidence')
    return json.loads(Path(pointer['path']).read_bytes())


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    fields = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, start_ticks=int(fields[19]),
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def alive(expected):
    try:
        fields = (Path('/proc') / str(expected['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()
        return identity(expected['pid']) == expected and fields[0] != 'Z'
    except (FileNotFoundError, ProcessLookupError):
        return False


def validate_completed(custody):
    terminal = checked(custody['terminal'])
    require(terminal['success'] is True and terminal['returncode'] == 0
            and terminal['no_replay'] is True and terminal['optimizer_steps'] == 0
            and terminal['parent_calls'] == 0 and 0 < terminal['native_calls'] <= 48,
            'actual_completed_original_FINAL_only')
    require(terminal['complete'] == custody['complete'] and terminal['selected'] == custody['selection'],
            'original_completion_and_selection_join')
    for key in ('complete', 'selection'):
        require(reference(custody[key]['path']) == custody[key], 'preserved_' + key)
    if 'reservations' in custody:
        require(reference(custody['reservations']['path']) == custody['reservations'], 'FINAL_ledger_unchanged')
    return terminal


def serve(control_path):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_custodian_empty_CVD')
    control = json.loads(Path(control_path).read_bytes())
    require(control['source'] == reference(__file__), 'immutable_custodian_source')
    plan = checked(control['plan'])
    root = Path(control['root'])
    require(control['plan']['path'] == str(root / 'R118_PARALLEL_PLAN.json')
            and plan['shared_learner']['branch'] == control['branch']
            and plan['physical'] == {'F1': 0, 'A1': 4}[control['branch']], 'exact_route_custody_plan')
    require(plan['bounds']['hard_end_unix'] == control['hard_end_unix'], 'unchanged_lease_wall')
    require(plan['lease_continuation']['completed_final'] == control['completed_final'], 'actual_completed_custody')
    require(alive(control['guardian']), 'live_actual_guardian')
    validate_completed(control['completed_final'])
    started = Path(control['directory']) / 'STARTED.json'
    write(started, dict(role=ROLE, identity=identity(os.getpid()), guardian=control['guardian'],
        root=str(root), branch=control['branch'], plan=control['plan'], source=control['source'],
        control=reference(control_path), completed_final=control['completed_final'],
        never_dispatch=True, evaluation_calls=0, optimizer_steps=0, parent_calls=0,
        started_unix=time.time(), hard_end_unix=control['hard_end_unix']))
    while time.time() < control['hard_end_unix'] and alive(control['guardian']):
        if (root / 'R118_PARALLEL_GUARD_TERMINAL.json').exists():
            break
        checked(control['plan'])
        validate_completed(control['completed_final'])
        time.sleep(2)
    write(Path(control['directory']) / 'EXITED.json', dict(role=ROLE, identity=identity(os.getpid()),
        evaluation_calls=0, parent_calls=0, optimizer_steps=0, finished_unix=time.time()))


def start(root, plan, guardian, interpreter):
    root = Path(root)
    expected_guardian = {key: guardian[key] for key in ('pid', 'start_ticks', 'boot_id')}
    expected_guardian['start_ticks'] = int(expected_guardian['start_ticks'])
    require(identity(guardian['pid']) == expected_guardian, 'exact_guardian_identity')
    directory = root / 'R120_COMPLETED_FINAL_CUSTODY'
    directory.mkdir(exist_ok=False)
    custody = dict(plan['lease_continuation']['completed_final'])
    validate_completed(custody)
    require(reference(__file__)['sha256'] == plan['source_files'][str(Path(__file__).resolve())],
            'custody_source_in_campaign_union')
    control = dict(root=str(root), directory=str(directory), branch=plan['shared_learner']['branch'],
        plan=reference(root / 'R118_PARALLEL_PLAN.json'), guardian=expected_guardian,
        completed_final=custody, source=reference(__file__), hard_end_unix=plan['bounds']['hard_end_unix'])
    write(directory / 'CONTROL.json', control)
    with (directory / 'process.log').open('x') as stream:
        process = subprocess.Popen([interpreter, '-B', str(Path(__file__).resolve()),
            '--control', str(directory / 'CONTROL.json')], stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, env=dict(os.environ, CUDA_VISIBLE_DEVICES=''),
            start_new_session=True)
    write(directory / 'LAUNCH.json', dict(identity=identity(process.pid), role=ROLE,
        control=reference(directory / 'CONTROL.json'), actual_CPU_process=True, never_dispatch=True))
    deadline = min(time.time() + 20, control['hard_end_unix'])
    while not (directory / 'STARTED.json').exists() and process.poll() is None and time.time() < deadline:
        time.sleep(.05)
    require((directory / 'STARTED.json').exists() and process.poll() is None, 'actual_live_custodian_started')
    document = json.loads((directory / 'STARTED.json').read_bytes())
    require(document['identity'] == identity(process.pid) and document['role'] == ROLE
            and document['never_dispatch'] is True, 'truthful_no_evaluation_custodian_identity')
    return process, dict(identity=document['identity'], evidence=reference(directory / 'STARTED.json'), role=ROLE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True)
    serve(parser.parse_args().control)
