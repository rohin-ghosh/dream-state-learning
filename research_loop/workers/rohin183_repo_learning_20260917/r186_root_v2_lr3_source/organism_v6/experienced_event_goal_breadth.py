"""Four actual 48-turn goal-pair blocks, with all-or-none sleep admission.

Eight closed TRAIN worlds and two PROBE worlds reuse the unchanged goal-pair
runtime, planner and encoder through private per-block bindings. Only block 0
has PROBE worlds. No actor, tokenizer, model or training runtime is loaded.
Replay proves internal consistency; callers authenticate native source/calls.
"""

from copy import deepcopy
from functools import lru_cache
from types import FunctionType

from organism_v6 import experienced_event_goal_pairs as goal


PREFIX = 'ASTRA-GOALBREADTH-20260914-V1'
BLOCK_PREFIXES = tuple(PREFIX + '-BLOCK-' + str(index) for index in range(4))
TRAIN_MASTERS = tuple(prefix + '-TRAIN-' + suffix for prefix in BLOCK_PREFIXES for suffix in ('A', 'B'))
PROBE_MASTERS = tuple(BLOCK_PREFIXES[0] + '-PROBE-' + suffix for suffix in ('A', 'B'))
MASTERS = TRAIN_MASTERS + PROBE_MASTERS
MASTER_BLOCK = {master: index // 2 for index, master in enumerate(TRAIN_MASTERS)}
MASTER_BLOCK.update(dict.fromkeys(PROBE_MASTERS, 0))
SCHEMA = 'DEV_EXPERIENCED_EVENT_GOAL_BREADTH_V1'
EXPOSE_CALLS = 80
TEACH_CALLS = MAX_CALLS = MAX_ROWS = 192
BASELINE_TRAIN_CALLS = 192
BASELINE_PROBE_CALLS = 96
BASELINE_CALLS = BASELINE_TRAIN_CALLS + BASELINE_PROBE_CALLS
MAX_CONTEXT = goal.MAX_CONTEXT
MAX_NEW_TOKENS = goal.MAX_NEW_TOKENS
MAX_WORLD_CALLS = goal.MAX_WORLD_CALLS
TASK_INDEXES = goal.TASK_INDEXES
GOAL_PAIRS = goal.GOAL_PAIRS
PROTOCOL = goal.PROTOCOL
TARGET_EOT = goal.TARGET_EOT
LOSS_POLICY = deepcopy(goal.LOSS_POLICY)
CLAIM = 'EIGHT_FIXED_TRAIN_WORLDS_PAIRED_SOURCE_USE_NOT_GENERAL_PLANNING_OR_H1_H2'
require = goal.require
document_sha256 = goal.document_sha256
identifiers = goal.identifiers


@lru_cache(maxsize=4)
def _block(index):
    """Bind cached and uncached goal functions without sharing mutable globals."""
    require(type(index) is int and 0 <= index < 4, 'fixed_breadth_block_required')
    trained = TRAIN_MASTERS[2 * index:2 * index + 2]
    probes = PROBE_MASTERS if index == 0 else ()
    namespace = dict(goal.__dict__, PREFIX=BLOCK_PREFIXES[index], TRAIN_MASTERS=trained,
                     PROBE_MASTERS=probes, MASTERS=trained + probes)
    for name, function in goal.__dict__.items():
        original = function.__wrapped__ if name == '_runtime' else function
        if isinstance(original, FunctionType) and original.__globals__ is goal.__dict__:
            bound = FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
            bound.__kwdefaults__ = original.__kwdefaults__
            namespace[name] = lru_cache(**function.cache_parameters())(bound) if name == '_runtime' else bound
    return namespace


def _for_master(master):
    require(type(master) is str and master in MASTERS, 'closed_breadth_master_required')
    return _block(MASTER_BLOCK[master])


def _for_world(world):
    require(type(world) is dict, 'breadth_world_required')
    return _for_master(world.get('master'))


def _for_collection(collection):
    require(type(collection) is dict, 'breadth_collection_required')
    return _for_world(collection.get('world'))


def build_world(master, *, old_ids=()):
    return _for_master(master)['build_world'](master, old_ids=old_ids)


def build_worlds(*, old_ids=()):
    """Return TRAIN[8]/PROBE[2], disjoint internally and from caller old IDs."""
    seen = set(goal._old_ids(old_ids))
    worlds = {}
    for split, masters in (('TRAIN', TRAIN_MASTERS), ('PROBE', PROBE_MASTERS)):
        worlds[split] = []
        for master in masters:
            world = build_world(master, old_ids=seen)
            seen.update(identifiers(world))
            worlds[split].append(world)
    return worlds


def validate_world(world, *, old_ids=()):
    return _for_world(world)['validate_world'](world, old_ids=old_ids)


def collect_world(world, generate, *, old_ids=()):
    return _for_world(world)['collect_world'](world, generate, old_ids=old_ids)


def replay_collection(collection, *, old_ids=()):
    return _for_collection(collection)['replay_collection'](collection, old_ids=old_ids)


def exact_text_store(collection):
    return _for_collection(collection)['exact_text_store'](collection)


def build_tasks(world):
    return _for_world(world)['build_tasks'](world)


def run_episode(world, task, actor, memory):
    return _for_world(world)['run_episode'](world, task, actor, memory)


def replay_episode(world, task, episode):
    return _for_world(world)['replay_episode'](world, task, episode)


def build_cases(collection):
    return _for_collection(collection)['build_cases'](collection)


def summarize_pairs(collection, episodes):
    return _for_collection(collection)['summarize_pairs'](collection, episodes)


def _evidence(blocks, old_ids):
    captures, episodes = [], []
    for block_index, block in enumerate(blocks):
        for capture in block['captures']:
            entry = deepcopy(capture)
            entry.update(block_index=block_index, block_call_index=capture['call_index'],
                         block_world_index=capture['world_index'], block_call_sha256=entry.pop('call_sha256'),
                         call_index=len(captures), world_index=2 * block_index + capture['world_index'])
            captures.append(goal.hop._seal(entry, 'call_sha256'))
        for episode in block['episodes']:
            entry = deepcopy(episode)
            entry.update(block_index=block_index, block_world_index=episode['world_index'],
                         world_index=2 * block_index + episode['world_index'])
            episodes.append(entry)
    ready = (len(blocks) == 4 and len(captures) == TEACH_CALLS
             and all(block['fit_ready'] and len(block['rows']) == goal.MAX_ROWS for block in blocks))
    return goal.hop._seal(dict(schema=SCHEMA, blocks=deepcopy(blocks), old_ids=list(old_ids),
        collections=[deepcopy(collection) for block in blocks for collection in block['collections']],
        captures=captures, episodes=episodes,
        summaries=[deepcopy(summary) for block in blocks for summary in block['summaries']],
        masters=list(TRAIN_MASTERS), task_indexes=list(TASK_INDEXES), protocol=PROTOCOL,
        expected_calls=TEACH_CALLS, model_calls=len(captures), ready=ready, fit_ready=ready,
        fits=0, parent_present=True, parent_kind='ALGORITHMIC_SOURCE_INFORMED_RESEARCHER_INSTRUCTION',
        claim=CLAIM, status='BREADTH_LESSONS_READY_NO_FIT' if ready else 'BREADTH_LESSONS_INCOMPLETE_NO_FIT'), 'evidence_sha256')


def _rows(evidence):
    if not evidence['fit_ready']:
        return []
    rows = []
    for block_index, block in enumerate(evidence['blocks']):
        for source_row in block['rows']:
            row = {key: deepcopy(value) for key, value in source_row.items() if key not in ('provenance', 'row_sha256')}
            row.update(schema=SCHEMA, block_index=block_index, block_row_index=source_row['row_index'],
                block_world_index=source_row['world_index'], block_evidence_sha256=source_row['evidence_sha256'],
                block_call_sha256=source_row['call_sha256'], row_index=len(rows), call_index=len(rows),
                world_index=2 * block_index + source_row['world_index'], evidence_sha256=evidence['evidence_sha256'],
                call_sha256=evidence['captures'][len(rows)]['call_sha256'])
            if not rows:
                row['provenance'] = deepcopy(evidence)
            rows.append(goal.hop._seal(row, 'row_sha256'))
    return rows


def collect_lessons(collections, generate, *, old_ids=()):
    """Attempt all four blocks; never repair/drop failures or admit a subset.

    Input order is TRAIN_MASTERS. Flat native captures have global call/world
    indexes plus original block indexes/hashes; blocks retain original evidence.
    Only all four successful blocks emit 192 rows. Row zero holds bundle evidence.
    """
    require(callable(generate), 'generation_callback_required')
    old_ids = goal._old_ids(old_ids)
    build_worlds(old_ids=old_ids)
    require(type(collections) in (list, tuple) and len(collections) == 8, 'all_eight_training_collections_required')
    collections = [replay_collection(collection, old_ids=old_ids) for collection in collections]
    require(tuple(collection['master'] for collection in collections) == TRAIN_MASTERS,
            'ordered_eight_train_worlds_only_no_probe')
    blocks = [_block(index)['collect_lessons'](collections[2 * index:2 * index + 2], generate, old_ids=old_ids)
              for index in range(4)]
    evidence = _evidence(blocks, old_ids)
    return goal.hop._seal(dict(evidence, rows=_rows(evidence)), 'lesson_sha256')


def _replay_evidence(evidence):
    require(type(evidence) is dict and evidence.get('schema') == SCHEMA, 'breadth_lesson_required')
    old_ids = goal._old_ids(evidence['old_ids'])
    build_worlds(old_ids=old_ids)
    blocks = evidence['blocks']
    require(type(blocks) is list and len(blocks) == 4, 'all_four_breadth_blocks_required')
    for index, block in enumerate(blocks):
        require(type(block) is dict and block.get('old_ids') == old_ids, 'breadth_block_old_ids_drift')
        _block(index)['replay_lessons'](block)
    verified = _evidence(blocks, old_ids)
    goal.lesson._same(evidence, verified, 'breadth_evidence_replay_drift')
    return verified


def replay_lessons(document):
    require(type(document) is dict and document.get('schema') == SCHEMA, 'breadth_lesson_required')
    evidence = {key: deepcopy(value) for key, value in document.items() if key not in ('rows', 'lesson_sha256')}
    verified = _replay_evidence(evidence)
    rows = _rows(verified)
    goal.lesson._same(document, goal.hop._seal(dict(verified, rows=rows), 'lesson_sha256'), 'breadth_document_replay_drift')
    return rows


def encode_rows(rows, tokenizer):
    """Validate all 192 rows, then reuse each unchanged 48-row block encoder."""
    require(type(rows) in (list, tuple) and len(rows) == MAX_ROWS, 'complete_192_breadth_rows_required')
    require(type(rows[0]) is dict and 'provenance' in rows[0], 'breadth_row_provenance_required')
    evidence = _replay_evidence(rows[0]['provenance'])
    require(evidence['fit_ready'], 'all_breadth_blocks_must_be_fit_ready')
    goal.lesson._same(list(rows), _rows(evidence), 'breadth_row_or_provenance_drift')
    return tuple(encoded for index, block in enumerate(evidence['blocks'])
                 for encoded in _block(index)['encode_rows'](block['rows'], tokenizer))
