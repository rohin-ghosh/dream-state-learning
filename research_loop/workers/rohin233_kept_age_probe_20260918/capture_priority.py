"""Fair bounded capture planning; never a GPU or learner controller."""

from collections import Counter, defaultdict


def plan_round(entries, baseline, captured_keys, last_attempted=None, historical=False, limit=16):
    if not 1 <= limit <= 16:
        raise ValueError('bounded_round')
    sources = {row['life']: row for row in baseline}
    if len(sources) != len(baseline) or len({row['journal_id'] for row in baseline}) != len(baseline):
        raise ValueError('distinct_pinned_sources')
    last_attempted = last_attempted or {}
    classes = Counter()
    candidates = {'prospective': defaultdict(list), 'historical': defaultdict(list)}
    seen = set()
    classified = []
    for entry in entries:
        source = sources.get(entry['life'])
        if source is None or source['journal_id'] != entry['journal_id'] or entry['key'] in seen:
            raise ValueError('unique_registered_entry')
        seen.add(entry['key'])
        age_class = 'prospective' if entry['record_index'] > source['source_frontier'] else 'historical'
        if entry['key'] in captured_keys:
            disposition = 'already_captured'
        elif entry['checkpoint_status'] != 'JOINED_NOT_COPIED':
            disposition = 'source_unavailable_or_mismatched'
        else:
            disposition = 'pending_capture'
            candidates[age_class][entry['life']].append(entry)
        classes[age_class + '_' + disposition] += 1
        classified.append(dict(key=entry['key'], life=entry['life'], sleep=entry['sleep'],
            age_class=age_class, disposition=disposition))
    active_class = 'prospective'
    if not candidates['prospective'] and historical:
        active_class = 'historical'
    active = candidates[active_class]
    order = sorted(active, key=lambda label: (last_attempted.get(label, 0), label))
    selected = [min(active[label], key=lambda entry: (entry['record_index'], entry['key']))
        for label in order[:limit]]
    selected_keys = {entry['key'] for entry in selected}
    for row in classified:
        row['selected_this_round'] = row['key'] in selected_keys
    return dict(policy='R233_PROSPECTIVE_FAIR_CAPTURE_V1', selected=selected,
        classes=dict(classes), classified=classified, enrolled_retained=len(entries),
        selected_count=len(selected), at_most_one_per_life=True,
        optional_historical_enabled=historical, active_class=active_class,
        no_hidden_age_subsampling=True, selection_is_not_capture_or_evaluation=True,
        gpu_dispatch=False, learner_signals=[])
