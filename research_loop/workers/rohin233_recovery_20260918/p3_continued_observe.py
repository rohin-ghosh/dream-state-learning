"""Read exact P3 continuation evidence and optionally bind its parent transport."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3')
TARGET = ROOT / 'r233_lease_continuation'
CONTROL = TARGET / 'control'
SOURCE = TARGET / 'source'
END_UNIX = 1790359200


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def process(pid):
    path = Path('/proc') / str(pid)
    if not path.exists():
        return None
    fields = path.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0],
        source=str(path.joinpath('cwd').resolve()))


def observe():
    recovery = read(CONTROL / 'RECOVERY.json')
    result = dict(observed_utc=utc(time.time()), status='CPU_REPLAY_BEFORE_DISPATCH',
        life='P3', node='node4', gpu=3, target_deadline_utc=utc(END_UNIX),
        actual_deadline_utc=None, recovery_sha256=digest(CONTROL / 'RECOVERY.json'),
        original_journal_id=recovery['journal_id'], complete_index=None,
        old_head_index=recovery['old_head_index'], preserved_tail_records=recovery['preserved_tail_record_count'],
        native=None, loaded=None, wall_extended=None, binding=None)
    result['complete_index'] = read(Path(recovery['complete_path']))['index']
    for name in ('RECOVERY_APPENDED.json', 'GUARD.json', 'DISPATCHING.json'):
        result[name] = digest(CONTROL / name) if (CONTROL / name).exists() else None
    if result['DISPATCHING.json'] is not None:
        result['status'] = 'DISPATCHED_LOAD_PENDING'
    paths = sorted((ROOT / 'life/stream/records').glob('*.json'))
    for path in paths:
        if not path.stem.isdigit() or int(path.stem) <= recovery['old_head_index']:
            continue
        row = read(path)
        if row['kind'] not in ('LOADED', 'WALL_EXTENDED'):
            continue
        document = row['document']
        projected = dict(index=row['index'], sha256=row['sha256'],
            document={key:value for key,value in document.items() if key in
                ('pid', 'loaded_unix', 'optimizer_steps', 'resume', 'previous_deadline_unix',
                 'new_deadline_unix', 'lease_end_unix', 'safety_margin_seconds')})
        if row['kind'] == 'WALL_EXTENDED':
            projected['authorization'] = document['authorization']
            projected['saved_state_sha256'] = document['state']['sha256']
        result['loaded' if row['kind'] == 'LOADED' else 'wall_extended'] = projected
    loaded = result['loaded']
    if loaded is not None:
        actual = process(loaded['document']['pid'])
        result['native'] = actual
        if actual is not None and actual['state'] != 'Z' and actual['source'] == str(SOURCE):
            sys.path.insert(0, str(SOURCE))
            from gpu.orch_r125_stream_journal import _digest
            row = read(ROOT / f'life/stream/records/{loaded["index"]:020d}.json')
            if _digest({key:value for key,value in row.items() if key != 'sha256'}) != row['sha256']:
                raise ValueError('actual_LOADED_digest')
            guard = read(CONTROL / 'GUARD.json')
            if guard['hard_end_unix'] != END_UNIX or result['wall_extended'] is None:
                raise ValueError('actual_wall_extension_required')
            wall = read(ROOT / f'life/stream/records/{result["wall_extended"]["index"]:020d}.json')
            if _digest({key:value for key,value in wall.items() if key != 'sha256'}) != wall['sha256']:
                raise ValueError('actual_WALL_EXTENDED_digest')
            if wall['document']['authorization']['new_deadline_unix'] != END_UNIX:
                raise ValueError('actual_requested_wall_adopted')
            binding = dict(pid=actual['pid'], start_ticks=actual['start_ticks'], source=str(SOURCE),
                loaded_index=loaded['index'], loaded_sha256=loaded['sha256'],
                journal_id=recovery['journal_id'], hard_end_unix=END_UNIX,
                guard_sha256=digest(CONTROL / 'GUARD.json'))
            result.update(status='LOADED_ALIVE_WALL_EXTENDED', actual_deadline_utc=utc(END_UNIX),
                binding=binding, loaded_utc=utc(loaded['document']['loaded_unix']))
        else:
            result['status'] = 'LOADED_RECEIPT_NATIVE_NOT_ALIVE'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', action='store_true')
    options = parser.parse_args()
    evidence = observe()
    if options.bind:
        binding = evidence['binding']
        if binding is None:
            raise ValueError('no_actual_continued_native_to_bind')
        path = CONTROL / 'LIVE_BINDING.json'
        if path.exists():
            if read(path) != binding:
                raise ValueError('preserve_existing_binding_new_incarnation_needs_new_receipt')
        else:
            with path.open('x') as stream:
                json.dump(binding, stream, sort_keys=True, indent=2)
                stream.write('\n')
        evidence['binding_persisted'] = True
    print(json.dumps(evidence, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
