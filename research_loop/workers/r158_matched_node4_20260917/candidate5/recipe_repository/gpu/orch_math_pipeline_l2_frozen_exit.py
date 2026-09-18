"""Final parent-free test after a frozen lane's source-mask failure."""

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
    campaign = root / 'campaign_01_existing_rich'
    phase = campaign / 'FROZEN/cycle3/experience'
    failure = common.read(phase / 'FAILED.json')
    after = common.read(phase / 'FAILED_AFTER.json')
    predecessor = common.read(campaign / 'FROZEN/cycle2/experience/COMPLETE.json')
    assert failure['message'] == 'verbatim_teacher_sentence_not_child_sleep_target'
    assert failure['arm'] == 'FROZEN' and failure['phase'] == 'experience' and failure['cycle'] == 3
    assert predecessor['status'] == 'COMPLETE' and predecessor['updates'] == 0
    assert after['frozen_base_verified'] and after['process'] == failure['process']
    assert after['mounted_adapter_state_sha256'] == predecessor['output_adapter']['state_sha256'] == common.INITIAL_SHA
    assert failure['input_adapter'] == predecessor['output_adapter']
    assert not (phase / 'COMPLETE.json').exists()
    return campaign, failure, predecessor


def run_native(root):
    campaign, failure, predecessor = binding(root)
    identity = common.verify_saved(predecessor['output_adapter'])
    driver = module('orch_math_pipeline_l2_native_continue')
    driver.bind_retention()
    def input_state(received_root, arm, cycle, phase):
        assert received_root == campaign and arm == 'FROZEN' and cycle == 3 and phase == 'readout'
        return identity, failure
    driver.frozen_native.input_state = input_state
    driver.frozen_native.run(campaign, 'FROZEN', 3, 'readout')


def launch(root):
    common.validate(root)
    campaign, failure, predecessor = binding(root)
    ready = root / 'FROZEN_FAILED_SLEEP_FINAL_TEST_READY.json'
    assert common.read(ready)['driver_sha256'] == common.sha(Path(__file__))
    assert common.read(ready)['cpu_tests_passed']
    lifetime = common.read(root / 'LIFETIME.json')
    output = campaign / 'FROZEN/cycle3/readout'
    assert not output.exists()
    module('orch_math_pipeline_l2_lane').admit(root, 'FROZEN', 3, 'failed_sleep_final_test', lifetime['native_deadline_unix'])
    with (root / 'FROZEN_FAILED_SLEEP_FINAL_TEST.log').open('x') as log:
        child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(root)],
            cwd=root / 'source', env=dict(os.environ, PYTHONPATH=str(root / 'source'),
                CUDA_VISIBLE_DEVICES=common.policy.DEVICES['FROZEN'][1], HF_HUB_OFFLINE='1',
                TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                TOKENIZERS_PARALLELISM='false'), start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
        identity = common.process_identity(Path('/proc') / str(child.pid))
        common.write(root / 'FROZEN_FAILED_SLEEP_FINAL_TEST_LAUNCH.json', dict(identity=identity,
            ready_sha256=common.sha(ready), started_unix=time.time()))
        try:
            assert child.wait(timeout=max(1, lifetime['native_deadline_unix'] - time.time())) == 0
        finally:
            common.stop_owned(child, identity)
    assert common.read(output / 'COMPLETE.json')['status'] == 'COMPLETE'
    assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
    report = module('orch_math_pipeline_l2_lane').admit(root, 'FROZEN', 9, 'final_release', lifetime['native_deadline_unix'])
    common.write(root / 'ROHIN100_CONTROL_RELEASE_FROZEN.json', dict(released=True,
        arm='FROZEN', physical_index=7, uuid=common.policy.DEVICES['FROZEN'][1],
        sleep_status='FAILED_TEACHER_EXCLUSION_NO_WAIVER', sleep_failure=failure,
        completed_readout=str(output), complete_sha256=common.sha(output / 'COMPLETE.json'),
        after_sha256=common.sha(output / 'AFTER.json'), fresh_full_admission=report,
        released_unix=time.time(), next_owner='MAIN_GENERATION_OR_TRAINING'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('launch', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    options = parser.parse_args()
    (launch if options.phase == 'launch' else run_native)(options.root)
