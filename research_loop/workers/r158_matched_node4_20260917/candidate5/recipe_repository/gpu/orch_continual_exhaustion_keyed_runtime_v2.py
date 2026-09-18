"""Unallocated prospective V2: host-bound legacy spans and independent R106 evidence."""

from copy import deepcopy
from pathlib import Path
import re

from gpu import orch_continual_exhaustion_keyed_runtime as transport


PROGRAM = 'gpu.orch_continual_exhaustion_keyed_runtime_v2'
SCHEMA = 'KEYED_LEGACY_LINE_EVIDENCE_R106_DEPARTURE_RETURN_V2'
BUILDER_AUTHORITY = 'R107_CURRENT_L1_SAME_BUDGET_TRANSPORT_ONLY_NO_MAIN_ACK'
KINDS = ('CHECK', 'JUDGMENT', 'WHAT_IF', 'ASSOCIATIVE_DEPARTURE', 'ALTERNATIVE_PATH')
PHASES = ('MID_SOLUTION', 'TERMINAL_CHECK_OR_ASIDE')
BASE_SCHEMA = transport.keyed.keyed_schema
BASE_NATIVE_PHASE = transport.native_phase
BASE_ALLOCATION = transport.validate_allocation
BASE_RESERVE = transport.old.reserve_budget
BASE_SCAN = transport.worker_scan
require, read, sha, write_once, digest = transport.require, transport.read, transport.sha, transport.write_once, transport.digest
INSTRUCTIONS = '''
PROSPECTIVE V2 SERIALIZATION AND R106 MEASUREMENT; old reviews cannot be reused.
Return row_key, not hashes. Read the full question, prefix and every source line.
Do not return has_meaningful_branch, branching_alternative or branch_rejection_reason.
Instead, explicitly author legacy_considered_and_rejected (boolean),
legacy_alternative_line_ids and legacy_rejection_line_ids. True requires both
nonempty evidence lists. False requires both lists empty. Do not force false
to get through validation: judge the legacy indicator honestly. The host alone
assembles literal legacy text from unchanged source lines. For noncontiguous
selected IDs it uses the exact inclusive source interval, retaining selected IDs.

R106 is SEPARATE: valid checks, judgments, what-ifs or associative departures
returning to main work can be branches without ANY rejected path or second method.
legacy_considered_and_rejected=false and positive r106.departures_and_returns is
valid. Never invent a rejected path to satisfy the legacy indicator.
For each R106 departure/return supply exact main_line_ids, departure_line_ids,
return_line_ids, kind and a specific reason. Source order must be main, departure,
then return (same-line evidence allowed; it does not establish intra-line order).
Author return_phase and return_to_main_computation: MID_SOLUTION means actual
resumed main computation, not merely a terminal Check, verification, conclusion
or FINAL. TERMINAL_CHECK_OR_ASIDE is reported separately and has false
return_to_main_computation. A check followed only by FINAL is not mid-solution.
Use UNKNOWN with an empty inventory if unable to measure; do not invent positives.

Worked-method counts remain in branch_metrics, separate from R106 departures.
Repeated checks/rearrangements are not automatically distinct solution methods.
r106.error and r106.coherence are separate descriptive evidence assessments;
repetition remains in existing branch_metrics. All existing quality axes, gold
verification and PASS/FAIL rules remain unchanged. No required branching count,
no >=2 method threshold, no voice/length gate, no target or numeric-answer repair.
Do not FAIL solely for a considered-and-rejected path; assess endorsed wrong claims.
Unsampled rows are UNREVIEWED with semantic measurements UNKNOWN.
Keep explanations concise within the unchanged8192-output-token cap, but read
all supplied full text and return all six rows. Never silently flip a claim.
'''


def response_schema(count):
    schema = BASE_SCHEMA(count)
    item = schema['properties']['reviews']['items']
    properties = item['properties']
    for name in ('has_meaningful_branch', 'branching_alternative', 'branch_rejection_reason'):
        del properties[name]
    ids = dict(type='array', items=dict(type='integer', minimum=1), uniqueItems=True)
    string = dict(type='string', minLength=1)

    def obj(fields):
        return dict(type='object', properties=fields, required=list(fields), additionalProperties=False)

    def assessment(statuses):
        return obj(dict(status=dict(type='string', enum=list(statuses)), evidence_line_ids=ids, reason=string))

    departure = obj(dict(main_line_ids=ids, departure_line_ids=ids, return_line_ids=ids,
        kind=dict(type='string', enum=list(KINDS)), return_phase=dict(type='string', enum=list(PHASES)),
        return_to_main_computation=dict(type='boolean'), reason=string))
    properties.update(legacy_considered_and_rejected=dict(type='boolean'),
        legacy_alternative_line_ids=ids, legacy_rejection_line_ids=ids,
        r106=obj(dict(measurement_status=dict(type='string', enum=['MEASURED', 'UNKNOWN']),
            departures_and_returns=dict(type='array', items=departure),
            error=assessment(('NO_ERROR_OBSERVED', 'ERROR_OBSERVED', 'UNKNOWN')),
            coherence=assessment(('COHERENT', 'INCOHERENT', 'UNKNOWN')))))
    item['required'] = list(properties)
    return schema


