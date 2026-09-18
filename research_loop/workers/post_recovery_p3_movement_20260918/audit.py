"""Bounded source-bound P3 movement capture; never publishes or controls lives."""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RECOVERY = HERE.parent / 'rohin233_recovery_20260918'
AUDIT = HERE.parent / 'rohin232_correction_audit_20260918'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def extend(prior, chunk, binding):
    if prior['journal_id'] != binding['journal_id'] or chunk['journal_id'] != binding['journal_id']:
        raise ValueError('same_original_journal_required')
    if prior['loaded_sha256'] != binding['loaded_sha256']:
        raise ValueError('same_actual_LOAD_required')
    previous = prior['through']
    for row in chunk['continuity']:
        if row['journal_id'] != binding['journal_id']:
            raise ValueError('same_original_journal_required')
        if row['index'] != previous['index'] + 1 or row['previous_sha256'] != previous['sha256']:
            raise ValueError('contiguous_authenticated_post_LOAD_window')
        previous = row
    return dict(prior, records=prior['records'] + chunk['records'], through=previous,
        caught_up=all(previous[key] == chunk['head'][key] for key in ('index', 'sha256')))


def selected_frames(evidence, loaded_index):
    audit = load_module('p3_movement_frames', AUDIT / 'audit.py')
    return [frame for frame in audit.frames(evidence)
        if frame['stage'] == 'ACT' and frame['request']['index'] > loaded_index][-10:]


def capture():
    binding = json.loads((RECOVERY / 'P3_RETRY_BINDING.json').read_text())
    cache = HERE / 'EVIDENCE.private.json'
    baseline = cache if cache.exists() else RECOVERY / 'P3_RETRY_EVIDENCE.private.json'
    baseline_sha256 = sha(baseline)
    evidence = json.loads(baseline.read_text())
    reader = (AUDIT / 'reader.py').read_text()
    receipts = []
    for unused in range(6):
        code = reader + '\nimport sys\nsys.path.insert(0, ' + repr(str(Path(binding['source']).parents[1] / 'r233_recovery')) + ')\n'
        code += 'import p3_retry_endpoint as endpoint\nendpoint.configure()\n'
        code += 'print(json.dumps(collect(' + repr(str(Path(binding['source']).parents[1] / 'life'))
        code += ', ' + repr(binding['journal_id']) + ', maximum=120, after=' + str(evidence['through']['index']) + ')))\n'
        response = subprocess.run(['bash', str(REPO / 'gpu/a40r_ssh.sh'), 'python3 -B -'],
            input=code, capture_output=True, text=True, check=True, timeout=120)
        chunk = json.loads(response.stdout)
        evidence = extend(evidence, chunk, binding)
        receipts.append(dict(after=chunk['coverage_start'], through=chunk['through'],
            bytes_read=chunk['bytes_read'], observed_unix=chunk['observed_unix']))
        if evidence['caught_up']:
            break
    cache.write_text(json.dumps(evidence, sort_keys=True) + '\n')
    frames = selected_frames(evidence, binding['loaded_index'])
    lines = []
    seen = set()
    for frame in frames:
        response, request = frame['response'], frame['request']
        lines.append(f"\n## ACT{response['index']} request{request['index']} cycle{request['cycle']}\n")
        for event in request['external']:
            if event['event_id'] not in seen:
                seen.add(event['event_id'])
                lines.append(f"\n### {event['actor']} {event['event_id']}\n" + event['text'] + '\n')
        lines.append('\n### CHILD ACT\n' + response['text'] + '\n')
    (HERE / 'READING.private.md').write_text(''.join(lines))
    public = dict(observed_utc=datetime.now(timezone.utc).isoformat(), journal_id=binding['journal_id'],
        loaded_index=binding['loaded_index'], loaded_sha256=binding['loaded_sha256'],
        baseline_cache_sha256=baseline_sha256, reader_sha256=sha(AUDIT / 'reader.py'),
        capture_sha256=sha(cache), through=evidence['through'], caught_up=evidence['caught_up'],
        available_post_LOAD_ACTs=len(frames), requested_latest_ACTs=10,
        frames=[dict(request_index=frame['request']['index'], request_sha256=frame['request']['sha256'],
            response_index=frame['response']['index'], response_sha256=frame['response']['sha256'],
            response_text_sha256=hashlib.sha256(frame['response']['text'].encode()).hexdigest(),
            committed_index=frame['commit']['index'], stage_index=frame['stage_receipt']['index'],
            cycle=frame['request']['cycle']) for frame in frames],
        windows=receipts, native_signals=[], remote_writes=0, scoring_calls=0,
        private_or_sealed_score_reads=0, publications=0)
    (HERE / 'CAPTURE.json').write_text(json.dumps(public, indent=2, sort_keys=True) + '\n')
    print(json.dumps(public, indent=2))


if __name__ == '__main__':
    capture()
