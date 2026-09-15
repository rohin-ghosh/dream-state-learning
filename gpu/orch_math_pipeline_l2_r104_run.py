"""Allocated training-wheels segment after old zero-write C2 parent timeout."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_math_pipeline_l2_run as common


CAMPAIGN = 'campaign_05_r104_training4'
CONFIG = dict(campaign=CAMPAIGN, physical=4, uuid='GPU-31583768-d90f-520c-51ed-5dac761526d0',
    parenting=dict(style='training-wheels', horizon='long', tone='supportive', strength='openai/openai/gpt-6-astra'))


def module(name):
    qualified = 'gpu.' + name
    specification = importlib.util.spec_from_file_location(qualified, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(specification)
    sys.modules[qualified] = result
    specification.loader.exec_module(result)
    return result


def source_bindings():
    return {name: common.sha(Path(__file__).with_name(name)) for name in (
        'orch_math_pipeline_l2_r104_run.py', 'orch_math_pipeline_l2_r104_native.py',
        'orch_math_pipeline_l2_r104_broker.py',
        'orch_math_pipeline_l2_r102_run.py', 'orch_math_pipeline_l2_r102_policy.py',
        'orch_math_pipeline_l2_lane.py', 'orch_math_pipeline_l2_guided_exit.py')}


def seed_binding(root):
    campaign, failure, predecessor = module('orch_math_pipeline_l2_guided_exit').binding(root)
    directory = campaign / 'GUIDED_SLEEP/cycle1/experience'
    assert common.sha(directory / 'optimizer.pt') == predecessor['optimizer_sha256']
    common.verify_saved(predecessor['output_adapter'])
    return campaign, directory, predecessor


def prepare(root):
    common.validate(root)
    seed_campaign, seed_directory, predecessor = seed_binding(root)
    policy = module('orch_math_pipeline_l2_r102_policy')
    prior = common.read(root / 'campaign_03_r102_micro5/COHORT.json')
    cohort = policy.make_cohort(prior)
    tests = root / 'R104_TRAINING4_CPU_TESTS.log'
    assert '\nOK\n' in tests.read_text()
    lifetime = common.read(root / 'LIFETIME.json')
    campaign = root / CAMPAIGN
    campaign.mkdir(exist_ok=False)
    (campaign / 'parent_queue').mkdir()
    rows = common.read(seed_directory / 'ROWS.json')
    rows = [dict(row, source_campaign=str(seed_campaign)) for row in rows]
    provenance = dict(campaign=str(seed_campaign), complete_path=str(seed_directory / 'COMPLETE.json'),
        complete_sha256=common.sha(seed_directory / 'COMPLETE.json'),
        rows_path=str(seed_directory / 'ROWS.json'), rows_sha256=common.sha(seed_directory / 'ROWS.json'),
        optimizer_path=str(seed_directory / 'optimizer.pt'), optimizer_sha256=predecessor['optimizer_sha256'],
        row_digests=[policy.digest(row) for row in rows], failed_c2_not_retried=True)
    common.write(campaign / 'COHORT.json', cohort)
    common.write(campaign / 'SEED_ROWS.json', rows)
    common.write(campaign / 'SEED_PROVENANCE.json', provenance)
    common.write(campaign / 'INITIAL.json', dict(output_adapter=predecessor['output_adapter'],
        process=predecessor['process'], cohort_sha256=common.sha(campaign / 'COHORT.json'),
        new_segment_saved_state_continuation=True, optimizer_reset=False, foundation_upgrade=False,
        source_receipt=dict(path=str(seed_directory / 'COMPLETE.json'), sha256=common.sha(seed_directory / 'COMPLETE.json'))))
    budget = root / 'R104_TRAINING4_PROSPECTIVE_BUDGET.json'
    assert not budget.exists()
    common.write(budget, dict(authority_commit='934a71f9', previous_native_cap=1920, previous_parent_cap=28,
        additional_native_cap=144, additional_parent_cap=8, aggregate_native_cap=2064, aggregate_parent_cap=36,
        train_per_cycle=2, reflections_per_cycle=2, held_per_cycle=8, cycles=8, terminal_retention=48,
        native_deadline_unix=lifetime['native_deadline_unix'], hard_deadline_unix=lifetime['hard_deadline_unix'],
        gpu_hours_ceiling=24, historical_counters_preserved=True, no_parent_retry=True, declared_unix=time.time()))
    common.write(campaign / 'R104_READY.json', dict(config=CONFIG, source_files=source_bindings(),
        files={name: common.sha(campaign / name) for name in ('COHORT.json', 'INITIAL.json', 'SEED_ROWS.json', 'SEED_PROVENANCE.json')},
        policy_sha256=common.sha(Path(policy.__file__)), budget_sha256=common.sha(budget),
        lifetime_sha256=common.sha(root / 'LIFETIME.json'), cpu_tests_passed=True,
        cpu_tests_sha256=common.sha(tests), old_mix_retained=True, no_new_controls=True, l2_into_l1=False,
        prepared_unix=time.time()))
    print(json.dumps(dict(campaign=str(campaign), ready_sha256=common.sha(campaign / 'R104_READY.json'))))


def validate(root, unused=None):
    common.validate(root)
    campaign = root / CAMPAIGN
    ready = common.read(campaign / 'R104_READY.json')
    assert ready['source_files'] == source_bindings() and ready['config'] == CONFIG and ready['cpu_tests_passed']
    assert all(common.sha(campaign / name) == digest for name, digest in ready['files'].items())
    assert common.sha(root / 'R104_TRAINING4_PROSPECTIVE_BUDGET.json') == ready['budget_sha256']
    assert common.sha(root / 'LIFETIME.json') == ready['lifetime_sha256']
    seed_binding(root)
    policy = module('orch_math_pipeline_l2_r102_policy')
    policy.VARIANTS['training4'] = CONFIG
    policy.configure('training4')
    return policy, campaign, ready


def native(root, cycle, phase):
    base = module('orch_math_pipeline_l2_r102_run')
    original_loader = base.load_module
    base.validate = validate
    base.load_module = lambda name: module('orch_math_pipeline_l2_r104_native') if name == 'orch_math_pipeline_l2_r102_native' else original_loader(name)
    base.native(root, 'training4', cycle, phase)


def release(root, lifetime):
    terminal = root / 'GUIDED4_FAILED_SLEEP_READOUT_TERMINAL.json'
    while not terminal.exists():
        assert time.time() < lifetime['native_deadline_unix'], 'no_new_lifetime'
        time.sleep(2)
    assert common.read(terminal)['status'] == 'COMPLETE'
    output = root / 'campaign_02_recovery_paired/GUIDED_SLEEP/cycle2/readout'
    assert common.read(output / 'COMPLETE.json')['status'] == 'COMPLETE'
    assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
    assert common.sha(output / 'COMPLETE.json') == common.read(terminal)['complete_sha256']
    report = module('orch_math_pipeline_l2_lane').admit(root, 'GUIDED_SLEEP', 0,
        'r104_previous_phase_strict_release', lifetime['native_deadline_unix'])
    common.write(root / 'R104_TRAINING4_PRIOR_RELEASE.json', dict(complete_sha256=common.sha(output / 'COMPLETE.json'),
        after_sha256=common.sha(output / 'AFTER.json'), fresh_full_admission=report,
        next_owner='SAME_OWNER_TRAINING4_CONTINUATION', released_unix=time.time()))


def run(root):
    policy, campaign, ready = validate(root)
    lifetime = common.read(root / 'LIFETIME.json')
    with (campaign / 'LANE_STARTED.json').open('x') as stream:
        json.dump(dict(identity=common.process_identity(Path('/proc') / str(os.getpid())),
            ready_sha256=common.sha(campaign / 'R104_READY.json'), started_unix=time.time()), stream)
    release(root, lifetime)
    child = identity = log = None
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    base = module('orch_math_pipeline_l2_r102_run')
    try:
        for cycle, phase in base.sequence():
            output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
            assert not output.exists(), 'never_repeat_completed_or_partial_phase'
            module('orch_math_pipeline_l2_lane').admit(root, 'GUIDED_SLEEP', cycle,
                'r104_' + phase, lifetime['native_deadline_unix'])
            log = (campaign / f'C{cycle}_{phase}.log').open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(root),
                '--cycle', str(cycle), '--native-phase', phase], cwd=root / 'source',
                env=dict(os.environ, PYTHONPATH=str(root / 'source'), CUDA_VISIBLE_DEVICES=CONFIG['uuid'],
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    TOKENIZERS_PARALLELISM='false'), start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(campaign / f'LAUNCH_C{cycle}_{phase}.json', dict(identity=identity,
                uuid=CONFIG['uuid'], started_unix=time.time()))
            while child.poll() is None:
                assert time.time() < lifetime['hard_deadline_unix'] - 150
                time.sleep(2)
            if (output / 'REQUEST.json').exists():
                base.phase_reduction(campaign, cycle, phase)
            assert child.returncode == 0, 'native_failure_lane_only_no_retry'
            complete = common.read(output / 'COMPLETE.json')
            assert complete['status'] == 'COMPLETE'
            assert complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
            assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
            common.write(campaign / 'PROGRESS.json', dict(cycle=cycle, phase=phase,
                complete_sha256=common.sha(output / 'COMPLETE.json'), observed_unix=time.time()))
            log.close()
            child = identity = log = None
        common.write(campaign / 'LANE_TERMINAL.json', dict(status='COMPLETE', finished_unix=time.time()))
    except BaseException as error:
        common.write(campaign / 'LANE_FAILED.json', dict(type=type(error).__name__, message=str(error), observed_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--native-phase', choices=('experience', 'readout'))
    options = parser.parse_args()
    if options.phase == 'native':
        native(options.root, options.cycle, options.native_phase)
    else:
        (prepare if options.phase == 'prepare' else run)(options.root)
