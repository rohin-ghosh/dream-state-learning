"""Count source-bound native outcomes, never envelopes or cached scores as new work."""

from collections import Counter


TRANSPORT_ERRORS = {'ORIGIN_TRANSPORT_NOT_DISPATCHED', 'ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY'}


def aggregate(attempts, opportunities):
    selected, receipts = {}, {}
    transport_origins = set()
    for attempt in attempts:
        key = attempt['origin_sha256']
        if attempt.get('error') in TRANSPORT_ERRORS or attempt.get('outcome_unknown'):
            transport_origins.add(key)
        previous = selected.get(key)
        if previous is None or (bool(attempt.get('scorer_receipt_sha256')), attempt['record_index']) > (
                bool(previous.get('scorer_receipt_sha256')), previous['record_index']):
            selected[key] = attempt
    scored, cached, pixels, parsed = {}, set(), set(), set()
    counts = Counter(ACT_outcomes=len(selected), duplicate_reroute_outcome_records=len(attempts) - len(selected),
        transport_fault_ACTs=len(transport_origins), parser_observed_ACTs=0, parser_fault_ACTs=0,
        no_caption_ACTs=0, routing_ambiguity_ACTs=0, resource_bound_ACTs=0,
        parser_unobserved_ACTs=0, unknown_caption_results=0, duplicate_submission_results=0,
        source_bound_THINK_caption_occurrences=0, source_bound_ACT_caption_occurrences=0)
    for key, attempt in selected.items():
        receipt = attempt.get('scorer_receipt_sha256')
        if receipt:
            if receipt in receipts and receipts[receipt] != key:
                raise ValueError('scorer_receipt_reused_for_different_ACT')
            receipts[receipt] = key
        if attempt.get('parser_observed'):
            counts['parser_observed_ACTs'] += 1
            counts['parser_fault_ACTs'] += int(attempt.get('parser_fault') is True)
            counts['no_caption_ACTs'] += int(attempt.get('no_caption') is True)
            counts['routing_ambiguity_ACTs'] += int(attempt.get('routing_ambiguity') is True)
            counts['resource_bound_ACTs'] += int(attempt.get('resource_bound') is True)
        else:
            counts['parser_unobserved_ACTs'] += 1
        for source in attempt.get('caption_sources', []):
            identity = (key, source['stage'], source['origin']['record_sha256'],
                source['start'], source['end'], source['text_sha256'])
            if identity not in parsed:
                parsed.add(identity)
                counts['source_bound_' + source['stage'] + '_caption_occurrences'] += 1
        for result in attempt.get('results', []):
            identifier = result.get('submission_id')
            if result.get('replayed') is True:
                cached.add(identifier or ('missing', key, result['ordinal']))
                continue
            if (not identifier or result.get('ok') is not True or
                    type(result.get('accepted')) is not bool or result.get('replayed') is not False):
                counts['unknown_caption_results'] += 1
                continue
            if identifier in scored:
                counts['duplicate_submission_results'] += 1
                if scored[identifier]['accepted'] != result['accepted']:
                    raise ValueError('conflicting_submission_result')
                continue
            scored[identifier] = result
            if result['accepted'] and result.get('status') == 'new_pixel':
                if not result.get('pixel_id'):
                    raise ValueError('new_pixel_requires_actual_pixel_identity')
                pixels.add(result['pixel_id'])
    completed, assigned = set(), set()
    for opportunity in opportunities:
        members = tuple(opportunity['attempt_origins'])
        if not members or len(members) != len(set(members)) or any(member not in selected for member in members):
            raise ValueError('completed_opportunity_requires_distinct_bound_ACT_receipts')
        identity = tuple(sorted(members))
        if identity in completed:
            continue
        if assigned.intersection(members):
            raise ValueError('ACT_cannot_belong_to_two_completed_opportunities')
        completed.add(identity)
        assigned.update(members)
    accepted = sum(result['accepted'] for result in scored.values())
    counts.update(completed_native_opportunities=len(completed), parsed_caption_occurrences=len(parsed),
        newly_scored_captions=len(scored), accepted_newly_scored_captions=accepted,
        new_pixels=len(pixels), cached_caption_result_ids=len(cached),
        ACT_outcomes_without_completed_opportunity=len(set(selected) - assigned))
    result = dict(counts)
    result.update(acceptance_rate=dict(numerator=accepted, denominator=len(scored),
        denominator_name='unique newly scored caption submission IDs with explicit replayed=false',
        value=accepted / len(scored) if scored else None),
        deduplicated_ACT_origin_ids=sorted(selected), deduplicated_scorer_receipt_ids=sorted(receipts),
        deduplicated_new_submission_ids=sorted(scored),
        parser_fault_breakdowns_may_overlap=True,
        failed_transport_does_not_establish_zero_parsed_captions=True)
    return result
