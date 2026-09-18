"""Read-only paged enrollment, explicitly distinct from immutable source capture."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
WORKER = Path(__file__).resolve().parent
WRAPPERS = {'ovx_ssh.sh', 'ovx2_ssh.sh', 'ovx3_ssh.sh', 'ovx4_ssh.sh', 'a40r_ssh.sh'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def put(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_bytes(canonical(value) + b'\n')
    temporary.replace(path)


def read_record(path, target, expected=None):
    if path.is_symlink() or path.stat().st_size > 33554432:
        raise ValueError('bounded_regular_record')
    record = json.loads(path.read_bytes())
    if (record['journal_id'] != target['journal_id'] or record['index'] != int(path.stem)
            or record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'})
            or expected is not None and record['sha256'] != expected):
        raise ValueError('journal_record_identity')
    return record


def page(target, cursor, limit=768):
    life = Path(target['root'])
    if life.resolve() != life or not life.is_absolute() or not 1 <= limit <= 2048:
        raise ValueError('pinned_physical_root_and_bounded_scan')
    records = life / 'stream/records'
    anchor = target['initial_loaded']
    loaded = read_record(records / f"{anchor['index']:020d}.json", target, anchor['sha256'])
    if loaded['kind'] != 'LOADED' or loaded['document']['base_sha256'] != BASE:
        raise ValueError('pinned_initial_loaded_base')
    paths = sorted(path for path in records.iterdir() if re.fullmatch(r'\d{20}\.json', path.name))
    observed_head = int(paths[-1].stem)
    if cursor.get('last_index') is not None:
        read_record(records / f"{cursor['last_index']:020d}.json", target, cursor['last_sha256'])
    selected = [path for path in paths if int(path.stem) > cursor.get('last_index', -1)][:limit]
    previous_index, previous_sha = cursor.get('last_index'), cursor.get('last_sha256')
    entries, epochs = [], []
    last_epoch = cursor.get('last_epoch')
    for path in selected:
        record = read_record(path, target)
        if previous_index is not None and (record['index'] != previous_index + 1
                or record.get('previous_sha256') != previous_sha):
            raise ValueError('contiguous_journal_frontier')
        if record['kind'] == 'LOADED':
            last_epoch = dict(index=record['index'], sha256=record['sha256'],
                attribution='journal_load_observed_owner_treatment_metadata_pending')
            epochs.append(last_epoch)
        document = record['document']
        if record['kind'] == 'SLEEP_COMPLETE' and document.get('status') == 'COMPLETE':
            cycle = document['cycle']
            checkpoint = life / 'checkpoints' / f'sleep_{cycle:06d}' / 'COMMIT.json'
            commit_status = 'MISSING'
            commit_sha = None
            if checkpoint.is_file() and not checkpoint.is_symlink():
                raw = checkpoint.read_bytes()
                commit = json.loads(raw)
                commit_sha = hashlib.sha256(raw).hexdigest()
                commit_status = ('JOINED_NOT_COPIED' if commit['base_sha256'] == BASE
                    and commit['optimizer_steps'] == document['total_optimizer_steps']
                    and commit['adapter_state_sha256'] == document['after_adapter_sha256'] else 'MISMATCH')
            entries.append(dict(key=target['journal_id'] + ':' + record['sha256'], life=target['label'],
                journal_id=target['journal_id'], sleep=cycle, record_index=record['index'],
                record_sha256=record['sha256'], optimizer_steps=document['total_optimizer_steps'],
                adapter_state_sha256=document['after_adapter_sha256'], runtime_load=last_epoch,
                recorded_unix=record.get('created_unix', record.get('unix')),
                enrollment='ENROLLED_REFERENCE_PENDING_CAPTURE', checkpoint_status=commit_status,
                commit_sha256=commit_sha, cumulative_training_tokens=None, cumulative_training_seconds=None,
                exposure='PENDING_SOURCE_AND_INHERITED_AUDIT', context_into_probe=False,
                evaluation='PENDING', captured=False, dispatched=False, evaluated=False))
        previous_index, previous_sha = record['index'], record['sha256']
    return dict(unix=time.time(), label=target['label'], observed_head=observed_head, scanned=len(selected),
        entries=entries, epochs=epochs, cursor=dict(last_index=previous_index, last_sha256=previous_sha,
        last_epoch=last_epoch), caught_up=previous_index == observed_head, learner_signals=[])


def remote_page(target, cursor, repo):
    if target['wrapper'] not in WRAPPERS:
        raise ValueError('registered_current_wrapper_only')
    source = Path(__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0]
    payload = source + '\nprint(json.dumps(page(' + repr(target) + ',' + repr(cursor) + ')))\n'
    result = subprocess.run(['bash', str(repo / 'gpu' / target['wrapper']), 'python3 -B -'],
        input=payload, text=True, capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError('remote_page_failed_' + str(result.returncode))
    if len(result.stdout) > 1048576:
        raise ValueError('bounded_remote_metadata')
    return json.loads(result.stdout)


def tick(registration, output, repo):
    state_path = output / 'private' / 'STATE.json'
    state = json.loads(state_path.read_bytes()) if state_path.exists() else dict(cursors={}, entries={})
    rows = []
    for target in registration['targets']:
        label = target['label']
        try:
            response = remote_page(target, state['cursors'].get(label, {}), repo)
            for entry in response['entries']:
                previous = state['entries'].get(entry['key'])
                if previous is not None and previous != entry:
                    raise ValueError('immutable_enrollment_changed')
                state['entries'][entry['key']] = entry
            state['cursors'][label] = response['cursor']
            rows.append(dict(life=label, status='CAUGHT_UP' if response['caught_up'] else 'BACKLOG_SCANNING',
                observed_head=response['observed_head'], verified_frontier=response['cursor']['last_index'],
                last_record_sha256=response['cursor']['last_sha256']))
        except Exception as error:
            rows.append(dict(life=label, status='READ_ERROR_PENDING', error_type=type(error).__name__,
                verified_frontier=state['cursors'].get(label, {}).get('last_index')))
        put(state_path, state)
    entries = sorted(state['entries'].values(), key=lambda row: (row['life'], row['record_index']))
    for row in rows:
        own = [entry for entry in entries if entry['life'] == row['life']]
        row.update(enrolled=len(own), completed_sleeps=[entry['sleep'] for entry in own],
            pending_capture=len(own), captured_by_this_queue=0, dispatched_by_this_queue=0,
            evaluated_by_this_queue=0, external_fresh_queue='reported_separately')
    status = dict(schema='R233_EVERY_KEPT_SLEEP_ENROLLMENT_V1', unix=time.time(), pid=os.getpid(),
        deadline_unix=registration['deadline_unix'], rows=rows, entries=entries,
        native_sources=len(rows), enrolled=len(entries), parent_free_evaluation=True,
        standalone_base=dict(sleep_age=None, classification='FROZEN_WEIGHT_FLAT_REFERENCE_WITH_TREATMENT_EPOCHS',
            in_life_parenting='R233_PARENT_v1_separately_observed_not_same_unparented_control'),
        no_hidden_subsampling=True, learner_signals=[],
        extra_node2_player='PENDING_MAIN_KEPT_DISPOSITION',
        capture_caveat='Enrollment verifies records and COMMIT joins, not retained adapter bytes; all evaluations pending here.')
    put(output / 'STATUS.json', status)
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (args.output / 'ENROLL.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    registration_bytes = args.registration.read_bytes()
    registration = json.loads(registration_bytes)
    while time.time() < registration['deadline_unix']:
        if args.registration.read_bytes() != registration_bytes:
            raise ValueError('frozen_registration_changed')
        result = tick(registration, args.output, args.repo)
        print(json.dumps(dict(unix=result['unix'], enrolled=result['enrolled'],
            rows=[dict(life=row['life'], status=row['status'], enrolled=row['enrolled']) for row in result['rows']])), flush=True)
        if args.once:
            break
        time.sleep(min(30, max(0, registration['deadline_unix'] - time.time())))


if __name__ == '__main__':
    main()
