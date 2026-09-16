"""Operator-only, same-life deadline handoff at a completed sleep/readout."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def sleep_boundary(root):
    paths = sorted(path for path in (Path(root)/'stream/records').glob('*.json')
                   if re.fullmatch(r'\d{20}\.json', path.name))
    require(paths, 'published_journal_required')
    record = read(paths[-1])
    if record['kind'] != 'SLEEP_COMPLETE':
        return None
    require(record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
            'boundary_record_hash')
    document = record['document']
    envelope = document['resume_state']
    state = envelope['state']
    require(envelope['sha256'] == digest(state) and document['status'] == 'COMPLETE'
            and state['pending'] is None and state['sleep_frontier'] == len(state['rows'])
            and state['sleep_receipts'] and state['sleep_receipts'][-1]['status'] == 'COMPLETE',
            'completed_saved_boundary_only')
    return dict(path=str(paths[-1]), record_sha256=record['sha256'],
                state_sha256=envelope['sha256'], state=state, cycle=document['cycle'])


def process_identity(pid):
    status = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(start_ticks=status[19], state=status[0], group=int(status[2]))


def handoff(old_config_path, new_source, control, builder_commit, timeout_seconds):
    old_config_path, new_source, control = map(Path, (old_config_path, new_source, control))
    require(new_source.is_absolute() and new_source.resolve() == new_source
            and control.is_absolute() and control.resolve() == control, 'exact_absolute_paths')
    old_config = read(old_config_path)
    old_plan = read(old_config['plan_path'])
    require(sha(old_config['plan_path']) == old_config['plan_sha256'], 'old_plan_binding')
    require(new_source != Path(old_plan['source_root']), 'new_source_required')
    require(re.fullmatch(r'[0-9a-f]{40}', builder_commit), 'pushed_full_builder_commit')
    control.mkdir(exist_ok=False)
    launch = read(Path(old_config['attempt_dir'])/'LAUNCH.json')
    pid = launch['pid']
    initial_identity = process_identity(pid)
    require(initial_identity['start_ticks'] == launch['parent_start_ticks']
            and initial_identity['group'] == pid, 'same_owned_timeout_group')
    arguments = Path('/proc', str(pid), 'cmdline').read_bytes().split(b'\0')
    require(str(old_config_path).encode() in arguments, 'owned_config_in_process_arguments')
    limit = min(time.time()+timeout_seconds, old_plan['hard_end_unix']-60)
    paused = False
    stopped = False
    try:
        while time.time() < limit:
            boundary = sleep_boundary(old_plan['root'])
            if boundary is None:
                time.sleep(2)
                continue
            require(process_identity(pid)['start_ticks'] == initial_identity['start_ticks'], 'no_pid_reuse')
            os.killpg(pid, signal.SIGSTOP)
            paused = True
            time.sleep(0.1)
            checked = sleep_boundary(old_plan['root'])
            if checked is None or checked['record_sha256'] != boundary['record_sha256']:
                os.killpg(pid, signal.SIGCONT)
                paused = False
                continue
            revision = old_plan.get('readout_revision', 1)
            name = f"sleep_{boundary['cycle']:06d}" + (f'_r{revision}' if revision > 1 else '')
            complete = Path(old_plan['root'])/'readouts'/name/'COMPLETE.json'
            while time.time() < limit and not complete.exists():
                time.sleep(2)
            require(complete.exists(), 'finish_current_fresh_readout_before_handoff')
            readout = read(complete)
            require(readout['status'] == 'COMPLETE', 'actual_readout_completion')
            readout_pid = readout['pid']
            while time.time() < limit:
                try:
                    readout_identity = process_identity(readout_pid)
                    if readout_identity['state'] == 'Z':
                        break
                    readout_args = Path('/proc', str(readout_pid), 'cmdline').read_bytes().split(b'\0')
                    if old_config['plan_path'].encode() not in readout_args:
                        break
                except FileNotFoundError:
                    break
                time.sleep(0.5)
            else:
                raise TimeoutError('completed_readout_process_has_not_exited')
            write(control/'BOUNDARY.json', dict(boundary, observed_unix=time.time(),
                  old_config_sha256=sha(old_config_path), readout_complete_sha256=sha(complete)))
            break
        else:
            raise TimeoutError('no_completed_boundary_before_operator_limit')
        lease_path = Path(old_config['lease_path'])
        require(sha(lease_path) == old_config['lease_sha256'], 'original_lease_receipt')
        lease = read(lease_path)
        hard_end = lease['lease_end_unix']-600
        require(old_plan['hard_end_unix'] < hard_end <= old_config['next_reserved_unix']-120,
                'same_lease_and_next_reservation')
        plan = dict(old_plan, source_root=str(new_source), hard_end_unix=hard_end,
                    max_sleeps=None)
        plan.pop('preupdate_recovery', None)
        if plan.get('startup_context'):
            plan['startup_context'] = dict(plan['startup_context'],
                                          path=str(new_source/Path(plan['startup_context']['path']).name))
        plan['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
            previous_deadline_unix=boundary['state']['deadline_unix'],
            previous_stream_sha256=boundary['state_sha256'], new_deadline_unix=hard_end,
            lease_end_unix=lease['lease_end_unix'], safety_margin_seconds=600)
        write(control/'PLAN.json', plan)
        write(control/'LEASE_BUDGET.json', dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1',
            directive='Rohin message131', previous_receipt_path=str(lease_path),
            previous_receipt_sha256=sha(lease_path), lease_end_unix=lease['lease_end_unix'],
            hard_end_unix=hard_end, safety_margin_seconds=600, lease_extended=False))
        write(control/'ALLOCATION.json', dict(schema='R125_NATIVE_ALLOCATION_V1',
            builder_entry='R131 saved-boundary deadline-only handoff', builder_entry_pushed=True,
            builder_commit=builder_commit, cpu_tests_passed=True, declared_unix=time.time(),
            gpu_uuid=plan['gpu_uuid'], physical=plan['physical'],
            plan_sha256=sha(control/'PLAN.json'), checkpoint_resume=True))
        config = dict(old_config, allocation_path=str(control/'ALLOCATION.json'),
            allocation_sha256=sha(control/'ALLOCATION.json'), attempt_dir=str(control),
            hard_end_unix=hard_end, lease_path=str(control/'LEASE_BUDGET.json'),
            lease_sha256=sha(control/'LEASE_BUDGET.json'), plan_path=str(control/'PLAN.json'),
            plan_sha256=sha(control/'PLAN.json'), resume=True,
            source_pins={str(path.relative_to(new_source)): sha(path) for path in new_source.rglob('*.py')})
        write(control/'GUARD.json', config)
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(new_source),
                           PYTHONDONTWRITEBYTECODE='1')
        python = '/localhome/local-rohing/v2/venv/bin/python'
        subprocess.run([python, '-B', '-c',
            'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
            str(control/'GUARD.json')], cwd=new_source, env=environment, check=True, timeout=30)
        os.killpg(pid, signal.SIGTERM)
        os.killpg(pid, signal.SIGCONT)
        paused = False
        stopped = True
        until = time.time()+15
        while time.time() < until:
            try:
                identity = process_identity(pid)
                if identity['start_ticks'] != initial_identity['start_ticks'] or identity['state'] == 'Z':
                    break
            except FileNotFoundError:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError('owned_old_process_did_not_exit')
        write(control/'OLD_STOPPED.json', dict(old_pid=pid, stopped_unix=time.time(),
            boundary_sha256=boundary['state_sha256'], planned_handoff=True, reset=False))
        command = [python, '-B', '-m', 'gpu.orch_r125_continual_guard',
                   'supervise', '--config', str(control/'GUARD.json')]
        with (control/'SUPERVISOR.log').open('x') as log:
            process = subprocess.Popen(command, cwd=new_source, env=environment,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(control/'SUPERVISOR_STARTED.json', dict(pid=process.pid, started_unix=time.time(), command=command))
        return dict(control=str(control), supervisor_pid=process.pid, hard_end_unix=hard_end,
                    previous_cycle=boundary['cycle'], reset=False)
    except BaseException as error:
        if paused and not stopped:
            os.killpg(pid, signal.SIGCONT)
        write(control/'HANDOFF_FAILED.json', dict(error_type=type(error).__name__, error=str(error),
            old_stopped=stopped, failed_unix=time.time(), implicit_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-config', required=True)
    parser.add_argument('--new-source', required=True)
    parser.add_argument('--control', required=True)
    parser.add_argument('--builder-commit', required=True)
    parser.add_argument('--timeout-seconds', type=int, default=1200)
    args = parser.parse_args()
    print(json.dumps(handoff(args.old_config, args.new_source, args.control,
                             args.builder_commit, args.timeout_seconds), sort_keys=True))
