"""Bounded metadata observer and final CPU provenance for admitted A40R7."""

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from gpu import orch_r145_a40r7_recovery as recovery


CONTROL = recovery.BASE / 'control_r145_a40r7_20260916t1630z_readmit1'
ORIGINAL_CONTROL = recovery.BASE / 'control_r145_a40r7_20260916t1630z'
NATIVE_PID = 2456537


def records_after(start):
    directory = recovery.ROOT / 'stream/records'
    records = []
    for path in sorted(directory.glob('*.json')):
        if path.name.endswith('.intent.json') or int(path.stem) < start:
            continue
        records.append(json.loads(recovery.raw(path)))
    return records


def status():
    records = records_after(1375)
    updates = [record for record in records if record['kind'] == 'UPDATE'
               and record['document'].get('r145_a40r7_attempt')]
    markers = ('00_REQUEST.json', '00_RESPONSE.json', '01_REQUEST.json', '01_RESPONSE.json',
               'GENERATIONS_VERIFIED.json', 'FAILED.json', 'RECOMPUTE_STARTED.json',
               'RECOMPUTE_FAILED.json', 'ACTUAL_SLEEP_MEMORY.json', 'SLEEP_RECOMPUTED.json')
    result = dict(observed_unix=time.time(), native_pid=NATIVE_PID,
        native_exists=Path('/proc', str(NATIVE_PID)).exists(), exit_exists=(CONTROL / 'EXIT.json').exists(),
        head_index=records[-1]['index'] if records else 1374, head_kind=records[-1]['kind'] if records else 'UPDATE',
        replacement_updates=len(updates), last_optimizer_step=updates[-1]['document']['optimizer_step'] if updates else None,
        markers=[name for name in markers if (recovery.RECOVERY / name).exists()],
        milestones=[dict(index=record['index'], kind=record['kind'], optimizer_steps=record['document'].get('optimizer_steps'))
                    for record in records if record['kind'] in ('SLEEP_COMPLETE', 'LOADED', 'COMMITTED')])
    for name in ('GENERATIONS_VERIFIED.json', 'FAILED.json', 'RECOMPUTE_FAILED.json', 'SLEEP_RECOMPUTED.json'):
        path = recovery.RECOVERY / name
        if path.exists():
            value = json.loads(recovery.raw(path))
            result[name] = {key: value.get(key) for key in ('status', 'matched_generations', 'optimizer_steps',
                'optimizer_updates', 'historical_abandoned_updates', 'finished_unix', 'error_type', 'error')}
    print(json.dumps(result, indent=2), flush=True)


