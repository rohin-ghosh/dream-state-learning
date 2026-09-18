"""Verify manually adjudicated correction traces; perform no semantic inference."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from reader import digest, message_match


OWN = Path(__file__).resolve().parent


def reference(record):
    return {key: record[key] for key in ('index', 'kind', 'sha256')}


def verify_projection(cut):
    if not cut['window_complete']:
        raise ValueError('complete_window_required_for_order_and_absence')
    rows = cut['records']
    if rows[0]['index'] != cut['anchor_index'] or rows[-1]['sha256'] != cut['initial_head']['sha256']:
        raise ValueError('exact_fixed_window_endpoints')
    for previous, current in zip(rows, rows[1:]):
        if current['index'] != previous['index'] + 1 or current['previous_sha256'] != previous['sha256']:
            raise ValueError('no_omitted_intervening_records')
    return {row['index']: row for row in rows}


def stages(cut):
    rows = verify_projection(cut)
    requests = {row['request_digest']: row for row in rows.values() if row['kind'] == 'REQUEST'}
    responses = {row['document_sha256']: row for row in rows.values() if row['kind'] == 'RESPONSE'}
    commits = {row['source_sha256']: row for row in rows.values() if row['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED')}
    result = {}
    for stage in rows.values():
        if stage['kind'] != 'R184_STAGE':
            continue
        source = stage['source_sha256']
        if source not in responses or source not in commits:
            raise ValueError('stage_needs_actual_response_and_commit')
        response = responses[source]
        request = requests.get(response['request_digest'])
        if request is None or not request['index'] < response['index'] < commits[source]['index'] < stage['index']:
            raise ValueError('source_bound_request_response_commit_stage_order')
        if response['index'] in result:
            raise ValueError('one_stage_per_own_response')
        result[response['index']] = dict(response=response, request=request, commit=commits[source], stage=stage)
    return result


def rendered_parents(request):
    result = {}
    source_by_slot = {}
    for event in request['external']:
        if event['actor'] != 'parent':
            continue
        matches = [index for index, message in enumerate(request['messages']) if message_match(event, message)]
        if matches != event['rendered_message_indices']:
            raise ValueError('actual_message_render_must_match_projection')
        if matches:
            for slot in matches:
                if slot in source_by_slot and source_by_slot[slot] != event['source_sha256']:
                    raise ValueError('ambiguous_parent_sources_for_one_message')
                source_by_slot[slot] = event['source_sha256']
            result[event['source_sha256']] = dict(event, matches=matches)
    return result


def new_parent_exposures(cut, first_request, last_request):
    seen = set(rendered_parents(first_request))
    found = []
    for request in cut['records']:
        if request['kind'] != 'REQUEST' or not first_request['index'] < request['index'] <= last_request['index']:
            continue
        for source, event in rendered_parents(request).items():
            if source in seen:
                continue
            seen.add(source)
            found.append(dict(event_id=event['event_id'], source_sha256=source,
                first_request=reference(request), message_indices=event['matches'], masked=request['masked']))
    return found


def new_external_inputs(cut, first_request, last_request):
    def visible(request):
        return {event['source_sha256']: event for event in request['external']
            if any(message_match(event, message) for message in request['messages'])}
    seen = set(visible(first_request))
    found = {}
    for request in cut['records']:
        if request['kind'] != 'REQUEST' or not first_request['index'] < request['index'] <= last_request['index']:
            continue
        for source, event in visible(request).items():
            if source not in seen:
                found[source] = dict(event_id=event['event_id'], actor=event['actor'],
                    first_request=reference(request), text_sha256=hashlib.sha256(event['text'].encode()).hexdigest())
                seen.add(source)
    return found


def certify_level(identifies, applies, later_applies, relevant, distinct, reminder_count,
                  all_intervening_external_reviewed=False, unknown_interventions=True):
    if not identifies:
        return 0
    if not applies:
        return 1
    if (later_applies and relevant and distinct and reminder_count == 0
            and all_intervening_external_reviewed and not unknown_interventions):
        return 3
    return 2


def trace(cut, annotation):
    rows = verify_projection(cut)
    linked = stages(cut)
    initial_request = rows[annotation['feedback_request']]
    candidate = linked[annotation['candidate']]
    if initial_request['kind'] != 'REQUEST' or initial_request['index'] != candidate['request']['index']:
        raise ValueError('feedback_in_actual_identification_request')
    feedback = [event for event in rendered_parents(initial_request).values()
        if event['event_id'] == annotation['feedback_event']]
    if len(feedback) != 1 or not initial_request['masked']:
        raise ValueError('exact_masked_parent_feedback_required')
    feedback = feedback[0]
    if feedback['source_sha256'] not in cut['parent_sources']:
        raise ValueError('parent_publication_backing_required')
    quote = annotation['identification_quote']
    if annotation['identifies'] and (not quote or quote not in candidate['response']['text']):
        raise ValueError('literal_own_identification_span_required')
    following = [item for index, item in sorted(linked.items())
        if index > annotation['candidate'] and item['stage']['stage'] == 'ACT']
    if not following or following[0]['response']['index'] != annotation['next_act']:
        raise ValueError('NEXT_ACT_not_a_convenient_later_attempt')
    immediate = following[0]
    later = linked.get(annotation['later_act'])
    if later and (later['stage']['stage'] != 'ACT' or later['response']['index'] <= immediate['response']['index']):
        raise ValueError('distinct_later_relevant_ACT_required')
    immediate_new = new_parent_exposures(cut, initial_request, immediate['request'])
    later_new = new_parent_exposures(cut, immediate['request'], later['request']) if later else None
    actual_reminders = {item['event_id'] for item in later_new or []}
    if actual_reminders != set(annotation['reminders']):
        raise ValueError('all_new_parent_exposures_need_exact_manual_disposition')
    external_inputs = new_external_inputs(cut, initial_request, later['request']) if later else None
    dispositions = annotation.get('external_dispositions')
    reviewed = bool(later) and dispositions is not None and set(dispositions) == set(external_inputs)
    if dispositions is not None and any(value not in ('REMINDER', 'SOLUTION', 'NON_CORRECTIVE', 'UNKNOWN') for value in dispositions.values()):
        raise ValueError('explicit_manual_external_dispositions')
    unknown = not reviewed or 'UNKNOWN' in (dispositions or {}).values()
    reminders_all = sum(value in ('REMINDER', 'SOLUTION') for value in (dispositions or {}).values())
    level = certify_level(annotation['identifies'], annotation['applies'], annotation['later_applies'],
        annotation['later_relevant'], bool(later), max(len(actual_reminders), reminders_all), reviewed, unknown)
    evidence = []
    for item in (candidate, immediate, later):
        if item is None:
            continue
        evidence.append(dict(response=reference(item['response']), stage=item['stage']['stage'],
            stage_receipt=reference(item['stage']), commit=reference(item['commit']),
            request=reference(item['request']), request_masked=item['request']['masked'],
            request_digest=item['request']['request_digest'], cycle=item['request']['cycle'],
            text_sha256=hashlib.sha256(item['response']['text'].encode()).hexdigest()))
    quote_receipt = None
    if quote:
        start = candidate['response']['text'].index(quote)
        quote_receipt = dict(text=quote, start=start, end=start + len(quote),
            response=reference(candidate['response']))
    return dict(id=annotation['id'], label=annotation['label'], level=level, manual_disposition=annotation['reason'],
        feedback=dict(event_id=feedback['event_id'], source_sha256=feedback['source_sha256'],
            request=reference(initial_request), message_indices=feedback['matches'], masked=True,
            excerpt=feedback['text'], backing=cut['parent_sources'][feedback['source_sha256']]),
        identification_demonstrated=annotation['identifies'], identification_span=quote_receipt,
        next_ACT_applies=annotation['applies'], later_ACT_applies=annotation['later_applies'] if later else None,
        child_records=evidence, original_parent_verbatim_in_next_ACT_request=
            feedback['source_sha256'] in rendered_parents(immediate['request']),
        no_new_parent_between_identification_and_next_ACT=dict(proven=not immediate_new,
            scope='verified captured REQUESTs only; not absence of standing runtime task/context',
            request_start=initial_request['index'], request_end=immediate['request']['index'],
            newly_rendered_parent_events=immediate_new),
        new_parent_reminders_before_later_ACT=later_new, reminder_count_before_later_ACT=len(actual_reminders) if later else None,
        standing_runtime_task_represented=any('Initial object: Calculate 17 + 8 - 6 in plain digits.' in event['text']
            and any(message_match(event, message) for message in immediate['request']['messages'])
            for event in immediate['request']['external'] if event['actor']=='environment'),
        new_external_inputs_before_later=external_inputs,
        later_absence_claim=reviewed and not unknown and not reminders_all and not actual_reminders,
        all_intervening_external_inputs_semantically_cleared=reviewed and not unknown,
        level3_checkpoint_capture=None, lifetime_or_first_ever_claim=False)


def report():
    annotations_path = OWN / 'annotations.json'
    annotations = json.loads(annotations_path.read_bytes())
    arms = []
    for label in ('learner', 'frozen'):
        path = OWN / 'private/reproduced' / (label + '.json')
        cut = json.loads(path.read_bytes())
        linked = stages(cut)
        selected = [item for item in annotations['traces'] if item['label'] == label]
        traces = [trace(cut, item) for item in selected]
        completes = [row for row in cut['records'] if row['kind'] == 'SLEEP_COMPLETE']
        requests = [row for row in cut['records'] if row['kind'] == 'REQUEST']
        arms.append(dict(label=label, journal_id=cut['target']['journal_id'],
            native=dict(pid=cut['native']['pid'], start_ticks=cut['native']['start_ticks'],
                guard_sha256=cut['native']['guard_sha256'], loaded=reference(cut['loaded'])),
            observation_utc=cut['observed_utc'], cut_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            reader_source_sha256=cut['reader_source_sha256'], exact_window_reproduced=cut['exact_window_reproduced'],
            initial_head=cut['initial_head'], anchor_index=cut['anchor_index'],
            completed_sleep_cycles=[row['cycle'] for row in completes[1:]],
            completed_checkpoints=[{key: row[key] for key in ('index','sha256','cycle','optimizer_steps',
                'checkpoint_sha256','adapter_state_sha256','resume_state_sha256')} for row in completes],
            checkpoint_files_rehashed=False, request_count=len(requests), response_count=len(linked),
            ACT_count=sum(item['stage']['stage']=='ACT' for item in linked.values()),
            all_REQUESTs_masked=all(row['masked'] for row in requests),
            fully_reviewed_child_record_ids=sorted(linked), strongest_current_level=max(item['level'] for item in traces),
            traces=traces, runtime_recipes=[dict(record=reference(row), recipe=row['document'])
                for row in cut['records'] if row['kind']=='SLEEP_RECIPE']))
    result = dict(schema='POST_RECOVERY_PAIR_MANUAL_CORRECTION_REVIEW_V1',
        published_utc=datetime.now(timezone.utc).isoformat(), annotations_sha256=hashlib.sha256(annotations_path.read_bytes()).hexdigest(),
        arms=arms, complete_level3_sequences=0, autonomous_semantic_classifier=False,
        level_claim_scope='Only the fixed reviewed windows; not lifetime bests or a matched causal effect.',
        safety=dict(remote_writes=0, GPU_calls=0, life_signals=0, parent_messages=0, policy_changes=0,
            sealed_score_files_read=0, checkpoint_copies=0),
        next_discriminating_test='Owner-run matched short correction/next-ACT/later-near-transfer probe, '
            'with exact context/compaction and all reminder sources recorded. First verify the correction '
            'survives into ACT; then test a different arithmetic instance without a new corrective hint. '
            'Do not attribute results to learning until both chains and matched exposures are observed. Not dispatched.')
    (OWN / 'EVIDENCE.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(path=str(OWN/'EVIDENCE.json'), strongest={arm['label']:arm['strongest_current_level'] for arm in arms},
        reviewed_responses={arm['label']:arm['response_count'] for arm in arms}, complete_level3=0), indent=2))


if __name__ == '__main__':
    report()
