"""Explicit TRAIN-only transition views; no runtime, storage, or outcome inference.

TargetSpan offsets address an actual row's native token_ids. DependencySpan
offsets address the first selected row's exact tokenized recorded prefix and
must decode to the named earlier history event. The caller chooses necessary
dependencies and transition/completion boundaries; this module does not decide
whether an episode succeeded or READY is warranted. Collection receipt custody
remains the caller's responsibility, as with TrainHistory.

Views keep the shortest contiguous recorded window containing all declared
dependencies, the preceding same-row child text, and one causal-prefix token.
No required context is dropped to fit. Complete-episode views require exact
recorded-prefix extension and every intervening child span. All nonselected
tokens, including actual EOS and contextual role markers, have masked loss.
Rows partition across views, so episodes replace rather than augment individual
presentations. No special target tokens, rewritten text, or new markers are added.
"""

from copy import deepcopy
from dataclasses import dataclass

from organism_v6.orch_r124_train_history import TrainHistory


POLICY = 'R184_EXPLICIT_TRANSITION_TARGETS_V1'
PRESENTATIONS = 16
MASK = -100


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


@dataclass(frozen=True)
class TargetSpan:
    source_sha256: str
    start: int
    stop: int


@dataclass(frozen=True)
class DependencySpan:
    event_id: str
    start: int
    stop: int


@dataclass(frozen=True)
class ViewSelection:
    kind: str
    targets: tuple
    dependencies: tuple


@dataclass(frozen=True)
class TransitionView:
    input_ids: tuple
    labels: tuple
    target_ids: tuple
    source_sha256s: tuple
    selection: ViewSelection
    prefix_start: int
    history_frontier_sha256: str


def _span(start, stop, length):
    require(type(start) is int and type(stop) is int and 0 <= start < stop <= length,
            'explicit_nonempty_token_span')


def _decode(tokenizer, tokens):
    return tokenizer.decode(list(tokens), skip_special_tokens=False, clean_up_tokenization_spaces=False)


def _row(row, events, tokenizer):
    require(row['split'] == 'TRAIN' and row['actor'] == 'child'
            and row['prefix_loss'] is False and row['target_loss'] is True,
            'actual_TRAIN_child_targets_only')
    require(row['event_id'] in events, 'actual_history_event_required')
    index, event = events[row['event_id']]
    require(event.actor == 'child' and event.source_sha256 == row['source_sha256']
            and event.text == row['target'], 'row_history_source_binding')
    tokens = tuple(row['token_ids'])
    require(tokens and all(type(token) is int and token >= 0 for token in tokens), 'actual_native_tokens')
    require(type(row['terminal']) is bool, 'actual_terminal_flag')
    require(not row['terminal'] or tokens[-1] == tokenizer.eos_token_id, 'actual_terminal_eos')
    visible = tokens[:-1] if row['terminal'] else tokens
    require(_decode(tokenizer, visible) == row['target'], 'actual_target_roundtrip')
    require(type(row['prefix']) is list and row['prefix'], 'actual_recorded_prefix_required')
    require(all(type(message) is dict and message.get('role') in ('system', 'user', 'assistant')
                and type(message.get('content')) is str for message in row['prefix']), 'recorded_prefix_messages')
    prefix = tuple(tokenizer.apply_chat_template(deepcopy(row['prefix']), tokenize=True,
                   add_generation_prompt=True, return_dict=False))
    require(prefix and all(type(token) is int and token >= 0 for token in prefix), 'actual_prefix_tokens')
    return dict(index=index, event=event, tokens=tokens, visible=visible, prefix=prefix)


