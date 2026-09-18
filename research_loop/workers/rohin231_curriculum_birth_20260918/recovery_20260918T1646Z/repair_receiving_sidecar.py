"""Repair a missing receiving artifact without editing runtime or journal."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from continue_pair import read, sha, write
from extension_spec import ROOT_NAMES, digest, require


def preservation(bound, checkpoint):
    complete = bound['complete']
    require(complete['kind'] == 'SLEEP_COMPLETE' and complete['document']['checkpoint'] == checkpoint,
        'actual_completed_checkpoint_binding')
    saved = complete['document']['resume_state']
    require(saved['sha256'] == digest(saved['state'])
        and saved['state']['model_state_sha256'] == digest(checkpoint['checkpoint_sha256'])
        and saved['state']['pending'] is None
        and saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'coherent_exact_state')
    return dict(checkpoint=checkpoint, coherent_state=saved, journal_id=bound['journal_id'],
        head_index=bound['head']['index'], head_sha256=bound['head']['sha256'],
        complete_index=complete['index'], complete_record_sha256=complete['sha256'],
        saved_checkpoint_RNG_preserved=True, resident_after_checkpoint_RNG_captured=False,
        repair='Required existing ReceivingChild artifact omitted from continuation packaging',
        runtime_source_changed=False, journal_changed=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', choices=(0, 1), type=int, required=True)
    parser.add_argument('--retry-ended-learner', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    root = Path('/localhome/local-rohing') / ROOT_NAMES[args.physical]
    preview = root / 'extension_oct01_preview_20260918T1742Z'
    previous = preview / 'authorized_continuation_1754Z'
    guard = read(previous / 'GUARD.json')
    plan = read(guard['plan_path'])
    source = Path(plan['source_root'])
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_continual_guard import validate
    bound = read(previous / 'BOUNDARY.json')
    checkpoint = bound['complete']['document']['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    paths = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    require(read(paths[-1])['sha256'] == bound['head']['sha256'], 'no_intervening_journal_work')
    required = source.parent / 'control'
    required.mkdir(exist_ok=True, mode=0o700)
    value = preservation(bound, checkpoint)
    path = required / 'PRESERVATION.json'
    if path.exists():
        require(read(path) == value, 'existing_sidecar_identical')
    else:
        prepared = required / ('PRESERVATION.prepared.' + str(time.time_ns()) + '.json')
        write(prepared, value)
        with prepared.open('rb') as handle:
            os.fsync(handle.fileno())
        os.link(prepared, path)
    write(previous / 'SIDECAR_REPAIR.json', dict(physical=args.physical, repaired_unix=time.time(),
        preservation_sha256=sha(path), bound_complete_index=bound['complete']['index'],
        checkpoint_verified=True, journal_head_unchanged=True, native_signals=[],
        source_pins_unchanged=True, no_admission_claim_from_sidecar=True))
    if not args.retry_ended_learner:
        print(json.dumps(read(previous / 'SIDECAR_REPAIR.json')), flush=True)
        return
    require(args.physical == 0 and read(previous / 'EXIT.json')['exit_code'] == 1,
        'only_failed_learner_attempt')
    launch = read(previous / 'LAUNCH.json')
    require(not Path('/proc', str(launch['pid'])).exists(), 'old_timeout_process_ended')
    output = preview / 'authorized_continuation_sidecar_retry_1811Z'
    output.mkdir(mode=0o700)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), OMP_NUM_THREADS='1')
    with (output / 'CPU.log').open('x') as log:
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_extension_spec',
            'test_continue_pair', 'test_receiving_sidecar'], cwd=Path(__file__).parent, env=environment,
            stdout=log, stderr=subprocess.STDOUT, timeout=45)
    require(result.returncode == 0, 'receiving_repair_CPU_tests')
    write(output / 'PLAN.json', plan)
    write(output / 'LEASE_WINDOW.json', read(previous / 'LEASE_WINDOW.json'))
    cpu = read(previous / 'RECEIVING_CPU.json')
    cpu['log_sha256'] = sha(output / 'CPU.log')
    cpu['required_receiving_sidecar_sha256'] = sha(path)
    write(output / 'RECEIVING_CPU.json', cpu)
    allocation = read(previous / 'ALLOCATION.json')
    allocation.update(declared_unix=time.time(), plan_sha256=sha(output / 'PLAN.json'),
        cpu_receipt_path=str(output / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(output / 'RECEIVING_CPU.json'))
    write(output / 'ALLOCATION.json', allocation)
    retry = deepcopy(guard)
    retry.update(attempt_dir=str(output), plan_path=str(output / 'PLAN.json'),
        plan_sha256=sha(output / 'PLAN.json'), lease_path=str(output / 'LEASE_WINDOW.json'),
        lease_sha256=sha(output / 'LEASE_WINDOW.json'), allocation_path=str(output / 'ALLOCATION.json'),
        allocation_sha256=sha(output / 'ALLOCATION.json'))
    write(output / 'GUARD.json', retry)
    validate(output / 'GUARD.json')
    write(output / 'PREVIOUS_FAILED_ATTEMPT.json', dict(path=str(previous),
        exit_sha256=sha(previous / 'EXIT.json'), native_log_sha256=sha(previous / 'NATIVE.log'),
        before_model_load=True, journal_head_unchanged=True, previous_complete=bound['complete']['index']))
    with (output / 'DISPATCH.stdout').open('x') as stdout, (output / 'DISPATCH.stderr').open('x') as stderr:
        child = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.r232_recovery', 'dispatch',
            '--config', str(output / 'GUARD.json')], cwd=source, env=environment, stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr, close_fds=True, start_new_session=True)
    write(output / 'DISPATCHED.json', dict(pid=child.pid, dispatched_unix=time.time(),
        prior_failure_preserved=True, loaded=False, no_new_native_signal=True,
        required_receiving_sidecar_sha256=sha(path), fresh_privileged_admission_required=True))
    print(json.dumps(read(output / 'DISPATCHED.json')), flush=True)


if __name__ == '__main__':
    main()
