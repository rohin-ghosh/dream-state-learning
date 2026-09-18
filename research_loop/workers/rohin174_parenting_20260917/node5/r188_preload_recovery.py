"""Fresh exact-saved-boundary admission after two pinned scanner-only refusals."""

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time


BASE = Path('/localhome/local-rohing')
PYTHON = BASE / 'v2/venv/bin/python'
SCOPES = {
    'pilot': ('orch_r181_node5_pilot_1789683883580514498', 46, 6,
              ['process_identity_drift:2694243']),
    'repo_reader': ('orch_r181_node5_repo_reader_1789683884022936464', 44, 7,
                    ['process_identity_drift:3159']),
}
DISPATCH_MARKERS = {'LAUNCH.json', 'NATIVE.log', 'NATIVE_EXIT.json',
    'CONTAINED_COMMAND.json', 'CONTAINMENT_VERIFIED.json', 'SERVICE_EXIT.json'}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def eligibility(label, failure, admission, names, present, actual, expected):
    require(label in SCOPES, 'only_two_pinned_preload_refusals')
    require(failure.get('reason') == 'original_privileged_clear_admission' and
            failure.get('retired') is True and failure.get('terminated') is True,
            'typed_scanner_refusal_only')
    require(admission.get('clear') is False and admission.get('scanner_euid') == 0 and
            admission.get('blocking_reasons') == SCOPES[label][3], 'exact_preserved_admission')
    require(not set(names).intersection(DISPATCH_MARKERS), 'never_retry_prior_native_dispatch')
    require(not present, 'all_retired_owners_absent')
    require(actual == expected, 'same_complete_boundary_no_suffix')


def inspect(label):
    original = BASE / SCOPES[label][0]
    ready = read(original / 'READY.json')
    actual = read(original / 'ACTUAL_BOUNDARY_READY.json')
    inputs = read(original / 'INPUT.json')
    record_path = Path(inputs['storage_root']) / 'stream/records' / Path(actual['boundary']['path']).name
    head = sorted(record_path.parent.glob('[0-9]' * 20 + '.json'))[-1]
    owners = list(ready['pair'].values()) + [read(original / 'OPERATOR_STARTED.json')['identity']]
    present = [owner['pid'] for owner in owners if Path('/proc', str(owner['pid'])).exists()]
    eligibility(label, read(original / 'EXECUTION_FAILED.json'), read(original / 'attempt/ADMISSION.json'),
                [path.name for path in (original / 'attempt').iterdir()], present,
                ref(head)['sha256'], actual['boundary']['sha256'])
    record = read(record_path)
    require(record['kind'] == 'SLEEP_COMPLETE' and record['document']['cycle'] == SCOPES[label][1]
            and actual['proof']['status'] == 'PASS' and actual['proof']['cuda_initialized'] is False,
            'exact_completed_cycle_and_restore_CPU')
    return original, ready, inputs, record_path


def load_operator(output):
    sys.path.insert(0, str(output))
    specification = importlib.util.spec_from_file_location('pinned_operator', output / 'rollout_operator.py')
    operator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(operator)
    return operator


def unit_name(operator, output, physical):
    unit = operator.successor_unit_name(output, physical)
    require(physical != 7 or re.fullmatch(r'orch-r136-native-[a-f0-9]{32}', unit),
            'unchanged_reader_capsule_unit_contract')
    return unit


def previous_refusal(previous):
    require(previous == BASE / 'orch_r181_node5_repo_reader_r188_readmit_1789687810659483047',
            'only_exact_reader_unit_refusal')
    failure = read(previous / 'READMISSION_FAILED.json')
    require(failure['reason'] == 'unique_probe_unit' and failure['automatic_retry'] is False,
            'only_pre_dispatch_unit_validation_refusal')
    require(not set(path.name for path in (previous / 'attempt').iterdir()).intersection(DISPATCH_MARKERS),
            'no_prior_reader_dispatch')
    require(not Path('/proc', str(read(previous / 'READMISSION_STARTED.json')['pid'])).exists(),
            'prior_readmission_operator_exited')
    return {name: ref(previous / name) for name in ('READMISSION_FAILED.json', 'READMISSION_STARTED.json',
        'READMISSION_BINDING.json', 'attempt/ADMISSION.json', 'GUARD.json')}


def execute(output):
    binding = read(output / 'READMISSION_BINDING.json')
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'node5_owner_only')
    label = binding['label']
    original, ready, inputs, record_path = inspect(label)
    require(binding['helper'] == ref(Path(__file__)), 'bound_readmission_helper')
    for name, expected in binding['preserved'].items():
        require(ref(original / name) == expected, 'preserved_original_' + name)
    if binding.get('previous'):
        require(previous_refusal(Path(binding['previous']['root'])) == binding['previous']['files'],
                'exact_preserved_reader_pre_dispatch_refusal')
    operator = load_operator(output)
    saved, config, plan = operator.validate_successor(output)
    require(plan['physical'] == SCOPES[label][2] and plan['rehearsal_presentations'] == 0
            and plan['new_presentations'] == 16, 'unchanged_R181_slot_recipe')
    boundary = saved.saved_boundary(plan['root'])
    require(boundary is not None and boundary['reference']['sha256'] == ref(record_path)['sha256'],
            'exact_current_saved_boundary')
    lock_path = BASE / ('orch_r157_' + label + '_HANDOFF.lock')
    descriptor = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (output / 'READMISSION_ONCE').mkdir()
        inspect(label)
        proof = operator.cpu_proof(output, boundary, 'READMISSION')
        require(proof['optimizer_steps'] == read(original / 'ACTUAL_BOUNDARY_READY.json')['proof']['optimizer_steps'],
                'same_saved_optimizer_steps')
        write(output / 'READMISSION_INTENT.json', dict(binding=ref(output / 'READMISSION_BINDING.json'),
            boundary=ref(record_path), lock_inode=os.fstat(descriptor).st_ino, signals=0,
            discarded_updates=0, reset=False, replay=False, observed_unix=time.time()))
        operator.supervise(output)
    except BaseException as error:
        write(output / 'READMISSION_FAILED.json', dict(error_type=type(error).__name__, reason=str(error),
            automatic_retry=False, signals=0, observed_unix=time.time()))
        raise
    finally:
        os.close(descriptor)


