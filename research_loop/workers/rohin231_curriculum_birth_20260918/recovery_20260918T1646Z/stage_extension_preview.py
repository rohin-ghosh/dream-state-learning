"""Read immutable COMPLETE state; write a separate preview, never dispatch/signal."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from extension_spec import POLICY, ROOT_NAMES, digest, preview_plan, require


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    arguments = parser.parse_args()
    helper = Path(__file__).resolve().parent
    root = Path('/localhome/local-rohing') / ROOT_NAMES[arguments.physical]
    old_epoch = root / 'recovery_20260918T1646Z'
    guard = read(old_epoch / 'control/GUARD.json')
    previous = read(guard['plan_path'])
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'immutable_admitted_plan')
    authority = read(helper / 'ALLOCATION_DATE_CORRECTION.json')
    records = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    head = dict(index=int(records[-1].stem), sha256=sha(records[-1]))
    selected_path = next(path for path in reversed(records) if read(path)['kind'] == 'SLEEP_COMPLETE')
    selected = read(selected_path)
    require(selected['sha256'] == digest({key: value for key, value in selected.items() if key != 'sha256'}),
        'immutable_COMPLETE_record_hash')
    saved = selected['document']['resume_state']
    checkpoint = selected['document']['checkpoint']
    output = root / 'extension_oct01_preview_20260918T1742Z'
    output.mkdir(mode=0o700)
    source = output / 'source'
    shutil.copytree(previous['source_root'], source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(pins == guard['source_pins'], 'exact_existing_runtime_bytes')
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_stream_journal import validate_wall_extension
    plan = preview_plan(previous, saved, checkpoint, authority, source)
    native.validate_plan(plan)
    validate_wall_extension(plan['authorized_wall_extension'])
    native.NativeChild.verify_checkpoint(checkpoint)
    log_path = output / 'CPU.log'
    with log_path.open('x') as log:
        tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_extension_spec'],
            cwd=helper, stdout=log, stderr=subprocess.STDOUT, timeout=30)
    require(tested.returncode == 0, 'receiving_preview_CPU_tests')
    write(output / 'PLAN_PREVIEW.json', plan)
    write(output / 'ALLOCATION_AUTHORITY.json', authority)
    write(output / 'BOUND_COMPLETE.json', selected)
    write(output / 'CHECKPOINT_COMMIT.json', checkpoint)
    write(output / 'PREVIEW_RECEIPT.json', dict(policy=POLICY, observed_unix=time.time(),
        status='PREVIEW_ONLY_NOT_AUTHORIZED_OR_DISPATCHABLE', physical=arguments.physical,
        original_guard_sha256=sha(old_epoch / 'control/GUARD.json'), old_plan_sha256=guard['plan_sha256'],
        plan_preview_sha256=sha(output / 'PLAN_PREVIEW.json'), runtime_source_pins_unchanged=True,
        authority_sha256=sha(output / 'ALLOCATION_AUTHORITY.json'), cpu_tests_passed=True,
        cpu_log_sha256=sha(log_path), observed_head=head, complete_index=selected['index'],
        complete_record_sha256=selected['sha256'], saved_state_sha256=saved['sha256'],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], optimizer_steps=checkpoint['optimizer_steps'],
        new_hard_end_unix=plan['hard_end_unix'], new_lease_end_unix=plan['lease_end_unix'],
        safety_margin_seconds=21600, no_signals=True, no_GPU_calls=True, no_journal_writes=True,
        source_files_changed=False, no_dispatch_guard_written=True, native_horizon_adopted=False,
        requires_user_restart_exception=True,
        requires_fresh_latest_boundary_rebinding_and_privileged_admission=True,
        this_observation_must_never_rollback_later_completed_or_pending_work=True))
    print(json.dumps(read(output / 'PREVIEW_RECEIPT.json'), sort_keys=True))


if __name__ == '__main__':
    main()
