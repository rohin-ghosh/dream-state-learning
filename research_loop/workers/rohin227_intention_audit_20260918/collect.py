"""CPU-only bounded live reads using existing transport and immutable readers."""

import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

from audit import analyze


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[2]
TARGETS = {
    'C2': 'gpu/ovx3_ssh.sh',
    'P7': 'gpu/a40r_ssh.sh',
}
READER = REPOSITORY / 'research_loop/workers/rohin220_fable_channel_20260918/read_journal.py'
if not READER.exists():
    READER = OWN / 'journal_reader.py'
PROJECTOR = OWN / 'read_tail.py'


def target_life(label):
    value = json.loads((OWN / 'private/TARGETS.json').read_bytes())[label]
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError('private_absolute_life_required')
    return value


def make_program(label, start_cycle, max_records):
    if label not in TARGETS or not 2 <= start_cycle <= 10000 or not 1 <= max_records <= 1600:
        raise ValueError('bounded_target_required')
    reader_bytes, projector_bytes = READER.read_bytes(), PROJECTOR.read_bytes()
    tail = (f'\nLIFE = Path({target_life(label)!r})\n'
            f'result = collect_window(LIFE, {start_cycle}, {max_records})\n'
            f'result["source_label"] = {label!r}\n'
            'print(json.dumps(result, ensure_ascii=False))\n').encode()
    program = (reader_bytes.rsplit(b'\nif __name__', 1)[0] + b'\n'
               + projector_bytes.rsplit(b'\nif __name__', 1)[0] + tail)
    provenance = dict(reader_sha256=hashlib.sha256(reader_bytes).hexdigest(),
                      projector_sha256=hashlib.sha256(projector_bytes).hexdigest(),
                      transported_program_sha256=hashlib.sha256(program).hexdigest(),
                      transport_wrapper_sha256=hashlib.sha256((REPOSITORY / TARGETS[label]).read_bytes()).hexdigest())
    return program, provenance


def collect(label, start_cycle, max_records):
    os.umask(0o077)
    program, provenance = make_program(label, start_cycle, max_records)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    private = OWN / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    result = subprocess.run(['bash', str(REPOSITORY / TARGETS[label]),
                             'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
                            input=program, capture_output=True, timeout=180, cwd=REPOSITORY)
    with (private / f'{label}_{stamp}.stderr').open('xb') as output:
        output.write(result.stderr)
    if result.returncode:
        raise RuntimeError('bounded_read_failed_private_error_retained')
    evidence = json.loads(result.stdout)
    with (private / f'{label}_{stamp}.json').open('xb') as output:
        output.write(result.stdout)
    report = analyze(evidence, label)
    report['input_file_sha256'] = hashlib.sha256(result.stdout).hexdigest()
    report['audit_module_sha256'] = hashlib.sha256((OWN / 'audit.py').read_bytes()).hexdigest()
    report['collection'] = dict(provenance, collector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                remote_writes=False, signals=0, inbox_changes=False, parent_changes=False,
                                event_counts=dict(collections.Counter(event['kind'] for event in evidence['events'])))
    output_path = OWN / f'{label}_AUDIT_{stamp}.json'
    with output_path.open('x') as output:
        json.dump(report, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(dict(report=output_path.name, sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                          label=label, observed_utc=report['observed_utc'], head=report['head']['index'],
                          cycles=report['cycles'], uncertainty_count=len(report['uncertainties'])), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=tuple(TARGETS), required=True)
    parser.add_argument('--start-cycle', type=int, required=True)
    parser.add_argument('--max-records', type=int, default=1600)
    arguments = parser.parse_args()
    collect(arguments.target, arguments.start_cycle, arguments.max_records)
