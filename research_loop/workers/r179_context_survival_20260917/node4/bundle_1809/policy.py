"""Prospective context-view policy; no change to generation, targets, or sleep."""

import ast
import re

from organism_v6.orch_r124_train_history import CompactionRequired


SCHEMA = 'R179_CONTEXT_SURVIVES_SLEEP_V1'
COMPACTION_BLOCK = re.compile(
    r"(?m)^(?P<indent> +)stream\.history\.compact\(summary, through=stream\.history\.frontier\(len\(stream\.history\.events\)-1\)\)\n"
    r"(?P=indent)journal\.record\('COMPACTION', dict\(kind='CHILD_COMPACTION', state=stream\.checkpoint\(\)\)\)\n"
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def threshold_tokens(stream):
    require(type(stream.context_limit) is int and type(stream.segment_tokens) is int
            and 0 < stream.segment_tokens < stream.context_limit,
            'bounded_context_and_generation_reservation')
    return min(stream.context_limit * 3 // 4, stream.context_limit - stream.segment_tokens)


def retain_or_compact(child, stream, journal, summary, cycle):
    require(stream.pending is None and stream.sleep_due, 'completed_presleep_generation_required')
    require(type(cycle) is int and cycle > 0, 'positive_sleep_cycle')
    require(summary.actor == 'child' and summary.phase == 'compaction'
            and bool(summary.text.strip()), 'own_nonempty_summary_required')
    require(len(stream.history.events) >= 2, 'summary_and_usage_events_required')
    latest = stream.history.events[-2]
    require(latest.actor == 'child' and latest.text == summary.text
            and latest.source_sha256 == summary.source_sha256,
            'summary_must_be_actual_latest_child_response')
    require(stream.history.events[-1].actor == 'environment'
            and stream.history.events[-1].source_id.startswith('cost:'),
            'exact_post_generation_usage_tail')
    threshold = threshold_tokens(stream)
    counts = []

    def count_visible(messages):
        count = child.count_tokens(messages)
        counts.append(count)
        return count

    try:
        stream.history.render(count_visible, threshold, presentation=stream.presentation)
    except CompactionRequired:
        pass
    require(len(counts) == 1 and type(counts[0]) is int and counts[0] >= 0,
            'one_actual_rendered_token_count')
    before = stream.history.checkpoint()
    decision = dict(schema=SCHEMA, cycle=cycle, context_limit=stream.context_limit,
        threshold_tokens=threshold, visible_prompt_tokens=counts[0],
        history_sha256_before=before['state_sha256'],
        raw_event_count=len(stream.history.events),
        visible_frontier_before=stream.history.visible_frontier.event_count,
        retelling_event_id=latest.event_id, retelling_source_sha256=latest.source_sha256,
        targets_rewritten=False, optimizer_recipe_changed=False)
    if counts[0] >= threshold:
        stream.history.compact(summary, through=stream.history.frontier(len(stream.history.events)-1))
        decision['action'] = 'COMPACT_AT_CONTEXT_THRESHOLD'
        decision['history_sha256_after'] = stream.history.checkpoint()['state_sha256']
        journal.record('COMPACTION', dict(kind='CHILD_COMPACTION',
            context_policy=decision, state=stream.checkpoint()))
    else:
        require(stream.history.checkpoint() == before, 'measurement_must_not_mutate_context')
        decision['action'] = 'RETAIN_CONTEXT_ACROSS_SLEEP'
        decision['history_sha256_after'] = before['state_sha256']
        journal.record('CONTEXT_RETAINED', decision)
    return decision


def patch_native(source):
    require(type(source) is str and 'orch_r179_context_survival' not in source,
            'new_context_policy_successor_only')
    matches = list(COMPACTION_BLOCK.finditer(source))
    require(len(matches) == 1, 'one_exact_native_compaction_block')
    match = matches[0]
    indent = match.group('indent')
    replacement = (indent + 'from gpu.orch_r179_context_survival import retain_or_compact\n'
                   + indent + 'retain_or_compact(child, stream, journal, summary, cycle)\n')
    patched = source[:match.start()] + replacement + source[match.end():]
    require(patched.replace(replacement, match.group(), 1) == source,
            'only_compaction_decision_changes')
    ast.parse(patched)
    compile(patched, '<r179-context-policy-successor>', 'exec')
    return patched
