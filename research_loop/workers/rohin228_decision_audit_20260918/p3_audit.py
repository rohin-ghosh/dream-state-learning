"""P3 decision observations joined to exact scorer-origin and ACT-byte receipts."""

from collections import Counter

from decision_audit import analyze, compare_objects


COUNT_KEYS = ('parsed', 'scored', 'accepted', 'new_pixels', 'judge_rejected', 'cached')


def bind_outcome(row, receipts):
    matching = [item for item in receipts if item['origin']['record_index'] == row['response']['index']
                and item['origin']['record_sha256'] == row['response']['sha256']]
    if not matching:
        return dict(status='UNKNOWN_NO_SCORER_RECEIPT', counts=None, selections=[])
    if len(matching) != 1:
        return dict(status='AMBIGUOUS_MULTIPLE_SCORER_RECEIPTS', counts=None, selections=[],
                    receipt_sha256=[item['receipt_sha256'] for item in matching])
    receipt = matching[0]
    if receipt['raw_act_sha256'] != row['target_sha256']:
        return dict(status='UNKNOWN_ACT_BYTES_MISMATCH', counts=None, selections=[])
    if not receipt['feedback_present']:
        return dict(status='UNKNOWN_FEEDBACK_MISSING', counts=None, selections=[])
    counts = receipt['counts']
    if any(type(counts.get(key)) is not int or counts[key] < 0 for key in COUNT_KEYS):
        return dict(status='UNKNOWN_INVALID_COUNTS', counts=None, selections=[])
    if not 0 <= counts['new_pixels'] <= counts['accepted'] <= counts['scored']:
        return dict(status='UNKNOWN_INCONSISTENT_COUNTS', counts=None, selections=[])
    return dict(status='BOUND_SCORER_ORIGIN_AND_EXACT_ACT_BYTES', counts=counts,
                receipt_sha256=receipt['receipt_sha256'], session_sha256=receipt['session_sha256'],
                saved_unix=receipt['saved_unix'], selections=receipt['selections'],
                feedback_delivered_or_consumed='NOT_MEASURED')


def project(evidence, receipts, provenance=None):
    report = analyze(evidence, 'SYNTHETIC')
    report['label'] = 'P3'
    report['binding_label_alias'] = 'Legacy binding label allowlist only; real P3 sources, not synthetic data.'
    report['schema'] = 'R228_P3_DECISION_AND_GAME_OUTCOME_V1'
    previous = []
    previous_cycle = None
    for cycle in report['cycles']:
        rows = [row for row in report['rows'] if row['cycle'] == cycle['cycle']
                and row['stage'] == 'ACT' and not row['console_reply']]
        outcomes = [dict(response=row['response'], **bind_outcome(row, receipts)) for row in rows]
        known = [outcome for outcome in outcomes if outcome['counts'] is not None]
        subtotal = {key: sum(outcome['counts'][key] for outcome in known) for key in COUNT_KEYS}
        complete = bool(rows) and len(known) == len(rows)
        selections = [item for outcome in known for item in outcome['selections']]
        transition = compare_objects(previous, selections)
        transition['basis'] = 'SCORER_PARSED_CHILD_SELECTIONS_NOT_ENVIRONMENT_NOVELTY'
        earlier_stop = previous_cycle is not None and (
            previous_cycle['self_declared_decision'] == 'STOP' or previous_cycle['declared_exhaustion'])
        behavior = []
        if earlier_stop and transition['inferred_decision'] == 'BRANCH':
            behavior.append(dict(label='STOPS_CHANGES',
                                 basis='EARLIER_SELF_DECLARED_STOP_OR_EXHAUSTION_THEN_PARSED_SELECTION_CHANGE'))
        elif earlier_stop and cycle['act_byte_relation'] == 'EXACT_REPEAT' and complete:
            behavior.append(dict(label='STOPS_REPEATS',
                                 basis='EARLIER_SELF_DECLARED_STOP_OR_EXHAUSTION_THEN_EXACT_ACT_BYTES_REPEAT'))
        if (complete and subtotal['new_pixels'] > 0 and previous_cycle is not None
                and previous_cycle['game']['all_ACTs_accounted']
                and previous_cycle['game']['counts']['new_pixels'] > 0
                and transition['inferred_decision'] == 'CONTINUE'):
            behavior.append(dict(label='KEEPS_DISCOVERING',
                                 basis='INFERRED_SUCCESSIVE_GAME_NEW_PIXEL_INCREMENTS_NOT_SEMANTIC_NOVELTY'))
        if cycle['declared_exhaustion']:
            behavior.append(dict(label='DECLARES_EXHAUSTION', basis='SELF_DECLARED_ONLY'))
        cycle['game'] = dict(outcomes=outcomes, bound_ACTs=len(known), unknown_ACTs=len(rows)-len(known),
                             counts=subtotal if complete else None, known_subtotal=subtotal,
                             all_ACTs_accounted=complete,
                             scene_direction_transition=transition,
                             behavior_observations=behavior or [dict(label='UNKNOWN', basis='INSUFFICIENT_EVIDENCE')],
                             no_ACT_is_not_stop=True, accepted_is_not_new_pixel=True)
        previous = selections if complete else []
        previous_cycle = cycle
    report['game_coverage'] = dict(
        bound_ACTs=sum(cycle['game']['bound_ACTs'] for cycle in report['cycles']),
        unknown_ACTs=sum(cycle['game']['unknown_ACTs'] for cycle in report['cycles']),
        totals_known_only={key: sum(cycle['game']['known_subtotal'][key] for cycle in report['cycles'])
                           for key in COUNT_KEYS},
        transition_counts=dict(Counter(cycle['game']['scene_direction_transition']['inferred_decision']
                                       for cycle in report['cycles'])),
        cycle_is_not_controller_opportunity=True, unjoined_receipts_not_counted=True,
        scoring_session_count=len({item['session_sha256'] for item in receipts}))
    report['scorer_cut'] = provenance or {}
    report['private_transcripts_included'] = False
    return report
