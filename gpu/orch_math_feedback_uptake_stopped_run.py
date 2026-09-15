"""One new guarded-reflection BASE cycle after the untouched R107 C2 boundary."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import gpu
import organism_v6

gpu.__path__.insert(0, str(Path(__file__).parent))
organism_v6.__path__.insert(0, str(Path(__file__).parents[1] / 'organism_v6'))

from gpu import orch_math_feedback_uptake_base_run as previous
from gpu import orch_math_pipeline_l2_run as common
from organism_v6 import orch_math_feedback_uptake_base as policy


CAMPAIGN = 'campaign_feedback_uptake_stopped_r107_5'


def predecessor(original):
    root = original / previous.CAMPAIGN
    terminal = common.read(root / 'TERMINAL.json')
    policy.require(terminal['status'] == 'COMPLETE', 'natural_c2_completion_required')
    bindings = {}
    for cycle in (1, 2):
        for phase in ('experience', 'readout'):
            output = root / f'cycle{cycle}' / phase
            complete, after = common.read(output / 'COMPLETE.json'), common.read(output / 'AFTER.json')
            policy.require(complete['status'] == 'COMPLETE' and after['actual_mounted_base_verified'], 'actual_predecessor_complete_after')
            policy.require(complete['process'] == after['process'] and complete['adapter'] is None and complete['optimizer'] is None, 'genuine_predecessor_base')
            policy.require(complete['base_sha256'] == policy.BASE_SHA and complete['training_updates'] == 0, 'same_frozen_base')
            policy.require(len(list(output.glob('CALL_*.json'))) == (6 if phase == 'experience' else 8), 'predecessor_denominators')
            for name in ('COMPLETE.json', 'AFTER.json'):
                bindings[str(output / name)] = common.sha(output / name)
    launch = common.read(root / 'LAUNCH_C2_readout.json')['identity']
    try:
        actual = common.process_identity(Path('/proc') / str(launch['pid']))
    except FileNotFoundError:
        actual = None
    policy.require(actual != launch, 'predecessor_native_must_exit')
    final = root / 'cycle2/experience'
    policy.require(common.sha(final / 'CARRY.json') == common.read(final / 'COMPLETE.json')['carry_sha256'], 'source_backed_context')
    for path in (root / 'READY.json', root / 'ACTIVATION.json', root / 'TERMINAL.json', final / 'CARRY.json'):
        bindings[str(path)] = common.sha(path)
    return dict(bindings=bindings, carry=common.read(final / 'CARRY.json'),
        predecessor_activation=common.read(root / 'ACTIVATION.json'), previous_native_calls=28,
        previous_parent_calls=4, contextual_continuation=True, no_weight_or_optimizer_reset=True)


def prepare(original):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    prepared = common.validate(original)
    handoff = predecessor(original)
    source = Path(__file__).parents[1]
    guard_receipt = common.read(source / 'PASTEUR_READY.json')
    policy.require(guard_receipt['source_sha256'] == common.sha(source / 'gpu/orch_reflection_repetition_stop.py'), 'pasteur_exact_source')
    policy.require(guard_receipt['test_sha256'] == common.sha(source / 'tests/test_orch_reflection_repetition_stop.py'), 'pasteur_exact_tests')
    tests = source / 'CPU_TESTS.log'
    policy.require('\nOK\n' in tests.read_text() and 'FAILED' not in tests.read_text(), 'node_cpu_tests_required')
    root = original / CAMPAIGN
    root.mkdir(exist_ok=False)
    paths = [original / 'COHORT.json', original.parent / 'orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json']
    paths.extend(original.glob('campaign_*/COHORT.json'))
    combined = original.parent / 'orch_combined_l1_continual_20260915_attempt1'
    paths.extend(path for path in (combined / 'COHORT.json', combined / 'CORPUS_MANIFEST.json') if path.exists())
    paths.extend(combined.glob('CORPORA/**/*.json'))
    identifiers, questions = previous.exclusions.exclusions([common.read(path) for path in sorted(set(paths))])
    policy.require(len(identifiers) >= 2856, 'complete_prior_registry')
    scopes = ('L1_ALL_SOURCE', 'L1_READOUT', 'L2_ALL_SOURCE', 'L2_READOUT', 'RETENTION')
    cohort = policy.history.make_cohort([dict(scope=scope, complete_pool=True, ids=sorted(identifiers),
        question_sha256=sorted(questions)) for scope in scopes])
    cohort['train'] = cohort['train'][:1]
    cohort['held'] = cohort['held'][:1]
    cohort.pop('retention')
    cohort['schema'] = 'ORCH_BASE_REFLECTION_STOP_CONTINUATION_V1'
    cohort['context_lineage_cycle'] = 3
    common.write(root / 'COHORT.json', cohort)
    common.write(root / 'EXCLUSIONS.json', dict(source_manifests={str(path): common.sha(path) for path in sorted(set(paths))},
        ids=len(identifiers), question_hashes=len(questions), outcomes_used_for_selection=False))
    common.write(root / 'HANDOFF.json', handoff)
    common.write(root / 'PREVIOUS_CARRY.json', handoff['carry'])
    common.write(root / 'BUDGET.json', dict(native_calls=14, parent_calls=2, cycles=1, episodes=2,
        reflections=2, checks=2, fresh_held=8, max_wall_seconds=1200, aggregate_native_cap=2106,
        aggregate_parent_cap=42, shared_original_gpu_hours_ceiling=24, native_retries=0,
        no_new_controls=True, frozen_base=True, weights_updated=False))
    tokenizer = previous.seam.native.source.native.load_local_tokenizer(prepared['model_dir'])
    prompt_lengths = [len(tokenizer.apply_chat_template(policy.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held',
        memory=handoff['carry']), tokenize=True, add_generation_prompt=True, return_dict=False))
        for group in cohort['train'] + cohort['held'] for task in group]
    policy.require(max(prompt_lengths) < policy.CONTEXT, 'actual_uncropped_tokenizer_check')
    base = previous.seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=previous.seam.BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.BASE_SHA, 'actual_base_files')
    (root / 'base_parent_queue_r107').mkdir()
    common.write(root / 'READY.json', dict(status='CPU_READY', source_files=previous.source_inventory(source),
        files={name: common.sha(root / name) for name in ('COHORT.json', 'EXCLUSIONS.json', 'HANDOFF.json', 'PREVIOUS_CARRY.json', 'BUDGET.json')},
        cpu_tests_sha256=common.sha(tests), pasteur_ready=guard_receipt,
        provider_files=common.read(source / 'PROVIDER_BINDINGS.json'), actual_prompt_lengths=prompt_lengths,
        base_verification=base, prepared_unix=time.time(), native_calls=0, parent_calls=0,
        allocation_native_delta=14, allocation_parent_delta=2, original_lifetime_sha256=common.sha(original / 'LIFETIME.json')))
    print(json.dumps(dict(root=str(root), ready_sha256=common.sha(root / 'READY.json'),
        cohort_sha256=common.sha(root / 'COHORT.json'), source_sha256=policy.digest(previous.source_inventory(source)))))


def guard(original, expected_ready):
    common.validate(original)
    root = original / CAMPAIGN
    policy.require(common.sha(root / 'READY.json') == expected_ready, 'ready_binding')
    ready = common.read(root / 'READY.json')
    publication = common.read(root / 'PUBLICATION.json')
    policy.require(publication['ready_sha256'] == expected_ready and publication['entry_sha256'] == common.sha(root / 'ALLOCATION.md'), 'published_exact_allocation')
    for path, digest in ready['source_files'].items():
        policy.require(common.sha(path) == digest, 'immutable_new_source')
    handoff = predecessor(original)
    policy.require(handoff == common.read(root / 'HANDOFF.json'), 'unchanged_natural_handoff')
    original_lifetime = common.read(original / 'LIFETIME.json')
    policy.require(common.sha(original / 'LIFETIME.json') == ready['original_lifetime_sha256'], 'original_lifetime_binding')
    started = time.time()
    old = handoff['predecessor_activation']
    activation = dict(started_unix=started, native_deadline_unix=min(started + 1020, old['native_deadline_unix'], original_lifetime['native_deadline_unix']),
        hard_deadline_unix=min(started + 1200, old['hard_deadline_unix'], original_lifetime['hard_deadline_unix']),
        ready_sha256=expected_ready, guardian=common.process_identity(Path('/proc') / str(os.getpid())),
        no_lifetime_reset=True, aggregate_native_cap=2106, aggregate_parent_cap=42)
    policy.require(started < activation['native_deadline_unix'], 'remaining_original_window')
    with (root / 'ACTIVATION.json').open('x') as stream:
        json.dump(activation, stream, indent=2)
    child = identity = log = None
    status = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for phase in ('experience', 'readout'):
            output = root / 'cycle1' / phase
            policy.require(not output.exists(), 'no_native_retry')
            previous.admit(original, root, 'C1_' + phase, activation['native_deadline_unix'])
            log = (root / ('C1_' + phase + '.log')).open('x')
            child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(original), '--native-phase', phase],
                cwd=original / 'source', start_new_session=True, stdout=log, stderr=subprocess.STDOUT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUID, PYTHONPATH=str(original / 'source'), HF_HUB_OFFLINE='1',
                    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1'))
            identity = common.process_identity(Path('/proc') / str(child.pid))
            common.write(root / ('LAUNCH_C1_' + phase + '.json'), dict(identity=identity, started_unix=time.time(), uuid=policy.UUID))
            while child.poll() is None:
                policy.require(time.time() < activation['hard_deadline_unix'] - 120, 'original_and_segment_hard_deadline')
                time.sleep(2)
            policy.require(child.returncode == 0, 'native_failure_no_retry')
            complete, after = common.read(output / 'COMPLETE.json'), common.read(output / 'AFTER.json')
            policy.require(complete['status'] == 'COMPLETE' and after['actual_mounted_base_verified'], 'actual_complete_after')
            policy.require(complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])], 'actual_process')
            policy.require(after['process'] == complete['process'], 'fresh_after_process')
            policy.require(len(list(output.glob('CALL_*.json'))) == (6 if phase == 'experience' else 8), 'all_denominators')
            common.write(root / ('COMPLETE_C1_' + phase + '.json'), dict(complete_sha256=common.sha(output / 'COMPLETE.json'),
                after_sha256=common.sha(output / 'AFTER.json'), observed_unix=time.time()))
            log.close()
            child = identity = log = None
        status = 'COMPLETE'
    except BaseException as error:
        common.write(root / 'GUARDIAN_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        common.write(root / 'TERMINAL.json', dict(status=status, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'guard', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--ready-sha256')
    parser.add_argument('--native-phase', choices=('experience', 'readout'))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'guard':
        guard(options.root, options.ready_sha256)
    else:
        from gpu import orch_math_feedback_uptake_stopped_native
        orch_math_feedback_uptake_stopped_native.run(options.root / CAMPAIGN, 1, options.native_phase)
