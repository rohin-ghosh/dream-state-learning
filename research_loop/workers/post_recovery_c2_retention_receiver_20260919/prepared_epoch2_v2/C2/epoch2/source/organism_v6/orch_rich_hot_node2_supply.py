"""Prospective TRAIN-only mixed supply using unchanged bounded code/route gyms."""

from types import FunctionType

from organism_v6 import experienced_event_two_hop as hop
from organism_v6 import orch_code_bounded as bounded_code
from organism_v6 import orch_full_rich as route
from organism_v6 import orch_persist_code as ledger
from organism_v6 import orch_rich_hot_node2 as hot


MAX_CALLS = 65536
CALLS_PER_SHARD = MAX_CALLS // 8
MAX_BATCHES = 256
TASKS_PER_BATCH = 24
ROUTE_WORLDS = 256
NAMESPACE = 'ORCH-RICH-HOT-NODE2-20260915-SUPPLY-TRAIN-'
GUIDANCE = (
    'Use your own first-person reasoning grounded in the actual task and observations. '
    'Explain the consequential operation or uncertainty, a useful check, and what '
    'you would reuse. Do not invent execution, evidence, disagreements or padding. '
    'No fixed length is required; stop when useful reasoning is complete. '
)
BRANCH = (
    'Explore relevant alternatives and prioritize the branch that could change the '
    'result. Evaluate the provisional conclusion against actual available evidence. '
)


def runtime(master):
    hot.require(master.startswith(NAMESPACE) and master[len(NAMESPACE):].isdigit(), 'supply_train_namespace_only')
    namespace = dict(hop.__dict__, MASTER=master, TRANSFER_MASTER=master)
    for name, function in hop.__dict__.items():
        if isinstance(function, FunctionType) and function.__globals__ is hop.__dict__:
            namespace[name] = FunctionType(function.__code__, namespace, name,
                (master,) if name == 'build_world' else function.__defaults__, function.__closure__)
    return namespace


def cohort(records, previous):
    excluded_ids = set(previous['excluded_ids']) | {task['id'] for task in previous['tasks']}
    excluded_questions = set(previous['excluded_question_hashes']) | {task['question_sha256'] for task in previous['tasks']}
    math = hot.roster(records, excluded_ids, excluded_questions)
    worlds = [runtime(NAMESPACE + str(index))['build_world'](NAMESPACE + str(index)) for index in range(ROUTE_WORLDS)]
    edges = [edge for world in worlds for edge in world['edges']]
    for field in ('event', 'port', 'receipt'):
        hot.require(len({edge[field] for edge in edges}) == len(edges), 'route_namespace_collision')
    return dict(schema='ORCH_RICH_HOT_NODE2_SUPPLY_V1', math=math, code=ledger.build_tasks(), route=worlds,
                max_calls=MAX_CALLS, calls_per_shard=CALLS_PER_SHARD, max_batches=MAX_BATCHES,
                tasks_per_batch=TASKS_PER_BATCH, max_new_tokens=hot.CAP, context=hot.CONTEXT,
                repeats='Explicit repeated TRAIN source identities after finite pools cycle; not new tasks.',
                route_claim='Own scheduled exposure plus two real route episodes; no teacher EVENT targets.',
                held_access=False, parent_calls=0, fits=0, semantic_admissions=0)


def task_at(document, batch, position):
    hot.require(0 <= batch < MAX_BATCHES and 0 <= position < TASKS_PER_BATCH, 'bounded_supply_cursor')
    family = ('math', 'code', 'route')[position % 3]
    pool = document['math']['tasks'] if family == 'math' else document[family]
    ordinal = batch * (TASKS_PER_BATCH // 3) + position // 3
    original = pool[ordinal % len(pool)]
    source_id = original['master'] if family == 'route' else original['id']
    return dict(id=f'B{batch:03d}-P{position:02d}', family=family, source_task_id=source_id,
                repeated_train_source=ordinal >= len(pool), payload=original, batch=batch, position=position)


def messages(task, condition, previous=None):
    hot.require(condition in hot.CONDITIONS, 'known_condition')
    if task['family'] == 'math':
        return hot.messages(task['payload'], condition, previous)
    hot.require(task['family'] == 'code', 'route_uses_actual_environment')
    public = task['payload']['spec'] + '\n' + ledger.HELPER_SPEC
    public += '\nFinish with a JSON object on its own last line: {"expression":"..."}.'
    guidance = GUIDANCE + (BRANCH if condition != 'ORIGINAL_RICH' else '')
    result = [dict(role='system', content=guidance), dict(role='user', content=public)]
    if previous is not None:
        instruction = ('Develop your own prior attempt with a useful check.' if condition == 'TWO_PASS' else
                       'Evaluate your own prior attempt, prioritizing the uncertainty most likely to change it.')
        result += [dict(role='assistant', content=previous), dict(role='user', content=instruction +
                   ' No execution feedback has been supplied. Do not invent tests run. Finish with the expression JSON last line.')]
    return result


def outcome(task, response):
    if task['family'] == 'math':
        return hot.outcome(task['payload'], response)
    result = dict(correct=None, semantic_status='UNREVIEWED', admitted=False, trainingAllowed=False,
                  content_tokens=len(response['token_ids']) - int(response['terminal']))
    if response['truncated']:
        return dict(result, category='truncation')
    if not response['terminal']:
        return dict(result, category='nonterminal_other')
    if task['family'] == 'route':
        return dict(result, category='route_response_requires_task_receipt')
    try:
        expression, unused_reasoning = bounded_code.parse_action(response['raw'])
    except (ValueError, IndexError, TypeError) as error:
        return dict(result, category='missing_exact_expression_JSON', parse_error=str(error))
    feedback = ledger.check_expression(task['payload'], expression)
    return dict(result, category='registered_correct' if feedback['success'] else 'bounded_oracle_failed',
                correct=feedback['success'], expression=expression, verifier=feedback)


def route_task(task, condition, generate):
    world = task['payload']
    environment = runtime(world['master'])
    collection = environment['collect_world'](world, lambda messages: generate('exposure', messages))
    environment['replay_collection'](collection)
    store = {record['edge']['event']: record['event']['raw'] for record in collection['records'] if record['accepted']}
    namespace = dict(route.__dict__, GUIDANCE=GUIDANCE + (BRANCH if condition != 'ORIGINAL_RICH' else ''))
    episode = FunctionType(route.episode.__code__, namespace, 'episode', route.episode.__defaults__)
    tasks = [public for index, public in enumerate(environment['build_tasks'](world)) if index in (0, 2)]
    episodes = [episode(world, public, lambda messages, goal=goal: generate(f'goal{goal}', messages), store)
                for goal, public in enumerate(tasks)]
    return dict(collection=collection, episodes=episodes, accepted_events=collection['accepted_events'],
                complete_routes=sum(record['correct'] for record in episodes), route_denominator=2,
                attempted_routes_are_not_gold=True, semantic_status='UNREVIEWED', trainingAllowed=False)
