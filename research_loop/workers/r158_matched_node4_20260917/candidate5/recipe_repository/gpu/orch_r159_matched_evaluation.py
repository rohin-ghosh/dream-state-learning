"""Separate, prospective, sealed R159 matched-checkpoint evaluation campaign."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time

from gpu import orch_r130_checkpoint_benchmark as native


SCHEMA = 'R159_MATCHED_EVALUATION_V1'
ARMS = ('parented_learning', 'parented_frozen', 'unparented_learning')
MILESTONES = (0, 1, 2, 4)
COUNTS = {'canary': 4, 'gate': 12, 'exam': 12}
CONDITIONS = ('LORA_ON', 'LORA_OFF')
CALLS = 56
CAP = 672
PACKAGE_VERSION = '0.1.25'
OLD_ROOT = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
CAMPAIGN_ROOT = Path('/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1')
PROTOCOL = 'single-fresh-user-goal;one-ACT-line;decode_answer;native-score_answer;no-feedback;v1'
IMPORT_PID = os.getpid()
USED = False
require, sha, digest = native.require, native.sha, native.digest


def read(path):
    return native.parse_json(Path(path).read_bytes())


def regular(value, exists=True):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts
            and not any(part.is_symlink() for part in (path, *path.parents)), 'regular_absolute_path')
    require(not exists or (path.exists() and stat.S_ISREG(path.stat().st_mode)), 'regular_file_required')
    return path


def write(path, value):
    path = regular(path, exists=False)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    checksum = native._write_once(path, value)
    path.chmod(0o400)
    return checksum


def ref(path):
    return dict(path=str(regular(path)), sha256=sha(path))


def bound(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_file_reference')
    path = regular(reference['path'])
    require(sha(path) == reference['sha256'], 'bound_file_changed')
    return read(path)


def slots():
    return [dict(arm=arm, milestone=milestone, key=f'{arm}_{milestone}',
                 weight_control='step0_repeated' if arm == 'parented_frozen' else 'saved_adapter')
            for milestone in MILESTONES for arm in ARMS]


def package_binding():
    import reasoning_gym
    require(importlib.metadata.version('reasoning-gym') == PACKAGE_VERSION, 'pinned_reasoning_gym_version')
    root = Path(inspect.getfile(reasoning_gym)).parent
    inventory = {}
    for path in sorted(root.rglob('*')):
        if '__pycache__' not in path.parts and path.is_file() and path.suffix != '.pyc':
            require(not path.is_symlink(), 'regular_package_resources')
            inventory[str(path.relative_to(root))] = sha(path)
    return dict(version=PACKAGE_VERSION, inventory_sha256=digest(inventory))


def scoring_binding():
    from organism_v6 import reasoning_gym_gym as backend
    return dict(protocol=PROTOCOL, wrapper_sha256=sha(backend.__file__),
                parser_sha256=digest(inspect.getsource(parse_action)), package=package_binding())


def ledger_ids(ledger):
    from organism_v6.reasoning_gym_gym import parse_id
    output = []
    groups = [set(ledger[name + '_families']) for name in ('train', 'gate', 'exam')]
    require(all(not left & right for index, left in enumerate(groups) for right in groups[index+1:]),
            'disjoint_family_groups')
    for split, count in COUNTS.items():
        entries = ledger[split + '_set']
        require(len(entries) == count and len(set(entries)) == count, 'complete_fixed_split_panel')
        lower, upper = ledger['seed_ranges'][split]
        families = ledger['train_families' if split == 'canary' else split + '_families']
        for identifier in entries:
            family, seed = parse_id(identifier)
            require(family in families and lower <= seed < upper and not 1500000 <= seed < 1500024,
                    'held_split_only_never_R158TRAIN')
            output.append((split, identifier))
    require(len({identifier for _, identifier in output}) == 28, 'unique_fixed_tasks')
    return output


def parse_action(raw):
    require(type(raw) is str, 'response_text')
    matches = re.findall(r'^ACT:[ \t]*(.*)$', raw, flags=re.MULTILINE)
    return matches[0] if len(matches) == 1 and matches[0].strip() else None


def build_tasks(ledger_path):
    from organism_v6.reasoning_gym_gym import ReasoningGymGym, parse_id
    gym = ReasoningGymGym(families_path=str(ledger_path), strict_verifier=True)
    tasks = []
    for split, identifier in ledger_ids(read(ledger_path)):
        family, seed = parse_id(identifier)
        _, entry = gym._item(family, seed)
        messages = [dict(role='user', content=gym.episode_from_id(identifier).goal)]
        tasks.append(dict(split=split, identifier=identifier, entry=entry, messages=messages))
    return tasks


def task_hashes(tasks, scoring):
    return dict(task_sha256=digest(tasks), prompt_sha256=digest([task['messages'] for task in tasks]),
                scoring_sha256=digest(scoring))


def freeze(output):
    from organism_v6 import reasoning_gym_gym as backend
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_freezer')
    output = regular(output, exists=False)
    require(not output.exists(), 'new_sealed_freeze_directory')
    output.mkdir(mode=0o700, parents=True)
    ledger_path = Path(backend.FAMILIES_JSON)
    scoring = scoring_binding()
    tasks = build_tasks(ledger_path)
    bundle = dict(schema=SCHEMA, tasks=tasks, scoring=scoring, ledger_sha256=sha(ledger_path))
    write(output / 'TASKSET.private.json', bundle)
    receipt = dict(schema=SCHEMA, status='TASKSET_FROZEN_NO_ENROLLMENT', frozen_unix=time.time(),
                   bundle=ref(output / 'TASKSET.private.json'), ledger_sha256=sha(ledger_path),
                   counts=COUNTS, **task_hashes(tasks, scoring))
    write(output / 'FREEZE.json', receipt)
    return receipt


def plan_document(freeze_reference):
    frozen = bound(freeze_reference)
    require(frozen['schema'] == SCHEMA and frozen['status'] == 'TASKSET_FROZEN_NO_ENROLLMENT'
            and frozen['counts'] == COUNTS, 'fixed_frozen_taskset')
    return dict(schema=SCHEMA, freeze=freeze_reference, model_id=native.MODEL_ID,
                base_sha256=native.BASE_SHA256, rank=8, decoder=native.DECODER,
                slots=slots(), conditions=list(CONDITIONS), calls_per_checkpoint=CALLS,
                max_checkpoints=12, total_call_cap=CAP, physical_slots=[0, 1],
                cohort=None, parent_access=False, file_tools=False, history_shared=False,
                evaluation_to_sleep=False, evaluation_to_inbox=False, scores_gate_selection=False,
                failed_keys_retry=False, instrument='existing_reasoning_gym_fixed_split_panel',
                general_battery='NOT_SCHEDULED_SEPARATE_INSTRUMENT_EXCEEDS_THIS_BUDGET')


def validate_plan(reference):
    plan = bound(reference)
    require(plan == plan_document(plan['freeze']), 'exact_immutable_campaign_contract')
    return plan


def sealed_tasks(plan):
    from organism_v6 import reasoning_gym_gym as backend
    frozen = bound(plan['freeze'])
    bundle = bound(frozen['bundle'])
    require(bundle['schema'] == SCHEMA and bundle['ledger_sha256'] == frozen['ledger_sha256']
            == sha(backend.FAMILIES_JSON), 'unchanged_split_ledger')
    tasks, scoring = bundle['tasks'], bundle['scoring']
    require(scoring == scoring_binding(), 'unchanged_native_scoring_package')
    require(task_hashes(tasks, scoring) == {key: frozen[key] for key in
            ('task_sha256', 'prompt_sha256', 'scoring_sha256')}, 'immutable_tasks_prompts_scoring')
    require(digest(tasks) == digest(build_tasks(Path(backend.FAMILIES_JSON))), 'deterministic_fixed_task_regeneration')
    return tasks


def validate_sources(config):
    root = regular(config['source_root'], exists=False)
    require(root.resolve() == Path(__file__).resolve().parents[1], 'executing_source_root')
    required = set(native.REQUIRED_SOURCES) | {
        'gpu/orch_r159_matched_evaluation.py', 'gpu/orch_r130_benchmark_sidecar.py',
        'gpu/orch_rich_hot_node2_scan.py', 'organism_v6/reasoning_gym_gym.py',
        'organism_v6/reasoning_gym_families.json', 'organism_v6/gym_backend.py',
        'organism_v6/bootstrap_reasoning_gym.txt', 'tests/test_orch_r159_matched_evaluation.py'}
    require(required <= set(config['sources']), 'required_evaluator_closure')
    require(all(str(path.relative_to(root)) in config['sources']
                for directory in ('gpu', 'organism_v6') for path in (root / directory).rglob('*.py')),
            'complete_executing_python_closure')
    for relative, checksum in config['sources'].items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts, 'source_relative_path')
        require(sha(regular(root / path)) == checksum, 'evaluator_source_changed')


def candidate_check(config, plan):
    root = regular(config['campaign_root'], exists=False)
    require(regular(config['candidate']['path']).is_relative_to(root / 'inputs'), 'local_candidate_metadata_only')
    candidate = bound(config['candidate'])
    expected = {'schema', 'arm', 'milestone', 'cohort', 'initialized', 'capacity', 'initial_commit',
                'source_commit_path', 'manifest', 'source_custody'}
    require(set(candidate) == expected and candidate['schema'] == SCHEMA, 'exact_candidate_fields')
    arm, milestone = candidate['arm'], candidate['milestone']
    require(arm in ARMS and type(milestone) is int and milestone in MILESTONES, 'registered_slot_only')
    for name in ('cohort', 'initialized', 'capacity', 'initial_commit', 'manifest', 'source_custody'):
        require(regular(candidate[name]['path']).is_relative_to(root / 'inputs'), 'copied_metadata_not_child_files')
    cohort, initialized = bound(candidate['cohort']), bound(candidate['initialized'])
    initial = bound(candidate['initial_commit'])
    custody = bound(candidate['source_custody'])
    require(cohort['schema'] == 'R150_MATCHED_CONTINUAL_COHORT_V1'
            and set(cohort['members']) == set(ARMS) and cohort['fresh_histories'] is True
            and cohort['evaluations_gate_continuation'] is False
            and cohort['initial_optimizer_steps'] == 0
            and cohort['common']['base_sha256'] == native.BASE_SHA256, 'prospective_three_arm_cohort')
    roots = {name: Path(cohort['members'][name]['root']) for name in ARMS}
    require(len(set(roots.values())) == 3 and all(path.is_absolute() for path in roots.values())
            and all(not left.is_relative_to(right) for left in roots.values() for right in roots.values()
                    if left != right), 'distinct_original_cohort_roots')
    require(all(cohort['members'][name]['parent_enabled'] is (name != 'unparented_learning') for name in ARMS),
            'explicit_matched_parent_conditions')
    authority = bound(config['source_owner_authority'])
    require(authority['schema'] == SCHEMA and authority['status'] == 'SOURCE_OWNER_ADMITTED'
            and authority['cohort_sha256'] == candidate['cohort']['sha256']
            and authority['source_roots'] == {name: str(path) for name, path in roots.items()}
            and authority['read_end_unix'] == config['source_read_end_unix']
            and authority['source_root'] == cohort['common']['source_root'], 'exact_current_source_owner_authority')
    lifecycle = bound(authority['initializer_lifecycle'])
    require(lifecycle['service_returncode'] == 0, 'actual_successful_initializer_exit')
    initial_path = Path(cohort['initial_directory']) / 'COMMIT.json'
    require(initial['schema'] == native.NATIVE_SCHEMA and initial['base_sha256'] == native.BASE_SHA256
            and initial['optimizer_steps'] == 0 and Path(initial['adapter_path']) == initial_path.parent / 'adapter',
            'same_initial_native_contract')
    require(initialized['schema'] == cohort['schema']
            and initialized['cohort_sha256'] == candidate['cohort']['sha256']
            and initialized['checkpoint_commit_sha256'] == candidate['initial_commit']['sha256']
            and initialized['generation_calls'] == initialized['optimizer_updates'] == 0
            and initialized['initialization_validation']['status'] == 'PASS', 'successful_common_initializer')
    capacity = bound(candidate['capacity'])
    require(candidate['capacity']['sha256'] == initialized['initialization_validation']['sha256']
            and capacity['schema'] == initialized['initialization_validation']['schema'] == 'R151_MATCHED_INITIAL_CAPACITY_V1'
            and capacity['status'] == 'PASS' and capacity['state_restored'] is True
            and capacity['restoration_status'] == 'VERIFIED'
            and capacity['generation_calls'] == capacity['optimizer_updates'] == 0
            and capacity['stream_data_written'] is False and capacity['scientific_evaluation'] is False
            and not any(name in capacity for name in ('error', 'error_type', 'measurement_error',
                                                     'cleanup_errors', 'acceptance_error')),
            'actual_bound_capacity_PASS_not_summary_only')
    recovery = cohort['common'].get('initialization_source')
    if recovery is not None:
        require(initialized.get('initialization_source') == recovery, 'same_optional_initialization_source')
        for name in ('initialization_source_copy', 'initialization_commit_copy'):
            require(regular(authority[name]['path']).is_relative_to(root / 'inputs'), 'copied_recovery_metadata_only')
        source = bound(authority['initialization_source_copy'])
        donor = bound(authority['initialization_commit_copy'])
        require(authority['initialization_source_copy']['sha256'] == recovery['sha256']
                and source['schema'] == 'R158_SAVED_INITIALIZATION_SOURCE_V1'
                and authority['initialization_commit_copy']['sha256'] == source['commit']['sha256'],
                'copied_recovery_metadata_hashes_only')
        observation = initialized['observed_initial_state']
        require(initialized['recovered_initial_state_before_validation'] == observation
                and observation['checkpoint_file_hashes'] == donor['checkpoint_sha256'] == initial['checkpoint_sha256']
                and donor['schema'] == native.NATIVE_SCHEMA and donor['base_sha256'] == native.BASE_SHA256
                and donor['optimizer_steps'] == 0 and donor['adapter_state_sha256'] == initial['adapter_state_sha256'],
                'exact_restored_step0_adapter_AdamW_RNG_hashes')
    else:
        require('initialization_source' not in initialized, 'no_unbound_initializer_recovery')
    frozen = bound(plan['freeze'])
    require(frozen['frozen_unix'] < initial['created_unix'] <= initialized['initialized_unix'],
            'taskset_frozen_before_initial_checkpoint')
    manifest = bound(candidate['manifest'])
    for value in (manifest['commit_path'], manifest['adapter_path'], candidate['manifest']['path']):
        require(regular(value, exists=False).is_relative_to(root / 'inputs'), 'adapter_only_local_custody')
    checkpoint = native.verify_checkpoint(manifest, Path(candidate['manifest']['path']).parent)
    commit = read(checkpoint['commit_path'])
    expected_source = roots[arm] / 'checkpoints' / ('initial' if milestone == 0 else f'sleep_{milestone:06d}')
    require(candidate['source_commit_path'] == str(expected_source / 'COMMIT.json')
            and Path(commit['adapter_path']) == expected_source / 'adapter'
            and Path(commit['optimizer_rng_path']) == expected_source / 'optimizer_rng.pt', 'exact_source_checkpoint_slot')
    require(commit.get('experiment') == initial.get('experiment') and commit.get('experiment') is not None,
            'same_experiment_binding')
    require(type(commit['optimizer_steps']) is int and commit['optimizer_steps'] >= 0
            and initial['created_unix'] <= commit['created_unix'], 'native_checkpoint_metadata')
    if milestone == 0 or arm == 'parented_frozen':
        require(commit['adapter_files'] == initial['adapter_files']
                and commit['adapter_state_sha256'] == initial['adapter_state_sha256']
                and commit['optimizer_steps'] == 0, 'identical_step0_control_weights')
    if milestone == 0:
        require(commit['checkpoint_sha256'] == initial['checkpoint_sha256'], 'exact_initial_clone_bytes')
    else:
        require(commit['created_unix'] > initial['created_unix'], 'sleep_checkpoint_not_relabelled_initial')
    adapter_config = read(Path(checkpoint['adapter_path']) / 'adapter_config.json')
    require(adapter_config['r'] == 8 and adapter_config['lora_alpha'] == 16
            and adapter_config['peft_type'] == 'LORA'
            and set(adapter_config['target_modules']) == {'q_proj', 'k_proj', 'v_proj', 'o_proj',
                'gate_proj', 'up_proj', 'down_proj'}
            and not adapter_config.get('use_dora', False) and not adapter_config.get('use_rslora', False),
            'frozen_native_rank8_adapter')
    require(custody == dict(schema=SCHEMA, cohort_sha256=candidate['cohort']['sha256'],
            source_root=str(roots[arm]), source_commit_path=candidate['source_commit_path'],
            commit_sha256=manifest['commit_sha256'], manifest_sha256=candidate['manifest']['sha256'],
            checkpoint_boundary=milestone, source_owner_authority=config['source_owner_authority'],
            source_read_end_unix=config['source_read_end_unix'], adapter_only=True,
            optimizer_rng_read=False, history_read=False, source_written=False), 'exact_Main_bound_source_custody')
    require(time.time() < config['source_read_end_unix'], 'source_read_authority_current')
    return candidate, checkpoint


def validate_execution(config_path, go_path):
    config_path, go_path = regular(config_path), regular(go_path)
    config, go = read(config_path), read(go_path)
    require(os.environ.get('R159_MAIN_GO_SHA256') == sha(go_path), 'explicit_Main_GO_hash')
    require(go == dict(schema=SCHEMA, status='MAIN_GO', execution=ref(config_path)), 'exact_Main_GO_scope')
    fields = {'schema', 'campaign', 'campaign_root', 'candidate', 'physical', 'gpu_uuid', 'source_root',
              'sources', 'model_dir', 'python', 'python_sha256', 'hard_end_unix', 'lease_end_unix', 'source_owner_authority',
              'source_read_end_unix', 'old_terminal', 'old_terminal_identity', 'cpu_gate', 'builder',
              'node2_authority', 'service_path'}
    require(set(config) == fields and config['schema'] == SCHEMA, 'exact_execution_fields_no_eval_leak_channels')
    require(Path(config['campaign_root']) == CAMPAIGN_ROOT and config_path.is_relative_to(CAMPAIGN_ROOT / 'control')
            and not CAMPAIGN_ROOT.is_relative_to(OLD_ROOT), 'separate_new_campaign_only')
    plan = validate_plan(config['campaign'])
    validate_sources(config)
    model_dir = regular(config['model_dir'], exists=False)
    require(model_dir.is_dir() and not model_dir.is_relative_to(CAMPAIGN_ROOT)
            and not CAMPAIGN_ROOT.is_relative_to(model_dir), 'separate_local_frozen_model')
    interpreter = Path(config['python'])
    require(interpreter.is_absolute() and interpreter.resolve().is_file()
            and os.access(interpreter, os.X_OK) and sha(interpreter) == config['python_sha256'],
            'pinned_existing_interpreter_symlink_allowed')
    regular(config['service_path'])
    from gpu import orch_r130_benchmark_sidecar as sidecar
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == sidecar.HOST_SHA256, 'node2_only')
    require(type(config['physical']) is int and config['physical'] in (0, 1)
            and config['gpu_uuid'] == sidecar.DEVICES[config['physical']], 'only_node2_slots0_1')
    require(all(type(config[key]) in (int, float) and math.isfinite(config[key]) for key in
            ('hard_end_unix', 'lease_end_unix', 'source_read_end_unix')), 'finite_execution_walls')
    require(time.time() < config['hard_end_unix'] <= config['lease_end_unix'] - 21600, 'node2_six_hour_margin')
    authority = bound(config['node2_authority'])
    require(authority['schema'] == SCHEMA and authority['node'] == 'node2'
            and authority['campaign_sha256'] == config['campaign']['sha256']
            and authority['lease_end_unix'] == config['lease_end_unix']
            and authority['hard_end_unix'] == config['hard_end_unix']
            and authority['physical_slots'] == [0, 1], 'separate_node2_budget_authority')
    terminal = bound(config['old_terminal'])
    require(Path(config['old_terminal']['path']).is_relative_to(OLD_ROOT)
            and terminal['status'] == 'BOUNDED_PHASE_FINISHED', 'original_phase_terminal_required')
    identity = config['old_terminal_identity']
    try:
        current = sidecar.identity(identity['pid'])
    except (FileNotFoundError, ProcessLookupError):
        current = None
    require(current != identity, 'old_controller_must_be_gone')
    gate = bound(config['cpu_gate'])
    require(gate['status'] == 'PASS' and gate['helper_sha256'] == sha(__file__)
            and gate['test_sha256'] == config['sources']['tests/test_orch_r159_matched_evaluation.py'],
            'bound_CPU_gate')
    builder = bound(config['builder'])
    require(builder['status'] == 'CPU_AND_PROVENANCE_PASS' and builder['campaign'] == config['campaign']
            and builder['cpu_gate'] == config['cpu_gate'] and type(builder['created_unix']) in (int, float)
            and 0 < builder['created_unix'] <= time.time(), 'dated_Builder_provenance_gate')
    candidate, checkpoint = candidate_check(config, plan)
    return config, plan, candidate, checkpoint


def ledger_status(root, campaign_hash):
    root = regular(root, exists=False)
    expected = {slot['key'] for slot in slots()}
    reserved, completed, failed = {}, [], []
    for path in sorted((root / 'ledger').glob('*.RESERVED.json')):
        regular(path)
        entry = read(path)
        key = path.name.removesuffix('.RESERVED.json')
        require(key in expected and entry['key'] == key and entry['campaign_sha256'] == campaign_hash
                and entry['calls_charged'] == CALLS, 'fixed_slot_reservation')
        reserved[key] = entry
        for suffix, target in [('COMPLETE', completed), ('FAILED', failed)]:
            marker = path.with_name(key + '.' + suffix + '.json')
            if marker.exists():
                document = read(marker)
                require(document['reservation_sha256'] == sha(path), 'terminal_reservation_binding')
                target.append(key)
    for path in (root / 'ledger').glob('*.json'):
        require(any(path.name == key + '.' + suffix + '.json' for key in reserved
                    for suffix in ('RESERVED', 'COMPLETE', 'FAILED')), 'unknown_ledger_artifact_refused')
    require(not set(completed) & set(failed) and len(reserved) <= 12 and len(reserved) * CALLS <= CAP,
            'bounded_new_campaign_budget')
    cohorts = {entry['cohort_sha256'] for entry in reserved.values()}
    require(len(cohorts) <= 1, 'one_actual_successful_cohort_only')
    return dict(status='METADATA_ONLY', reserved=len(reserved), completed=len(completed), failed=len(failed),
                unresolved=len(reserved)-len(completed)-len(failed), calls_charged=len(reserved)*CALLS,
                calls_remaining=CAP-len(reserved)*CALLS, checkpoint_cap=12, call_cap=CAP,
                control_complete=set(completed) == expected, missing_slots=sorted(expected-set(completed)))


@contextmanager
def lock(path):
    regular(path, exists=False).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with Path(path).open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def reserve(config_path, config, candidate):
    root = Path(config['campaign_root'])
    key = f"{candidate['arm']}_{candidate['milestone']}"
    with lock(root / 'budget.lock'):
        status = ledger_status(root, config['campaign']['sha256'])
        require(status['reserved'] < 12 and status['calls_remaining'] >= CALLS, 'new_budget_remaining')
        path = root / 'ledger' / (key + '.RESERVED.json')
        require(not path.exists(), 'failed_or_reserved_slot_never_replayed')
        for previous in (root / 'ledger').glob('*.RESERVED.json'):
            require(read(previous)['cohort_sha256'] == candidate['cohort']['sha256'], 'no_mixed_actual_cohorts')
        write(path, dict(schema=SCHEMA, key=key, campaign_sha256=config['campaign']['sha256'],
                        execution=ref(config_path), candidate=config['candidate'], calls_charged=CALLS,
                        cohort_sha256=candidate['cohort']['sha256'], created_unix=time.time()))
    return key, path


def clean_environment(config, config_path, go_path):
    return dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=str(Path(config['campaign_root']) / 'empty_home'),
                CUDA_VISIBLE_DEVICES=config['gpu_uuid'], PYTHONPATH=config['source_root'],
                PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                R159_MAIN_GO_SHA256=sha(go_path), R159_EXECUTION_SHA256=sha(config_path))


def completion_metadata(path, execution_hash):
    terminal = read(regular(path))
    require(terminal['status'] == 'COMPLETE' and terminal['execution_sha256'] == execution_hash
            and terminal['calls'] == CALLS and terminal['parent_access'] is False
            and terminal['history_shared'] is False, 'actual_fixed_call_completion')
    names = [f'CALL_{position:04d}.{kind}.private.json' for position in range(CALLS)
             for kind in ('RESERVED', 'RAW', 'SCORE')]
    receipts = {str(Path(path).parent / name): sha(regular(Path(path).parent / name)) for name in names}
    require(digest(receipts) == terminal['receipts_sha256'], 'sealed_receipt_hash_custody')
    return dict(calls=CALLS, completion_sha256=sha(path))


def dispatch(config_path, go_path):
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config, _, candidate, _ = validate_execution(config_path, go_path)
    require(config['hard_end_unix'] - time.time() > 3615, 'full_existing_3600s_job_window')
    root = Path(config['campaign_root'])
    with lock(OLD_ROOT / f"physical{config['physical']}.lock"):
        report = sidecar.scan(config)
        if not report['clear'] or report['blocking_reasons']:
            return dict(status='DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION')
        validate_execution(config_path, go_path)
        require(config['hard_end_unix'] - time.time() > 3615, 'full_window_after_scan')
        key, claim = reserve(config_path, config, candidate)
        attempt = root / 'attempts' / key
        attempt.mkdir(mode=0o700, parents=True, exist_ok=False)
        write(attempt / 'ADMISSION.private.json', report)
        deadline = min(config['hard_end_unix'] - 15, time.time() + 3600)
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(int(deadline-time.time())) + 's',
                   config['python'], '-B', '-m', 'gpu.orch_r159_matched_evaluation', 'evaluate',
                   '--config', str(config_path), '--go', str(go_path)]
        process = None
        try:
            with (attempt / 'runner.private.log').open('x') as log:
                process = subprocess.Popen(command, cwd=attempt, env=clean_environment(config, config_path, go_path),
                                           stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                write(attempt / 'LAUNCH.json', dict(identity=sidecar.identity(process.pid), execution=ref(config_path),
                                                   reservation_sha256=sha(claim), observed_unix=time.time()))
                returncode = process.wait()
            complete = attempt / 'sealed' / 'COMPLETE.json'
            require(returncode == 0 and complete.is_file(), 'fresh_runner_complete_required')
            completion_metadata(complete, sha(config_path))
            write(root / 'ledger' / (key + '.COMPLETE.json'), dict(status='COMPLETE',
                  reservation_sha256=sha(claim), completion=ref(complete), observed_unix=time.time()))
        except BaseException:
            if process is not None and process.poll() is None:
                process.wait()
            if not (root / 'ledger' / (key + '.COMPLETE.json')).exists():
                write(root / 'ledger' / (key + '.FAILED.json'), dict(status='FAILED_NO_RETRY',
                      reservation_sha256=sha(claim), observed_unix=time.time()))
            raise
    return ledger_status(root, config['campaign']['sha256'])


def score_task(task, response):
    from organism_v6.reasoning_gym_gym import ReasoningGymGym, parse_id, decode_answer
    action = parse_action(response['raw'])
    if response['truncated'] or action is None:
        return dict(eligible=False, score=None, parse_valid=action is not None, truncated=response['truncated'])
    family, seed = parse_id(task['identifier'])
    dataset, entry = ReasoningGymGym(strict_verifier=True)._item(family, seed)
    require(digest(entry) == digest(task['entry']), 'immutable_generated_entry')
    score = float(dataset.score_answer(answer=decode_answer(action), entry=entry))
    require(math.isfinite(score) and 0 <= score <= 1, 'native_verifier_valid_score')
    return dict(eligible=True, score=score, parse_valid=True, truncated=False)


def gym_selftest(freeze_path, output):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_sealed_selftest')
    output = regular(output, exists=False)
    require(not output.exists(), 'fresh_selftest_output')
    output.mkdir(mode=0o700, parents=True)
    try:
        plan = plan_document(ref(freeze_path))
        tasks = sealed_tasks(plan)
        require(parse_action('ACT: synthetic smoke response') == 'synthetic smoke response'
                and parse_action('ACT: first\nACT: second') is None, 'actual_protocol_parser_smoke')
        for position, task in enumerate(tasks):
            response = dict(raw='ACT: synthetic CPU verifier smoke', terminal=True, truncated=False)
            result = score_task(task, response)
            write(output / f'VERIFIER_{position:04d}.private.json', dict(result=result))
        require(digest(sealed_tasks(plan)) == digest(tasks), 'stable_regenerated_28_tasks')
        receipt = dict(status='PASS', task_count=28, verifier_invocations=28, model_calls=0,
                       checkpoints_enrolled=0, CUDA_visible=False, scores_published=False,
                       freeze=ref(freeze_path), helper_sha256=sha(__file__), observed_unix=time.time())
        write(output / 'CPU_COMPLETE.json', receipt)
        return receipt
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED', error_type=type(error).__name__, model_calls=0))
        raise


def evaluate(config_path, go_path):
    global USED
    require(os.getpid() == IMPORT_PID and not USED, 'one_checkpoint_per_fresh_process')
    require(os.environ.get('R159_EXECUTION_SHA256') == sha(config_path), 'fresh_dispatch_execution_binding')
    config, plan, candidate, checkpoint = validate_execution(config_path, go_path)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['gpu_uuid'], 'one_bound_visible_device')
    root = Path(config['campaign_root'])
    key = f"{candidate['arm']}_{candidate['milestone']}"
    claim = read(root / 'ledger' / (key + '.RESERVED.json'))
    require(claim['execution'] == ref(config_path) and claim['candidate'] == config['candidate'], 'charged_exact_execution')
    output = root / 'attempts' / key / 'sealed'
    require(not output.exists(), 'new_private_evaluator_directory')
    output.mkdir(mode=0o700, parents=True)
    USED = True
    tasks = sealed_tasks(plan)
    configuration_hash = sha(config_path)
    immutable_references = [config['candidate'], config['campaign'], plan['freeze'],
                            candidate['manifest'], candidate['source_custody'], candidate['cohort'],
                            candidate['initial_commit'], candidate['initialized'], candidate['capacity'],
                            config['source_owner_authority']]

    def check(label):
        require(time.time() < config['hard_end_unix'] and sha(config_path) == configuration_hash,
                'evaluation_wall_and_immutable_config')
        for reference in immutable_references:
            require(sha(regular(reference['path'])) == reference['sha256'], 'immutable_evaluation_input')

    engine_plan = dict(model_dir=config['model_dir'], gpu_uuid=config['gpu_uuid'])
    engine = None
    count = 0
    receipts = {}
    try:
        check('load')
        engine = native._load_engine(engine_plan, checkpoint, check)
        before = native._snapshot(engine, engine_plan, checkpoint)
        write(output / 'BEFORE.private.json', before)
        from gpu.orch_r107_capability_run import readonly_condition, ordered_conditions
        for position, task in enumerate(tasks):
            for condition in ordered_conditions(position):
                check('call')
                require(count < CALLS, 'fixed_per_checkpoint_call_cap')
                messages = deepcopy(task['messages'])
                require(len(messages) == 1 and messages[0]['role'] == 'user', 'empty_context_one_fixed_item')
                prefix = output / f'CALL_{count:04d}'
                reservation_path = str(prefix) + '.RESERVED.private.json'
                receipts[reservation_path] = write(reservation_path, dict(position=position, condition=condition))
                count += 1
                tokens = engine.tokenizer.apply_chat_template(messages, tokenize=True,
                            add_generation_prompt=True, return_dict=False)
                with readonly_condition(engine.model, condition):
                    native._require_readonly(engine.model, condition)
                    response = engine.generate(messages, max_new_tokens=native.MAX_NEW_TOKENS)
                raw_path = str(prefix) + '.RAW.private.json'
                receipts[raw_path] = write(raw_path, dict(task=task, condition=condition, response=response))
                require(messages == task['messages'], 'no_cross_item_context_mutation')
                native._validate_response(response, task['messages'], len(tokens), engine.tokenizer.eos_token_id)
                score_path = str(prefix) + '.SCORE.private.json'
                receipts[score_path] = write(score_path, score_task(task, response))
        after = native._snapshot(engine, engine_plan, checkpoint)
        require(before == after and count == CALLS, 'immutable_model_and_all_calls')
        validate_execution(config_path, go_path)
        require(sealed_tasks(plan) == tasks, 'taskset_unchanged_after_evaluation')
        require(all(sha(path) == checksum for path, checksum in receipts.items()), 'immutable_sealed_receipts')
        write(output / 'AFTER.private.json', after)
        write(output / 'COMPLETE.json', dict(status='COMPLETE', calls=count, execution_sha256=configuration_hash,
              checkpoint_commit_sha256=checkpoint['commit_sha256'], parent_access=False, history_shared=False,
              receipts_sha256=digest(receipts),
              completed_unix=time.time()))
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED_NO_RETRY', error_type=type(error).__name__, calls=count))
        raise
    return dict(status='COMPLETE', calls=count)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'gym-selftest', 'plan', 'validate', 'dispatch', 'evaluate', 'status'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--go', type=Path)
    parser.add_argument('--plan', type=Path)
    arguments = parser.parse_args(argv)
    try:
        if arguments.action == 'freeze':
            receipt = freeze(arguments.output)
            result = {key: receipt[key] for key in ('status', 'counts', 'frozen_unix', 'task_sha256',
                                                   'prompt_sha256', 'scoring_sha256')}
            result['freeze'] = ref(arguments.output / 'FREEZE.json')
        elif arguments.action == 'gym-selftest':
            result = gym_selftest(arguments.freeze, arguments.output)
        elif arguments.action == 'plan':
            write(arguments.output, plan_document(ref(arguments.freeze)))
            result = dict(status='IMMUTABLE_PLAN_NO_ENROLLMENT', plan=ref(arguments.output),
                          call_cap=CAP, checkpoint_cap=12)
        elif arguments.action == 'status':
            result = ledger_status(CAMPAIGN_ROOT, sha(arguments.plan))
        elif arguments.action == 'validate':
            validate_execution(arguments.config, arguments.go)
            result = dict(status='PASS_NO_GPU')
        elif arguments.action == 'dispatch':
            result = dispatch(arguments.config, arguments.go)
        else:
            result = evaluate(arguments.config, arguments.go)
        print(json.dumps(result, sort_keys=True))
        return 0
    except BaseException:
        print(json.dumps(dict(status='REFUSED_OR_FAILED', details='PRIVATE_NO_AUTOMATIC_RETRY')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
