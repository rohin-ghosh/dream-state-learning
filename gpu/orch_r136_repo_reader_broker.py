"""One-shot node-local TRAIN-request reader; no evaluator or arbitrary path access."""

import argparse
import json
from pathlib import Path
import time

from gpu.orch_r125_stream_console import _open_stream_directory, _read_record
from gpu.orch_r127_pilot_console import _bytes, _directory, _read, _stage
from gpu.orch_r125_stream_journal import SCHEMA as JOURNAL_SCHEMA, _digest
from gpu.orch_r136_repo_reader import DOCUMENTS, deliver, digest, requests, require, verify


def write(output, name, value):
    with _directory(output) as directory:
        _stage(directory, name, _bytes(value))


def validate(config):
    require(config['schema'] == 'R136_REPO_READER_BROKER_V1', 'broker_schema')
    require(time.time() < config['hard_end_unix'] <= 1789596240, 'existing_wall_only')
    for key in ('root', 'snapshot', 'output', 'receipts'):
        path = Path(config[key])
        require(path.is_absolute() and '..' not in path.parts
                and str(path).startswith('/localhome/local-rohing/orch_r136_repo_reader_'),
                'owned_node_local_paths')
    if 'connection_receipt_path' in config:
        path = Path(config['connection_receipt_path'])
        require(path.is_absolute() and '..' not in path.parts
                and path.parent == Path(config['root']).parent / 'broker1'
                and path.name == 'FIRST_READ.json', 'own_prior_connection_only')
    verify(config['snapshot'], config['manifest_sha256'])
    return config


def serve(config_path):
    config_path = Path(config_path)
    config = validate(json.loads(config_path.read_text()))
    output = Path(config['output'])
    output.mkdir(mode=0o700, exist_ok=False)
    Path(config['receipts']).mkdir(mode=0o700, exist_ok=False)
    write(output, 'STARTED.json', dict(started_unix=time.time(), config_sha256=digest(config_path.read_bytes())))
    while time.time() < config['hard_end_unix']:
        if (Path(config['root']) / 'stream' / 'inbox').exists():
            break
        time.sleep(2)
    require(time.time() < config['hard_end_unix'], 'wall_before_connection')
    stream = Path(config['root']) / 'stream'
    with _directory(stream) as directory:
        journal = json.loads(_read(directory, 'JOURNAL.json', 16384))
    require(set(journal) == {'schema', 'journal_id'} and journal['schema'] == JOURNAL_SCHEMA,
            'real_journal_manifest')
    if 'connection_receipt_path' in config:
        path = Path(config['connection_receipt_path'])
        with _directory(path.parent) as directory:
            raw = _read(directory, path.name, 16384)
        require(digest(raw) == config['connection_receipt_sha256'], 'prior_connection_hash')
        first = json.loads(raw)
        require(first['manifest_sha256'] == config['manifest_sha256']
                and first['file_sha256'] == digest(DOCUMENTS['access.md'].encode()), 'same_connection_snapshot')
        require(not list(path.parent.glob('READ_*.json')), 'no_prior_child_reads_to_replay')
        write(output, 'CONNECTION_REUSED.json', first)
    else:
        first = deliver(config['root'], config['snapshot'], config['manifest_sha256'],
                        'access.md', config['receipts'], dict(actor='operator', reason='initial_connection'))
        first['published_unix'] = time.time()
        write(output, 'FIRST_READ.json', first)
    previous, index, journal_id = _digest(journal), 0, journal['journal_id']
    pending = {first['publication']['id']: 'FIRST_READ_CONSUMED.json'}
    while time.time() < config['hard_end_unix']:
        with _open_stream_directory(config['root'], 'records') as (directory, unused):
            record = _read_record(directory, index)
        if record is None:
            time.sleep(2)
            continue
        require(record['previous_sha256'] == previous, 'journal_chain')
        require(record['journal_id'] == journal_id, 'one_journal_identity')
        if record['kind'] == 'INBOX':
            identifier = record['document']['message']['id']
            if identifier in pending:
                write(output, pending.pop(identifier), dict(inbox_id=identifier, record_index=index,
                      record_sha256=record['sha256'], observed_unix=time.time()))
        if record['kind'] == 'RESPONSE':
            request = dict(actor='child', split='TRAIN', record_index=index, record_sha256=record['sha256'])
            try:
                names = requests(record['document']['response']['raw'])
            except ValueError as error:
                write(output, f'REJECTED_{index:020d}.json', dict(request=request, reason=str(error)))
                names = []
            for name in names:
                require(time.time() < config['hard_end_unix'], 'wall_before_read')
                write(output, f'INTENT_{index:020d}.json', dict(request=request, file=name))
                result = deliver(config['root'], config['snapshot'], config['manifest_sha256'],
                                 name, config['receipts'], request)
                result.update(request=request, published_unix=time.time())
                write(output, f'READ_{index:020d}.json', result)
                pending[result['publication']['id']] = f'CONSUMED_{index:020d}.json'
        previous = record['sha256']
        index += 1
    write(output, 'EXIT.json', dict(reason='existing_lease_wall', finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    serve(parser.parse_args().config)
