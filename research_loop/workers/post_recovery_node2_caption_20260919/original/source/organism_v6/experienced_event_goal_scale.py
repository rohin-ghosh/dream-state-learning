"""Eight private breadth shards; actual-source replay, not actor/state attestation.

Each shard retains the frozen breadth protocol and its 192-target admission.
The registry checks all 80 fixed worlds against each other and caller old IDs.
Aggregate row_index is global; shard_row_index and call/world indexes are local.
Native callers bind actual actor, loaded state and source artifacts separately.
"""

from copy import deepcopy
from functools import lru_cache
from types import FunctionType

from organism_v6 import experienced_event_goal_breadth as breadth


PREFIX = 'ASTRA-GOALSCALE-20260914-V1'
SHARDS = tuple(range(8))
SHARD_PREFIXES = tuple(PREFIX + '-SHARD-' + str(shard) for shard in SHARDS)
SCHEMA = 'DEV_EXPERIENCED_EVENT_GOAL_SCALE_V1'
CAPS = dict(expose_calls=80, teach_calls=192, baseline_train_calls=192,
            baseline_probe_calls=96, baseline_calls=288, max_calls=560,
            max_rows=192, max_context=breadth.MAX_CONTEXT, max_new_tokens=breadth.MAX_NEW_TOKENS)
EXPOSE_CALLS = len(SHARDS) * CAPS['expose_calls']
TEACH_CALLS = MAX_ROWS = len(SHARDS) * CAPS['teach_calls']
BASELINE_CALLS = len(SHARDS) * CAPS['baseline_calls']
MAX_CALLS = EXPOSE_CALLS + TEACH_CALLS + BASELINE_CALLS
CLAIM = 'SIXTY_FOUR_FIXED_TRAIN_WORLDS_NOT_GENERAL_PLANNING_OR_H1_H2'
require = breadth.require
identifiers = breadth.identifiers
document_sha256 = breadth.document_sha256


