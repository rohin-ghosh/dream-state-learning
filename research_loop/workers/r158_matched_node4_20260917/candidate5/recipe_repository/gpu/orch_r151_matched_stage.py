"""CPU-only source and cohort staging; this module never admits or launches GPUs."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

from gpu import orch_r125_continual_native as native
from gpu import orch_r150_matched_native as matched
from gpu import orch_r150_guard_patch as guard_patch
from gpu import orch_r145_suffix_boundary as memory_patch
from gpu.orch_r151_memory_probe import PRIOR_GPU_SHA256, RUNTIME_SHA256
from organism_v6.orch_r125_plain_context import VERSION


SCHEMA = 'R151_MATCHED_STAGE_V1'
HOST = '[REDACTED_HOST]'
BASE = Path('/localhome/local-rohing')
LEASE_SHA256 = '12e187a3237d6c167d91c4abaae9e6ef671e096d827c9ed68a662aa465d51049'
DEVICES = {0: 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
           3: 'GPU-d23c9369-39cf-51fd-833e-13292f173006',
           4: 'GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d'}
ARM_DEVICES = {'parented_learning': 0, 'parented_frozen': 4, 'unparented_learning': 3}
OLD_INITIALIZE = "        matched.initialize(config['plan_path'])\n"
NEW_INITIALIZE = """        from gpu.orch_r151_memory_probe import initial_capacity
        matched.initialize(config['plan_path'], validate_child=initial_capacity)
