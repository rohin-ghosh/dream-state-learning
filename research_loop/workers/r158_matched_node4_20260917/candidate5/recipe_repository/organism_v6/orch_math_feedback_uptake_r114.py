"""Prospective F2 v4 contract; no provider, GPU, or weight-update dispatch."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r113 as previous


original = previous.previous
require, digest, sha = previous.require, previous.digest, previous.sha
AREA = Path('research_notes/analysis/orch_math_feedback_uptake_r114_f2_20260915_attempt1')
COMMIT = '05a0b4287d037ce6b9c7c8545bbbfc32230d08e9'
MORNING = datetime(2026, 9, 15, 17, 0, tzinfo=timezone.utc).timestamp()
OPEN_TURN = 'The task is over; the environment is still here.'
FOCUSED = '{question}\n\nfocus and give the answer'
FIELDS = dict(GAME='math word problems', STYLE='creative, supportive',
    NUDGING='You may nudge the child to try a different route, think through several different solutions, or run a different chain of thought, never supply the answer.',
    FOCUS="Attend to your own parenting of the child's thinking rather than its game performance",
    REFLECTION='long')
CORE_CAP = 1168
PARENT_CAP = 384
SLEEP0_CALLS = 18
CYCLE_CALLS = 18
FINAL_CALLS = 8
CYCLES = min((CORE_CAP - SLEEP0_CALLS - FINAL_CALLS) // CYCLE_CALLS, PARENT_CAP // 6)
PERSISTENCE_LABELS = ('PERSISTED', 'ABANDONED', 'LOOPED')
INITIATIVE_LABELS = ('INITIATE_QUESTION', 'REVISIT', 'SEEK', 'NEW_GOAL', 'STOP')


def parent_template(repository, fields=None):
    fields = dict(FIELDS if fields is None else fields)
    require(set(fields) == set(FIELDS), 'exact_section6_fields')
    require(fields['REFLECTION'] in ('short', 'long'), 'reflection_length_field')
    require(all(isinstance(value, str) and value.strip() for value in fields.values()), 'nonempty_fields')
    text = (Path(repository) / AREA / 'PARENT_TEMPLATE_V4.txt').read_text()
    for name in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        require(text.count('[' + name + ']') == 1, 'exact_fixed_template')
        text = text.replace('[' + name + ']', fields[name])
    return text


def parent_prompt(repository):
    principles = Path(repository) / original.AREA / 'PRINCIPLES_V2.md'
    require(sha(principles) == original.PRINCIPLES_SHA, 'exact_principles_v2')
    return parent_template(repository) + '\n\n' + principles.read_text()


def messages(purpose, question=None):
    if purpose not in ('open_turn', 'focused'):
        return original.messages(purpose, question)
    require((question is not None) == (purpose == 'focused'), 'question_scope')
    return [dict(role='system', content=original.SYSTEM),
        dict(role='user', content=FOCUSED.format(question=question) if purpose == 'focused' else OPEN_TURN)]


def decoder(purpose):
    return original.decoder('held' if purpose == 'focused' else 'episode' if purpose == 'open_turn' else purpose)


def cycle_plan(cycle):
    require(type(cycle) is int and 1 <= cycle <= CYCLES, 'prospective_cycle_cap')
    result = []
    for episode in (1, 2):
        result.extend([dict(phase='episode', episode=episode, parent_slot=True, split='TRAIN'),
            dict(phase='open_turn', episode=episode, parent_slot=True, split='TRAIN')])
    result.extend(dict(phase=phase, episode=None, parent_slot=True, split='TRAIN')
        for phase in ('presleep', 'reflection'))
    result.extend(dict(phase='boundary_open_turn', episode=episode, parent_slot=False,
        split='PROBE', after_context_boundary=True, parent_context_visible=False)
        for episode in (1, 2))
    result.extend(dict(phase='dev', index=index, parent_slot=False, split='DEV') for index in range(8))
    result.extend(dict(phase='focused', index=index, parent_slot=False, split='DEV') for index in range(2))
    return result


def focused_tasks(dev):
    require(len(dev) == 8 and all(task['split'] == 'DEV' for task in dev), 'dev_only_focused_probe')
    return [dict(id=task['id'], question_sha256=task['question_sha256'],
        messages=messages('focused', task['question']), decoder=decoder('focused')) for task in dev[:2]]


def contract(repository):
    result = previous.contract(repository)
    result.update(schema='R114_F2_SYSTEMS_COMPARISON_V1', commit=COMMIT,
        battleplan_sha256=sha(Path(repository) / AREA / 'BATTLE_PLAN_V4.md'),
        parent_template_sha256=sha(Path(repository) / AREA / 'PARENT_TEMPLATE_V4.txt'),
        parent_prompt_sha256=hashlib.sha256(parent_prompt(repository).encode()).hexdigest(),
        parent_fields=dict(FIELDS), head_editable_fields=['FOCUS', 'STYLE', 'REFLECTION'],
        reflection_field_transport='BRANCH_CONFIG_NOT_INSERTED_IN_FIXED_TEXT_WHICH_HAS_NO_REFLECTION_PLACEHOLDER',
        open_turn_prompt=OPEN_TURN, focused_prompt=FOCUSED, focused_dev_indices=[0, 1],
        focused_schedule='SLEEP0_AND_EVERY_CYCLE', focused_count=2,
        open_turn_after_each_episode=True, boundary_open_turns=2,
        boundary_open_parent_free=True, boundary_open_parent_context_visible=False,
        boundary_label='CONTEXT_BOUNDARY_NOT_WEIGHT_SLEEP',
        cycle_plan=cycle_plan(1), segment_order=[item['phase'] for item in cycle_plan(1)],
        cycles=CYCLES, core_native_cap=CORE_CAP, parent_slot_cap=PARENT_CAP,
        sleep0_native_calls=SLEEP0_CALLS, native_calls_per_cycle=CYCLE_CALLS,
        planned_native_calls=SLEEP0_CALLS + CYCLES * CYCLE_CALLS + FINAL_CALLS,
        planned_parent_slots=CYCLES * 6, morning_final_reserved_calls=FINAL_CALLS,
        separate_morning_final_cap=0, morning_included_in_core_cap=True,
        final_morning_unix=MORNING, morning_exceeds_existing_native_wall=True,
        morning_final_window_end_unix=original.HARD_END,
        morning_dispatch_authorized=False,
        morning_window_policy='V4_FINAL_ONLY_AT_1700_UNDER_UNCHANGED_1702_HARD_WALL_NO_EXTENSION',
        persistence_labels=list(PERSISTENCE_LABELS), initiative_labels=list(INITIATIVE_LABELS),
        persistence='OBSTACLE_ENGAGEMENT_CHANGED_APPROACH_EVENTUAL_DECISION_SOURCE_REVIEW_REQUIRED',
        semantic_labels_default='UNKNOWN_UNTIL_SHARED_JUDGE_OR_AUTHOR_REVIEW',
        post_answer_exploration='DESCRIPTIVE_NOT_PERSISTENCE_OR_CAUSAL_METACOGNITION',
        no_outcome_quality_gate=True, no_new_baselines=True)
    result['decoders'].update(open_turn=decoder('open_turn'), focused=decoder('focused'))
    return result


def reserve_final(root, phase, now, checkpoint_sha256, calls_used, episodes_started=0):
    require(phase in ('sleep0', 'morning'), 'two_final_phases_only')
    require(type(calls_used) is int and 0 <= calls_used <= CORE_CAP - FINAL_CALLS, 'reserved_final_call_budget')
    require(isinstance(checkpoint_sha256, str) and len(checkpoint_sha256) == 64, 'checkpoint_binding')
    require((phase == 'sleep0' and episodes_started == 0 and now < original.NATIVE_END)
        or (phase == 'morning' and MORNING <= now < original.HARD_END), 'v4_exact_final_window')
    path = Path(root) / ('FINAL_' + phase + '.reservation')
    with path.open('x') as stream:
        stream.write(checkpoint_sha256 + '\n')
    return path


visible_events = previous.visible_events
request = previous.request
readout_access = previous.readout_access
export_dev = previous.export_dev
require_done = previous.require_done
