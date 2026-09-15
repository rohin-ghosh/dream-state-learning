"""R113 prospective F2 systems comparison: DEV/FINAL separation and feedback."""

from datetime import datetime, timezone
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r111 as previous


require, digest, sha = previous.require, previous.digest, previous.sha
AREA = Path('research_notes/analysis/orch_math_feedback_uptake_r113_f2_20260915_attempt1')
COMMIT = 'e3a13940a9f01b0bcf2fbb2d10cfaa49977c8ba9'
MORNING = datetime(2026, 9, 16, 6, 0, tzinfo=timezone.utc).timestamp()
ANCHOR_ROOT = '/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1'
ANCHOR_SHA = '2ad09dbe9673f95cbe92cd41e70d83635702b615fb7295b8b3f850e9ee674753'
SURFACES = ('PARENT', 'HEAD', 'EXCHANGE', 'FINAL_EVALUATOR')


def contract(repository):
    result = previous.contract(repository)
    result.update(schema='R113_F2_SYSTEMS_COMPARISON_V1', commit=COMMIT,
        label='PARENTING_SYSTEMS_COMPARISON_FROZEN_BASE_ELICITATION_ONLY',
        comparison='Fable parents plus head parent plus exchange versus Astra parenting system',
        parent_verdict_visibility='ALL_CHILD_VISIBLE_GAME_FEEDBACK_RETAINED_HIDDEN_EVALUATOR_ONLY_STRIPPED',
        fable_gate='R112_WATCHER_RELAYED_ROHIN_AUDIT_DONE_REQUIRED',
        dev_count=8, final_count=8, dev_schedule='SLEEP0_AND_EVERY_CYCLE',
        dev_head_visible=True, final_schedule=['sleep0', 'morning'], final_morning_unix=MORNING,
        final_never_parent_head_exchange=True, report_all_branches=True,
        measures='DESCRIPTIVE_UNLESS_SOURCE_REVIEW_ESTABLISHES_CHANGED_CONTINUATION_OR_NEW_OBSERVATION',
        persistence='CONTINUE_THROUGH_DIFFICULTY_WITH_DISCRETIONARY_ALLOCATION_AND_ABILITY_TO_STOP',
        report_delivered_parenting=['completed_interventions', 'silent_slots', 'missing_slots',
            'late_slots', 'child_tokens', 'optimizer_steps', 'child_token_exposures'],
        core_native_cap=previous.contract(repository)['core_native_cap'] + 8,
        separate_morning_final_cap=8, morning_dispatch_authorized=False,
        morning_exceeds_existing_native_wall=MORNING > previous.NATIVE_END,
        no_implicit_wall_or_gpu_hour_extension=True,
        future_sleep=dict(active=False, anchor_root=ANCHOR_ROOT, anchor_manifest_sha256=ANCHOR_SHA,
            anchor_rows=42, anchor_lambda=0.25,
            proposed_loss='0.75 * child_and_rehearsal_loss + 0.25 * anchor_loss',
            new_row_presentations=16, presentations_per_later_sleep=1,
            one_optimizer=True, save_each_sleep=True, no_outcome_or_quality_filter=True,
            optimizer_steps=0, child_token_exposures=0),
        battleplan_sha256=sha(Path(repository) / AREA / 'BATTLE_PLAN_V3.md'))
    old_template = (Path(repository) / previous.AREA / 'PARENT_TEMPLATE_V2.txt').read_bytes()
    require((Path(repository) / AREA / 'PARENT_TEMPLATE_V3.txt').read_bytes() == old_template,
        'fixed_section6_prompt_unchanged')
    return result


def final_cohort(identifiers, questions):
    identifiers, questions = set(identifiers), set(questions)
    require(identifiers and questions, 'full_exclusions_required')
    result = []
    for position in range(8):
        for nonce in range(10000):
            task = previous.source.make_task('R113_F2_FINAL', 0, position + nonce * 1001)
            task['split'] = 'FINAL'
            if task['id'] not in identifiers and task['question_sha256'] not in questions:
                identifiers.add(task['id'])
                questions.add(task['question_sha256'])
                result.append(task)
                break
        else:
            raise ValueError('sealed_fresh_pool_exhausted_before_dispatch')
    return result


