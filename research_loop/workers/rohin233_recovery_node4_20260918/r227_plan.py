"""Prospective plan transformation only; no live source or process mutation."""

from copy import deepcopy
from pathlib import PurePosixPath


POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
FIELDS = ('code_target_filter', 'learn_review_filter', 'prose_target_filter',
    'content_target_filter', 'question_target_filter', 'fabricated_speaker_filter', 'language_target_policy')


def proposed_plan(current, proposed_source):
    source = PurePosixPath(proposed_source)
    if not source.is_absolute() or '..' in source.parts or source == PurePosixPath(current['source_root']):
        raise ValueError('distinct_absolute_prospective_source_required')
    result = deepcopy(current)
    removed = {'plan': {}, 'think_act_learn': {}}
    for label, config in [('plan', result), ('think_act_learn', result['think_act_learn'])]:
        for key in FIELDS:
            if key in config:
                removed[label][key] = config.pop(key)
        config['learn_row_policy'] = POLICY
    previous_extension = result.pop('authorized_wall_extension', None)
    result['source_root'] = proposed_source
    return result, dict(removed_future_selectors=removed,
        old_wall_extension_removed_for_same_long_wall_resume=previous_extension is not None,
        previous_row_annotations='UNCHANGED_NOT_REPLAYED',
        source_status='RECEIVING_OVERLAY_NOT_BUILT_OR_LOADED',
        admission='NEXT_FRESH_COMPLETE_ONLY_AFTER_RECEIVING_SOURCE_TESTS_NO_CURRENT_REPLAY_INTERRUPT')
