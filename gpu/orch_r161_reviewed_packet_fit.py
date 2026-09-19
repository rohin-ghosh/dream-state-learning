"""Bounded, explicitly injected reviewed-packet fitting; no native sleep or launcher."""

from copy import deepcopy
from dataclasses import asdict, dataclass
import fcntl
import inspect
import os
from pathlib import Path
import time

from gpu import orch_r125_continual_native as native
from gpu import orch_r144_sleep_targets as targets
from gpu import orch_r159_train_capture as capture
from gpu.astra_pchain2_native import EncodedRow
from gpu.orch_r108_guided_native import validate_anchor_inventory


SCHEMA = 'R161_REVIEWED_PACKET_FIT_V1'
BATCH_AUTHORIZATION_SCHEMA = 'R161_BATCH_EVIDENCE_AUTHORITY_V1'
DYNAMIC = 'DYNAMIC_BATCH_V1'
CONTRACT = 'EXACT_ENCODED_BATCH_075_4X00625_NEW16_PREVIOUS1_V1'
NATIVE_EXECUTOR_CLASS = 'gpu.orch_r161_native_executor.NativeExecutor'
REQUIRED_SOURCES = (Path(__file__), Path(capture.__file__), Path(capture.eligibility.__file__),
                    Path(native.__file__), Path(targets.__file__),
                    Path(inspect.getsourcefile(validate_anchor_inventory)),
                    Path(inspect.getsourcefile(EncodedRow)))
require = capture.require
digest = native.digest


@dataclass(frozen=True)
class Limits:
    max_candidates: int = 32
    max_admitted: int = 128
    max_anchor_rows: int = 256
    max_payload_bytes: int = 32 * 1024**2
    max_output_bytes: int = 32 * 1024**2
    max_context: int = 32768

    def __post_init__(self):
        ceilings = (128, 512, 1024, 64 * 1024**2, 64 * 1024**2, 32768)
        require(all(type(value) is int and 0 < value <= ceiling
                    for value, ceiling in zip(asdict(self).values(), ceilings)), 'bounded_fit_limits')


@dataclass(frozen=True)
class Component:
    label: str
    input_ids: tuple
    labels: tuple
    target_ids: tuple
    objective_weight: float


@dataclass(frozen=True)
class Batch:
    index: int
    identity: str
    source_sha256: str
    components: tuple

    @property
    def sha256(self):
        return digest(asdict(self))


def fingerprint_tokenizer(tokenizer):
    vocab = tokenizer.get_vocab()
    require(type(vocab) is dict and 0 < len(vocab) <= 262144, 'bounded_tokenizer_vocabulary')
    require(all(type(key) is str and type(value) is int and value >= 0 for key, value in vocab.items()),
            'tokenizer_vocabulary_types')
    document = dict(vocab=vocab, chat_template=tokenizer.chat_template,
                    eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
                    all_special_ids=list(tokenizer.all_special_ids))
    require(len(capture.encoded(document)) <= 32 * 1024**2, 'bounded_tokenizer_fingerprint')
    return digest(document)


def anchor_document(anchors):
    return {family: [dict(record, encoded=asdict(record['encoded'])) for record in records]
            for family, records in anchors.items()}


def _sample(sample, context_limit):
    inputs, labels, target = tuple(sample.input_ids), tuple(sample.labels), tuple(sample.target_ids)
    require(0 < len(target) <= len(inputs) <= context_limit and len(labels) == len(inputs),
            'whole_encoded_context_required')
    require(all(type(token) is int and token >= 0 for token in inputs)
            and all(type(token) is int for token in labels+target), 'encoded_input_ids')
    require(inputs[-len(target):] == target
            and labels == (-100,) * (len(inputs)-len(target)) + target, 'exact_prefix_mask_and_target')
    return EncodedRow(inputs, labels, target)


def _anchor_sample(sample, context_limit):
    inputs, labels, target = tuple(sample.input_ids), tuple(sample.labels), tuple(sample.target_ids)
    require(0 < len(target) <= len(inputs) <= context_limit and len(labels) == len(inputs),
            'whole_anchor_context_required')
    require(all(type(token) is int and token >= 0 for token in inputs+target)
            and all(type(label) is int and (label == -100 or label == token)
                    for token, label in zip(inputs, labels)), 'anchor_input_label_alignment')
    require(tuple(label for label in labels if label != -100) == target, 'anchor_target_mask_join')
    return EncodedRow(inputs, labels, target)


