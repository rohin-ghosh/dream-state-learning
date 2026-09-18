"""Retry only a failed pre-native admission scan, preserving its evidence."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

from math_c import HOME, PYTHON, host, read, require, sha, write


def run(physical, withdrawn=False, r206=False, r210=False):
    host()
    require(physical in (0, 1, 3, 5) or withdrawn and physical in (2, 7)
        or r206 and physical in (0, 1, 2, 3, 5, 6, 7)
        or r210 and physical in (2, 3, 5, 6, 7), 'only_selected_slots')
    require(not r210 or not (r206 or withdrawn), 'one_phase_only')
    life_root = HOME if physical == 6 else HOME.parent / f'SCALE_physical{physical}'
    require(not (life_root / 'R207_MAIN_INFERENCE_RESERVATION.json').exists(), 'reserved_for_Main_no_new_allocation')
    root = life_root / 'r210' if r210 else life_root / 'reload_r206' if r206 else life_root
    control = root / ('withdrawn/control' if withdrawn else 'control')
    source = Path(read(control / 'PLAN.json')['source_root'])
    dispatch_name = 'WITHDRAWN_DISPATCHED.json' if withdrawn else 'DISPATCHED.json'
    with (root / 'SOURCE.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = read(root / dispatch_name)
        require(not Path('/proc', str(previous['supervisor_pid'])).exists(), 'previous_supervisor_exited')
        require(not any((control / name).exists() for name in
            ('LAUNCH.json', 'CONTAINED_COMMAND.json', 'ADMISSION_TIME.json', 'EXIT.json')),
            'failed_before_native_or_containment_dispatch')
        records = [path for path in (life_root / 'life/stream/records').glob('*.json') if path.stem.isdigit()]
        if r210:
            last = read(max(records, key=lambda path: int(path.stem)))
            preserved = read(root / 'PRESERVED.json')
            require(last['sha256'] == preserved['last_record_sha256']
                and last['kind'] == 'TERMINAL' and last['document'] ==
                dict(completed_sleeps=57, status='R184_SCREEN_STOP'), 'unchanged_R210_exact_saved_screen')
        elif r206:
            last = read(max(records, key=lambda path: int(path.stem)))
            retired = read(root / 'boundary/RETIRED.json')
            require(last['kind'] == 'R184_LEARN_COMPLETE' and last['document']['cycle'] == retired['cycle']
                and last['previous_sha256'] == retired['saved']['record_sha256']
                and read(life_root / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'],
                'exact_preserved_boundary_no_new_native_records')
        elif withdrawn:
            last = read(max(records, key=lambda path: int(path.stem)))
            require(last['kind'] == 'TERMINAL' and last['document']['completed_sleeps'] == 54
                and read(root / 'PARENT_WITHDRAWAL_RECONCILED.json')['no_pending_parent_replay'],
                'saved_COMPLETE54_terminal_no_new_continuation_records')
        else:
            require(len(records) == 4 and max(int(path.stem) for path in records) == 3,
                'fixed_source_only_no_new_native_records')
        report = read(control / 'ADMISSION.json')
        require(not report['clear'] and report['blocking_reasons'] and
            all(reason.startswith('process_identity_drift:') for reason in report['blocking_reasons']),
            'only_transient_scan_identity_drift_no_admission_override')
        require(report['gpu']['memory_used_mib'] == 0, 'previous_scan_observed_empty_device')
        if withdrawn:
            subprocess.run([str(PYTHON), '-B', '-c',
                'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
                str(control / 'GUARD.json')], cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
                PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'), check=True, timeout=45)
        else:
            require(sha(control / 'GUARD.json') == read(root / 'RECEIVING_READY.json')['guard_sha256'],
                'same_receiving_guard')
        sidecars = [('bridge_pid', ['--config', str(root / ('withdrawn/BRIDGE.json' if withdrawn else 'BRIDGE.json'))])]
        if not withdrawn and not r206 and not r210:
            sidecars.append(('withdrawal_pid', [str(root / 'withdraw_math_c.py')]))
        for label, expected_tail in sidecars:
            process = Path('/proc', str(previous[label]))
            arguments = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
            require(process.stat().st_uid == os.getuid() and arguments[-len(expected_tail):] == expected_tail,
                'same_existing_owned_sidecar_no_duplicate')
        failed = root / f'pre_native_admission_{time.time_ns()}'
        failed.mkdir()
        for name in ('DISPATCH_ONCE', 'ADMISSION.json', 'SERVICE_IDENTITY.json', 'SUPERVISOR.log'):
            if (control / name).exists():
                (control / name).rename(failed / name)
        (root / dispatch_name).rename(failed / dispatch_name)
        module = 'gpu.orch_r188_node4_rehome_containment' if physical == 6 else 'gpu.r203_node4_containment'
        command = [str(PYTHON), '-B', '-m', module,
            'contained-supervise', '--config', str(control / 'GUARD.json')]
        with (control / 'SUPERVISOR.log').open('x') as log:
            supervisor = subprocess.Popen(command, cwd=source, env=dict(os.environ,
                CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(previous, supervisor_pid=supervisor.pid, started_unix=time.time(),
            previous_pre_native_attempt=str(failed), fresh_unchanged_admission_required=True)
        write(root / dispatch_name, receipt)
        if withdrawn:
            with (root / 'SCREEN_R204_MONITOR.log').open('x') as log:
                subprocess.Popen([str(PYTHON), '-B', str(HOME / 'finish_r204_screen.py'),
                    '--physical', str(physical)], stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
        print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--physical', type=int, required=True)
    parser.add_argument('--withdrawn', action='store_true')
    parser.add_argument('--r206', action='store_true')
    parser.add_argument('--r210', action='store_true')
    options = parser.parse_args()
    run(options.physical, options.withdrawn, options.r206, options.r210)
