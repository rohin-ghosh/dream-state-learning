"""C2 opt-in prefix authority; called only through the original admission route."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat


CONTEXT = ContextVar('c2_original_admission_prefix', default=None)
SAME = 'SAME_MOUNT_NAMESPACE'
CROSS = 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'
RELOCATIONS = {'attempt_dir', 'plan_path', 'plan_sha256', 'lease_path', 'lease_sha256',
    'allocation_path', 'allocation_sha256', 'source_pins'}


def require(condition, reason):
    if not condition:
        raise ValueError('c2_prefix_' + reason)


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
    identity = lambda entry: (entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns, entry.st_mode)
    require(identity(before) == identity(after) == identity(path.stat(follow_symlinks=False))
        and len(content) == before.st_size and hashlib.sha256(content).hexdigest() == reference['sha256'],
        'exact_unchanged_reference_bytes')
    return content


def document(reference):
    return json.loads(pinned(reference))


def reference(path):
    path = Path(path)
    result = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    pinned(result)
    return result


def confinement_digest(config):
    return digest({key: value for key, value in config.items() if key not in RELOCATIONS})


def load_authority(approved, plan, pins, *, life_binding_sha256=None, epoch_id=None, config=None):
    authority = document(approved)
    require(set(authority) == {'schema', 'status', 'epoch_id', 'life_binding_sha256', 'deadline_unix',
        'physical', 'source', 'proof', 'producer', 'producer_receipt', 'selection_policy',
        'max_advance_records', 'max_advance_bytes', 'confinement_sha256', 'consumer_context_mode',
        'bounded_context_clause_derivation'}, 'authority_schema_no_namespace_allowlist')
    require(authority['schema'] == 'C2_PREFIX_OPERATOR_AUTHORITY_V1'
        and authority['status'] == 'MAIN_APPROVED_IMMUTABLE_PREFIX', 'explicit_Main_approval_required')
    require(authority['consumer_context_mode'] in (SAME, CROSS)
        and authority['bounded_context_clause_derivation'] is True, 'explicit_mode_and_bounded_delegation')
    require(plan['physical'] == authority['physical'] == 1
        and plan['hard_end_unix'] == authority['deadline_unix'] == 1789927200
        and plan['gpu_uuid'] == 'GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c'
        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance', 'same_C2_life_bounds')
    require(authority['source']['root'] == plan['source_root'] and authority['source']['pins'] == pins
        and authority['selection_policy']['root'] == str(Path(plan['root']) / 'stream'), 'same_source_original_journal')
    require(type(authority['max_advance_records']) is int and 0 <= authority['max_advance_records'] <= 100000
        and type(authority['max_advance_bytes']) is int and 0 <= authority['max_advance_bytes'] <= 8 * 1024**3,
        'explicit_bounded_advance')
    if life_binding_sha256 is not None:
        require(authority['life_binding_sha256'] == life_binding_sha256, 'same_exact_native_binding')
    if epoch_id is not None:
        require(authority['epoch_id'] == epoch_id, 'same_explicit_epoch')
    if config is not None:
        require('c2_prefix_authority' not in config and 'consumer_context_mode' not in config,
            'no_arbitrary_guard_field_authority')
        require(confinement_digest(config) == authority['confinement_sha256']
            and config['copy_raw'] == plan['root'] and config['resume'] is True,
            'original_confinement_and_uncloned_journal')
    pinned(authority['producer'])
    epoch = document(authority['source']['epoch'])
    require(epoch == dict(schema='C2_PREFIX_SOURCE_EPOCH_V1', epoch_id=authority['epoch_id'],
        source_root=plan['source_root'], source_pins_sha256=digest(pins), deadline_unix=1789927200),
        'exact_separate_source_epoch')
    proof = document(authority['proof'])
    require(proof['binding']['source'] == authority['source']
        and proof['binding']['journal_type'] == 'gpu.orch_r125_stream_journal:StreamJournal', 'exact_source_journal_family')
    require({key: value for key, value in proof['binding']['selection'].items()
        if key not in ('complete_index', 'complete_sha256')} == authority['selection_policy'], 'same_selection_policy')
    producer = document(authority['producer_receipt'])
    require(producer['status'] == 'CANDIDATE_NOT_AUTHORIZATION'
        and producer['proof_path'] == authority['proof']['path']
        and producer['proof_sha256'] == authority['proof']['sha256']
        and producer['journal_writes'] == 0 and producer['writer_lock_acquired'] is False,
        'exact_readonly_producer_receipt_not_admission')
    return authority, proof


def selection_guard(approved, plan, pins, selection):
    from gpu.immutable_prefix_proof import guard_candidate
    authority, proof = load_authority(approved, plan, pins)
    require({key: value for key, value in selection.items() if key not in ('complete_index', 'complete_sha256')}
        == authority['selection_policy'], 'no_selection_policy_change')
    return guard_candidate(proof, authority['proof']['path'], authority['proof']['sha256'],
        resume_selection=selection, max_advance_records=authority['max_advance_records'],
        max_advance_bytes=authority['max_advance_bytes'], consumer_context_mode=authority['consumer_context_mode'])


def verify_selection_binding(binding, approved, plan, pins, selection):
    require(type(binding) is dict and set(binding) == {'schema', 'authority', 'selection_guard', 'selection_sha256'}
        and binding['schema'] == 'C2_PREFIX_SELECTION_BINDING_V1' and binding['authority'] == approved
        and binding['selection_sha256'] == digest(selection), 'exact_external_selection_binding')
    require(document(binding['selection_guard']) == selection_guard(approved, plan, pins, selection),
        'only_Main_bounded_guard_derivation')
    return dict(guard_path=binding['selection_guard']['path'], guard_sha256=binding['selection_guard']['sha256'])


def receiving_cpu(cpu, approved, plan, pins, selection, binding):
    from gpu.immutable_prefix_proof import admission_clause
    require(cpu['passed'] is True and cpu['source_pins'] == pins and cpu.get('c2_prefix_authority') == approved,
        'original_passed_source_CPU_Main_authority')
    argument = verify_selection_binding(binding, approved, plan, pins, selection)
    guard = document(binding['selection_guard'])
    result = deepcopy(cpu)
    require('c2_prefix_context' not in result, 'unmodified_source_CPU_receipt_required')
    if guard['consumer_context_mode'] == CROSS:
        result['c2_prefix_context'] = admission_clause(guard, argument)
    return result


@contextmanager
def admitted_prefix(config, plan, *, guard_path):
    require(CONTEXT.get() is None, 'no_nested_admission')
    require('c2_prefix_authority' not in config and 'consumer_context_mode' not in config,
        'no_arbitrary_guard_field_authority')
    allocation = document(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    require(allocation['plan_sha256'] == config['plan_sha256'], 'original_allocation_plan_binding')
    cpu_reference = dict(path=allocation['cpu_receipt_path'], sha256=allocation['cpu_receipt_sha256'])
    cpu = document(cpu_reference)
    approved = cpu.get('c2_prefix_authority')
    state = None
    if approved is not None:
        require(cpu['passed'] is True and cpu['source_pins'] == config['source_pins'], 'original_CPU_source_binding')
        load_authority(approved, plan, config['source_pins'], config=config)
        guard_reference = reference(guard_path)
        require(document(guard_reference) == config, 'same_validated_original_guard')
        state = dict(approved=deepcopy(approved), plan=deepcopy(plan), guard=deepcopy(config),
            guard_reference=guard_reference, cpu_reference=cpu_reference)
    else:
        require('c2_prefix_context' not in cpu, 'no_context_without_Main_authority')
    marker = CONTEXT.set(state)
    try:
        yield
    finally:
        CONTEXT.reset(marker)


def reader_arguments(plan, token, selection):
    from gpu.immutable_prefix_proof import admission_clause
    binding = token['receiver'].get('prefix_binding')
    state = CONTEXT.get()
    if state is None:
        require(binding is None, 'prefix_requires_original_validated_admission_context')
        return dict(prefix_proof=None, prefix_admission=None)
    require(binding is not None and plan == state['plan'], 'no_implicit_full_prefix_fallback')
    config = document(state['guard_reference'])
    require(config == state['guard'], 'original_guard_unchanged')
    allocation = document(dict(path=config['allocation_path'], sha256=config['allocation_sha256']))
    require(allocation['plan_sha256'] == config['plan_sha256']
        and dict(path=allocation['cpu_receipt_path'], sha256=allocation['cpu_receipt_sha256']) == state['cpu_reference'],
        'unchanged_original_allocation_chain')
    cpu = document(state['cpu_reference'])
    pins = config['source_pins']
    require(cpu['c2_prefix_authority'] == state['approved'] and cpu['passed'] is True and cpu['source_pins'] == pins,
        'unchanged_original_CPU_authority_chain')
    authority, _ = load_authority(state['approved'], plan, pins, config=config,
        life_binding_sha256=token['life_binding_sha256'], epoch_id=token['epoch_id'])
    require(token['new_source_pins'] == pins and token['deadline_unix'] == authority['deadline_unix']
        and token['receiver']['guard_path'] == state['guard_reference']['path']
        and token['receiver']['artifact_pins'][state['guard_reference']['path']] == state['guard_reference']['sha256'],
        'same_admitted_source_and_receiving_guard')
    argument = verify_selection_binding(binding, state['approved'], plan, pins, selection)
    admission = None
    if authority['consumer_context_mode'] == CROSS:
        require(cpu.get('c2_prefix_context') == admission_clause(document(binding['selection_guard']), argument),
            'exact_original_CPU_bounded_context_clause')
        admission = dict(state['cpu_reference'], field_path=['c2_prefix_context'])
    else:
        require('c2_prefix_context' not in cpu, 'strict_default_has_no_cross_context_clause')
    return dict(prefix_proof=argument, prefix_admission=admission)
