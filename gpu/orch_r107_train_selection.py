"""CPU-only prospective BASE TRAIN selection; never exports supervision or calls models."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re


SCHEMA = 'R107_BASE_TRAIN_SELECTION_PROPOSAL_V1'
ROOT = '/localhome/local-rohing/orch_rich_hot_node3_20260915_base107_refill1536'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
PHASE = 'R107_GENUINE_BASE_REASONING_FIRST_1536_V1'
MASTERS = tuple(f'ORCH-FULL-RICH-20260914-TRAIN-V1-WORLD-{index}' for index in range(8))
CAPABILITY_FAMILIES = ('code', 'math', 'toolcall', 'concise_instruction')
ARMS = {4: 'FROZEN_BASE_REASONING_PERSISTENCE', 5: 'FROZEN_BASE_FUNCTIONAL_ALLOCATION'}
PINS = {
    'PROTOCOL.json': '073f1d08729145aa61d2a18245993b2f819d874b5eb8b978149bf87900030453',
    'SOURCE_SHA256.json': '8958c6e230d10927160345a04bc7976eecf9dae78d371b066e23a1c168a41ad7',
    'COHORT.json': 'dd058367b97f3f6a5d9b51deb0ac8700c2e2ea6c375cc5ebb48373b09fe72c6e',
    'SOURCE_EVENTS.json': '706c33bd8a6788a67798f32c8f28b94757b7b069db9dd719bf3c9e79373f8c74',
    'TASKS.json': 'b588a43c2abfbbdaaee5f90dd18118fe933468381d804aabc0336193e82726c6',
    'BASE_CPU_IDENTITY.json': 'cc3c6832e407cb4cf6c20b7e7af793400c03df7e41e8708742e2ff4b6139d5d1',
    'shard4/ACTOR_READY.json': '294ccd327833fb11f6e2e0af1fa4e1e2032addc7fce26a9a5c2bdcc876113723',
    'shard5/ACTOR_READY.json': 'e64a0e58ff0590f1d839368eb46840e084921134ff34077f1602928c6e4f528a',
}
PREVIOUSLY_AUDITED = (
    '6a8b28c00b384201254efcd6c60531d8e7d3f20f33ac24c39cc87e9d3bf0ffa5',
    'c806ecb2b1c423baf86b151bc76b165e7b3e0f5e6a124fad25b95889eb7d8bcb',
    '20e0b5e9c6fc619917c9ebf305bc988ca2cecca7417aa1cdf4a1c5ed42870304',
    '6a33b46e0d2dc3a934b8cb2b705fced1d3dd556500c2b249ec123420dcdc2748',
    '990c8320eb09537e323c823b4037d12af37a0df37a2f74b280b18e8f2908ec15',
    '253dd6d523ae586188f380348e3eccffb3ced6f0ba3f6f102b4fce2da8ecbf5d',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def protocol():
    return dict(schema=SCHEMA, state='CPU_PROPOSAL_NOT_ALLOCATED', source_root=ROOT,
        source_purpose='SELF_GENERATED_BASE_TRAIN_EPISODES', source_phase=PHASE,
        base_sha256=BASE, adapter_state=None, source_pins=PINS,
        allowed_world_masters=list(MASTERS), allowed_family='route',
        contamination_family='EXACT_TRAIN_WORLD_MASTER_ALL_DISPLAY_DESCENDANTS',
        held_policy='DENY_EVERY_WORLD_OUTSIDE_EXACT_TRAIN_ALLOWLIST',
        excluded_capability_families=list(CAPABILITY_FAMILIES),
        excluded_capability_id_prefix='R107_',
        excluded_sources=['L2_PARENTING', 'TEACHER', 'CHECKPOINT_DERIVED', 'HELD_READOUT', 'FIXED_CAPABILITY'],
        context_lineage='EXISTING_TRAIN_CHILD_EVENTS_CONTEXT_ONLY_NOT_BASE_AUTHORED_TARGETS',
        previously_audited_episode_sha256s=list(PREVIOUSLY_AUDITED),
        selection_order='FIRST_8_COMPLETED_UNAUDITED_PER_ARM_BY_FINISH_THEN_TASK_ID',
        max_episodes=16, max_episodes_per_arm=8, max_calls=96,
        semantic_axes=['functional_change', 'ordinary_anchor', 'grounding'],
        no_outcome_or_branch_count_or_form_gate=True, annotation_before_fit_required=True,
        missing_annotation='UNKNOWN_NOT_NEGATIVE_SUPERVISION', causal_effect='UNMEASURED',
        semantic_pass_is='AUTHOR_SUPPORTED_NOT_INDEPENDENT_CERTIFICATION',
        functional_PASS_requires='GROUNDED_REALIZATION_AND_OBSERVED_CHANGED_REASONING_OR_ACTION_NOT_ANNOUNCEMENT',
        ordinary_anchor_PASS_requires='USEFUL_GROUNDED_REASONING_WITHOUT_FORCED_REALIZATION',
        future_compile_gate='SEPARATE_ALLOCATION_ENCODER_CONTEXT_MASK_CHECKS_NO_CROPPING',
        raw_output=False, trainingAllowed=False, labels_exported=False,
        provider_calls=0, generation_calls=0, fit_calls=0, live_allocation_required=True)


def check_actor(actor):
    require(actor.get('actual_base_sha256') == BASE and actor.get('adapter_state') is None
            and actor.get('loading_mode') == 'DIRECT_BASE_NO_ADAPTER'
            and actor.get('phase_version') == PHASE, 'genuine_base_identity_required')
    flags = actor['no_adapter']
    require(all(flags.get(key) == 0 for key in ('adapter_parameter_count', 'peft_wrapper_count',
                                               'trainable_parameter_count'))
            and flags.get('hf_peft_config_loaded') is False, 'no_adapter_or_trainable_parameters')


def check_lineage(row):
    require(row.get('source_root') == ROOT and row.get('source_phase') == PHASE,
            'registered_generation_root_and_purpose_only')
    require(row.get('source_purpose') == 'SELF_GENERATED_BASE_TRAIN_EPISODES'
            and all(row.get(key) is False for key in ('parenting_experience', 'teacher_target',
                                                     'held_readout', 'checkpoint_derived')),
            'no_L2_teacher_held_checkpoint_sources')
    require(row.get('family') == 'route' and row.get('split') == 'TRAIN_SCREEN_NO_FIT'
            and row.get('world_master') in MASTERS, 'exact_TRAIN_family_world_allowlist')
    require(row.get('task_id', '').startswith('route-train-display-')
            and not row['task_id'].startswith('R107_'), 'fixed_capability_tasks_excluded')
    require(row.get('source_state') == BASE and row.get('adapter_state') is None,
            'BASE_targets_not37ec_or_checkpoint')


def public_lines(calls):
    lines, previous_messages = [], []
    for turn, call in enumerate(calls):
        messages = call['messages']
        require(messages[:len(previous_messages)] == previous_messages, 'observed_conversation_continuity')
        fresh = messages[len(previous_messages):]
        require(all(message['role'] in ('system', 'user') for message in fresh), 'no_invented_assistant_history')
        for message in fresh:
            if message['role'] == 'user':
                for text in message['content'].splitlines(keepends=True):
                    lines.append(dict(line_id=len(lines) + 1, turn=turn, kind='PUBLIC_OBSERVATION', text=text))
        response = call['response']['raw']
        for text in response.splitlines(keepends=True):
            lines.append(dict(line_id=len(lines) + 1, turn=turn, kind='SELF_GENERATED', text=text))
        previous_messages = deepcopy(messages) + [dict(role='assistant', content=response)]
    return lines


def bind_episode(episode, calls, reference, roster, world):
    check_lineage(reference)
    require(episode['world'] == world and world['master'] == reference['world_master'], 'whole_world_family_binding')
    require(episode['task'] == roster['task'] and episode['task_id'] == roster['task_id']
            and episode['task_id'] == 'route-train-display-' + digest(episode['task']), 'exact_roster_task_binding')
    require(episode['phase_version'] == PHASE and episode['semantic_status'] == 'UNREVIEWED'
            and episode['admitted'] is False and episode['trainingAllowed'] is False, 'preserve_original_labels')
    require(0 < len(calls) <= 6 and len(calls) == episode['actor_calls'] == len(episode['captures']),
            'complete_bounded_episode_required')
    for turn, call in enumerate(calls):
        capture = episode['captures'][turn]
        require(call['task_id'] == episode['task_id'] and call['family'] == 'route'
                and call['source_state'] == BASE and call['adapter_state'] is None
                and call['phase_version'] == PHASE and call['arm'] == ARMS[reference['index']]
                and call['physical_index'] == reference['index'], 'per_call_native_source_binding')
        require(call['source_events_sha256'] == PINS['SOURCE_EVENTS.json'], 'TRAIN_context_lineage_bound')
        require(call['response'] == capture['response'] and call['messages'] == capture['messages']
                and call['response']['messages'] == call['messages'], 'exact_CALL_episode_join')
        require(call['semantic_status'] == 'UNREVIEWED' and call['admitted'] is False
                and call['trainingAllowed'] is False, 'original_call_labels_preserved')
    lines = public_lines(calls)
    return dict(reference=reference, lines=lines, lines_sha256=digest(lines),
        mechanical=dict(truncated_calls=sum(call['response']['truncated'] for call in calls),
            nonterminal_calls=sum(not call['response']['terminal'] for call in calls),
            generated_content_tokens=sum(call['generated_tokens'] for call in calls),
            action_parse_failures=sum(capture['command'] is None for capture in episode['captures'])),
        outcomes_projected=False, hidden_world_projected=False, teacher_steering_projected=False)


def freeze(documents, snapshot_exclusions=()):
    for document in documents:
        check_lineage(document['reference'])
        require(document['lines_sha256'] == digest(document['lines']), 'actual_public_line_hash_binding')
    selected = []
    for index in ARMS:
        eligible = [doc for doc in documents if doc['reference']['index'] == index
                    and doc['reference']['episode_sha256'] not in PREVIOUSLY_AUDITED]
        eligible.sort(key=lambda doc: (doc['reference']['finished_unix'], doc['reference']['task_id']))
        selected.extend(eligible[:8])
    require(selected and len({doc['reference']['episode_sha256'] for doc in selected}) == len(selected),
            'unique_nonempty_prospective_episode_inventory')
    require(sum(len(doc['reference']['calls']) for doc in selected) <= 96, 'bounded_existing_calls_only')
    rows = [dict(reference=doc['reference'], lines_sha256=doc['lines_sha256'], mechanical=doc['mechanical'])
            for doc in selected]
    return dict(schema=SCHEMA, protocol=protocol(), protocol_sha256=digest(protocol()), rows=rows,
        snapshot_exclusions=list(snapshot_exclusions),
        annotations_applied=False, source_calls_are_existing=True, raw_embedded=False,
        trainingAllowed=False, no_outcome_based_ordering=True)


def evidence(lines, selectors, kinds, required=False):
    require(isinstance(selectors, list) and (selectors or not required), 'bound_evidence_required')
    inventory = {line['line_id']: line for line in lines}
    spans = []
    for selected in selectors:
        require(set(selected) == {'line_id', 'start', 'end'}
                and all(type(value) is int for value in selected.values()), 'exact_span_coordinates')
        line = inventory.get(selected['line_id'])
        require(line is not None and line['kind'] in kinds, 'evidence_visibility_and_authorship')
        require(0 <= selected['start'] < selected['end'] <= len(line['text']), 'literal_span_bounds')
        spans.append(dict(selected, kind=line['kind'], turn=line['turn'],
            text_sha256=hashlib.sha256(line['text'][selected['start']:selected['end']].encode()).hexdigest()))
    require(len({(span['line_id'], span['start'], span['end']) for span in spans}) == len(spans),
            'duplicate_evidence_coordinates')
    return spans


def precedes(first, second):
    return max((span['line_id'], span['end']) for span in first) <= min(
        (span['line_id'], span['start']) for span in second)


def evaluate(document, annotation, registration_sha256):
    reference = document['reference']
    output = dict(episode_sha256=reference['episode_sha256'], task_id=reference['task_id'],
        contamination_family=reference['world_master'], source_reference=reference,
        original_semantic_status='UNREVIEWED', original_admitted=False,
        selection_tag='UNKNOWN', functional_status='UNKNOWN', anchor_status='UNKNOWN',
        grounding_status='UNKNOWN', supervision_status='NONE', trainingAllowed=False,
        labels_exported=False, causal_effect='UNMEASURED', mechanical=document['mechanical'],
        source_line_sha256=document['lines_sha256'], annotation_sha256=None)
    if annotation is None:
        return output
    require(set(annotation) == {'episode_sha256', 'registration_sha256', 'lines_sha256', 'reviewer',
        'full_episode_read', 'outcome_used', 'functional_change', 'ordinary_anchor', 'grounding'},
        'prospective_annotation_contract_no_branch_or_outcome_fields')
    require(annotation['episode_sha256'] == reference['episode_sha256']
            and annotation['registration_sha256'] == registration_sha256
            and annotation['lines_sha256'] == document['lines_sha256'], 'exact_prospective_review_binding')
    require(isinstance(annotation['reviewer'], str) and annotation['reviewer'].strip()
            and annotation['full_episode_read'] is True and annotation['outcome_used'] is False,
            'full_public_episode_author_review_not_outcome_selection')
    bound = {}
    for name, fields in (
            ('functional_change', ('prior', 'observation', 'realization', 'continuation')),
            ('ordinary_anchor', ('observation', 'reasoning')),
            ('grounding', ('evidence',))):
        axis = annotation[name]
        require(set(axis) == {'status', 'reason', *fields} and axis['status'] in ('PASS', 'FAIL', 'UNKNOWN')
                and isinstance(axis['reason'], str) and axis['reason'].strip(), 'explicit_semantic_axis')
        bound[name] = dict(status=axis['status'], reason=axis['reason'])
        for field in fields:
            kinds = ('PUBLIC_OBSERVATION',) if field == 'observation' else (
                ('PUBLIC_OBSERVATION', 'SELF_GENERATED') if field == 'evidence' else ('SELF_GENERATED',))
            bound[name][field] = evidence(document['lines'], axis[field], kinds,
                required=axis['status'] == 'PASS' or (name == 'grounding' and axis['status'] == 'FAIL'))
    functional, anchor, grounding = (bound[name] for name in ('functional_change', 'ordinary_anchor', 'grounding'))
    if functional['status'] == 'PASS':
        require(precedes(functional['prior'], functional['realization'])
                and precedes(functional['observation'], functional['realization'])
                and precedes(functional['realization'], functional['continuation']),
                'observed_realization_followed_by_changed_continuation')
    if anchor['status'] == 'PASS':
        require(precedes(anchor['observation'], anchor['reasoning']), 'ordinary_anchor_after_available_evidence')
    if grounding['status'] == 'PASS' and functional['status'] == 'PASS':
        output['selection_tag'] = 'FUNCTIONAL_CHANGE_CANDIDATE'
    elif grounding['status'] == 'PASS' and anchor['status'] == 'PASS':
        output['selection_tag'] = 'ORDINARY_ANCHOR_CANDIDATE'
    elif grounding['status'] == 'FAIL' or (functional['status'] == anchor['status'] == 'FAIL'):
        output['selection_tag'] = 'FAILED'
    output.update(functional_status=functional['status'], anchor_status=anchor['status'],
        grounding_status=grounding['status'], author_measurements=bound,
        annotation_sha256=digest(annotation), reviewer=annotation['reviewer'],
        failed_is_not_negative_supervision=True, author_supported_not_independent=True)
    return output


def select(registration, documents, annotations):
    require(registration['schema'] == SCHEMA and registration['protocol'] == protocol()
            and registration['protocol_sha256'] == digest(protocol()), 'frozen_proposal_protocol')
    bound = {doc['reference']['episode_sha256']: doc for doc in documents}
    expected = {row['reference']['episode_sha256'] for row in registration['rows']}
    require(0 < len(expected) == len(registration['rows']) <= 16
            and all(sum(row['reference']['index'] == index for row in registration['rows']) <= 8 for index in ARMS)
            and all(row['reference']['index'] in ARMS for row in registration['rows'])
            and sum(len(row['reference']['calls']) for row in registration['rows']) <= 96,
            'frozen_episode_and_call_caps_no_duplicates')
    require(set(annotations) <= expected, 'no_unregistered_or_old_review')
    outputs = []
    for row in registration['rows']:
        key = row['reference']['episode_sha256']
        require(key in bound and all(bound[key][field] == row[field]
            for field in ('reference', 'lines_sha256', 'mechanical')), 'immutable_episode_snapshot')
        require(bound[key]['lines_sha256'] == digest(bound[key]['lines']), 'actual_public_line_hash_binding')
        check_lineage(row['reference'])
        outputs.append(evaluate(bound[key], annotations.get(key), digest(registration)))
    return dict(schema=SCHEMA, registration_sha256=digest(registration), rows=outputs,
        selection_counts=dict(Counter(row['selection_tag'] for row in outputs)),
        denominator_episodes=len(outputs), reviewed_episodes=len(annotations),
        episode_display_variants_not_independent_worlds=True,
        distinct_world_families=len({row['contamination_family'] for row in outputs}),
        supervision_rows=0, trainingAllowed=False, labels_exported=False,
        calls=0, fits=0, raw_embedded=False, allocation_state='CPU_PROPOSAL_ONLY')


def native_documents(root, snapshot_exclusions=None):
    snapshot_exclusions = [] if snapshot_exclusions is None else snapshot_exclusions
    require(root.resolve() == Path(ROOT) and not root.is_symlink(), 'native_allowlisted_root_only')
    for name, expected in PINS.items():
        require(sha(root / name) == expected, 'immutable_source_pin:' + name)
    cohort, roster = read(root / 'COHORT.json'), read(root / 'TASKS.json')
    require(cohort['split'] == 'TRAIN_SCREEN_NO_FIT'
            and tuple(world['master'] for world in cohort['worlds']) == MASTERS, 'exact_TRAIN_cohort')
    task_map = {row['task_id']: row for row in roster['tasks']}
    documents = []
    for index in ARMS:
        check_actor(read(root / f'shard{index}/ACTOR_READY.json'))
        shard = root / f'shard{index}'
        call_map = {}
        for path in sorted(shard.glob('CALL_[0-9][0-9][0-9][0-9].json')):
            call = read(path)
            call_map.setdefault(call['episode_receipt'], []).append((path, call))
        for path in sorted(shard.glob('EPISODE_*.json')):
            require(re.fullmatch(r'EPISODE_\d+_\d+\.json', path.name), 'exact_episode_filename')
            episode = read(path)
            pairs = call_map.get(path.name, [])
            if not pairs or len(pairs) != episode['actor_calls']:
                snapshot_exclusions.append(dict(path=str(path), sha256=sha(path),
                    tag='UNKNOWN_INCOMPLETE_CALL_CAPTURE_NOT_SUPERVISION',
                    captured_calls=len(pairs), episode_actor_calls=episode['actor_calls']))
                continue
            task = task_map[episode['task_id']]
            require(task['index'] == index, 'exact_arm_roster')
            reference = dict(source_root=ROOT, source_phase=PHASE,
                source_purpose='SELF_GENERATED_BASE_TRAIN_EPISODES',
                parenting_experience=False, teacher_target=False, held_readout=False, checkpoint_derived=False,
                family='route', split=cohort['split'], world_master=episode['world']['master'],
                task_id=episode['task_id'], source_state=BASE, adapter_state=None, index=index,
                episode_path=str(path), episode_sha256=sha(path),
                finished_unix=max(call['finished_unix'] for _, call in pairs),
                calls=[dict(path=str(call_path), sha256=sha(call_path),
                    raw_sha256=hashlib.sha256(call['response']['raw'].encode()).hexdigest(),
                    prompt_sha256=digest(call['messages']), global_call=call['global_call']) for call_path, call in pairs])
            documents.append(bind_episode(episode, [call for _, call in pairs], reference,
                task, cohort['worlds'][task['world_index']]))
    return documents


def write_new(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('freeze', 'select'))
    parser.add_argument('--source-root', type=Path, default=Path(ROOT))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--registration', type=Path)
    parser.add_argument('--annotations', type=Path)
    args = parser.parse_args()
    require(args.output.resolve().is_relative_to(Path('/localhome/local-rohing'))
            and not args.output.resolve().is_relative_to(Path(ROOT)), 'distinct_native_proposal_output_only')
    snapshot_exclusions = []
    documents = native_documents(args.source_root, snapshot_exclusions)
    if args.mode == 'freeze':
        require(args.registration is None and args.annotations is None, 'freeze_before_annotations')
        result = freeze(documents, snapshot_exclusions)
    else:
        require(args.registration is not None, 'explicit_frozen_registration')
        result = select(read(args.registration), documents, read(args.annotations) if args.annotations else {})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_new(args.output, result)
    print(json.dumps(dict(path=str(args.output), sha256=sha(args.output),
        rows=len(result['rows']), raw_embedded=False, trainingAllowed=False, calls=0)))


if __name__ == '__main__':
    main()
