"""R114/V4 prospective F3 policy, no inference or provider dispatch."""

from copy import deepcopy
from datetime import datetime, timezone
import re

from organism_v6 import orch_r108_code_parent_r113_f3 as previous


PROTOCOL_COMMIT = '05a0b428'
PROTOCOL_SHA256 = '7b8bb0b233d0b6d68f0e6ca9440e188a8cbdc20434b1ef34e014baf9c2fdc07d'
FINAL_CUT = datetime(2026, 9, 15, 17, tzinfo=timezone.utc)
OPEN_TURN_PROMPT = 'The task is over; the environment is still here.'
FOCUS_PROMPT = 'focus and give the answer'
HEAD_MUTABLE_FIELDS = ('FOCUS', 'STYLE', 'REFLECTION')
PERSISTENCE_LABELS = ('PERSISTED', 'ABANDONED', 'LOOPED')
INITIATIVE_LABELS = ('INITIATE_QUESTION', 'REVISIT', 'SEEK', 'NEW_GOAL', 'STOP')
DEFAULT_FIELDS = dict(previous.previous.PARENT_FIELDS,
    REFLECTION=dict(mode='long', max_new_tokens=previous.DECODER['reflection_max_new_tokens']))
require, digest, text_sha, tasks = previous.require, previous.digest, previous.text_sha, previous.tasks


def parent_template(protocol):
    require(text_sha(protocol) == PROTOCOL_SHA256, 'exact_v4_protocol')
    start = protocol.index('> You are the parent of a young model.')
    block = protocol[start:].split('\n\n', 1)[0]
    require(all(line.startswith('> ') for line in block.splitlines()), 'fixed_quoted_parent')
    return '\n'.join(line[2:] for line in block.splitlines())


def validate_fields(fields):
    require(isinstance(fields, dict) and set(fields) == set(DEFAULT_FIELDS), 'fixed_field_names')
    require(fields['GAME'] == DEFAULT_FIELDS['GAME'] and fields['NUDGING'] == DEFAULT_FIELDS['NUDGING'], 'fixed_game_no_nudging')
    for key in ('FOCUS', 'STYLE'):
        require(isinstance(fields[key], str) and fields[key].strip() and len(fields[key]) <= 4000, 'bounded_head_text')
    reflection = fields['REFLECTION']
    require(isinstance(reflection, dict) and set(reflection) == {'mode', 'max_new_tokens'}
        and reflection['mode'] in ('short', 'long') and type(reflection['max_new_tokens']) is int
        and 1 <= reflection['max_new_tokens'] <= previous.DECODER['reflection_max_new_tokens'], 'reflection_within_existing_call_cap')
    return deepcopy(fields)


def parent_prompt(protocol, principles, fields=None):
    require(text_sha(principles) == previous.PRINCIPLES_SHA256, 'exact_principles')
    fields = validate_fields(DEFAULT_FIELDS if fields is None else fields)
    prompt = parent_template(protocol)
    for field in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        require(prompt.count('[' + field + ']') == 1, 'exact_parent_field_occurrence')
        prompt = prompt.replace('[' + field + ']', fields[field])
    require('[REFLECTION]' not in prompt, 'v4_quote_has_no_reflection_placeholder')
    return prompt + '\n\n' + principles


def head_update(current, changes, *, source_sha256, next_cycle):
    current = validate_fields(current)
    require(isinstance(source_sha256, str) and re.fullmatch('[a-f0-9]{64}', source_sha256), 'head_update_provenance')
    require(type(next_cycle) is int and next_cycle >= 1, 'next_cycle_boundary')
    require(isinstance(changes, dict), 'head_changes_object')
    candidate = deepcopy(current)
    try:
        require(set(changes) <= set(HEAD_MUTABLE_FIELDS), 'only_head_mutable_fields')
        candidate.update(deepcopy(changes))
        candidate = validate_fields(candidate)
    except ValueError:
        return dict(status='UNUSABLE_KEEP_PREVIOUS', fields=current, source_sha256=source_sha256,
            next_cycle=next_cycle, stop_life=False, retry=False)
    return dict(status='BOUND_FOR_NEXT_CYCLE', fields=candidate, source_sha256=source_sha256,
        previous_fields_sha256=digest(current), fields_sha256=digest(candidate), next_cycle=next_cycle,
        stop_life=False, retry=False, changes_lifetime_caps=False, live_source_mutation=False)