def line_selection(lines, identifiers, *, nonempty):
    require(isinstance(identifiers, list) and all(type(index) is int and index in lines for index in identifiers),
            'v2_exact_existing_source_line_ids')
    require(identifiers == sorted(set(identifiers)) and (identifiers or not nonempty),
            'v2_ordered_unique_nonempty_evidence')
    return [lines[index] for index in identifiers]


def literal_interval(lines, identifiers):
    line_selection(lines, identifiers, nonempty=True)
    return ''.join(lines[index] for index in range(identifiers[0], identifiers[-1] + 1))


def resolve_r106(value, lines):
    require(set(value) == {'measurement_status', 'departures_and_returns', 'error', 'coherence'}, 'v2_exact_r106_fields')
    require(value['measurement_status'] in ('MEASURED', 'UNKNOWN')
            and isinstance(value['departures_and_returns'], list), 'v2_r106_measurement_status')
    require(value['measurement_status'] != 'UNKNOWN' or not value['departures_and_returns'], 'unknown_r106_not_positive')
    resolved = deepcopy(value)
    identities = set()
    for item in resolved['departures_and_returns']:
        require(set(item) == {'main_line_ids', 'departure_line_ids', 'return_line_ids', 'kind', 'return_phase',
                             'return_to_main_computation', 'reason'}, 'v2_exact_departure_fields')
        require(item['kind'] in KINDS and item['return_phase'] in PHASES and isinstance(item['reason'], str)
                and item['reason'].strip(), 'v2_departure_kind_phase_and_reason')
        main, departure, resumed = (item[key] for key in ('main_line_ids', 'departure_line_ids', 'return_line_ids'))
        evidence = {key: line_selection(lines, item[key], nonempty=True)
                    for key in ('main_line_ids', 'departure_line_ids', 'return_line_ids')}
        require(max(main) <= min(departure) and max(departure) <= min(resumed), 'v2_main_departure_return_order')
        identity = (tuple(main), tuple(departure), tuple(resumed))
        require(identity not in identities, 'v2_duplicate_departure_evidence')
        identities.add(identity)
        midline = item['return_phase'] == 'MID_SOLUTION'
        require(type(item['return_to_main_computation']) is bool and item['return_to_main_computation'] == midline,
                'v2_explicit_return_phase_consistency')
        if midline:
            require(not all(re.match(r'^\s*FINAL\s*:', lines[index], re.IGNORECASE) for index in resumed),
                    'terminal_final_is_not_mid_solution')
        item['source_evidence_spans'] = evidence
        item['same_line_order_not_mechanically_proven'] = bool(set(main) & set(departure) or set(departure) & set(resumed))
    for name, statuses in (('error', ('NO_ERROR_OBSERVED', 'ERROR_OBSERVED', 'UNKNOWN')),
                           ('coherence', ('COHERENT', 'INCOHERENT', 'UNKNOWN'))):
        assessment = resolved[name]
        require(set(assessment) == {'status', 'evidence_line_ids', 'reason'} and assessment['status'] in statuses
                and isinstance(assessment['reason'], str) and assessment['reason'].strip(), 'v2_descriptive_assessment_shape')
        assessment['source_evidence_spans'] = line_selection(lines, assessment['evidence_line_ids'],
            nonempty=assessment['status'] in ('ERROR_OBSERVED', 'INCOHERENT'))
    measured = value['measurement_status'] == 'MEASURED'
    resolved['author_counts'] = dict(departures_and_returns=len(identities) if measured else None,
        mid_solution=sum(item['return_phase'] == 'MID_SOLUTION' for item in value['departures_and_returns']) if measured else None,
        terminal_check_or_aside=sum(item['return_phase'] == 'TERMINAL_CHECK_OR_ASIDE' for item in value['departures_and_returns']) if measured else None)
    return resolved


