"""Audit actual captured reader text; select existing source rows, never new facts.

The caller authenticates files and actors. Public route content is replayed here.
Incomplete routes rejected by the shared replay contract are not reconstructed.
"""

from copy import deepcopy
from hashlib import sha256

from organism_v6 import experienced_event_corrective_replay as corrective
from organism_v6 import experienced_event_microloop as micro
from organism_v6 import experienced_event_reader_audit_lesson as lesson


SCHEMA = 'DEV_ACTUAL_READER_AUDIT_SELECTION_V1'
MAX_CALLS = 8
MAX_CONTEXT = lesson.MAX_CONTEXT
MAX_NEW_TOKENS = lesson.MAX_NEW_TOKENS
SYSTEM = lesson.SYSTEM
SKIN = lesson.HELD_SKINS[0]
document_sha256 = lesson.document_sha256
require = micro._require


def _seal(value, key):
    return dict(value, **{key: document_sha256(value)})


def build_cases(collection, route_records):
    """Return a sealed bundle of all actual memory invocations, in trace order."""
    replayed = corrective.prepare_cases(collection, route_records)
    sources = deepcopy(replayed['sources'])
    table = ''.join(entry['canonical'] for entry in sources)
    cases = []
    for episode_index, record in enumerate(route_records):
        episode = record['episode']
        read_index = 0
        for trace_index, trace in enumerate(episode['traces']):
            if trace['kind'] != 'memory':
                continue
            require(len(cases) < MAX_CALLS, 'actual_reader_call_cap')
            address, response = trace['address'], trace['response']
            matches = [entry for entry in sources if entry['event'] == address]
            require(len(matches) == 1, 'queried_address_must_have_own_source')
            raw = response['raw']
            try:
                canonical = micro.canonical_event(raw)
            except ValueError:
                canonical = None
            mismatch = canonical != matches[0]['canonical']
            user = (SKIN + '\nREQUESTED EVENT: ' + address + '\nRECEIPT-GROUNDED SOURCE TABLE\n'
                    + table + 'UNTRUSTED READER REPLY\n' + raw)
            case = dict(case_index=len(cases), episode_index=episode_index, read_index=read_index,
                trace_index=trace_index, address=address, reader_raw=raw,
                reader_terminal=response['terminal'], reader_truncated=response['truncated'],
                kind='fault' if mismatch else 'true', expected=address if mismatch else 'NONE',
                stimulus_origin='ACTUAL_CAPTURED_READER_RESPONSE_NOT_VERIFIED_EXPERIENCE',
                transcript_sha256=document_sha256(episode['messages']),
                episode_sha256=document_sha256(record), trace_sha256=document_sha256(trace),
                response_sha256=document_sha256(response), reader_raw_sha256=sha256(raw.encode('utf-8')).hexdigest(),
                messages=[dict(role='system', content=SYSTEM), dict(role='user', content=user)])
            cases.append(_seal(case, 'case_sha256'))
            read_index += 1
        require(read_index == episode['memory_calls'], 'actual_reader_count_drift')
    return _seal(dict(schema=SCHEMA, fits=0, collection=deepcopy(collection),
        route_records=deepcopy(route_records), source_document_sha256=replayed['source_document_sha256'],
        sources=sources, cases=cases, expected_calls=len(cases), task_denominator=4), 'cases_sha256')


def _score(case, capture, sources):
    response = capture['response']
    if capture['error'] is not None:
        return False, None, 'CALL_ERROR'
    if (type(response) is not dict or type(response.get('raw')) is not str
            or type(response.get('terminal')) is not bool or type(response.get('truncated')) is not bool):
        return False, None, 'MALFORMED_RESPONSE'
    if 'messages' in response and response['messages'] != capture['messages']:
        return False, None, 'RESPONSE_PROMPT_DRIFT'
    if not response['terminal'] or response['truncated']:
        return False, None, 'NONTERMINAL_OR_TRUNCATED'
    raw = response['raw']
    correct = raw in (case['expected'], case['expected'] + '\n')
    if raw in ('NONE', 'NONE\n'):
        return correct, None, 'NONE'
    matches = [entry['source_index'] for entry in sources if raw in (entry['event'], entry['event'] + '\n')]
    if len(matches) == 1:
        return correct, matches[0], 'SOURCED_POINTER_NOT_UTILITY'
    return False, None, 'INVALID_POINTER'


def collect_cases(cases, generate):
    """One classifier call per actual read, with independent source-only admission."""
    require(type(cases) is dict and callable(generate), 'case_bundle_and_callback_required')
    require(document_sha256(cases) == document_sha256(build_cases(cases['collection'], cases['route_records'])),
            'actual_reader_case_source_drift')
    cases = deepcopy(cases)
    captures, selected, row_indexes, origins = [], [], [], []
    summary = {kind: dict(correct=0, denominator=0) for kind in ('overall', 'true', 'fault')}
    for case in cases['cases']:
        response = error = None
        try:
            response = deepcopy(generate(deepcopy(case['messages'])))
        except Exception as failure:
            error = dict(type=type(failure).__name__, message=str(failure))
        capture = dict(call_index=len(captures), case_sha256=case['case_sha256'],
                       messages=deepcopy(case['messages']), response=response, error=error)
        correct, source_index, status = _score(case, capture, cases['sources'])
        capture.update(correct=correct, admitted=source_index is not None, source_index=source_index, status=status)
        capture = _seal(capture, 'call_sha256')
        captures.append(capture)
        selected.append(source_index)
        for kind in ('overall', case['kind']):
            summary[kind]['denominator'] += 1
            summary[kind]['correct'] += int(correct)
        if source_index is not None:
            entry = cases['sources'][source_index]
            for source_row_index in entry['row_source_indexes']:
                row_indexes.append(source_row_index)
                origins.append(dict(call_index=capture['call_index'], case_sha256=case['case_sha256'],
                    call_sha256=capture['call_sha256'], episode_index=case['episode_index'],
                    trace_index=case['trace_index'], source_index=source_index, source_row_index=source_row_index,
                    source_raw_sha256=entry['source_raw_sha256'], event=entry['event'],
                    mapping='EXISTING_OWN_EVENT_QUERY_ROW_NOT_NEW_CHILD_CONTENT'))
    return _seal(dict(schema=SCHEMA, status='ACTUAL_READER_AUDIT_CAPTURED_NO_FIT', fits=0, parent_present=False,
        source_document_sha256=cases['source_document_sha256'], cases_sha256=cases['cases_sha256'],
        cases=cases['cases'], sources=cases['sources'], captures=captures,
        chosen_source_indexes=selected, admitted_selections=sum(index is not None for index in selected),
        row_source_indexes=row_indexes, material_origins=origins, model_calls=len(captures),
        expected_calls=cases['expected_calls'], task_denominator=4, summary=summary,
        correct=summary['overall']['correct'], denominator=summary['overall']['denominator'],
        claim='PUBLIC_ACTUAL_READER_CLASSIFICATION_AND_SOURCE_POINTER_NOT_GOAL_UTILITY_OR_NEW_EXPERIENCE'),
        'audit_sha256')
