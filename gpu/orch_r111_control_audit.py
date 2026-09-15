"""Read-only availability and provenance reduction for one canonical control triple."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


ARMS = ('GUIDED', 'UNPARENTED', 'NO_LORA')
SOURCES = ('gpu/orch_route_parent_campaign_canonical.py', 'gpu/orch_route_parent_campaign_run.py',
           'organism_v6/orch_route_parent_campaign_canonical.py', 'organism_v6/orch_route_parent_campaign.py')


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def identity_summary(identity, cache):
    files = []
    for name, expected in identity.get('files', []):
        path = Path(identity['path']) / name
        key = (str(path), expected)
        if key not in cache:
            cache[key] = path.is_file() and sha(path) == expected
        files.append(dict(path=str(path), expected_sha256=expected, verified=cache[key]))
    base_only = identity.get('kind') == 'FROZEN_QWEN_BASE_NO_ADAPTER'
    return dict(kind=identity.get('kind', 'ADAPTER'), state_sha256=identity['state_sha256'],
        base_sha256=identity['base_sha256'], files=files,
        saved_files_verified=all(item['verified'] for item in files) if files else None,
        explicit_no_adapter=base_only and identity.get('path') is None and identity.get('files') == [])


def terminal(folder):
    complete, failed = folder/'COMPLETE.json', folder/'FAILED.json'
    if complete.exists() and failed.exists():
        return dict(status='CONFLICTING_TERMINALS', complete=ref(complete), failed=ref(failed))
    path = complete if complete.exists() else failed if failed.exists() else None
    if path is None:
        return dict(status='REQUEST_WITHOUT_TERMINAL' if (folder/'REQUEST.json').exists() else 'NOT_STARTED')
    value = read(path)
    result = dict(status='COMPLETE' if path == complete else 'FAILED', receipt=ref(path),
                  finished_unix=value.get('finished_unix'))
    if path == failed:
        result.update(error_type=value.get('error_type'),
                      error_sha256=hashlib.sha256(str(value.get('error', '')).encode()).hexdigest())
    return result


def audit(root):
    root = Path(root)
    prepared = read(root/'PREPARE.json')
    cache, arms = {}, {}
    for arm in ARMS:
        cycles = []
        for cycle in range(prepared['caps']['cycles']+1):
            folder = root/arm/f'cycle{cycle}'
            row = dict(cycle=cycle, phases={phase: terminal(folder/phase)
                for phase in ('experience', 'sleep', 'readout')})
            sleep = None
            if row['phases']['sleep']['status'] == 'COMPLETE':
                sleep = read(folder/'sleep/COMPLETE.json')
                row['sleep'] = dict(updates=sleep['updates'], fits=sleep.get('fits'),
                    reason=sleep.get('reason'),
                    input=identity_summary(sleep['input_adapter'], cache),
                    output=identity_summary(sleep['output_adapter'], cache),
                    same_child=sleep['input_adapter'] == sleep['output_adapter'])
            if row['phases']['readout']['status'] == 'COMPLETE':
                record = read(folder/'readout/COMPLETE.json')
                loaded_path = folder/'readout/LOADED.json'
                loaded = read(loaded_path) if loaded_path.exists() else None
                episodes = sorted((folder/'readout').glob('EPISODE_*.json'))
                row['readout'] = dict(parent_free=record.get('parent_free'),
                    input=identity_summary(record['input_adapter'], cache),
                    task_hashes=[digest(read(path)['task']) for path in episodes],
                    episode_receipts=[ref(path) for path in episodes],
                    fresh_process_vs_sleep=record['process'] != sleep['process'] if sleep else None,
                    exact_saved_child=record['input_adapter'] == sleep['output_adapter'] if sleep else None,
                    loaded_identity_matches=loaded['observed'] == record['input_adapter'] if loaded else None,
                    loaded_parent_absent=loaded.get('parent_present') is False if loaded else None,
                    loaded_receipt=ref(loaded_path) if loaded else None,
                    ancillary_successes=record.get('successes'),
                    ancillary_episode_count=record.get('all_episode_count'),
                    world_denominator=record.get('world_denominator'))
            cycles.append(row)
        dispatch = read(root/f'DISPATCH_{arm}.json')
        ledger = root/f'CALLS_PARENT_{arm}.jsonl'
        parent_charges = len(ledger.read_bytes().splitlines()) if ledger.exists() else 0
        completed_sleeps = [row for row in cycles if 'sleep' in row]
        completed_readouts = [row for row in cycles if 'readout' in row]
        arms[arm] = dict(guard=terminal(root/(arm+'_GUARD')), dispatch=ref(root/f'DISPATCH_{arm}.json'),
            original_dispatch_pid=dispatch['pid'], original_dispatch_pid_present=Path('/proc', str(dispatch['pid'])).exists(),
            physical_index=dispatch['physical_index'], allocation_is_not_current_occupancy=True,
            parent_calls_charged=parent_charges, parent_ledger=ref(ledger) if ledger.exists() else None,
            latest_sleep_cycle=completed_sleeps[-1]['cycle'] if completed_sleeps else None,
            latest_readout_cycle=completed_readouts[-1]['cycle'] if completed_readouts else None,
            saved_updates_all_completed=sum(row['sleep']['updates'] for row in completed_sleeps), cycles=cycles)
    matched = sorted(set.intersection(*[{row['cycle'] for row in arms[arm]['cycles'] if 'readout' in row}
                                       for arm in ARMS]))
    matched_table = []
    for cycle in matched:
        rows = {arm: next(row for row in arms[arm]['cycles'] if row['cycle'] == cycle) for arm in ARMS}
        hashes = [row['readout']['task_hashes'] for row in rows.values()]
        matched_table.append(dict(cycle=cycle, task_hashes_equal=all(value == hashes[0] for value in hashes),
            task_hashes=hashes[0], saved_updates={arm: row.get('sleep', {}).get('updates') for arm, row in rows.items()},
            ancillary_successes={arm: row['readout']['ancillary_successes'] for arm, row in rows.items()},
            episode_denominators={arm: row['readout']['ancillary_episode_count'] for arm, row in rows.items()},
            post_sleep_joins_verified=all(row['readout']['fresh_process_vs_sleep'] is True
                and row['readout']['exact_saved_child'] is True and row['readout']['parent_free'] is True
                and row['readout']['loaded_parent_absent'] is True
                and row['readout']['loaded_identity_matches'] is True for row in rows.values()) if cycle else None))
    updates = {arm: sum(row['saved_updates'][arm] or 0 for row in matched_table if row['cycle']) for arm in ARMS}
    initial = {arm: arms[arm]['cycles'][0]['readout']['input'] for arm in ARMS}
    overlaps = [len(set(before['task_hashes']) & set(after['task_hashes']))
                for before, after in zip(matched_table, matched_table[1:])]
    return dict(schema='R118_ONE_CANONICAL_CONTROL_AVAILABILITY_V1', observed_unix=time.time(),
        observed_utc=datetime.now(timezone.utc).isoformat(), root=str(root), reducer=ref(__file__),
        task_hash_serialization='json.dumps(sort_keys=True, default separators), matching Main1211',
        prepare=ref(root/'PREPARE.json'), cohort=ref(root/'COHORT.json'),
        cohort_matches_prepared=sha(root/'COHORT.json') == prepared['inputs']['COHORT.json'],
        execution_source_hashes_bound_by_PREPARE={name: prepared['source_files'][name] for name in SOURCES},
        current_runtime_source_tree_revalidation=False, source_receipt_scope='Historical execution binding; no claim current mutable checkout is unchanged',
        initial=initial, arms=arms, matched_cycles=matched_table, matched_saved_updates=updates,
        adjacent_readout_task_overlaps=overlaps,
        comparability=dict(guided_unparented_same_initial_state=initial['GUIDED']['state_sha256'] == initial['UNPARENTED']['state_sha256'],
            no_lora_is_frozen_base_not_adapter_matched_twin=initial['NO_LORA']['explicit_no_adapter'],
            guided_unparented_realized_update_doses_equal=updates['GUIDED'] == updates['UNPARENTED'],
            same_task_retention_test=False, retained_thinking_claim_established=False,
            current_pooled_learner_matched_control=False,
            missing_evidence=['adapter-matched frozen twin for isolating later adaptation',
                'matched realized training exposure', 'repeated common-task retention readout',
                'validated retained-thinking measure', 'matched controls for the later shared pooled lineage']),
        new_native_calls=0, new_provider_calls=0, new_judge_calls=0, raw_exported=False,
        claim='Availability and provenance only; ancillary outcomes do not establish retained thinking gains')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = audit(arguments.root)
    with arguments.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(output=ref(arguments.output), arms={arm: {key: result['arms'][arm][key]
        for key in ('latest_sleep_cycle', 'latest_readout_cycle', 'saved_updates_all_completed',
                    'original_dispatch_pid_present')} for arm in ARMS}, matched_saved_updates=result['matched_saved_updates'],
        joins=[row['post_sleep_joins_verified'] for row in result['matched_cycles']])))
