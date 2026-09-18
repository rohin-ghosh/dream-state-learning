"""Read-only, transcript-free heuristic work metrics, never training decisions."""

import argparse
import ast
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re


SCHEMA = 'R227_INTENTION_ACT_AUDIT_V1'
INTENTION = re.compile(r'\b(?:I|we)\s+(?:will|shall|plan to|intend to|aim to|am ready to|are ready to)\b', re.I)
CALCULATION = re.compile(r'\b\d+(?:\.\d+)?\s*[+*/−-]\s*\d+(?:\.\d+)?\s*=\s*[-+]?\d')
NARRATIVE = re.compile(r'\b(?:was|were|walked|found|heard|saw|said|asked|opened|stepped|looked|felt|stood)\b', re.I)
HASH = re.compile(r'[0-9a-f]{64}')
ACT_CLASSES = ('INTENTION_ONLY_HEURISTIC', 'QUESTION_OBSERVED', 'WORK_SURFACE_OBSERVED', 'UNKNOWN')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def reference(event):
    return {'index': event['record_index'], 'sha256': event['record_sha256']}


def utc(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat() if timestamp is not None else None


def text_features(text):
    prose, blocks, current = [], [], []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
                current = []
            elif marker.group(1)[0] == fence:
                blocks.append('\n'.join(current))
                fence = None
            continue
        if fence is None:
            prose.append(line)
        else:
            current.append(line)
    outside = '\n'.join(prose)
    narrative_parts = [part for part in re.split(r'\n\s*\n', outside) if len(part.split()) >= 8]
    literal_parts = []
    numeric_code = False
    for block in blocks:
        try:
            tree = ast.parse(block)
        except (SyntaxError, ValueError, RecursionError):
            continue
        numeric_code |= any(isinstance(node, ast.BinOp) and any(
            isinstance(child, ast.Constant) and type(child.value) in (int, float)
            for child in ast.walk(node)) for node in ast.walk(tree))
        literal_parts.extend(node.value for node in ast.walk(tree)
                             if isinstance(node, ast.Constant) and isinstance(node.value, str))
    byte_paragraphs = sum(bool(re.search(r'\bByte\b', part) and NARRATIVE.search(part)
                               and len(part.split()) >= 12)
                          for part in narrative_parts + literal_parts)
    calculation = bool(CALCULATION.search(outside) or numeric_code)
    return dict(intention_cue=bool(INTENTION.search(outside)),
                question_candidate=any('?' in line for line in prose),
                code_blocks=len(blocks), unterminated_fence=fence is not None,
                numeric_calculation_candidate=calculation,
                byte_story_paragraph_candidates=byte_paragraphs,
                three_paragraph_shape=len(narrative_parts) == 3,
                math_or_byte_surface_candidate=calculation or byte_paragraphs > 0,
                math_object_cue=bool(re.search(r'\b(?:math|graph|vertices|subset|equation|calculate)\b', text, re.I)),
                byte_object_cue=bool(re.search(r'\bByte\b', text)),
                fulfillment_uncertain=True)


def intention_act_classification(text):
    """Conservative output-form metric; never eligibility or a failure score."""
    if len(text) > 65536:
        return dict(classification='UNKNOWN', reason='scan_bound_exceeded')
    features = text_features(text)
    if features['question_candidate'] or '？' in re.sub(r'```[\s\S]*?```|~~~[\s\S]*?~~~', '', text):
        return dict(classification='QUESTION_OBSERVED', reason='question_retained_not_a_failure')
    if features['unterminated_fence']:
        return dict(classification='UNKNOWN', reason='unfinished_code_fence')
    if features['math_or_byte_surface_candidate']:
        return dict(classification='WORK_SURFACE_OBSERVED', reason='math_or_narrative_surface_not_correctness')
    if re.search(r'\b(?:subset|set)\b', text, re.I) and re.search(r'\{[^{}\n]{1,160}\}', text):
        return dict(classification='WORK_SURFACE_OBSERVED', reason='explicit_set_answer_not_correctness')
    blocks = re.findall(r'```[^\n]*\n([\s\S]*?)```|~~~[^\n]*\n([\s\S]*?)~~~', text)
    literals = []
    for alternatives in blocks:
        block = next((value for value in alternatives if value), '')
        try:
            statements = ast.parse(block).body
        except (SyntaxError, ValueError, RecursionError):
            return dict(classification='UNKNOWN', reason='code_form_uncertain')
        for statement in statements:
            if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                    and isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'print'
                    and statement.value.args and not statement.value.keywords
                    and all(isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                            for argument in statement.value.args)):
                return dict(classification='WORK_SURFACE_OBSERVED', reason='nonliteral_code_emitted_not_execution')
            literals.extend(argument.value for argument in statement.value.args)
    outside = re.sub(r'```[\s\S]*?```|~~~[\s\S]*?~~~', '', text)
    material = '\n'.join([outside] + literals)
    if re.search(r'(?:^|\n|[\"“])\s*(?:We (?:propose|present|demonstrate)|Once upon a time)\b', material, re.I) and len(material.split()) >= 25:
        return dict(classification='WORK_SURFACE_OBSERVED', reason='literal_draft_present_not_truth_or_quality')
    if re.search(r'[\u3400-\u9fff]', material):
        return dict(classification='UNKNOWN', reason='english_intention_heuristic_not_applicable')
    units = [unit.strip() for unit in re.split(r'\n+|(?<=[.!])\s+', material) if unit.strip()]
    prospective = False
    recognized = 0
    for unit in units:
        unit = re.sub(r'^(?:Intentions?|Continue thinking|Ready to act)\s*:\s*', '', unit, flags=re.I)
        unit = re.sub(r'^Now,?\s*', '', unit, flags=re.I)
        future = re.match(r'^(?:I|we)\s+(?:will|shall|plan to|intend to|aim to|need to|am ready to|are ready to)\b', unit, re.I)
        if future:
            prospective = True
            recognized += 1
            continue
        status = bool(re.match(r'^(?:I|we)\s+have\s+(?:printed|written|calculated|verified)\b', unit, re.I)
                      or re.match(r'^The resulting (?:abstract|report|answer)\s+(?:meets|satisfies)\b', unit, re.I)
                      or re.match(r'^Forced myself to\b', unit, re.I))
        anticipatory_state = bool(re.match(r'^Comprehended that\b', unit, re.I)
                                  and re.search(r'\b(?:might|could|can|may)\b', unit, re.I))
        if status or anticipatory_state:
            recognized += 1
    if prospective and units and recognized == len(units):
        return dict(classification='INTENTION_ONLY_HEURISTIC',
                    reason='only_future_action_plus_bounded_unverified_status_scaffolding', unit_count=len(units))
    return dict(classification='UNKNOWN', reason='content_mixed_or_insufficiently_characterized')


