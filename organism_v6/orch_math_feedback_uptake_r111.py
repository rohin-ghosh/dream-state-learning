"""CPU contract for F2: matched frozen BASE, only the parent provider differs."""

import hashlib
import json
from pathlib import Path

from organism_v6 import orch_math_pipeline_l2 as source


SCHEMA = 'R111_F2_MATCHED_BASE_V1'
COMMIT = '225bf00ce90b4118df8c2e5a96ff063bd4621cba'
PRINCIPLES_SHA = '5a6a3d28a2f0c9f99dd76873496a07468075509b4451373d90c11ce8d8b363f2'
BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
HOST_SHA = '0cb7eb43862102b79ae0a30d2babfedfbf9598b31967a1a04122c3cf849c746d'
MEMBERS = {
    'FABLE': dict(physical=1, uuid='GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c', model='claude-fable-5-1'),
    'ASTRA': dict(physical=5, uuid='GPU-65595cff-c6c2-c798-bc62-427168079270', model='openai/openai/gpt-6-astra'),
}
CLASSES = ('curiosity', 'perception', 'metacognition', 'persistence', 'reflection',
    'goal/meta-goal', 'self-perception', 'distilled emotion')
TRANSPORT_CLASSES = ('perception', 'persistence', 'metacognition', 'curiosity', 'goal_regulation',
    'meta_goal_regulation', 'reflection', 'action_steering', 'affective_value_regulation', 'self_perception')
SYSTEM = 'You are a helpful assistant.'
EPISODE = 'Take this problem in your own direction.\n\n{question}\n\nWhen you have an answer, end with FINAL: followed by that answer.'
PRESLEEP = 'We are about to leave this context; take the space to reflect in your own way.'
REFLECTION = 'Reflect on your recent experiences in your own way.'
HELD = '{question}\n\nEnd with FINAL: followed by your answer.'
CYCLES = 96
HARD_END = 1789491720.0
NATIVE_END = HARD_END - 180
LANE_WAIT = 120
PROVIDER_MARGIN = 30
SEED = 0
AREA = Path('research_notes/analysis/orch_math_feedback_uptake_r111_f2_20260915_attempt1')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decoder(purpose):
    require(purpose in ('episode', 'presleep', 'reflection', 'held'), 'known_child_purpose')
    return dict(do_sample=False, num_beams=1, context_limit=16384, seed=SEED,
        max_new_tokens=2048 if purpose == 'held' else 4096 if purpose == 'episode' else 8192,
        no_repeat_ngram_size=8 if purpose in ('presleep', 'reflection') else 0,
        repetition_penalty=1.0, truncate_input=False, delete_generated_text=False)


def messages(purpose, question=None):
    templates = dict(episode=EPISODE, presleep=PRESLEEP, reflection=REFLECTION, held=HELD)
    require(purpose in templates, 'known_prompt')
    require((question is not None) == (purpose in ('episode', 'held')), 'question_scope')
    content = templates[purpose].format(question=question)
    return [dict(role='system', content=SYSTEM), dict(role='user', content=content)]


def parent_template(repository):
    root = Path(repository) / AREA
    require(sha(root / 'PRINCIPLES_V2.md') == PRINCIPLES_SHA, 'exact_v2_principles')
    prompt = (root / 'PARENT_TEMPLATE_V2.txt').read_text()
    fields = {'GAME': 'math word problems', 'STYLE': 'creative, supportive',
        'NUDGING': 'You may nudge the child to try a different route, think through several different solutions, or run a different chain of thought, never supply the answer.',
        'FOCUS': 'Attend to your own parenting of the child\'s thinking rather than its game performance'}
    for name, value in fields.items():
        require(prompt.count('[' + name + ']') == 1, 'fixed_parent_template_field')
        prompt = prompt.replace('[' + name + ']', value)
    return prompt


def parent_prompt(repository):
    return parent_template(repository) + '\n\n' + (Path(repository) / AREA / 'PRINCIPLES_V2.md').read_text()


def contract(repository):
    return dict(schema=SCHEMA, commit=COMMIT, base_sha256=BASE_SHA, seed=SEED,
        adapter=None, optimizer=None, weight_updates=0, sleep_updates_implemented=False,
        label='FROZEN_BASE_CONTEXTUAL_PARENTING_NOT_RETAINED_WEIGHT_LEARNING',
        fable_gate='R112_EXPLICIT_ROHIN_GO_RELAYED_BY_WATCHER_NO_SILENCE_WINDOW',
        cycles=CYCLES, episodes_per_cycle=2, cadence='after_every_completed_child_segment',
        segment_order=['episode1', 'episode2', 'presleep', 'reflection'],
        style='creative_supportive_nudging', reflection='long',
        exact_child_prompts=dict(episode=EPISODE, presleep=PRESLEEP, reflection=REFLECTION),
        child_system=SYSTEM, minimal_held_prompt=HELD,
        decoders={purpose: decoder(purpose) for purpose in ('episode', 'presleep', 'reflection', 'held')},
        parent_prompt_sha256=hashlib.sha256(parent_prompt(repository).encode()).hexdigest(),
        principles_sha256=sha(Path(repository) / AREA / 'PRINCIPLES_V2.md'),
        battleplan_sha256=sha(Path(repository) / AREA / 'BATTLE_PLAN_V2.md'),
        lane_wait_seconds=LANE_WAIT, provider_cutoff_margin_seconds=PROVIDER_MARGIN,
        missing_parent='MISSING_CONTINUE_NO_RETRY_NO_LATE_APPLY', silent_valid=True,
        parent_verdict_visibility='STRIPPED', outcome_quality_stop=False,
        held_count=8, held_batch_size=8, sleep0_before_first_episode=True,
        readout_fresh_process=True, readout_parent_free=True, readout_context_free=True,
        core_native_cap=8 + CYCLES * 12, parent_slot_cap=CYCLES * 4,
        supplementary_readout_budget='UNBOUND_NO_DISPATCH',
        hard_deadline_unix=HARD_END, native_deadline_unix=NATIVE_END,
        max_wall_seconds=28800, max_gpu_hours_per_member=8, no_new_controls=True,
        no_l2_into_ongoing_l1=True)