def validate_result(packet, result, expected_packet_sha256):
    require(digest(packet) == expected_packet_sha256, 'immutable_full_packet_mismatch')
    rows = transport.packet_rows(packet)
    reviews = deepcopy(result['reviews'])
    keys = [review.get('row_key') for review in reviews]
    require(all(type(key) is int for key in keys) and sorted(keys) == list(range(len(rows))), 'exact_unique_response_keys')
    for review in reviews:
        forbidden = set(transport.keyed.HASH_FIELDS) | {'has_meaningful_branch', 'branching_alternative', 'branch_rejection_reason'}
        require(not forbidden.intersection(review), 'v2_no_legacy_strings_hashes_or_rehydration')
        row = rows[review.pop('row_key')]
        lines = {line['line_id']: line['text'] for line in transport.old.policy.source_lines(row['target'])}
        indicator = review['legacy_considered_and_rejected']
        require(type(indicator) is bool, 'v2_explicit_author_legacy_boolean')
        alternative, rejection = review['legacy_alternative_line_ids'], review['legacy_rejection_line_ids']
        if indicator:
            alternative_text, rejection_text = literal_interval(lines, alternative), literal_interval(lines, rejection)
        else:
            require(alternative == [] and rejection == [], 'v2_false_legacy_indicator_cannot_discard_evidence')
            alternative_text = rejection_text = ''
        review.update(target_sha256=row['target_sha256'], student_prefix_sha256=row['student_prefix_sha256'],
            raw_call_sha256=row['provenance']['raw_call_sha256'], has_meaningful_branch=indicator,
            branching_alternative=alternative_text, branch_rejection_reason=rejection_text,
            legacy_evidence_serialization='HOST_BOUND_EXACT_INCLUSIVE_SOURCE_INTERVALS_NO_CLAIM_COERCION')
        review['r106'] = resolve_r106(review['r106'], lines)
    return transport.FROZEN_VALIDATOR(rows, dict(reviews=reviews))


def review_instructions(base):
    replacements = {
        'Record branching_alternative and\nbranch_rejection_reason as exact short spans when present, or empty strings;\nhas_meaningful_branch measures whether a consequential alternative was actually\nexamined and evaluated, not merely mentioned.':
            'Author legacy_considered_and_rejected and the two legacy source-line-ID lists under the explicit V2 contract below.',
        'Copy all hashes exactly and\nreturn every supplied row once.':
            'Return every supplied integer row_key exactly once; never copy hashes or literal legacy evidence strings.',
        'Keep has_meaningful_branch as the legacy alternative/rejection measurement, not a two-method claim.':
            'Keep legacy_considered_and_rejected separate from the R106 departure/return inventory.'}
    for previous, replacement in replacements.items():
        require(base.count(previous) == 1, 'v2_pinned_instruction_replacement')
        base = base.replace(previous, replacement)
    return base + INSTRUCTIONS


def validate_allocation(allocation, config, config_sha256, now):
    delegated = dict(allocation)
    if allocation.get('approved_by') == 'BUILDER_USER_DELEGATED':
        require(allocation.get('delegated_authority') == BUILDER_AUTHORITY
                and allocation.get('historical_acceptance_unchanged') is True
                and allocation.get('r107_selection_enabled') is False,
                'explicit_builder_transport_only_delegation_required')
        delegated['approved_by'] = 'MAIN'
    BASE_ALLOCATION(delegated, config, config_sha256, now)
    require(allocation.get('serialization_contract') == SCHEMA
            and type(allocation.get('maximum_additional_review_calls')) is int
            and 0 < allocation['maximum_additional_review_calls'] <= 118
            and allocation['maximum_additional_review_calls'] % 2 == 0, 'v2_exact_contract_and_118_or_lower_ceiling')


def worker_scan():
    current = transport.PROGRAM
    try:
        transport.PROGRAM = 'gpu.orch_continual_exhaustion_keyed_runtime'
        previous = BASE_SCAN()
    finally:
        transport.PROGRAM = current
    current_scan = BASE_SCAN()
    workers = {item['pid']: item for item in previous['active'] + current_scan['active']}
    return dict(active=list(workers.values()), unreadable_pids=sorted(set(previous['unreadable_pids'] + current_scan['unreadable_pids'])))


