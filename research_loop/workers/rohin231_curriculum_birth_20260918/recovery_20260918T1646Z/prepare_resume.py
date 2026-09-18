"""Prepare a new immutable attempt; never signal or mutate a live child."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from recovery_spec import POLICY, SAFETY_MARGIN_SECONDS, extend_plan


def inventory(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob('*')) if path.is_file() and not path.is_symlink()
        and '__pycache__' not in path.parts}


def finalize(epoch, physical, deadline):
    root, previous = epoch.parent, epoch.parent / 'recovery_6144'
    control, source = epoch / 'control', epoch / 'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_continual_guard import validate
    from organism_v6.orch_r125_continual_stream import require
    binding = native.read(control / 'PRESERVATION.json')
    coherent, checkpoint = binding['coherent_state'], binding['checkpoint']
    old_control = previous / ('control_admission2' if physical == 0 else 'control')
    old_guard = native.read(old_control / 'GUARD.json')
    old_plan, lease = native.read(old_guard['plan_path']), native.read(old_guard['lease_path'])
    paths = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    require(int(paths[-1].stem) == binding['head_index'] and native.sha(paths[-1]) == binding['head_sha256'],
        'preserved_journal_head_unchanged')
    require(not Path('/proc', str(binding['old_loaded']['document']['pid'])).exists(), 'old_native_absent')
    require(native.sha(old_guard['plan_path']) == binding['old_plan_sha256'], 'same_previous_plan')
    native.NativeChild.verify_checkpoint(checkpoint)
    plan = extend_plan(old_plan, coherent, source, deadline, lease['lease_end_unix'])
    native.validate_plan(plan)
    for name in ('test_recovery.py', 'test_frozen.py', 'r232_runtime.py'):
        destination = epoch / name
        if destination.exists():
            require(native.sha(destination) == native.sha(previous / name), 'same_test_helper_bytes')
        else:
            shutil.copy2(previous / name, destination)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source) + ':' + str(epoch), OMP_NUM_THREADS='1')
    log = control / ('CPU_' + str(time.time_ns()) + '.log')
    with log.open('x') as output:
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v',
            'test_recovery_spec', 'test_recovery', 'test_frozen'], cwd=epoch, env=environment,
            stdout=output, stderr=subprocess.STDOUT, timeout=120)
    require(result.returncode == 0, 'receiving_CPU_tests_pass')
    builder = native.read(epoch / 'BUILDER_LOG_MARGIN_CORRECTION.json')
    require(builder['logged'] is True, 'dated_builder_entry')
    pins = {str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
    require(pins == old_guard['source_pins'], 'exact_old_runtime_source_provenance')
    native.write_once(control / 'PLAN.json', plan)
    window = deepcopy(lease)
    window.update(hard_end_unix=deadline, previous_lease_receipt_sha256=native.sha(old_guard['lease_path']),
        physical_lease_changed=False, provider_exact_expiry_claimed=False,
        recovery_authorization='User explicit same-state pair recovery September18 2026',
        note='Bounded recovery inside prior conservative allocation, not a provider lease extension.')
    native.write_once(control / 'LEASE_WINDOW.json', window)
    native.write_once(control / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins,
        log_sha256=native.sha(log), builder_log=builder,
        exact_saved_state_verified=True, no_model_or_GPU_calls=True, policy=POLICY))
    native.write_once(control / 'ALLOCATION.json', dict(physical=plan['physical'], gpu_uuid=plan['gpu_uuid'],
        declared_unix=time.time(), builder_entry_logged=True, cpu_tests_passed=True,
        plan_sha256=native.sha(control / 'PLAN.json'), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'),
        cpu_receipt_sha256=native.sha(control / 'RECEIVING_CPU.json')))
    guard = deepcopy(old_guard)
    guard.update(attempt_dir=str(control), resume=True, plan_path=str(control / 'PLAN.json'),
        plan_sha256=native.sha(control / 'PLAN.json'), source_pins=pins,
        hard_end_unix=deadline, lease_path=str(control / 'LEASE_WINDOW.json'),
        lease_sha256=native.sha(control / 'LEASE_WINDOW.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=native.sha(control / 'ALLOCATION.json'))
    native.write_once(control / 'GUARD.json', guard)
    validate(control / 'GUARD.json')
    native.write_once(control / 'READY.json', dict(status='CPU_READY_NOT_LOADED', physical=physical,
        cycle=coherent['state']['sleep_receipts'][-1]['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        state_sha256=coherent['sha256'], checkpoint_sha256=checkpoint['checkpoint_sha256'],
        plan_sha256=native.sha(control / 'PLAN.json'), guard_sha256=native.sha(control / 'GUARD.json'),
        journal_id=native.read(root / 'raw/stream/JOURNAL.json')['journal_id'],
        source_bytes_changed=False, no_child_journal_writes=True, hard_end_unix=deadline,
        lease_end_unix=lease['lease_end_unix'], provider_exact_expiry_verified=False))
    print(json.dumps(native.read(control / 'READY.json'), sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    parser.add_argument('--deadline', type=float, required=True)
    parser.add_argument('--finalize-preserved', action='store_true')
    arguments = parser.parse_args()
    os.umask(0o077)
    epoch = Path(__file__).resolve().parent
    if arguments.finalize_preserved:
        finalize(epoch, arguments.physical, arguments.deadline)
        return
    root = epoch.parent
    previous = root / 'recovery_6144'
    source = epoch / 'source'
    control = epoch / 'control'
    control.mkdir(exist_ok=False)
    shutil.copytree(previous / 'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    assert inventory(source) == inventory(previous / 'source'), 'runtime_bytes_unchanged'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu import r232_recovery as recovery
    from gpu import r232_runtime as frozen
    from gpu.orch_r125_continual_guard import validate
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest, require
    require(root == recovery.ROOTS[arguments.physical], 'exact_pair_identity')
    old_control = previous / ('control_admission2' if arguments.physical == 0 else 'control')
    old_guard = native.read(old_control / 'GUARD.json')
    old_plan = native.read(old_guard['plan_path'])
    lease = native.read(old_guard['lease_path'])
    require(time.time() + 600 < arguments.deadline <= lease['lease_end_unix'] - SAFETY_MARGIN_SECONDS,
        'receiving_time_and_original_allocation_margin')
    old_records = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    loaded = [native.read(path) for path in old_records if native.read(path)['kind'] == 'LOADED'][-1]
    require(not Path('/proc', str(loaded['document']['pid'])).exists(), 'old_native_absent')
    gpu = subprocess.check_output(['nvidia-smi', '-i', str(arguments.physical),
        '--query-gpu=uuid,memory.used', '--format=csv,noheader,nounits'], text=True).strip().split(',')
    require(gpu[0].strip() == old_plan['gpu_uuid'] and int(gpu[1]) == 0, 'assigned_device_idle')
    frozen.INITIAL = native.read(recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
    journal_class = recovery.FrozenJournal if arguments.physical == 1 else recovery.LearnerJournal
    with journal_class(root / 'raw/stream') as journal:
        coherent = journal.latest_checkpoint()['document']
        stream = ContinualStream.restore(coherent, expected_sha256=coherent['sha256'])
        models = [native.read(path) for path in (root / 'raw/checkpoints').glob('*/COMMIT.json')
            if digest(native.read(path)['checkpoint_sha256']) == coherent['state']['model_state_sha256']]
        require(len(models) == 1, 'one_exact_current_model')
        checkpoint = models[0]
        native.NativeChild.verify_checkpoint(checkpoint)
        plan = extend_plan(old_plan, coherent, source, arguments.deadline, lease['lease_end_unix'])
        native.validate_plan(plan)
        proposal = native.prepare_wall_extension(plan, stream, resume=True, plan_sha256='0' * 64)
        restored = deepcopy(proposal['state']['state'])
        restored['deadline_unix'] = coherent['state']['deadline_unix']
        require(restored == coherent['state'], 'all_non_deadline_state_exact')
        raw_before = inventory(root / 'raw')
        shutil.copytree(root / 'raw', epoch / 'preserved_raw', copy_function=shutil.copy2)
        require(inventory(epoch / 'preserved_raw') == raw_before == inventory(root / 'raw'),
            'coherent_full_raw_preservation')
        native.write_once(control / 'PRESERVATION.json', dict(policy=POLICY,
            checkpoint=checkpoint, coherent_state=coherent, raw_inventory=raw_before,
            old_loaded=loaded, old_outer_exit=native.read(old_control / 'OUTER_EXIT.json'),
            old_plan_sha256=native.sha(old_guard['plan_path']), old_guard_sha256=native.sha(old_control / 'GUARD.json'),
            journal_id=native.read(root / 'raw/stream/JOURNAL.json')['journal_id'],
            head_index=native.read(old_records[-1])['index'], head_sha256=native.sha(old_records[-1]),
            saved_checkpoint_RNG_preserved=True, resident_after_checkpoint_RNG_captured=False,
            no_signals=True, no_gap_claim=False, preserved_unix=time.time()))
    finalize(epoch, arguments.physical, arguments.deadline)


if __name__ == '__main__':
    main()
