"""Public reader-audit lessons over stored records and explicit synthetic faults.

Pure rendering/admission, not experience authentication or autonomous extraction.
The caller authenticates the original records and the actor generating responses.
"""

from copy import deepcopy
from hashlib import sha256
import json

from gpu import astra_pchain2_native as native
from organism_v6 import experienced_event_microloop as micro


SCHEMA = 'DEV_EXPERIENCED_READER_AUDIT_LESSON_V1'
DEV = 'DEV'
HELD = 'HELD'
MAX_CONTEXT = 2048
MAX_NEW_TOKENS = 160
DEV_CASE_COUNT = 64
HELD_CASE_COUNT = 16
MAX_ROWS = DEV_CASE_COUNT
TARGET_EOT = '<|im_end|>'
LOSS_POLICY = dict(prefix='MASK_ALL', assistant='TRAIN', eot='TRAIN')
SYSTEM = ('Compare the untrusted reader reply with the receipt-grounded source record for the requested '
          'EVENT address. If any EVENT/AT/DID/GOT/EVIDENCE field differs, return only the requested '
          'bare E_id. If every field matches, return NONE. No other text.')
PARENT_GUIDANCE = ('PARENT PROCEDURAL GUIDANCE: Locate the requested EVENT in the source table. '
                   'Compare every field of the reply with that record, including EVIDENCE. '
                   'A plausible reply or a matching address alone is not enough. If any field differs, '
                   'answer with the requested bare address; otherwise answer NONE. Do not output an EVENT line.')
DEV_SKINS = ('Audit this reader reply.', 'Check the returned memory record.',
             'Inspect this memory lookup.', 'Verify the reader against the source table.')
HELD_SKINS = ('Assess this retrieved entry.', 'Does the returned tuple agree with the stored record?')
require = micro._require


def document_sha256(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                             separators=(',', ':')).encode('ascii')).hexdigest()


def _seal(value, key):
    return dict(value, **{key: document_sha256(value)})


def _same(actual, expected, reason):
    require(document_sha256(actual) == document_sha256(expected), reason)


def build_cases(events, split):
    """Return a sealed bundle; four contiguous records define each source bank."""
    require(split in (DEV, HELD), 'DEV_or_HELD_required')
    require(type(events) is list and len(events) == (8 if split == DEV else 4), 'exact_split_event_count_required')
    sources = deepcopy(events)
    canonical = []
    for entry in sources:
        require(type(entry) is dict and set(entry) == {'event', 'raw'}, 'only_event_and_original_raw_required')
        text = micro.canonical_event(entry['raw'])
        require(micro.parse_event_line(text)['event'] == entry['event'], 'source_address_mismatch')
        canonical.append(text)
    require(len({entry['event'] for entry in sources}) == len(sources), 'distinct_source_addresses_required')
    source_hash = document_sha256(sources)
    table = ''.join(canonical)
    cases = []
    skins = DEV_SKINS if split == DEV else HELD_SKINS
    for skin_index, skin in enumerate(skins):
        for event_index, entry in enumerate(sources):
            donor_index = event_index // 4 * 4 + (event_index + 1) % 4
            donor_body = canonical[donor_index].split(' AT ', 1)[1]
            fault = 'EVENT ' + entry['event'] + ' AT ' + donor_body
            require(fault != canonical[event_index], 'fault_must_change_full_tuple')
            for kind, reply in (('true', canonical[event_index]), ('fault', fault)):
                user = (skin + '\nREQUESTED EVENT: ' + entry['event'] + '\nRECEIPT-GROUNDED SOURCE TABLE\n'
                        + table + 'UNTRUSTED READER REPLY\n' + reply)
                mismatch = micro.parse_event_line(reply) != micro.parse_event_line(canonical[event_index])
                case = dict(case_index=len(cases), split=split, skin_index=skin_index,
                    event_index=event_index, event=entry['event'], kind=kind, reader_reply=reply,
                    expected=entry['event'] if mismatch else 'NONE', source_sha256=source_hash,
                    stimulus=dict(origin='RESEARCHER_RENDERED_UNTRUSTED_REPLY', authentic_experience=False,
                        composite_fault=kind == 'fault', address_source_index=event_index,
                        body_source_index=donor_index if kind == 'fault' else event_index),
                    prefix=[dict(role='system', content=SYSTEM), dict(role='user', content=user)])
                cases.append(_seal(case, 'case_sha256'))
    return _seal(dict(schema=SCHEMA, split=split, events=sources, source_sha256=source_hash,
                      expected_calls=len(cases), cases=cases), 'cases_sha256')


def _messages(case, coached):
    messages = deepcopy(case['prefix'])
    if coached:
        messages[-1]['content'] += '\n\n' + PARENT_GUIDANCE
    return messages


def _success(case, capture):
    response = capture['response']
    if capture['error'] is not None:
        return False, 'CALL_ERROR'
    if (type(response) is not dict or type(response.get('raw')) is not str
            or type(response.get('terminal')) is not bool or type(response.get('truncated')) is not bool):
        return False, 'MALFORMED_RESPONSE'
    if 'messages' in response and response['messages'] != capture['messages']:
        return False, 'RESPONSE_PROMPT_DRIFT'
    if not response['terminal'] or response['truncated']:
        return False, 'NONTERMINAL_OR_TRUNCATED'
    if response['raw'] not in (case['expected'], case['expected'] + '\n'):
        return False, 'ABSTAINED_ON_FAULT' if response['raw'] in ('NONE', 'NONE\n') else 'WRONG_OUTPUT'
    return True, None