def focused_tasks():
    return tasks('DEV')[:2]


def focused_messages(task):
    require(task in focused_tasks(), 'fixed_two_dev_only')
    messages = previous.messages(task, 'readout')
    messages[0]['content'] += '\n' + FOCUS_PROMPT
    return messages


def open_turn_messages(context, *, parent_present, task_finished):
    require(type(parent_present) is bool and task_finished is True and context, 'actual_finished_task_context_required')
    split = 'TRAIN' if parent_present else 'DEV'
    registered = {row['task_id']: row for row in tasks(split)}
    messages = []
    for event in context:
        require(event.get('split') == split and event.get('task_id') in registered, 'open_context_split_no_final')
        require(event.get('task_sha256') == registered[event['task_id']]['content_sha256'], 'open_context_task_binding')
        require(event.get('visibility') == 'CHILD_VISIBLE', 'open_context_child_visible_only')
        actor = event.get('actor')
        require(actor in ('child', 'parent', 'environment', 'checker', 'oracle'), 'actual_open_context_actor')
        require(parent_present or actor != 'parent', 'unparented_context_has_no_parent')
        require(isinstance(event.get('text'), str) and event.get('source_sha256') == text_sha(event['text']), 'open_capture_hash')
        require(event.get('event_type') in ('text', 'environment_feedback', 'checker_feedback', 'checker_output'), 'no_hidden_open_events')
        if actor in ('environment', 'checker', 'oracle'):
            require(event.get('child_received') is True, 'open_environment_actually_received')
        if actor == 'child':
            require(event.get('completed_response') is True, 'open_after_completed_response')
        messages.append(dict(role='assistant' if actor == 'child' else 'user', content=event['text']))
    require(any(event['actor'] == 'child' for event in context), 'actual_child_before_open_turn')
    messages.append(dict(role='user', content=OPEN_TURN_PROMPT))
    return messages


def readout_plan(cycle, now, *, stage='cycle', completed=()):
    require(type(cycle) is int and cycle >= 0 and isinstance(now, datetime) and now.tzinfo is not None, 'readout_position_time')
    require(stage in ('cycle', 'final_cut'), 'v4_readout_stage')
    require(stage != 'final_cut' or now >= FINAL_CUT, 'no_final_before_corrected_cut')
    if stage == 'final_cut':
        candidates = [('FINAL', 'FINAL_CUT_20260915T170000Z', 8)]
    else:
        candidates = [('DEV', f'DEV_CYCLE_{cycle:04d}', 8)]
        if cycle == 0:
            candidates.append(('FINAL', 'FINAL_CYCLE_0000', 8))
        candidates.extend([('DEV_FOCUSED', f'DEV_FOCUSED_CYCLE_{cycle:04d}', 2),
            ('DEV_OPEN', f'DEV_OPEN_CYCLE_{cycle:04d}', 1)])
    rows = []
    for split, key, count in candidates:
        if key in completed:
            continue
        row = dict(split=split, key=key, count=count, parent_free=True, context_free_at_readout_start=True,
            max_new_tokens=previous.DECODER['readout_max_new_tokens'], greedy=True,
            head_visible=split != 'FINAL', exchange_visible=False, outcome_may_gate=False)
        if split in ('DEV', 'FINAL'):
            row.update(cohort_sha256=digest(tasks(split)), one_batch=True)
        elif split == 'DEV_FOCUSED':
            row.update(task_ids=[task['task_id'] for task in focused_tasks()],
                message_hashes=[digest(focused_messages(task)) for task in focused_tasks()], prompt=FOCUS_PROMPT)
        else:
            row.update(prompt=OPEN_TURN_PROMPT, task_id=tasks('DEV')[0]['task_id'],
                context='FIRST_DEV_TASK_OWN_COMPLETED_RESPONSE_AND_ENVIRONMENT_ONLY_NO_PARENT',
                new_control_arm=False, description='One unparented open opportunity at each context/readout boundary')
        rows.append(row)
    return rows


