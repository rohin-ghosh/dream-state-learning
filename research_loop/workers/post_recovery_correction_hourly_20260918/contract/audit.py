"""Receipt validation and conservative correction-level adjudication."""

import hashlib
import re


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def frames(evidence):
    requests, responses, commits, stages = {}, {}, {}, {}
    for row in evidence['records']:
        if row['kind'] == 'REQUEST':
            requests[row['request_digest']] = row
        elif row['kind'] == 'RESPONSE':
            responses[row['document_sha256']] = row
        elif row['kind'] in ('COMMITTED', 'CONTEXT_COMMITTED'):
            commits[row['source_sha256']] = row
        elif row['kind'] == 'R184_STAGE':
            stages[row['source_sha256']] = row
    result = []
    for source, response in responses.items():
        request = requests.get(response['request_digest'])
        commit, stage = commits.get(source), stages.get(source)
        if not request or not commit or not stage:
            continue
        if not request['masked'] or not request['index'] < response['index'] < commit['index'] < stage['index']:
            raise ValueError('committed_masked_source_order')
        result.append(dict(response=response, request=request, commit=commit, stage=stage['stage'], stage_receipt=stage))
    return sorted(result, key=lambda item: item['response']['index'])


def ref(row):
    return {key: row[key] for key in ('index', 'sha256', 'kind')}


def exposure_id(event):
    return event['event_id'] + ':' + event['source_sha256']


def candidates(evidence):
    found = {}
    inboxes = {row['event_id']: row for row in evidence['records'] if row['kind'] == 'INBOX'}
    for frame in frames(evidence):
        for event in frame['request']['external']:
            text = event['text']
            if text.startswith(('Runtime status:', 'Your visible context was compacted', 'The working state')):
                continue
            if not (event['actor'] == 'parent' or event.get('phase') == 'feedback'):
                continue
            if not re.search(r'wrong|incorrect|error|not |check|instead|fail|reject|revise|correc|mistake|no caption|错误|不对|修改|检查|更正|纠正', text, re.I):
                continue
            key = exposure_id(event)
            if key not in found:
                inbox = inboxes.get(event['event_id'])
                found[key] = dict(key=key, event=event, first_request=ref(frame['request']),
                    first_response=ref(frame['response']), inbox=ref(inbox) if inbox else None,
                    semantic_status='Candidate external feedback, not a proved correction or compliance.')
    return list(found.values())


def validate_span(frame, annotation):
    row = frame['response']
    if annotation['index'] != row['index'] or annotation['sha256'] != row['sha256']:
        raise ValueError('exact_child_record_required')
    start, end = annotation['start'], annotation['end']
    text = row['text']
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise ValueError('actual_nonempty_child_span')
    if text_sha(text[start:end]) != annotation['span_sha256']:
        raise ValueError('literal_child_span_hash')
    return dict(record=ref(row), request=ref(frame['request']), committed=ref(frame['commit']),
        stage=frame['stage'], stage_record=ref(frame['stage_receipt']), start=start, end=end,
        span_sha256=annotation['span_sha256'], cycle=frame['request']['cycle'])