def normalize(evidence):
    events = {}
    for event in evidence['events']:
        index = event['record_index']
        if type(index) is not int or not HASH.fullmatch(event['record_sha256']):
            raise ValueError('invalid_record_identity')
        if event.get('envelope_verified') is not True:
            raise ValueError('unverified_event_projection')
        if index in events and events[index] != event:
            raise ValueError('conflicting_record_identity')
        events[index] = event
    return sorted(events.values(), key=lambda event: event['record_index'])


def work_windows(evidence, events):
    anchor = evidence['anchor']
    completes = {anchor['cycle']: anchor['index']}
    complete_refs = {}
    requests = {}
    for event in events:
        if event['kind'] not in ('SLEEP_REQUEST', 'SLEEP_COMPLETE'):
            continue
        cycle = event['document']['cycle']
        destination = requests if event['kind'] == 'SLEEP_REQUEST' else complete_refs
        if cycle in destination:
            raise ValueError('ambiguous_repeated_sleep_cycle')
        destination[cycle] = event
        if event['kind'] == 'SLEEP_COMPLETE':
            completes[cycle] = event['record_index']
    windows = []
    for cycle, event in sorted(requests.items()):
        if cycle - 1 not in completes:
            raise ValueError('missing_preceding_cycle_boundary')
        windows.append(dict(cycle=cycle, lower=completes[cycle - 1], upper=event['record_index'],
                            sleep_request=reference(event),
                            complete=reference(complete_refs[cycle]) if cycle in complete_refs else None,
                            status='COMPLETE' if cycle in complete_refs else 'SLEEP_PENDING'))
    latest = max(completes)
    if latest + 1 not in requests:
        windows.append(dict(cycle=latest + 1, lower=completes[latest], upper=evidence['head']['index'] + 1,
                            sleep_request=None, complete=None, status='OPEN'))
    return windows


