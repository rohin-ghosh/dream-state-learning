"""Versioned next-batch prompts and CODE-first ordering for Rohin98."""

from types import FunctionType

from organism_v6 import orch_rich_hot_node2_supply as previous


MAX_CALLS = previous.MAX_CALLS
CALLS_PER_SHARD = previous.CALLS_PER_SHARD
MAX_BATCHES = previous.MAX_BATCHES
TASKS_PER_BATCH = previous.TASKS_PER_BATCH
ALTERNATIVE = (
    'When relevant, before your final answer or action, state the consequential '
    'alternative you actually considered and why the available evidence led you '
    'to reject it. If no consequential alternative is relevant, do not invent '
    'a branch, disagreement or padding. Do not claim to have run a test or '
    'observed evidence that was not supplied. '
)
GUIDANCE = (
    'Ground your reasoning in the actual task and observations. Explain the '
    'useful operation, uncertainty and check without forced length or padding. '
) + ALTERNATIVE


def cohort(records, old_tasks):
    document = previous.cohort(records, old_tasks)
    document.update(schema='ORCH_RICH_HOT_NODE2_FLOOR98_V1', prompt_version='FLOOR98_CONSEQUENTIAL_ALTERNATIVE_V1',
                    branching_measurement='Sampled semantic annotation only; no keyword/count proof.',
                    first_person_gate=False, length_150_400_gate=False, first_family_per_shard='code')
    return document


def task_at(document, batch, position):
    previous.hot.require(0 <= position < TASKS_PER_BATCH, 'bounded_supply_cursor')
    family_index = (1, 0, 2)[(position % 6) // 2]
    pool_position = 2 * (position // 6) + position % 2
    task = previous.task_at(document, batch, pool_position * 3 + family_index)
    task.update(id=f'B{batch:03d}-P{position:02d}', position=position)
    return task


def messages(task, condition, previous_response=None):
    result = previous.messages(task, condition, previous_response)
    result[0] = dict(result[0], content=result[0]['content'] + '\n' + ALTERNATIVE)
    return result


def outcome(task, response):
    return dict(previous.outcome(task, response), branching_semantic_annotation='UNREVIEWED',
                first_person_gate=False, length_150_400_gate=False)


def route_task(task, condition, generate):
    world = task['payload']
    environment = previous.runtime(world['master'])
    collection = environment['collect_world'](world, lambda messages: generate('exposure', messages))
    environment['replay_collection'](collection)
    store = {record['edge']['event']: record['event']['raw'] for record in collection['records'] if record['accepted']}
    namespace = dict(previous.route.__dict__, GUIDANCE=GUIDANCE + (previous.BRANCH if condition != 'ORIGINAL_RICH' else ''))
    episode = FunctionType(previous.route.episode.__code__, namespace, 'episode', previous.route.episode.__defaults__)
    tasks = [public for index, public in enumerate(environment['build_tasks'](world)) if index in (0, 2)]
    episodes = [episode(world, public, lambda messages, goal=goal: generate(f'goal{goal}', messages), store)
                for goal, public in enumerate(tasks)]
    return dict(collection=collection, episodes=episodes, accepted_events=collection['accepted_events'],
                complete_routes=sum(record['correct'] for record in episodes), route_denominator=2,
                attempted_routes_are_not_gold=True, semantic_status='UNREVIEWED', trainingAllowed=False,
                branching_semantic_annotation='UNREVIEWED', first_person_gate=False, length_150_400_gate=False)