def native_phase(config, allocation, allocation_sha, phase, number=None):
    root = Path(config['native_root'])
    if phase in ('inspect', 'claim'):
        return BASE_NATIVE_PHASE(config, allocation, allocation_sha, phase, number)
    if phase == 'prepare':
        result = BASE_NATIVE_PHASE(config, allocation, allocation_sha, phase, number)
        if 'packets' in result:
            batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
            write_once(batch / 'V2_SERIALIZATION_REGISTRATION.json', dict(schema=SCHEMA,
                allocation_sha256=allocation_sha, response_schema_sha256=digest(response_schema(6)),
                instruction_addendum_sha256=digest(INSTRUCTIONS), source_sha256=sha(__file__),
                no_rejected_path_required_for_r106=True, semantic_thresholds_unchanged=True))
        return result
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    registration = read(batch / 'V2_SERIALIZATION_REGISTRATION.json')
    require(registration['schema'] == SCHEMA and registration['allocation_sha256'] == allocation_sha
            and registration['response_schema_sha256'] == digest(response_schema(6))
            and registration['source_sha256'] == sha(__file__), 'v2_prospective_serialization_binding')
    if phase == 'reserve':
        claim = read(root / 'KEYED_CONTINUATION_CLAIM.json')
        ceiling = min(128, claim['state']['budget']['reserved'] + allocation['maximum_additional_review_calls'])

        def bounded(state, deadline, now):
            require(state['reserved'] + 2 <= ceiling, 'v2_additional_allowance_exhausted_no_new_pool')
            return BASE_RESERVE(state, deadline, now)

        previous = transport.old.reserve_budget
        try:
            transport.old.reserve_budget = bounded
            return BASE_NATIVE_PHASE(config, allocation, allocation_sha, phase, number)
        finally:
            transport.old.reserve_budget = previous
    if phase != 'finalize':
        return BASE_NATIVE_PHASE(config, allocation, allocation_sha, phase, number)
    transport.old.verify_native(root)
    claim = read(root / 'KEYED_CONTINUATION_CLAIM.json')
    require(claim['allocation_sha256'] == allocation_sha and number >= claim['state']['next_number'] and number > 54,
            'v2_fresh_post54_batch_only')
    require(not (batch / 'RESULT_REDUCTION.json').exists(), 'single_finalize_no_salvage')
    packets = [read(batch / f'REVIEW_PACKET_{group}.json') for group in range(2)]
    keyed_registration = read(batch / 'KEYED_DISPATCH_REGISTRATION.json')
    for group, packet in enumerate(packets):
        uploaded = batch / 'PROVIDER_UPLOAD' / f'batch_{number:03d}_{group}'
        require(read(uploaded / 'HOST_REGISTRY.json') == packet
            and read(uploaded / 'PACKET.json') == transport.model_packet(packet)
            and digest(packet) == keyed_registration['packet_sha256s'][group]
            and not list(uploaded.rglob('*FAILED*.json')), 'v2_original_packet_no_failed_review')

    def bound_validate(rows, result):
        expected = [dict(target=row['target'], target_sha256=row['target_sha256'], gold=row['gold'],
            student_prefix_sha256=row['student_prefix_sha256'], provenance=dict(raw_call_sha256=row['provenance']['raw_call_sha256'])) for row in rows]
        matches = [packet for packet in packets if transport.packet_rows(packet) == expected]
        require(len(matches) == 1, 'exact_native_sample_group_join')
        return validate_result(matches[0], result, digest(matches[0]))

    previous = transport.old.validate_reviews
    try:
        transport.old.validate_reviews = bound_validate
        result = transport.old.native_finalize(root, number)
    finally:
        transport.old.validate_reviews = previous
    reviews = read(batch / 'SAMPLED_REVIEWS.json')
    measurements = [dict(target_sha256=review['target_sha256'], legacy_considered_and_rejected=review['legacy_considered_and_rejected'],
        r106=review['r106'], worked_methods=transport.old.method_measurement(review),
        repetition=review['branch_metrics']['repetition_failure']) for review in reviews]
    receipt = dict(schema=SCHEMA, serialization_registration_sha256=sha(batch / 'V2_SERIALIZATION_REGISTRATION.json'),
        reviews_sha256=sha(batch / 'SAMPLED_REVIEWS.json'), sampled_measurements=measurements,
        legacy_considered_and_rejected_rows=sum(review['legacy_considered_and_rejected'] for review in reviews),
        r106_broad_rows=sum(bool(review['r106']['departures_and_returns']) for review in reviews),
        r106_mid_solution_rows=sum(any(item['return_phase'] == 'MID_SOLUTION' for item in review['r106']['departures_and_returns']) for review in reviews),
        r106_terminal_rows=sum(any(item['return_phase'] == 'TERMINAL_CHECK_OR_ASIDE' for item in review['r106']['departures_and_returns']) for review in reviews),
        r106_unknown_rows=sum(review['r106']['measurement_status'] == 'UNKNOWN' for review in reviews),
        denominator=12, unsampled='UNKNOWN_UNREVIEWED', historical_relabeling=False, semantic_thresholds_unchanged=True)
    write_once(batch / 'V2_MEASUREMENT_RECEIPT.json', receipt)
    return dict(result, measurement_receipt_path=str(batch / 'V2_MEASUREMENT_RECEIPT.json'),
                measurement_receipt_sha256=sha(batch / 'V2_MEASUREMENT_RECEIPT.json'))


def activate():
    transport.PROGRAM = PROGRAM
    transport.R106_ADDENDUM = INSTRUCTIONS
    transport.keyed.keyed_schema = response_schema
    transport.validate_result = validate_result
    transport.review_instructions = review_instructions
    transport.validate_allocation = validate_allocation
    transport.worker_scan = worker_scan
    transport.native_phase = native_phase


if __name__ == '__main__':
    activate()
    transport.main()