def analyze(evidence, label='C2'):
    if label not in ('C2', 'P7', 'SYNTHETIC'):
        raise ValueError('public_label_not_allowed')
    head = evidence['head']
    if type(head['index']) is not int or not HASH.fullmatch(head['sha256']):
        raise ValueError('invalid_head_identity')
    events = normalize(evidence)
    windows = work_windows(evidence, events)
    grouped = collections.defaultdict(list)
    for event in events:
        grouped[event['kind']].append(event)
    issues, rows, bound = [], [], {}

    def issue(reason, event):
        issues.append(dict(reason=reason, record=reference(event)))

    for stage in grouped['R184_STAGE']:
        document = stage['document']
        if document.get('stage') not in ('THINK', 'ACT', 'LEARN'):
            issue('unknown_stage', stage)
            continue
        source = document.get('source_sha256')
        responses = [event for event in grouped['RESPONSE'] if event.get('source_sha256') == source]
        commits = [event for event in grouped['COMMITTED'] if event.get('source_sha256') == source]
        if len(responses) != 1 or len(commits) != 1:
            issue('missing_or_ambiguous_committed_source', stage)
            continue
        response, commit = responses[0], commits[0]
        raw = response['document']['response']['raw']
        request_hash = response['document']['request_sha256']
        requests = [event for event in grouped['REQUEST'] if digest({key: value for key, value in event['document'].items()
                    if key != 'resume_state'}) == request_hash]
        if len(requests) != 1:
            issue('missing_or_ambiguous_request_identity', stage)
            continue
        request = requests[0]
        segment = document['segment']
        valid = (type(segment) is int and digest(response['document']) == source and commit.get('committed_row_verified') is True
                 and commit['target_sha256'] == text_hash(raw)
                 and segment == commit['segment'] == request['document']['segment']
                 and request['record_index'] < response['record_index'] < commit['record_index'] < stage['record_index'])
        matching = [window for window in windows if window['lower'] < request['record_index']
                    < response['record_index'] < stage['record_index'] < window['upper']]
        if not valid or len(matching) != 1:
            issue('candidate_or_cycle_identity_mismatch', stage)
            continue
        if source in bound:
            issue('duplicate_stage_for_source', stage)
            continue
        console = any(event['document'].get('source_sha256') == source
                      and event['document'].get('segment') == segment for event in grouped['R205_CONSOLE_REPLY'])
        row = dict(cycle=matching[0]['cycle'], stage=document['stage'], segment=segment,
                   source_sha256=source, target_sha256=text_hash(raw),
                   request=reference(request), response=reference(response), commit=reference(commit),
                   stage_record=reference(stage), finished_utc=utc(response['document'].get('finished_unix')),
                   console_reply=console, features=text_features(raw),
                   act_form=intention_act_classification(raw) if document['stage'] == 'ACT' else None,
                   pairing='CONSOLE_REPLY_SEPARATE' if console else 'UNPAIRED_AT_CUT' if document['stage'] in ('THINK', 'ACT') else 'NOT_APPLICABLE',
                   execution='NO_BOUND_EXECUTION_RECEIPT', execution_receipt=None,
                   result_sha256=None, artifact_link_present=False)
        if row['stage'] == 'ACT' and not console:
            outcomes = [event for event in grouped['R184_ACT'] if event['document'].get('source_sha256') == source]
            if len(outcomes) == 1:
                outcome_event = outcomes[0]
                action = outcome_event['document']
                origin = action.get('origin', {})
                if (action.get('segment') == segment and origin.get('record_index') == response['record_index']
                        and origin.get('record_sha256') == response['record_sha256']
                        and stage['record_index'] < outcome_event['record_index'] < matching[0]['upper']):
                    outcome = action.get('outcome', {})
                    executed = outcome.get('executed')
                    row['execution'] = ('EXECUTION_RECORDED' if executed is True else
                                        'NOT_EXECUTED_RECORDED' if executed is False else 'EXECUTION_UNKNOWN')
                    row['execution_receipt'] = reference(outcome_event)
                    result_sha = outcome.get('result_sha256')
                    row['result_sha256'] = result_sha if isinstance(result_sha, str) and HASH.fullmatch(result_sha) else None
                    row['artifact_link_present'] = bool(outcome.get('artifact_link'))
                else:
                    issue('execution_origin_mismatch', outcome_event)
            elif len(outcomes) > 1:
                issue('ambiguous_execution_receipt', stage)
        rows.append(row)
        bound[source] = (row, stage, request)

    pairs = []
    for transition in grouped['R184_TRANSITION']:
        document = transition['document']
        if document.get('from_stage') != 'THINK' or document.get('to_stage') != 'ACT':
            continue
        endings = [entry for entry in bound.values() if entry[0]['stage'] == 'THINK'
                   and entry[0]['segment'] == document.get('segment')
                   and entry[0]['stage_record']['index'] < transition['record_index']]
        if len(endings) != 1:
            issue('transition_think_identity_uncertain', transition)
            continue
        ending, stage, request = endings[0]
        window = next(window for window in windows if window['cycle'] == ending['cycle'])
        next_boundary = min([event['record_index'] for event in grouped['R184_TRANSITION']
                             if transition['record_index'] < event['record_index'] < window['upper']] + [window['upper']])
        actions = [entry for entry in bound.values() if entry[0]['stage'] == 'ACT'
                   and not entry[0]['console_reply'] and entry[0]['cycle'] == ending['cycle']
                   and transition['record_index'] < entry[0]['request']['index']
                   < entry[0]['stage_record']['index'] < next_boundary
                   and entry[1]['document'].get('trial_id') == stage['document'].get('trial_id')]
        preceding = max([event['record_index'] for event in grouped['R184_TRANSITION']
                         if window['lower'] < event['record_index'] < transition['record_index']] + [window['lower']])
        thinks = [entry[0] for entry in bound.values() if entry[0]['stage'] == 'THINK'
                  and entry[0]['cycle'] == ending['cycle']
                  and preceding < entry[0]['stage_record']['index'] <= ending['stage_record']['index']
                  and entry[1]['document'].get('trial_id') == stage['document'].get('trial_id')]
        count_matches = document.get('think_segments_used') == len(thinks)
        if len(actions) == 1 and count_matches:
            for row in thinks + [actions[0][0]]:
                row['pairing'] = 'TRANSITION_BOUND'
            pairs.append(dict(cycle=ending['cycle'], transition=reference(transition),
                              think_source_sha256=[row['source_sha256'] for row in thinks],
                              think_segments=[row['segment'] for row in thinks],
                              act_source_sha256=actions[0][0]['source_sha256'], act_segment=actions[0][0]['segment'],
                              semantic_alignment='UNCERTAIN_NOT_SCORED'))
        elif not actions and window['status'] == 'OPEN':
            issue('act_pending_at_observation_cut', transition)
        else:
            issue('transition_action_or_think_count_uncertain', transition)

    parent_delivery = []
    for event in grouped['INBOX']:
        message = event['document'].get('message', {})
        if message.get('actor') != 'parent' or not isinstance(message.get('text'), str) or not message['text']:
            continue
        text = message['text']
        rendered = []
        for row, stage, request in bound.values():
            if request['record_index'] <= event['record_index']:
                continue
            positions = [position for position, item in enumerate(request['document'].get('messages', []))
                         if item.get('role') != 'assistant' and isinstance(item.get('content'), str)
                         and text in item['content']]
            if positions:
                rendered.append(dict(request=row['request'], response=row['response'], segment=row['segment'],
                                     stage=row['stage'], message_positions=positions))
        features = text_features(text)
        parent_delivery.append(dict(inbox=reference(event), text_sha256=text_hash(text),
                                    math_object_cue=features['math_object_cue'], byte_object_cue=features['byte_object_cue'],
                                    exact_rendered_to_committed_response=rendered,
                                    semantic_uptake='UNCERTAIN_NOT_INFERRED_FROM_RENDERING'))

    summaries = []
    for window in windows:
        selected = [row for row in rows if row['cycle'] == window['cycle']]
        thinks = [row for row in selected if row['stage'] == 'THINK']
        acts = [row for row in selected if row['stage'] == 'ACT' and not row['console_reply']]
        if not selected and window['status'] == 'OPEN':
            continue
        summaries.append(dict(cycle=window['cycle'], status=window['status'], sleep_request=window['sleep_request'],
                              complete=window['complete'], think_responses=len(thinks),
                              think_intention_cues=sum(row['features']['intention_cue'] for row in thinks),
                              act_responses=len(acts), console_act_responses=sum(row['console_reply'] for row in selected),
                              act_intention_cues=sum(row['features']['intention_cue'] for row in acts),
                              act_form_counts={name: sum(row['act_form']['classification'] == name for row in acts)
                                               for name in ACT_CLASSES},
                              act_math_or_byte_surface_candidates=sum(row['features']['math_or_byte_surface_candidate'] for row in acts),
                              act_questions=sum(row['features']['question_candidate'] for row in acts),
                              act_code_submissions=sum(row['features']['code_blocks'] > 0 for row in acts),
                              executions_recorded=sum(row['execution'] == 'EXECUTION_RECORDED' for row in acts),
                              not_executed_receipts=sum(row['execution'] == 'NOT_EXECUTED_RECORDED' for row in acts),
                              executions_unknown=sum(row['execution'] in ('EXECUTION_UNKNOWN', 'NO_BOUND_EXECUTION_RECEIPT') for row in acts),
                              artifact_link_receipts=sum(row['artifact_link_present'] for row in acts),
                              task_fulfillment_uncertain=len(acts),
                              unpaired_acts=sum(row['pairing'] == 'UNPAIRED_AT_CUT' for row in acts),
                              paired_opportunities=sum(pair['cycle'] == window['cycle'] for pair in pairs)))
    return dict(schema=SCHEMA, label=label, metric_kind='HEURISTIC_DESCRIPTIVE_NOT_A_FILTER',
                observed_utc=utc(evidence.get('observed_unix')), head=dict(index=head['index'], sha256=head['sha256']),
                input_sha256=digest(evidence), rows=rows, pairs=pairs, cycles=summaries,
                parent_delivery=parent_delivery, uncertainties=issues,
                private_transcripts_included=False, semantic_exclusions=False,
                questions_are_failures=False, correctness_or_causality_claimed=False,
                learner_or_parent_changes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--label', choices=('C2', 'P7', 'SYNTHETIC'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    payload = arguments.evidence.read_bytes()
    report = analyze(json.loads(payload), arguments.label)
    report['input_file_sha256'] = hashlib.sha256(payload).hexdigest()
    report['audit_module_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with arguments.output.open('x') as destination:
        json.dump(report, destination, sort_keys=True, indent=2)
        destination.write('\n')
    print(json.dumps(dict(label=report['label'], observed_utc=report['observed_utc'],
                          cycles=report['cycles'], uncertainty_count=len(report['uncertainties'])), indent=2))


if __name__ == '__main__':
    main()
