"""Prospective plan transformation only; no live source or process mutation."""

import argparse
from copy import deepcopy
import json
from pathlib import Path, PurePosixPath


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
    if result.get('startup_context') is not None:
        startup = PurePosixPath(result['startup_context']['path'])
        previous_source = PurePosixPath(current['source_root'])
        if '..' in startup.parts or not startup.is_relative_to(previous_source):
            raise ValueError('startup_must_remain_inside_pinned_source')
        result['startup_context']['path'] = str(source / startup.relative_to(previous_source))
    return result, dict(removed_future_selectors=removed,
        old_wall_extension_removed_for_same_long_wall_resume=previous_extension is not None,
        previous_row_annotations='UNCHANGED_NOT_REPLAYED',
        source_status='PROSPECTIVE_PLAN_NOT_LOADED',
        admission='NEXT_FRESH_COMPLETE_ONLY_AFTER_RECEIVING_SOURCE_TESTS_NO_CURRENT_REPLAY_INTERRUPT')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    arguments = parser.parse_args()
    if arguments.output.exists() or arguments.output.resolve() == arguments.plan.resolve():
        raise ValueError('new_prospective_plan_only_no_overwrite')
    if arguments.receipt is not None and (arguments.receipt.exists()
            or arguments.receipt.resolve() == arguments.output.resolve()):
        raise ValueError('new_distinct_receipt_only')
    proposed, receipt = proposed_plan(json.loads(arguments.plan.read_bytes()), arguments.source)
    with arguments.output.open('x') as stream:
        json.dump(proposed, stream, indent=2, sort_keys=True)
        stream.write('\n')
    if arguments.receipt is not None:
        with arguments.receipt.open('x') as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write('\n')
    print(json.dumps(dict(status='PROSPECTIVE_PLAN_NOT_LOADED', output=str(arguments.output),
        runtime_files_changed=False, native_signals=[])))


if __name__ == '__main__':
    main()
