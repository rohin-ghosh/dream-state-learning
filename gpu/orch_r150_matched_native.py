"""Prospective matched continual lives; no existing child or checkpoint is reset."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import random
import shutil
import signal
import stat
import time

from gpu import orch_r125_continual_native as native
from organism_v6.orch_r124_train_history import TrainEvent, TrainHistory
from organism_v6.orch_r125_continual_stream import digest, experiment_binding, require


SCHEMA = 'R150_MATCHED_CONTINUAL_COHORT_V1'
ARMS = ('parented_learning', 'parented_frozen', 'unparented_learning')
COMMON_KEYS = ('base_sha256', 'model_dir', 'anchors', 'source_root', 'system_prompt', 'birth_prompt',
               'startup_context', 'presentation_version', 'seed', 'presleep_variant', 'compaction_invitation',
               'segments_per_sleep', 'segment_tokens', 'context_limit', 'new_presentations',
               'rehearsal_presentations', 'anchor_lambda', 'decoder', 'hard_end_unix', 'lease_end_unix',
               'max_sleeps', 'readout_revision')
INITIALIZATION_SOURCE_ROOT = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt3')
INITIALIZATION_SOURCE_FILES = {
    'commit': ('common_initial/COMMIT.json', 'f1fdb87d92e3e2efc401583faa02f2d6c5a8de07f5dcd20866215c8cb54a332c'),
    'plan': ('parented_learning.PLAN.json', '7ec0fc2375b7ca1f691cb158bfd361474c2ba23810b8ee925e9af2eea3dfeb56'),
    'capacity': ('common_initial/capacity_validation/RESULT.json', '630f3e54febf7da680d1f5eb34340a0b2bb2cbfa26418387fe059c60a49f1eb9'),
    'lifecycle': ('attempts/initialize-parented_learning-attempt1/LIFECYCLE.json', '9dcbcc3922f19a07c99d211af463d4e4a7bccb21d605e40bdce0a9e2afb5ed65'),
}


def common_configuration(plan):
    common = dict({key: deepcopy(plan[key]) for key in COMMON_KEYS},
                  initialization_validation_schema=plan.get('initialization_validation_schema'))
    if 'initialization_source' in plan:
        common['initialization_source'] = deepcopy(plan['initialization_source'])
    return common


def read_initialization_reference(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_initialization_reference')
    path = Path(reference['path'])
    require(path.is_absolute() and path == path.resolve()
            and not any(part.is_symlink() for part in (path, *path.parents))
            and stat.S_ISREG(path.lstat().st_mode), 'regular_initialization_reference')
    require(native.sha(path) == reference['sha256'], 'immutable_initialization_reference')
    return native.read(path)


def validate_initialization_source(plan):
    source = read_initialization_reference(plan['initialization_source'])
    require(type(source) is dict and set(source) == {'schema', *INITIALIZATION_SOURCE_FILES}
            and source['schema'] == 'R158_SAVED_INITIALIZATION_SOURCE_V1', 'scoped_initialization_source')
    documents = {}
    for name, (relative, checksum) in INITIALIZATION_SOURCE_FILES.items():
        require(source[name] == dict(path=str(INITIALIZATION_SOURCE_ROOT / relative), sha256=checksum),
                'exact_failed_attempt3_initialization_source')
        documents[name] = read_initialization_reference(source[name])
    require('initialization_source' not in documents['plan'], 'no_chained_initializer_recovery')
    original, original_cohort = validate_plan(documents['plan'])
    require(original['matched_arm'] == 'parented_learning' and original['physical'] == 5
            and original['gpu_uuid'] == 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30'
            and original_cohort['initial_directory'] == str(INITIALIZATION_SOURCE_ROOT / 'common_initial'),
            'original_node4_initializer_binding')
    require(not (INITIALIZATION_SOURCE_ROOT / 'common_initial/INITIALIZED.json').exists()
            and not (INITIALIZATION_SOURCE_ROOT / 'common_initial/INITIALIZED.json').is_symlink()
            and all(member['root'] == str(INITIALIZATION_SOURCE_ROOT / arm)
                    and not Path(member['root']).exists() and not Path(member['root']).is_symlink()
                    for arm, member in original_cohort['members'].items()),
            'failed_initializer_never_admitted_or_born')
    current = common_configuration(plan)
    expected = common_configuration(original)
    current.pop('initialization_source')
    for configuration in (current, expected):
        configuration.pop('source_root')
        if configuration['startup_context'] is not None:
            configuration['startup_context'].pop('path')
    require(current == expected and plan.get('initialization_validation_schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1',
            'recovery_preserves_exact_initialization_recipe')
    member = original_cohort['members'][plan['matched_arm']]
    require(plan['physical'] == member['physical'] and plan['gpu_uuid'] == member['gpu_uuid'],
            'recovery_preserves_node4_arm_devices')
    new_source = Path(plan['source_root'])
    require(new_source.name == 'source' and new_source.parent.parent == INITIALIZATION_SOURCE_ROOT.parent
            and new_source.parent.name.startswith('orch_r158_matched_node4_')
            and new_source.parent != INITIALIZATION_SOURCE_ROOT
            and plan['root'] == str(new_source.parent / plan['matched_arm']), 'new_recovery_cohort_only')
    capacity = documents['capacity']
    require(capacity['schema'] == 'R151_MATCHED_INITIAL_CAPACITY_V1' and capacity['status'] == 'FAIL'
            and capacity['error'] == 'designated_node5_initializer_only'
            and capacity['error_type'] == 'ValueError' and capacity['plan_sha256'] == source['plan']['sha256']
            and capacity['optimizer_updates'] == capacity['generation_calls'] == 0
            and capacity['stream_data_written'] is False and capacity['scientific_evaluation'] is False
            and capacity['state_restored'] is False and capacity['restoration_status'] == 'UNVERIFIED'
            and not {'bounded_comparison', 'maximum_shape', 'maximum_losses'}.intersection(capacity),
            'only_known_premeasurement_node_binding_failure')
    lifecycle = documents['lifecycle']
    require(lifecycle['status'] == 'SERVICE_EXIT_VERIFIED' and lifecycle['cgroup_empty_verified'] is True
            and lifecycle['service_returncode'] == 1, 'failed_initializer_exited_and_empty')
    checkpoint = documents['commit']
    native.NativeChild.verify_checkpoint(checkpoint)
    require(checkpoint['optimizer_steps'] == 0
            and checkpoint['adapter_path'] == str(INITIALIZATION_SOURCE_ROOT / 'common_initial/adapter')
            and checkpoint['optimizer_rng_path'] == str(INITIALIZATION_SOURCE_ROOT / 'common_initial/optimizer_rng.pt'),
            'original_saved_zero_step_checkpoint')
    native.verify_experiment_resume(plan, checkpoint.get('experiment'))
    return source, checkpoint


def cohort_document(plans, initial_directory):
    require(len(plans) == 3 and {plan['matched_arm'] for plan in plans} == set(ARMS), 'exact_three_matched_arms')
    first = common_configuration(plans[0])
    require(all(common_configuration(plan) == first for plan in plans), 'identical_common_runtime_configuration')
    require(len({plan['root'] for plan in plans}) == len({plan['gpu_uuid'] for plan in plans})
            == len({plan['physical'] for plan in plans}) == 3,
            'distinct_lives_and_GPUs')
    require(all(plan['parent_enabled'] is (plan['matched_arm'] != 'unparented_learning') for plan in plans),
            'explicit_parent_condition')
    initial = Path(initial_directory)
    roots = [Path(plan['root']) for plan in plans]
    require(initial.is_absolute() and all(root.is_absolute() for root in roots), 'absolute_cohort_paths')
    require(all(path == path.resolve() for path in [initial, *roots]), 'canonical_cohort_paths')
    require(not initial.is_relative_to(Path(first['source_root']).resolve()), 'initial_outside_source_tree')
    require(all(not initial.is_relative_to(root) and not root.is_relative_to(initial)
                for root in roots), 'shared_initial_not_a_branch_history')
    require(all(not left.is_relative_to(right) for left in roots for right in roots if left != right),
            'nonoverlapping_branch_roots')
    return dict(schema=SCHEMA, common=first, initial_directory=str(initial),
                members={plan['matched_arm']: dict(root=plan['root'], gpu_uuid=plan['gpu_uuid'],
                                                   physical=plan['physical'], parent_enabled=plan['parent_enabled'])
                         for plan in plans},
                initial_optimizer_steps=0, fresh_histories=True, evaluations_gate_continuation=False,
                comparison='PARENTED_LEARNING_VS_PARENTED_FROZEN_AND_UNPARENTED_LEARNING',
                boundary_alignment='ORDINARY_SEGMENTS_NOT_WALL_TIME_OR_EQUAL_REALIZED_TOKEN_EXPOSURE')


def validate_plan(plan):
    native.validate_plan(plan)
    from organism_v6.orch_r125_plain_context import VERSION
    require(plan.get('presentation_version') == VERSION, 'matched_plain_presentation_required')
    require(plan.get('initialization_validation_schema') in (None, 'R151_MATCHED_INITIAL_CAPACITY_V1'),
            'known_initialization_validation')
    require(plan.get('matched_arm') in ARMS and type(plan.get('parent_enabled')) is bool, 'bound_matched_arm')
    require(plan['parent_enabled'] is (plan['matched_arm'] != 'unparented_learning'), 'exact_parent_condition')
    require(plan.get('authorized_wall_extension') is None and plan.get('preupdate_recovery') is None,
            'no_implicit_existing_life_handoff')
    reference = plan['matched_cohort']
    require(native.sha(reference['path']) == reference['sha256'], 'immutable_matched_cohort')
    cohort = native.read(reference['path'])
    require(cohort['schema'] == SCHEMA and cohort['common'] == common_configuration(plan), 'common_plan_binding')
    require(type(cohort.get('members')) is dict and set(cohort['members']) == set(ARMS), 'exact_cohort_members')
    reconstructed = [dict(cohort['common'], matched_arm=arm, **cohort['members'][arm]) for arm in ARMS]
    require(cohort_document(reconstructed, cohort['initial_directory']) == cohort, 'exact_cohort_contract')
    member = dict(root=plan['root'], gpu_uuid=plan['gpu_uuid'], physical=plan['physical'],
                  parent_enabled=plan['parent_enabled'])
    require(cohort['members'][plan['matched_arm']] == member and set(cohort['members']) == set(ARMS),
            'cohort_allocation_binding')
    require(cohort['initial_optimizer_steps'] == 0 and cohort['fresh_histories'] is True
            and cohort['evaluations_gate_continuation'] is False, 'prospective_initialization_not_relabelled_lives')
    if 'initialization_source' in plan:
        validate_initialization_source(plan)
        require(cohort['initial_directory'] == str(Path(plan['source_root']).parent / 'common_initial'),
                'recovery_common_initial_namespace')
    return plan, cohort


def verify_initialization_validation(plan, cohort, initialized):
    if 'initialization_source' in plan:
        source, checkpoint = validate_initialization_source(plan)
        require(initialized.get('initialization_source') == plan['initialization_source']
                and initialized.get('recovered_initial_state_before_validation') == initialized.get('observed_initial_state')
                and type(initialized.get('observed_initial_state')) is dict
                and initialized['observed_initial_state'].get('checkpoint_file_hashes') == checkpoint['checkpoint_sha256'],
                'bound_recovered_initialization_provenance')
    schema = plan.get('initialization_validation_schema')
    if schema is None:
        return
    from gpu import orch_r151_memory_probe as probe

    def finite_number(value):
        try:
            return type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            return False

    def memory_evidence(memory, inputs, targets, logits, label):
        fields = ('full_input_tokens', 'target_tokens', 'logits_tokens', 'peak_allocated_bytes',
                  'peak_reserved_bytes', 'free_after_bytes', 'total_bytes')
        require(type(memory) is dict and all(type(memory.get(field)) is int and memory[field] >= 0
                for field in fields), label)
        require(memory['full_input_tokens'] == inputs and memory['target_tokens'] == targets
            and memory['logits_tokens'] == logits
            and 0 < memory['peak_allocated_bytes'] <= memory['peak_reserved_bytes'] <= memory['total_bytes']
            and memory['free_after_bytes'] <= memory['total_bytes'], label)

    def losses_evidence(losses):
        require(type(losses) is list and len(losses) == 5 and all(finite_number(value) for value in losses),
                'finite_capacity_child_plus_four_anchor_losses')

    reference = initialized.get('initialization_validation', {})
    expected = Path(cohort['initial_directory'])/'capacity_validation/RESULT.json'
    require(type(reference) is dict and reference.get('status') == 'PASS' and reference.get('schema') == schema
        and reference.get('path') == str(expected), 'required_initial_GPU_capacity_validation')
    require(not any(path.is_symlink() for path in (expected, *expected.parents))
        and native.sha(expected) == reference.get('sha256'), 'bound_initial_capacity_proof')
    proof = native.read(expected)
    require(type(proof) is dict and proof.get('status') == 'PASS' and proof.get('schema') == schema == probe.SCHEMA
        and proof.get('state_restored') is True and type(proof.get('optimizer_updates')) is int
        and proof['optimizer_updates'] == 0 and type(proof.get('generation_calls')) is int
        and proof['generation_calls'] == 0 and proof.get('stream_data_written') is False
        and proof.get('synthetic_shape_only') is True and proof.get('scientific_evaluation') is False
        and proof.get('restoration_status') == 'VERIFIED'
        and not any(field in proof for field in ('measurement_error', 'cleanup_errors', 'acceptance_error', 'error', 'error_type'))
        and proof.get('plan_sha256') == initialized.get('source_plan_sha256')
        and type(proof.get('context_limit')) is int and proof['context_limit'] == plan['context_limit'] == 16384
        and type(proof.get('segment_tokens')) is int and proof['segment_tokens'] == plan['segment_tokens'] == 512,
        'successful_same_initial_configuration_capacity_proof')
    require(proof.get('runtime_sha256') == probe.RUNTIME_SHA256
        and proof.get('prior_GPU_proof_sha256') == probe.PRIOR_GPU_SHA256, 'exact_capacity_runtime_and_prior_proof')
    require(proof.get('loss_tolerance') == probe.capacity.LOSS_TOLERANCE
        and proof.get('gradient_tolerance') == probe.capacity.GRAD_TOLERANCE,
        'unchanged_capacity_numerical_tolerances')
    require(all(type(proof.get(field)) is str and len(proof[field]) == 64
                and all(character in '0123456789abcdef' for character in proof[field])
                for field in ('plan_sha256', 'anchor_receipt_sha256'))
        and proof.get('exact_learning_trajectory_claim') is False, 'capacity_provenance_and_claim_boundary')
    comparison = proof.get('bounded_comparison')
    require(type(comparison) is dict and comparison.get('exact_rng') is True, 'complete_capacity_bounded_comparison')
    for field in ('original_losses', 'suffix_losses'):
        losses_evidence(comparison.get(field))
    require(all(abs(actual-expected_loss) <= probe.capacity.LOSS_TOLERANCE['atol']
                + probe.capacity.LOSS_TOLERANCE['rtol']*abs(expected_loss)
                for actual, expected_loss in zip(comparison['suffix_losses'], comparison['original_losses'])),
            'capacity_paired_losses_within_declared_tolerance')
    gradient_error = comparison.get('max_gradient_absolute_error')
    require(finite_number(gradient_error) and gradient_error >= 0, 'finite_capacity_gradient_error_evidence')
    original, suffix = comparison.get('original_memory'), comparison.get('suffix_memory')
    memory_evidence(original, 2048, 128, 2048, 'actual_bounded_original_memory')
    memory_evidence(suffix, 2048, 128, 129, 'actual_bounded_suffix_memory')
    require(suffix['peak_allocated_bytes'] <= original['peak_allocated_bytes']
        and suffix['total_bytes'] == original['total_bytes'], 'capacity_suffix_peak_not_increased_same_device')
    maximum = proof.get('maximum_shape', {})
    memory_evidence(maximum, 16384, 512, 513, 'actual_maximum_shape_capacity_headroom')
    require(maximum['free_after_bytes'] >= probe.MIN_HEADROOM_BYTES
        and maximum['total_bytes'] == original['total_bytes']
        and type(proof.get('minimum_headroom_bytes')) is int
        and proof['minimum_headroom_bytes'] == probe.MIN_HEADROOM_BYTES,
        'actual_maximum_shape_capacity_headroom')
    losses_evidence(proof.get('maximum_losses'))
    timing = ('started_unix', 'deadline_unix', 'measurement_finished_unix', 'finished_unix',
              'elapsed_seconds', 'cleanup_elapsed_seconds')
    require(all(finite_number(proof.get(field)) and proof[field] >= 0 for field in timing)
        and type(proof.get('work_budget_seconds')) is int and proof['work_budget_seconds'] == probe.PROBE_SECONDS
        and type(proof.get('cleanup_allowance_seconds')) is int and proof['cleanup_allowance_seconds'] == 0,
        'finite_capacity_timing_and_no_PASS_cleanup_extension')
    require(proof['deadline_unix'] == min(plan['hard_end_unix'], proof['started_unix']+probe.PROBE_SECONDS)
        and proof['started_unix'] <= proof['measurement_finished_unix'] <= proof['finished_unix'] < proof['deadline_unix']
        and proof['elapsed_seconds'] == proof['finished_unix']-proof['started_unix']
        and proof['cleanup_elapsed_seconds'] == proof['finished_unix']-proof['measurement_finished_unix'],
        'capacity_completed_within_declared_work_budget')


def verify_stream_plan(stream, plan):
    expected = dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                    birth_prompt=plan['birth_prompt'])
    require(stream.presentation == expected and stream.context_limit == plan['context_limit'],
            'restored_presentation_matches_cohort')
    require(stream.segment_tokens == plan['segment_tokens']
        and stream.segments_per_sleep == plan['segments_per_sleep']
        and stream.deadline_unix == plan['hard_end_unix'] and stream.allow_eviction is True,
        'restored_runtime_matches_cohort')
    history = stream.history.checkpoint()
    require(history['system_prompt'] == plan['system_prompt']
        and history['birth_prompt'] == plan['birth_prompt'], 'restored_history_prompts_match_cohort')
    native.verify_experiment_resume(plan, stream.experiment)


def copy_initial_checkpoint(source_commit, destination, *, verifier=native.NativeChild.verify_checkpoint):
    source_commit, destination = Path(source_commit), Path(destination)
    for path in (source_commit, destination):
        require(path.is_absolute() and not any(part.is_symlink() for part in (path, *path.parents)),
                'absolute_checkpoint_paths_without_symlinks')
    source_commit = source_commit.resolve(strict=True)
    original = native.read(source_commit)
    verifier(original)
    require(original['optimizer_steps'] == 0, 'fresh_initial_optimizer_only')
    require(not destination.exists(), 'new_life_checkpoint_destination')
    source_adapter, source_optimizer = Path(original['adapter_path']), Path(original['optimizer_rng_path'])
    require(not source_adapter.is_symlink() and not source_optimizer.is_symlink(), 'regular_initial_artifact_paths')
    require(source_adapter.resolve() == source_commit.parent/'adapter'
            and source_optimizer.resolve() == source_commit.parent/'optimizer_rng.pt', 'bound_initial_file_paths')
    require(stat.S_ISREG(source_optimizer.lstat().st_mode), 'regular_initial_optimizer')
    destination.mkdir(parents=True, exist_ok=False)
    adapter = destination/'adapter'
    adapter.mkdir()
    for name, expected in original['adapter_files'].items():
        require(Path(name).name == name and name not in ('', '.', '..'), 'flat_adapter_files')
        source = source_adapter/name
        require(stat.S_ISREG(source.lstat().st_mode) and native.sha(source) == expected, 'exact_regular_adapter_file')
        with source.open('rb') as reader, (adapter/name).open('xb') as writer:
            shutil.copyfileobj(reader, writer)
    optimizer = destination/'optimizer_rng.pt'
    with source_optimizer.open('rb') as reader, optimizer.open('xb') as writer:
        shutil.copyfileobj(reader, writer)
    result = dict(original, adapter_path=str(adapter.resolve()), optimizer_rng_path=str(optimizer.resolve()))
    verifier(result)
    require(result['checkpoint_sha256'] == original['checkpoint_sha256'], 'identical_initial_file_bytes')
    native.write_once(destination/'COMMIT.json', result)
    native.write_once(destination/'CLONE_PROVENANCE.json', dict(source_commit=str(source_commit),
        source_commit_sha256=native.sha(source_commit), destination_commit_sha256=native.sha(destination/'COMMIT.json'),
        copied_only=['adapter_files', 'optimizer_rng.pt'], history_copied=False, inbox_copied=False,
        training_rows_copied=False, identical_checkpoint_file_hashes=True))
    return result


def boundary_checkpoint(stream, root):
    checkpoint = (stream.sleep_receipts[-1]['checkpoint'] if stream.sleep_receipts
                  else stream.checkpoint()['state']['initial_checkpoint'])
    directory = Path(root)/'checkpoints'/(
        f'sleep_{len(stream.sleep_receipts):06d}' if stream.sleep_receipts else 'initial')
    require(not any(path.is_symlink() for path in (directory, *directory.parents)),
            'saved_boundary_without_symlinks')
    require(Path(checkpoint['adapter_path']) == directory/'adapter'
            and Path(checkpoint['optimizer_rng_path']) == directory/'optimizer_rng.pt',
            'latest_receipt_checkpoint_paths')
    require(native.read(directory/'COMMIT.json') == checkpoint, 'exact_latest_receipt_COMMIT')
    require(digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256,
            'latest_receipt_model_state')
    native.NativeChild.verify_checkpoint(checkpoint)
    return checkpoint


@contextmanager
def wall_timer(deadline_unix):
    remaining = deadline_unix-time.time()
    require(remaining > 0, 'native_wall_before_model_load')
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'no_nested_wall_timer')
    previous = signal.signal(signal.SIGALRM,
        lambda signum, frame: (_ for _ in ()).throw(TimeoutError('native_wall')))
    try:
        signal.setitimer(signal.ITIMER_REAL, remaining)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def verify_loaded_initial(child, checkpoint):
    child.verify_checkpoint(checkpoint)
    payload = child.torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(child.optimizer_steps == payload['optimizer_steps'] == 0 and not child.optimizer.state,
            'actual_fresh_empty_AdamW_state')
    require(child.optimizer.state_dict() == payload['optimizer'], 'actual_initial_optimizer_groups')
    require(list(child.parameters) == payload['parameter_names'], 'actual_initial_parameter_order')
    require(child.adapter_hash() == checkpoint['adapter_state_sha256'], 'actual_shared_initial_adapter')
    require(child.torch.equal(child.torch.get_rng_state(), payload['cpu_rng']), 'actual_common_CPU_RNG')
    actual_cuda = child.torch.cuda.get_rng_state_all()
    require(len(actual_cuda) == len(payload['cuda_rng']) == 1
            and all(child.torch.equal(actual, expected) for actual, expected in zip(actual_cuda, payload['cuda_rng'])),
            'actual_common_single_GPU_RNG')
    require(random.getstate() == payload['python_rng'], 'actual_common_python_RNG')
    return dict(adapter_state_sha256=child.adapter_hash(), optimizer_steps=0,
                optimizer_state_entries=0, parameter_count=len(child.parameters),
                cpu_rng_sha256=digest(payload['cpu_rng'].tolist()),
                cuda_rng_sha256=[digest(value.tolist()) for value in actual_cuda],
                python_rng_sha256=digest(payload['python_rng']),
                checkpoint_file_hashes=deepcopy(checkpoint['checkpoint_sha256']))


class MatchedChild(native.NativeChild):
    def sleep(self, new_rows, old_rows, anchors, record):
        if self.plan['matched_arm'] != 'parented_frozen':
            return super().sleep(new_rows, old_rows, anchors, record)
        require(new_rows and self.optimizer_steps == 0 and not self.optimizer.state,
                'frozen_control_never_updates_optimizer')
        require(not any(parameter.requires_grad for parameter in self.engine.model.parameters()),
                'frozen_control_parameters_readonly')
        before = self.adapter_hash()
        self.engine.verify_base()
        require(self.adapter_hash() == before, 'frozen_adapter_unchanged')
        return dict(kind='FROZEN_CONTROL_BOUNDARY', optimizer_steps=0, total_optimizer_steps=0,
                    cumulative_optimizer_steps=0, before_adapter_sha256=before, after_adapter_sha256=before,
                    child_token_exposures=0, anchor_token_exposures=0, presentations=[],
                    frozen_base_verified=True, weight_updates_enabled=False,
                    no_update_reason='frozen_control_condition',
                    context_compaction_schedule='SAME_AS_LEARNING_ARMS',
                    configured_anchor_lambda=0.25, anchor_mix_applied=False)


def require_admission(plan_path, plan):
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == native.sha(plan_path), 'admitted_plan_environment')
    require(os.environ.get('R150_COHORT_SHA256') == plan['matched_cohort']['sha256'], 'admitted_cohort_environment')


def initialize(plan_path, *, validate_child=None):
    plan_path = Path(plan_path)
    plan, cohort = validate_plan(native.read(plan_path))
    require_admission(plan_path, plan)
    require(plan['matched_arm'] == 'parented_learning', 'single_designated_initializer')
    destination = Path(cohort['initial_directory'])
    require(not destination.exists(), 'common_initial_checkpoint_never_recreated')
    with wall_timer(plan['hard_end_unix']):
        if 'initialization_source' in plan:
            require(validate_child is not None, 'recovery_requires_actual_capacity_callback')
            source, original_checkpoint = validate_initialization_source(plan)
            checkpoint = copy_initial_checkpoint(source['commit']['path'], destination)
            require(checkpoint['checkpoint_sha256'] == original_checkpoint['checkpoint_sha256'],
                    'recovery_copies_exact_original_checkpoint')
            child = MatchedChild(plan, checkpoint)
            before_validation = verify_loaded_initial(child, checkpoint)
        else:
            child = MatchedChild(plan)
            checkpoint = child.checkpoint(destination)
        validation = (validate_child(child, plan_path, destination) if validate_child is not None
                      else dict(status='NOT_REQUESTED', GPU_capacity_claim=False))
        require(validate_child is None or validation.get('status') == 'PASS', 'initial_validation_must_pass')
        observation = verify_loaded_initial(child, checkpoint)
        initialized = dict(schema=SCHEMA,
            cohort_sha256=plan['matched_cohort']['sha256'], checkpoint_commit_sha256=native.sha(destination/'COMMIT.json'),
            source_plan_sha256=native.sha(plan_path), source_process=child.native.process_identity(),
            observed_initial_state=observation, initialization_validation=validation,
            generation_calls=0, optimizer_updates=0, initialized_unix=time.time())
        if 'initialization_source' in plan:
            require(observation == before_validation, 'recovered_initial_state_unchanged_after_capacity')
            initialized.update(initialization_source=deepcopy(plan['initialization_source']),
                recovered_initial_state_before_validation=before_validation)
        verify_initialization_validation(plan, cohort, initialized)
        native.write_once(destination/'INITIALIZED.json', initialized)
    return observation


def birth_stream(plan, checkpoint, stream_class):
    history = TrainHistory(system_prompt=plan['system_prompt'], birth_prompt=plan['birth_prompt'])
    budget = dict(context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'],
                  total_generated_tokens=0, segments_per_sleep=plan['segments_per_sleep'])
    history.append(TrainEvent(event_id='runtime:birth_budget', actor='environment', split='TRAIN',
        phase='feedback', episode_id='continual_stream', source_id='R125_RUNTIME_BUDGET',
        source_sha256=digest(budget), origin='TRAIN_COLLECTION', text='[budget] '+json.dumps(budget, sort_keys=True)))
    stream = stream_class(history, context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'],
        segments_per_sleep=2, deadline_unix=plan['hard_end_unix'],
        model_state_sha256=digest(checkpoint['checkpoint_sha256']), allow_eviction=True,
        experiment=experiment_binding(plan), arm=plan['matched_arm'], cohort_sha256=plan['matched_cohort']['sha256'],
        initial_checkpoint=checkpoint)
    stream.set_presentation(dict(version=plan['presentation_version'], system_prompt=plan['system_prompt'],
                                birth_prompt=plan['birth_prompt']), plan['context_limit'])
    return stream


def run(plan_path, *, resume=False):
    from gpu.orch_r107_base_anchors_inventory import build_inventory
    from gpu.orch_r150_matched_journal import MatchedJournal
    from organism_v6.orch_r150_matched_stream import MatchedStream
    from gpu import orch_r150_readout_custody as readouts

    plan_path = Path(plan_path)
    plan, cohort = validate_plan(native.read(plan_path))
    require_admission(plan_path, plan)
    root = Path(plan['root'])
    initialized = native.read(Path(cohort['initial_directory'])/'INITIALIZED.json')
    initial_commit = Path(cohort['initial_directory'])/'COMMIT.json'
    require(initialized['cohort_sha256'] == plan['matched_cohort']['sha256']
            and initialized['checkpoint_commit_sha256'] == native.sha(initial_commit), 'bound_common_initialization')
    verify_initialization_validation(plan, cohort, initialized)
    with wall_timer(plan['hard_end_unix']):
        root.mkdir(parents=True, exist_ok=True)
        with MatchedJournal(root/'stream', create=not resume, arm=plan['matched_arm'],
                            cohort_sha256=plan['matched_cohort']['sha256']) as journal:
            if resume:
                latest = journal.latest_checkpoint()
                require(latest is not None, 'saved_matched_boundary_required')
                stream = MatchedStream.restore(latest['document'], expected_sha256=latest['expected_sha256'],
                    expected_arm=plan['matched_arm'], expected_cohort_sha256=plan['matched_cohort']['sha256'])
                require(stream.pending is None and stream.sleep_frontier == len(stream.rows), 'saved_boundary_resume_only')
                require(stream.arm == plan['matched_arm'] and stream.cohort_sha256 == plan['matched_cohort']['sha256'],
                        'exact_matched_condition_resume')
                verify_stream_plan(stream, plan)
                checkpoint = boundary_checkpoint(stream, root)
                completed = len(stream.sleep_receipts)
                readout_state = readouts.disposition(plan_path, plan, checkpoint, completed)
                child = MatchedChild(plan, checkpoint)
            else:
                checkpoint = copy_initial_checkpoint(initial_commit, root/'checkpoints/initial')
                readout_state = readouts.disposition(plan_path, plan, checkpoint, 0)
                require(readout_state == 'NOT_STARTED', 'new_life_has_no_prior_readout')
                child = MatchedChild(plan, checkpoint)
                observation = verify_loaded_initial(child, checkpoint)
                require(observation == initialized['observed_initial_state'], 'actual_cross_arm_initial_identity')
                native.write_once(root/'INITIAL_STATE_VERIFIED.json', dict(observation,
                    arm=plan['matched_arm'], cohort_sha256=plan['matched_cohort']['sha256'], observed_unix=time.time()))
                stream = birth_stream(plan, checkpoint, MatchedStream)
                journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
                completed = 0
            anchors, anchor_receipt = build_inventory(plan['anchors'], child.tokenizer, plan['context_limit'])
            journal.record('LOADED', dict(pid=os.getpid(), runtime=child.engine.runtime,
                base_sha256=native.BASE_SHA256, adapter_sha256=child.adapter_hash(), optimizer_steps=child.optimizer_steps,
                anchors=anchor_receipt, resume=resume, matched_arm=plan['matched_arm'],
                cohort_sha256=plan['matched_cohort']['sha256'], loaded_unix=time.time()))
            if readout_state == 'NOT_STARTED':
                readouts.fresh_readout(child, plan_path, checkpoint, completed)
            if plan['max_sleeps'] is not None and completed >= plan['max_sleeps']:
                return
            while time.time() < plan['hard_end_unix']:
                stream.step(child.generate, child.count_tokens, journal.record, incoming=journal.read_inbox())
                if not stream.sleep_due:
                    continue
                cycle = completed+1
                native.prepare_sleep(child, stream, journal, cycle)
                pending = stream.checkpoint()
                pending['state']['pending'] = 'sleep:'+digest([row['source_sha256'] for row in stream.pending_rows()])
                pending['sha256'] = digest(pending['state'])
                journal.record('SLEEP_REQUEST', dict(cycle=cycle, resume_state=pending))
                checkpoint = native.finish_sleep(child, stream, journal, anchors, root, cycle)
                completed = cycle
                readouts.fresh_readout(child, plan_path, checkpoint, cycle)
                if plan['max_sleeps'] is not None and completed >= plan['max_sleeps']:
                    journal.record('TERMINAL', dict(status='MATCHED_FIXED_BOUNDARY_BUDGET_COMPLETE',
                        boundaries=completed, optimizer_steps=child.optimizer_steps,
                        matched_arm=plan['matched_arm'], retained_learning_claim=False, finished_unix=time.time()))
                    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('initialize', 'run'))
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    arguments = parser.parse_args()
    if arguments.phase == 'initialize':
        require(not arguments.resume, 'initialization_is_not_recovery')
        print(json.dumps(initialize(arguments.plan), sort_keys=True))
    else:
        run(arguments.plan, resume=arguments.resume)
