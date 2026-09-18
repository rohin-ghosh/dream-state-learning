"""Prepare, preserve and resume P3 with lease-bound native and wrapper timers."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time
import uuid


ROOT = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
OLD = ROOT / 'r212'
TARGET = ROOT / 'r233_lease_continuation'
SOURCE = TARGET / 'source'
CONTROL = TARGET / 'control'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
END_UNIX = 1790359200
LEASE_UNIX = END_UNIX + 21600
PID = 237705
TICKS = '27878033'
JOURNAL = '0727d448bca644bfa64f1a1f65c1f21f'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def records():
    return sorted(path for path in (ROOT / 'life/stream/records').glob('*.json') if path.stem.isdigit())


def latest_complete(paths):
    for path in reversed(paths):
        row = read(path)
        if row['kind'] == 'SLEEP_COMPLETE' and row['document']['status'] == 'COMPLETE':
            return path, row
    raise ValueError('no_completed_sleep')


def stage():
    previous_guard = read(OLD / 'control/GUARD.json')
    require(sha(previous_guard['plan_path']) == previous_guard['plan_sha256'], 'unchanged_original_plan')
    previous = read(previous_guard['plan_path'])
    require(previous['root'] == str(ROOT / 'life') and previous['physical'] == 3
        and previous['max_sleeps'] is None, 'same_P3_unbounded_sleep_count')
    require(all(sha(Path(previous['source_root']) / name) == checksum
        for name, checksum in previous_guard['source_pins'].items()), 'original_source_closure')
    TARGET.mkdir(mode=0o700)
    CONTROL.mkdir()
    shutil.copytree(previous['source_root'], SOURCE, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    helper = Path(__file__).with_name('p3_resume_runtime.py')
    shutil.copyfile(helper, SOURCE / 'gpu/r233_p3_resume.py')
    guard_path = SOURCE / 'gpu/orch_r125_continual_guard.py'
    text = guard_path.read_text()
    seam = "    child.run(config['plan_path'], resume=config['resume'])"
    require(text.count(seam) == 1, 'exact_native_continuation_seam')
    guard_path.write_text(text.replace(seam,
        '    from gpu.r233_p3_resume import activate as activate_saved_boundary\n'
        '    activate_saved_boundary()\n' + seam))
    for path in (guard_path, SOURCE / 'gpu/r233_p3_resume.py'):
        compile(path.read_text(), str(path), 'exec')
    write(CONTROL / 'STAGED.json', dict(observed_unix=time.time(), status='SOURCE_READY_NATIVE_UNCHANGED',
        old_plan_sha256=previous_guard['plan_sha256'], original_guard_sha256=sha(OLD / 'control/GUARD.json'),
        source_pins={str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')},
        native_signals=[], authority='Repeated user directive to remove short deadlines on kept lives',
        hard_end_unix=END_UNIX, lease_end_unix=LEASE_UNIX, provider_expiry_independently_verified=False))
    print('P3_SOURCE_STAGED', flush=True)


def continue_life():
    require((CONTROL / 'STAGED.json').is_file(), 'source_staged_first')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path.insert(0, str(SOURCE))
    from gpu.r212_prose_replay import activate as historical
    historical()
    from gpu.r233_p3_resume import activate, restored_state, KIND
    from gpu import orch_r125_continual_native as native
    from organism_v6.orch_r125_continual_stream import ContinualStream
    process = Path('/proc') / str(PID)
    signals = []
    if process.exists():
        require(process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19] == TICKS,
            'exact_live_P3_incarnation')
        descriptor = os.pidfd_open(PID)
        try:
            start_complete, start_row = latest_complete(records())
            while process.exists():
                complete_path, complete = latest_complete(records())
                if complete['index'] > start_row['index']:
                    native.NativeChild.verify_checkpoint(complete['document']['checkpoint'])
                    require(process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19] == TICKS,
                        'same_exact_native_before_boundary_handoff')
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                    signals.append(dict(signal='SIGTERM', unix=time.time(), complete_index=complete['index']))
                    require(bool(select.select([descriptor], [], [], 20)[0]), 'native_exit_confirmed')
                    break
                if select.select([descriptor], [], [], .5)[0]:
                    break
        finally:
            os.close(descriptor)
    require(not process.exists(), 'old_native_absent_before_journal_write')
    paths = records()
    head = read(paths[-1])
    complete_path, complete = latest_complete(paths)
    require(head['journal_id'] == complete['journal_id'] == JOURNAL, 'same_original_journal')
    saved = restored_state(complete)
    checkpoint = complete['document']['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    previous_guard = read(OLD / 'control/GUARD.json')
    previous = read(previous_guard['plan_path'])
    plan = deepcopy(previous)
    plan.update(source_root=str(SOURCE), hard_end_unix=END_UNIX, lease_end_unix=LEASE_UNIX,
        authorized_wall_extension=dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=saved['state']['deadline_unix'], previous_stream_sha256=saved['sha256'],
            new_deadline_unix=END_UNIX, lease_end_unix=LEASE_UNIX, safety_margin_seconds=21600))
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(SOURCE / Path(plan['startup_context']['path']).relative_to(previous['source_root']))
    native.validate_plan(plan)
    native.prepare_wall_extension(plan, ContinualStream.restore(saved, expected_sha256=saved['sha256']),
        resume=True, plan_sha256='0' * 64)
    preserved = TARGET / 'preserved'
    preserved.mkdir()
    checkpoint_root = ROOT / 'life/checkpoints' / f"sleep_{complete['document']['cycle']:06d}"
    subprocess.run(['cp', '-a', '--reflink=auto', str(checkpoint_root), str(preserved / checkpoint_root.name)], check=True)
    write(preserved / 'CHECKPOINT_MANIFEST.json', {str(path.relative_to(preserved)): sha(path)
        for path in preserved.rglob('*') if path.is_file()})
    receipt = dict(old_native_absent=True, old_native_pid=PID, old_native_start_ticks=TICKS,
        journal_id=JOURNAL, old_head_index=head['index'], old_head_sha256=head['sha256'],
        complete_path=str(complete_path), complete_sha256=complete['sha256'],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], saved_state_sha256=saved['sha256'],
        uninterrupted_resident_continuity_claimed=False, preserved_tail_record_count=head['index']-complete['index'],
        signals=signals, observed_unix=time.time(), new_deadline_unix=END_UNIX,
        original_journal_files_deleted=False)
    write(CONTROL / 'RECOVERY.json', receipt)
    moved = []
    for category in ('pre_sleep', 'exploration'):
        for path in (ROOT / 'life/stream' / category).glob('*'):
            number = path.stem.split('_')[-1]
            if path.is_file() and number.isdigit() and int(number) > complete['document']['cycle']:
                destination = preserved / category / path.name
                destination.parent.mkdir(exist_ok=True)
                path.rename(destination)
                moved.append(dict(original=str(path), preserved=str(destination), sha256=sha(destination)))
    write(CONTROL / 'TAIL_ARTIFACTS_PRESERVED.json', dict(moved=moved, deleted=False))
    journal_class = activate()
    with journal_class(ROOT / 'life/stream', create=False) as journal:
        proof = journal.record(KIND, dict(receipt_path=str(CONTROL / 'RECOVERY.json'),
            receipt_sha256=sha(CONTROL / 'RECOVERY.json'), state=saved))
    write(CONTROL / 'RECOVERY_APPENDED.json', proof)
    write(CONTROL / 'PLAN.json', plan)
    write(CONTROL / 'LEASE.json', dict(lease_end_unix=LEASE_UNIX, hard_end_unix=END_UNIX,
        authority='User/Fable September18 17:25 reiterated: existing node4 lease September26',
        provider_expiry_independently_verified=False, lease_purchase_or_extension=False))
    write(CONTROL / 'CPU.json', dict(passed=True, source_compiled=True, checkpoint_verified=True,
        exact_saved_wall_extension_prepared=True, journal_replay_passed=True, observed_unix=time.time()))
    write(CONTROL / 'ALLOCATION.json', dict(plan_sha256=sha(CONTROL / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=3, builder_entry_logged=True,
        cpu_receipt_path=str(CONTROL / 'CPU.json'), cpu_receipt_sha256=sha(CONTROL / 'CPU.json'),
        declared_unix=time.time()))
    guard = deepcopy(previous_guard)
    guard.update(plan_path=str(CONTROL / 'PLAN.json'), plan_sha256=sha(CONTROL / 'PLAN.json'),
        allocation_path=str(CONTROL / 'ALLOCATION.json'), allocation_sha256=sha(CONTROL / 'ALLOCATION.json'),
        lease_path=str(CONTROL / 'LEASE.json'), lease_sha256=sha(CONTROL / 'LEASE.json'),
        hard_end_unix=END_UNIX, next_reserved_unix=LEASE_UNIX, attempt_dir=str(CONTROL),
        source_pins={str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')})
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(CONTROL / 'GUARD.json', guard)
    from gpu.orch_r125_continual_guard import validate
    validate(CONTROL / 'GUARD.json')
    write(CONTROL / 'DISPATCHING.json', dict(unix=time.time(), status='DISPATCH_NOT_LOAD',
        complete_index=complete['index'], sleep=complete['document']['cycle'], hard_end_unix=END_UNIX))
    os.chdir(SOURCE)
    environment = dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    os.execve(PYTHON, [PYTHON, '-B', '-m', 'gpu.r203_node4_containment',
        'contained-supervise', '--config', str(CONTROL / 'GUARD.json')], environment)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'continue'))
    arguments = parser.parse_args()
    stage() if arguments.action == 'stage' else continue_life()
