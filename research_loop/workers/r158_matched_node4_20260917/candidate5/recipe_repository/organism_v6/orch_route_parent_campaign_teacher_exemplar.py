"""Held-excluded, teacher-labelled exemplars; deliberately no trainer interface."""

from fractions import Fraction
import json

from organism_v6 import orch_route_parent_campaign as route


LABEL = 'TEACHER_DISTILLATION'
MODEL = 'openai/openai/gpt-6-astra'
SYSTEM = (
    'Write a rich, clearly explained TEACHER_DISTILLATION exemplar for the supplied TRAIN problem. '
    'Give at least two genuinely different solution methods and explicit consistency checks. '
    'These are worked educational solutions, not a report of hidden deliberation or executed tools. '
    'Use only the supplied problem and observed event evidence; do not invent observations. '
    'Distinguish reasoned checks from actual tool execution: no tools are available. '
    'Return exactly one JSON object with keys source_label, methods, final_answer, checks, limitations. '
    'source_label must be TEACHER_DISTILLATION. methods is a list of objects with name and explanation; '
    'checks is a list of strings; limitations and final_answer are strings. '
    'For math, final_answer is only the requested number. For route, final_answer is the two commands '
    'ROUTE <port>; ROUTE <port>, with exact case-sensitive supplied ports. '
    'For route, compare forward graph traversal and backward goal/constraint reasoning, explain '
    'why alternatives fail, and cite supplied event evidence. For math, use two distinct derivations '
    'where feasible and check the answer against the original quantities. '
    'Never claim this teacher response was generated or experienced by the learner. '
    'Never produce a learner replay, an ingestion instruction, or an unlabelled training example.'
)


def validate_prompt(prompt):
    route.require(set(prompt) == {'source_label', 'split', 'task_id', 'domain', 'problem', 'observed_events'},
                  'exact_teacher_prompt_allowlist')
    route.require(prompt['source_label'] == LABEL and prompt['split'] == 'TRAIN', 'teacher_train_label')
    route.require('TRAIN' in prompt['task_id'] and prompt['domain'] in ('math', 'route'), 'existing_train_task')
    text = json.dumps(prompt, sort_keys=True)
    route.require(not any(token in text for token in ('HELD', 'sealed_score', '/tmp/', 'gold', 'readout_score')),
                  'teacher_visibility_boundary')
    route.require(isinstance(prompt['problem'], str) and isinstance(prompt['observed_events'], list), 'prompt_types')
    return prompt


def freeze_tasks(math_cohort, route_cohort, source):
    route.require(source['cohort_sha256'] == route.digest(route_cohort), 'original_route_cohort_join')
    tasks, checks = [], {}
    held_math = [task for group in math_cohort['held'] for task in group]
    held_math_ids = {task['id'] for task in held_math}
    held_questions = {task['question_sha256'] for task in held_math}
    for task in math_cohort['train'][0]:
        route.require(task['split'] == 'TRAIN' and task['id'] not in held_math_ids
            and task['id'] not in math_cohort['excluded_ids']
            and task['question_sha256'] not in held_questions
            and task['question_sha256'] not in math_cohort['excluded_question_hashes'], 'math_train_exclusion')
        prompt = dict(source_label=LABEL, split='TRAIN', task_id=task['id'], domain='math',
            problem=task['question'], observed_events=[])
        tasks.append(validate_prompt(prompt))
        checks[task['id']] = dict(domain='math', answer=task['gold'])
    route.require(len(tasks) == 8, 'eight_existing_math_train_tasks')
    held_worlds = [world for group in route_cohort['held'] for world in group]
    held_ids = {value for world in held_worlds for edge in world['edges'] for value in edge.values()}
    collections = {collection['master']: collection for collection in source['collections']}
    for world in route_cohort['train'][0]:
        route.require('TRAIN' in world['master'], 'route_train_only')
        route.require(not {value for edge in world['edges'] for value in edge.values()} & held_ids, 'route_held_exclusion')
        collection = collections[world['master']]
        route.require(collection['world'] == world, 'original_route_world_join')
        route.runtime(world['master'])['replay_collection'](collection)
        events = [record['event']['raw'] for record in collection['records'] if record['accepted']]
        observed_edges = [record['edge'] for record in collection['records'] if record['accepted']]
        for ordinal, task in enumerate(route.shared.tasks(world)):
            task_id = world['master'] + f'-GOAL{ordinal}'
            problem = ('Find a two-command route from ' + task['node'] + ' to ' + task['goal'] +
                '. Initial ports: ' + ','.join(task['ports']) +
                '. Identifiers are opaque and case-sensitive. The supplied event records are the observed transition evidence.')
            prompt = dict(source_label=LABEL, split='TRAIN', task_id=task_id, domain='route',
                problem=problem, observed_events=events)
            route.require(not any(identifier in json.dumps(prompt) for identifier in held_ids), 'no_held_identifier_in_teacher_prompt')
            tasks.append(validate_prompt(prompt))
            checks[task_id] = dict(domain='route', start=task['node'], goal=task['goal'], observed_edges=observed_edges)
    route.require(len(tasks) == 16 and len({task['task_id'] for task in tasks}) == 16, 'fixed_sixteen_task_roster')
    return tasks, checks, dict(math_held_ids=len(held_math_ids), math_held_question_hashes=len(held_questions),
        route_held_identifiers=len(held_ids), selection='FIRST_EXISTING_TRAIN_GROUPS_FIXED_ORDER_NO_OUTCOME_SELECTION',
        held_outcomes_read=False, regenerated_tasks=False)