def prepare(label, output, previous=None):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'node5_owner_only')
    original, old_ready, inputs, record_path = inspect(label)
    prior = dict(root=str(previous), files=previous_refusal(previous)) if previous else None
    require(output.parent == BASE and output.name.startswith('orch_r181_node5_' + label + '_r188_readmit_'),
            'fresh_owned_readmission_root')
    output.mkdir(mode=0o700)
    operator = load_operator(original)
    old_manifest = read(original / 'SOURCE_MANIFEST.json')
    saved = operator.load_saved(original / 'source')
    require(saved.files(original / 'source') == old_manifest['source_files'], 'unchanged_tested_source')
    shutil.copytree(original / 'source', output / 'source')
    required = set(old_ready['auxiliary_files']) | {
        'rollout_operator.py', 'policy.py', 'MAIN_JOURNAL.py', 'INPUT.json', 'R181_AUTHORITY.json',
        'OWNER_RETIRED.json', 'STAGE_CPU.json', 'OPERATOR_CPU.log', 'JOURNAL_OVERLAY.json'}
    for name in required:
        shutil.copyfile(original / name, output / name)
    shutil.copyfile(Path(__file__), output / 'r188_preload_recovery.py')
    plan = read(original / 'PLAN.json')
    old_source = Path(plan['source_root'])
    plan['source_root'] = str(output / 'source')
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(output / 'source' / Path(plan['startup_context']['path']).relative_to(old_source))
    write(output / 'PLAN.json', plan)
    allocation = read(original / 'ALLOCATION.json')
    allocation.update(plan_sha256=ref(output / 'PLAN.json')['sha256'], declared_unix=time.time())
    write(output / 'ALLOCATION.json', allocation)
    config = read(original / 'GUARD.json')
    config.update(plan_path=str(output / 'PLAN.json'), plan_sha256=ref(output / 'PLAN.json')['sha256'],
        allocation_path=str(output / 'ALLOCATION.json'), allocation_sha256=ref(output / 'ALLOCATION.json')['sha256'],
        attempt_dir=str(output / 'attempt'))
    config['device_containment']['unit'] = unit_name(operator, output, plan['physical'])
    write(output / 'GUARD.json', config)
    write(output / 'COMMAND_PREFLIGHT.json', operator.command_preflight(saved, config, plan, output))
    manifest = copy.deepcopy(old_manifest)
    manifest['source_root'] = str(output / 'source')
    require(saved.files(output / 'source') == old_manifest['source_files'], 'byte_identical_source_copy')
    write(output / 'SOURCE_MANIFEST.json', manifest)
    ready = copy.deepcopy(old_ready)
    ready.update(config=ref(output / 'GUARD.json'), plan=ref(output / 'PLAN.json'),
        source_manifest=ref(output / 'SOURCE_MANIFEST.json'), operator=ref(output / 'rollout_operator.py'),
        status='TYPED_PRELOAD_RECOVERY_NO_SIGNALS', staged_unix=time.time())
    write(output / 'READY.json', ready)
    preserved = ('EXECUTION_FAILED.json', 'OWNER_RETIRED.json', 'attempt/ADMISSION.json',
        'READY.json', 'OPERATOR_STARTED.json', 'ACTUAL_BOUNDARY_READY.json', 'GUARD.json', 'PLAN.json', 'SOURCE_MANIFEST.json')
    write(output / 'READMISSION_BINDING.json', dict(label=label, original=str(original),
        preserved={name: ref(original / name) for name in preserved}, helper=ref(output / 'r188_preload_recovery.py'),
        boundary=ref(record_path), previous=prior, native_source_unchanged=True, signals=0))
    command = [str(PYTHON), '-B', str(output / 'r188_preload_recovery.py'), 'execute', '--output', str(output)]
    if inputs['storage_root'] != inputs['logical_root']:
        shell = 'mount --bind ' + shlex.quote(inputs['storage_root']) + ' ' + shlex.quote(inputs['logical_root'])
        shell += ' && exec /usr/bin/setpriv --reuid=2524 --regid=2524 --clear-groups ' + shlex.join(command)
        command = ['sudo', '-n', 'unshare', '--mount', '--propagation', 'private', '/bin/bash', '-c', shell]
    with (output / 'READMISSION.log').open('x') as stream:
        process = subprocess.Popen(command, cwd=output, env=operator.environment(output / 'source'),
            stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    write(output / 'READMISSION_STARTED.json', dict(pid=process.pid, started_unix=time.time(),
        binding=ref(output / 'READMISSION_BINDING.json'), loaded=False, signals=0))
    print(json.dumps(dict(output=str(output), pid=process.pid, binding=ref(output / 'READMISSION_BINDING.json'), loaded=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'execute'))
    parser.add_argument('--label', choices=SCOPES)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    arguments = parser.parse_args()
    if arguments.action == 'prepare':
        prepare(arguments.label, arguments.output, arguments.previous)
    else:
        execute(arguments.output)
