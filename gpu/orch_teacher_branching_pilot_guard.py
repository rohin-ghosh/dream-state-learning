"""Candidate node1 4/5 guardian, fail closed until Main's exact allocation.

ALLOCATION.json must be Main's hash-bound native publication, status ALLOCATED,
experiment TEACHER_DISTILLATION_DOSE4, node node1, exact devices per CELL, and
prepare_sha256. publication and lease_receipt contain path/sha256 pairs. The
lease receipt states node and lease_end_unix. No allocation is synthesized.
Run: --root NATIVE_ROOT --allocation-sha256 SHA. No automatic retries/resumes.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_rich_hot_node1_scan as scanner
from gpu import orch_teacher_branching_pilot_run as run
from organism_v6 import orch_rich_hot_node1 as node


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
DEVICES = {'FULL':dict(index=4,uuid=node.UUIDS[4]), 'OFF':dict(index=5,uuid=node.UUIDS[5])}
require = run.require


def identity(pid):
    path = Path('/proc') / str(pid)
    value = scanner.process_identity(path)
    value.update(command_sha256=hashlib.sha256((path / 'cmdline').read_bytes()).hexdigest(),
                 pgid=os.getpgid(pid), sid=os.getsid(pid))
    return value


def allocation_fields(allocation, prepare_sha256):
    require(allocation['status'] == 'ALLOCATED' and allocation['authorized_by'] == 'Main' and
        allocation['experiment'] == 'TEACHER_DISTILLATION_DOSE4' and allocation['node'] == 'node1',
        'explicit_main_allocation_required')
    require(allocation['devices'] == DEVICES, 'exact_candidate4_5_allocation_required')
    require(allocation['prepare_sha256'] == prepare_sha256 and allocation['manifest_sha256'] == run.MANIFEST_SHA,
            'allocated_CPU_and_packet_binding')
    require(allocation['max_seconds'] == 7200 and allocation['gpu_hours'] == 4 and
        allocation['readout_calls'] == 224 and allocation['updates_per_cell'] == 56, 'allocation_exact_caps')
    require(type(allocation['lease_end_unix']) in (int,float) and allocation['lease_end_unix'] <= node.LEASE_END,
            'no_unverified_lease_extension')


def validate_allocation(root, expected_sha256, prepared):
    scanner.host()
    path = root / 'ALLOCATION.json'
    require(run.sha(path) == expected_sha256, 'allocation_hash')
    allocation = run.read(path)
    allocation_fields(allocation,run.sha(root / 'PREPARE.json'))
    require(allocation['root'] == str(root), 'allocation_root')
    run.verify_refs({name:allocation[name] for name in ('publication','lease_receipt')})
    lease = run.read(allocation['lease_receipt']['path'])
    require(lease['node'] == 'node1' and lease['lease_end_unix'] == allocation['lease_end_unix'], 'verified_lease_receipt')
    require(prepared['status'] == 'CPU_READY_NOT_ALLOCATED', 'actual_CPU_ready_required')
    return allocation


def lifetime(allocation, started):
    deadline = min(started + 7200, allocation['lease_end_unix'] - 21600)
    require(deadline - started >= 600, 'insufficient_lease_margin')
    return dict(started_unix=started, hard_deadline_unix=deadline, native_deadline_unix=deadline-30,
        gpu_hours_ceiling=4, call_cap=224, output_tokens_cap=539648, no_retries=True,
        no_parent_provider_source_calls=True, scope='ISOLATED_TEACHER_DISTILLATION_NOT_CONTINUAL')


def admission(root, cell, phase, prepared):
    index = DEVICES[cell]['index']
    snapshot = scanner.scan(index, Path(prepared['config']['service_identity']))
    path = root / f'{cell}_{phase}_ADMISSION.json'
    require(not path.exists(), 'no_admission_retry')
    run.write(path, snapshot)
    require(snapshot['scanner_euid'] == 0 and snapshot['blocking_reasons'] == scanner.evaluate(snapshot,index),
            'privileged_scan_complete')
    require(snapshot['clear'] is True and not snapshot['blocking_reasons'], 'GPU_not_released_no_waiver')
    observed = datetime.fromisoformat(snapshot['created_utc']).timestamp()
    require(0 <= time.time() - observed <= 90, 'fresh_UUID_minor_lease_admission')
    return run.sha(path)


def command(root, cell, phase):
    require(cell in run.CELLS and phase in ('fit','readout'), 'known_native_phase')
    return [PYTHON,'-B','-m',run.PROGRAM,'--phase',phase,'--root',str(root),'--cell',cell]


def signal_owned(child, expected, sig):
    if child.poll() is not None:
        return False
    current = identity(child.pid)
    require(current == expected and current['uid'] == os.getuid() and current['pgid'] == child.pid and
        current['sid'] == child.pid, 'exact_owned_process_group_only')
    os.killpg(child.pid, sig)
    return True


def guard(root, expected_allocation_sha256):
    run.owned_root(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES','') == '', 'CPU_only_guard')
    prepared = run.validate_inputs(root)
    allocation = validate_allocation(root, expected_allocation_sha256, prepared)
    require(not (root / 'LIFETIME.json').exists(), 'shared_clock_exists_no_restart')
    clock = dict(lifetime(allocation,time.time()), allocation_sha256=expected_allocation_sha256,
        prepare_sha256=run.sha(root / 'PREPARE.json'))
    with (root / 'LIFETIME.json').open('x') as stream:
        json.dump(clock,stream,indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    children, streams, phases = {}, [], {}
    status, error = 'FAILED', None
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    def spawn(cell, phase, admission_sha256):
        run.check_deadline(clock, 'spawn_' + phase)
        output = (root / f'{cell}_{phase}.log').open('x')
        streams.append(output)
        child = subprocess.Popen(command(root,cell,phase),cwd=root/'source',stdout=output,stderr=subprocess.STDOUT,
            start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=DEVICES[cell]['uuid'],
                PYTHONPATH=str(root/'source'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1'))
        expected = identity(child.pid)
        require(expected['uid'] == os.getuid() and expected['pgid'] == child.pid and expected['sid'] == child.pid,
                'owned_child_session')
        children[cell] = child,expected
        phases[cell] = phase
        run.write(root/f'{cell}_{phase}_LAUNCH.json',dict(identity=expected,phase=phase,cell=cell,
            allocation_sha256=expected_allocation_sha256,admission_sha256=admission_sha256,
            command=command(root,cell,phase),uuid=DEVICES[cell]['uuid'],started_unix=time.time()))
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    try:
        checks = {cell:admission(root,cell,'fit',prepared) for cell in run.CELLS}
        for cell in run.CELLS:
            spawn(cell,'fit',checks[cell])
        while any(value in ('fit','readout') for value in phases.values()):
            require(time.time() < clock['native_deadline_unix'], 'native_deadline_stop_owned_only')
            for cell,(child,expected) in list(children.items()):
                if phases[cell] not in ('fit','readout') or child.poll() is None:
                    continue
                phase = phases[cell]
                run.write(root/f'{cell}_{phase}_EXIT.json',dict(returncode=child.returncode,finished_unix=time.time()))
                if child.returncode != 0:
                    phases[cell] = 'FAILED'
                elif not (root/cell/phase/'COMPLETE.json').exists():
                    phases[cell] = 'MISSING_COMPLETE'
                elif phase == 'fit':
                    try:
                        checked = admission(root,cell,'readout',prepared)
                        spawn(cell,'readout',checked)
                    except Exception as failure:
                        phases[cell] = 'READOUT_BLOCKED'
                        run.write(root/f'{cell}_READOUT_BLOCKED.json',dict(error=type(failure).__name__,message=str(failure)))
                else:
                    phases[cell] = 'COMPLETE'
            run.write(root/'STATUS.json',dict(phases=phases,finished_unix=time.time(),source_label=run.pilot.LABEL))
            time.sleep(1)
        status = 'COMPLETE' if all(value == 'COMPLETE' for value in phases.values()) else 'INCOMPLETE'
    except BaseException as failure:
        error = dict(type=type(failure).__name__,message=str(failure))
    finally:
        cleanup = []
        for cell,(child,expected) in children.items():
            try:
                if signal_owned(child,expected,signal.SIGTERM):
                    try:
                        child.wait(timeout=min(15,max(.1,clock['hard_deadline_unix']-time.time())))
                    except subprocess.TimeoutExpired:
                        signal_owned(child,expected,signal.SIGKILL)
                        child.wait(timeout=5)
                cleanup.append(dict(cell=cell,returncode=child.poll(),identity=expected))
            except Exception as failure:
                cleanup.append(dict(cell=cell,error=type(failure).__name__,message=str(failure),foreign_signal_sent=False))
        for stream in streams:
            stream.close()
        ledger=root/'CALL_LEDGER.jsonl'
        calls=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        run.write(root/'TERMINAL.json',dict(status=status,phases=phases,error=error,cleanup=cleanup,
            actual_reserved_calls=len(calls),reserved_output_tokens=sum(entry['cap'] for entry in calls),
            started_unix=clock['started_unix'],finished_unix=time.time(),source_label=run.pilot.LABEL,
            failed_reserved_calls_not_refunded=True,continual_changed=False,no_improvement_claim=True))
    return status


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--allocation-sha256',required=True)
    args=parser.parse_args()
    raise SystemExit(0 if guard(args.root,args.allocation_sha256)=='COMPLETE' else 1)
