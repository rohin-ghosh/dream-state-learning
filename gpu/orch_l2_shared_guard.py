"""Owned process-group lifetime guard; never signals other workers."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_l2_shared_run as run
from gpu import orch_replication_guard as existing


PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
LEASE_END = 1790463900


def sequence(root, arm, source_only=False, resume=False, suffix=''):
    run.source.require(root == run.ROOT and arm in ('SHORT', 'FROZEN', 'UNPARENTED'), 'SHORT_guard_never_owns_LONG')
    deadline = float((root / 'DEADLINE').read_text())
    run.source.require(time.time() < deadline <= LEASE_END, 'bounded_lease_lifetime')
    manifest_name = os.environ.get('L2_NATIVE_MANIFEST', 'PREPARE.json')
    publication = run.source.read(root / os.environ.get('L2_PUBLICATION', 'PUBLICATION.json'))
    run.source.require(publication['prepare_sha256'] == run.bridge.file_sha256(root / manifest_name)
                       and publication['cpu_tests_passed'], 'own_cpu_provenance_gate')
    index, uuid = run.DEVICES[arm]
    run.source.require(not suffix or suffix in ('_REPAIR_V4', '_REPAIR_V5'), 'exact_repair_suffix_required')
    guardian = root / (('SOURCE_GUARD' if source_only else arm + '_GUARD') + suffix)
    guardian.mkdir(exist_ok=False)
    child = None

    def stop(signum, frame):
        if child is not None:
            existing.stop(child)
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    def stage(phase, cycle):
        nonlocal child
        run.source.require(time.time() < deadline, 'batch_deadline')
        completed = root / arm / f'cycle{cycle}' / phase / 'COMPLETE.json'
        if resume and completed.exists():
            receipt = run.source.read(completed)
            expected, unused = run.input_identity(root, arm, cycle, phase)
            run.source.require(receipt['status'] == 'COMPLETE' and receipt['arm'] == arm
                               and receipt['cycle'] == cycle and receipt['phase'] == phase
                               and receipt['input_adapter'] == expected.document(), 'resume_completed_binding_drift')
            if phase == 'sleep':
                run.bridge.AdapterIdentity.from_document(receipt['output_adapter'])
            run.write(guardian / f'{cycle}_{phase}_PRESERVED.json', dict(
                path=str(completed), sha256=run.bridge.file_sha256(completed), model_calls_replayed=0))
            return
        inventory = existing.query('index,name,uuid', 'gpu')
        run.source.require(any(row[0] == str(index) and 'A100' in row[1] and row[2] == uuid for row in inventory), 'physical_uuid_drift')
        with (root / 'service_exceptions.json').open() as exceptions:
            result = subprocess.run(['python3', str(root / 'scanner.py'), str(index), uuid],
                stdin=exceptions, capture_output=True, text=True, timeout=40)
        run.write(guardian / f'{cycle}_{phase}_ADMISSION.json', dict(code=result.returncode,
                  stdout=result.stdout, stderr=result.stderr, inventory=inventory))
        run.source.require(result.returncode == 0, 'fail_closed_physical_admission')
        command = [PYTHON, '-B', '-m', 'gpu.orch_l2_shared_run', '--root', str(root),
                   '--phase', phase, '--arm', arm, '--cycle', str(cycle)]
        with (guardian / f'{cycle}_{phase}.log').open('x') as stream:
            child = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid),
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            run.write(guardian / f'{cycle}_{phase}_LAUNCH.json', dict(pid=child.pid, guardian_pid=os.getpid(),
                index=index, uuid=uuid, deadline=deadline, started_unix=time.time()))
            try:
                code = child.wait(timeout=max(1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                existing.stop(child)
                raise
        run.write(guardian / f'{cycle}_{phase}_EXIT.json', dict(code=code, finished_unix=time.time()))
        run.source.require(code == 0, 'stage_failed:' + phase)

    try:
        if source_only:
            run.source.require(arm == 'FROZEN', 'source_physical2_only')
            stage('source', 0)
        else:
            early = arm in ('SHORT', 'UNPARENTED')
            if early:
                stage('experience', 1)
            while not (root / 'SOURCE.json').exists():
                run.source.require(time.time() < deadline, 'source_wait_deadline')
                if (root / 'SOURCE_GUARD/FAILED.json').exists():
                    raise ValueError('shared_source_failed')
                time.sleep(5)
            stage('readout', 0)
            for cycle in range(1, 4):
                if not early or cycle != 1:
                    stage('experience', cycle)
                stage('sleep', cycle)
                stage('readout', cycle)
        run.write(guardian / 'COMPLETE.json', dict(status='COMPLETE', finished_unix=time.time()))
    except Exception as error:
        if child is not None:
            existing.stop(child)
        run.write(guardian / 'FAILED.json', dict(type=type(error).__name__, message=str(error)))
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=('SHORT', 'FROZEN', 'UNPARENTED'), required=True)
    parser.add_argument('--source-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--suffix', default='')
    arguments = parser.parse_args()
    sequence(run.ROOT, arguments.arm, arguments.source_only, arguments.resume, arguments.suffix)


if __name__ == '__main__':
    main()
