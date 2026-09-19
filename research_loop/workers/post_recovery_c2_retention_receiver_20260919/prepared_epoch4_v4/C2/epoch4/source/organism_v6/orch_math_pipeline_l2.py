"""Source-attributed all-experience math replay, not success-only admission."""

from fractions import Fraction
import hashlib
import json
import random
import re

from organism_v6 import orch_math_rich as original


ARMS = ('GUIDED_SLEEP', 'UNPARENTED_SLEEP', 'FROZEN')
DEVICES = dict(GUIDED_SLEEP=(4, 'GPU-31583768-d90f-520c-51ed-5dac761526d0'),
    UNPARENTED_SLEEP=(5, 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9'),
    FROZEN=(7, 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037'))
HOST_SHA = '6bcd6b8370cc2f2a15e1e488352b4cec96b1e137489d52c3324c199536a09ba8'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
CONTEXT = 16384
GENERATION = 8192
CYCLES = 3
EPISODES = 8
WRITE_WINDOW_SECONDS = 60
MAX_CALLS_PER_ARM = 272
HOURS = 8
SEED = 'MATH_PIPELINE_L2_20260915_ATTEMPT1'
PARENT_SCHEDULE = {
    1: dict(style='micro', horizon='short', tone='harsh-critical', strength='existing_strong_codex'),
    2: dict(style='training-wheels', horizon='long', tone='supportive', strength='existing_strong_codex'),
    3: dict(style='creative', horizon='long', tone='supportive', strength='existing_strong_codex'),
}
WAKE = ('Solve the supplied math problem in your own voice. Develop useful reasoning, test consequential '
    'uncertainties and check the requested quantity. Distinguish calculations, hypotheses and actual '
    'observations. Use the space you need, without padding. Finish with a separate FINAL: numeric answer.')
REFLECT = ('Reflect in your own voice on your recorded attempt and the actual checker feedback. '
    'A failed attempt is a past mistake, not a correct example. Explain what you actually tried, what '
    'the supplied outcome establishes, useful corrections or hypotheses, and a concrete future check. '
    'Do not invent experiences, claim an unperformed test passed, or quote a teacher lesson. '
    'This is your own replay, not a new environment result. Use the available reasoning space.')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def make_task(split, cycle, position):
    master = f'{SEED}_{split}_C{cycle}_E{position}'
    rng = random.Random(int(text_sha(master), 16))
    family = ('affine_balance', 'inventory_balance', 'modular_join', 'rate_balance')[position % 4]
    solution = rng.randrange(12, 240)
    factor = rng.randrange(3, 20)
    offset = rng.randrange(7, 100)
    if family == 'affine_balance':
        question = f'An integer x satisfies {factor} times x plus {offset} equals {factor * solution + offset}. Find x and check the equality.'
    elif family == 'inventory_balance':
        question = (f'A store begins with {solution + offset} sealed boxes. It ships {offset} boxes, then '
            f'opens every remaining box, each containing {factor} parts. How many parts does it unpack?')
        solution *= factor
    elif family == 'rate_balance':
        question = (f'A machine makes {factor} identical parts per minute at a constant rate. It runs '
            f'for {solution} minutes, then discards {offset} defective parts. How many usable parts remain?')
        solution = factor * solution - offset
    else:
        left, right = (23, 29) if position < 4 else (31, 37)
        solution = rng.randrange(left * right)
        question = (f'Find the unique integer x in the range 0 through {left * right - 1} inclusive '
            f'whose remainder on division by {left} is {solution % left} and whose remainder on '
            f'division by {right} is {solution % right}. Verify both remainders.')
    return dict(id=master, split=split, cycle=cycle, family=family, question=question,
        question_sha256=original.digest(' '.join(question.lower().split())), gold=str(solution))


def cohort(excluded_ids=(), excluded_questions=()):
    train = [[make_task('TRAIN', cycle, position) for position in range(EPISODES)] for cycle in range(1, 4)]
    held = [[make_task('HELD', cycle, position) for position in range(EPISODES)] for cycle in range(4)]
    tasks = [task for group in train + held for task in group]
    assert len({task['id'] for task in tasks}) == len({task['question_sha256'] for task in tasks}) == 56
    assert not {task['id'] for task in tasks}.intersection(excluded_ids)
    assert not {task['question_sha256'] for task in tasks}.intersection(excluded_questions)
    return dict(schema='ORCH_MATH_PIPELINE_L2_COHORT_V1', train=train, held=held,
        excluded_ids=sorted(set(excluded_ids)), excluded_question_hashes=sorted(set(excluded_questions)),
        seed=SEED, train_per_cycle=8, held_per_readout=8, cycles=3)


def judge(task, response):
    parsed = original.final_value(response['raw'])
    correct = parsed is not None and parsed == Fraction(task['gold'])
    return dict(status='CORRECT' if correct else 'INCORRECT', correct=correct,
        parsed_answer=str(parsed) if parsed is not None else None,
        final_parseable=parsed is not None, terminal=response['terminal'], truncated=response['truncated'])


def public_episode(episode):
    assert '_TRAIN_' in episode['task']['id']
    return dict(task_id=episode['task']['id'], question=episode['task']['question'],
        original_trace=episode.get('trace', ''), outcome=episode['outcome'],
        native_error=dict(type=episode['error']['type']) if episode.get('error') else None,
        source_call_sha256=episode.get('trace_call_sha256'))


def parent_payload(episodes, cycle, previous=()):
    payload = dict(kind='replay_plan', cycle=cycle, episodes=[public_episode(episode) for episode in episodes],
        previous_own_reflections=list(previous), child_context=CONTEXT, child_generation_budget=GENERATION,
        parenting=PARENT_SCHEDULE[cycle],
        instruction='Guide what to learn and how to replay every episode; do not omit failures or supply solutions.')
    validate_parent_payload(payload)
    return payload


def validate_parent_payload(payload):
    assert set(payload) == {'kind', 'cycle', 'episodes', 'previous_own_reflections', 'child_context',
        'child_generation_budget', 'instruction', 'parenting'}
    assert payload['parenting'] == PARENT_SCHEDULE[payload['cycle']]
    assert payload['kind'] == 'replay_plan' and 1 <= payload['cycle'] <= CYCLES
    assert len(payload['episodes']) == 8
    for episode in payload['episodes']:
        assert set(episode) == {'task_id', 'question', 'original_trace', 'outcome', 'native_error', 'source_call_sha256'}
        assert '_TRAIN_' in episode['task_id']
        assert set(episode['outcome']) <= {'status', 'correct', 'parsed_answer', 'final_parseable', 'terminal', 'truncated'}
        assert episode['outcome']['status'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE')
    assert not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/tmp/|/localhome/|api[_-]?key|PRIVATE KEY',
        json.dumps(payload), re.I)


def validate_parent_plan(plan, episodes):
    assert set(plan) == {'guidance', 'order', 'episode_guidance', 'rationale'}
    ids = [episode['task']['id'] for episode in episodes]
    assert len(plan['order']) == len(ids) and set(plan['order']) == set(ids)
    assert set(plan['episode_guidance']) == set(ids)
    assert all(isinstance(value, str) for value in [plan['guidance'], plan['rationale'], *plan['episode_guidance'].values()])
    return plan


def reflection_messages(episode, teacher=''):
    public = [dict(role='user', content=episode['task']['question'])]
    if episode.get('trace'):
        public.append(dict(role='assistant', content=episode['trace']))
    public.append(dict(role='user', content='ACTUAL VERIFIER OUTCOME: ' + json.dumps(episode['outcome'], sort_keys=True)
        + '\nReflect on this recorded episode. The outcome above is the only supplied environment observation.'))
    actual = [dict(role='system', content=REFLECT + ('\n\nPRIVATE PARENT REPLAY GUIDANCE:\n' + teacher if teacher else ''))] + public
    return actual, public


def historical_prefix(episode, kind):
    assert kind in ('past_attempt', 'past_reflection')
    outcome = episode['outcome']['status']
    context = (f'SOURCED HISTORICAL CHILD UTTERANCE. Task: {episode["task"]["question"]}\n'
        f'Actual recorded attempt outcome: {outcome}. Kind: {kind}.\n'
        'Reproduce the recorded child utterance below as a historical record, NOT as an endorsed solution '
        'or a certified fact. An INCORRECT attempt remains incorrect. Reflection is an unverified child '
        'hypothesis, not a new test result. No teacher lesson is supplied in this context.')
    if kind == 'past_reflection':
        context += '\nRecorded original attempt:\n' + episode.get('trace', '')
        context += '\nActual checker report: ' + json.dumps(episode['outcome'], sort_keys=True)
    return [dict(role='user', content=context)]


def recorded_row(episode, kind, target, source_call, source_call_sha256, teacher=''):
    assert kind in ('past_attempt', 'past_reflection') and target
    assert source_call['response']['raw'] == target
    assert source_call['task_id'] == episode['task']['id']
    assert kind == 'past_attempt' or source_call['purpose'] == 'reflection'
    assert source_call_sha256 and text_sha(target) == source_call['target_sha256']
    assert not teacher or teacher not in target
    for fragment in re.split(r'(?<=[.!?])\s+|\n+', teacher):
        if len(fragment.split()) >= 8:
            assert fragment not in target, 'verbatim_teacher_sentence_not_child_sleep_target'
    prefix = historical_prefix(episode, kind)
    outcome = episode['outcome']['status']
    assert not teacher or all(teacher not in message['content'] for message in prefix)
    return dict(episode_id=episode['task']['id'], kind=kind, outcome=outcome,
        student_prefix=prefix, target=target, target_sha256=text_sha(target),
        source_call_sha256=source_call_sha256, source_call_path=source_call['relative_path'],
        dose_rule='paired_original_reflection_wallclock_window', semantic_admission='NOT_USED',
        teacher_in_prefix=False, observed_fact_endorsement=False)


def validate_coverage(episodes, rows):
    assert len(episodes) == EPISODES
    expected = {episode['task']['id'] for episode in episodes}
    assert {row['episode_id'] for row in rows} <= expected
    for episode in episodes:
        covered = [row['kind'] for row in rows if row['episode_id'] == episode['task']['id']]
        assert (covered.count('past_attempt') == 1) == bool(episode.get('trace'))
        assert covered.count('past_reflection') == 1, 'every_episode_requires_actual_child_reflection'
    return dict(episodes=8, rows=len(rows), failures=sum(not episode['outcome']['correct'] for episode in episodes),
        episode_coverage=sorted(expected), quality_filter=False)
