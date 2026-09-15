"""Prospective R113 F3 contextual elicitation policy; no native dispatch."""

from copy import deepcopy
from datetime import datetime, timezone
import math
import re

from organism_v6 import orch_r108_code_parent as gym_policy
from organism_v6 import orch_r108_code_parent_r111_f3 as previous


PROTOCOL_COMMIT = 'e3a13940'
PROTOCOL_SHA256 = 'a8e4d8d0d2aa5df171da94debf7e539e610ad940b63824684c0923f2072d1692'
PRINCIPLES_SHA256 = previous.PRINCIPLES_SHA256
MORNING_CUT = datetime(2026, 9, 16, 6, tzinfo=timezone.utc)
PROMPTS = dict(
    episode='Work through this code task in your own way. When ready, put your answer on the final nonempty line as a JSON object containing only "expression".',
    presleep='What from this experience would you like to keep with you?',
    reflection='Reflect on this experience freely, in your own words.')
READOUT_PROMPT = previous.READOUT_PROMPT
DECODER = deepcopy(previous.DECODER)
SPLITS = {'TRAIN': (800000, 0), 'DEV': (900000, 3), 'FINAL': (1000000, 7)}
FEEDBACK_KEYS = {'feedback', 'outcome', 'score', 'correct', 'passed', 'failure_class'}
HIDDEN_KEYS = {'hidden_oracle', 'hidden_outcome', 'hidden_evaluator_verdict', 'oracle_verdict',
    'answer_key', 'answer_keys', 'gold', 'expected', 'reference_expression', 'tests',
    'held_scores', 'readout', 'readouts', 'final_readout'}
digest = previous.digest
text_sha = previous.text_sha
require = gym_policy.require


def tasks(split, count=None):
    require(split in SPLITS, 'r113_split')
    count = (200 if split == 'TRAIN' else 8) if count is None else count
    require(type(count) is int and (1 <= count <= 200 if split == 'TRAIN' else count == 8), 'bounded_registry')
    marker_base, rotation = SPLITS[split]
    rows = []
    for offset in range(count):
        parameter = 7 + offset % 13
        kind = (offset + rotation) % 10
        question, reference = gym_policy.specification(kind, parameter)
        marker = marker_base + offset
        scalar = kind in (0, 2, 5, 7)
        question += f' Finally, add {marker} to the numeric result.' if scalar else f' Finally, append the marker {marker} to the resulting list.'
        reference = '(' + reference + ') + ' + (str(marker) if scalar else '[' + str(marker) + ']')
        prompt = 'The only named argument is values, a list of integers with length at most 12. ' + question
        arguments = [[], [0], [-parameter, parameter + 1], [parameter, 1, -1, parameter, 0], [2, -3, 2, 8, -3, 0]]
        row = dict(task_id=f'R113_F3_{split}_{offset + 1:04d}', split=split, family='code',
            prompt=prompt, prompt_sha256=text_sha(prompt), question=question,
            question_sha256=gym_policy.question_hash(question), reference_expression=reference,
            tests=[dict(arguments=dict(values=values), expected=gym_policy.gym.evaluate(reference, dict(values=values))) for values in arguments])
        row['content_sha256'] = digest(row)
        rows.append(row)
    return rows


def registry_exclusions(historical_rows):
    rows = [row for split in SPLITS for row in tasks(split)]
    identifiers = [row['task_id'] for row in rows]
    hashes = [row['prompt_sha256'] for row in rows]
    require(len(set(identifiers)) == len(rows) and len(set(hashes)) == len(rows), 'disjoint_v3_cohorts')
    old_ids = {row.get('task_id', row.get('id')) for row in historical_rows}
    old_hashes = {row.get('prompt_sha256') for row in historical_rows}
    old_hashes.update(text_sha(row['prompt']) for row in historical_rows if isinstance(row.get('prompt'), str))
    old_questions = {row.get('question_sha256') for row in historical_rows}
    old_questions.update(gym_policy.question_hash(row['question']) for row in historical_rows if isinstance(row.get('question'), str))
    require(not set(identifiers).intersection(old_ids), 'historical_id_collision')
    require(not set(hashes).intersection(old_hashes), 'historical_prompt_collision')
    require(not {row['question_sha256'] for row in rows}.intersection(old_questions), 'historical_question_collision')
    return dict(status='PASS', new_count=len(rows), historical_count=len(historical_rows),
        historical_registry_sha256=digest(historical_rows), scope='SUPPLIED_REGISTRIES_ONLY')


