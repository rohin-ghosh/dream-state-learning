"""Bounded TRAIN-stage/device metadata for six copies; no journal replay or writes."""

import hashlib
import json
import argparse
from pathlib import Path
import time


MAX_TOTAL = 64 * 1024**2
MAX_FILE = 8 * 1024**2
charged = 0


def read(path):
    global charged
    size = path.stat().st_size
    if size > MAX_FILE or charged + size > MAX_TOTAL:
        raise ValueError('bounded_operational_read_budget')
    charged += size
    with path.open('rb') as stream:
        raw = stream.read(size + 1)
    if len(raw) != size:
        raise ValueError('operational_file_changed_during_read')
    return raw


def process(pid):
    try:
        fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, alive=True, startticks=fields[19], state=fields[0])
    except FileNotFoundError:
        return dict(pid=pid, alive=False)


def observe(root):
    receipts = {}
    for name in ('READY.json', 'STARTED.json', 'control/LAUNCH.json', 'control/CONFINEMENT_CPU.json',
        'control/CONFINEMENT_CHILD.json', 'control/FAILED.json', 'control/OUTER_FAILED.json',
        'control/EXIT.json', 'control/OUTER_EXIT.json'):
        path = root / name
        if path.exists():
            raw = read(path)
            document = json.loads(raw)
            document.pop('source_pins', None)
            receipts[name] = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), document=document)
    pinraw = read(root / 'SOURCE.json')
    expected = json.loads(pinraw)['source_pins']
    source = root / 'source'
    actual = {str(path.relative_to(source)): hashlib.sha256(read(path)).hexdigest() for path in source.rglob('*.py')}
    plan = json.loads(read(root / 'control/PLAN.json'))
    records = sorted((root / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    selected = {path.name: path for path in records[-4:] if int(path.stem) >= 5129}
    for index in (5129, 5130, 5133, 5138, 5139, 5144, 5147, 5149):
        path = root / 'raw/stream/records' / f'{index:020d}.json'
        if path.exists():
            selected[path.name] = path
    events = []
    keys = ('pid', 'loaded_unix', 'started_unix', 'finished_unix', 'optimizer_step', 'optimizer_steps',
        'stage', 'trial_id', 'segment', 'cycle', 'completed_sleeps', 'resume', 'policy', 'new_presentations',
        'new_rows', 'selected_old_rows', 'anchor_lambda', 'plasticity', 'status')
    for path in sorted(selected.values()):
        raw = read(path)
        record = json.loads(raw)
        document = record['document']
        item = dict(index=record['index'], kind=record['kind'], record_sha256=record['sha256'],
            file_sha256=hashlib.sha256(raw).hexdigest(), persisted_unix=path.stat().st_mtime,
            **{key: document[key] for key in keys if key in document})
        if record['kind'] == 'R184_STAGE':
            item['consolidation'] = {key: value for key, value in document.get('consolidation', {}).items()
                if key in ('status', 'revision')}
        if record['kind'] == 'R184_ACT':
            item['outcome'] = {key: value for key, value in document['outcome'].items()
                if key in ('status', 'executed', 'result_status', 'result_sha256', 'error_type')}
        events.append(item)
    loaded = next((item for item in events if item['kind'] == 'LOADED'), None)
    native = process(loaded['pid']) if loaded else None
    launch = receipts.get('control/LAUNCH.json', {}).get('document')
    if native is None and launch:
        parent_pid = launch['pid']
        children = Path('/proc', str(parent_pid), 'task', str(parent_pid), 'children')
        if children.exists():
            native = dict(loaded_verified=False, processes=[process(int(value)) for value in children.read_text().split()])
    return dict(base=str(root), source_pins_unchanged=actual == expected,
        source_manifest_sha256=hashlib.sha256(pinraw).hexdigest(), source_file_count=len(actual),
        plan={key: plan.get(key) for key in ('physical', 'gpu_uuid', 'new_presentations', 'plasticity',
            'max_sleeps', 'hard_end_unix', 'lease_end_unix', 'segments_per_sleep', 'seed')},
        receipts=receipts, events=events, native=native, retained_record_count=len(records),
        records_read=len(selected), complete_episode_encoder_integrated=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=('first', 'root-v2'), default='first')
    parser.add_argument('--lr3-attempt', choices=('2', '3'), default='2')
    arguments = parser.parse_args()
    copies = {}
    base = Path('/localhome/local-rohing/orch_r186_c2_plasticity_20260917' if arguments.version == 'first'
        else '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917')
    suffix = '1' if arguments.version == 'first' else '2'
    for label in ('p4', 'p32', 'lr03', 'lr3'):
        current_suffix = arguments.lr3_attempt if label == 'lr3' and arguments.version == 'root-v2' else suffix
        copies[label] = observe(base / (label + current_suffix))
    baseline = Path('/localhome/local-rohing/orch_r153_r184_node2_20260917')
    for label in ('explicit', 'brief'):
        copies[label] = observe(baseline / (label + '1'))
    print(json.dumps(dict(observed_unix=time.time(), attempt_version=arguments.version, operational_bytes_read=charged, copies=copies,
        source_changes=False, learner_signals=0, full_journal_audit_claim=False), sort_keys=True))


if __name__ == '__main__':
    main()