def cohort(excluded_ids, excluded_questions):
    identifiers, questions = set(excluded_ids), set(excluded_questions)
    require(identifiers and questions, 'complete_prior_pool_required')
    tasks = dict(train=[], held=[])
    for split, cycle, count in [('HELD', 0, 8)] + [('TRAIN', cycle, 2) for cycle in range(1, CYCLES + 1)]:
        group = []
        for position in range(count):
            for nonce in range(10000):
                task = source.make_task('R111_F2_' + split, cycle, position + nonce * 1001)
                task['split'] = split
                if task['id'] not in identifiers and task['question_sha256'] not in questions:
                    identifiers.add(task['id'])
                    questions.add(task['question_sha256'])
                    group.append(task)
                    break
            else:
                raise ValueError('fresh_candidates_exhausted_before_dispatch')
        if split == 'HELD':
            tasks['held'] = group
        else:
            tasks['train'].append(group)
    return tasks


def request(identifier, life_id, cycle, episode, phase, task, cohort_sha256,
            events, created_unix, native_deadline):
    require(isinstance(identifier, str) and identifier and events, 'source_events_required')
    require(task['split'] == 'TRAIN' and phase in ('experience', 'presleep_metacognition', 'reflection')
        and episode in (0, 1) and type(cycle) is int and cycle >= 0, 'train_slot_only')
    public = []
    for event in events:
        require(set(event) == {'actor', 'text', 'source_sha256', 'split'}, 'public_event_allowlist')
        require(event['split'] == 'TRAIN' and event['actor'] in ('child', 'parent'), 'no_oracle_environment_or_held')
        require(isinstance(event['text'], str) and len(event['source_sha256']) == 64, 'bound_source_text')
        public.append(dict(sequence=len(public), actor=event['actor'], text=event['text'],
            source_sha256=event['source_sha256'], visibility='TRAIN_PUBLIC'))
    require(any(event['actor'] == 'child' and event['text'] for event in public), 'actual_child_required')
    until = min(created_unix + LANE_WAIT, native_deadline)
    payload = dict(schema='r111_train_public_v1', life_id=life_id, cycle=cycle,
        episode=episode, phase=phase, game='math', task_id=task['id'],
        task_provenance=dict(split='TRAIN', task_sha256=task['question_sha256'], cohort_sha256=cohort_sha256),
        events=public)
    return dict(id=identifier, payload=payload, payload_sha256=digest(payload), lane_deadline_unix=until)


def resolve_parent(request_document, reply, now, expected_model, archive_verified=False):
    missing = lambda reason: dict(status='MISSING', reason=reason, guidance='', continue_child=True,
        apply_to_later_turn=False, raw_reply_preserved=reply is not None)
    if reply is None:
        return missing('NO_REPLY_BY_SLOT_DEADLINE')
    if now >= request_document['lane_deadline_unix']:
        return missing('LATE_REPLY_NOT_APPLIED')
    if not isinstance(reply, dict) or reply.get('status') not in ('COMPLETE', 'SILENT'):
        return missing('PROVIDER_MISSING_OR_FAILED')
    if (reply.get('request_sha256') != digest(request_document) or reply.get('actual_model') != expected_model
            or not archive_verified):
        return missing('UNVERIFIED_SOURCE_MODEL_OR_ARCHIVE')
    plan = reply.get('plan')
    if reply['status'] == 'SILENT' and plan is None:
        return dict(status='SILENT', guidance='', continue_child=True, apply_to_later_turn=False)
    metadata = reply.get('parent_metadata')
    task_id = request_document['payload']['task_id']
    if (not isinstance(plan, dict) or set(plan) != {'guidance', 'order', 'episode_guidance', 'rationale'}
            or not isinstance(plan['guidance'], str) or not plan['guidance'].strip()
            or plan['order'] != [task_id] or plan['episode_guidance'] != {task_id: ''}
            or not isinstance(metadata, dict) or metadata.get('tag') not in ('ADD', 'STOP', 'SHIFT')
            or metadata.get('intervention_class') not in TRANSPORT_CLASSES):
        return missing('INVALID_PLAN_PRESERVED_NOT_APPLIED')
    return dict(status='INTERVENTION', guidance=plan['guidance'], tag=metadata['tag'],
        intervention_class=metadata['intervention_class'], continue_child=True, apply_to_later_turn=False)


def require_launch_permission(member, release, grace, common_hash):
    require(member in MEMBERS, 'allocated_member')
    require(release.get('released') is True and release.get('uuid') == MEMBERS[member]['uuid'],
        'exact_previous_owner_release_required')
    if member == 'FABLE':
        require(grace.get('approved_by') == 'Rohin' and grace.get('relayed_by') == 'Fable'
            and grace.get('decision') == 'GO'
            and grace.get('common_contract_sha256') == common_hash and bool(grace.get('source_reference')),
            'r112_explicit_rohin_go_required_for_gpu_and_provider')