def messages(task, phase='episode'):
    require(phase in ('episode', 'readout'), 'message_phase')
    require(task['split'] == 'TRAIN' if phase == 'episode' else task['split'] in ('DEV', 'FINAL'), 'phase_split')
    return [dict(role='system', content=PROMPTS['episode'] if phase == 'episode' else READOUT_PROMPT),
        dict(role='user', content=task['prompt'])]


def public_events(events):
    result = []
    train_tasks = {row['task_id']: row for row in tasks('TRAIN')}
    for event in events:
        require(isinstance(event, dict), 'event_object')
        if event.get('split') != 'TRAIN' or event.get('visibility') != 'CHILD_VISIBLE':
            continue
        if event.get('actor') not in ('child', 'parent', 'environment', 'checker', 'oracle'):
            continue
        if event.get('event_type') not in ('text', 'environment_feedback', 'checker_feedback', 'checker_output'):
            continue
        require(event.get('task_id') in train_tasks, 'registered_train_event')
        require(event.get('task_sha256') == train_tasks[event['task_id']]['content_sha256'], 'train_event_binding')
        text = event.get('text')
        require(isinstance(text, str) and event.get('source_sha256') == text_sha(text), 'exact_child_visible_capture')
        feedback = {key: strip_hidden_fields(event[key]) for key in FEEDBACK_KEYS if key in event}
        environmental = event['actor'] in ('environment', 'checker', 'oracle')
        if feedback or environmental and event['event_type'] != 'text' or event['actor'] in ('checker', 'oracle'):
            require(environmental and event.get('child_received') is True, 'feedback_delivery_required')
        projected = dict(sequence=len(result), actor=event['actor'], event_type=event['event_type'],
            task_id=event['task_id'], task_sha256=event['task_sha256'],
            visibility='CHILD_VISIBLE', split='TRAIN', text=text, source_sha256=event['source_sha256'])
        if environmental:
            projected['child_received'] = event.get('child_received') is True
        result.append(dict(projected, **feedback))
    return result


def strip_hidden_fields(value):
    if isinstance(value, dict):
        return {key: strip_hidden_fields(item) for key, item in value.items() if key not in HIDDEN_KEYS}
    if isinstance(value, list):
        return [strip_hidden_fields(item) for item in value]
    return value


def context_for(audience, events, readouts=()):
    require(audience in ('parent', 'head', 'exchange'), 'context_audience')
    summaries = []
    dev_tasks = {row['task_id']: row for row in tasks('DEV')}
    if audience == 'head':
        for row in readouts:
            require(isinstance(row, dict), 'readout_object')
            if row.get('split') != 'DEV':
                continue
            require(row.get('task_id') in dev_tasks, 'registered_dev_only')
            task = dev_tasks[row['task_id']]
            require(row.get('content_sha256') == task['content_sha256'], 'dev_task_binding')
            require(type(row.get('cycle')) is int and row['cycle'] >= 0, 'dev_cycle')
            require(row.get('status') in ('COMPLETE', 'FAILED', 'MISSING'), 'dev_status')
            require(row.get('correct') is None or type(row['correct']) is bool, 'dev_machine_outcome')
            require(row['status'] == 'COMPLETE' or row.get('correct') is None, 'no_uncompleted_dev_outcome')
            summaries.append({key: row.get(key) for key in ('task_id', 'split', 'content_sha256', 'cycle', 'status', 'correct')})
    return dict(audience=audience, train_events=public_events(events), dev_readouts=summaries)


