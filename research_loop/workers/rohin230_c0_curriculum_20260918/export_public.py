"""Read-only, explicit-field C0 evidence projection; never export child text."""

from collections import Counter
import json
from pathlib import Path
import time

from c0_receipt import ROOT, canonical, checked_record, identity, require, sha, utc
from curriculum_parent import capture_inbox, request_receipt
from handoff import process


OPERATOR = Path('/localhome/local-rohing/orch_r230_c0_operator_20260918')


def read(path):
    return json.loads(path.read_bytes())


def bound_response(pending, request_index, response_index, stage_index):
    records = ROOT/'raw/stream/records'
    request = checked_record(records/f'{request_index:020d}.json')
    response = checked_record(records/f'{response_index:020d}.json')
    stage = checked_record(records/f'{stage_index:020d}.json')
    rendered = request_receipt(pending, request, pending.get('story_excerpt', ''))
    require(rendered and response['document']['request_sha256'] == rendered['request_sha256'], 'actual_response_request_binding')
    require(stage['document']['source_sha256'] == sha(canonical(response['document'])), 'actual_stage_response_binding')
    return dict(request=rendered, response=dict(index=response_index, sha256=response['sha256'],
        raw_sha256=sha(response['document']['response']['raw'].encode()),
        finished_utc=utc(response['document']['finished_unix']),
        source_path=str(records/f'{response_index:020d}.json')),
        stage=dict(index=stage_index, sha256=stage['sha256'], name=stage['document']['stage']))


def main():
    from reading_parent import protocol
    owner = identity()
    current = OPERATOR/'curriculum_current'
    service = read(current/'SERVICE.json')
    state = read(current/'STATE.json')
    service_identity = process(service['pid'], service['start_ticks'], 'curriculum_parent.py')
    math_identity = process(2561001, 94172764, str(ROOT/'parent.py'))
    pending = read(OPERATOR/'curriculum/PUBLISHED_0000.json')
    pending['story_excerpt'] = protocol(Path(__file__).with_name('PROTOCOL.md'))[0]
    inbox = checked_record(ROOT/'raw/stream/records/00000000000000001535.json')
    capture_inbox(pending, inbox)
    first = bound_response(pending, 1537, 1538, 1540)
    act = bound_response(pending, 1546, 1547, 1549)
    paths = sorted((ROOT/'raw/stream/records').glob('[0-9]'*20+'.json'))[-128:]
    records = [checked_record(path) for path in paths]
    complete = next(record for record in reversed(records) if record['kind']=='SLEEP_COMPLETE')
    eligibility = next(record for record in reversed(records) if record['kind']=='TARGET_ELIGIBILITY')
    recipe = next(record for record in reversed(records) if record['kind']=='SLEEP_RECIPE')
    document = eligibility['document']
    exclusions = document.get('excluded', [])
    reason_counts = Counter(item.get('reason', 'unspecified') for item in exclusions)
    next_reading = read(current/'PUBLISHED_0001.json') if (current/'PUBLISHED_0001.json').exists() else None
    reading_delivery = {name: read(current/name) for name in ('RENDER_0001.json', 'FIRST_CONTENT_0001.json', 'TURN_0001.json') if (current/name).exists()}
    projection = dict(observed_utc=utc(time.time()), identity=owner, original_math_parent=math_identity,
        current_publisher=dict(service=service, actual_process=service_identity,
            state={key: state.get(key) for key in ('completed_cycle','record_cursor','publications','topic_index','reading_step','next_due_cycle','unresolved_recall')},
            pending_topic=(state.get('pending') or {}).get('topic'),
            failure_receipt_present=(current/'FAILED.json').exists()),
        graceful_handoff=read(OPERATOR/'curriculum/HANDOFF.public.json'),
        coherent_checkpoint_before_addition=read(OPERATOR/'curriculum/BEFORE_HANDOFF.public.json')['checkpoint'],
        reprobe=dict(publication=pending['publication'], published_utc=pending['published_utc'],
            text_sha256=pending['text_sha256'], inbox=pending['inbox'], first_content=first, act=act,
            manual_review=dict(reviewer='C0 operator', observed_content='Predominantly Chinese restatement of the method/task; not an actual story recollection or explicit first-person lack-of-recall answer.',
                recall='unresolved', content_vs_intention='method_or_intention_only',
                relation_to_own_situation='not_answered', story_detail_accuracy='not_scored',
                context_carryover_controlled=False, adapter_retention_claim=False)),
        reading_followup=None if not next_reading else {key:next_reading.get(key) for key in ('number','topic','published_utc','publication','after_cycle','reading_step','text_sha256')},
        reading_delivery=reading_delivery,
        current_native_learning=dict(completed_sleep_index=complete['index'], completed_sleep_sha256=complete['sha256'],
            cycle=complete['document']['cycle'], optimizer_steps=complete['document']['total_optimizer_steps'],
            recipe_index=recipe['index'], recipe_sha256=recipe['sha256'],
            recipe={key:recipe['document'].get(key) for key in ('policy','code_target_filter','learn_review_filter','new_rows','selected_old_rows','new_presentations')},
            eligibility_index=eligibility['index'], eligibility_sha256=eligibility['sha256'],
            excluded_count=len(exclusions), excluded_reason_counts=dict(reason_counts),
            raw_modified=document.get('raw_modified'),
            semantic_filters_off=False, supported_live_disable='Not established for resident C0; source changes do not change this process. No native intervention authorized or performed.'),
        corrections=read(current/'RECEIPT_CORRECTION.public.json'),
        safety=dict(raw_child_text_exported=False, external_messages_masked=True, model_calls=0,
            learner_signals=0, learner_restarts=0, learning_rate_changes=0, no_birth_reset=True,
            no_new_Astra7_parent=True, parent_turns_withheld=0))
    print(json.dumps(projection, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
