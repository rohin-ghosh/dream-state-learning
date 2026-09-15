"""R107 CPU prepare and once-only strict guardian; original campaign files untouched."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import gpu
import organism_v6

gpu.__path__.insert(0, str(Path(__file__).parent))
organism_v6.__path__.insert(0, str(Path(__file__).parents[1] / 'organism_v6'))

from gpu import orch_math_pipeline_l2_run as common
from gpu import orch_math_pipeline_l2_r104_native as seam
from organism_v6 import orch_l1_bootstrap_transfer as exclusions
from organism_v6 import orch_math_feedback_uptake_base as policy


CAMPAIGN = 'campaign_feedback_uptake_base_r107_5'


def natural_completion(original):
    campaign = original / 'campaign_03_r102_micro5'
    terminal = common.read(campaign / 'LANE_TERMINAL.json')
    policy.require(terminal['status'] == 'COMPLETE', 'natural_micro_completion_required')
    identities = [common.read(campaign / 'LANE_STARTED.json')['identity'],
        common.read(campaign / 'LAUNCH_C8_readout.json')['identity']]
    for identity in identities:
        try:
            current = common.process_identity(Path('/proc') / str(identity['pid']))
        except FileNotFoundError:
            current = None
        policy.require(current != identity, 'predecessor_process_still_alive')
    readout = campaign / 'GUIDED_SLEEP/cycle8/readout'
    complete, after = common.read(readout / 'COMPLETE.json'), common.read(readout / 'AFTER.json')
    policy.require(complete['status'] == 'COMPLETE' and after['actual_mounted_identity_verified'] and after['frozen_base_verified'], 'predecessor_test_and_after')
    policy.require(complete['output_adapter'] == after['output_adapter'] and terminal['finished_unix'] >= after['finished_unix'], 'predecessor_after_join')
    policy.require(len(list(readout.glob('CALL_*.json'))) == 56, 'predecessor_full_bounded_readout')
    return dict(terminal_path=str(campaign / 'LANE_TERMINAL.json'), terminal_sha256=common.sha(campaign / 'LANE_TERMINAL.json'),
        complete_path=str(readout / 'COMPLETE.json'), complete_sha256=common.sha(readout / 'COMPLETE.json'),
        after_path=str(readout / 'AFTER.json'), after_sha256=common.sha(readout / 'AFTER.json'), identities=identities)


def source_inventory(directory):
    return {str(path): common.sha(path) for path in sorted(directory.rglob('*.py'))}


def prepare(original):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_prepare_only')
    prepared = common.validate(original)
    release = natural_completion(original)
    root = original / CAMPAIGN
    root.mkdir(exist_ok=False)
    documents, bindings = [], {}
    paths = [original / 'COHORT.json', original.parent / 'orch_l1_bootstrap_transfer_20260915_attempt1/COHORT.json']
    paths.extend(original.glob('campaign_*/COHORT.json'))
    combined = original.parent / 'orch_combined_l1_continual_20260915_attempt1'
    paths.extend(path for path in [combined / 'COHORT.json', combined / 'CORPUS_MANIFEST.json'] if path.exists())
    paths.extend(combined.glob('CORPORA/**/*.json'))
    for path in sorted(set(paths)):
        documents.append(common.read(path))
        bindings[str(path)] = common.sha(path)
    identifiers, questions = exclusions.exclusions(documents)
    policy.require(len(identifiers) >= 2640 and len(questions) >= 2632, 'prior_full_source_registry')
    scopes = ('L1_ALL_SOURCE', 'L1_READOUT', 'L2_ALL_SOURCE', 'L2_READOUT', 'RETENTION')
    manifests = [dict(scope=scope, complete_pool=True, ids=sorted(identifiers), question_sha256=sorted(questions)) for scope in scopes]
    cohort = policy.history.make_cohort(manifests)
    cohort['schema'] = policy.SCHEMA
    cohort.pop('retention')
    common.write(root / 'COHORT.json', cohort)
    common.write(root / 'EXCLUSIONS.json', dict(source_manifests=bindings, excluded_ids=len(identifiers),
        excluded_questions=len(questions), scope='union_of_registered_source_pools_and_complete_campaign_cohorts', outcomes_used_for_selection=False))
    common.write(root / 'PREDECESSOR.json', release)
    common.write(root / 'BUDGET.json', policy.budget())
    tokenizer = seam.native.source.native.load_local_tokenizer(prepared['model_dir'])
    lengths = [len(tokenizer.apply_chat_template(policy.messages(task, purpose='experience' if task['split'] == 'TRAIN' else 'held'),
        tokenize=True, add_generation_prompt=True, return_dict=False)) for group in cohort['train'] + cohort['held'] for task in group]
    policy.require(max(lengths) < 2048, 'actual_native_tokenizer_cpu_gate')
    base = seam.portable.verify_base_files(prepared['bundle'], prepared['model_dir'], expected_manifest_sha256=seam.BUNDLE_SHA)
    policy.require(base['expected_base_sha256'] == policy.BASE_SHA, 'actual_base_binding')
    tests = Path(__file__).parents[1] / 'CPU_TESTS.log'
    policy.require('\nOK\n' in tests.read_text(), 'bound_cpu_tests_required')
    (root / 'base_parent_queue_r107').mkdir()
    common.write(root / 'READY.json', dict(status='CPU_READY_NO_MODEL', schema=policy.SCHEMA,
        source_files=source_inventory(Path(__file__).parents[1]), files={name: common.sha(root / name) for name in
            ('COHORT.json', 'EXCLUSIONS.json', 'PREDECESSOR.json', 'BUDGET.json')},
        cpu_tests_sha256=common.sha(tests), actual_tokenizer_prompt_lengths=lengths, base_verification=base,
        provider_files=common.read(Path(__file__).parents[1] / 'PROVIDER_BINDINGS.json'),
        adapter=None, optimizer=None, training_updates=0, parent_model=policy.STRONG,
        frozen_base_sha256=policy.BASE_SHA, original_lifetime_sha256=common.sha(original / 'LIFETIME.json'),
        device=dict(physical=policy.PHYSICAL, uuid=policy.UUID), old_sources_unchanged=True,
        prepared_unix=time.time(), native_calls=0, parent_calls=0))
    print(json.dumps(dict(root=str(root), ready_sha256=common.sha(root / 'READY.json'),
        cohort_sha256=common.sha(root / 'COHORT.json'), native_calls=0, parent_calls=0)))


def admit(original, root, label, deadline):
    until = min(time.time() + 180, deadline)
    attempt = 0
    while time.time() < until:
        try:
            report = common.scan(policy.PHYSICAL, original / 'SERVICE_IDENTITY.json')
            common.write(root / f'ADMISSION_{label}_{attempt}.json', report)
            policy.require(report['gpu']['uuid'] == policy.UUID and report['gpu']['index'] == policy.PHYSICAL, 'pinned_uuid')
            policy.require(report['host_sha256'] == policy.history.source.HOST_SHA and 'device_minor' in report, 'full_host_minor_scan')
            if report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']:
                return report
        except subprocess.CalledProcessError as error:
            common.write(root / f'ADMISSION_ERROR_{label}_{attempt}.json', dict(error=str(error), stderr=error.stderr, no_waiver=True))
        attempt += 1
        time.sleep(2)
    raise TimeoutError('strict_admission_blocked_no_peer_kill')


def guard(original, expected_ready):
    common.validate(original)
    root = original / CAMPAIGN
    policy.require(common.sha(root / 'READY.json') == expected_ready, 'ready_binding')
    publication = common.read(root / 'PUBLICATION.json')
    policy.require(publication['ready_sha256'] == expected_ready and publication['board_entry_sha256'] == publication['coordination_entry_sha256'], 'exact_posted_allocation')
    natural_completion(original)
    ready = common.read(root / 'READY.json')
    for name, digest in ready['source_files'].items():
        policy.require(common.sha(name) == digest, 'immutable_source')
    lifetime = common.read(original / 'LIFETIME.json')
    started = time.time()
    activation = dict(started_unix=started, native_deadline_unix=min(started + policy.WALL_SECONDS - 180, lifetime['native_deadline_unix']),
        hard_deadline_unix=min(started + policy.WALL_SECONDS, lifetime['hard_deadline_unix']),
        ready_sha256=expected_ready, budget=policy.budget(), no_existing_counter_reset=True)
    with (root / 'ACTIVATION.json').open('x') as stream:
        json.dump(activation, stream, indent=2)
    child = identity = log = None
    state = 'FAILED'
    def interrupted(signum, frame):
        raise SystemExit(signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for cycle in range(1, 3):
            for phase in ('experience', 'readout'):
                output = root / f'cycle{cycle}' / phase
                policy.require(not output.exists(), 'phase_never_retried')
                admit(original, root, f'C{cycle}_{phase}', activation['native_deadline_unix'])
                log = (root / f'C{cycle}_{phase}.log').open('x')
                child = subprocess.Popen([common.PYTHON, '-B', str(Path(__file__)), 'native', '--root', str(original),
                    '--cycle', str(cycle), '--native-phase', phase], cwd=original / 'source', start_new_session=True,
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES=policy.UUID, PYTHONPATH=str(original / 'source'), HF_HUB_OFFLINE='1',
                        TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'), stdout=log, stderr=subprocess.STDOUT)
                identity = common.process_identity(Path('/proc') / str(child.pid))
                common.write(root / f'LAUNCH_C{cycle}_{phase}.json', dict(identity=identity, uuid=policy.UUID, started_unix=time.time()))
                while child.poll() is None:
                    policy.require(time.time() < activation['hard_deadline_unix'] - 120, 'bounded_native_guardian')
                    time.sleep(2)
                policy.require(child.returncode == 0, 'native_phase_failure_no_retry')
                complete = common.read(output / 'COMPLETE.json')
                policy.require(complete['status'] == 'COMPLETE' and complete['process'] == [identity['boot_id'], identity['pid'], int(identity['start_ticks'])], 'actual_phase_process')
                policy.require(common.read(output / 'AFTER.json')['actual_mounted_base_verified'], 'fresh_after_base')
                common.write(root / 'PROGRESS.json', dict(cycle=cycle, phase=phase, complete_sha256=common.sha(output / 'COMPLETE.json'), observed_unix=time.time()))
                log.close()
                log = child = identity = None
        state = 'COMPLETE'
    except BaseException as error:
        common.write(root / 'GUARDIAN_FAILED.json', dict(type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if child is not None:
            common.stop_owned(child, identity)
        if log is not None:
            log.close()
        common.write(root / 'TERMINAL.json', dict(status=state, finished_unix=time.time(), peer_processes_signalled=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'guard', 'native'))
    parser.add_argument('--root', type=Path, default=common.ROOT)
    parser.add_argument('--ready-sha256')
    parser.add_argument('--cycle', type=int, choices=(1, 2))
    parser.add_argument('--native-phase', choices=('experience', 'readout'))
    options = parser.parse_args()
    if options.phase == 'prepare':
        prepare(options.root)
    elif options.phase == 'guard':
        guard(options.root, options.ready_sha256)
    else:
        from gpu import orch_math_feedback_uptake_base_native
        orch_math_feedback_uptake_base_native.run(options.root / CAMPAIGN, options.cycle, options.native_phase)