def _row(events, case, capture, coached):
    return _seal(dict(schema=SCHEMA, split=DEV, events=deepcopy(events), case=deepcopy(case),
        capture=deepcopy(capture), coached=coached, prefix=deepcopy(case['prefix']),
        assistant=capture['response']['raw'], target_eot=TARGET_EOT, loss_policy=deepcopy(LOSS_POLICY),
        source_sha256=document_sha256(events), case_sha256=case['case_sha256'],
        call_sha256=capture['call_sha256'], source_call_index=capture['call_index'],
        response_sha256=document_sha256(capture['response'])), 'row_sha256')


def collect_cases(cases, generate, coached):
    """Exactly one callback per case. All outcomes retained; only DEV successes train."""
    require(type(cases) is dict and callable(generate) and type(coached) is bool, 'case_bundle_callback_and_bool_required')
    _same(cases, build_cases(cases['events'], cases['split']), 'case_bundle_source_drift')
    require(cases['split'] == DEV or not coached, 'HELD_must_be_parent_free')
    cases = deepcopy(cases)
    captures, rows = [], []
    coverage = {entry['event']: dict(true_successes=0, fault_successes=0, true_calls=0, fault_calls=0)
                for entry in cases['events']}
    for case in cases['cases']:
        messages = _messages(case, coached)
        response = error = None
        try:
            response = deepcopy(generate(deepcopy(messages)))
        except Exception as failure:
            error = dict(type=type(failure).__name__, message=str(failure))
        capture = dict(call_index=len(captures), case_sha256=case['case_sha256'], messages=messages,
                       response=response, error=error)
        success, reason = _success(case, capture)
        capture.update(success=success, failure=reason)
        capture = _seal(capture, 'call_sha256')
        captures.append(capture)
        coverage[case['event']][case['kind'] + '_calls'] += 1
        if success:
            coverage[case['event']][case['kind'] + '_successes'] += 1
            if cases['split'] == DEV:
                rows.append(_row(cases['events'], case, capture, coached))
    covered = all(item['true_successes'] >= 1 and item['fault_successes'] >= 1 for item in coverage.values())
    summary = {'overall': dict(correct=sum(capture['success'] for capture in captures), denominator=len(captures))}
    for kind in ('true', 'fault'):
        summary[kind] = dict(correct=sum(item[kind + '_successes'] for item in coverage.values()),
                             denominator=sum(item[kind + '_calls'] for item in coverage.values()))
    return _seal(dict(schema=SCHEMA, split=cases['split'], status='COLLECTED_NO_FIT', fits=0,
        cases=deepcopy(cases['cases']), events=deepcopy(cases['events']), cases_sha256=cases['cases_sha256'],
        source_sha256=cases['source_sha256'], captures=captures, rows=rows, coverage=coverage,
        ready=cases['split'] == DEV and covered, coverage_complete=covered,
        model_calls=len(captures), expected_calls=cases['expected_calls'], parent_present=coached,
        successes=summary['overall']['correct'], summary=summary,
        claim='STORED_OWN_RECORDS_EXTERNAL_FAULT_TASK_NOT_AUTONOMOUS_EXTRACTION_OR_NEW_EXPERIENCE'), 'collection_sha256')


def _validate_row(row):
    require(type(row) is dict and row.get('schema') == SCHEMA and row.get('split') == DEV,
            'actual_DEV_row_required')
    bundle = build_cases(row['events'], DEV)
    index = row['case']['case_index']
    require(type(index) is int and 0 <= index < DEV_CASE_COUNT and type(row['coached']) is bool,
            'valid_row_case_required')
    case = bundle['cases'][index]
    _same(row['case'], case, 'row_source_case_drift')
    capture = deepcopy(row['capture'])
    digest = capture.pop('call_sha256')
    require(document_sha256(capture) == digest and capture['call_index'] == index
            and capture['case_sha256'] == case['case_sha256']
            and capture['messages'] == _messages(case, row['coached']), 'row_captured_call_drift')
    require(_success(case, capture) == (True, None) and capture.get('success') is True
            and capture.get('failure') is None, 'row_must_be_successful_actual_child_response')
    _same(row, _row(row['events'], case, row['capture'], row['coached']), 'row_target_or_provenance_drift')


def encode_rows(rows, tokenizer):
    """Mask the complete student prefix; supervise only actual response and EOT."""
    require(type(rows) in (list, tuple) and 0 < len(rows) <= MAX_ROWS, 'nonempty_bounded_DEV_rows_required')
    require(tokenizer.eos_token == TARGET_EOT and type(tokenizer.eos_token_id) is int
            and native._encode(tokenizer, TARGET_EOT) == (tokenizer.eos_token_id,), 'exact_lesson_eot_required')
    encoded = []
    for row in rows:
        _validate_row(row)
        messages = row['prefix'] + [dict(role='assistant', content=row['assistant'])]
        context = tokenizer.apply_chat_template(row['prefix'], tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + row['assistant'] + TARGET_EOT + '\n', 'exact_lesson_template_boundary_required')
        prefix_ids, target = native._encode(tokenizer, context), native._encode(tokenizer, row['assistant'])
        suffix = native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target), 'lesson_target_special_token_forbidden')
        supervised = target + (tokenizer.eos_token_id,)
        sequence = native._encode(tokenizer, full)
        require(sequence == prefix_ids + supervised + suffix and len(sequence) <= MAX_CONTEXT,
                'untruncated_exact_lesson_sequence_required')
        require(native._decode(tokenizer, sequence) == full
                and native._decode(tokenizer, supervised) == row['assistant'] + TARGET_EOT,
                'lesson_token_roundtrip_failed')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
            return_dict=False, truncation=False, padding=False)) == sequence, 'lesson_template_token_ids_mismatch')
        encoded.append(native.EncodedRow(sequence, (-100,) * len(prefix_ids) + supervised
                                       + (-100,) * len(suffix), supervised))
    return tuple(encoded)
