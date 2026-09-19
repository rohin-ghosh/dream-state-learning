"""Finite matched-cohort identities and source-bound TRAIN-only hook contract."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


SCHEMA = 'R233_MATCHED_DIAGNOSTIC_V1'
LEASE_END = 1789927200
HARD_END = LEASE_END - 21600
SLEEPS = 8
ARMS = {
    'guided-learn': dict(physical=0, gpu_uuid='GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
        pci='0000:4f:00.0', guided=True, weight_updates=True),
    'guided-frozen': dict(physical=3, gpu_uuid='GPU-d23c9369-39cf-51fd-833e-13292f173006',
        pci='0000:57:00.0', guided=True, weight_updates=False),
    'unparented-learn': dict(physical=4, gpu_uuid='GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d',
        pci='0000:ce:00.0', guided=False, weight_updates=True),
}
MAIN_FACTS = ('This is a finite diagnostic campaign. Only delivered TRAIN inputs and recorded '
    'observations are evidence. No heldout evaluation is supplied to this conversation. '
    'Respond to the current environment input; do not invent tool execution or feedback.')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fresh_birth(original, deadline=HARD_END):
    require(original['kind'] == 'COMMITTED' and original['document']['kind'] == 'BIRTH', 'original_birth_only')
    require(original['sha256'] == digest({key: value for key, value in original.items() if key != 'sha256'}),
        'original_birth_record_hash')
    document = deepcopy(original['document'])
    saved = document['state']
    state = saved['state']
    require(saved['sha256'] == digest(state), 'original_birth_state_hash')
    require(not state['rows'] and not state['sleep_receipts'] and state['pending'] is None
        and state['sleep_frontier'] == 0, 'unlearned_unadvanced_birth_only')
    require(state['context_limit'] == 4096 and state['segment_tokens'] == 512, 'exact_initial_context')
    require(deadline == HARD_END, 'fixed_existing_node5_window')
    state['deadline_unix'] = deadline
    saved['sha256'] = digest(state)
    return document


def plan_for(original, arm, root, *, main=None):
    require(arm in ARMS, 'declared_arm_only')
    root = Path(root)
    require(root.is_absolute(), 'absolute_new_receiving_root')
    require('post_recovery_matched_cohort_runtime_20260918' in root.parts, 'new_diagnostic_root_only')
    require(original['learn_row_policy'] == original['think_act_learn']['learn_row_policy']
        == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'R227_no_semantic_exclusions')
    plan = deepcopy(original)
    treatment = ARMS[arm]
    plan.update(root=str(root / 'arms' / arm / 'raw'), source_root=str(root / 'source'),
        anchors=str(root / 'common/anchors'), physical=treatment['physical'], gpu_uuid=treatment['gpu_uuid'],
        max_sleeps=SLEEPS, hard_end_unix=HARD_END, lease_end_unix=LEASE_END)
    plan.pop('authorized_wall_extension', None)
    plan['startup_context']['path'] = str(root / 'source/context/BIRTH_R231.txt')
    plan['think_act_learn']['cpu_gate_root'] = str(root / 'arms' / arm)
    plan['think_act_learn']['environment_facts'] = (main or {}).get('environment_facts', MAIN_FACTS)
    plan['cohort'] = dict(schema=SCHEMA, arm=arm, **treatment, sleeps=SLEEPS,
        main_configured=main is not None, main=deepcopy(main),
        eval_capture='ADAPTER_ONLY_NO_EVALUATION_IN_TRAIN_PROCESS',
        original_birth_deadline_only_rebound=True, original_lives_untouched=True)
    return plan


def validate_treatment(plan):
    cohort = plan['cohort']
    require(cohort['schema'] == SCHEMA and cohort['arm'] in ARMS, 'known_diagnostic_arm')
    require(all(cohort[key] == value for key, value in ARMS[cohort['arm']].items()), 'exact_arm_treatment')
    require(plan['physical'] == cohort['physical'] and plan['gpu_uuid'] == cohort['gpu_uuid'], 'exact_arm_device')
    require(plan['physical'] in (0, 3, 4), 'protected_devices_never_selected')
    require(plan['max_sleeps'] == cohort['sleeps'] == SLEEPS, 'finite_eight_sleep_campaign')
    require(plan['hard_end_unix'] == HARD_END and plan['lease_end_unix'] == LEASE_END, 'no_lease_extension')
    require(plan['context_limit'] == 4096 and plan['segment_tokens'] == 512, 'same_original_context')
    for scope in (plan, plan['think_act_learn']):
        require(scope.get('learn_row_policy') == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1', 'R227_required')
        require(not set(scope).intersection(('code_target_filter', 'learn_review_filter', 'prose_target_filter',
            'content_target_filter', 'question_target_filter', 'fabricated_speaker_filter')), 'no_semantic_filter_fields')


def validate_main(main, source):
    require(type(main) is dict and set(main) == {'schema', 'module', 'module_sha256', 'environment_facts', 'assets'},
        'exact_main_TRAIN_config')
    require(main['schema'] == 'MATCHED_COHORT_TRAIN_INTERFACE_V1'
        and main['module'] == 'gpu.cohort_train_interface', 'fixed_TRAIN_module')
    require(type(main['environment_facts']) is str and 0 < len(main['environment_facts'].encode()) <= 2048,
        'bounded_common_environment_facts')
    require(sha(Path(source) / 'gpu/cohort_train_interface.py') == main['module_sha256'], 'pinned_MAIN_TRAIN_module')
    require(type(main['assets']) is dict, 'explicit_TRAIN_asset_hashes')
    for name, expected in main['assets'].items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'train_assets',
            'TRAIN_assets_only')
        target = Path(source) / path
        require(target.resolve() == target and sha(target) == expected, 'pinned_TRAIN_asset')


def bound_events(values, *, actor, cycle, segment):
    from organism_v6.orch_r124_train_history import TrainEvent
    require(type(values) is list and len(values) <= 8, 'bounded_input_list')
    result = []
    for position, envelope in enumerate(values):
        require(type(envelope) is dict and set(envelope) == {'document', 'sha256'}, 'source_bound_envelope')
        document = envelope['document']
        require(type(document) is dict and set(document) == {'schema', 'split', 'source_id', 'text'},
            'TRAIN_document_fields_no_scores_or_state')
        require(document['schema'] == 'MATCHED_COHORT_TRAIN_SOURCE_V1' and document['split'] == 'TRAIN',
            'TRAIN_sources_only')
        require(envelope['sha256'] == digest(document), 'source_document_hash')
        require(type(document['source_id']) is str and 0 < len(document['source_id']) <= 256
            and type(document['text']) is str and 0 < len(document['text'].encode()) <= 16384, 'bounded_source_text')
        identifier = 'cohort:' + digest([actor, cycle, segment, position, envelope['sha256']])
        result.append(TrainEvent(event_id=identifier, actor=actor, text=document['text'], split='TRAIN',
            phase='experience' if actor == 'parent' else 'feedback', episode_id=f'cohort-sleep-{cycle}',
            source_id=document['source_id'], source_sha256=envelope['sha256'], origin='TRAIN_COLLECTION'))
    return result
