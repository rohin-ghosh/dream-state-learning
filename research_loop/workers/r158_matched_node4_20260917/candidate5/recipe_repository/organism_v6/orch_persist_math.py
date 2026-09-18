"""Small finite-ring curriculum; only child-proposed records enter memory."""

from copy import deepcopy
import hashlib
import json


FAMILIES = {
    'L1mining': 'PM_AFFINE_POWER_V1',
    'heldL1validation': 'PM_AFFINE_WORD_V1',
    'L2proposal': 'PM_CONGRUENCE_JOIN_V1',
    'heldL3proposal': 'PM_LINEAR_RECURRENCE_V1',
}
BLOCKS = ((17, 3, 5), (19, 7, 4), (23, 5, 9), (29, 11, 6))
SCREEN_STEPS = (11, 23, 47, 59)
MAX_CALLS = 32
MAX_TURNS = 2
MAX_CONTEXT = 2048
MAX_GENERATED = 512


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def curriculum(instances_per_block=32):
    if type(instances_per_block) is not int or not 1 <= instances_per_block <= 32:
        raise ValueError('bounded_instance_count_required')
    tasks = []
    for block_index, (modulus, multiplier, offset) in enumerate(BLOCKS):
        for instance in range(instances_per_block):
            steps = SCREEN_STEPS[instance] if instance < 4 else 7 + instance * 3
            tasks.append(dict(family=FAMILIES['L1mining'], block=block_index,
                task_id=f'PM_POWER_B{block_index}_I{instance:02d}', modulus=modulus,
                multiplier=multiplier, offset=offset, start=(instance * 7 + block_index + 2) % modulus,
                steps=steps))
    return tasks


def advance(task, start, steps):
    value = start
    for unused in range(steps):
        value = (task['multiplier'] * value + task['offset']) % task['modulus']
    return value


def check_record(task, record):
    if type(record) is not dict or set(record) != {'steps', 'multiplier', 'offset'}:
        return dict(valid=False, reason='record_requires_steps_multiplier_offset')
    if any(type(value) is not int for value in record.values()):
        return dict(valid=False, reason='record_fields_must_be_integers_not_booleans')
    if not 1 <= record['steps'] <= 128 or not all(
            0 <= record[key] < task['modulus'] for key in ('multiplier', 'offset')):
        return dict(valid=False, reason='record_range')
    for start in range(task['modulus']):
        expected = advance(task, start, record['steps'])
        actual = (record['multiplier'] * start + record['offset']) % task['modulus']
        if expected != actual:
            return dict(valid=False, reason='finite_domain_counterexample', start=start,
                actual=actual, observed_by_iteration=expected)
    return dict(valid=True, domain_size=task['modulus'], checked_steps=record['steps'])


def project(raw):
    if type(raw) is not str or raw.count('FINAL ') != 1:
        raise ValueError('one_final_json_line_required')
    prose, final = raw.split('FINAL ', 1)
    if prose and not prose.endswith('\n'):
        raise ValueError('final_must_start_on_its_own_line')
    if '\n' in final.strip():
        raise ValueError('final_json_must_be_one_line')

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result

    action = json.loads(final, object_pairs_hook=unique)
    if type(action) is not dict or set(action) != {'answer', 'records'}:
        raise ValueError('final_requires_answer_and_records')
    if type(action['answer']) is not int or type(action['records']) is not list or len(action['records']) > 3:
        raise ValueError('integer_answer_and_at_most_three_records_required')
    return dict(prose=prose.rstrip(), action=action)


def judge(task, raw, terminal=True):
    if not terminal:
        return dict(outcome_success=False, record_success=False, accepted=False,
            feedback=dict(error='unterminated_response'), projection=None)
    try:
        projection = project(raw)
    except (ValueError, TypeError) as error:
        return dict(outcome_success=False, record_success=False, accepted=False,
            feedback=dict(error=str(error)), projection=None)
    action = projection['action']
    checks = [check_record(task, record) for record in action['records']]
    outcome = action['answer'] == advance(task, task['start'], task['steps'])
    records = bool(checks) and all(check['valid'] for check in checks)
    nontrivial = records and any(record['steps'] > 1 for record in action['records'])
    return dict(outcome_success=outcome, record_success=bool(nontrivial),
        accepted=bool(outcome and nontrivial), projection=projection,
        feedback=dict(answer_correct=outcome, records=checks,
            reusable_nontrivial_record=bool(nontrivial)))


