"""Return actual post-repair broker rejections; never execute or replay tools."""

import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r183_repo_learning_20260917/birth1')
OUTPUT = ROOT / 'r206_error_feedback'
FLOOR = 5104


def eligible(receipt, seen):
    origin = receipt.get('origin', {})
    index = origin.get('record_index')
    return (origin.get('actor') == 'child' and origin.get('split') == 'TRAIN'
        and isinstance(index, int) and index > FLOOR and index not in seen
        and receipt.get('error_type') in ('ValueError', 'FileNotFoundError', 'FileExistsError', 'UnicodeError'))


def message(receipt, checksum):
    return ('Tool result status: REPO_ACTION_REJECTED\n'
        'The repository broker recorded an error for your request. Do not infer a successful read or write; '
        'no action is automatically retried.\n'
        'Error: ' + receipt['error_type'] + ': ' + receipt['reason'][:300] + '\nReceipt: ' + checksum)


def main():
    source = ROOT / 'r204_boundary_20260918t0356z/source'
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import _open_stream_directory, _publish, SCHEMA
    OUTPUT.mkdir(mode=0o700)
    with (OUTPUT / 'STARTED.json').open('x') as stream:
        json.dump(dict(started_unix=time.time(), floor=FLOOR, maximum_publications=12,
            actual_tool_executions=0, no_historical_replay=True), stream)
    seen = set()
    deadline = json.loads((ROOT / 'control/PLAN.json').read_bytes())['hard_end_unix']
    while time.time() < deadline and len(seen) < 12:
        for path in sorted((ROOT / 'tool_receipts').glob('REJECTED_*.json')):
            if int(path.stem.split('_')[1]) <= FLOOR:
                continue
            receipt = json.loads(path.read_bytes())
            if not eligible(receipt, seen):
                continue
            origin = receipt['origin']
            index = origin['record_index']
            record = json.loads((ROOT / 'life/stream/records' / f'{index:020d}.json').read_bytes())
            assert record['kind'] == 'RESPONSE' and record['sha256'] == origin['record_sha256']
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            text = message(receipt, checksum)
            document = dict(schema=SCHEMA, id=f'r206_birth1_rejected_{index}', text=text, actor='environment',
                speaker='Tool', split='TRAIN', source_receipt=dict(path=str(path), sha256=checksum))
            with _open_stream_directory(ROOT / 'life', 'inbox') as (descriptor, directory):
                publication = _publish(descriptor, directory, document)
            with (OUTPUT / f'PUBLICATION_{index:020d}.json').open('x') as stream:
                json.dump(dict(publication=publication, published_unix=time.time(), origin=origin,
                    actual_rejection_sha256=checksum, text=text, executions=0, rendered=False), stream, indent=2)
            seen.add(index)
        time.sleep(2)
    with (OUTPUT / 'EXIT.json').open('x') as stream:
        json.dump(dict(finished_unix=time.time(), published_indices=sorted(seen), executions=0), stream)


if __name__ == '__main__':
    main()
