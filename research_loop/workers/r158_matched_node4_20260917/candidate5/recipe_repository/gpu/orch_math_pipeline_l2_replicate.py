"""New paired replicate after terminal interruption; never resume lost state."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_math_pipeline_l2_run as common


NAME = 'campaign_02_recovery_paired'
ARMS = ('GUIDED_SLEEP', 'UNPARENTED_SLEEP')


def lane_module():
    specification = importlib.util.spec_from_file_location('math_replicate_lane', Path(__file__).with_name('orch_math_pipeline_l2_lane.py'))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def require_failed_recovery(document):
    assert document['no_state_accepted'] and document['native_generation_calls'] == 0
    assert document['message'].startswith('reconstruction_loss_mismatch_no_tolerance_waiver:')


def sequence():
    return [(0, 'readout')] + [(cycle, phase) for cycle in range(1, 4) for phase in ('experience', 'readout')]


def prepare(root):
    prepared = common.validate(root)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    old = root / 'campaign_01_existing_rich'
    assert not (root / NAME).exists()
    terminal = {}
    for arm in ARMS:
        output = old / arm / 'cycle1/experience'
        assert not (output / 'adapter').exists() and not (output / 'COMPLETE.json').exists()
        failed = root / f'RECOVERY_{arm}/FAILED.json'
        require_failed_recovery(common.read(failed))
        native_identity = common.read(output / 'REQUEST.json')['process']
        process = Path('/proc') / str(native_identity[1])
        if process.exists():
            observed = common.process_identity(process)
            assert [observed['boot_id'], observed['pid'], int(observed['start_ticks'])] != native_identity
        records = [json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines()]
        terminal[arm] = dict(status='TERMINAL_INTERRUPT', original_unsaved_updates=len(records),
            original_saved_final_identity_unavailable=True, numerical_recovery='FAILED_AT_UPDATE_2',
            recovery_failure_sha256=common.sha(failed),
            preserved_files={str(path.relative_to(old)): common.sha(path) for path in sorted(output.rglob('*')) if path.is_file()})
    marker = root / 'INTERRUPTED_LEARNING_ARMS.json'
    assert not marker.exists()
    common.write(marker, dict(arms=terminal, observed_unix=time.time(), no_state_accepted=True))
    initial_path = old / 'INITIAL.json'
    initial = common.read(initial_path)
    assert initial['output_adapter']['state_sha256'] == common.INITIAL_SHA
    campaign = common.initialize(root, NAME, initial, dict(path=str(initial_path), sha256=common.sha(initial_path)))
    siblings = {name: common.sha(Path(__file__).with_name(name)) for name in (
        'orch_math_pipeline_l2_lane.py', 'orch_math_pipeline_l2_replicate_native.py', 'orch_math_pipeline_l2_native_continue.py')}
    tests = root / 'REPLICATE_CPU_TESTS.log'
    assert tests.exists() and '\nOK\n' in tests.read_text()
    common.write(campaign / 'REPLICATE_READY.json', dict(schema='NEW_PAIRED_RECOVERY_LIVES_V1',
        campaign=NAME, not_continuation_of_interrupted_lives=True, initial_optimizer='NEW',
        same_genuine_saved_child=True, source_sha256=prepared['source_sha256'],
        runner_sha256=common.sha(Path(__file__)), lane_sha256=siblings['orch_math_pipeline_l2_lane.py'],
        native_driver_sha256=siblings['orch_math_pipeline_l2_replicate_native.py'],
        retention_driver_sha256=siblings['orch_math_pipeline_l2_native_continue.py'],
        cpu_tests_passed=True, cpu_tests_sha256=common.sha(tests),
        lifetime_sha256=common.sha(root / 'LIFETIME.json'), cohort_sha256=common.sha(campaign / 'COHORT.json'),
        interrupted_receipt_sha256=common.sha(marker), foundation_upgrade=False,
        counter_policy='NEW_REPLICATE_COUNTERS_SAME_ORIGINAL_LIFETIME_SECOND_CAMPAIGN_SLOT',
        max_calls_per_arm=272, independent_new_tasks=False, repeated_cohort_monitoring=True,
        frozen_comparator=dict(campaign=old.name, arm='FROZEN', contemporaneous=False,
            unchanged_saved_identity=common.INITIAL_SHA, baseline_retention_missing=True),
        previous_experience_calls_retried_in_original_life=0, l2_into_l1=False,
        new_parent_calls=True, all_experience_source_masks_unchanged=True, prepared_unix=time.time()))
    print(json.dumps(dict(campaign=str(campaign), ready_sha256=common.sha(campaign / 'REPLICATE_READY.json'))))


def run(root, arm):
    common.validate(root)
    campaign = root / NAME
    ready = common.read(campaign / 'REPLICATE_READY.json')
    assert ready['runner_sha256'] == common.sha(Path(__file__)) and ready['cpu_tests_passed']
    assert ready['lifetime_sha256'] == common.sha(root / 'LIFETIME.json')
    assert ready['cohort_sha256'] == common.sha(campaign / 'COHORT.json')
    assert ready['lane_sha256'] == common.sha(Path(__file__).with_name('orch_math_pipeline_l2_lane.py'))
    driver = Path(__file__).with_name('orch_math_pipeline_l2_replicate_native.py')
    assert ready['native_driver_sha256'] == common.sha(driver)
    lifetime = common.read(root / 'LIFETIME.json')
    with (campaign / f'LANE_STARTED_{arm}.json').open('x') as stream:
        json.dump(dict(process=common.process_identity(Path('/proc') / str(os.getpid())),
            ready_sha256=common.sha(campaign / 'REPLICATE_READY.json'), started_unix=time.time()), stream)
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    child = identity = log = None
    state = 'FAILED'
    try:
        for cycle, phase in sequence():
            output = campaign / arm / f'cycle{cycle}' / phase
            assert not output.exists(), 'completed_or_partial_phase_never_rerun'
            lane_module().admit(root, arm, cycle, 'new_replicate_' + phase, lifetime['native_deadline_unix'])
            log = (campaign / f'{arm}_C{cycle}_{phase}.log').open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(driver), '--root', str(campaign),
                '--arm', arm, '--cycle', str(cycle), '--phase', phase], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=common.policy.DEVICES[arm][1],
                    PYTHONPATH=str(root / 'source'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false',
                    PYTHONDONTWRITEBYTECODE='1'), start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(campaign / f'LAUNCH_{arm}_C{cycle}_{phase}.json', dict(identity=identity,
                uuid=common.policy.DEVICES[arm][1], started_unix=time.time()))
            while child.poll() is None:
                assert time.time() < lifetime['hard_deadline_unix'] - 150, 'original_lifetime'
                time.sleep(2)
            assert child.returncode == 0, 'native_failure_this_lane_only'
            complete = common.read(output / 'COMPLETE.json')
            assert complete['status'] == 'COMPLETE'
            assert complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
            assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
            common.write(campaign / f'PROGRESS_{arm}.json', dict(cycle=cycle, phase=phase,
                complete_sha256=common.sha(output / 'COMPLETE.json'), observed_unix=time.time()))
            log.close()
            child = identity = log = None
        state = 'COMPLETE'
    except BaseException as error:
        common.write(campaign / f'FAILED_{arm}.json', dict(type=type(error).__name__, message=str(error), observed_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        common.write(campaign / f'TERMINAL_{arm}.json', dict(status=state, peer_processes_signalled=0, finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--arm', choices=ARMS)
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    else:
        assert options.arm
        run(options.root, options.arm)
