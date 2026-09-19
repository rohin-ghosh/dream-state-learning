"""Explicit two-cycle reviewed learner driver; prospective staging never admits execution."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import os
from pathlib import Path
import signal
import sys
import time

from gpu import orch_r164_guided_cycle as cycle


fit, capture, gym = cycle.fit, cycle.capture, cycle.gym
require = fit.require
SCHEMA = 'R165_GUIDED_DRIVER_V1'
ROOT = Path(__file__).resolve().parents[1]
CANDIDATE5 = ROOT/'research_loop/workers/r158_matched_node4_20260917'


def reference(path):
    path = capture.canonical(path)
    raw = capture.Reader(capture.Limits()).read(path)[0]
    return dict(path=str(path), sha256=capture.sha(raw))


def bound(reference_value):
    return capture.decode(fit._ref(capture.Reader(capture.Limits()), reference_value))


def write(path, value):
    path = capture.canonical(path)
    with gym.console._directory(path.parent) as descriptor:
        gym.console._stage(descriptor, path.name, capture.encoded(value))
        os.fsync(descriptor)
    return reference(path)


def prospect(output, *, cohort_root, source_root, candidate5=CANDIDATE5):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'prospect_CPU_only_environment')
    output, cohort_root, source_root = map(capture.canonical, (output, cohort_root, source_root))
    require(cohort_root.name.startswith('orch_r158_'), 'new_R158_labelled_cohort')
    plans = {arm: bound(reference(Path(candidate5)/'candidate5_inputs'/f'{arm}.PLAN.json')) for arm in cycle.ARMS}
    initialized_path = Path(candidate5)/'candidate5_initializer_attempt1/common_initial/INITIALIZED.json'
    metadata_path = Path(candidate5)/'candidate5_initializer_attempt1/operator_metadata/INITIAL_METADATA.json'
    initialized, metadata = bound(reference(initialized_path)), bound(reference(metadata_path))
    require(initialized['checkpoint_commit_sha256'] == metadata['commit_sha256']
            and metadata['saved_optimizer_steps'] == initialized['observed_initial_state']['optimizer_steps'] == 0,
            'candidate5_saved_zero_update_initializer_metadata_join')
    old_roots = [plan['root'] for plan in plans.values()]
    require(all(not cohort_root.is_relative_to(Path(root)) and not Path(root).is_relative_to(cohort_root)
                for root in old_roots), 'never_reuse_candidate5_life_roots')
    require(all(not output.is_relative_to(Path(root)) for root in old_roots), 'prospect_not_in_raw_life')
    initial_parent = Path(plans['parented_learning']['root']).parent/'common_initial'
    initializer = dict(path=str(initial_parent/'COMMIT.json'), sha256=metadata['commit_sha256'])
    adapter_bytes = sum(part['bytes'] for item in metadata['adapter_headers'].values() for part in item['dtypes'].values())
    blockers = ['R163_REAL_7B_PARITY_AND_MAIN_GO_REQUIRED', 'MAIN_NATIVE_EXECUTOR_INITIALIZER_FINGERPRINTS_REQUIRED',
                'PINNED_PREENCODED_TRAIN_ANCHORS_REQUIRED', 'FULL_RUNTIME_SOURCE_AND_TOKENIZER_PINS_REQUIRED',
                'FRESH_EXTERNAL_ALLOCATION_CONFINEMENT_AND_LEASE_ADMISSION_REQUIRED',
                'MAIN_GENERATOR_AUTHORITY_AND_TASK_EXCLUSIONS_REQUIRED']
    if adapter_bytes > 64*1024**2:
        blockers.append('CANDIDATE5_ADAPTER_EXCEEDS_R159_HARD_64_MIB_READ_LIMIT')
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    references = {}
    for arm, original in plans.items():
        plan = deepcopy(original)
        plan.update(root=str(cohort_root/arm), source_root=str(source_root), hard_end_unix=None,
                    lease_end_unix=None, physical=None, gpu_uuid=None, max_sleeps=2)
        for name in ('initialization_source', 'initialization_validation_schema', 'authorized_wall_extension'):
            plan.pop(name, None)
        plan['matched_cohort'] = dict(path=str(output/'PROSPECT.json'), sha256=None)
        if plan.get('startup_context'):
            relative = Path(original['startup_context']['path']).relative_to(original['source_root'])
            plan['startup_context']['path'] = str(source_root/relative)
        policy = dict(schema=fit.SCHEMA, contract=fit.CONTRACT, evidence_mode=fit.DYNAMIC,
            fork_root=plan['root'], fork_label='R165_TWO_CYCLE_'+arm.upper(), protected_roots=old_roots,
            mode='frozen' if arm == 'parented_frozen' else 'learning', execution_kind='EXTERNALLY_VALIDATED_EXECUTOR',
            context_limit=plan['context_limit'], allow_off_policy_new=False,
            fit_limits=asdict(fit.Limits()), reader_limits=asdict(capture.Limits()),
            initializer=dict(commit=initializer, state=None), source_pins=None, tokenizer_pins=None,
            tokenizer_class=None, executor_class=fit.NATIVE_EXECUTOR_CLASS, tokenizer_sha256=None,
            anchors_sha256=None, generator_binding=None, excluded_task_ids=None, executor_validation=None)
        plan_ref = write(output/f'{arm}.DRAFT_PLAN.json', plan)
        policy_ref = write(output/f'{arm}.DRAFT_AUTHORITY.json', policy)
        curriculum = dict(schema=cycle.SCHEMA, authority_sha256=None, plan=plan_ref,
            capture_root=str(cohort_root.parent/(cohort_root.name+'_captures')/arm), hard_end_unix=None,
            max_output_bytes=32*1024**2,
            tasks=[dict(task_index=index, guidance=None if arm == 'unparented_learning' else dict(speaker='Astra',
                text='Investigate this training puzzle in your own words. Try a checkable answer, inspect the actual '
                     'Tool feedback, and explain what it supports and what remains uncertain. Do not invent a result.'))
                for index in (0, 1)],
            capture_specs=[dict(response='answer', target_kind='ANSWER', label='grounded_reasoning', feedback=False),
                           dict(response='followup', target_kind='POST_FEEDBACK_REFLECTION', label='grounded_reasoning', feedback=False)])
        curriculum_ref = write(output/f'{arm}.DRAFT_CURRICULUM.json', curriculum)
        config = dict(schema=SCHEMA, status='BLOCKED_PROSPECTIVE_NOT_ADMITTED', plan=plan_ref,
            authority=policy_ref, authority_sha256=None, curriculum=curriculum_ref, curriculum_sha256=None,
            anchors=None, anchor_authority=None, candidate5_initialized=reference(initialized_path),
            mailbox=str(cohort_root.parent/(cohort_root.name+'_mailboxes')/arm), review_timeout_seconds=300,
            max_runtime_seconds=1800, initializer_metadata=reference(metadata_path))
        references[arm] = write(output/f'{arm}.DRAFT_CONFIG.json', config)
    return write(output/'PROSPECT.json', dict(schema=SCHEMA, status='BLOCKED_PROSPECTIVE_NOT_ADMITTED',
        arms=references, initializer=initializer, source_receipts=[reference(initialized_path), reference(metadata_path)],
        observed_adapter_tensor_bytes=adapter_bytes, reader_hard_limit_bytes=64*1024**2, blockers=blockers,
        task_indices=[0, 1], task_ids=[gym.task_id(index) for index in (0, 1)], cycles_per_arm=2,
        helper=reference(__file__), remote_state_verified=False, GPU_calls=0, scientific_claim=False))


def load_anchors(config, authority):
    approval = bound(config['anchor_authority'])
    require(approval['schema'] == 'R165_TRAIN_ANCHOR_AUTHORITY_V1' and approval['inventory'] == config['anchors']
            and approval['split'] == 'TRAIN' and approval['original_masks_preserved'] is True
            and approval['verified_competence'] is True and approval['source_receipts'], 'external_TRAIN_anchor_authority')
    for source in approval['source_receipts']:
        bound(source)
    document = bound(config['anchors'])
    anchors = {family: [dict(row, encoded=fit.EncodedRow(tuple(row['encoded']['input_ids']),
                tuple(row['encoded']['labels']), tuple(row['encoded']['target_ids']))) for row in records]
               for family, records in document.items()}
    require(fit.digest(fit.anchor_document(anchors)) == authority['anchors_sha256'] == approval['anchors_sha256'],
            'original_encoded_anchor_masks_hash')
    from gpu.orch_r108_guided_native import validate_anchor_inventory
    validate_anchor_inventory(anchors)
    for records in anchors.values():
        for row in records:
            fit._anchor_sample(row['encoded'], authority['context_limit'])
    return anchors


def check(config_reference):
    config = bound(config_reference)
    require(config['schema'] == SCHEMA and config['status'] == 'READY_FOR_EXTERNAL_ADMISSION',
            'prospective_or_unapproved_config_not_executable')
    authority, curriculum, plan = bound(config['authority']), bound(config['curriculum']), bound(config['plan'])
    require(authority['execution_kind'] == 'EXTERNALLY_VALIDATED_EXECUTOR', 'no_CPU_fixture_mode_in_executable')
    require(type(config['review_timeout_seconds']) is int and 1 <= config['review_timeout_seconds'] <= 600
            and type(config['max_runtime_seconds']) is int and 1 <= config['max_runtime_seconds'] <= 1800,
            'finite_two_cycle_timeout')
    require(len(curriculum['tasks']) == 2 and curriculum['plan'] == config['plan'], 'exact_two_cycles_and_plan')
    cycle.validate_curriculum(curriculum, config['curriculum_sha256'], authority, config['authority_sha256'])
    reader = capture.Reader(capture.Limits(**authority['reader_limits']))
    fit.verify_authority(authority, config['authority_sha256'], reader=reader)
    require(str(Path(__file__).resolve()) in authority['source_pins'], 'driver_in_bound_source_closure')
    initialized, metadata = bound(config['candidate5_initialized']), bound(config['initializer_metadata'])
    require(initialized['checkpoint_commit_sha256'] == metadata['commit_sha256'] == authority['initializer']['commit']['sha256']
            and metadata['saved_optimizer_steps'] == 0
            and initialized['observed_initial_state']['adapter_state_sha256'] == authority['initializer']['state']['adapter_sha256'],
            'actual_candidate5_initializer_not_later_raw_sleep')
    anchors = load_anchors(config, authority)
    fit.native.validate_plan(plan)
    mailbox = capture.canonical(config['mailbox'])
    excluded = [capture.canonical(path) for path in [authority['fork_root'], plan['source_root'],
                                                   curriculum['capture_root'], *authority['protected_roots']]]
    require(all(not mailbox.is_relative_to(path) and not path.is_relative_to(mailbox) for path in excluded),
            'separate_review_mailbox')
    require(curriculum['hard_end_unix'] == plan['hard_end_unix'], 'exact_original_wall')
    return config, authority, curriculum, plan, anchors


def verify_imports(authority):
    for name, module in tuple(sys.modules.items()):
        if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
            path = str(Path(module.__file__).resolve())
            require(path in authority['source_pins'] and reference(path)['sha256'] == authority['source_pins'][path],
                    'runtime_import_outside_pinned_closure:'+name)


def verify_go(go_reference, config_reference, *, action, round_index=None, submission=None):
    go = bound(go_reference)
    require(go['schema'] == 'R165_MAIN_GO_V1' and go['approved_by'] == 'Main' and go['action'] == action
            and go['driver_config_sha256'] == config_reference['sha256'], 'externally_pinned_Main_GO')
    require(type(go['created_unix']) in (int, float) and type(go['expires_unix']) in (int, float)
            and go['created_unix'] <= time.time() < go['expires_unix'], 'unexpired_Main_GO')
    if action == 'FIT':
        require(type(go['round_index']) is int and go['round_index'] == round_index
                and go['submission'] == submission, 'Main_exact_round_submission_GO')
    return go


def admit_run(config_reference, config, plan, go_reference):
    go = verify_go(go_reference, config_reference, action='RUN_TWO_CYCLES')
    admission = bound(go['admission'])
    require(admission['schema'] == 'R165_EXTERNAL_ADMISSION_V1' and admission['status'] == 'PASS'
            and admission['driver_config_sha256'] == config_reference['sha256']
            and admission['root'] == plan['root'] and admission['gpu_uuid'] == plan['gpu_uuid']
            and admission['physical'] == plan['physical'] and admission['lease_end_unix'] == plan['lease_end_unix']
            and admission['hard_end_unix'] == plan['hard_end_unix']
            and admission['negative_confinement_passed'] is True and admission['foreign_processes_clear'] is True
            and admission['evidence'], 'fresh_exact_external_confinement_and_census_required')
    require(time.time() < admission['expires_unix'] <= go['expires_unix']
            and admission['created_unix'] <= time.time() < plan['hard_end_unix']
            <= time.time()+config['max_runtime_seconds'], 'fresh_finite_admission_wall')
    for evidence in admission['evidence']:
        bound(evidence)
    require(os.environ.get('R165_ADMISSION_CONFIG_SHA256') == config_reference['sha256']
            and os.environ.get('R125_ADMISSION_PLAN_SHA256') == config['plan']['sha256']
            and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
            and os.environ.get('HF_HUB_OFFLINE') == os.environ.get('TRANSFORMERS_OFFLINE') == '1',
            'external_wrapper_admission_and_local_model_only')
    require(os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True', 'unchanged_allocator_contract')


@contextmanager
def deadline(unix):
    require(signal.getitimer(signal.ITIMER_REAL)[0] == 0, 'dedicated_driver_process_no_existing_timer')

    def expired(unused_signal, unused_frame):
        raise TimeoutError('R165 finite process wall')

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, unix-time.time()))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def fresh_learner(plan, authority, authority_sha256):
    from gpu.orch_r161_native_executor import NativeExecutor, admit_initializer_checkpoint
    binding = dict(fork_root=authority['fork_root'], mode=authority['mode'], authority_sha256=authority_sha256,
                   initializer_commit_sha256=authority['initializer']['commit']['sha256'])
    admitted = admit_initializer_checkpoint(fork_binding=binding, reference=authority['initializer']['commit'])
    require(admitted.fingerprint() == authority['initializer']['state'], 'admitted_initializer_semantic_fingerprints')
    verify_imports(authority)
    child = fit.native.NativeChild(plan, checkpoint=None)
    verify_imports(authority)
    executor = NativeExecutor(child, fork_binding=binding, execution_kind='EXTERNALLY_VALIDATED_EXECUTOR',
                              initializer_reference=authority['initializer']['commit'])
    require(executor.restore_admitted_checkpoint(admitted) == authority['initializer']['state'], 'safe_admitted_restore')
    return child, executor


def birth(plan, checkpoint):
    from organism_v6.orch_r124_train_history import TrainHistory
    stream = cycle.stream_module.ContinualStream(TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt']),
        context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'], segments_per_sleep=2,
        deadline_unix=plan['hard_end_unix'], model_state_sha256=fit.digest(checkpoint['checkpoint_sha256']),
        allow_eviction=True, experiment=fit.native.experiment_binding(plan))
    if plan.get('presentation_version'):
        stream.set_presentation(dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                                     birth_prompt=plan['birth_prompt']), plan['context_limit'])
    return stream


def candidates(entries):
    require(type(entries) is list and len(entries) <= 32, 'bounded_explicit_reviewed_packets')
    result = []
    for entry in entries:
        require(type(entry) is dict and set(entry) == {'capture_manifest', 'reviews'}, 'exact_packet_review_handoff')
        manifest = entry['capture_manifest']
        require(Path(manifest['path']).name == 'MANIFEST.json', 'actual_capture_manifest')
        packet = capture.load_packet(Path(manifest['path']).parent, expected_manifest_sha256=manifest['sha256'])
        require(type(entry['reviews']) is list and 2 <= len(entry['reviews']) <= 8, 'external_independent_reviews_required')
        reviews = []
        reader = capture.Reader(capture.Limits())
        for review in entry['reviews']:
            raw = fit._ref(reader, review)
            reviews.append(capture.eligibility.capture(review['path'], raw))
        result.append(dict(packet=packet, reviews=reviews))
    return result


def submit(config_reference, submission_reference, fit_go_reference):
    config = bound(config_reference)
    require(config['schema'] == SCHEMA and config['status'] == 'READY_FOR_EXTERNAL_ADMISSION', 'active_driver_config_required')
    submission = bound(submission_reference)
    index = submission['round_index']
    require(type(index) is int and index in (0, 1), 'only_two_rounds')
    verify_go(fit_go_reference, config_reference, action='FIT', round_index=index, submission=submission_reference)
    waiting = reference(Path(config['mailbox'])/f'WAIT{index:04d}.json')
    require(submission['wait_receipt'] == waiting and bound(waiting)['driver_config_sha256'] == config_reference['sha256'],
            'exact_resident_capture_handoff')
    return write(Path(config['mailbox'])/f'SUBMIT{index:04d}.json',
                 dict(submission=submission_reference, fit_go=fit_go_reference))


def run_resident(runner, config_reference, config, authority):
    mailbox = Path(config['mailbox'])
    for index in range(2):
        verify_imports(authority)
        captured = runner.collect_next()
        expires = min(time.time()+config['review_timeout_seconds'], runner.curriculum['hard_end_unix'])
        waiting = write(mailbox/f'WAIT{index:04d}.json', dict(schema=SCHEMA, status='WAITING_EXTERNAL_REVIEWS_NOT_ELIGIBLE',
            driver_config_sha256=config_reference['sha256'], round_index=index, captured=captured,
            review_deadline_unix=expires, next_command='submit', scientific_claim=False))
        command = mailbox/f'SUBMIT{index:04d}.json'
        while not command.exists():
            require(time.time() < expires, 'finite_external_review_wait_expired')
            time.sleep(min(1, max(.001, expires-time.time())))
        require(time.time() < expires, 'review_submission_after_deadline')
        handoff = bound(reference(command))
        submission = bound(handoff['submission'])
        require(submission['schema'] == 'R165_REVIEW_SUBMISSION_V1' and submission['round_index'] == index
                and submission['wait_receipt'] == waiting, 'exact_current_review_submission')
        verify_go(handoff['fit_go'], config_reference, action='FIT', round_index=index, submission=handoff['submission'])
        new, replay = candidates(submission['new']), candidates(submission['replay'])
        require(new, 'no_empty_or_synthetic_acceptance_to_advance_curriculum')
        authorization = bound(submission['batch_authorization'])
        verify_imports(authority)
        result = runner.fit_pending(new, replay, batch_authorization=authorization,
            expected_batch_authorization_sha256=submission['batch_authorization_sha256'])
        write(mailbox/f'FIT{index:04d}.json', dict(status='BOUND_FIT_AND_STREAM_COMMITTED',
            commit=dict(path=result['path'], sha256=result['sha256']), scientific_claim=False))
    return write(mailbox/'COMPLETE.json', dict(schema=SCHEMA, status='TWO_CYCLES_COMPLETED', scientific_claim=False))


def run(config_reference, run_go_reference):
    config, authority, curriculum, plan, anchors = check(config_reference)
    admit_run(config_reference, config, plan, run_go_reference)
    verify_imports(authority)
    root, mailbox = Path(authority['fork_root']), Path(config['mailbox'])
    require(not root.exists() and not mailbox.exists(), 'fresh_fork_and_mailbox_only_no_resume')
    mailbox.mkdir(mode=0o700, parents=False, exist_ok=False)
    write(mailbox/'STARTED.json', dict(schema=SCHEMA, driver_config_sha256=config_reference['sha256'], pid=os.getpid()))
    try:
        with deadline(plan['hard_end_unix']):
            fit.create_fork(authority, expected_authority_sha256=config['authority_sha256'],
                            reader=capture.Reader(capture.Limits(**authority['reader_limits'])))
            child, executor = fresh_learner(plan, authority, config['authority_sha256'])
            checkpoint = bound(authority['initializer']['commit'])
            journal = (cycle.GuidedJournal(root/'stream', expected_authority_sha256=config['authority_sha256'], create=True)
                       if authority['mode'] == 'frozen' else cycle.journal_module.StreamJournal(root/'stream', create=True))
            with journal:
                stream = birth(plan, checkpoint)
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
                runner = cycle.GuidedCycle(child=child, stream=stream, journal=journal, executor=executor, anchors=anchors,
                    authority=authority, expected_authority_sha256=config['authority_sha256'], curriculum=curriculum,
                    expected_curriculum_sha256=config['curriculum_sha256'])
                return run_resident(runner, config_reference, config, authority)
    except BaseException as error:
        write(mailbox/'FAILED.json', dict(error_type=type(error).__name__, retry_allowed=False,
                                         state_requires_owner_reconciliation=True, scientific_claim=False))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    prepare = actions.add_parser('prospect')
    for name in ('output', 'cohort-root', 'source-root'):
        prepare.add_argument('--'+name, required=True)
    prepare.add_argument('--candidate5', default=str(CANDIDATE5))
    for action in ('check', 'run', 'submit'):
        command = actions.add_parser(action)
        command.add_argument('--config', required=True)
        command.add_argument('--config-sha256', required=True)
        if action in ('run', 'submit'):
            command.add_argument('--go', required=True)
            command.add_argument('--go-sha256', required=True)
        if action == 'submit':
            command.add_argument('--submission', required=True)
            command.add_argument('--submission-sha256', required=True)
    args = parser.parse_args(argv)
    if args.action == 'prospect':
        result = prospect(args.output, cohort_root=args.cohort_root, source_root=args.source_root, candidate5=args.candidate5)
    else:
        config_reference = dict(path=args.config, sha256=args.config_sha256)
        if args.action == 'check':
            require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'preflight_CPU_only_environment')
            check(config_reference)
            result = dict(status='CPU_PROVENANCE_ONLY_NOT_ADMISSION', config=config_reference, GPU_calls=0)
        elif args.action == 'run':
            result = run(config_reference, dict(path=args.go, sha256=args.go_sha256))
        else:
            result = submit(config_reference, dict(path=args.submission, sha256=args.submission_sha256),
                            dict(path=args.go, sha256=args.go_sha256))
    print(capture.encoded(result).decode(), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
