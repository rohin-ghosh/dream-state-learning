"""Prepare immutable NODE5 parent metadata and config candidates, never activate."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
import time


ASSIGNMENTS = {
    'run1': ('A', 1), 'pilot': ('B', 2), 'repo_reader': ('C', 3),
    'C1': ('B', 2), 'C3': ('A', 1), 'C4': ('C', 3), 'C5': ('D', 3),
}
PEERS = (('C1', 'C3'), ('C4', 'C5'))
SCOPE = Path(__file__).resolve().parent
INVENTORY_SHA256 = 'ed03ce5bb26c4d5ddf9f7ba7f385e9a9b18bb496e2c9067dc4c9f649660c0947'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read_json(path):
    path = Path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 16 * 1024 * 1024,
                'bounded_regular_metadata')
        raw = handle.read()
        after = os.fstat(handle.fileno())
    current = path.stat(follow_symlinks=False)
    identities = {(entry.st_dev, entry.st_ino, entry.st_size, entry.st_mtime_ns,
                   entry.st_ctime_ns) for entry in (before, after, current)}
    require(len(identities) == 1, 'metadata_changed_during_read')
    return json.loads(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def summarize_ledger(entries, initial_cursor=0):
    cursor, pending, blockers, pins, objects = initial_cursor, [], [], [], []
    for entry in entries:
        source = entry['source']
        require(source.get('schema') in ('R153_COMMITTED_TRAIN_SNAPSHOT_V1',
                'R133_TRAIN_PARENT_SNAPSHOT_V1'), 'known_TRAIN_source_only')
        require(source.get('split', 'TRAIN') == 'TRAIN', 'TRAIN_only')
        count = source['response_count']
        require(type(count) is int and count >= 0, 'response_cursor_integer')
        cursor = max(cursor, count)
        pins.append(entry['source_pin'])
        result = entry.get('result')
        if result is None:
            blockers.append(dict(attempt=entry['attempt'], reason='UNSETTLED_ATTEMPT_NO_REPLAY'))
            continue
        pins.append(entry['result_pin'])
        if source['schema'] == 'R153_COMMITTED_TRAIN_SNAPSHOT_V1':
            require(result['source_sha256'] == entry['source_pin']['sha256'], 'result_source_pin')
        else:
            require(result['source_head_sha256'] == source['head_sha256'] and
                    result['source_response_count'] == count, 'legacy_result_source_binding')
        status = result['status']
        if status == 'PUBLICATION_UNKNOWN':
            blockers.append(dict(attempt=entry['attempt'], reason='UNCERTAIN_PUBLICATION_NO_REPLAY'))
        elif status == 'PUBLISHED':
            publication = result.get('publication', result.get('inbox_publication'))
            require(type(publication) is dict and all(key in publication for key in
                    ('id', 'path', 'sha256')), 'exact_publication_reference')
            delivery = entry.get('delivery')
            if delivery is None:
                pending.append(deepcopy(publication))
            else:
                require(delivery['result_sha256'] == entry['result_pin']['sha256'],
                        'delivery_result_binding')
                pins.append(entry['delivery_pin'])
                objects.append(dict(publication=deepcopy(publication),
                    object_id=result.get('object_id'), delivery_status=delivery.get('status'),
                    rendered_exposure_requires_independent_REQUEST_binding=True))
        elif status not in ('MISSING', 'SILENT', 'PROVIDER_FAILED', 'REFUSED', 'INVALID'):
            blockers.append(dict(attempt=entry['attempt'], reason='UNKNOWN_TERMINAL_STATUS', status=status))
        if entry.get('object_state_pin'):
            pins.append(entry['object_state_pin'])
    return dict(response_cursor_lower_bound=cursor, pending_publications=pending,
                prior_delivery_metadata=objects, preserved_metadata_pins=pins, blockers=blockers,
                recollect_under_exact_parent_takeover=True, state_cloned=False,
                new_exposure_proven=False)


def collect_ledger(output, config):
    entries = []
    directories = sorted(Path(output).glob('parent_*'))
    require(len(directories) <= 10000, 'bounded_parent_attempt_ledger')
    for directory in directories:
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt_directory')
        source, source_pin = read_json(directory / 'SOURCE.json')
        entry = dict(attempt=directory.name, source=source, source_pin=source_pin)
        for name, key in (('RESULT.json', 'result'), ('DELIVERED.json', 'delivery'),
                          ('OBJECT_STATE.json', 'object_state')):
            path = directory / name
            if path.exists():
                entry[key], entry[key + '_pin'] = read_json(path)
        entries.append(entry)
    return summarize_ledger(entries, config.get('start_after_response_count', 0))


def candidate(row, config, ledger):
    label = row['label']
    require(label in ASSIGNMENTS and 'C2' not in Path(config['root']).parts and
            '_C2_' not in config['root'], 'NODE5_scope_C2_excluded')
    require(config['node'] == 'ovx3', 'NODE5_only')
    arm, cadence = ASSIGNMENTS[label]
    proposed = deepcopy(config)
    proposed.update(cadence_responses=cadence, schedule_on='response',
                    start_after_response_count=ledger['response_cursor_lower_bound'])
    proposed.pop('start_after_request_count', None)
    if row['entry_kind'] == 'R169_FROZEN_SOURCE_AUTH_REFRESH':
        proposed['predecessor_output'] = row['output_path']
    return dict(schema='R175_NODE5_PARENT_TAKEOVER_CANDIDATE_V1', label=label,
        status='PREPARED_NOT_EXECUTABLE', arm=arm, response_cadence=cadence,
        candidate_config=proposed, predecessor=deepcopy(row), observed_state=ledger,
        must_rebind_predecessor_started_receipt=(row['entry_kind'] == 'R169_FROZEN_SOURCE_AUTH_REFRESH'),
        common_source_bundle=None, common_policy=None, long_parent_cap=None,
        first_parent_turn=None, first_rendered_REQUEST=None, three_sleep_start=None,
        no_auto_replay=True, no_child_restart=True, no_sleep_change=True)


def verify_parent(row):
    require(row['label'] in ASSIGNMENTS, 'C2_and_unknown_lanes_excluded')
    process = Path('/proc') / str(row['pid'])
    before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    command = (process / 'cmdline').read_bytes()
    config, pin = read_json(row['config']['path'])
    require(pin == row['config'], 'unchanged_actual_parent_config')
    after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] == str(row['start_ticks']) and
            after[0] not in ('T', 't', 'Z', 'X') and
            hashlib.sha256(command).hexdigest() == row['argv_sha256'] and
            command == (process / 'cmdline').read_bytes() and
            os.readlink(process / 'cwd') == row['cwd'], 'exact_live_parent_identity')
    return config


def patch_file(path, document):
    require(path.is_relative_to(SCOPE) and not path.exists(), 'new_own_scope_file_only')
    content = json.dumps(document, sort_keys=True, indent=2) + '\n'
    return ('*** Add File: ' + str(path) + '\n' +
            ''.join('+' + line + '\n' for line in content.splitlines()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    inventory, pin = read_json(args.inventory)
    require(pin['sha256'] == INVENTORY_SHA256, 'exact_inventory_binding')
    require(sorted(row['label'] for row in inventory['rows']) == sorted(ASSIGNMENTS),
            'exact_seven_parent_roster')
    stage = SCOPE / ('takeover_stage_' + str(time.time_ns()))
    patches, manifest = [], []
    for row in inventory['rows']:
        config = verify_parent(row)
        ledger = collect_ledger(row['output_path'], config)
        document = candidate(row, config, ledger)
        path = stage / row['label'] / 'TAKEOVER_CONFIG_CANDIDATE.json'
        patches.append(patch_file(path, document))
        manifest.append(dict(label=row['label'], arm=document['arm'],
            response_cadence=document['response_cadence'], path=str(path),
            response_cursor_lower_bound=ledger['response_cursor_lower_bound'],
            pending_publications=len(ledger['pending_publications']), blockers=ledger['blockers']))
    peers = dict(schema='R175_NODE5_STATE_ONLY_PEER_STAGING_V1', pairs=PEERS,
        excluded=['C2'], exchange_mode='EXPLICIT_EXCHANGE_ONLY', messages=[],
        automatic_full_thought_relay=False, source_state_payloads_selected=False,
        required_recipient_evidence=['attributed_prediction', 'actual_test_receipt',
                                     'recipient_own_restatement', 'rendered_TRAIN_REQUEST'],
        trainable_peer_text='recipient_own_restatement_only',
        peer_text_masking_runtime_verified=False, transmissions=0)
    patches.append(patch_file(stage / 'PEER_STATE_ONLY.json', peers))
    patches.append(patch_file(stage / 'READY.json', dict(
        schema='R175_NODE5_PARENT_STAGING_MANIFEST_V1', observed_unix=time.time(),
        inventory=pin, rows=manifest, main_source_bundle=None, activation_ready=False,
        activation_blocker='MAIN_COMMON_SOURCE_BUNDLE_AND_TEST_PINS_NOT_YET_SUPPLIED',
        no_wait_for_C2_success=True, configured_is_not_exposed=True,
        three_sleep_start_requires_first_actual_rendered_REQUEST=True,
        messages_sent=0, parent_signals_sent=0, child_restarts=0, sleep_changes=0)))
    print('*** Begin Patch\n' + ''.join(patches) + '*** End Patch')


if __name__ == '__main__':
    main()