def readout_plan(cycle, now, *, stage='cycle', completed=()):
    require(type(cycle) is int and cycle >= 0, 'readout_cycle')
    require(isinstance(now, datetime) and now.tzinfo is not None, 'aware_readout_time')
    require(stage in ('cycle', 'morning'), 'scheduled_readout_stage')
    require(stage != 'morning' or now >= MORNING_CUT, 'no_early_morning_final')
    candidates = [('DEV', f'DEV_CYCLE_{cycle:04d}')] if stage == 'cycle' else []
    if stage == 'cycle' and cycle == 0:
        candidates.append(('FINAL', 'FINAL_CYCLE_0000'))
    if stage == 'morning':
        candidates.append(('FINAL', 'FINAL_MORNING_20260916T060000Z'))
    return [dict(split=split, key=key, count=8, cohort_sha256=digest(tasks(split)),
        fresh_process=True, parent_free=True, context_free=True, one_batch=True,
        max_new_tokens=DECODER['readout_max_new_tokens'], greedy=True,
        head_visible=split == 'DEV', exchange_visible=False)
        for split, key in candidates if key not in completed]


def hourly_exposure(records, *, life_id, start_unix, end_unix):
    require(type(start_unix) in (int, float) and type(end_unix) in (int, float)
        and math.isfinite(start_unix) and math.isfinite(end_unix) and start_unix < end_unix, 'hourly_window')
    seen = set()
    result = dict(life_id=life_id, start_unix=start_unix, end_unix=end_unix,
        parent_provider_completed=0, parent_delivered=0, parent_silent=0,
        parent_missing=0, parent_missing_late=0, parent_pending=0,
        child_completed=0, child_failed=0, child_pending=0,
        child_tokens=0, child_token_counts_missing=0, optimizer_steps=0,
        trained_child_token_exposures=0, sleep_count=0,
        measurement='RECEIPT_COUNTS_NOT_RESERVATION_CAPACITY', semantic_effect='UNASSESSED')
    for row in records:
        require(row.get('life_id') == life_id, 'single_life_exposure')
        require(isinstance(row.get('call_id'), str) and row['call_id'], 'native_call_id')
        require(row['call_id'] not in seen, 'duplicate_receipt_no_double_count')
        seen.add(row['call_id'])
        require(isinstance(row.get('receipt_sha256'), str)
            and re.fullmatch('[a-f0-9]{64}', row['receipt_sha256']), 'native_receipt_provenance')
        require(type(row.get('observed_unix')) in (int, float) and math.isfinite(row['observed_unix']), 'receipt_time')
        require(row.get('optimizer_steps', 0) == 0, 'f3_has_no_optimizer')
        if not start_unix <= row['observed_unix'] < end_unix:
            continue
        status = row.get('status')
        if row.get('kind') == 'parent':
            require(status in ('COMPLETE', 'SILENT', 'MISSING', 'PENDING'), 'settled_parent_status')
            require(type(row.get('provider_completed')) is bool and type(row.get('late')) is bool, 'parent_delivery_evidence')
            require(not row['late'] or status == 'MISSING', 'late_is_missing_not_delivered')
            require(status not in ('COMPLETE', 'SILENT') or row['provider_completed'], 'delivery_requires_completion')
            require(status != 'PENDING' or not row['provider_completed'], 'completed_provider_not_pending')
            result['parent_provider_completed'] += row['provider_completed']
            result['parent_delivered'] += status == 'COMPLETE'
            result['parent_silent'] += status == 'SILENT'
            result['parent_missing'] += status == 'MISSING'
            result['parent_missing_late'] += status == 'MISSING' and row['late']
            result['parent_pending'] += status == 'PENDING'
        else:
            require(row.get('kind') == 'child' and status in ('COMPLETE', 'FAILED', 'PENDING'), 'child_receipt_status')
            result['child_' + {'COMPLETE': 'completed', 'FAILED': 'failed', 'PENDING': 'pending'}[status]] += 1
            if status != 'PENDING':
                tokens = row.get('output_tokens')
                require(tokens is None or type(tokens) is int and tokens >= 0, 'actual_child_tokens')
                if tokens is None:
                    result['child_token_counts_missing'] += 1
                else:
                    result['child_tokens'] += tokens
    return result


