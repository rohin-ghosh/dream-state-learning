"""Read parent-visible evidence and reuse the existing attributed inbox transport."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


TARGETS = {
    'learner': ('orch_r231_curriculum_birth_20260918', 493500, '10070880',
                '038f85cbde5c4abfb749ea4d59da6897'),
    'frozen': ('orch_r232_curriculum_frozen_20260918', 471737, '9987073',
               '30fa18c869b34fd496a2758a4a28e197'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def identity(arm):
    name, process_id, ticks, journal = TARGETS[arm]
    root = Path('/localhome/local-rohing') / name
    process = Path('/proc') / str(process_id)
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    argv = (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(fields[19] == ticks and fields[0] not in ('Z', 'X'), 'native_identity_changed')
    require('gpu.r232_recovery' in argv and 'native' in argv and '--config' in argv,
            'unexpected_native_command')
    config_path = Path(argv[argv.index('--config') + 1])
    require(root in config_path.parents, 'native_config_root_mismatch')
    manifest = json.loads((root / 'raw/stream/JOURNAL.json').read_bytes())
    require(manifest['journal_id'] == journal, 'native_journal_changed')
    return root, dict(pid=process_id, start_ticks=ticks, journal_id=journal,
                     boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                     argv=argv, cwd=str((process / 'cwd').resolve()), root=str(root))


def project(record):
    result = {key: record[key] for key in ('index', 'sha256', 'kind')}
    document = record['document']
    kind = record['kind']
    if kind == 'REQUEST':
        state = document['resume_state']['state']
        result['document'] = {key: document.get(key) for key in
                              ('messages', 'started_unix', 'segment', 'deadline_unix')}
        result['document']['pending_sha256'] = state['pending']
        result['document']['parent_provenance'] = [
            {key: event.get(key) for key in ('event_id', 'source_sha256')}
            for event in state['history']['events'] if event.get('actor') == 'parent']
    elif kind == 'RESPONSE':
        result['document'] = dict(request_sha256=document['request_sha256'],
                                  finished_unix=document.get('finished_unix'),
                                  response=dict(raw=document['response']['raw']))
    elif kind == 'COMMITTED':
        result['document'] = {key: document.get(key) for key in ('segment', 'source_sha256')}
    elif kind in ('R184_STAGE', 'INBOX', 'R184_ACT'):
        result['document'] = document
    elif kind == 'TERMINAL':
        result['document'] = dict(terminal_observed=True)
    return result


def poll(root, request, native):
    records = root / 'raw/stream/records'
    start = request['next_index']
    previous = request['previous_sha256']
    anchor = json.loads((records / f'{start - 1:020d}.json').read_bytes())
    require(anchor['sha256'] == previous, 'cursor_anchor_changed')
    require(anchor['sha256'] == digest({key: value for key, value in anchor.items()
                                       if key != 'sha256'}), 'cursor_anchor_corrupt')
    result = []
    for index in range(start, start + 160):
        path = records / f'{index:020d}.json'
        if not path.exists():
            break
        record = json.loads(path.read_bytes())
        require(record['index'] == index and record['journal_id'] == native['journal_id'],
                'canonical_index_or_journal_mismatch')
        require(record['previous_sha256'] == previous, 'journal_chain_changed')
        require(record['sha256'] == digest({key: value for key, value in record.items()
                                           if key != 'sha256'}), 'journal_record_corrupt')
        previous = record['sha256']
        result.append(project(record))
    return dict(records=result, next_index=start + len(result), previous_sha256=previous,
                caught_up=len(result) < 160)


def execute(request):
    root, native = identity(request['arm'])
    if request.get('native') is not None:
        require(request['native'] == native, 'fresh_native_binding_changed')
    if request['action'] == 'bind':
        result = {}
    elif request['action'] == 'poll':
        result = poll(root, request, native)
    elif request['action'] == 'publish':
        require(request['journal_id'] == native['journal_id'], 'publication_journal_mismatch')
        payload = {key: value for key, value in request.items() if key not in ('arm', 'native')}
        child = subprocess.run([sys.executable, '-B', str(root / 'parent_io.py')],
                               input=json.dumps(payload), text=True, capture_output=True, timeout=60)
        require(child.returncode == 0, 'existing_parent_transport_failed')
        result = json.loads(child.stdout)
    else:
        raise ValueError('unknown_parent_operation')
    require(identity(request['arm'])[1] == native, 'native_changed_during_operation')
    return dict(result, native=native, observed_unix=time.time())


if __name__ == '__main__':
    try:
        print(json.dumps(execute(json.load(sys.stdin)), ensure_ascii=False))
    except (ValueError, FileNotFoundError) as error:
        print(json.dumps(dict(fatal=type(error).__name__, reason=str(error))))
        sys.exit(2)