"""


def patch_guard(source):
    intermediate = guard_patch.patch_source(source)
    native.require(intermediate.count(OLD_INITIALIZE) == 1, 'single_initializer_dispatch')
    result = intermediate.replace(OLD_INITIALIZE, NEW_INITIALIZE)
    native.require(revert_guard(result) == source, 'exact_guard_validation_callback_patch')
    compile(result, '<r151-bound-initializer-guard>', 'exec')
    return result


def revert_guard(source):
    native.require(source.count(NEW_INITIALIZE) == 1, 'exact_capacity_initializer_callback')
    return guard_patch.revert_source(source.replace(NEW_INITIALIZE, OLD_INITIALIZE))


def regular(path):
    path = Path(path)
    native.require(path.is_absolute() and path == path.resolve()
        and not any(part.is_symlink() for part in (path, *path.parents)), 'canonical_staging_paths')
    native.require(path.is_file(), 'regular_staging_input')
    return path


def source_files(repository):
    repository = Path(repository).resolve()
    files = {}
    for package in ('gpu', 'organism_v6', 'tests'):
        for path in sorted((repository/package).rglob('*.py')):
            regular(path)
            files[str(path.relative_to(repository))] = native.sha(path)
    startup = repository/'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    regular(startup)
    files[str(startup.relative_to(repository))] = native.sha(startup)
    return files


def stage_source(repository, destination, runtime_path, proof_path):
    repository, destination = Path(repository).resolve(), Path(destination)
    runtime_path, proof_path = regular(runtime_path), regular(proof_path)
    native.require(native.sha(runtime_path) == RUNTIME_SHA256 and native.sha(proof_path) == PRIOR_GPU_SHA256,
                   'same_validated_runtime_and_GPU_proof')
    memory_patch.validate_gpu_proof(native.read(proof_path), RUNTIME_SHA256)
    native.require(destination.is_absolute() and destination == destination.resolve()
        and not destination.exists() and all(not destination.is_relative_to(repository/package)
                                           for package in ('gpu', 'organism_v6', 'tests')),
        'new_source_outside_input_packages')
    before = source_files(repository)
    native.require(before.get('gpu/orch_r125_continual_guard.py') == guard_patch.ORIGINAL_SHA256,
                   'original_guard_source_required')
    destination.mkdir(parents=True, exist_ok=False)
    for relative, expected in before.items():
        source, target = repository/relative, destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        native.require(native.sha(target) == expected, 'source_copy_hash')
    native.require(source_files(repository) == before, 'source_inputs_unchanged_during_stage')
    native_target = destination/'gpu/orch_r125_continual_native.py'
    native_source = native_target.read_text()
    patched_native = memory_patch.patch_source(native_source, before['gpu/orch_r125_continual_native.py'],
                                               RUNTIME_SHA256, proof_path, PRIOR_GPU_SHA256)
    native_target.write_text(patched_native)
    guard_target = destination/'gpu/orch_r125_continual_guard.py'
    guard_target.write_text(patch_guard(guard_target.read_text()))
    for source, name in [(runtime_path, memory_patch.RUNTIME_FILE), (proof_path, 'R145_GPU_PROOF.json')]:
        target = destination/'gpu'/name
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        native.require(native.sha(target) == native.sha(source), 'memory_receipt_copy')
    files = {str(path.relative_to(destination)): native.sha(path)
             for path in sorted(destination.rglob('*')) if path.is_file()}
    record = dict(schema=SCHEMA, status='SOURCE_STAGED_NOT_ADMITTED', source_root=str(destination),
        input_root=str(repository), input_files=before, files=files,
        changed_runtime_files=['gpu/orch_r125_continual_native.py', 'gpu/orch_r125_continual_guard.py'],
        fixed_initializer_capacity_callback=True, original_guard_policy_preserved=True,
        prior_GPU_proof_sha256=PRIOR_GPU_SHA256, runtime_sha256=RUNTIME_SHA256,
        GPU_calls=0, donor_retirements=0, staged_unix=time.time())
    native.write_once(destination/'STAGED_SOURCE.json', record)
    return record


def prepare_cohort(source, output, lease_path):
    source, output, lease_path = Path(source).resolve(), Path(output), regular(lease_path)
    native.require(native.sha(lease_path) == LEASE_SHA256, 'existing_node5_runtime_receipt')
    lease = native.read(lease_path)
    native.require(lease['lease_extended'] is False and lease['safety_margin_seconds'] == 600
        and lease['hard_end_unix'] == lease['lease_end_unix']-600 and time.time() < lease['hard_end_unix'],
        'unchanged_existing_lease_end_and_margin')
    native.require(output.is_absolute() and output == output.resolve() and not output.exists()
        and str(output).startswith(str(BASE)+'/orch_r151_')
        and not output.is_relative_to(source), 'new_node5_cohort_root')
    staged = native.read(source/'STAGED_SOURCE.json')
    for relative, expected in staged['files'].items():
        native.require(native.sha(source/relative) == expected, 'staged_source_unchanged')
    startup = source/'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt'
    plans = []
    for arm, physical in ARM_DEVICES.items():
        plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256, system_prompt=native.SYSTEM,
            birth_prompt=startup.read_text(), startup_context=dict(version='R127_STARTUP_V1',
                path=str(startup), sha256=native.sha(startup)),
            presentation_version=VERSION, presleep_variant='free_distillation', seed=0,
            compaction_invitation=native.PRESLEEP_INVITATIONS['free_distillation'],
            new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25, segments_per_sleep=2,
            segment_tokens=512, context_limit=16384, max_sleeps=None, readout_revision=1,
            root=str(output/arm), source_root=str(source), physical=physical, gpu_uuid=DEVICES[physical],
            model_dir=str(BASE/'.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28'),
            anchors=str(BASE/'orch_r107_base_anchors_20260915_attempt1'),
            decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
            hard_end_unix=lease['hard_end_unix'], lease_end_unix=lease['lease_end_unix'],
            matched_arm=arm, parent_enabled=arm != 'unparented_learning',
            initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
        native.validate_plan(plan)
        plans.append(plan)
    cohort = matched.cohort_document(plans, output/'common_initial')
    output.mkdir(parents=True, exist_ok=False)
    native.write_once(output/'COHORT.json', cohort)
    budget = dict(schema='R151_EXISTING_NODE5_COHORT_BUDGET_V1',
        derived_from=dict(path=str(lease_path), sha256=LEASE_SHA256),
        lease_end_unix=lease['lease_end_unix'], hard_end_unix=lease['hard_end_unix'], safety_margin_seconds=600,
        lease_extended=False, existing_life_wall_changed=False, physical_devices=sorted(DEVICES),
        host_sha256=hashlib.sha256(HOST.encode()).hexdigest(),
        new_experiment_scope='R150_PROSPECTIVE_MATCHED_CONTINUAL_TRIPLET',
        owner_authorization='Standing builder scope; Rohin continuity/control rulings',
        declaration_only_not_admission=True)
    native.write_once(output/'LEASE_BUDGET.json', budget)
    for plan in plans:
        plan['matched_cohort'] = dict(path=str(output/'COHORT.json'), sha256=native.sha(output/'COHORT.json'))
        matched.validate_plan(plan)
        native.write_once(output/(plan['matched_arm']+'.PLAN.json'), plan)
    result = dict(schema=SCHEMA, status='COHORT_PREPARED_NOT_ALLOCATED',
        plans={plan['matched_arm']: dict(path=str(output/(plan['matched_arm']+'.PLAN.json')),
            sha256=native.sha(output/(plan['matched_arm']+'.PLAN.json'))) for plan in plans},
        cohort_sha256=native.sha(output/'COHORT.json'), lease_budget_sha256=native.sha(output/'LEASE_BUDGET.json'),
        source_manifest_sha256=native.sha(source/'STAGED_SOURCE.json'),
        GPU_calls=0, donor_retirements=0, initial_checkpoint_exists=False, prepared_unix=time.time())
    native.write_once(output/'PREPARED.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    staging = commands.add_parser('source')
    for option in ('repository', 'destination', 'runtime', 'proof'):
        staging.add_argument('--'+option, type=Path, required=True)
    plans = commands.add_parser('cohort')
    for option in ('source', 'output', 'lease'):
        plans.add_argument('--'+option, type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.action == 'source':
        result = stage_source(arguments.repository, arguments.destination, arguments.runtime, arguments.proof)
    else:
        result = prepare_cohort(arguments.source, arguments.output, arguments.lease)
    print(json.dumps(result, sort_keys=True))