def artifact(protocol, principles):
    value = previous.artifact(principles)
    value.update(schema='R114_V4_F3_CPU_BINDING_V1', protocol_commit=PROTOCOL_COMMIT,
        protocol_sha256=PROTOCOL_SHA256, label='R114_F3_CONTEXTUAL_ELICITATION',
        parent_prompt=parent_prompt(protocol, principles), parent_fixed_template_sha256=text_sha(parent_template(protocol)),
        parent_fields=deepcopy(DEFAULT_FIELDS), head_mutable_fields=list(HEAD_MUTABLE_FIELDS),
        reflection_binding='V4 quoted parent has no REFLECTION placeholder; head field binds per-call reflection budget and metadata without altering fixed text',
        open_turn=dict(prompt=OPEN_TURN_PROMPT, prompt_sha256=text_sha(OPEN_TURN_PROMPT),
            parented='ONE_AFTER_EACH_TRAIN_TASK_END', unparented='ONE_AT_EACH_CONTEXT_READOUT_BOUNDARY_ON_FIRST_DEV',
            goal_prescribed=False, parent_response_after='COMPLETED_OPEN_CHILD_RESPONSE_ONLY',
            no_forced_answer_json_on_open=True, observed_labels='MAIN_JUDGE_NOT_RUN'),
        focused_probe=dict(task_ids=[task['task_id'] for task in focused_tasks()], prompt=FOCUS_PROMPT,
            messages_sha256=[digest(focused_messages(task)) for task in focused_tasks()],
            status='NOT_RUN', max_new_tokens=previous.DECODER['readout_max_new_tokens']),
        metrics=dict(owner='MAIN_SHARED_JUDGE', persistence_labels=list(PERSISTENCE_LABELS),
            persistence='CONTINUED_ENGAGEMENT_AFTER_OBSTACLE_NOT_POSTANSWER_LENGTH',
            post_answer_exploration='DESCRIPTIVE_NOT_PERSISTENCE_PROOF', initiative_labels=list(INITIATIVE_LABELS),
            semantic_labels='UNASSESSED', causal_realisation_claim=False),
        final=dict(schedule=['CYCLE_ZERO', 'FINAL_CUT'], final_cut_utc=FINAL_CUT.isoformat(),
            parent_visible=False, head_visible=False, exchange_visible=False, status='NOT_RUN'),
        corrected_cut_replaces='2026-09-16T06:00:00+00:00', fable_launch='R112_WATCHER_RELAYED_ROHIN_DONE_RECEIPT_REQUIRED')
    value['parent_prompt_sha256'] = text_sha(value['parent_prompt'])
    value['cycle_zero'].update(focused_dev_calls=2, unparented_open_calls=1, total_planned_native_calls=37)
    value['native_call_accounting'] = dict(cycle_zero_readout=37, later_cycle_readout=29,
        final_cut_readout=8, includes_legacy_fact16_audit2=True, parented_open_extra_native_per_cycle=2,
        existing_caps_not_increased=True, reservation='ALL_NEW_OPEN_FOCUSED_CALLS_MUST_BE_INCLUDED_BEFORE_DISPATCH')
    value['remaining'] = ['Immutable native backend with new open/focused calls included in finite total caps',
        'Actual parent reply/archive and Astra dispatch wiring', 'Legacy readout source binding',
        'Native historical exclusions', 'Receiver-ready completed-cycle release and fresh admission',
        'R112 explicit done receipt for Fable2; no grace', 'Actual cycle-zero readouts']
    return value