def final():
    from gpu.orch_r125_continual_native import NativeChild
    records = records_after(0)
    completed = next(record for record in records[1375:] if record['kind'] == 'SLEEP_COMPLETE'
                     and record['document']['cycle'] == 23)
    receipt = completed['document']
    checkpoint = receipt['checkpoint']
    NativeChild.verify_checkpoint(checkpoint)
    recovery.require(checkpoint['optimizer_steps'] == 1242 and receipt['optimizer_steps'] == 76,
                     'durable1242_exact76_replacement_updates')
    eligibility = records[1373]['document']
    expected_sources = eligibility['new_row_sha256'] * 16 + eligibility['rehearsal_row_sha256']
    updates = [record['document'] for record in records[1375:completed['index']] if record['kind'] == 'UPDATE']
    recovery.require([item['optimizer_step'] for item in updates] == list(range(1167,1243))
        and [item['source_sha256'] for item in updates] == expected_sources, 'exact_contiguous_original_schedule')
    recovery.require(all(item['r145_a40r7_original_abandoned_record'] == 1374 for item in updates)
        and Counter(expected_sources) == receipt['presentations'], 'no_historical_update_double_count')
    corrected = [record['document'] for record in records[1375:completed['index']] if record['kind'] == 'TARGET_ELIGIBILITY']
    recovery.require(corrected == [eligibility] and receipt['excluded_rows'] == [], 'no_target_or_rehearsal_change')
    manifest = json.loads(recovery.raw(ORIGINAL_CONTROL / 'MANIFEST.json'))
    config = json.loads(recovery.raw(CONTROL / 'GUARD.json'))
    recovery.verify_manifest(manifest,config['r145_a40r7_acknowledgment'])
    metadata = [record['document'] for record in records[1375:completed['index']] if record['kind'] == 'CHECKPOINT_METADATA']
    from gpu.orch_r145_suffix_boundary import POLICY
    policy = dict(runtime_memory_policy=POLICY,runtime_sha256=manifest['memory']['runtime']['sha256'],
                  GPU_validation_sha256=manifest['memory']['proof']['sha256'])
    recovery.require(len(metadata) == 2 and metadata[1] == policy
        and metadata[0]['r145_a40r7_recovery']['abandoned_update_record'] == 1374,
        'one_recovery_accounting_and_one_bound_runtime_metadata')
    previous = records[0]['previous_sha256']
    for index,record in enumerate(records):
        recovery.require(record['index'] == index and record['previous_sha256'] == previous
            and recovery.digest({key:value for key,value in record.items() if key != 'sha256'}) == record['sha256'],
            'full_original_and_recovery_chain_valid')
        previous = record['sha256']
    recovery.require(records[1374]['sha256'] == recovery.HEAD, 'original1375_prefix_preserved')
    recovery.pinned_evidence()
    loaded = next(record for record in records[completed['index']+1:] if record['kind'] == 'LOADED')
    recovery.require(loaded['document']['pid'] == NATIVE_PID and loaded['document']['resume'] is True
        and loaded['document']['optimizer_steps'] == 1242, 'actual_native_saved_resume1242')
    committed = next(record for record in records[loaded['index']+1:] if record['kind'] == 'COMMITTED')
    request_record, response_record = records[committed['index']-2:committed['index']]
    recovery.require(request_record['kind'] == 'REQUEST' and response_record['kind'] == 'RESPONSE', 'first_continuation_chain')
    request = {key:value for key,value in request_record['document'].items() if key != 'resume_state'}
    response = response_record['document']
    recovery.require(request['split'] == 'TRAIN' and recovery.digest(request) == response['request_sha256']
        and recovery.digest(response) == committed['document']['source_sha256'], 'actual_TRAIN_request_response_commit')
    recovery.require(response['response']['adapter_state_sha256'] == checkpoint['adapter_state_sha256'], 'saved_adapter_continuation')
    original_state = records[1372]['document']['resume_state']['state']
    continued_state = committed['document']['state']['state']
    recovery.require(continued_state['rows'][:46] == original_state['rows'] and continued_state['sleep_frontier'] == 46,
                     'all46_original_rows_preserved_and_frontier_advanced')
    arguments = Path('/proc',str(NATIVE_PID),'cmdline').read_bytes().split(b'\0')
    recovery.require(b'gpu.orch_r145_a40r7_recovery' in arguments and str(CONTROL / 'GUARD.json').encode() in arguments
        and not (CONTROL / 'EXIT.json').exists(), 'same_live_admitted_native_without_exit')
    result = dict(status='SLEEP23_SAVED_AND_FIRST_TRAIN_CONTINUATION_VERIFIED', native_pid=NATIVE_PID,
        optimizer_steps=1242, replacement_updates=76, historical_abandoned_updates=1,
        checkpoint_commit_sha256=recovery.sha(recovery.ROOT / 'checkpoints/sleep_000023/COMMIT.json'),
        sleep_complete_index=completed['index'], sleep_complete_sha256=completed['sha256'],
        checkpoint_created_unix=checkpoint['created_unix'], loaded_index=loaded['index'], loaded_unix=loaded['document']['loaded_unix'],
        first_request_index=request_record['index'], first_response_index=response_record['index'],
        first_commit_index=committed['index'], first_commit_sha256=committed['sha256'],
        first_generated_tokens=len(response['response']['token_ids']), original1375_chain_preserved=True,
        all46_original_rows_preserved=True, original_eligibility_and_rehearsal_preserved=True,
        held_contents_read=False, parents_unchanged=True, observed_unix=time.time())
    recovery.save(CONTROL / 'RECOVERY_COMPLETE_OBSERVED.json',result)
    recovery.save_bytes(CONTROL / 'RECOVERED_NATIVE_LOADED.json',
        recovery.raw(recovery.ROOT / 'stream/records' / f"{loaded['index']:020d}.json"))
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true')
    arguments = parser.parse_args()
    if arguments.final:
        final()
    else:
        status()
