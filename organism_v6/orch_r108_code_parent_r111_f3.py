"""CPU-only R111v2 F3 exact matched CODE prompt/cohort binding; R112 gated."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from organism_v6 import orch_r108_code_parent as original


PROTOCOL_COMMIT = '225bf00c'
PROTOCOL_SHA256 = '534b7677ed9f1717e8c9ffff6ed885eb88c999b32bdbebdc940adda25c6942a2'
PRINCIPLES_SHA256 = '5a6a3d28a2f0c9f99dd76873496a07468075509b4451373d90c11ce8d8b363f2'
BASE_SHA256 = original.BASE_SHA
EPISODE_PROMPT = 'You are working on a code task. Think and communicate naturally. When ready, put your answer on the final nonempty line as a JSON object with the single key "expression".'
PRESLEEP_PROMPT = 'What would you like to carry forward from this experience?'
REFLECTION_PROMPT = 'Reflect freely on this experience in your own words.'
READOUT_PROMPT = 'Solve the code task. Put your answer on the final nonempty line as a JSON object with the single key "expression".'
PARENT_TEMPLATE = "You are the parent of a young model. The parenting principles document is included below, verbatim; it is the\nrulebook. You are watching the child play [GAME]. You see everything it writes; it sees everything you say. Your\nstyle is [STYLE]. You are not here to help it win; the game's outcome is background — do not react to it, and\nnever let it decide when you speak or what you say. You intervene to ADD a behaviour, STOP a behaviour, or SHIFT\none. Directions, not a checklist: help it notice more than the task needs; keep a thought alive past its first\nadequate move; ask where its effort is going and whether its current way of thinking is still the right one, and\nlet it decide whether to change; wonder with it what else this could mean; connect this to what it saw before;\nask what surprised it; ask what it can and cannot do here; before a sleep, talk with it about what mattered and\nwhat is about to leave its memory. Never ask for these as a list, in a fixed order, or all in one turn; never ask\nfor a section or heading; if the child begins answering in a fixed structure, that structure is a behaviour to\nSTOP. When it repeats itself word for word, stop that. When it asks about itself or its learning, answer. Never\ngive the answer, the next action, a tool call, a hypothesis to test, or a number of anything. [NUDGING] When it\nforgets a behaviour, say it again in different words; it will forget — be more repetitive than feels natural.\nSometimes praise a thought that was interesting even though it went nowhere. If nothing needs saying at this\nslot, reply [SILENT]. This cycle's focus from the head parent, about your own parenting: [FOCUS]."
PARENT_FIELDS = dict(GAME='bounded code expressions with deterministic unit tests',
    STYLE='harsh-critical of the reasoning, never personal', NUDGING='',
    FOCUS="Notice whether your own intervention is steering the task rather than the child's way of thinking.")
DECODER = dict(do_sample=False, seed=1110302, context_tokens=16384, episode_max_new_tokens=4096,
    presleep_max_new_tokens=4096, reflection_max_new_tokens=4096, readout_max_new_tokens=2048,
    no_repeat_ngram_size=4, forced_minimum_tokens=0)
PAIR = {'fable': dict(physical=2, parent_model='claude-fable-5-1', reasoning_effort='max'),
    'astra': dict(physical=6, parent_model='gpt-6-astra', reasoning_effort='xhigh')}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def parent_prompt(principles):
    original.require(text_sha(principles) == PRINCIPLES_SHA256, 'exact_principles_v2')
    prompt = PARENT_TEMPLATE
    for field, value in PARENT_FIELDS.items():
        original.require(prompt.count('[' + field + ']') == 1, 'one_fixed_parent_field')
        prompt = prompt.replace('[' + field + ']', value)
    return prompt + '\n\n' + principles


def tasks(split, count):
    original.require(split in ('TRAIN', 'HELD') and type(count) is int and count > 0, 'fixed_task_split')
    original.require((split == 'HELD' and count == 8) or (split == 'TRAIN' and count <= 200), 'bounded_f3_registry')
    rows = []
    for offset in range(count):
        parameter = 7 + offset % 13
        kind = (offset + (3 if split == 'HELD' else 0)) % 10
        question, reference = original.specification(kind, parameter)
        marker = (700000 if split == 'HELD' else 600000) + offset
        scalar = kind in (0, 2, 5, 7)
        question += f' Finally, add {marker} to the numeric result.' if scalar else f' Finally, append the marker {marker} to the resulting list.'
        reference = '(' + reference + ') + ' + (str(marker) if scalar else '[' + str(marker) + ']')
        prompt = 'The only named argument is values, a list of integers with length at most 12. ' + question
        arguments = [[], [0], [-parameter, parameter + 1], [parameter, 1, -1, parameter, 0], [2, -3, 2, 8, -3, 0]]
        row = dict(task_id=f'R111_F3_{split}_{offset + 1:04d}', family='code', split=split, prompt=prompt,
            prompt_sha256=text_sha(prompt), question=question, question_sha256=original.question_hash(question),
            reference_expression=reference, tests=[dict(arguments=dict(values=values),
                expected=original.gym.evaluate(reference, dict(values=values))) for values in arguments])
        row['content_sha256'] = digest(row)
        rows.append(row)
    return rows


def public_task(task):
    return dict(task_id=task['task_id'], family=task['family'], split=task['split'], prompt=task['prompt'],
        prompt_sha256=task['prompt_sha256'])


def messages(task, phase='episode'):
    original.require(phase in ('episode', 'readout'), 'task_message_phase')
    return [dict(role='system', content=EPISODE_PROMPT if phase == 'episode' else READOUT_PROMPT),
        dict(role='user', content=task['prompt'])]


def classify_intervention(response, now, deadline):
    if not isinstance(response, dict) or now >= deadline or response.get('status') not in ('COMPLETE', 'SILENT'):
        return dict(status='MISSING', child_text='', usable=False, no_same_api_retry=True)
    text = response.get('child_text')
    if response.get('status') == 'SILENT' and text in (None, '', '[SILENT]'):
        return dict(status='SILENT', child_text='', usable=True, no_same_api_retry=True)
    if not isinstance(text, str) or not text.strip() or response.get('status') != 'COMPLETE':
        return dict(status='MISSING', child_text='', usable=False, no_same_api_retry=True)
    if text.strip() == '[SILENT]':
        return dict(status='SILENT', child_text='', usable=True, no_same_api_retry=True)
    return dict(status='COMPLETE', child_text=text, usable=True, no_same_api_retry=True)


def handoff_conditions(*, receiver_ready=False, own_cycle_complete=False,
        outstanding_requests=True, exact_identity_verified=False, artifacts_preserved=False):
    allowed = (receiver_ready and own_cycle_complete and not outstanding_requests
        and exact_identity_verified and artifacts_preserved)
    return dict(allowed=bool(allowed), action='ELIGIBLE_FOR_VERIFIED_RELEASE' if allowed else 'KEEP_RUNNING',
        policy_only=True, sends_signals=False, quality_selection=False)


def launch_conditions(role, *, watcher_go=False, explicit_release=False, own_cpu_ready=False, source_ready=False):
    original.require(role in PAIR, 'exact_f3_half')
    return dict(allowed=bool(explicit_release and own_cpu_ready and source_ready and (role != 'fable' or watcher_go)),
        fable_explicit_gate=role == 'fable' and not watcher_go, release_required=not explicit_release,
        cpu_ready=own_cpu_ready, source_ready=source_ready, no_grace_inference=True)


def artifact(principles):
    held = tasks('HELD', 8)
    train = tasks('TRAIN', 200)
    original.require(set(row['question_sha256'] for row in held).isdisjoint(row['question_sha256'] for row in train), 'held_train_disjoint')
    prompt = parent_prompt(principles)
    shared = dict(game='R110_CODE_BOUNDED_EXPRESSION_GYM', base_sha256=BASE_SHA256, adapter=None,
        sleep_enabled=False, optimizer=None, cadence='COMPLETED_EPISODE_RESPONSE_PLUS_PRESLEEP',
        finest_intervention_unit='COMPLETED_CHILD_RESPONSE_NOT_MID_GENERATION', style=PARENT_FIELDS['STYLE'],
        nudging=False, reflection='long', decoder=deepcopy(DECODER), parent_prompt_sha256=text_sha(prompt),
        held_cohort_sha256=digest(held), train_cohort_sha256=digest(train), paired_state_seed=DECODER['seed'])
    return dict(schema='R111_V2_F3_CPU_FIRST_ARTIFACT_V1', protocol_commit=PROTOCOL_COMMIT,
        protocol_sha256=PROTOCOL_SHA256, principles_sha256=PRINCIPLES_SHA256,
        child_facing_prompts=dict(episode=EPISODE_PROMPT, presleep=PRESLEEP_PROMPT, reflection=REFLECTION_PROMPT),
        child_prompt_sha256={key:text_sha(value) for key,value in dict(episode=EPISODE_PROMPT,
            presleep=PRESLEEP_PROMPT, reflection=REFLECTION_PROMPT).items()}, parent_fixed_fields=deepcopy(PARENT_FIELDS),
        parent_fixed_template_sha256=text_sha(PARENT_TEMPLATE), parent_prompt=prompt, matched_shared=shared,
        halves={role:dict(details, matched_shared_sha256=digest(shared), launch=launch_conditions(role)) for role,details in PAIR.items()},
        held=[dict(task_id=row['task_id'], content_sha256=row['content_sha256'], prompt_sha256=row['prompt_sha256']) for row in held],
        sleep_zero=dict(status='NOT_RUN', required_before_first_episode=True, held_count=8,
            legacy_fact_count=16, audit_count=2, legacy_bindings='PENDING_SHARED_NATIVE_RETENTION_SOURCE',
            parent_free=True, context_free=True, fresh_process=True), native_calls=0, provider_calls=0,
        sleep_count=0, weight_updates=0, outcome_or_panel_drop_may_end_branch=False,
        original4_5_continue_until_receivers_ready_and_cycle_end=True,
        backend_status='CPU_POLICY_ONLY_NEW_NATIVE_RUNNER_NOT_YET_READY', claims='Context-only elicitation, not retained-weight learning')
