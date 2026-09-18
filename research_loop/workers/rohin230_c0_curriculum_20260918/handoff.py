"""Gracefully replace only the verified C0 reading CPU publisher."""

import argparse
import json
import os
from pathlib import Path
import time

from c0_receipt import ROOT, checked_record, identity, require, sha, utc
from curriculum_parent import checkpoint_reference
from reading_parent import write


def process(pid, start_ticks, command_fragment):
    directory = Path('/proc')/str(pid)
    fields = (directory/'stat').read_text().rsplit(')', 1)[1].split()
    command = (directory/'cmdline').read_bytes()
    require(int(fields[19]) == start_ticks and command_fragment.encode() in command
        and fields[0] not in ('T', 'Z', 'X'), 'exact_live_owner_identity')
    return dict(pid=pid, start_ticks=start_ticks, state=fields[0], cmdline_sha256=sha(command))


def handoff(directory, legacy_directory):
    os.umask(0o077)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    owner = identity()
    math = process(2561001, 94172764, str(ROOT/'parent.py'))
    legacy = json.loads((legacy_directory/'SERVICE.json').read_bytes())
    require(legacy['pid'] == 2729920 and legacy['start_ticks'] == 94773801, 'assigned_old_reading_service')
    old = process(legacy['pid'], legacy['start_ticks'], 'reading_parent.py')
    records = ROOT/'raw/stream/records'
    complete = next(record for path in reversed(sorted(records.glob('[0-9]'*20+'.json'))[-256:])
        if (record := checked_record(path))['kind'] == 'SLEEP_COMPLETE')
    checkpoint = checkpoint_reference(complete)
    write(directory/'BEFORE_HANDOFF.public.json', dict(observed_utc=utc(time.time()), identity=owner,
        original_math_parent=math, previous_reading_publisher=old, checkpoint=checkpoint,
        learner_controls=0, no_model_calls=True))
    identity()
    process(legacy['pid'], legacy['start_ticks'], 'reading_parent.py')
    write(legacy_directory/'CANCEL_READING_SERVICE', dict(requested_utc=utc(time.time()),
        operation='Supported graceful reading-publisher-only handoff to R230',
        expected_pid=legacy['pid'], expected_start_ticks=legacy['start_ticks'], learner_controls=0))
    for attempt in range(30):
        exit_path = legacy_directory/'EXIT.json'
        process_path = Path('/proc')/str(legacy['pid'])
        stopped = not process_path.exists()
        if process_path.exists():
            fields = (process_path/'stat').read_text().rsplit(')', 1)[1].split()
            stopped = fields[0] == 'Z' or int(fields[19]) != legacy['start_ticks']
        if stopped and exit_path.is_file():
            final = json.loads(exit_path.read_bytes())
            write(directory/'HANDOFF.public.json', dict(completed_utc=utc(time.time()), identity=identity(),
                original_math_parent=process(2561001, 94172764, str(ROOT/'parent.py')),
                old_reading_publisher=old, old_exit_sha256=sha(exit_path.read_bytes()),
                inherited_pending=final['state']['pending'] is not None,
                inherited_record_cursor=final['state']['record_cursor'],
                signals=0, learner_controls=0, no_learning_rate_changes=True))
            return
        time.sleep(1)
    raise ValueError('old_reading_graceful_exit_not_verified_no_new_publisher_started')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--legacy-directory', type=Path, required=True)
    arguments = parser.parse_args()
    handoff(arguments.directory, arguments.legacy_directory)
