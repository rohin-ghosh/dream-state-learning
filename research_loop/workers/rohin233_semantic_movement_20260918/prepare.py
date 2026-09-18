"""Freeze existing local evidence and expose only canonical committed ACT pairs."""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


OWN = Path(__file__).resolve().parent
WORKERS = OWN.parent
SOURCE = WORKERS / 'rohin233_focus_20260918/private'
CANONICAL = WORKERS / 'rohin232_correction_audit_20260918/audit.py'


def load_canonical():
    spec = importlib.util.spec_from_file_location('r232_canonical_movement_frames', CANONICAL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CANON = load_canonical()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def stable_bytes(path):
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('evidence_changed_during_read')
    return raw


def act_pairs(evidence):
    return [frame for frame in CANON.frames(evidence) if frame['stage'] == 'ACT'][-2:]


def event_key(event):
    return event['event_id'], event['source_sha256']


def selected(evidence):
    frames = CANON.frames(evidence)
    pair = act_pairs(evidence)
    first_seen = {}
    for frame in frames:
        for event in frame['request']['external']:
            first_seen.setdefault(event_key(event), frame['request']['index'])
    result = []
    for frame in pair:
        externals = []
        for event in frame['request']['external']:
            externals.append(dict(event, first_seen_request=first_seen[event_key(event)]))
        result.append(dict(response=frame['response'], request=frame['request'],
                           commit=frame['commit'], stage_receipt=frame['stage_receipt'],
                           rendered_external=externals))
    return result


def main():
    private = OWN / 'private'
    private.mkdir(exist_ok=True)
    inputs = sorted(SOURCE.glob('*/EVIDENCE.json'))
    if len(inputs) != 16:
        raise ValueError('expected_exactly_16_available_roots')
    rows = []
    for path in inputs:
        label = path.parent.name
        raw = stable_bytes(path)
        evidence = json.loads(raw)
        target = private / label
        target.mkdir()
        (target / 'EVIDENCE.json').write_bytes(raw)
        acts = selected(evidence)
        row = dict(label=label, source_path=str(path.relative_to(WORKERS.parent.parent)),
                   evidence_sha256=sha(raw), evidence_bytes=len(raw),
                   observed_utc=utc(evidence['observed_unix']), coverage_start=evidence['coverage_start'],
                   through=evidence['through'], caught_up=evidence['caught_up'], journal_id=evidence['journal_id'],
                   selected_acts=acts)
        (target / 'REVIEW.json').write_text(json.dumps(row, indent=2) + '\n')
        rows.append({key: value for key, value in row.items() if key != 'selected_acts'})
    manifest = dict(prepared_utc=datetime.now(timezone.utc).isoformat(), inputs=rows,
                    canonical_frames_source=dict(path=str(CANONICAL.relative_to(WORKERS.parent.parent)),
                                                 sha256=sha(CANONICAL.read_bytes())))
    (private / 'CUT.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(cut_start=min(row['observed_utc'] for row in rows),
                          cut_end=max(row['observed_utc'] for row in rows),
                          labels=[row['label'] for row in rows]), indent=2))


if __name__ == '__main__':
    main()
