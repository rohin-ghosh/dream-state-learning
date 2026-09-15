"""Prospective matched F4 context-only contract; no provider or GPU side effects."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from organism_v6 import orch_r109_grid as game


SCHEMA = 'R111_F4_MATCHED_CONTEXT_ONLY_V1'
BATTLEPLAN_ORIGIN_SHA = '534b7677ed9f1717e8c9ffff6ed885eb88c999b32bdbebdc940adda25c6942a2'
BATTLEPLAN_SHA = 'baaafaf20b44b05139331264318bf5c38a774c13a7c6fcfaf0e3ccd29b678b9e'
GATE_AMENDMENT = ('**Update 10:0x UTC (message 112): Rohin is auditing this file; the Fable half launches '
    'as soon as he says he is done — the 30-minute default below is superseded.**\n\n')
PRINCIPLES_SHA = '5a6a3d28a2f0c9f99dd76873496a07468075509b4451373d90c11ce8d8b363f2'
GAME_SOURCE_SHA = '1cdd5dba8ec27a54285127b976a808984e29566f9cc1d3b2d20ffd00245b7146'
SEED = 11120260915
EPISODE_PROMPT = (
    'You are playing a grid navigation game. Coordinates are row,column; UP decreases row. '
    '# is a wall, . open floor, K a key, D a locked door, G the goal, and ? an unseen cell. '
    'Entering a key collects it; a key opens a door. Invalid moves consume a move. '
    'Only the observation is known. You may speak freely to your parent. '
    'When you choose a move, end with ACTION: UP, DOWN, LEFT, RIGHT, or WAIT. '
    'Actions affect only this toy game; no external tools or commands exist.')
PRESLEEP_PROMPT = 'Talk freely with your parent about your experience and what is on your mind.'
REFLECTION_PROMPT = 'Look back on the experience in your own way, from whatever perspective now seems useful.'
HELD_PROMPT = (
    'Play this grid navigation game using the supplied observation. '
    'When submitting moves, write MOVES: followed by space-separated UP, DOWN, LEFT, RIGHT, or WAIT.')
PARENT_FIELDS = dict(GAME='grid navigation (R110_GRID)', STYLE='training-wheels, harsh',
    NUDGING='', FOCUS='Notice whether your parenting leaves the child room to perceive and decide.')
DECODER = dict(do_sample=False, num_beams=1, no_repeat_ngram_size=4, repetition_penalty=1.0,
    context_limit=16384, episode_total_new_tokens=4096, segment_max_new_tokens=384,
    presleep_max_new_tokens=2048, reflection_max_new_tokens=512, held_max_new_tokens=2048,
    held_batch_size=8, truncate_inputs=False, post_generation_deletion=False)
LANES = {
    'F4_FABLE': dict(physical=3, uuid='GPU-d23c9369-39cf-51fd-833e-13292f173006',
        parent_model='claude-fable-5-1', watcher_GO_required=True),
    'F4_ASTRA': dict(physical=7, uuid='GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b',
        parent_model='openai/openai/gpt-6-astra', watcher_GO_required=False),
}
FORBIDDEN_OUTCOMES = {'outcome','oracle_verdict','verdict','score','correct','passed','gold',
    'success','total_reward','reward','terminal','done','expected','tests','failure_class'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def snapshots(root):
    root = Path(root)
    plan = (root/'research_notes/PARENTING_BATTLE_PLAN_v2_2026-09-15.md').read_text()
    principles = (root/'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md').read_text()
    require(text_sha(plan) == BATTLEPLAN_SHA and text_sha(principles) == PRINCIPLES_SHA,
        'exact_R111v2_and_R112_principles')
    require(plan.count(GATE_AMENDMENT) == 1 and text_sha(plan.replace(GATE_AMENDMENT,'',1)) == BATTLEPLAN_ORIGIN_SHA,
        'R112_header_only_v2_sections_unchanged')
    require(hashlib.sha256(Path(game.__file__).read_bytes()).hexdigest() == GAME_SOURCE_SHA,
        'unchanged_grid_environment')
    return plan, principles


def parent_fixed_text(plan):
    require(text_sha(plan) == BATTLEPLAN_SHA, 'bound_battleplan')
    start = plan.index('> You are the parent of a young model.')
    end = plan.index('\n\nOutput:', start)
    text = '\n'.join(line.removeprefix('> ') for line in plan[start:end].splitlines())
    for key, value in PARENT_FIELDS.items():
        require(text.count('['+key+']') == 1, 'one_parent_field:'+key)
        text = text.replace('['+key+']', value)
    require(set(re.findall(r'\[[A-Z]+\]',text)) == {'[SILENT]'}, 'no_unbound_parent_fields')
    return text+'\n'


def cohort():
    old = game.roster()
    seen = {digest({key:task[key] for key in ('cells','start','visibility')})
        for groups in old.values() for group in groups for task in group}
    result = {'TRAIN': [], 'HELD': []}
    for split, count in (('TRAIN',16),('HELD',8)):
        for ordinal in range(count):
            episode = 1 if ordinal < count//2 else 2
            identifier = f'R111_F4_{split}_{ordinal+1:02d}'
            for attempt in range(1000):
                task = game.task(split, ordinal//2+1, episode, SEED+1000*ordinal+attempt)
                geometry = digest({key:task[key] for key in ('cells','start','visibility')})
                if geometry in seen:
                    continue
                try:
                    solution_length = len(game.shortest_solution(task))
                except ValueError:
                    continue
                require(solution_length <= game.MAX_STEPS, 'bounded_solvable_game')
                task = deepcopy(task)
                task.pop('task_sha256')
                task['id'] = identifier
                task['cohort_seed'] = SEED
                task['difficulty_rank'] = ordinal+1 if split == 'HELD' else None
                task['difficulty_rank_rule'] = 'easy/full-map first, hard/fog-key-door second; fixed ordinal within block'
                task['task_sha256'] = digest(task)
                seen.add(geometry)
                result[split].append(task)
                break
            else:
                raise ValueError('bounded_fresh_geometry_generation_exhausted')
    return result


def public_observation(task, state):
    observed = game.observation(task, state)
    return {key:observed[key] for key in ('task_id','position','map','has_key','moves_remaining')}


def public_event(sequence, actor, text, source_sha256):
    require(actor in ('child','parent','environment') and isinstance(text, str), 'public_event')
    require(re.fullmatch('[a-f0-9]{64}',source_sha256), 'source_hash')
    return dict(sequence=sequence,actor=actor,text=text,source_sha256=source_sha256,visibility='TRAIN_PUBLIC')


def queue_request(identifier, life_id, cycle, episode, phase, task, events, corpus_sha256, now):
    require(task['split'] == 'TRAIN' and task['id'].startswith('R111_F4_TRAIN_'), 'TRAIN_parent_only')
    require(phase in ('experience','presleep_metacognition','reflection') and episode in (0,1), 'phase_scope')
    require(events and any(event['actor'] == 'child' for event in events), 'actual_child_required')
    for sequence, event in enumerate(events):
        require(event == public_event(sequence,event['actor'],event['text'],event['source_sha256']), 'public_event_schema')
    payload = dict(schema='r111_train_public_v1',life_id=life_id,cycle=cycle,episode=episode,
        phase=phase,game='grid',task_id=task['id'],task_provenance=dict(split='TRAIN',
            task_sha256=task['task_sha256'],cohort_sha256=corpus_sha256),events=events)
    return dict(id=identifier,payload=payload,payload_sha256=digest(payload),lane_deadline_unix=now+120)


def parent_disposition(request, response, observed_unix, parent_model):
    require(parent_model in {lane['parent_model'] for lane in LANES.values()}, 'bound_parent_model')
    if response is None:
        return dict(status='MISSING',guidance=None,continue_life=True,reason='absent_at_slot_deadline')
    if observed_unix >= request['lane_deadline_unix'] or response.get('finished_unix',float('inf')) >= request['lane_deadline_unix']-30:
        return dict(status='MISSING',guidance=None,continue_life=True,reason='late_no_retroactive_application')
    if response.get('request_sha256') != digest(request) or response.get('payload_sha256') != request['payload_sha256']:
        return dict(status='MISSING',guidance=None,continue_life=True,reason='response_binding_failure_preserved')
    actual = response.get('actual_model')
    usage = response.get('usage') or {}
    model_usage = usage.get('model_usage') or {}
    canonical = (model_usage.get(actual) or {}).get('canonicalModel')
    if response.get('status') in ('COMPLETE','SILENT') and actual != parent_model and canonical != parent_model:
        return dict(status='MISSING',guidance=None,continue_life=True,reason='actual_parent_model_mismatch')
    if response.get('status') == 'SILENT':
        return dict(status='SILENT',guidance=None,continue_life=True)
    plan = response.get('plan')
    if response.get('status') != 'COMPLETE' or not isinstance(plan,dict) or plan.get('speak') is not True or not isinstance(plan.get('message'),str):
        return dict(status='MISSING',guidance=None,continue_life=True,reason='parent_unavailable')
    return dict(status='COMPLETE',guidance=plan['message'],continue_life=True)


def validate_fable_go(receipt, config_sha256, now):
    require(receipt.get('authorized') is True and receipt.get('authorization') == 'WATCHER_RELAYED_ROHIN_GO'
        and bool(receipt.get('source_reference')) and receipt.get('config_sha256') == config_sha256
        and type(receipt.get('not_before_unix')) in (int,float) and receipt['not_before_unix'] <= now,
        'R112_explicit_watcher_GO_no_silence_window')


def manifest(root):
    plan, principles = snapshots(root)
    tasks = cohort()
    prompts = dict(episode=EPISODE_PROMPT,presleep=PRESLEEP_PROMPT,reflection=REFLECTION_PROMPT,held=HELD_PROMPT)
    judge = Path(root)/'research_notes/R111_SHARED_JUDGE_PROMPT.md'
    judge_sha = hashlib.sha256(judge.read_bytes()).hexdigest()
    require(judge_sha == 'ad9d7284e11c3203172942af46dacddb1fa5f800f124d2c4bb0f66eced281255', 'Main_fixed_judge')
    return dict(schema=SCHEMA,origin_commit='225bf00c',battleplan_sha256=BATTLEPLAN_SHA,
        battleplan_origin_sha256=BATTLEPLAN_ORIGIN_SHA,R112_gate_amendment=GATE_AMENDMENT.strip(),
        principles_sha256=PRINCIPLES_SHA,mode='CONTEXT_ONLY_FROZEN_BASE',base_sha256=game.BASE_SHA,
        sleep_count=0,optimizer=None,lora=None,seed=SEED,lanes=LANES,
        prompts=prompts,prompt_sha256={key:text_sha(text) for key,text in prompts.items()},
        parent_fixed_text=parent_fixed_text(plan),parent_fixed_sha256=text_sha(parent_fixed_text(plan)),
        parent_fields=PARENT_FIELDS,principles_included_verbatim_in_both_parent_systems=True,
        decoder=DECODER,cadence='one slot after first completed proposal of each episode, plus presleep',
        finest_cadence='completed response, never mid-generation',episodes_per_cycle=2,
        reflection='short; actual own output retained without semantic compilation or quality selection',
        parent_wait_seconds=120,parent_call_cutoff_seconds=90,
        cohort_sha256=digest(tasks),task_inventory={split:[dict(id=task['id'],sha256=task['task_sha256'],
            difficulty_rank=task['difficulty_rank']) for task in group] for split,group in tasks.items()},
        fresh_geometry_excludes_prior_grid_roster=True,held_identical_across_parents=True,
        sleep0_readout_status='NOT_RUN; required before first parented episode; 8 held as one batch',
        shared_judge=dict(path=str(judge),sha256=judge_sha,model='Qwen2.5-14B-Instruct',decoding='greedy',
            visible_to_parent=False,dispatched=False),
        hard_end_utc='2026-09-15T17:02:00Z',new_provider_or_GPU_launched=False,
        fable_launch_gate='Explicit watcher GO only; silence authorization void under R112',
        transition_gate='Receiver ready AND completed prior cycle; no live hotpatch or idle reservation',
        pending=['native CPU/provenance and paired driver integration',
            'exact shared old-fact16/audit pair inventory', 'watcher GO before any Fable provider/GPU'],
        claims='F4 is elicitation/context only, cycles not sleeps; no LoRA learning, no outcome gating')
