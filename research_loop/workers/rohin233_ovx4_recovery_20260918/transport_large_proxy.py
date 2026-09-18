"""New immutable CPU transport epoch; no native/scorer source replacement."""

import json
from pathlib import Path
import shlex
import subprocess

from gpu import ny_caption_data as data
from research_loop.workers.rohin221_continuous_caption_20260918.native_proxy import require_future_origin
from research_loop.workers.rohin221_continuous_caption_20260918.journal_transport import MAX_ENVELOPE_BYTES, SCHEMA
from research_loop.workers.rohin233_ovx4_recovery_20260918 import transport_proxy


MODULE = 'research_loop.workers.rohin233_ovx4_recovery_20260918.transport_entry'


def export_via_ssh(config, request, source, wrapper):
    require_future_origin(config, request)
    origin = request['origin']
    data.require(set(origin) == {'kind', 'record_index', 'record_sha256'} and origin['kind'] == 'TRAIN_CHILD_RESPONSE'
        and type(origin['record_index']) is int and origin['record_index'] >= 0
        and len(origin['record_sha256']) == 64 and all(character in '0123456789abcdef' for character in origin['record_sha256']), 'actual_native_origin')
    command = ['env', 'PYTHONPATH='+source, '/usr/bin/python3', '-B', '-m', MODULE,
        '--root', config['life_root'], '--journal-id', config['journal']['journal_id'],
        '--index', str(origin['record_index']), '--sha256', origin['record_sha256']]
    result = subprocess.run(['bash', wrapper, shlex.join(command)], text=True, capture_output=True, timeout=30, check=True)
    data.require(len(result.stdout) <= MAX_ENVELOPE_BYTES, 'bounded_export_response')
    envelope = json.loads(result.stdout)
    data.require(envelope['schema'] == SCHEMA and envelope['origin'] == origin and envelope['journal_id'] == config['journal']['journal_id'], 'same_exported_source_binding')
    return envelope


def stage_via_ssh(config, envelope, source, shared_root):
    mirror = str(Path(shared_root) / 'mirrors' / config['session_id'])
    command = ['env', 'PYTHONPATH='+source, '/usr/bin/python3', '-B', '-m', MODULE,
        '--root', mirror, '--journal-id', config['journal']['journal_id'], '--import-chunk']
    for records in envelope['chunks']:
        result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', shlex.join(command)], input=data.canonical(records),
            capture_output=True, timeout=30, check=True)
        data.require(json.loads(result.stdout) == dict(imported=len(records), first=records[0]['index'], last=records[-1]['index']), 'same_imported_chunk')
    return [envelope['chunks'][-1][-1]]


if __name__ == '__main__':
    transport_proxy.export_via_ssh = export_via_ssh
    transport_proxy.stage_via_ssh = stage_via_ssh
    transport_proxy.main()
