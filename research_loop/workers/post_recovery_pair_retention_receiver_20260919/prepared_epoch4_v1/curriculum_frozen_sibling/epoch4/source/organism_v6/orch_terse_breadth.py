"""Prospective sixteen-shard specialization of the existing goal-quality APIs."""

from copy import deepcopy
from functools import lru_cache
from types import FunctionType, SimpleNamespace

from organism_v6 import experienced_event_goal_quality as quality
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


PREFIX = 'ORCH-TERSE-BREADTH-20260914-V1'
SHARDS = tuple(range(16))
SEEDS = (7801, 7802)
SEED_DOSES = ((7801, 4), (7802, 4), (7801, 16))
ARMS = ('FULL_TARGET', 'NEW_TRAJECTORY_LOSS_OFF')
MIN_TARGETS = 1000
MAX_TARGETS = 3072
require = quality.require
digest = quality.document_sha256


def bind_module(module, overrides):
    namespace = dict(vars(module), **overrides)
    for name, candidate in vars(module).items():
        function = getattr(candidate, '__wrapped__', candidate)
        if isinstance(function, FunctionType) and function.__globals__ is vars(module):
            bound = FunctionType(function.__code__, namespace, function.__name__,
                                 function.__defaults__, function.__closure__)
            bound.__kwdefaults__ = function.__kwdefaults__
            namespace[name] = lru_cache(**candidate.cache_parameters())(bound) if hasattr(candidate, 'cache_parameters') else bound
    namespace.update(overrides)
    return namespace


@lru_cache(maxsize=16)
def runtime(shard):
    require(type(shard) is int and shard in SHARDS, 'fixed_sixteen_shards_required')
    prefix = f'{PREFIX}-SHARD-{shard}'
    blocks = tuple(f'{prefix}-BLOCK-{index}' for index in range(4))
    trained = tuple(f'{block}-TRAIN-{suffix}' for block in blocks for suffix in ('A', 'B'))
    probes = tuple(f'{blocks[0]}-PROBE-{suffix}' for suffix in ('A', 'B'))
    mapping = {master: index // 2 for index, master in enumerate(trained)}
    mapping.update(dict.fromkeys(probes, 0))
    return SimpleNamespace(**bind_module(quality.scale.breadth,
        dict(PREFIX=prefix, BLOCK_PREFIXES=blocks, TRAIN_MASTERS=trained,
             PROBE_MASTERS=probes, MASTERS=trained + probes, MASTER_BLOCK=mapping)))


def registry(old_ids):
    seen = set(old_ids)
    for worlds in quality.scale.validate_registry(old_ids=old_ids).values():
        for world in worlds['TRAIN'] + worlds['PROBE']:
            seen.update(quality.scale.identifiers(world))
    result = []
    for shard in SHARDS:
        worlds = runtime(shard).build_worlds(old_ids=seen)
        for world in worlds['TRAIN'] + worlds['PROBE']:
            identifiers = set(quality.scale.identifiers(world))
            require(not identifiers.intersection(seen), 'fresh_world_identifier_collision')
            seen.update(identifiers)
        result.append(worlds)
    return result


def collect_quality(shard, collection, invoke, offset=0):
    namespace = bind_module(quality, dict(runtime=runtime))
    return namespace['_collect_world'](shard, collection, invoke, offset)


def replay_quality(shard, document):
    captures = iter(document['evidence']['captures'])

    def invoke(messages, metadata):
        capture = next(captures, None)
        require(capture is not None, 'missing_native_capture')
        quality.same(capture['messages'], messages, 'native_guidance_drift')
        quality.same({key: capture[key] for key in metadata}, metadata, 'native_metadata_drift')
        return {key: deepcopy(capture[key]) for key in ('response', 'error')}

    first = document['evidence']['captures'][0]['call_index']
    replayed = collect_quality(shard, document['evidence']['collection'], invoke, first)
    require(next(captures, None) is None, 'extra_native_capture')
    quality.same(replayed, document, 'quality_projection_drift')
    return replayed


def qualified_rows(documents, held_worlds):
    rows = []
    for shard, document in documents:
        replay_quality(shard, document)
        rows.extend(deepcopy(document['quality']['rows']))
    keys = [digest(dict(prefix=row['prefix'], assistant=row['assistant'])) for row in rows]
    require(len(keys) == len(set(keys)), 'distinct_qualified_targets_required')
    require(MIN_TARGETS <= len(rows) <= MAX_TARGETS and len(rows) % 12 == 0,
            'minimum_thousand_quality_pair_targets_required')
    held_ids = set().union(*(quality.scale.identifiers(world) for world in held_worlds))
    for row in rows:
        require(row['master'] in runtime(row['shard']).TRAIN_MASTERS, 'held_target_forbidden')
        require(all(quality.lesson.PARENT_GUIDANCE not in message['content'] for message in row['prefix']),
                'parent_guidance_forbidden')
        text = quality.hop.json.dumps(dict(prefix=row['prefix'], assistant=row['assistant']))
        require(not any(identifier in text for identifier in held_ids), 'held_identifier_in_training')
    return rows


def updates(new_count, presentations=4):
    require(type(new_count) is int and MIN_TARGETS <= new_count <= MAX_TARGETS and new_count % 12 == 0,
            'qualified_corpus_size_required')
    require(type(presentations) is int and presentations in (4, 16), 'four_or_sixteen_presentations_required')
    return GoalReplayLayout(new_count, presentations).updates


def indexes(update, new_count, presentations=4):
    require(type(update) is int and 1 <= update <= updates(new_count, presentations), 'bounded_update_required')
    return GoalReplayLayout(new_count, presentations).training_indexes(update)
