"""Frozen L2 cohort and wire contract shared by independent learner lanes."""

from types import FunctionType

from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import orch_replication as readout


SCHEMA = 'ORCH_L2_SHARED_V1'
FAMILY = 'ROUTE_GUIDED_CYCLES_L2_V1'
ARMS = ('SHORT', 'LONG', 'FROZEN', 'UNPARENTED')
INITIAL_STATE = 'e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf'
PORTABLE_SHA = '5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469'
TRAIN_MASTERS = tuple(tuple(f'ORCH-L2-SHARED-20260914-V1-TRAIN-C{cycle}-W{world}'
                            for world in range(8)) for cycle in range(1, 4))
HELD_MASTERS = tuple(tuple(f'ORCH-L2-SHARED-20260914-V1-HELD-R{stage}-W{world}'
                           for world in range(8)) for stage in range(4))
MASTERS = frozenset(master for group in TRAIN_MASTERS + HELD_MASTERS for master in group)
CAPS = dict(source_calls=448, learner_calls_per_lane=1600,
            parent_calls_per_parented_lane=600, all_calls=8648,
            updates_per_sleep=216, child_context=2048, child_generation=512,
            child_turns_per_episode=6, short_parent_opportunities_per_episode=3,
            short_parent_response_tokens=160, short_parent_distillation_calls=3,
            hours=12, short_gpu_hours=36)
RECIPE = dict(optimizer='AdamW', learning_rate=0.00003, seed=8203,
              optimizer_kwargs=dict(betas=[0.9, 0.999], eps=1e-8,
                                    weight_decay=0.01, amsgrad=False,
                                    foreach=False, fused=False),
              trajectory_presentations=4, legacy_sizes=[128, 20, 62, 12],
              batch_size=4, gradient_clip=None, cumulative_new_rows=False,
              zero_yield='NO_UPDATE_PRESERVE_PREVIOUS_CHILD_AND_FRESH_READOUT')


def runtime(master):
    hop.require(master in MASTERS, 'unfrozen_l2_master')
    namespace = dict(hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is hop.__dict__:
            defaults = (master,) if name == 'build_world' else function.__defaults__
            namespace[name] = FunctionType(function.__code__, namespace, name,
                                           defaults, function.__closure__)
    return namespace


def tasks(world):
    return [task for index, task in enumerate(readout.tasks(world)) if index in (0, 2)]


def cohort(exclusions):
    seen = set(exclusions)
    worlds = {}
    for master in sorted(MASTERS):
        world = runtime(master)['build_world'](master)
        identifiers = {value for edge in world['edges'] for value in edge.values()}
        hop.require(not identifiers.intersection(seen), 'release_namespace_collision')
        seen.update(identifiers)
        worlds[master] = world
    return dict(schema=SCHEMA, family=FAMILY, initial_state=INITIAL_STATE,
                train=[[worlds[master] for master in group] for group in TRAIN_MASTERS],
                held=[[worlds[master] for master in group] for group in HELD_MASTERS],
                exclusions_sha256=hop.document_sha256(sorted(exclusions)),
                caps=CAPS, recipe=RECIPE,
                denominators=dict(experience_worlds_per_cycle=8,
                    experience_episodes_per_cycle=16, held_worlds_per_readout=8,
                    held_episodes_per_readout=16, readouts_per_lane=4,
                    sleep_cycles_per_learning_lane=3, max_new_rows_per_sleep=96,
                    parent_opportunities_per_short_cycle=48,
                    science_lanes=4, independent_training_seeds=1))


def source_document(frozen, generate, emit):
    collections, store = [], {}
    for group in frozen['train'] + frozen['held']:
        for world in group:
            collection = runtime(world['master'])['collect_world'](world, generate)
            runtime(world['master'])['replay_collection'](collection)
            collections.append(collection)
            for record in collection['records']:
                if record['accepted']:
                    store[record['edge']['event']] = record['event']['raw']
            emit(world['master'] + '.json', collection)
    return dict(schema=SCHEMA, cohort_sha256=hop.document_sha256(frozen),
                collections=collections, store=store, store_sha256=hop.document_sha256(store),
                source_policy='ONE_INITIAL_CHILD_SOURCE_SHARED_ALL_LANES_NO_REGENERATION',
                source_world_denominator=56, source_event_denominator=224)


def verify_source(frozen, document):
    hop.require(document['cohort_sha256'] == hop.document_sha256(frozen), 'cohort_drift')
    worlds = [world for group in frozen['train'] + frozen['held'] for world in group]
    hop.require(len(document['collections']) == len(worlds), 'source_world_denominator_drift')
    store = {}
    for world, collection in zip(worlds, document['collections']):
        hop.require(collection['world'] == world, 'source_world_drift')
        runtime(world['master'])['replay_collection'](collection)
        for record in collection['records']:
            if record['accepted']:
                store[record['edge']['event']] = record['event']['raw']
    hop.require(store == document['store'] and hop.document_sha256(store) == document['store_sha256'],
                'source_bytes_drift')
    return store
