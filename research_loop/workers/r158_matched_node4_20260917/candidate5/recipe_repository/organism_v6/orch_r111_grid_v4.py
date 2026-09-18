"""Prospective R114 F4 contract; original running lives and v2 remain untouched."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from organism_v6 import orch_r111_grid as previous


game = previous.game
require = previous.require
digest = previous.digest
text_sha = previous.text_sha
SCHEMA = 'R114_F4_V4_ELICITATION_SYSTEMS_V1'
PLAN_PATH = 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md'
PLAN_ORIGIN_SHA = '7b8bb0b233d0b6d68f0e6ca9440e188a8cbdc20434b1ef34e014baf9c2fdc07d'
PLAN_SHA = '6a1b78c54b28493e0932e0c5974eecd3753a712a15c2f787a769fa1ba9706cd6'
OPEN_PARENT_AMENDMENT = ('When a task ends and the child is offered the open turn, do not hand it a\n'
    '> goal; be curious with it about what, if anything, is worth pursuing — stopping is an acceptable answer. ')
PRINCIPLES_SHA = previous.PRINCIPLES_SHA
SEED = 11420260915
EPISODE_PROMPT = previous.EPISODE_PROMPT
PRESLEEP_PROMPT = previous.PRESLEEP_PROMPT
REFLECTION_PROMPT = previous.REFLECTION_PROMPT
HELD_PROMPT = previous.HELD_PROMPT
OPEN_PROMPT = 'The task is over; the environment is still here.'
FOCUSED_PROMPT = 'Focus and give the answer.'
FINAL_UNIX = datetime(2026, 9, 15, 17, 0, tzinfo=timezone.utc).timestamp()
HARD_END_UNIX = datetime(2026, 9, 15, 17, 2, tzinfo=timezone.utc).timestamp()
LANES = deepcopy(previous.LANES)
DECODER = dict(previous.DECODER, open_max_new_tokens=2048)
PARENT_FIELDS = dict(previous.PARENT_FIELDS,
    REFLECTION=dict(mode='short', max_new_tokens=512))
HIDDEN_KEYS = frozenset(('hidden_evaluator_verdict', 'hidden_answer_keys',
    'hidden_readout', 'held_scores', 'answer_keys', 'readouts'))


def snapshots(root):
    root = Path(root)
    plan = (root / PLAN_PATH).read_text()
    principles = (root / 'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md').read_text()
    require(text_sha(plan) == PLAN_SHA, 'exact_v4_ac5872e6')
    require(plan.count(OPEN_PARENT_AMENDMENT) == 1
        and text_sha(plan.replace(OPEN_PARENT_AMENDMENT, '', 1)) == PLAN_ORIGIN_SHA,
        'only_explicit_open_turn_parent_amendment_since_05a0b428')
    require(text_sha(principles) == PRINCIPLES_SHA, 'exact_principles')
    require(hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest() == previous.GAME_SOURCE_SHA,
        'same_grid_environment')
    return plan, principles


def parent_template(plan):
    require(text_sha(plan) == PLAN_SHA, 'bound_v4_parent_template')
    start = plan.index('> You are the parent of a young model.')
    lines = []
    for line in plan[start:].splitlines():
        if not line.startswith('> '):
            break
        lines.append(line[2:])
    return '\n'.join(lines)


def parent_fixed_text(plan, fields=None):
    fields = deepcopy(PARENT_FIELDS if fields is None else fields)
    validate_fields(fields)
    text = parent_template(plan)
    for key in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        require(text.count('[' + key + ']') == 1, 'exact_parent_field:' + key)
        text = text.replace('[' + key + ']', fields[key])
    require(set(re.findall(r'\[[A-Z]+\]', text)) == {'[SILENT]'}, 'unbound_parent_field')
    return text


def validate_fields(fields, prior=None):
    require(set(fields) == set(PARENT_FIELDS), 'exact_parent_fields')
    require(all(isinstance(fields[key], str) for key in ('GAME', 'STYLE', 'NUDGING', 'FOCUS')),
        'text_parent_fields')
    reflection = fields['REFLECTION']
    require(isinstance(reflection, dict) and set(reflection) == {'mode', 'max_new_tokens'}
        and reflection['mode'] in ('short', 'long') and type(reflection['max_new_tokens']) is int
        and 1 <= reflection['max_new_tokens'] <= 8192, 'bounded_reflection_field')
    if prior is not None:
        require(all(fields[key] == prior[key] for key in ('GAME', 'NUDGING')),
            'only_FOCUS_STYLE_REFLECTION_editable')
    return deepcopy(fields)


def geometry(task):
    return digest({key: task[key] for key in ('cells', 'start', 'visibility')})


def cohort():
    seen = {geometry(task) for groups in game.roster().values() for group in groups for task in group}
    seen.update(geometry(task) for group in previous.cohort().values() for task in group)
    result = {'TRAIN': [], 'DEV': [], 'FINAL': []}
    for split_index, (split, count) in enumerate((('TRAIN', 16), ('DEV', 8), ('FINAL', 8))):
        for ordinal in range(count):
            for attempt in range(1000):
                task = game.task('TRAIN' if split == 'TRAIN' else 'HELD', ordinal // 2 + 1,
                    1 if ordinal < count // 2 else 2,
                    SEED + split_index * 100000 + ordinal * 1000 + attempt)
                if geometry(task) in seen:
                    continue
                try:
                    solution = game.shortest_solution(task)
                except ValueError:
                    continue
                require(len(solution) <= game.MAX_STEPS, 'mechanical_solvability_only')
                task.pop('task_sha256')
                task.update(id=f'R114_F4_{split}_{ordinal + 1:02d}', split=split, cohort_seed=SEED,
                    difficulty_rank=ordinal + 1,
                    difficulty_rank_rule='easy/full-map first; hard/fog-key-door second; fixed ordinal')
                task['task_sha256'] = digest(task)
                seen.add(geometry(task))
                result[split].append(task)
                break
            else:
                raise ValueError('fresh_geometry_exhausted')
    return result


def public_observation(task, state):
    return deepcopy(game.observation(task, state))


def strip_hidden(value):
    if isinstance(value, dict):
        return {key: strip_hidden(item) for key, item in value.items() if key not in HIDDEN_KEYS}
    if isinstance(value, list):
        return [strip_hidden(item) for item in value]
    return deepcopy(value)


def feedback_event(sequence, text, source_sha256, *, child_received, hidden=None):
    require(child_received is True, 'verified_child_delivery_required')
    event = previous.public_event(sequence, 'environment', text, source_sha256)
    event.update(event_type='environment_feedback', child_received=True)
    if hidden is not None:
        event['hidden_evaluator_verdict'] = hidden
    return strip_hidden(event)


def queue_request(identifier, life_id, cycle, episode, phase, task, events, corpus_sha256, now):
    require(task['split'] == 'TRAIN' and task['id'].startswith('R114_F4_TRAIN_'), 'TRAIN_parent_only')
    require(phase in ('experience', 'presleep_metacognition', 'reflection', 'open_turn')
        and episode in (0, 1), 'phase_scope')
    require(events and any(event['actor'] == 'child' for event in events), 'actual_child_required')
    cleaned = strip_hidden(events)
    for sequence, event in enumerate(cleaned):
        require(event['sequence'] == sequence and event['visibility'] == 'TRAIN_PUBLIC', 'public_sequence')
        require(event['actor'] in ('child', 'parent', 'environment'), 'public_actor')
        require(isinstance(event['text'], str) and re.fullmatch('[a-f0-9]{64}', event['source_sha256']),
            'source_bound_text')
        if event['actor'] == 'environment':
            require(event.get('child_received') is True, 'feedback_delivery_provenance')
    payload = dict(schema='r111_train_public_v1', life_id=life_id, cycle=cycle, episode=episode,
        phase=phase, game='grid', task_id=task['id'], task_provenance=dict(split='TRAIN',
            task_sha256=task['task_sha256'], cohort_sha256=corpus_sha256), events=cleaned)
    return dict(id=identifier, payload=payload, payload_sha256=digest(payload), lane_deadline_unix=now + 120)


def readout_plan(cycle, now, completed_final=()):
    require(type(cycle) is int and cycle >= 0 and now < HARD_END_UNIX, 'bounded_readout')
    final_window = 'cycle0' if cycle == 0 else 'morning' if now >= FINAL_UNIX else None
    final_due = final_window is not None and final_window not in completed_final
    return dict(cycle=cycle, DEV=8, focused_DEV=2, FINAL=8 if final_due else 0,
        final_window=final_window if final_due else None, parent_free_open=2 if cycle else 0,
        parent_absent=True, fresh_context=True, sleep_count=0, optimizer_steps=0)


def validate_audience(split, audience):
    require(audience in ('parent', 'head', 'exchange'), 'known_audience')
    require(split == 'TRAIN' or split == 'DEV' and audience in ('head', 'exchange'),
        'FINAL_never_visible_DEV_not_child_parent')


def manifest(root):
    plan, unused_principles = snapshots(root)
    tasks = cohort()
    prompts = dict(episode=EPISODE_PROMPT, presleep=PRESLEEP_PROMPT, reflection=REFLECTION_PROMPT,
        held=HELD_PROMPT, open_turn=OPEN_PROMPT, focused=FOCUSED_PROMPT)
    return dict(schema=SCHEMA, origin_commit='05a0b428', parent_open_turn_amendment_commit='ac5872e6',
        origin_battleplan_sha256=PLAN_ORIGIN_SHA, battleplan_sha256=PLAN_SHA,
        principles_sha256=PRINCIPLES_SHA, base_sha256=game.BASE_SHA, mode='FROZEN_BASE_CONTEXT_ONLY',
        comparison='ELICITATION_ONLY_PARENTING_SYSTEMS', lora=None, optimizer=None, optimizer_steps=0,
        sleep_count=0, seed=SEED, lanes=LANES, decoder=DECODER, prompts=prompts,
        prompt_sha256={key: text_sha(text) for key, text in prompts.items()},
        parent_fixed_text=parent_fixed_text(plan), parent_fixed_sha256=text_sha(parent_fixed_text(plan)),
        parent_fields=deepcopy(PARENT_FIELDS), head_editable=['FOCUS', 'STYLE', 'REFLECTION'],
        cohort_sha256=digest(tasks), split_sha256={key: digest(group) for key, group in tasks.items()},
        DEV_inventory=[dict(id=task['id'], sha256=task['task_sha256']) for task in tasks['DEV']],
        FINAL_inventory_visibility='native private only; commitment public; no parent/head/exchange',
        focused_DEV_ids=[tasks['DEV'][0]['id'], tasks['DEV'][4]['id']],
        task_feedback='all actually child-visible environment feedback retained, including failure/terminal/reward',
        withheld='only hidden evaluator verdicts, answer keys, held/readout outputs',
        episodes_per_cycle=2, dependent_episodes_batched=False,
        cadence='episode: after first completed action response; plus presleep and post-task open opportunity',
        open_turn=dict(after_each_TRAIN_task=True, parent_response_allowed=True,
            at_context_readout_boundary='same prompt without parent, on TRAIN completed-state context only',
            descriptive_labels=['INITIATE_QUESTION', 'REVISIT', 'SEEK', 'NEW_GOAL', 'STOP'],
            semantic_labels_not_inferred_from_tokens=True, environment_stays_available=True),
        persistence=dict(labels=['PERSISTED', 'ABANDONED', 'LOOPED'], requires_obstacle=True,
            postanswer_exploration_separate_descriptive=True, judgement_owner='Main shared judge'),
        readout=dict(DEV_per_cycle=8, focused_DEV_per_cycle=2, FINAL_windows=['cycle0', '2026-09-15T17:00:00Z'],
            FINAL_per_window=8, evaluations_never_gate_continuation=True, sleep0_status='NOT_RUN'),
        parent_wait_seconds=120, parent_call_cutoff_seconds=90,
        hard_end_utc='2026-09-15T17:02:00Z', morning_final_utc='2026-09-15T17:00:00Z',
        Fable_gate='EXPLICIT_WATCHER_RELAYED_ROHIN_GO_REQUIRED; silence never authorizes',
        old_life_transition='receiver ready AND complete cycle; no live source mutation',
        native_calls=0, parent_calls=0, gpu_launch_ready=False,
        pending=['paired resident native driver binding/open-environment continuation',
            'exact old-fact16/audit inventory and total per-life call ceilings',
            'morning FINAL reserve/settling within 17:02 hard end',
            'watcher GO for Fable; receiver-ready completed-cycle transition for Astra7'])