def adjudicate(evidence, annotation):
    if annotation['journal_id'] != evidence['journal_id']:
        raise ValueError('same_life_annotation')
    if annotation.get('feedback_reviewed_as_correction') is not True:
        raise ValueError('semantic_feedback_review_required')
    ordered = frames(evidence)
    by_index = {frame['response']['index']: frame for frame in ordered}
    feedback = next((item for item in candidates(evidence) if item['key'] == annotation['feedback_key']), None)
    if feedback is None:
        raise ValueError('actual_rendered_feedback_required')
    result = dict(level=0, journal_id=evidence['journal_id'], correction_key=annotation['feedback_key'],
        feedback=dict(event_id=feedback['event']['event_id'], actor=feedback['event']['actor'],
            source_sha256=feedback['event']['source_sha256'], text_sha256=text_sha(feedback['event']['text']),
            inbox=feedback['inbox'], request=feedback['first_request']),
        child_records=[], observer_assessment=annotation['assessment'], method='Source-bound observer semantic adjudication; not an optimizer or causal-retention proof.',
        reminders=None, parent_supplied_solution=annotation.get('parent_supplied_solution', 'unknown'),
        cross_task_transfer='not_demonstrated', context_exposure_at_transfer=None)
    result['observed_following_child_records'] = [dict(response=ref(frame['response']),
        request=ref(frame['request']), stage=frame['stage']) for frame in ordered
        if frame['request']['index'] >= feedback['first_request']['index']][:3]
    previous = feedback['first_request']['index']
    for number, key in enumerate(('identifies', 'applies_next_act', 'transfers'), 1):
        step = annotation.get(key)
        if step is None or step.get('substantive_correct') is not True:
            break
        frame = by_index.get(step['index'])
        if frame is None or frame['response']['index'] <= previous:
            raise ValueError('ordered_distinct_actual_child_records')
        if number > 1 and frame['stage'] != 'ACT':
            raise ValueError('application_must_be_ACT')
        if number == 2:
            next_act = next((item for item in ordered if item['stage'] == 'ACT' and item['response']['index'] > previous), None)
            if next_act is not frame:
                raise ValueError('must_be_the_NEXT_ACT_not_later_cherry_pick')
        if number == 3:
            if step.get('another_relevant_attempt') is not True:
                break
            first_context = {exposure_id(event) for event in by_index[previous]['request']['external']}
            new_context = {}
            for middle in ordered:
                if previous < middle['response']['index'] <= frame['response']['index']:
                    for event in middle['request']['external']:
                        identity = exposure_id(event)
                        if identity not in first_context:
                            new_context[identity] = event
            decisions = annotation.get('intervening_context', {})
            unresolved = {identity for identity in new_context if identity not in decisions or
                type(decisions[identity].get('reminder')) is not bool or
                type(decisions[identity].get('supplies_solution')) is not bool}
            reminders = sum(decisions.get(identity, {}).get('reminder') is True for identity in new_context)
            result['reminders'] = reminders
            result['intervening_external_count'] = len(new_context)
            result['unclassified_intervening_context'] = len(unresolved)
            result['context_exposure_at_transfer'] = annotation['feedback_key'] in {exposure_id(event) for event in frame['request']['external']}
            result['intervening_parent_solution'] = any(decisions.get(identity, {}).get('supplies_solution') is True for identity in new_context)
            if unresolved or reminders or result['intervening_parent_solution']:
                break
            if step.get('different_task') is True:
                result['cross_task_transfer'] = 'observer_identified_different_relevant_task'
        result['child_records'].append(validate_span(frame, step))
        result['level'] = number
        previous = frame['response']['index']
    if result['level'] == 3:
        last = result['child_records'][-1]['record']['index']
        complete = next((row for row in evidence['records'] if row['kind'] == 'SLEEP_COMPLETE' and row['index'] > last and row['status'] == 'COMPLETE'), None)
        result['checkpoint_pending'] = complete is None
        result['first_following_complete'] = ref(complete) if complete else None
        result['sleep_survival'] = result['child_records'][-1]['cycle'] - result['child_records'][1]['cycle']
    return result


def report(evidence, label, annotations=()):
    actual = frames(evidence)
    possible = candidates(evidence)
    traces, rejected = [], []
    for annotation in annotations:
        try:
            traces.append(adjudicate(evidence, annotation))
        except (ValueError, KeyError, StopIteration) as error:
            rejected.append(dict(annotation_sha256=text_sha(str(annotation)), reason=type(error).__name__ + ':' + str(error)))
    return dict(label=label, journal_id=evidence['journal_id'], observed_unix=evidence['observed_unix'],
        coverage_start=evidence['coverage_start'], coverage_end=evidence['through']['index'], caught_up=evidence['caught_up'],
        actual_committed_outputs=len(actual), actual_ACTs=sum(frame['stage'] == 'ACT' for frame in actual),
        external_feedback_candidates=len(possible), reviewed_corrections=len(traces),
        highest_verified_level=max((trace['level'] for trace in traces), default=None),
        status='REVIEWED_PARTIAL' if traces else 'SEMANTIC_REVIEW_PENDING_NOT_A_LEVEL0_FAILURE',
        traces=traces, rejected_annotations=rejected,
        level_counts={str(level): sum(trace['level'] == level for trace in traces) for level in range(4)},
        confirmed_reminders=sum(trace['reminders'] or 0 for trace in traces),
        reminder_count_unknown=sum(trace['reminders'] is None for trace in traces),
        cross_task_transfers=sum(trace['cross_task_transfer'] == 'observer_identified_different_relevant_task' for trace in traces),
        unknown_candidates=max(0, len(possible) - len({trace['correction_key'] for trace in traces})),
        lifetime_absence_claim=False, model_calls=0, learner_controls=0)
