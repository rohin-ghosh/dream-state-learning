"""Explicit pair prefix authority carried by the original admission CPU receipt."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat


SCHEMA = 'PAIR_PREFIX_OPERATOR_AUTHORITY_V1'
DERIVATION = 'EXACT_B_AND_PREAPPROVED_CAPS_IN_ORIGINAL_CPU_ALLOCATION_GUARD_V1'
CONTEXT = ContextVar('pair_original_admission_prefix', default=None)
RELOCATED_GUARD_FIELDS = {'attempt_dir', 'plan_path', 'plan_sha256', 'lease_path', 'lease_sha256',
    'allocation_path', 'allocation_sha256', 'source_pins'}


def require(condition, reason):
    if not condition:
        raise ValueError('pair_prefix_' + reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pinned(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_external_reference')
    path = Path(reference['path'])
    require(path.is_absolute() and path.resolve() == path and '..' not in path.parts, 'literal_reference_path')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 64 * 1024**2, 'bounded_regular_reference')
        content = handle.read(64 * 1024**2 + 1)
        after = os.fstat(handle.fileno())
    identity = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns)
    require(identity(before) == identity(after) == identity(path.stat(follow_symlinks=False))
        and len(content) == before.st_size and hashlib.sha256(content).hexdigest() == reference['sha256'],
        'exact_unchanged_reference_bytes')
    return content


def document(reference):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_document_key')
            result[key] = value
        return result
    return json.loads(pinned(reference), object_pairs_hook=unique)


def reference(path):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def confinement_digest(config):
    return digest({key: value for key, value in config.items() if key not in RELOCATED_GUARD_FIELDS})


def directory_identity(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'literal_filesystem_object_path')
    entry = path.stat(follow_symlinks=False)
    require(stat.S_ISDIR(entry.st_mode), 'filesystem_directory_required')
    return dict(dev=entry.st_dev, ino=entry.st_ino, mode=entry.st_mode)


def load_authority(approved, plan, pins, *, life_binding_sha256=None, epoch_id=None, config=None):
    authority = document(approved)
    require(set(authority) == {'schema', 'status', 'epoch_id', 'life_binding_sha256', 'deadline_unix',
        'physical', 'source', 'proof', 'producer', 'producer_receipt', 'selection_policy',
        'max_advance_records', 'max_advance_bytes', 'confinement_sha256', 'namespace_policy',
        'admission_derivation'}, 'authority_schema')
    require(authority['schema'] == SCHEMA and authority['status'] == 'MAIN_APPROVED_IMMUTABLE_PREFIX',
        'explicit_main_approval_not_producer_candidate')
    require(authority['namespace_policy'] == 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'
        and authority['admission_derivation'] == DERIVATION,
        'explicit_filesystem_bound_namespace_policy')
    require(authority['deadline_unix'] == plan['hard_end_unix'] and authority['physical'] == plan['physical']
        and authority['source']['root'] == plan['source_root'] and authority['source']['pins'] == pins,
        'same_source_deadline_and_control')
    require(type(authority['max_advance_records']) is int and 0 <= authority['max_advance_records'] <= 100000
        and type(authority['max_advance_bytes']) is int and 0 <= authority['max_advance_bytes'] <= 8 * 1024**3,
        'explicit_bounded_advance')
    if life_binding_sha256 is not None:
        require(authority['life_binding_sha256'] == life_binding_sha256, 'same_exact_native_life_binding')
    if epoch_id is not None:
        require(authority['epoch_id'] == epoch_id, 'same_explicit_source_epoch')
    if config is not None:
        require('pair_prefix_authority' not in config, 'no_arbitrary_guard_field_authority')
        require(confinement_digest(config) == authority['confinement_sha256'], 'same_original_confinement')
        require(str(Path(config.get('copy_raw', plan['root'])) / 'stream')
            == authority['selection_policy']['root'], 'original_guard_actual_journal_mapping')
    pinned(authority['producer'])
    epoch = document(authority['source']['epoch'])
    require(epoch['schema'] == 'PAIR_PREFIX_SOURCE_EPOCH_V1' and epoch['epoch_id'] == authority['epoch_id']
        and epoch['source_root'] == authority['source']['root']
        and epoch['source_pins_sha256'] == digest(pins) and epoch['deadline_unix'] == plan['hard_end_unix'],
        'separate_exact_source_epoch')
    proof = document(authority['proof'])
    require(proof['binding']['source'] == authority['source'], 'proof_exact_source_epoch')
    require({key: value for key, value in proof['binding']['selection'].items()
        if key not in ('complete_index', 'complete_sha256')} == authority['selection_policy'],
        'approved_selection_policy_only_complete_may_advance')
    require(proof['binding']['journal_type'] == ('gpu.r232_recovery:FrozenJournal' if plan['physical'] == 1
        else 'gpu.r232_recovery:LearnerJournal'), 'original_pair_journal_family')
    producer = document(authority['producer_receipt'])
    require(producer['status'] == 'CANDIDATE_NOT_AUTHORIZATION'
        and producer['proof_path'] == authority['proof']['path']
        and producer['proof_sha256'] == authority['proof']['sha256']
        and producer['journal_writes'] == 0 and producer['writer_lock_acquired'] is False,
        'pinned_operator_production_not_child_authority')
    return authority, proof


def selection_guard(approved, plan, pins, selection):
    from gpu.immutable_prefix_proof import guard_candidate
    authority, proof = load_authority(approved, plan, pins)
    require({key: value for key, value in selection.items() if key not in ('complete_index', 'complete_sha256')}
        == authority['selection_policy'], 'no_selection_policy_change')
    return guard_candidate(proof, authority['proof']['path'], authority['proof']['sha256'],
        resume_selection=selection, max_advance_records=authority['max_advance_records'],
        max_advance_bytes=authority['max_advance_bytes'], consumer_context_mode=authority['namespace_policy'])


def verify_selection_binding(binding, approved, plan, pins, selection):
    require(set(binding) == {'schema', 'authority', 'selection_guard', 'selection_sha256'}
        and binding['schema'] == 'PAIR_PREFIX_SELECTION_BINDING_V1'
        and binding['authority'] == approved and binding['selection_sha256'] == digest(selection),
        'same_explicit_preflight_and_startup_binding')
    require(document(binding['selection_guard']) == selection_guard(approved, plan, pins, selection),
        'exact_bounded_guard_derived_from_approved_proof')
    return dict(guard_path=binding['selection_guard']['path'], guard_sha256=binding['selection_guard']['sha256'])


def derive_cpu_receipt(parent, approved, plan, pins, selection, binding):
    from gpu.immutable_prefix_proof import admission_clause
    base = document(parent)
    require(base['passed'] is True and base['source_pins'] == pins
        and base['pair_prefix_authority'] == approved, 'original_tested_CPU_authority_required')
    fields = {'pair_prefix_admission', 'pair_prefix_selection', 'pair_prefix_cpu_parent'}
    require(not fields.intersection(base), 'no_nested_or_existing_clause_derivation')
    argument = verify_selection_binding(binding, approved, plan, pins, selection)
    result = deepcopy(base)
    result.update(pair_prefix_admission=admission_clause(document(binding['selection_guard']), argument),
        pair_prefix_selection=deepcopy(binding), pair_prefix_cpu_parent=deepcopy(parent))
    return result


def checked_cpu(config, plan, binding, selection):
    allocation = document(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    require(allocation['plan_sha256'] == config['plan_sha256'], 'original_allocation_plan_binding')
    cpu_reference = dict(path=allocation['cpu_receipt_path'], sha256=allocation['cpu_receipt_sha256'])
    cpu = document(cpu_reference)
    expected = derive_cpu_receipt(cpu['pair_prefix_cpu_parent'], cpu['pair_prefix_authority'], plan,
        config['source_pins'], selection, binding)
    require(cpu == expected, 'only_approved_B_clause_derivation_no_CPU_evidence_changes')
    return dict(cpu_reference, field_path=['pair_prefix_admission'])


@contextmanager
def admitted_prefix(config, plan, *, guard_path):
    require(CONTEXT.get() is None, 'no_nested_admission')
    require('pair_prefix_authority' not in config, 'no_arbitrary_guard_field_authority')
    allocation = document(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    require(allocation['plan_sha256'] == config['plan_sha256'], 'original_allocation_plan_binding')
    cpu = document(dict(path=allocation['cpu_receipt_path'], sha256=allocation['cpu_receipt_sha256']))
    approved = cpu.get('pair_prefix_authority')
    state = None
    if approved is not None:
        require(cpu['passed'] is True and cpu['source_pins'] == config['source_pins'], 'original_CPU_source_binding')
        authority, _ = load_authority(approved, plan, config['source_pins'], config=config)
        guard_reference = reference(guard_path)
        require(document(guard_reference) == config, 'same_original_validated_guard_bytes')
        state = dict(reference=deepcopy(approved), plan_sha256=digest(plan), pins=config['source_pins'],
            authority=authority, original_guard=deepcopy(config), guard_reference=guard_reference)
    marker = CONTEXT.set(state)
    try:
        yield
    finally:
        CONTEXT.reset(marker)


def reader_argument(plan, token, selection):
    binding = token['receiver'].get('prefix_binding')
    state = CONTEXT.get()
    if state is None:
        require(binding is None, 'prefix_requires_original_validated_admission_context')
        return None
    require(binding is not None and state['plan_sha256'] == digest(plan), 'no_implicit_full_replay_fallback')
    sidecars = ([dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)]
        if (Path(selection['root']) / 'correction_ledger.json').exists() else [])
    require(selection['sidecars'] == sidecars, 'current_sidecars_must_be_selected_at_startup')
    authority, _ = load_authority(state['reference'], plan, state['pins'],
        life_binding_sha256=token['life_binding_sha256'], epoch_id=token['epoch_id'], config=state['original_guard'])
    require(token['new_source_pins'] == state['pins'] and authority['deadline_unix'] == token['deadline_unix'],
        'same_admitted_source_epoch')
    require(token['receiver']['guard_path'] == state['guard_reference']['path']
        and token['receiver']['artifact_pins'][state['guard_reference']['path']] == state['guard_reference']['sha256'],
        'exact_receiving_guard_in_handoff_and_original_admission')
    return verify_selection_binding(binding, state['reference'], plan, state['pins'], selection)


def admission_argument(plan, token, selection):
    state = CONTEXT.get()
    if state is None:
        reader_argument(plan, token, selection)
        return None
    reader_argument(plan, token, selection)
    config = document(state['guard_reference'])
    require(config == state['original_guard'] and config['resume'] is True,
        'unchanged_original_admission_resume_guard')
    return checked_cpu(config, plan, token['receiver']['prefix_binding'], selection)
