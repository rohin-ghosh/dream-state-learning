"""Observe actual publications/rendering; arm authorized post-three-sleep withdrawal."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from inventory_node1 import HERE, Reader, digest, require
from parent_custody import write


REPO = HERE.parents[3]
PROBE = HERE / 'exposure_probe.py'


def publications():
    entries = []
    for path in sorted(HERE.glob('FIRST_BASELINE_*/PUBLICATION.json')):
        document = json.loads(Reader().raw(path))
        entries.append(dict(document, receipt=dict(path=str(path), sha256=digest(path.read_bytes()))))
    for activation_path in sorted(HERE.glob('lane*_activation_*/PARENT_ACTIVATED.json')):
        directory = activation_path.parent
        spec = json.loads((directory / 'SPEC.json').read_text())
        for marker in sorted((directory / 'parent').glob('parent_*/ARM_PUBLISHED.json')):
            document = json.loads(Reader().raw(marker))
            source_path = marker.parent / 'SOURCE.json'
            raw = Reader().raw(source_path)
            source = json.loads(raw)
            entries.append(dict(document, active_spec=str(directory / 'SPEC.json'),
                source_path=str(source_path), source_sha256=digest(raw),
                source_record_count=source['record_count'], source_head_sha256=source['head_sha256'],
                receipt=dict(path=str(marker), sha256=digest(marker.read_bytes()))))
    require(len(entries) <= 2048, 'bounded_owned_publications')
    require(len({entry['publication']['id'] for entry in entries}) == len(entries), 'unique_publication_receipts')
    return entries


def observe(entry, cursor, probe_raw):
    spec = json.loads(Reader().raw(entry['active_spec']))
    config = json.loads(Reader().raw(spec['config']))
    require(spec['root'] == entry['root'] and spec['arm'] == entry['arm'], 'actual_assignment_root')
    script = probe_raw.decode() + '\nimport json\nprint(json.dumps(probe(' + repr(entry) + ',' + repr(cursor) + ')))\n'
    command = 'PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=' + shlex.quote(config['source_root'])
    command += ' python3 -c ' + shlex.quote(script)
    result = subprocess.run(['bash', str(REPO / 'gpu/a100_ssh.sh'), command],
                            capture_output=True, text=True, timeout=45)
    require(result.returncode == 0, 'exposure_probe_failed:' + result.stderr[-2000:])
    require(len(result.stdout.encode()) <= 1024 * 1024, 'bounded_metadata_transport')
    return json.loads(result.stdout)


def withdrawal(entry, observation, receipt):
    cursor = observation['cursor']
    directory = Path(entry['active_spec']).parent
    if len(cursor['completed_sleeps']) < 3:
        return
    flag = directory / 'PARENT_WITHDRAWAL.json'
    if not flag.exists():
        write(flag, dict(schema='ROHIN175_AUTHORIZED_THREE_SLEEP_WITHDRAWAL_V1', observed_unix=time.time(),
              first_exposure=cursor['exposure'], three_completed_sleeps=cursor['completed_sleeps'][:3],
              evidence=receipt, check_status='INCOMPLETE_REQUIRES_SOURCE_ADJUDICATION',
              retirement=False, child_actions=0, already_inflight_publications_may_complete=True,
              old_parent_and_peer_messages_may_remain_visible=True))
    pending = [path for path in (directory / 'parent').glob('parent_*')
               if path.is_dir() and not (path / 'RESULT.json').exists()]
    started = directory / 'WITHDRAWAL_SETTLED.json'
    if not pending and not started.exists():
        write(started, dict(observed_unix=time.time(), after_record_index=cursor['next_index'] - 1,
              head_sha256=cursor['head_sha256'], flag_sha256=digest(flag.read_bytes()),
              no_more_new_provider_turns=True, no_clean_context_claim=True, peer_treatment_not_started=True))
    if started.exists() and not (directory / 'WITHDRAWAL_SLEEP_COMPLETE.json').exists():
        boundary = json.loads(started.read_text())['after_record_index']
        complete = next((item for item in cursor['completed_sleeps'] if item['record_index'] > boundary), None)
        if complete:
            write(directory / 'WITHDRAWAL_SLEEP_COMPLETE.json', dict(observed_unix=time.time(),
                  completed_sleep=complete, source_evidence=receipt, no_clean_context_claim=True,
                  resumed_or_retired=False, outcome_status='INCOMPLETE_REQUIRES_REVIEW'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', type=int, default=120)
    arguments = parser.parse_args()
    require(60 <= arguments.interval <= 300, 'bounded_nonbusy_observer')
    directory = HERE / ('EXPOSURE_OBSERVER_' + str(time.time_ns()))
    directory.mkdir(mode=0o700)
    probe_raw = Reader().raw(PROBE)
    pins = {str(path): digest(path.read_bytes()) for path in (PROBE, Path(__file__))}
    write(directory / 'STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(), source_pins=pins,
          interval_seconds=arguments.interval, child_actions=0, only_own_receipts_and_TRAIN_records=True))
    states = {}
    print(json.dumps(dict(status='OBSERVER_STARTED', directory=str(directory), pid=os.getpid())), flush=True)
    while True:
        require(all(digest(Path(path).read_bytes()) == expected for path, expected in pins.items()),
                'observer_source_unchanged')
        entries = publications()
        clocks = {}
        for entry in entries:
            identifier = entry['publication']['id']
            try:
                observation = observe(entry, states.get(identifier), probe_raw)
                states[identifier] = observation['cursor']
                receipt_path = directory / (identifier + '_' + str(time.time_ns()) + '.json')
                write(receipt_path, dict(observation, publication_receipt=entry['receipt'], source_pins=pins))
                reference = dict(path=str(receipt_path), sha256=digest(receipt_path.read_bytes()))
                if observation['rendered']:
                    current = clocks.get(entry['root'])
                    if current is None or observation['cursor']['exposure']['record_index'] < current[1]['cursor']['exposure']['record_index']:
                        clocks[entry['root']] = (entry, observation, reference)
                print(json.dumps(dict(publication=identifier, receipt=reference,
                      registered=observation['registered'], rendered=observation['rendered'],
                      completed_sleeps_after_exposure=observation['completed_sleeps_after_exposure'],
                      bytes_charged=observation['bytes_charged'])), flush=True)
            except Exception as error:
                path = directory / ('ERROR_' + identifier + '_' + str(time.time_ns()) + '.json')
                write(path, dict(error_type=type(error).__name__, reason=str(error), publication=identifier,
                      observed_unix=time.time(), status='INCOMPLETE_NOT_FAILURE_OR_SUCCESS'))
                print(json.dumps(dict(status='OBSERVER_INCOMPLETE', error_receipt=str(path))), flush=True)
        for entry, observation, reference in clocks.values():
            withdrawal(entry, observation, reference)
        if arguments.once:
            break
        specs = [json.loads(path.read_text()) for path in HERE.glob('lane*_activation_*/SPEC.json')]
        walls = [json.loads(Path(spec['config']).read_text())['hard_end_unix'] for spec in specs]
        if walls and time.time() >= min(walls):
            break
        time.sleep(arguments.interval)


if __name__ == '__main__':
    main()
