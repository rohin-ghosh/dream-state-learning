"""One scanner-repaired saved-cycle45 recovery, using the existing launcher."""

from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import support_identity_repair as repair


BASE = Path('/localhome/local-rohing/orch_r181_node1_20260917/journal_overlay')
LANE = BASE / 'lanes/lane7'
OUTPUT = LANE / 'identity_repair'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
STATE_SHA = '20721837aa242595049ee51c043eca6a6703b2af568ecd8199c864d602b4ba97'
CHECKPOINT_SHA = '23c5e1329b21fd1d86007321fc8e0b65ff16addb1c38046724efe45fbef7dbfd'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    path = Path(path)
    require(not path.is_symlink() and path.stat().st_size <= 64 * 1024 * 1024, 'bounded_regular_metadata')
    return json.loads(path.read_bytes())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def helpers():
    path = Path('/localhome/local-rohing/orch_r181_node1_20260917/operator/r144_base.py')
    require(sha(path) == '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270', 'existing_exact_handoff_helpers')
    spec = importlib.util.spec_from_file_location('support_existing_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.current_node('a100')
    return module


def verify_retired(base):
    request = read(LANE / 'STAGED.json')
    config = read(LANE / 'control/GUARD.json')
    plan = read(config['plan_path'])
    require(plan['physical'] == 7 and plan['root'] == '/localhome/local-rohing/orch_r136_a100_classroom_support_20260916_attempt1/run1', 'support_only')
    require(plan['hard_end_unix'] == 1790442300 and config['resume'] is True and (LANE / 'RETIRED.json').is_file(), 'same_retired_resume_wall')
    for previous in (LANE, LANE / 'readmission', LANE / 'stable_dispatch_readmission'):
        report = read(previous / 'control/ADMISSION.json')
        require(report['clear'] is False and report['blocking_reasons'] and all(reason.startswith('process_identity_drift:') for reason in report['blocking_reasons']), 'exact_known_pre_native_refusals')
        require(not any((previous / 'control' / name).exists() for name in ('LAUNCH.json', 'NATIVE.log', 'CONTAINED_COMMAND.json')), 'never_replay_possible_launch')
    for expected in request['processes'].values():
        stat = Path('/proc', str(expected['pid']), 'stat')
        if stat.exists():
            actual = stat.read_text().rsplit(')', 1)[1].split()
            require(actual[19] != expected['start_ticks'], 'retired_owner_must_not_be_live')
    saved = base.sleep_boundary(plan['root'])
    require(saved is not None and saved['cycle'] == 45 and saved['state_sha256'] == STATE_SHA, 'exact_cycle45_no_new_suffix')
    checkpoint = Path(plan['root']) / 'checkpoints/sleep_000045/COMMIT.json'
    require(sha(checkpoint) == CHECKPOINT_SHA, 'unchanged_full_saved_checkpoint')
    return request, config, plan, saved


def stage(base):
    request, config, plan, saved = verify_retired(base)
    original = Path(plan['source_root'])
    pins = base.inventory_files(original)
    require({name: value for name, value in pins.items() if name.endswith('.py')} == config['source_pins'], 'original_full_source_closure')
    require(all(pins[name] == value for name, value in repair.ORIGINAL_HASHES.items()), 'exact_scanner_before_bytes')
    OUTPUT.mkdir()
    source, control = OUTPUT / 'source', OUTPUT / 'control'
    shutil.copytree(original, source)
    for relative in repair.ORIGINAL_HASHES:
        path = source / relative
        mode = path.stat().st_mode & 0o777
        path.chmod(mode | 0o200)
        path.write_text(repair.patch(relative, path.read_text()))
        path.chmod(mode)
    after = base.inventory_files(source)
    require({name for name in pins if pins[name] != after[name]} == set(repair.ORIGINAL_HASHES) and set(pins) == set(after), 'only_two_scanner_comparisons_changed')
    require(base.inventory_files(original) == pins, 'original_source_never_mutated')
    control.mkdir()
    proposed = base.relocated_plan(plan, source)
    write(control / 'PLAN.json', proposed)
    allocation = read(config['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), support_identity_repair_sha256=sha(repair.__file__))
    write(control / 'ALLOCATION.json', allocation)
    updated = deepcopy(config)
    updated.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        source_pins={name: value for name, value in after.items() if name.endswith('.py')})
    updated['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', updated)
    env = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    check = 'from gpu.orch_r125_continual_guard import validate; from gpu.orch_rich_hot_a100_scan import same_process_identity; import sys; validate(sys.argv[1]); assert same_process_identity(dict(pid=1,uid=1,start_ticks="1",boot_id="b",command_sha256="a"), dict(pid=1,uid=1,start_ticks="1",boot_id="b",command_sha256="z")); print("ACTUAL_SOURCE_GUARD_AND_KERNEL_IDENTITY_PASS")'
    result = subprocess.run([PYTHON, '-B', '-c', check, str(control / 'GUARD.json')], cwd=source, env=env, text=True, capture_output=True, timeout=90)
    write(OUTPUT / 'RECEIVING_CPU.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0, 'actual_source_guard_validation')
    verify_retired(base)
    write(OUTPUT / 'REPAIR.json', dict(observed_unix=time.time(), source=str(source), original_source=str(original),
        changed_files={name: dict(before=pins[name], after=after[name]) for name in repair.ORIGINAL_HASHES},
        native_sha256=after['gpu/orch_r125_continual_native.py'], journal_sha256=after['gpu/orch_r125_stream_journal.py'],
        state_sha256=STATE_SHA, checkpoint_sha256=CHECKPOINT_SHA, training_configuration_unchanged=True,
        guard_sha256=sha(control / 'GUARD.json'), operator_sha256=sha(__file__), repair_sha256=sha(repair.__file__),
        final_target_fd_CVD_compute_and_visibility_guards_unchanged=True))
    print(json.dumps(dict(status='SCANNER_REPAIR_STAGED', source=str(source), record_sha256=saved['record_sha256'])), flush=True)


def launch(base):
    verify_retired(base)
    proof = read(OUTPUT / 'REPAIR.json')
    require(proof['operator_sha256'] == sha(__file__) and proof['repair_sha256'] == sha(repair.__file__), 'tested_operator_bytes')
    config = OUTPUT / 'control/GUARD.json'
    require(sha(config) == proof['guard_sha256'] and not (OUTPUT / 'control/DISPATCH_ONCE').exists(), 'one_repaired_dispatch_only')
    source = OUTPUT / 'source'
    env = dict(os.environ, PYTHONPATH=str(source), CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1')
    with (OUTPUT / 'SUCCESSOR_SUPERVISOR.log').open('xb') as log:
        process = subprocess.Popen([PYTHON, '-B', '-m', 'gpu.orch_r136_node1_launcher', 'contained-supervise', '--config', str(config)],
            cwd=source, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(OUTPUT / 'DISPATCHED.json', dict(supervisor_pid=process.pid, observed_unix=time.time(), no_retry=True))
    print(json.dumps(dict(status='REPAIRED_SUCCESSOR_DISPATCHED_NOT_LOADED', supervisor_pid=process.pid)), flush=True)


if __name__ == '__main__':
    require(os.getuid() == 1395 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'scoped_CPU_operator')
    descriptor = os.open(BASE / 'lane7.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        module = helpers()
        {'stage': stage, 'launch': launch}[sys.argv[1]](module)
    finally:
        os.close(descriptor)