def build_views(rows, history, selections, tokenizer, context_limit):
    """Return detached encoded views; explicit selections may omit unchosen rows.

    kind is transition, completion, or complete_episode (a caller declaration,
    never a success label). No automatic dependency discovery or target picking.
    Pass only admitted TRAIN rows; this function never opens collection/eval files.
    """
    require(type(history) is TrainHistory, 'actual_TRAIN_history_required')
    require(type(context_limit) is int and context_limit > 1, 'positive_context_limit')
    require(type(rows) in (list, tuple) and type(selections) in (list, tuple)
            and len(selections) <= len(rows) <= 4096, 'bounded_explicit_row_selection')
    require(all(type(row) is dict and row.get('split') == 'TRAIN' and row.get('actor') == 'child'
                and row.get('prefix_loss') is False and row.get('target_loss') is True
                for row in rows), 'actual_TRAIN_child_targets_only')
    events = {event.event_id: (index, event) for index, event in enumerate(history.events)}
    source_rows = {row['source_sha256']: row for row in rows}
    require(len(source_rows) == len(rows), 'unique_actual_rows')
    specials = set(tokenizer.all_special_ids)
    prepared, assigned, views = {}, set(), []
    for selection in selections:
        require(type(selection) is ViewSelection and selection.kind in
                ('transition', 'completion', 'complete_episode'), 'explicit_view_kind')
        require(type(selection.targets) is tuple and 0 < len(selection.targets) <= 4096
                and type(selection.dependencies) is tuple and len(selection.dependencies) <= 4096,
                'explicit_targets_and_dependencies')
        ordered, sources = [], []
        for target in selection.targets:
            require(type(target) is TargetSpan and target.source_sha256 in source_rows, 'explicit_actual_row')
            source = target.source_sha256
            if source not in prepared:
                prepared[source] = _row(source_rows[source], events, tokenizer)
            item = prepared[source]
            _span(target.start, target.stop, len(item['tokens']))
            require(not specials.intersection(item['tokens'][target.start:target.stop]), 'no_special_target_tokens')
            ordered.append((item['index'], target.start, target.stop))
            if source not in sources:
                sources.append(source)
        require(ordered == sorted(ordered) and all(
            previous[0] != current[0] or previous[2] <= current[1]
            for previous, current in zip(ordered, ordered[1:])), 'ordered_disjoint_actual_targets')
        require(not assigned.intersection(sources), 'row_already_assigned_no_extra_presentations')
        require(selection.kind == 'complete_episode' or len(sources) == 1, 'single_row_transition_or_completion')
        first, last = prepared[sources[0]], prepared[sources[-1]]
        for previous_source, current_source in zip(sources, sources[1:]):
            previous, current = prepared[previous_source], prepared[current_source]
            continuation = previous['prefix'] + previous['tokens']
            require(current['prefix'][:len(continuation)] == continuation, 'episode_requires_exact_recorded_continuation')
        if selection.kind == 'complete_episode':
            require(len({prepared[source]['event'].episode_id for source in sources}) == 1,
                    'complete_episode_same_actual_episode')
            expected = [event.source_sha256 for index, event in events.values()
                        if first['index'] <= index <= last['index'] and event.actor == 'child']
            require(len(sources) >= 2 and sources == expected, 'complete_episode_all_actual_child_rows')
            require(len(selection.targets) == len(sources) and all(
                target.start == 0 and target.stop == len(prepared[target.source_sha256]['visible'])
                for target in selection.targets), 'complete_episode_whole_child_spans')
        starts = [len(first['prefix']) - 1]
        dependency_ids = set()
        for dependency in selection.dependencies:
            require(type(dependency) is DependencySpan and dependency.event_id in events,
                    'explicit_actual_dependency')
            require(dependency.event_id not in dependency_ids, 'unique_dependencies')
            dependency_ids.add(dependency.event_id)
            index, event = events[dependency.event_id]
            require(index < first['index'], 'no_future_dependency')
            _span(dependency.start, dependency.stop, len(first['prefix']))
            require(event.text and _decode(tokenizer, first['prefix'][dependency.start:dependency.stop])
                    == event.text, 'dependency_exact_recorded_text')
            starts.append(dependency.start)
        start = min(starts)
        end = len(last['prefix']) + selection.targets[-1].stop
        require(end - start <= context_limit, 'required_window_exceeds_context_no_trimming')
        inputs = (last['prefix'] + last['tokens'])[:end]
        labels = [MASK] * len(inputs)
        for target in selection.targets:
            item = prepared[target.source_sha256]
            offset = len(item['prefix'])
            require(inputs[offset:offset + len(item['tokens'][:target.stop])]
                    == item['tokens'][:target.stop], 'actual_target_position')
            labels[offset + target.start:offset + target.stop] = item['tokens'][target.start:target.stop]
        targets = tuple(token for token in labels[start:] if token != MASK)
        views.append(TransitionView(inputs[start:], tuple(labels[start:]), targets, tuple(sources),
                     selection, start, history.frontier(last['index'] + 1).sha256))
        assigned.update(sources)
    return views


def presentation_schedule(views):
    """Exactly16 NEW views, with each selected source row assigned to one view."""
    require(type(views) in (list, tuple), 'explicit_views')
    assigned = set()
    for view in views:
        require(type(view) is TransitionView and view.source_sha256s
                and len(set(view.source_sha256s)) == len(view.source_sha256s), 'actual_built_view')
        require(not assigned.intersection(view.source_sha256s), 'row_already_assigned_no_extra_presentations')
        assigned.update(view.source_sha256s)
    return [('NEW', view) for unused in range(PRESENTATIONS) for view in views]
