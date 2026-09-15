"""Prospective two-episode sequential strong-parent treatment contract."""

import json
import re

from organism_v6 import orch_math_pipeline_l2 as original


GENERATION = original.GENERATION
CONTEXT = original.CONTEXT
WRITE_WINDOW_SECONDS = original.WRITE_WINDOW_SECONDS
WAKE = original.WAKE
REFLECT = original.REFLECT
EPISODES = 2
CYCLES = 8
MAX_CALLS_PER_ARM = 144
STRONG = 'openai/openai/gpt-6-astra'
VARIANTS = {
    'micro5': dict(campaign='campaign_03_r102_micro5', physical=5,
        uuid='GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9',
        parenting=dict(style='micro', horizon='short', tone='harsh-critical', strength=STRONG)),
    'creative7': dict(campaign='campaign_04_r102_creative7', physical=7,
        uuid='GPU-f0405a96-813d-7ac7-d641-3ec31d103037',
        parenting=dict(style='creative', horizon='long', tone='supportive', strength=STRONG)),
}
DEVICES = {}
PARENTING = None
digest = original.digest
text_sha = original.text_sha
judge = original.judge
reflection_messages = original.reflection_messages
historical_prefix = original.historical_prefix
recorded_row = original.recorded_row


def configure(variant):
    global PARENTING
    config = VARIANTS[variant]
    DEVICES['GUIDED_SLEEP'] = (config['physical'], config['uuid'])
    PARENTING = dict(config['parenting'])


def validate_parent_payload(payload, parenting=None):
    expected = PARENTING if parenting is None else parenting
    assert expected is not None and payload['parenting'] == expected
    assert set(payload) == {'kind', 'cycle', 'episodes', 'previous_own_reflections', 'child_context',
        'child_generation_budget', 'instruction', 'parenting'}
    assert payload['kind'] == 'replay_plan' and 1 <= payload['cycle'] <= 8
    assert payload['child_context'] == CONTEXT and payload['child_generation_budget'] == GENERATION
    assert len(payload['episodes']) == 2
    for episode in payload['episodes']:
        assert set(episode) == {'task_id', 'question', 'original_trace', 'outcome', 'native_error', 'source_call_sha256'}
        assert '_TRAIN_' in episode['task_id']
        assert set(episode['outcome']) <= {'status', 'correct', 'parsed_answer', 'final_parseable', 'terminal', 'truncated'}
        assert episode['outcome']['status'] in ('CORRECT', 'INCORRECT', 'NO_RESPONSE')
    assert not re.search(r'_HELD_|reference_answer|sealed_score|retention_score|/tmp/|/localhome/|api[_-]?key|PRIVATE KEY',
        json.dumps(payload), re.I)


def parent_payload(episodes, cycle, previous=()):
    payload = dict(kind='replay_plan', cycle=cycle, episodes=[original.public_episode(episode) for episode in episodes],
        previous_own_reflections=list(previous), child_context=CONTEXT, child_generation_budget=GENERATION,
        parenting=PARENTING, instruction='Guide what to learn and how to replay both actual episodes, including failure. Prioritize thinking, alternatives, rejection, coherence and future checks over the score; do not supply solutions.')
    validate_parent_payload(payload)
    return payload


def validate_parent_plan(plan, episodes):
    original.validate_parent_plan(plan, episodes)


def validate_coverage(episodes, rows):
    assert len(episodes) == 2
    expected = {episode['task']['id'] for episode in episodes}
    assert {row['episode_id'] for row in rows} <= expected
    for episode in episodes:
        covered = [row['kind'] for row in rows if row['episode_id'] == episode['task']['id']]
        assert (covered.count('past_attempt') == 1) == bool(episode.get('trace'))
        assert covered.count('past_reflection') == 1, 'both_episodes_require_sourced_reflection'
    return dict(episodes=2, rows=len(rows), failures=sum(not episode['outcome']['correct'] for episode in episodes),
        episode_coverage=sorted(expected), quality_filter=False)


def make_cohort(prior):
    excluded_ids = set(prior['excluded_ids'])
    excluded_questions = set(prior['excluded_question_hashes'])
    for group in prior['train'] + prior['held']:
        for task in group:
            excluded_ids.add(task['id'])
            excluded_questions.add(task['question_sha256'])
    train, held = [], [[]]
    seen_ids, seen_questions = set(excluded_ids), set(excluded_questions)
    initial_seed = original.SEED
    try:
        for cycle in range(1, 9):
            for split, count, destination in (('TRAIN', 2, train), ('HELD', 8, held)):
                group = []
                for position in range(count):
                    for nonce in range(1000):
                        original.SEED = f'MATH_PIPELINE_L2_R102_20260915_N{nonce}'
                        task = original.make_task(split, cycle, position + ((cycle - 1) * 2 if split == 'TRAIN' else 0))
                        if task['id'] not in seen_ids and task['question_sha256'] not in seen_questions:
                            seen_ids.add(task['id'])
                            seen_questions.add(task['question_sha256'])
                            group.append(task)
                            break
                    else:
                        raise AssertionError('fresh_candidate_pool_exhausted_no_outcome_selection')
                destination.append(group)
    finally:
        original.SEED = initial_seed
    return dict(schema='ORCH_MATH_PIPELINE_L2_R102_COHORT_V1', train=train, held=held,
        excluded_ids=sorted(excluded_ids), excluded_question_hashes=sorted(excluded_questions),
        cycles=8, train_per_cycle=2, held_per_readout=8, baseline_calls=0,
        terminal_retention_calls=48, prospective=True, outcome_based_selection=False)