def _ref(reader, reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_path_hash_reference')
    raw, unused = reader.read(reference['path'])
    require(capture.sha(raw) == reference['sha256'], 'pinned_file_changed:'+reference['path'])
    return raw


def _implementation(instance, pins):
    source = inspect.getsourcefile(type(instance))
    require(source is not None and str(Path(source).resolve()) in pins, 'injected_implementation_source_pin')


def implementation_name(instance):
    return type(instance).__module__+'.'+type(instance).__qualname__


def native_executor_source_paths():
    root = Path(__file__).resolve().parents[1]
    return tuple(str(root/relative) for relative in (
        'gpu/orch_r161_native_executor.py', 'gpu/orch_r145_suffix_boundary.py',
        'gpu/orch_r145_suffix_loss.py', 'organism_v6/pcfl_vertical_train.py'))


def _state(state):
    require(type(state) is dict and set(state) == {'adapter_sha256', 'optimizer_sha256', 'rng_sha256',
            'optimizer_steps', 'base_sha256', 'base_frozen'}, 'exact_state_fingerprint_contract')
    require(all(capture.eligibility.hex_sha256(state[key]) for key in
                ('adapter_sha256', 'optimizer_sha256', 'rng_sha256', 'base_sha256')), 'state_hashes')
    require(type(state['optimizer_steps']) is int and state['optimizer_steps'] >= 0
            and state['base_frozen'] is True and state['base_sha256'] == native.BASE_SHA256,
            'frozen_base_and_optimizer_state')
    return deepcopy(state)


def _checkpoint(reader, reference, expected_state, *, directory=None):
    document = capture.decode(_ref(reader, reference))
    parent = capture.canonical(reference['path']).parent
    require(Path(reference['path']).name == 'COMMIT.json', 'checkpoint_COMMIT_required')
    if directory is not None:
        require(parent == directory, 'fork_local_checkpoint_only')
    require(document['base_sha256'] == expected_state['base_sha256']
            and document['adapter_state_sha256'] == expected_state['adapter_sha256']
            and document['optimizer_steps'] == expected_state['optimizer_steps'], 'checkpoint_state_binding')
    require(document['adapter_path'] == str(parent/'adapter')
            and document['optimizer_rng_path'] == str(parent/'optimizer_rng.pt'), 'checkpoint_file_locations')
    files = document['adapter_files']
    require(type(files) is dict and 0 < len(files) <= 16, 'bounded_checkpoint_files')
    for name, expected in files.items():
        require(Path(name).name == name and name not in ('', '.', '..'), 'flat_checkpoint_files')
        _ref(reader, dict(path=str(parent/'adapter'/name), sha256=expected))
    hashes = document['checkpoint_sha256']
    require(digest(files) == hashes['adapter'] and hashes['optimizer'] == hashes['rng'],
            'checkpoint_hash_joins')
    _ref(reader, dict(path=document['optimizer_rng_path'], sha256=hashes['optimizer']))
    return document


def verify_authority(authority, expected_sha256, *, reader):
    require(digest(authority) == expected_sha256, 'external_authority_hash_required')
    require(authority['schema'] == SCHEMA and authority['contract'] == CONTRACT, 'fit_authority_contract')
    require(authority['mode'] in ('learning', 'frozen') and authority['execution_kind'] in
            ('CPU_TEST_ONLY', 'EXTERNALLY_VALIDATED_EXECUTOR'), 'explicit_execution_kind_and_arm')
    require(type(authority['fork_label']) is str and bool(authority['fork_label'].strip()), 'labelled_fork_required')
    root = capture.canonical(authority['fork_root'])
    require(authority['protected_roots'] and all(not root.is_relative_to(capture.canonical(path))
            for path in authority['protected_roots']), 'no_protected_life_mutation')
    require(type(authority['context_limit']) is int and 0 < authority['context_limit'] <= 32768,
            'bounded_context_limit')
    require(authority.get('evidence_mode', 'FIXED_CORPUS_V1') in ('FIXED_CORPUS_V1', DYNAMIC), 'known_evidence_mode')
    require(type(authority['excluded_task_ids']) is list, 'explicit_policy_exclusions')
    if authority.get('evidence_mode') == DYNAMIC:
        require(not any(key in authority for key in ('trusted_artifacts', 'reviewer_provenance', 'generation_sources')),
                'dynamic_evidence_not_embedded_in_fork_policy')
        Limits(**authority['fit_limits'])
        capture.Limits(**authority['reader_limits'])
        require(asdict(reader.limits) == authority['reader_limits'], 'immutable_reader_caps')
        require(type(authority['allow_off_policy_new']) is bool, 'explicit_off_policy_new_policy')
    else:
        require(type(authority['trusted_artifacts']) is dict and authority['trusted_artifacts']
                and type(authority['reviewer_provenance']) is dict, 'external_capture_review_exclusion_authority')
    pins = authority['source_pins']
    require(type(pins) is dict and all(str(path.resolve()) in pins for path in REQUIRED_SOURCES),
            'bridge_compiler_encoder_policy_source_pins')
    if authority['executor_class'] == NATIVE_EXECUTOR_CLASS:
        require(all(path in pins for path in native_executor_source_paths()), 'native_executor_loss_fingerprint_pins')
    require(type(authority['tokenizer_pins']) is dict and authority['tokenizer_pins'], 'tokenizer_file_pins')
    for group in (pins, authority['tokenizer_pins']):
        for path, expected in group.items():
            _ref(reader, dict(path=path, sha256=expected))
    _state(authority['initializer']['state'])
    require(authority['initializer']['state']['optimizer_steps'] == 0, 'common_zero_update_initializer')
    _checkpoint(reader, authority['initializer']['commit'], authority['initializer']['state'])
    if authority['execution_kind'] != 'CPU_TEST_ONLY':
        validation = capture.decode(_ref(reader, authority['executor_validation']))
        require(validation.get('contract') == CONTRACT and validation.get('real_7b_validated') is True
                and validation.get('source_pins_sha256') == digest(pins)
                and validation.get('tokenizer_sha256') == authority['tokenizer_sha256'],
                'external_real_7b_executor_validation_required')
    return root


def _extends(previous, current, label):
    require(type(previous) is type(current), 'changed_old_evidence_pin:'+label)
    if type(previous) is dict:
        require(set(previous).issubset(current), 'removed_old_evidence_pin:'+label)
        for key, value in previous.items():
            _extends(value, current[key], label+'/'+str(key))
    else:
        require(previous == current, 'changed_old_evidence_pin:'+label)


def _path_registry(previous, *documents):
    registry = deepcopy(previous)

    def register(path, expected):
        capture.canonical(path)
        require(capture.eligibility.hex_sha256(expected), 'authorized_path_hash')
        require(path not in registry or registry[path] == expected, 'cross_map_or_old_path_pin_changed:'+path)
        registry[path] = expected

    def visit(value):
        if type(value) is dict:
            if set(value) == {'path', 'sha256'}:
                register(value['path'], value['sha256'])
            for key, item in value.items():
                if key in ('trusted_artifacts', 'source_pins', 'tokenizer_pins'):
                    for path, expected in item.items():
                        register(path, expected)
                else:
                    visit(item)
        elif type(value) in (list, tuple):
            for item in value:
                visit(item)

    for document in documents:
        visit(document)
    return registry


def _dynamic_context(policy, policy_sha256, authorization, authorization_sha256,
                     batch_index, previous_commit_sha256, reader, limits):
    require(asdict(limits) == policy['fit_limits'], 'immutable_fit_caps')
    require(type(batch_index) is int and 0 <= batch_index < 1024, 'bounded_batch_index')
    require(type(authorization) is dict and capture.eligibility.hex_sha256(authorization_sha256)
            and digest(authorization) == authorization_sha256, 'independent_batch_authorization_hash_required')
    require(len(capture.encoded(authorization)) <= limits.max_payload_bytes, 'batch_authorization_budget')
    expected_keys = {'schema', 'fork_policy_sha256', 'batch_index', 'previous_commit_sha256',
        'previous_batch_authorization_sha256', 'parent_checkpoint', 'parent_state_sha256',
        'fit_start_checkpoint', 'fit_start_state', 'learner_journal_id', 'trusted_artifacts',
        'reviewer_provenance_by_sha256', 'generation_sources', 'excluded_task_ids'}
    require(set(authorization) == expected_keys and authorization['schema'] == BATCH_AUTHORIZATION_SCHEMA,
            'exact_batch_evidence_authorization')
    require(authorization['fork_policy_sha256'] == policy_sha256
            and type(authorization['batch_index']) is int and authorization['batch_index'] == batch_index
            and authorization['previous_commit_sha256'] == previous_commit_sha256, 'batch_policy_and_parent_binding')
    root = capture.canonical(policy['fork_root'])
    require(capture.decode(reader.read(root/'AUTHORITY.json')[0]) == policy, 'fork_authority_immutable')
    require(not os.path.lexists(root/f'batch{batch_index:04d}'), 'existing_or_uncertain_batch_never_retried')
    prior = None
    if batch_index:
        require(not os.path.lexists(root/f'batch{batch_index-1:04d}'/'FAILED.json'),
                'previous_failed_boundary_never_advanced')
        prior = capture.decode(_ref(reader, dict(path=str(root/f'batch{batch_index-1:04d}'/'COMMIT.json'),
                                                sha256=previous_commit_sha256)))
        require(prior['status'] == 'COMMITTED' and prior['batch_index'] == batch_index-1
                and prior['authority_sha256'] == policy_sha256
                and prior['evidence_mode'] == DYNAMIC, 'previous_dynamic_boundary_required')
        require(digest(prior['batch_authorization']) == prior['batch_authorization_sha256']
                == authorization['previous_batch_authorization_sha256'], 'batch_authorization_chain')
        previous_authorization = prior['batch_authorization']
        for key in ('trusted_artifacts', 'reviewer_provenance_by_sha256', 'generation_sources'):
            _extends(previous_authorization[key], authorization[key], key)
        require(set(previous_authorization['excluded_task_ids']).issubset(authorization['excluded_task_ids']),
                'cannot_remove_previous_exclusions')
        require(authorization['learner_journal_id'] == previous_authorization['learner_journal_id'],
                'continuing_learner_journal_identity')
        parent_checkpoint, parent_state = prior['checkpoint'], prior['after_state']
    else:
        require(previous_commit_sha256 is None and authorization['previous_batch_authorization_sha256'] is None,
                'initial_batch_has_no_parent_authorization')
        parent_checkpoint, parent_state = policy['initializer']['commit'], policy['initializer']['state']
    require(authorization['parent_checkpoint'] == parent_checkpoint
            and authorization['parent_state_sha256'] == digest(parent_state), 'exact_parent_fit_boundary')
    parent_document = _checkpoint(reader, parent_checkpoint, parent_state,
        directory=root/f'batch{batch_index-1:04d}'/'checkpoint' if prior else None)
    fit_state = _state(authorization['fit_start_state'])
    require(all(fit_state[key] == parent_state[key] for key in parent_state if key != 'rng_sha256'),
            'generation_must_not_change_adapter_AdamW_steps_or_base')
    fit_checkpoint = authorization['fit_start_checkpoint']
    if fit_checkpoint != parent_checkpoint:
        fit_path = capture.canonical(fit_checkpoint['path'])
        require(fit_path.is_relative_to(root/'generation_boundaries'), 'post_generation_checkpoint_inside_fork')
    _checkpoint(reader, fit_checkpoint, fit_state)
    require(type(authorization['learner_journal_id']) is str and len(authorization['learner_journal_id']) == 32
            and all(character in '0123456789abcdef' for character in authorization['learner_journal_id']),
            'explicit_learner_journal_identity')
    require(type(authorization['excluded_task_ids']) is list
            and all(type(task) is str for task in authorization['excluded_task_ids'])
            and len(set(authorization['excluded_task_ids'])) == len(authorization['excluded_task_ids'])
            and set(policy['excluded_task_ids']).issubset(authorization['excluded_task_ids']), 'policy_exclusions_preserved')
    for key in ('trusted_artifacts', 'reviewer_provenance_by_sha256', 'generation_sources'):
        require(type(authorization[key]) is dict, 'batch_evidence_map:'+key)
    for path, expected in authorization['trusted_artifacts'].items():
        capture.canonical(path)
        require(capture.eligibility.hex_sha256(expected), 'authorized_artifact_hash')
    for expected, provenance in authorization['reviewer_provenance_by_sha256'].items():
        require(capture.eligibility.hex_sha256(expected) and type(provenance) is dict
                and provenance.get('review_sha256') == expected, 'review_artifact_specific_provenance')
    registry = _path_registry(prior['evidence_path_pins'] if prior else {}, policy, authorization)
    effective = dict(policy, **{key: deepcopy(authorization[key]) for key in
        ('trusted_artifacts', 'reviewer_provenance_by_sha256', 'generation_sources', 'excluded_task_ids')})
    context = dict(authorization=deepcopy(authorization), authorization_sha256=authorization_sha256,
        prior=prior, parent_checkpoint=parent_checkpoint, parent_document=parent_document,
        fit_start_checkpoint=fit_checkpoint, fit_start_state=fit_state,
        learner_journal_id=authorization['learner_journal_id'], evidence_path_pins=registry)
    return effective, context


def _reviewer_authority(candidate, authority):
    if authority.get('evidence_mode') != DYNAMIC:
        return authority['reviewer_provenance']
    reviewers = {}
    for artifact in candidate['reviews']:
        document = capture.decode(artifact['raw'])
        identity = document['reviewer_id']
        require(identity not in reviewers, 'distinct_review_ids_within_candidate')
        require(artifact['sha256'] in authority['reviewer_provenance_by_sha256'], 'batch_review_provenance_missing')
        reviewers[identity] = deepcopy(authority['reviewer_provenance_by_sha256'][artifact['sha256']])
    return reviewers


def _artifact_budget(value, authority, limits):
    count, size = 0, 0

    def visit(item, depth=0):
        nonlocal count, size
        count += 1
        require(count <= 200000 and depth <= 32, 'bounded_packet_structure')
        if type(item) is dict:
            if 'raw' in item:
                require(set(item) == {'path', 'sha256', 'raw'} and type(item['raw']) is bytes,
                        'original_artifact_bytes_required')
                require(size+len(item['raw']) <= limits.max_payload_bytes, 'bounded_packet_payload')
                capture.canonical(item['path'])
                require(authority['trusted_artifacts'].get(item['path']) == item['sha256']
                        == capture.sha(item['raw']), 'independent_artifact_hash_join')
            for key, child in item.items():
                visit(key, depth+1)
                visit(child, depth+1)
        elif type(item) in (list, tuple):
            for child in item:
                visit(child, depth+1)
        elif type(item) in (str, bytes):
            size += len(item.encode() if type(item) is str else item)
        else:
            require(item is None or type(item) in (int, bool, float), 'packet_value_type')
            size += 16
        require(size <= limits.max_payload_bytes, 'bounded_packet_payload')

    visit(value)


def _generation_lineage(evidence, authority, reader):
    records = [capture.decode(artifact['raw']) for artifact in evidence['records']]
    request = records[0]['document']
    state = request['resume_state']['state']
    row = records[2]['document']['state']['state']['rows'][-1]
    source_root = str(capture.canonical(evidence['records'][0]['path']).parents[2])
    require(source_root != authority['fork_root'] or authority.get('evidence_mode') == DYNAMIC,
            'on_policy_generation_requires_future_round_authority')
    source = authority['generation_sources'][source_root]
    plan = capture.decode(_ref(reader, source['plan']))
    require(plan['root'] == source_root and plan['matched_arm'] == Path(source_root).name,
            'actual_generating_plan_arm_and_root')
    matched = state.get('matched')
    if matched is not None:
        require(matched['arm'] == plan['matched_arm']
                and matched['cohort_sha256'] == plan['matched_cohort']['sha256'], 'generating_matched_cohort_join')
    source_directory = capture.canonical(plan['source_root'])
    require(type(source['source_pins']) is dict and source['source_pins'], 'generating_source_closure_required')
    for path, expected in source['source_pins'].items():
        require(capture.canonical(path).is_relative_to(source_directory), 'generating_source_path_join')
        _ref(reader, dict(path=path, sha256=expected))
    model_state = request['model_state_sha256']
    require(capture.eligibility.hex_sha256(model_state)
            and model_state == state['model_state_sha256'] == row['model_state_sha256'],
            'actual_generating_model_state_join')
    reference = source['checkpoints'][model_state]
    checkpoint = capture.decode(_ref(reader, reference))
    hashes = checkpoint['checkpoint_sha256']
    require(set(hashes) == {'adapter', 'optimizer', 'rng'}
            and all(capture.eligibility.hex_sha256(value) for value in hashes.values())
            and digest(hashes) == model_state and hashes['optimizer'] == hashes['rng']
            and checkpoint['base_sha256'] == native.BASE_SHA256
            and capture.eligibility.hex_sha256(checkpoint['adapter_state_sha256'])
            and type(checkpoint['optimizer_steps']) is int and checkpoint['optimizer_steps'] >= 0,
            'generating_checkpoint_model_state_join')
    embedded = state['sleep_receipts'][-1].get('checkpoint') if state['sleep_receipts'] else state.get('initial_checkpoint')
    if embedded is not None:
        require(embedded == checkpoint, 'generating_embedded_checkpoint_join')
    own_initializer = capture.decode(_ref(reader, authority['initializer']['commit']))
    source_initializer = state.get('initial_checkpoint')
    sibling = (source_initializer is not None
               and source_initializer['checkpoint_sha256'] == own_initializer['checkpoint_sha256']
               and source_initializer['optimizer_steps'] == own_initializer['optimizer_steps'] == 0
               and source_initializer['adapter_state_sha256'] == own_initializer['adapter_state_sha256']
               and source_initializer['base_sha256'] == native.BASE_SHA256)
    own_learner = source_root == authority['fork_root']
    return dict(source_root=source_root, source_arm=plan['matched_arm'],
        source_plan=deepcopy(source['plan']), source_directory=str(source_directory),
        source_pins_sha256=digest(source['source_pins']), source_matched_binding=deepcopy(matched),
        journal_id=records[0]['journal_id'], request_index=records[0]['index'],
        request_started_unix=request['started_unix'],
        response_index=records[1]['index'], committed_index=records[2]['index'],
        request_record_sha256=records[0]['sha256'], response_record_sha256=records[1]['sha256'],
        committed_record_sha256=records[2]['sha256'], row_source_sha256=row['source_sha256'],
        model_state_sha256=model_state, generating_checkpoint=deepcopy(reference),
        generating_checkpoint_sha256=deepcopy(hashes), generating_adapter_state_sha256=checkpoint['adapter_state_sha256'],
        generating_optimizer_steps=checkpoint['optimizer_steps'],
        source_initial_checkpoint_sha256=deepcopy(source_initializer['checkpoint_sha256']) if source_initializer else None,
        common_initializer_proven=sibling,
        relation=('OWN_CONTINUING_LEARNER_TRAJECTORY' if own_learner else
                  'OFF_POLICY_SIBLING_BOOTSTRAP' if sibling else 'OFF_POLICY_EXTERNAL_OWN_TRAJECTORY'),
        own_text_origin='ORIGINAL_CONSUMING_LEARNER_CHILD' if own_learner else 'ORIGINAL_GENERATING_CHILD_NOT_CONSUMING_FORK',
        generated_by_consuming_fork=own_learner)


def prepare_fit(new_candidates, replay_candidates, *, authority, expected_authority_sha256,
                tokenizer, anchors, previous_admitted=None, previous_consumed=None, limits=Limits(), reader=None,
                batch_authorization=None, expected_batch_authorization_sha256=None,
                batch_index=None, previous_commit_sha256=None):
    """Compile supplied reviews and construct batches; performs no updates or ledger writes."""
    authority = deepcopy(authority)
    reader = reader or capture.Reader(capture.Limits())
    verify_authority(authority, expected_authority_sha256, reader=reader)
    context = None
    if authority.get('evidence_mode') == DYNAMIC:
        require(previous_admitted is None and previous_consumed is None, 'dynamic_previous_evidence_loaded_from_ledger_only')
        authority, context = _dynamic_context(authority, expected_authority_sha256, batch_authorization,
            expected_batch_authorization_sha256, batch_index, previous_commit_sha256, reader, limits)
        previous_admitted = context['prior']['admitted'] if context['prior'] else {}
        previous_consumed = context['prior']['consumed'] if context['prior'] else []
    else:
        require(batch_authorization is None and expected_batch_authorization_sha256 is None,
                'batch_authorization_requires_dynamic_policy')
    require(len(new_candidates)+len(replay_candidates) <= limits.max_candidates, 'candidate_count_budget')
    require(authority['context_limit'] <= limits.max_context, 'fit_context_budget')
    _artifact_budget([new_candidates, replay_candidates], authority, limits)
    _implementation(tokenizer, authority['source_pins'])
    require(implementation_name(tokenizer) == authority['tokenizer_class'], 'pinned_tokenizer_class')
    require(fingerprint_tokenizer(tokenizer) == authority['tokenizer_sha256'], 'tokenizer_fingerprint_changed')
    require(sum(len(records) for records in anchors.values()) <= limits.max_anchor_rows, 'anchor_row_budget')
    validate_anchor_inventory(anchors)
    require(len(capture.encoded(anchor_document(anchors))) <= limits.max_payload_bytes, 'anchor_payload_budget')
    require(digest(anchor_document(anchors)) == authority['anchors_sha256'], 'pinned_encoded_anchor_inventory')
    for records in anchors.values():
        for record in records:
            _anchor_sample(record['encoded'], authority['context_limit'])
    previous = deepcopy(previous_admitted or {})
    consumed = deepcopy(previous_consumed if previous_consumed is not None else list(previous))
    require(type(consumed) is list and len(set(consumed)) == len(consumed)
            and set(previous).issubset(consumed), 'previous_consumed_identity_ledger')
    require(len(previous) <= limits.max_admitted, 'admitted_ledger_budget')
    admitted, seen, seen_sources, replay_seen = deepcopy(previous), set(), set(), set()
    rows, encoded, identities = {'NEW': [], 'REHEARSAL': []}, {}, {}
    decisions, exclusions, lineages, policy_relations = [], [], {}, {}
    own_frontier = context['prior']['learner_frontier'] if context and context['prior'] else -1
    own_new = 0
    for kind, candidates in (('NEW', new_candidates), ('REHEARSAL', replay_candidates)):
        for candidate in candidates:
            require(set(candidate) == {'packet', 'reviews'}, 'packet_and_supplied_reviews_only')
            decision = capture.compile_reviewed(deepcopy(candidate['packet']), deepcopy(candidate['reviews']),
                trusted_artifacts=authority['trusted_artifacts'], reviewer_provenance=_reviewer_authority(candidate, authority),
                generator_binding=authority['generator_binding'], excluded_task_ids=authority['excluded_task_ids'])
            decisions.append(dict(cohort=kind, decision=decision))
            require(decision['status'] == 'PASS' and decision['eligible'] is True and decision['row'] is not None,
                    'reviewed_candidate_not_eligible:'+','.join(reason['code'] for reason in decision['reasons']))
            row = deepcopy(decision['row'])
            identity = decision['binding']['response_sha256']
            require(identity not in seen and row['source_sha256'] not in seen_sources, 'duplicate_response_or_source')
            seen.add(identity)
            seen_sources.add(row['source_sha256'])
            lineage = _generation_lineage(candidate['packet'], authority, reader)
            require(lineage['response_record_sha256'] == identity
                    and lineage['row_source_sha256'] == row['source_sha256']
                    and lineage['model_state_sha256'] == row['model_state_sha256'], 'compiled_row_generation_lineage_join')
            related = {name: _generation_lineage(candidate['packet'][name], authority, reader)
                       for name in ('anchor_attempt', 'feedback') if name in candidate['packet']}
            lineages[identity] = dict(target=lineage, related=related)
            on_policy_new = False
            if context:
                if lineage['generated_by_consuming_fork']:
                    require(lineage['journal_id'] == context['learner_journal_id'], 'actual_continuing_learner_journal')
                    if kind == 'NEW':
                        parent = context['parent_document']
                        require(lineage['generating_checkpoint_sha256'] == parent['checkpoint_sha256']
                                and lineage['generating_adapter_state_sha256'] == parent['adapter_state_sha256']
                                and lineage['generating_optimizer_steps'] == parent['optimizer_steps'],
                                'on_policy_NEW_requires_current_parent_model')
                        require(lineage['request_index'] > own_frontier, 'fresh_ordered_own_REQUEST_frontier')
                        if context['prior']:
                            require(lineage['request_started_unix'] > context['prior']['committed_unix'],
                                    'own_generation_must_follow_previous_fit_commit')
                        own_frontier = lineage['committed_index']
                        on_policy_new = True
                elif kind == 'NEW':
                    require(authority['allow_off_policy_new'], 'off_policy_NEW_not_authorized')
            policy_relations[identity] = ('HISTORICAL_ELIGIBLE_REPLAY' if kind == 'REHEARSAL' else
                'ON_POLICY_NEW_AT_PARENT_BOUNDARY' if on_policy_new else lineage['relation'])
            entry = dict(row_sha256=digest(row), binding_sha256=digest(decision['binding']),
                         lineage_sha256=digest(lineages[identity]))
            if kind == 'NEW':
                require(identity not in consumed, 'previous_response_cannot_be_new')
                consumed.append(identity)
            else:
                require(previous.get(identity) == entry, 'rehearsal_requires_exact_previous_eligible_row')
                replay_seen.add(identity)
            before = digest(row)
            try:
                sample = native.encode_own(deepcopy(row), tokenizer, authority['context_limit'])
            except ValueError as error:
                if error.args != (targets.REJECTION,):
                    raise
                require(kind == 'NEW', 'previous_eligible_target_changed')
                exclusions.append(dict(identity=identity, source_sha256=row['source_sha256'], cohort=kind,
                    reason=targets.REJECTION, policy=targets.POLICY))
                continue
            sample = _sample(sample, authority['context_limit'])
            prefix = tuple(tokenizer.apply_chat_template(deepcopy(row['prefix']), tokenize=True,
                           add_generation_prompt=True, return_dict=False))
            require(sample.input_ids == prefix+tuple(row['token_ids']) and sample.target_ids == tuple(row['token_ids'])
                    and digest(row) == before, 'exact_captured_prefix_and_tokens')
            vocab_ids = set(tokenizer.get_vocab().values())
            require(set(sample.input_ids).issubset(vocab_ids), 'tokens_in_pinned_vocabulary')
            rows[kind].append(row)
            encoded[row['source_sha256']] = sample
            identities[row['source_sha256']] = identity
            admitted[identity] = entry
            own_new += int(on_policy_new)
    require(replay_seen == set(previous), 'all_previous_eligible_replayed_once')
    require(len(admitted) <= limits.max_admitted and len(consumed) <= limits.max_admitted, 'admitted_ledger_budget')
    schedule = (native.presentation_schedule(rows['NEW'], rows['REHEARSAL']) if rows['NEW'] else
                [('REHEARSAL', row) for row in rows['REHEARSAL']])
    batches, presentations, own_tokens, anchor_tokens = [], {}, 0, 0
    for index, (kind, row) in enumerate(schedule):
        own = encoded[row['source_sha256']]
        components = [Component(kind, own.input_ids, own.labels, own.target_ids, 0.75)]
        for family, records in sorted(anchors.items()):
            anchor = _anchor_sample(records[index % len(records)]['encoded'], authority['context_limit'])
            components.append(Component('ANCHOR:'+family, anchor.input_ids, anchor.labels, anchor.target_ids, 0.0625))
            anchor_tokens += sum(label != -100 for label in anchor.labels)
        identity = identities[row['source_sha256']]
        presentations[identity] = presentations.get(identity, 0)+1
        own_tokens += sum(label != -100 for label in own.labels)
        batches.append(Batch(index, identity, row['source_sha256'], tuple(components)))
    require(fingerprint_tokenizer(tokenizer) == authority['tokenizer_sha256'], 'tokenizer_changed_during_encoding')
    report = dict(schema=SCHEMA, status='CPU_PREFLIGHT_ONLY_NOT_TRAINED', authority_sha256=expected_authority_sha256,
        decisions=decisions, exclusions=exclusions, admitted=admitted, consumed=consumed,
        generation_lineage=lineages, policy_relations=policy_relations, on_policy_new_rows=own_new,
        learner_frontier=own_frontier,
        on_policy_rounds=context['prior']['on_policy_rounds'] if context and context['prior'] else 0,
        simulated_on_policy_rounds=context['prior']['simulated_on_policy_rounds'] if context and context['prior'] else 0,
        planned_presentations=presentations,
        presentations=presentations if authority['mode'] == 'learning' else {},
        planned_updates=len(batches) if authority['mode'] == 'learning' else 0,
        child_token_exposures=own_tokens if authority['mode'] == 'learning' else 0,
        anchor_token_exposures=anchor_tokens if authority['mode'] == 'learning' else 0,
        anchor_lambda=0.25, mix_kind='OBJECTIVE_WEIGHT_NOT_TOKEN_FRACTION',
        anchor_mix_applied=authority['mode'] == 'learning' and bool(batches),
        batch_sha256=[batch.sha256 for batch in batches], scientific_claim=False,
        synthetic_fixture=authority['execution_kind'] == 'CPU_TEST_ONLY')
    report['evidence_mode'] = authority.get('evidence_mode', 'FIXED_CORPUS_V1')
    if context:
        report.update(batch_authorization=context['authorization'],
            batch_authorization_sha256=context['authorization_sha256'],
            evidence_path_pins=context['evidence_path_pins'],
            fit_start_checkpoint=context['fit_start_checkpoint'], fit_start_state=context['fit_start_state'])
    require(2*len(capture.encoded(report))+len(batches)*1024+16384 <= limits.max_output_bytes, 'fit_output_budget')
    return tuple(batches), report


@dataclass
class OutputBudget:
    remaining: int


def _write(directory, name, document, budget):
    raw = capture.encoded(document)
    require(len(raw) <= budget.remaining, 'ledger_output_budget')
    budget.remaining -= len(raw)
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory)
    return capture.sha(raw)


