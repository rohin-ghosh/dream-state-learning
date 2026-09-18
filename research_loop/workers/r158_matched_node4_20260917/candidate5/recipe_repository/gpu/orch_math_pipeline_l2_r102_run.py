"""Two new strong-parent treatment lineages within the original wallclock lease."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from gpu import orch_math_pipeline_l2_run as common


def load_module(name):
    qualified = 'gpu.' + name
    specification = importlib.util.spec_from_file_location(qualified, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(specification)
    sys.modules[qualified] = module
    specification.loader.exec_module(module)
    return module


def sequence():
    return [(cycle, phase) for cycle in range(1, 9) for phase in ('experience', 'readout')]


def phase_reduction(campaign, cycle, phase):
    output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
    request = common.read(output / 'REQUEST.json')
    complete = common.read(output / 'COMPLETE.json') if (output / 'COMPLETE.json').exists() else None
    failure = common.read(output / 'FAILED.json') if (output / 'FAILED.json').exists() else None
    calls = [(path, common.read(path)) for path in sorted(output.glob('CALL_*.json'))]
    finished = (complete or failure or {}).get('finished_unix', time.time())
    metrics = []
    for path, call in calls:
        response = call.get('response', {})
        words = response.get('raw', '').split()
        grams = [tuple(words[index:index + 4]) for index in range(max(0, len(words) - 3))]
        metrics.append(dict(path=str(path.relative_to(campaign)), sha256=common.sha(path), task_id=call['task_id'],
            purpose=call['purpose'], response_present='response' in call,
            emitted_tokens=len(response.get('token_ids', [])), private_thinking_tokens='NOT_OBSERVABLE',
            approaches='AUTHOR_REVIEW_PENDING', rejections='AUTHOR_REVIEW_PENDING', coherence='AUTHOR_REVIEW_PENDING',
            repeated_fourgram_fraction=1 - len(set(grams)) / len(grams) if grams else 0,
            repetition_is_lexical_proxy_not_semantic_admission=True,
            generation_seconds=call.get('finished_unix', finished) - call['started_unix']))
    queue = campaign / 'parent_queue' / f'GUIDED_SLEEP_C{cycle}.request.json'
    response_path = queue.with_name(f'GUIDED_SLEEP_C{cycle}.response.json')
    reflections = [call for unused, call in calls if call['purpose'] == 'reflection']
    summary = dict(cycle=cycle, phase=phase, status='COMPLETE' if complete else 'FAILED_OR_PARTIAL',
        thinking_trajectory_primary=True, semantic_admission=False, ancillary_outcomes=(complete or {}).get('successes'),
        call_count=len(calls), observed_responses=sum(item['response_present'] for item in metrics), metrics=metrics,
        phase_elapsed_seconds=finished - request['started_unix'],
        parent_queue_seconds=response_path.stat().st_mtime - queue.stat().st_mtime if response_path.exists() and queue.exists() else None,
        pure_provider_compute_seconds='UNKNOWN',
        sleep_envelope_seconds=finished - min(call['started_unix'] for call in reflections) if reflections else None,
        held_size=8 if phase == 'readout' else 0, retention_slots=48 if phase == 'readout' and cycle == 8 else 0,
        legacy_readout_size=56, source_failure=(failure or {}).get('message'), parent_may_read=False)
    common.write(campaign / f'C{cycle}_{phase}_REDUCTION.json', summary)
    if cycle > 1 and phase == 'experience':
        previous = campaign / 'GUIDED_SLEEP' / f'cycle{cycle - 1}/experience'
        source_rows = common.read(previous / 'ROWS.json')
        common.write(campaign / f'AUTHOR_TAUGHT_NEXT_C{cycle - 1}_C{cycle}.json', dict(
            prior_plan_sha256=common.sha(previous / 'PARENT_PLAN.json'),
            prior_reflection_sources=[dict(episode_id=row['episode_id'], source_call_path=row['source_call_path'],
                source_call_sha256=row['source_call_sha256']) for row in source_rows if row['kind'] == 'past_reflection'],
            next_original_sources=[item for item in metrics if item['purpose'] == 'experience'],
            next_original_parent_free=all(call['prior_updates'] == 0 for unused, call in calls if call['purpose'] == 'experience'),
            expected_next_episodes=2, uptake='AUTHOR_REVIEW_PENDING_NOT_INFERRED_FROM_OUTCOME',
            general_trajectory_join_not_necessarily_same_family=True, parent_may_read=False, extra_native_calls=0))


def source_bindings():
    return {name: common.sha(Path(__file__).with_name(name)) for name in (
        'orch_math_pipeline_l2_r102_run.py', 'orch_math_pipeline_l2_r102_policy.py',
        'orch_math_pipeline_l2_r102_native.py', 'orch_math_pipeline_l2_lane.py')}


def validate_release(root, variant):
    predecessor_arm = 'UNPARENTED_SLEEP' if variant == 'micro5' else 'FROZEN'
    path = root / f'ROHIN100_CONTROL_RELEASE_{predecessor_arm}.json'
    release = common.read(path)
    config = load_module('orch_math_pipeline_l2_r102_policy').VARIANTS[variant]
    assert release['released'] and release['physical_index'] == config['physical'] and release['uuid'] == config['uuid']
    report = release['fresh_full_admission']
    assert report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
    output = Path(release['completed_readout'])
    assert common.sha(output / 'COMPLETE.json') == release['complete_sha256']
    assert common.sha(output / 'AFTER.json') == release['after_sha256']
    assert common.read(output / 'COMPLETE.json')['status'] == 'COMPLETE'
    assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
    return dict(path=str(path), sha256=common.sha(path), released_unix=release['released_unix'])


def prepare(root):
    prepared = common.validate(root)
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    policy = load_module('orch_math_pipeline_l2_r102_policy')
    initial_path = root / 'campaign_01_existing_rich/INITIAL.json'
    initial = common.read(initial_path)
    saved = common.verify_saved(initial['output_adapter'])
    assert saved.state_sha256 == common.INITIAL_SHA
    cohort = policy.make_cohort(common.read(root / 'COHORT.json'))
    tests = root / 'R102_CPU_TESTS.log'
    assert '\nOK\n' in tests.read_text()
    budget_path = root / 'R102_PROSPECTIVE_BUDGET.json'
    assert not budget_path.exists()
    lifetime = common.read(root / 'LIFETIME.json')
    common.write(budget_path, dict(authority_commit='7946df80', supersedes_queued_commit='20566b3e',
        historical_native_cap=1632, additional_native_cap=288, aggregate_native_cap=1920,
        historical_parent_cap=12, additional_parent_cap=16, aggregate_parent_cap=28,
        native_per_new_lineage=144, parent_plans_per_new_lineage=8, cycles=8,
        train_per_cycle=2, reflections_per_cycle=2, held_per_cycle=8,
        terminal_retention=48, no_c0_calls=True, no_batching=True, no_counter_reset=True,
        original_lifetime_sha256=common.sha(root / 'LIFETIME.json'),
        native_deadline_unix=lifetime['native_deadline_unix'], hard_deadline_unix=lifetime['hard_deadline_unix'],
        gpu_hours_ceiling=24, existing_lives_unchanged=True, frozen_source_sha256=prepared['source_sha256'],
        new_source_files=source_bindings(), declared_unix=time.time()))
    for variant, config in policy.VARIANTS.items():
        campaign = root / config['campaign']
        campaign.mkdir(exist_ok=False)
        common.write(campaign / 'COHORT.json', cohort)
        common.write(campaign / 'INITIAL.json', dict(output_adapter=saved.document(), process=initial['process'],
            source_receipt=dict(path=str(initial_path), sha256=common.sha(initial_path)),
            cohort_sha256=common.sha(campaign / 'COHORT.json'), same_genuine_initial_child=True,
            lineage_kind='STRONG_PARENT_TREATMENT', no_previous_life_continuity_claim=True, foundation_upgrade=False))
        (campaign / 'parent_queue').mkdir()
        common.write(campaign / 'R102_READY.json', dict(schema='MATH_R102_STRONG_TREATMENT_V1',
            variant=variant, config=config, source_files=source_bindings(),
            cohort_sha256=common.sha(campaign / 'COHORT.json'), initial_sha256=common.sha(campaign / 'INITIAL.json'),
            budget_sha256=common.sha(budget_path), lifetime_sha256=common.sha(root / 'LIFETIME.json'),
            cpu_tests_passed=True, cpu_tests_sha256=common.sha(tests), release=validate_release(root, variant),
            thinking_trajectory_primary=True, outcome_based_retirement=False, shared_route_baseline_descriptive_only=True,
            no_style_matched_math_control_claim=True, all_experience_source_masks_preserved=True, l2_into_l1=False,
            prepared_unix=time.time()))
        print(json.dumps(dict(variant=variant, root=str(campaign), ready_sha256=common.sha(campaign / 'R102_READY.json'))))


def validate(root, variant):
    common.validate(root)
    policy = load_module('orch_math_pipeline_l2_r102_policy')
    campaign = root / policy.VARIANTS[variant]['campaign']
    ready = common.read(campaign / 'R102_READY.json')
    assert ready['source_files'] == source_bindings() and ready['cpu_tests_passed']
    assert ready['budget_sha256'] == common.sha(root / 'R102_PROSPECTIVE_BUDGET.json')
    assert ready['lifetime_sha256'] == common.sha(root / 'LIFETIME.json')
    assert ready['cohort_sha256'] == common.sha(campaign / 'COHORT.json')
    assert ready['initial_sha256'] == common.sha(campaign / 'INITIAL.json')
    policy.configure(variant)
    return policy, campaign, ready


def native(root, variant, cycle, phase):
    policy, campaign, ready = validate(root, variant)
    driver = load_module('orch_math_pipeline_l2_r102_native')
    driver.policy = policy
    captured = {}
    load_training = driver.native.load_training
    def capture(*args, **kwargs):
        loaded = load_training(*args, **kwargs)
        captured['loaded'] = loaded
        return loaded
    driver.native.load_training = capture
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        driver.run(campaign, 'GUIDED_SLEEP', cycle, phase)
    except BaseException:
        loaded = captured.get('loaded')
        output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
        if loaded is not None and (output / 'LOSSES.jsonl').exists():
            updates = len((output / 'LOSSES.jsonl').read_text().splitlines())
            if updates:
                engine = loaded.engine
                engine.verify_base()
                parameters = {name: value for name, value in engine.model.named_parameters() if driver.native.is_lora(name)}
                destination = output / 'failed_partial_adapter'
                engine.model.save_pretrained(destination, safe_serialization=True, save_embedding_layers=False)
                saved = driver.bridge.AdapterIdentity(str(destination), driver.native.state_hash(parameters),
                    loaded.observed.base_sha256, tuple((path.name, common.sha(path)) for path in sorted(destination.iterdir()) if path.is_file())).verify()
                assert driver.native.observe_adapter(engine, saved) == saved
                engine.torch.save(loaded.optimizer.state_dict(), output / 'failed_partial_optimizer.pt')
                common.write(output / 'FAILED_PARTIAL_SAVED.json', dict(status='FAILED_NOT_COMPLETE_NOT_AUTO_RESUMED',
                    output_adapter=saved.document(), updates=updates, actual_mounted_identity_verified=True,
                    optimizer_sha256=common.sha(output / 'failed_partial_optimizer.pt'), process=loaded.process))
        raise


def run(root, variant):
    policy, campaign, ready = validate(root, variant)
    lifetime = common.read(root / 'LIFETIME.json')
    config = policy.VARIANTS[variant]
    with (campaign / 'LANE_STARTED.json').open('x') as stream:
        json.dump(dict(identity=common.process_identity(Path('/proc') / str(os.getpid())),
            ready_sha256=common.sha(campaign / 'R102_READY.json'), started_unix=time.time()), stream)
    validate_release(root, variant)
    admission_arm = 'UNPARENTED_SLEEP' if variant == 'micro5' else 'FROZEN'
    child = identity = log = None
    state = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle, phase in sequence():
            output = campaign / 'GUIDED_SLEEP' / f'cycle{cycle}' / phase
            assert not output.exists(), 'completed_or_partial_phase_never_retried'
            load_module('orch_math_pipeline_l2_lane').admit(root, admission_arm, cycle, 'r102_' + phase, lifetime['native_deadline_unix'])
            log = (campaign / f'C{cycle}_{phase}.log').open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(root),
                '--variant', variant, '--cycle', str(cycle), '--native-phase', phase], cwd=root / 'source',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=config['uuid'], PYTHONPATH=str(root / 'source'),
                    HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                    TOKENIZERS_PARALLELISM='false'), start_new_session=True, stdout=log, stderr=subprocess.STDOUT)
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(campaign / f'LAUNCH_C{cycle}_{phase}.json', dict(identity=identity, uuid=config['uuid'], started_unix=time.time()))
            while child.poll() is None:
                assert time.time() < lifetime['hard_deadline_unix'] - 150
                time.sleep(2)
            if (output / 'REQUEST.json').exists():
                phase_reduction(campaign, cycle, phase)
            assert child.returncode == 0, 'native_failure_lane_only_no_quality_waiver'
            complete = common.read(output / 'COMPLETE.json')
            assert complete['status'] == 'COMPLETE'
            assert complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])]
            assert common.read(output / 'AFTER.json')['actual_mounted_identity_verified']
            common.write(campaign / 'PROGRESS.json', dict(cycle=cycle, phase=phase,
                complete_sha256=common.sha(output / 'COMPLETE.json'), observed_unix=time.time()))
            log.close()
            child = identity = log = None
        state = 'COMPLETE'
    except BaseException as error:
        common.write(campaign / 'LANE_FAILED.json', dict(type=type(error).__name__, message=str(error), observed_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        common.write(campaign / 'LANE_TERMINAL.json', dict(status=state, peer_processes_signalled=0, finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'run', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--variant', choices=('micro5', 'creative7'))
    parser.add_argument('--cycle', type=int)
    parser.add_argument('--native-phase', choices=('experience', 'readout'))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'run':
        run(options.root, options.variant)
    else:
        native(options.root, options.variant, options.cycle, options.native_phase)