def artifact(principles):
    parent = previous.parent_prompt(principles)
    cohorts = {split: tasks(split) for split in SPLITS}
    return dict(schema='R113_V3_F3_CPU_BINDING_V1', protocol_commit=PROTOCOL_COMMIT,
        protocol_sha256=PROTOCOL_SHA256, principles_sha256=PRINCIPLES_SHA256,
        label='R113_F3_FRESH_CONTEXTUAL_ELICITATION', comparison='PARENTING_SYSTEMS_NOT_PARENT_MODEL_ONLY',
        systems=dict(fable='Fable parent plus head parent plus exchange', astra='Astra parenting system'),
        claims='Elicitation and within-context behavior only; no retained-weight learning',
        base_sha256=previous.BASE_SHA256, adapter=None, optimizer=None, sleep_enabled=False,
        child_facing_prompts=deepcopy(PROMPTS), child_prompt_sha256={key: text_sha(text) for key, text in PROMPTS.items()},
        parent_fixed_template_sha256=text_sha(previous.PARENT_TEMPLATE), parent_prompt=parent,
        parent_prompt_sha256=text_sha(parent), parent_models=deepcopy(previous.PAIR), decoder=deepcopy(DECODER),
        readout_prompt=READOUT_PROMPT, readout_prompt_sha256=text_sha(READOUT_PROMPT),
        cohorts={split: dict(count=len(rows), cohort_sha256=digest(rows),
            tasks=[{key: row[key] for key in ('task_id', 'content_sha256', 'prompt_sha256')} for row in rows])
            for split, rows in cohorts.items()},
        dev=dict(schedule='EVERY_CYCLE_INCLUDING_ZERO', head_visible=True, parent_visible=False, exchange_visible=False),
        final=dict(schedule=['CYCLE_ZERO', 'MORNING_CUT'], morning_cut_utc=MORNING_CUT.isoformat(),
            parent_visible=False, head_visible=False, exchange_visible=False, status='NOT_RUN'),
        cycle_zero=dict(status='NOT_RUN', dev=8, final=8, legacy_facts=16, audit_cases=2,
            legacy_bindings='PENDING_NATIVE_SOURCE_BINDING'),
        cadence='COMPLETED_EPISODE_RESPONSE_PLUS_PRESLEEP', finest_unit='COMPLETED_RESPONSE_NOT_MID_GENERATION',
        environment_feedback='EXACT_CHILD_VISIBLE_CHECKER_AND_ENVIRONMENT_TEXT_RETAINED',
        excluded_visibility='HIDDEN_ORACLE_ANSWER_KEYS_READOUTS_AND_FINAL_NEVER_PARENT_CONTEXT',
        fable_launch='EXPLICIT_R112_WATCHER_GO_REQUIRED', astra6='EXPLICIT_LAPLACE_RELEASE_AND_FRESH_ADMISSION_REQUIRED',
        own4_5='CONTINUE_UNTIL_RECEIVER_READY_AND_OWN_COMPLETED_CYCLE',
        native_ready=False, new_native_calls=0, new_provider_calls=0, optimizer_steps=0,
        old_runtime_changed=False, old_deadlines_extended=False, outcome_may_stop_branch=False,
        remaining=['Immutable native backend and fresh runtime quotas/deadline', 'Shared transport V3 visibility binding',
            'Historical exclusion inventory completion', 'Legacy readout source binding',
            'Actual gated admission and cycle-zero readouts', 'Receiver-ready exact completed-cycle release mechanism'])