def create_fork(authority, *, expected_authority_sha256, reader=None, limits=Limits()):
    """Create a new ledger only; caller separately clones/verifies the common initializer."""
    authority = deepcopy(authority)
    reader = reader or capture.Reader(capture.Limits())
    root = verify_authority(authority, expected_authority_sha256, reader=reader)
    if authority.get('evidence_mode') == DYNAMIC:
        require(asdict(limits) == authority['fit_limits'], 'immutable_fit_caps')
    budget = OutputBudget(limits.max_output_bytes)
    with capture.gym.console._directory(root.parent) as parent:
        os.mkdir(root.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    with capture.gym.console._directory(root) as directory:
        _write(directory, 'AUTHORITY.json', authority, budget)
        _write(directory, 'LOCK', {}, budget)
    return dict(fork_root=str(root), authority_sha256=expected_authority_sha256, training_performed=False)


def fit_batch(new_candidates, replay_candidates, *, authority, expected_authority_sha256,
              batch_index, previous_commit_sha256, tokenizer, anchors, executor,
              limits=Limits(), reader=None, batch_authorization=None, expected_batch_authorization_sha256=None):
    """Explicit injected execution. An existing attempt, including failure, is never retried."""
    authority = deepcopy(authority)
    require(type(batch_index) is int and 0 <= batch_index < 1024, 'bounded_batch_index')
    reader = reader or capture.Reader(capture.Limits())
    root = verify_authority(authority, expected_authority_sha256, reader=reader)
    require(capture.decode(reader.read(root/'AUTHORITY.json')[0]) == authority, 'fork_authority_immutable')
    _implementation(executor, authority['source_pins'])
    require(implementation_name(executor) == authority['executor_class'], 'pinned_executor_class')
    require(executor.contract == CONTRACT and executor.execution_kind == authority['execution_kind'],
            'explicit_pinned_executor_contract')
    require(executor.fork_binding == dict(fork_root=str(root), mode=authority['mode'],
            authority_sha256=expected_authority_sha256,
            initializer_commit_sha256=authority['initializer']['commit']['sha256']), 'executor_is_bound_to_new_fork')
    with capture.gym.console._directory(root) as directory:
        lock = os.open('LOCK', os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            attempt = root/f'batch{batch_index:04d}'
            require(not os.path.lexists(attempt), 'existing_or_uncertain_batch_never_retried')
            previous, consumed, expected_state = {}, [], authority['initializer']['state']
            starting_checkpoint = authority['initializer']['commit']
            if batch_index:
                require(not os.path.lexists(root/f'batch{batch_index-1:04d}'/'FAILED.json'),
                        'previous_failed_boundary_never_advanced')
                reference = dict(path=str(root/f'batch{batch_index-1:04d}'/'COMMIT.json'),
                                 sha256=previous_commit_sha256)
                prior = capture.decode(_ref(reader, reference))
                require(prior['authority_sha256'] == expected_authority_sha256
                        and prior['batch_index'] == batch_index-1 and prior['status'] == 'COMMITTED',
                        'previous_completed_fork_boundary_required')
                previous, expected_state = prior['admitted'], prior['after_state']
                consumed = prior['consumed']
                starting_checkpoint = prior['checkpoint']
                _checkpoint(reader, prior['checkpoint'], expected_state,
                            directory=root/f'batch{batch_index-1:04d}'/'checkpoint')
            else:
                require(previous_commit_sha256 is None, 'no_previous_commit_at_birth')
            batches, report = prepare_fit(new_candidates, replay_candidates, authority=authority,
                expected_authority_sha256=expected_authority_sha256, tokenizer=tokenizer, anchors=anchors,
                previous_admitted=None if authority.get('evidence_mode') == DYNAMIC else previous,
                previous_consumed=None if authority.get('evidence_mode') == DYNAMIC else consumed,
                limits=limits, reader=reader, batch_authorization=batch_authorization,
                expected_batch_authorization_sha256=expected_batch_authorization_sha256,
                batch_index=batch_index, previous_commit_sha256=previous_commit_sha256)
            if authority.get('evidence_mode') == DYNAMIC:
                starting_checkpoint, expected_state = report['fit_start_checkpoint'], report['fit_start_state']
            require(executor.verify_checkpoint(starting_checkpoint) == expected_state,
                    'loaded_boundary_optimizer_RNG_binding')
            before = _state(executor.snapshot())
            require(before == expected_state, 'exact_loaded_initializer_or_previous_state')
            budget = OutputBudget(limits.max_output_bytes)
            os.mkdir(attempt.name, mode=0o700, dir_fd=directory)
            os.fsync(directory)
            with capture.gym.console._directory(attempt) as attempt_fd:
                _write(attempt_fd, 'INTENT.json', dict(report, batch_index=batch_index,
                    previous_commit_sha256=previous_commit_sha256, before_state=before), budget)
                try:
                    state = before
                    if authority['mode'] == 'learning':
                        for batch in batches:
                            receipt = executor.update(batch)
                            require(receipt == dict(batch_sha256=batch.sha256,
                                    optimizer_step=state['optimizer_steps']+1), 'exact_update_acknowledgment')
                            after = _state(executor.snapshot())
                            require(after['optimizer_steps'] == state['optimizer_steps']+1, 'one_AdamW_step_per_batch')
                            _write(attempt_fd, f'UPDATE{batch.index:04d}.json', dict(receipt, after_state=after),
                                   budget)
                            state = after
                    after = _state(executor.snapshot())
                    require(after == state, 'no_unacknowledged_state_change')
                    if authority['mode'] == 'frozen' or not batches:
                        require(after == before, 'frozen_or_empty_exact_state_unchanged')
                    else:
                        require(after['adapter_sha256'] != before['adapter_sha256'], 'actual_adapter_change_required')
                    checkpoint = executor.checkpoint(attempt/'checkpoint')
                    _checkpoint(reader, checkpoint, after, directory=attempt/'checkpoint')
                    require(executor.verify_checkpoint(checkpoint) == after, 'saved_optimizer_RNG_state_verified')
                    require(_state(executor.snapshot()) == after, 'checkpoint_does_not_change_state')
                    committed = dict(report, status='COMMITTED', batch_index=batch_index,
                        previous_commit_sha256=previous_commit_sha256, before_state=before, after_state=after,
                        checkpoint=checkpoint, updates=after['optimizer_steps']-before['optimizer_steps'],
                        committed_unix=time.time(),
                        training_performed=authority['execution_kind'] != 'CPU_TEST_ONLY'
                            and authority['mode'] == 'learning' and bool(batches))
                    if committed['updates'] and report['on_policy_new_rows']:
                        counter = 'simulated_on_policy_rounds' if report['synthetic_fixture'] else 'on_policy_rounds'
                        committed[counter] += 1
                    commit_sha = _write(attempt_fd, 'COMMIT.json', committed, budget)
                    return dict(commit=committed, path=str(attempt/'COMMIT.json'), sha256=commit_sha)
                except BaseException as error:
                    _write(attempt_fd, 'FAILED.json', dict(error_type=type(error).__name__, retry_allowed=False,
                        state_uncertain=True), budget)
                    raise
        finally:
            os.close(lock)
