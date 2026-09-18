"""Authorized exact-owned-native continuation at a completed learning boundary."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from extension_spec import ROOT_NAMES, digest, preview_plan, require


IDENTITIES = {0: (399101, '9637168'), 1: (412570, '9735357')}


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')


def boundary(records):
    if len(records) < 2:
        return None
    complete, learned = records[-2:]
    if complete['kind'] != 'SLEEP_COMPLETE' or learned['kind'] != 'R184_LEARN_COMPLETE':
        return None
    require(complete['index'] + 1 == learned['index'], 'adjacent_complete_and_driver_receipt')
    saved = complete['document']['resume_state']
    state = saved['state']
    require(saved['sha256'] == digest(state) and state['pending'] is None
        and state['sleep_frontier'] == len(state['rows']), 'coherent_no_pending_boundary')
    require(state['sleep_receipts'][-1]['status'] == 'COMPLETE', 'completed_learning_only')
    return complete


def tail(root):
    paths = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    return paths[-2:], [read(path) for path in paths[-2:]]


def ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()[19]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, choices=(0, 1), required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    physical = arguments.physical
    root = Path('/localhome/local-rohing') / ROOT_NAMES[physical]
    old = root / 'recovery_20260918T1646Z/control'
    preview = root / 'extension_oct01_preview_20260918T1742Z'
    output = preview / 'authorized_continuation_1754Z'
    output.mkdir(mode=0o700)
    source = preview / 'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_continual_guard import validate
    guard = read(old / 'GUARD.json')
    previous = read(guard['plan_path'])
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'previous_admitted_plan_unchanged')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    require(pins == guard['source_pins'], 'identical_runtime_source')
    authority = read(preview / 'ALLOCATION_AUTHORITY.json')
    authorization = read(Path(__file__).parent / 'CONTINUATION_AUTHORITY.json')
    require(authorization['explicit_boundary_continuation_authorized'] is True
        and authorization['physical_devices'] == [0, 1], 'explicit_user_scope')
    write(output / 'AUTHORITY.json', authorization)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(source), OMP_NUM_THREADS='1')
    with (output / 'CPU.log').open('x') as log:
        tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v',
            'test_extension_spec', 'test_continue_pair'], cwd=Path(__file__).parent,
            env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=45)
    require(tested.returncode == 0, 'receiving_CPU_tests')
    subprocess.run(['sudo', '-n', 'true'], check=True, timeout=10)
    pid, expected_ticks = IDENTITIES[physical]
    require(ticks(pid) == expected_ticks, 'exact_owned_native_identity')
    write(output / 'WAITING_BOUNDARY.json', dict(pid=os.getpid(), native_pid=pid,
        native_start_ticks=expected_ticks, started_unix=time.time(), source_pins_verified=True,
        cpu_passed=True, dispatch_module='gpu.r232_recovery', no_native_signal_yet=True))
    while True:
        paths, records = tail(root)
        complete = boundary(records)
        if complete is None:
            require(ticks(pid) == expected_ticks, 'native_identity_while_waiting')
            time.sleep(0.15)
            continue
        checkpoint = complete['document']['checkpoint']
        saved = complete['document']['resume_state']
        plan = preview_plan(previous, saved, checkpoint, authority, source)
        native.validate_plan(plan)
        native.NativeChild.verify_checkpoint(checkpoint)
        config = deepcopy(guard)
        config.update(attempt_dir=str(output), resume=True, plan_path=str(output / 'PLAN.json'),
            hard_end_unix=plan['hard_end_unix'], lease_path=str(output / 'LEASE_WINDOW.json'),
            allocation_path=str(output / 'ALLOCATION.json'), next_reserved_unix=authority['lease_end_unix'])
        require(ticks(pid) == expected_ticks, 'native_identity_before_TERM')
        current_paths, current_records = tail(root)
        if current_paths != paths or current_records[-1]['sha256'] != records[-1]['sha256']:
            continue
        bound = dict(complete=complete, head=records[-1],
            journal_id=read(root / 'raw/stream/JOURNAL.json')['journal_id'],
            bound_unix=time.time(), saved_checkpoint_RNG_preserved=True,
            unsaved_resident_sampling_RNG_claim=False, raw_originals_unchanged=True)
        from repair_receiving_sidecar import preservation
        required = source.parent / 'control'
        required.mkdir(exist_ok=True, mode=0o700)
        sidecar = required / 'PRESERVATION.json'
        document = preservation(bound, checkpoint)
        if sidecar.exists():
            require(read(sidecar) == document, 'receiving_sidecar_current_boundary')
        else:
            prepared = required / ('PRESERVATION.prepared.' + str(time.time_ns()) + '.json')
            write(prepared, document)
            with prepared.open('rb') as handle:
                os.fsync(handle.fileno())
            os.link(prepared, sidecar)
        require(read(sidecar)['checkpoint'] == checkpoint, 'receiving_constructor_sidecar_ready_before_TERM')
        write(output / 'PLAN.json', plan)
        write(output / 'LEASE_WINDOW.json', dict(lease_end_unix=authority['lease_end_unix'],
            hard_end_unix=authority['hard_end_unix'], authority_sha256=sha(preview / 'ALLOCATION_AUTHORITY.json'),
            previous_lease_receipt_sha256=guard['lease_sha256'], physical_lease_changed=False,
            provider_exact_expiry_claimed=False, safety_margin_seconds=21600))
        write(output / 'RECEIVING_CPU.json', dict(passed=True, source_pins=pins,
            log_sha256=sha(output / 'CPU.log'), no_GPU_calls=True, builder_entry_logged=True))
        write(output / 'ALLOCATION.json', dict(physical=physical, gpu_uuid=plan['gpu_uuid'],
            declared_unix=time.time(), builder_entry_logged=True, cpu_tests_passed=True,
            plan_sha256=sha(output / 'PLAN.json'), cpu_receipt_path=str(output / 'RECEIVING_CPU.json'),
            cpu_receipt_sha256=sha(output / 'RECEIVING_CPU.json')))
        config.update(plan_sha256=sha(output / 'PLAN.json'), lease_sha256=sha(output / 'LEASE_WINDOW.json'),
            allocation_sha256=sha(output / 'ALLOCATION.json'))
        write(output / 'GUARD.json', config)
        validate(output / 'GUARD.json')
        write(output / 'BOUNDARY.json', bound)
        current_paths, current_records = tail(root)
        require(current_paths == paths and current_records[-1]['sha256'] == records[-1]['sha256'],
            'still_coherent_after_successor_readiness')
        descriptor = os.pidfd_open(pid)
        require(ticks(pid) == expected_ticks, 'pidfd_exact_start_identity')
        sent = time.time()
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        write(output / 'TERM.json', dict(pid=pid, start_ticks=expected_ticks, sent_unix=sent,
            complete_index=complete['index'], head_index=records[-1]['index'],
            ready_guard_sha256=sha(output / 'GUARD.json'), signal='SIGTERM', no_SIGSTOP=True))
        poll = select.poll()
        poll.register(descriptor, select.POLLIN)
        require(bool(poll.poll(15000)), 'owned_native_exits_after_TERM')
        os.close(descriptor)
        exited = time.time()
        final_paths, final_records = tail(root)
        write(output / 'EXIT_BOUNDARY.json', dict(observed_exit_unix=exited,
            exact_head_preserved=final_paths == paths and final_records[-1]['sha256'] == records[-1]['sha256'],
            final_head_index=final_records[-1]['index'], last_old_complete_index=complete['index']))
        require(final_paths == paths and final_records[-1]['sha256'] == records[-1]['sha256'],
            'no_intervening_or_discarded_pending_work')
        time.sleep(1)
        with (output / 'DISPATCH.stdout').open('x') as stdout, (output / 'DISPATCH.stderr').open('x') as stderr:
            process = subprocess.Popen([sys.executable, '-B', '-m', 'gpu.r232_recovery',
                'dispatch', '--config', str(output / 'GUARD.json')], cwd=source, env=environment,
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True, close_fds=True)
        write(output / 'DISPATCHED.json', dict(pid=process.pid, start_ticks=ticks(process.pid),
            dispatched_unix=time.time(), old_native_exit_unix=exited, loaded=False,
            fresh_privileged_admission_required=True, no_rebirth_or_rollback=True))
        print(json.dumps(read(output / 'DISPATCHED.json')), flush=True)
        return


if __name__ == '__main__':
    main()
