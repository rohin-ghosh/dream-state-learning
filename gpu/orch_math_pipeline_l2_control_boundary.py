"""Retire extra controls only after their current saved phase and readout."""

import argparse
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_math_pipeline_l2_run as common


def lane_module():
    specification = importlib.util.spec_from_file_location('math_control_lane', Path(__file__).with_name('orch_math_pipeline_l2_lane.py'))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def same_process(identity):
    path = Path('/proc') / str(identity['pid'])
    return path.exists() and common.process_identity(path) == identity


def send(identity, signum):
    descriptor = os.pidfd_open(identity['pid'])
    try:
        assert identity['uid'] == os.getuid() and same_process(identity)
        signal.pidfd_send_signal(descriptor, signum)
    finally:
        os.close(descriptor)


def require_complete(output):
    result = common.read(output / 'COMPLETE.json')
    assert result['status'] == 'COMPLETE'
    assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
    return result


def run(root, arm):
    common.validate(root)
    lifetime = common.read(root / 'LIFETIME.json')
    if arm == 'UNPARENTED_SLEEP':
        campaign = root / 'campaign_02_recovery_paired'
        marker = campaign / 'CONTROL_BOUNDARY_CLAIM.json'
        with marker.open('x') as stream:
            stream.write(str(time.time()))
        guardian = common.read(campaign / f'LANE_STARTED_{arm}.json')['process']
        assert not (campaign / arm / 'cycle2').exists()
        send(guardian, signal.SIGSTOP)
        common.write(campaign / 'CONTROL_BOUNDARY_HELD.json', dict(guardian=guardian,
            native_not_signalled=True, no_future_off_cycle=True, observed_unix=time.time()))
        phase = campaign / arm / 'cycle1/experience'
        child_identity = common.read(campaign / f'LAUNCH_{arm}_C1_experience.json')['identity']
        while same_process(child_identity):
            assert time.time() < lifetime['native_deadline_unix'], 'original_deadline'
            if (Path('/proc') / str(child_identity['pid']) / 'stat').read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                break
            time.sleep(2)
        completed = require_complete(phase)
        assert completed['updates'] > 0 and completed['optimizer_sha256']
        common.verify_saved(completed['output_adapter'])
        send(guardian, signal.SIGTERM)
        send(guardian, signal.SIGCONT)
        while same_process(guardian):
            assert time.time() < lifetime['native_deadline_unix']
            time.sleep(1)
        output = campaign / arm / 'cycle1/readout'
        assert not output.exists(), 'readout_never_retried'
        lane_module().admit(root, arm, 1, 'final_control_readout', lifetime['native_deadline_unix'])
        driver = Path(__file__).with_name('orch_math_pipeline_l2_replicate_native.py')
        ready = common.read(campaign / 'REPLICATE_READY.json')
        assert common.sha(driver) == ready['native_driver_sha256']
        with (campaign / 'UNPARENTED_FINAL_C1_READOUT.log').open('x') as log:
            child = subprocess.Popen([common.PYTHON, '-B', str(driver), '--root', str(campaign),
                '--arm', arm, '--cycle', '1', '--phase', 'readout'], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=common.policy.DEVICES[arm][1],
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false'),
                start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(campaign / 'FINAL_CONTROL_READOUT_LAUNCH.json', dict(identity=identity, observed_unix=time.time()))
            try:
                assert child.wait(timeout=max(1, lifetime['native_deadline_unix'] - time.time())) == 0
            finally:
                common.stop_owned(child, identity)
        require_complete(output)
    else:
        campaign = root / 'campaign_01_existing_rich'
        output = campaign / arm / 'cycle3/readout'
        terminal = root / 'LANE_TERMINAL_FROZEN_C2_experience.json'
        while not terminal.exists():
            assert time.time() < lifetime['native_deadline_unix']
            time.sleep(2)
        assert common.read(terminal)['status'] == 'COMPLETE'
        require_complete(output)
    report = lane_module().admit(root, arm, 9, 'release_after_safe_control_boundary', lifetime['native_deadline_unix'])
    common.write(root / f'ROHIN100_CONTROL_RELEASE_{arm}.json', dict(released=True,
        arm=arm, physical_index=common.policy.DEVICES[arm][0], uuid=common.policy.DEVICES[arm][1],
        completed_readout=str(output), complete_sha256=common.sha(output / 'COMPLETE.json'),
        after_sha256=common.sha(output / 'AFTER.json'), fresh_full_admission=report,
        released_unix=time.time(), next_owner='MAIN_GENERATION_OR_TRAINING'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--arm', choices=('UNPARENTED_SLEEP', 'FROZEN'), required=True)
    options = parser.parse_args()
    run(options.root, options.arm)
