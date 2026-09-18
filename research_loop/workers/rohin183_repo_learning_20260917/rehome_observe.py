"""Bounded receiving operational metadata; never evaluator files or response text."""

import argparse
import hashlib
import json
from pathlib import Path
import time


BASE = Path('/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z')
charged = 0


def read(path):
    global charged
    size = path.stat().st_size
    if size > 8 * 1024**2 or charged + size > 64 * 1024**2:
        raise ValueError('bounded_operational_metadata_budget')
    charged += size
    with path.open('rb') as stream:
        raw = stream.read(size + 1)
    if len(raw) != size:
        raise ValueError('metadata_changed_during_read')
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def process(pid):
    try:
        fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, startticks=fields[19], state=fields[0], alive=fields[0] not in ('Z', 'X'))
    except FileNotFoundError:
        return dict(pid=pid, alive=False)


parser = argparse.ArgumentParser()
parser.add_argument('--original', type=int, choices=(1, 4, 7))
arguments = parser.parse_args()
copies = {}
for original in ((arguments.original,) if arguments.original is not None else (1, 4, 7)):
    folder = BASE / ('receiving' + str(original))
    if not (folder / 'CPU_READY.json').exists():
        continue
    ready, ready_sha = read(folder / 'CPU_READY.json')
    item = {key: value for key, value in ready.items() if key != 'source_pins'}
    item['cpu_ready_sha256'] = ready_sha
    item['receipts'] = {}
    for name in ('DISPATCH_STARTED.json', 'CONFINEMENT_PROBE.json', 'CONFINEMENT_CONTAINED.json',
                 'ADMISSION_TIME.json', 'LAUNCH.json', 'EXIT.json', 'OUTER_EXIT.json',
                 'DISPATCH_FAILED.json', 'CONTAINED_FAILED.json'):
        path = folder / name
        if path.exists():
            document, digest = read(path)
            item['receipts'][name] = dict(path=str(path), sha256=digest, document=document)
    paths = sorted((folder / 'root/stream/records').glob('[0-9]' * 20 + '.json'))
    selected = {path.name: path for path in paths[-2:]}
    for index in range(ready['saved_index'] + 1, ready['saved_index'] + 4):
        path = folder / 'root/stream/records' / f'{index:020d}.json'
        if path.exists():
            selected[path.name] = path
    item['events'] = []
    for path in sorted(selected.values()):
        record, file_sha = read(path)
        document = record['document']
        event = dict(index=record['index'], kind=record['kind'], record_sha256=record['sha256'],
            file_sha256=file_sha, persisted_unix=path.stat().st_mtime,
            **{key: document[key] for key in ('loaded_unix', 'started_unix', 'finished_unix', 'pid',
                'optimizer_steps', 'optimizer_step', 'cycle', 'segment', 'resume') if key in document})
        if record['kind'] == 'LOADED':
            item['native'] = process(document['pid'])
        item['events'].append(event)
    copies[str(original)] = item
print(json.dumps(dict(observed_unix=time.time(), copies=copies, operational_bytes_read=charged,
    source_edits=False, learner_signals=0, provider_calls=0), sort_keys=True))
