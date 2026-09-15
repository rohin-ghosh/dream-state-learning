"""Previously unattempted C2 readout after a zero-write parent timeout."""

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import time

from gpu import orch_math_pipeline_l2_run as common


def module(name):
    specification = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


def binding(root):
    campaign = root / 'campaign_02_recovery_paired'
    phase = campaign / 'GUIDED_SLEEP/cycle2/experience'
    failure = common.read(phase / 'FAILED.json')
    after = common.read(phase / 'FAILED_AFTER.json')
    predecessor = common.read(campaign / 'GUIDED_SLEEP/cycle1/experience/COMPLETE.json')
    parent = common.read(campaign / 'parent_queue/GUIDED_SLEEP_C2.response.json')
    assert failure['message'] == 'parent_backend_failure_no_substitute'
    assert parent['status'] == 'FAILED' and parent['error']['type'] == 'TimeoutError'
    assert failure['arm'] == 'GUIDED_SLEEP' and failure['cycle'] == 2 and failure['phase'] == 'experience'
    assert predecessor['status'] == 'COMPLETE' and predecessor['updates'] == 1194
    assert after['frozen_base_verified'] and after['process'] == failure['process']
    assert after['mounted_adapter_state_sha256'] == predecessor['output_adapter']['state_sha256']
    assert failure['input_adapter'] == predecessor['output_adapter']
    assert not (phase / 'COMPLETE.json').exists() and not (phase / 'LOSSES.jsonl').exists()
    return campaign, failure, predecessor


def native(root):
    campaign, failure, predecessor = binding(root)
    identity = common.verify_saved(predecessor['output_adapter'])
    driver = module('orch_math_pipeline_l2_native_continue')
    driver.bind_retention()
    def input_state(received_root, arm, cycle, phase):
        assert received_root == campaign and arm == 'GUIDED_SLEEP' and cycle == 2 and phase == 'readout'
        return identity, failure
    driver.frozen_native.input_state = input_state
    driver.frozen_native.run(campaign, 'GUIDED_SLEEP', 2, 'readout')


def launch(root):
    common.validate(root)
    campaign, failure, predecessor = binding(root)
    ready = root / 'GUIDED4_FAILED_SLEEP_READOUT_READY.json'
    receipt = common.read(ready)
    assert receipt['driver_sha256'] == common.sha(Path(__file__)) and receipt['cpu_tests_passed']
    assert receipt['failure_sha256'] == common.sha(campaign / 'GUIDED_SLEEP/cycle2/experience/FAILED.json')
    lifetime = common.read(root / 'LIFETIME.json')
    output = campaign / 'GUIDED_SLEEP/cycle2/readout'
    assert not output.exists(), 'unattempted_readout_only_never_retry'
    with (root / 'GUIDED4_FAILED_SLEEP_READOUT_CLAIM.json').open('x') as stream:
        stream.write(str(time.time()))
    module('orch_math_pipeline_l2_lane').admit(root, 'GUIDED_SLEEP', 2,
        'failed_parent_final_readout', lifetime['native_deadline_unix'])
    with (root / 'GUIDED4_FAILED_SLEEP_READOUT.log').open('x') as log:
        child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(root)],
            cwd=root / 'source', env=dict(os.environ, PYTHONPATH=str(root / 'source'),
                CUDA_VISIBLE_DEVICES=common.policy.DEVICES['GUIDED_SLEEP'][1], HF_HUB_OFFLINE='1',
                TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                TOKENIZERS_PARALLELISM='false'), start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
        identity = common.process_identity(Path('/proc') / str(child.pid))
        common.write(root / 'GUIDED4_FAILED_SLEEP_READOUT_LAUNCH.json', dict(identity=identity,
            ready_sha256=common.sha(ready), started_unix=time.time()))
        try:
            assert child.wait(timeout=max(1, lifetime['native_deadline_unix'] - time.time())) == 0
        finally:
            common.stop_owned(child, identity)
    assert common.read(output / 'COMPLETE.json')['status'] == 'COMPLETE'
    assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
    common.write(root / 'GUIDED4_FAILED_SLEEP_READOUT_TERMINAL.json', dict(status='COMPLETE',
        complete_sha256=common.sha(output / 'COMPLETE.json'), after_sha256=common.sha(output / 'AFTER.json'),
        parent_retry=False, sleep_status='FAILED_ZERO_WRITES', new_native_allowance=0,
        finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('launch', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    options = parser.parse_args()
    (launch if options.phase == 'launch' else native)(options.root)