def parse_response(envelope):
    route.require(envelope.get('model') == MODEL, 'actual_verified_primary_identity')
    route.require(envelope.get('status') == 'completed' and not envelope.get('error'), 'completed_teacher_response')
    route.require(envelope.get('usage', {}).get('output_tokens', 8193) <= 8192, 'observed_output_budget')
    output = envelope.get('output', [])
    route.require(all(item.get('type') in ('reasoning', 'message') for item in output), 'teacher_tool_calls_forbidden')
    messages = [part['text'] for item in output if item.get('type') == 'message'
        for part in item.get('content', []) if part.get('type') == 'output_text']
    route.require(len(messages) == 1 and bool(envelope.get('usage')), 'one_teacher_message_with_usage')
    raw = messages[0]
    if raw.startswith('```json\n') and raw.endswith('\n```'):
        raw = raw[8:-4]
    response = json.loads(raw)
    route.require(set(response) == {'source_label', 'methods', 'final_answer', 'checks', 'limitations'}
        and response['source_label'] == LABEL, 'explicit_teacher_response_label')
    route.require(isinstance(response['methods'], list) and 2 <= len(response['methods']) <= 6,
        'multiple_teacher_methods')
    route.require(all(isinstance(method, dict) and set(method) == {'name', 'explanation'}
        and isinstance(method['name'], str) and isinstance(method['explanation'], str)
        and len(method['explanation'].split()) >= 20 for method in response['methods']), 'substantive_method_fields')
    route.require(len({method['name'] for method in response['methods']}) == len(response['methods']), 'distinct_named_methods')
    route.require(isinstance(response['final_answer'], str) and isinstance(response['limitations'], str)
        and isinstance(response['checks'], list) and len(response['checks']) >= 2
        and all(isinstance(check, str) for check in response['checks']), 'teacher_answer_and_checks')
    return response


def check_answer(response, oracle):
    if oracle['domain'] == 'math':
        try:
            correct = Fraction(response['final_answer'].strip()) == Fraction(oracle['answer'])
        except (ValueError, ZeroDivisionError):
            correct = False
    else:
        commands = [command.strip() for command in response['final_answer'].split(';')]
        current = oracle['start']
        correct = len(commands) == 2
        for command in commands:
            matching = [edge for edge in oracle['observed_edges'] if edge['node'] == current
                and command == 'ROUTE ' + edge['port']]
            if len(matching) != 1:
                correct = False
                break
            current = matching[0]['outcome']
        correct = correct and current == oracle['goal']
    return dict(final_answer_correct=correct, denominator=1,
        method_proofs='NOT_INDEPENDENTLY_VERIFIED', runtime_execution_claim=False,
        source_label=LABEL, ingestion_authorized=False)
