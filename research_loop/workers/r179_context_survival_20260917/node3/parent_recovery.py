"""Reattach settled node3 parents to recovered journals without replaying turns."""

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REFRESH = REPO / 'research_loop/workers/r169_parent_auth_refresh_20260917/refresh.py'
MAPPING = HERE / 'PARENT_RECOVERY_MAPPING.json'
HARD_END = 1789689000
LEASE_END = 1789689600


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, indent=2, sort_keys=True, allow_nan=False)
        output.flush()
        os.fsync(output.fileno())


def reference(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def verify(reference_value):
    require(sha(reference_value['path']) == reference_value['sha256'], 'unchanged_bound_evidence')
    return Path(reference_value['path'])


def refresh_module():
    spec = importlib.util.spec_from_file_location('r169_parent_refresh', REFRESH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recover_clock(state, row):
    require(state['schema'] == 'R133_TRAIN_PARENT_SNAPSHOT_V1', 'training_snapshot_only')
    require(state['record_count'] > row['saved_record_index'], 'saved_prefix_present')
    result = copy.deepcopy(state)
    offsets = {}
    for kind, field in (('REQUEST', 'request_count'), ('RESPONSE', 'response_count')):
        saved = row['saved_counts'][kind]
        terminal = row['terminal_counts'][kind]
        require(all(type(value) is int and value >= 0 for value in (saved, terminal, state[field])),
                'nonnegative_exact_counters')
        require(terminal >= saved and state[field] >= saved, 'no_counter_regression')
        offsets[field] = terminal - saved
        result['journal_' + field] = state[field]
        result[field] = state[field] + offsets[field]
    for boundary in result.get('boundaries', []):
        if boundary['record_index'] > row['saved_record_index']:
            boundary['journal_response_count'] = boundary['response_count']
            boundary['response_count'] += offsets['response_count']
    result['recovery_clock'] = dict(
        schema='R179_ACCOUNTED_LIFETIME_PARENT_CLOCK_V1', offsets=offsets,
        active_host_root=row['active_host_root'], original_archived_root=row['logical_root'],
        saved_record_index=row['saved_record_index'], terminal_counts=row['terminal_counts'],
        discarded_suffix_not_replayed=True, raw_journal_counters_preserved=True)
    return result


def recovered_config(original, row, ledger, predecessor, source_root):
    require(original['node'] == 'ovx2' and original['root'] == row['logical_root'], 'exact_node3_life')
    require(original['hard_end_unix'] == 1789668000, 'known_expired_internal_wall')
    config = dict(original)
    config.update(root=row['active_host_root'], source_root=source_root, hard_end_unix=HARD_END,
                  predecessor_output=str(predecessor),
                  predecessor_started_sha256=sha(predecessor / 'STARTED.json'))
    for kind, field in (('REQUEST', 'request_count'), ('RESPONSE', 'response_count')):
        config['start_after_' + field] = max(row['terminal_counts'][kind],
            ledger['cursor'] if ledger['clock'] == field else 0)
    return config


def prepare(physical):
    refresh = refresh_module()
    mapping = read(MAPPING)
    rows = [row for row in mapping['rows'] if row['physical'] == physical]
    require(len(rows) == 1, 'one_recovered_life')
    row = rows[0]
    loaded_path = HERE / f'RECOVERY_LOADED_{physical}.json'
    loaded = read(loaded_path)
    require(loaded['status'] == 'SAVED_PREFIX_R179_WALL_SUCCESSOR_LOADED'
            and loaded['active_host_root'] == row['active_host_root']
            and loaded['saved_cycle'] == row['saved_cycle']
            and loaded['hard_end_unix'] == HARD_END and loaded['lease_end_unix'] == LEASE_END,
            'actual_bound_loaded_recovery')
    bindings = []
    for path in REFRESH.parent.glob('parent_*/BINDING.json'):
        binding = read(path)
        config = read(binding['config'])
        if config['node'] == 'ovx2' and config['root'] == row['logical_root']:
            bindings.append((path, binding, config))
    require(len(bindings) == 1, 'one_previous_parent_binding')
    previous_path, previous, config = bindings[0]
    spawned = read(previous_path.parent / 'SPAWNED.json')
    require(not Path('/proc', str(spawned['pid'])).exists(), 'expired_predecessor_process_gone')
    for field in ('source', 'provider'):
        require(sha(previous[field + '_copy']) == previous[field + '_sha256'], 'frozen_parent_policy')
    require(sha(previous['config']) == previous['config_sha256'], 'frozen_previous_config')
    require(sha(REFRESH) == previous['operator_sha256'], 'frozen_refresh_operator')
    ledger = refresh.settled(Path(previous['output']), config)
    output = HERE / 'parents' / f'physical{physical}'
    output.mkdir(parents=True, exist_ok=False)
    new_config = recovered_config(config, row, ledger, Path(previous['output']), loaded['source_root'])
    write(output / 'CONFIG.json', new_config)
    write(output / 'PREDECESSOR_LEDGER.json', ledger)
    binding = dict(previous, config=str(output / 'CONFIG.json'), config_sha256=sha(output / 'CONFIG.json'),
                   output=str(output / 'parent'), previous_output=previous['output'],
                   cursor=new_config['start_after_' + ledger['clock']])
    document = dict(schema='R179_NODE3_PARENT_REATTACHMENT_V1', row=row, parent_binding=binding,
        references=[reference(__file__), reference(REFRESH), reference(MAPPING), reference(loaded_path),
                    reference(previous_path), reference(output / 'PREDECESSOR_LEDGER.json'),
                    reference(HERE.parent / 'NODE3_EXISTING_LEASE_CONTINUATION.md'),
                    reference(HERE.parent / 'NODE3_POST_WALL_RECOVERY.md')],
        physical=physical, hard_end_unix=HARD_END, machine_lease_unchanged=LEASE_END,
        historical_pending_inbox_ids_preserved_not_republished=ledger['pending_inbox_ids'],
        programme_policy_unchanged=True, source_and_provider_unchanged=True,
        prepared_unix=time.time())
    write(output / 'BINDING.json', document)
    print(json.dumps(dict(status='PREPARED_PARENT_NOT_STARTED', physical=physical,
                         binding=str(output / 'BINDING.json'), cursor=binding['cursor'])))


def load(document):
    for item in document['references']:
        verify(item)
    binding = document['parent_binding']
    sys.path.insert(0, binding['original']['cwd'])
    parent = refresh_module().load_parent(binding)
    original_snapshot = parent['snapshot']
    row = document['row']

    def routed_snapshot(repository, config):
        require(config['root'] == row['active_host_root'], 'recovered_root_only')
        return recover_clock(original_snapshot(repository, config), row)

    parent['snapshot'] = routed_snapshot
    return parent


def start(binding_path):
    document = read(binding_path)
    parent = load(document)
    binding = document['parent_binding']
    config = read(binding['config'])
    require(bool(os.environ.get('NVIDIA_API_KEY')), 'current_credential_environment_required')
    state = parent['snapshot'](REPO, config)
    output = binding_path.parent
    write(output / 'PREFLIGHT.json', dict(status='CPU_LIVE_TRAIN_SNAPSHOT_PASS',
        observed_unix=time.time(), record_count=state['record_count'], head_sha256=state['head_sha256'],
        request_count=state['request_count'], response_count=state['response_count'],
        recovery_clock=state['recovery_clock'], no_provider_call=True))
    write(output / 'DISPATCH_ONCE.json', dict(created_unix=time.time(), binding=reference(binding_path)))
    command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--binding', str(binding_path)]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                       PYTHONPATH=binding['original']['cwd'])
    with (output / 'PARENT.log').open('xb') as log:
        process = subprocess.Popen(command, env=environment, cwd=binding['original']['cwd'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    identity = refresh_module().identity(process.pid)
    receipt = dict(status='PARENT_PROCESS_STARTED_NOT_DELIVERY', physical=document['physical'],
        identity=identity, started_unix=time.time(), command=command,
        active_host_root=config['root'], cursor=binding['cursor'],
        credential_from_current_environment=True, model=refresh_module().MODEL)
    write(output / 'SPAWNED.json', receipt)
    print(json.dumps(receipt))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'start', 'serve'))
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7))
    parser.add_argument('--binding', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.physical)
    elif args.action == 'start':
        start(args.binding.resolve())
    else:
        document = read(args.binding)
        parent = load(document)
        binding = document['parent_binding']
        parent['serve'](Path(binding['config']), REPO, Path(binding['output']))


if __name__ == '__main__':
    main()
