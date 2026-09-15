"""Independent phase continuation; admission blocks never terminate peer lanes."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_math_pipeline_l2_run as common


def admit(root, arm, cycle, phase, deadline):
    index, unused = common.policy.DEVICES[arm]
    until = min(time.time() + 180, deadline)
    attempt = 0
    while time.time() < until:
        report = common.scan(index, root / 'SERVICE_IDENTITY.json')
        common.write(root / f'LANE_ADMISSION_{arm}_C{cycle}_{phase}_{attempt}_{time.time_ns()}.json', report)
        if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
            return report
        attempt += 1
        time.sleep(2)
    raise TimeoutError('strict_admission_blocked_lane_only_no_owner_waiver')


def stages(start_cycle, start_phase):
    sequence = [(cycle, phase) for cycle in range(1, 4) for phase in ('experience', 'readout')]
    return sequence[sequence.index((start_cycle, start_phase)):]


def run(root, arm, start_cycle, start_phase, driver, ready):
    prepared = common.validate(root)
    receipt = common.read(ready)
    assert receipt['lane_sha256'] == common.sha(Path(__file__)) and receipt['cpu_tests_passed']
    assert receipt['driver_sha256'] == common.sha(driver)
    lifetime = common.read(root / 'LIFETIME.json')
    assert receipt['lifetime_sha256'] == common.sha(root / 'LIFETIME.json')
    campaign = root / 'campaign_01_existing_rich'
    identifier = f'{arm}_C{start_cycle}_{start_phase}'
    marker = root / f'LANE_STARTED_{identifier}.json'
    with marker.open('x') as stream:
        json.dump(dict(process=common.process_identity(Path('/proc') / str(os.getpid())),
            ready_sha256=common.sha(ready), started_unix=time.time()), stream)
    child = identity = log = None
    state = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle, phase in stages(start_cycle, start_phase):
            output = campaign / arm / f'cycle{cycle}' / phase
            assert not output.exists(), 'completed_or_partial_native_phase_never_rerun'
            admit(root, arm, cycle, phase, lifetime['native_deadline_unix'])
            uuid = common.policy.DEVICES[arm][1]
            log = (campaign / f'{arm}_C{cycle}_{phase}.log').open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(driver), '--root', str(campaign),
                '--arm', arm, '--cycle', str(cycle), '--phase', phase], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=uuid, PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    TOKENIZERS_PARALLELISM='false', PYTHONDONTWRITEBYTECODE='1'),
                start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(campaign / f'LAUNCH_{arm}_C{cycle}_{phase}.json', dict(identity=identity,
                uuid=uuid, started_unix=time.time(), isolated_lane=True))
            while child.poll() is None:
                assert time.time() < lifetime['hard_deadline_unix'] - 150, 'original_lifetime'
                time.sleep(2)
            assert child.returncode == 0, 'native_failure_this_lane_only'
            completed = common.read(output / 'COMPLETE.json')
            assert completed['status'] == 'COMPLETE'
            assert completed['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
            assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
            log.close()
            log = child = identity = None
            common.write(root / f'LANE_PROGRESS_{identifier}.json', dict(completed_cycle=cycle,
                completed_phase=phase, observed_unix=time.time()))
        state = 'COMPLETE'
    except BaseException as error:
        common.write(root / f'LANE_FAILED_{identifier}.json', dict(type=type(error).__name__, message=str(error)))
        raise
    finally:
        if child is not None and child.poll() is None:
            descriptor = os.pidfd_open(child.pid)
            try:
                assert common.process_identity(Path('/proc') / str(child.pid)) == identity
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                try:
                    child.wait(timeout=max(1, min(120, lifetime['hard_deadline_unix'] - time.time() - 20)))
                except subprocess.TimeoutExpired:
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                    child.wait(timeout=10)
            finally:
                os.close(descriptor)
        if log is not None:
            log.close()
        common.write(root / f'LANE_TERMINAL_{identifier}.json', dict(status=state,
            peer_processes_signalled=0, finished_unix=time.time(), lifetime_sha256=common.sha(root / 'LIFETIME.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--arm', choices=common.policy.ARMS, required=True)
    parser.add_argument('--cycle', type=int, required=True)
    parser.add_argument('--phase', choices=('experience', 'readout'), required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--ready', type=Path, required=True)
    options = parser.parse_args()
    run(options.root, options.arm, options.cycle, options.phase, options.driver, options.ready)