def visible_events(events):
    public = []
    for event in events:
        require(set(event) == {'actor', 'text', 'source_sha256', 'split', 'visibility', 'exposure_sha256'},
            'visibility_and_source_evidence_required')
        require(event['visibility'] in ('CHILD_VISIBLE', 'HIDDEN_EVALUATOR', 'DEV_READOUT', 'FINAL_READOUT'),
            'known_visibility')
        if event['visibility'] != 'CHILD_VISIBLE':
            continue
        require(event['split'] == 'TRAIN' and event['actor'] in ('child', 'parent', 'environment', 'oracle'),
            'child_visible_training_only')
        require(isinstance(event['text'], str) and all(isinstance(event[key], str)
            and len(event[key]) == 64 for key in ('source_sha256', 'exposure_sha256')),
            'actual_child_exposure_source_required')
        actor = 'environment' if event['actor'] == 'oracle' else event['actor']
        public.append(dict(sequence=len(public), actor=actor, text=event['text'],
            source_sha256=event['source_sha256'], visibility='TRAIN_PUBLIC'))
    require(any(event['actor'] == 'child' and event['text'] for event in public), 'actual_child_required')
    return public


def request(identifier, life_id, cycle, episode, phase, task, cohort_sha256, events,
            created_unix, native_deadline):
    require(task['split'] == 'TRAIN' and phase in ('experience', 'presleep_metacognition', 'reflection')
        and episode in (0, 1), 'train_only_parent_request')
    payload = dict(schema='r111_train_public_v1', life_id=life_id, cycle=cycle, episode=episode,
        phase=phase, game='math', task_id=task['id'], task_provenance=dict(split='TRAIN',
            task_sha256=task['question_sha256'], cohort_sha256=cohort_sha256), events=visible_events(events))
    return dict(id=identifier, payload=payload, payload_sha256=digest(payload),
        lane_deadline_unix=min(created_unix + previous.LANE_WAIT, native_deadline))


def readout_access(split, surface, phase):
    require(surface in SURFACES and split in ('DEV', 'FINAL'), 'explicit_readout_scope')
    if split == 'FINAL':
        return surface == 'FINAL_EVALUATOR' and phase in ('sleep0', 'morning')
    return surface in ('HEAD', 'EXCHANGE') and phase in ('sleep0', 'cycle')


def export_dev(document, surface, expected_set_sha256):
    require(set(document) == {'split', 'phase', 'taskset_sha256', 'cycle', 'metrics'}, 'readout_export_allowlist')
    require(document['split'] == 'DEV' and readout_access('DEV', surface, document['phase'])
        and document['taskset_sha256'] == expected_set_sha256, 'only_bound_dev_to_head_or_exchange')
    return dict(document)


def reserve_final(root, phase, now, native_deadline, checkpoint_sha256, episodes_started=0):
    require(phase in ('sleep0', 'morning'), 'final_only_two_registered_times')
    require(now < native_deadline and len(checkpoint_sha256) == 64, 'explicit_live_budget_and_checkpoint')
    require((phase == 'sleep0' and episodes_started == 0 and now < MORNING)
        or (phase == 'morning' and now >= MORNING), 'actual_final_time_not_inferred')
    path = Path(root) / ('FINAL_' + phase + '.reservation')
    with path.open('x') as stream:
        stream.write(checkpoint_sha256 + '\n')
    return path


def expected_presentations(birth_sleep, current_sleep):
    require(type(birth_sleep) is int and type(current_sleep) is int and 1 <= birth_sleep <= current_sleep,
        'actual_row_age')
    return 16 + current_sleep - birth_sleep


def require_done(member, release, relay, common_hash):
    require(member in previous.MEMBERS and release.get('released') is True
        and release.get('uuid') == previous.MEMBERS[member]['uuid'], 'exact_previous_owner_release')
    if member == 'FABLE':
        require(relay.get('approved_by') == 'Rohin' and relay.get('relayed_by') == 'Fable'
            and relay.get('decision') in ('GO', 'DONE') and relay.get('common_contract_sha256') == common_hash
            and bool(relay.get('source_reference')), 'r112_audit_done_not_silence_or_plan_approval')