@lru_cache(maxsize=8)
def runtime(shard):
    """Return the shard's privately bound breadth namespace (treat as read-only)."""
    require(type(shard) is int and shard in SHARDS, 'fixed_scale_shard_0_through_7_required')
    prefix = SHARD_PREFIXES[shard]
    block_prefixes = tuple(prefix + '-BLOCK-' + str(index) for index in range(4))
    trained = tuple(block + '-TRAIN-' + suffix for block in block_prefixes for suffix in ('A', 'B'))
    probes = tuple(block_prefixes[0] + '-PROBE-' + suffix for suffix in ('A', 'B'))
    master_block = {master: index // 2 for index, master in enumerate(trained)}
    master_block.update(dict.fromkeys(probes, 0))
    namespace = dict(breadth.__dict__, PREFIX=prefix, BLOCK_PREFIXES=block_prefixes,
                     TRAIN_MASTERS=trained, PROBE_MASTERS=probes, MASTERS=trained + probes,
                     MASTER_BLOCK=master_block, SHARD=shard, CAPS=deepcopy(CAPS),
                     TOTAL_CALLS=CAPS['max_calls'])
    for name, function in breadth.__dict__.items():
        original = function.__wrapped__ if name == '_block' else function
        if isinstance(original, FunctionType) and original.__globals__ is breadth.__dict__:
            bound = FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
            bound.__kwdefaults__ = original.__kwdefaults__
            namespace[name] = lru_cache(**function.cache_parameters())(bound) if name == '_block' else bound
    return namespace


def validate_registry(*, old_ids=()):
    """Build all eight shards, rejecting any cross-shard or old-ID collision."""
    seen = set(breadth.goal._old_ids(old_ids))
    registry = {}
    for shard in SHARDS:
        worlds = runtime(shard)['build_worlds'](old_ids=seen)
        for world in worlds['TRAIN'] + worlds['PROBE']:
            seen.update(identifiers(world))
        registry[shard] = worlds
    return registry


def build_worlds(shard, *, old_ids=()):
    """Return this shard's TRAIN[8]/PROBE[2] after checking the whole registry."""
    runtime(shard)
    return validate_registry(old_ids=old_ids)[shard]


def _evidence(shard_documents):
    require(type(shard_documents) in (list, tuple) and len(shard_documents) == len(SHARDS),
            'all_eight_ordered_shard_documents_required')
    old_ids = set()
    for shard, document in enumerate(shard_documents):
        require(type(document) is dict and document.get('masters') == list(runtime(shard)['TRAIN_MASTERS']),
                'ordered_unique_shard_train_masters_only_no_probe')
        old_ids.update(breadth.goal._old_ids(document['old_ids']))
    validate_registry(old_ids=old_ids)
    for shard, document in enumerate(shard_documents):
        runtime(shard)['replay_lessons'](document)
    ready = all(document['fit_ready'] and len(document['rows']) == CAPS['max_rows'] for document in shard_documents)
    return breadth.goal.hop._seal(dict(schema=SCHEMA, shard_documents=deepcopy(list(shard_documents)),
        shards=list(SHARDS), old_ids=sorted(old_ids),
        shard_lesson_sha256=[document['lesson_sha256'] for document in shard_documents],
        masters=[master for shard in SHARDS for master in runtime(shard)['TRAIN_MASTERS']],
        protocol=breadth.PROTOCOL, expected_calls=TEACH_CALLS,
        model_calls=sum(document['model_calls'] for document in shard_documents),
        ready=ready, fit_ready=ready, fits=0, parent_present=True, claim=CLAIM,
        state_binding='NATIVE_CALLER_REQUIRED_NOT_VERIFIED_HERE',
        status='SCALE_LESSONS_READY_NO_FIT' if ready else 'SCALE_LESSONS_INCOMPLETE_NO_FIT'), 'evidence_sha256')


def _rows(evidence):
    if not evidence['fit_ready']:
        return []
    rows = []
    for shard, document in enumerate(evidence['shard_documents']):
        for source_row in document['rows']:
            row = {key: deepcopy(value) for key, value in source_row.items() if key not in ('provenance', 'row_sha256')}
            row.update(schema=SCHEMA, shard=shard, shard_row_index=source_row['row_index'], row_index=len(rows),
                       shard_row_sha256=source_row['row_sha256'], shard_evidence_sha256=source_row['evidence_sha256'],
                       evidence_sha256=evidence['evidence_sha256'])
            if not rows:
                row['provenance'] = deepcopy(evidence)
            rows.append(breadth.goal.hop._seal(row, 'row_sha256'))
    return rows


def aggregate_lessons(shard_documents):
    """Replay exactly shards 0..7; preserve negative evidence, never admit a subset."""
    evidence = _evidence(shard_documents)
    return breadth.goal.hop._seal(dict(evidence, rows=_rows(evidence)), 'lesson_sha256')


def _replay_evidence(evidence):
    require(type(evidence) is dict and evidence.get('schema') == SCHEMA, 'scale_lesson_required')
    verified = _evidence(evidence['shard_documents'])
    breadth.goal.lesson._same(evidence, verified, 'scale_evidence_replay_drift')
    return verified


def replay_lessons(document):
    require(type(document) is dict and document.get('schema') == SCHEMA, 'scale_lesson_required')
    evidence = {key: deepcopy(value) for key, value in document.items() if key not in ('rows', 'lesson_sha256')}
    verified = _replay_evidence(evidence)
    rows = _rows(verified)
    breadth.goal.lesson._same(document, breadth.goal.hop._seal(dict(verified, rows=rows), 'lesson_sha256'),
                             'scale_document_replay_drift')
    return rows


def encode_rows(rows, tokenizer):
    """Verify all 1,536 actual rows; reuse each unchanged shard's 192-row encoder."""
    require(type(rows) in (list, tuple) and len(rows) == MAX_ROWS, 'complete_1536_scale_rows_required')
    require(type(rows[0]) is dict and 'provenance' in rows[0], 'scale_row_provenance_required')
    evidence = _replay_evidence(rows[0]['provenance'])
    require(evidence['fit_ready'], 'all_scale_shards_must_be_fit_ready')
    breadth.goal.lesson._same(list(rows), _rows(evidence), 'scale_row_or_provenance_drift')
    return tuple(encoded for shard, document in enumerate(evidence['shard_documents'])
                 for encoded in runtime(shard)['encode_rows'](document['rows'], tokenizer))