def initial_messages(task, records, arm):
    if arm not in ('RICH', 'TERSE'):
        raise ValueError('unknown_arm')
    style = ('Use 150–400 tokens of first-person reasoning before the final action. Connect the '
        'visible mathematical evidence and any checked records to my goal, explain a testable '
        'expectation, and then act. Do not invent observations or claim checks not performed.'
        if arm == 'RICH' else 'Return only the final action, without explanatory prose.')
    system = ('Solve modular recurrence tasks. A record states that after steps iterations, every '
        'residue x becomes (multiplier*x+offset) modulo the current modulus. Propose up to three '
        'such reusable records; at least one must cover more than one step. All records are '
        'checked by direct iteration over every input residue; valid records from successful '
        'tasks persist only within this recurrence block. You may use these records on later '
        'tasks. End with exactly one line: FINAL followed by a JSON object with integer answer '
        'and records (a list of objects with integer steps, multiplier, offset). Use canonical '
        'residues from 0 through modulus-1. No code fences. ' + style)
    user = (f"Task {task['task_id']}: x_(t+1)=({task['multiplier']}*x_t+{task['offset']}) "
        f"mod {task['modulus']}; x_0={task['start']}. Find x_{task['steps']}.\n"
        'Checked child records from earlier tasks in this block: ' + json.dumps(records, separators=(',', ':')))
    return [dict(role='system', content=system), dict(role='user', content=user)]


def screen(generate, arm, emit=None):
    emit = emit or (lambda name, value: None)
    tasks = curriculum(4)
    episodes, stores, calls = [], {}, 0
    for task in tasks:
        store = stores.setdefault(task['block'], {})
        before = deepcopy(list(store.values()))
        messages = initial_messages(task, before, arm)
        episode = dict(task=task, arm=arm, records_before=before, turns=[], semantic_status='UNREVIEWED')
        for turn_index in range(MAX_TURNS):
            if calls >= MAX_CALLS:
                raise ValueError('call_budget_exceeded')
            response = generate(deepcopy(messages), task_id=task['task_id'], turn=turn_index)
            calls += 1
            verdict = judge(task, response['raw'], response.get('terminal') is True)
            episode['turns'].append(dict(messages=deepcopy(messages), response=deepcopy(response), verdict=verdict))
            emit(f"{task['task_id']}_turn{turn_index}.json", episode['turns'][-1])
            if verdict['accepted']:
                for record in verdict['projection']['action']['records']:
                    store[record['steps']] = dict(**record, source_task=task['task_id'], source_turn=turn_index)
                break
            messages += [dict(role='assistant', content=response['raw']), dict(role='user',
                content='Deterministic checker feedback: ' + json.dumps(verdict['feedback']) +
                    '\nCorrect the attempt using this feedback; no reference solution is supplied.')]
        final = episode['turns'][-1]['verdict']
        episode.update(outcome_success=final['outcome_success'], record_success=final['record_success'],
            accepted=final['accepted'], records_after=deepcopy(list(store.values())))
        episodes.append(episode)
        emit(task['task_id'] + '.json', episode)
    return dict(arm=arm, episodes=episodes, model_calls=calls, tasks=len(tasks),
        first_turn_outcomes=sum(episode['turns'][0]['verdict']['outcome_success'] for episode in episodes),
        final_outcomes=sum(episode['outcome_success'] for episode in episodes),
        outcome_and_record=sum(episode['accepted'] for episode in episodes),
        corrected=sum(episode['accepted'] and len(episode['turns']) > 1 for episode in episodes),
        tasks_with_prior_records=sum(bool(episode['records_before']) for episode in episodes),
        admitted_targets=0, fits=0, updates=0, semantic_status='UNREVIEWED',
        claim='L1_PROMPT_SCREEN_NOT_A_LEARNING_SLOPE_OR_MEMORY_CAUSAL_TEST')
