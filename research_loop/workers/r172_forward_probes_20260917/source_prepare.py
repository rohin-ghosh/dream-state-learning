"""Bounded source custody; imports only the copied CPU custody/queue helpers."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

import prep_common as common


ROOT = common.REMOTE_ROOT
MIB = 1024 ** 2


def limits(metadata, adapter, discovery=0):
    return dict(metadata=metadata, adapter=adapter, per_life=2 * common.GIB, discovery=discovery)


def original_plan_candidates(life):
    root = Path(life['proposed_storage_root'])
    paths = [root.parent / name for name in ('control1/PLAN.json', 'control/PLAN.json', 'PLAN.json')]
    paths += [root / 'PLAN.json', Path(life['snapshot_plan_ref']['path'])]
    if life.get('old_birth_plan'):
        paths.insert(0, Path(life['old_birth_plan']['path']))
    return list(dict.fromkeys(paths))


def identity_same(expected, actual):
    return all(str(expected[field]) == str(actual[field]) for field in ('pid', 'start_ticks', 'boot_id', 'uid'))


def discover(request):
    import native_custody
    output = ROOT / 'source_discovery' / request['node']
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    ledger = common.Ledger(output / 'ledger', limits(request['read_cap'], 0, request['read_cap']),
        [life['life_id'] for life in request['lives']])
    common.write(output / 'ONCE.json', dict(request=request, started_unix=time.time(), model_calls=0))
    ledger.reserve('bounded_native_proc_identity_reads', '_campaign', 'metadata', 2 * MIB, True)
    rows = []
    for life in sorted(request['lives'], key=lambda row: (not row['prior_registered'], row['life_id'])):
        row = dict(life_id=life['life_id'], status='DISCOVERY_HELD', observed_unix=time.time())
        try:
            identity, argv = native_custody.identity(life['snapshot_native_identity']['pid'])
            common.require(identity_same(life['snapshot_native_identity'], identity), 'fresh_native_identity_drift')
            candidates = original_plan_candidates(life)
            roots = [life['proposed_storage_root'], life['process_plan_root'],
                life['snapshot_config_ref']['path'], life['snapshot_plan_ref']['path'], *map(str, candidates)]
            reader = common.Reader(ledger, life['life_id'], 'discovery', roots, discovery=True)
            current_plan, plan_ref = reader.document(life['snapshot_plan_ref']['path'], limit=MIB)
            current_guard, guard_ref = reader.document(life['snapshot_config_ref']['path'], limit=MIB)
            common.require(plan_ref == life['snapshot_plan_ref'] and guard_ref == life['snapshot_config_ref'], 'current_PLAN_GUARD_pin_drift')
            common.require(current_plan['root'] in (life['process_plan_root'], life['proposed_storage_root']), 'current_exact_declared_root')
            common.require(identity['cwd'] == life['current_source_root'], 'current_source_cwd')
            births = []
            for path in candidates:
                if path.is_file():
                    document, reference = reader.document(path, limit=MIB)
                    if all(isinstance(document.get(field), str) for field in ('birth_prompt', 'system_prompt')):
                        births.append(reference)
            common.require(bool(births), 'no_original_birth_candidate')
            root = Path(life['proposed_storage_root'])
            files = [path for path in (root / 'stream/records').iterdir() if path.is_file()]
            journal_stat_bytes = sum(path.stat().st_size for path in files)
            initial = root / 'checkpoints/initial/adapter'
            adapter_files = [initial / name for name in ('adapter_model.safetensors', 'adapter_config.json', 'README.md')]
            adapter_bytes = 0
            for path in adapter_files:
                if path.exists():
                    common.require(stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink(), 'regular_initial_adapter_stat')
                    adapter_bytes += path.stat().st_size
            common.require(adapter_bytes > 0, 'initial_adapter_missing')
            after, unused = native_custody.identity(identity['pid'])
            common.require(identity_same(identity, after) and identity['argv_sha256'] == after['argv_sha256'], 'identity_changed_during_discovery')
            row.update(status='METADATA_CANDIDATE_NOT_ENROLLED', native_identity=identity,
                birth_candidates=births, current_plan_ref=plan_ref, current_guard_ref=guard_ref,
                journal_stat_bytes=journal_stat_bytes, initial_adapter_stat_bytes=adapter_bytes,
                metadata_read_cap=min(2 * common.GIB, journal_stat_bytes + 768 * MIB),
                adapter_read_cap=adapter_bytes * 8 + 32 * MIB,
                storage_alias_unverified=life['process_plan_root'] != life['proposed_storage_root'])
        except Exception as error:
            row['error_type'] = type(error).__name__
            row['reason'] = str(error) if isinstance(error, ValueError) else 'BOUNDED_SOURCE_DISCOVERY_FAILED'
        rows.append(row)
        common.write(output / (life['life_id'] + '.json'), row)
    result = dict(status='DISCOVERY_METADATA_ONLY', rows=rows, observed_unix=time.time(),
        bytes_charged=ledger.totals()['metadata'], model_calls=0, provider_calls=0)
    common.write(output / 'COMPLETE.json', result)
    print(json.dumps(result))


def enroll(request):
    import native_custody
    from gpu import orch_r167_object_probe_queue as queue
    protocol = queue.protocol
    life = request['life']
    discovery = request['discovery']
    name = life['life_id']
    directory = ROOT / 'source_controls' / name
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    common.write(directory / 'ONCE.json', dict(request=request, started_unix=time.time(), model_calls=0))
    custody_ledger = common.Ledger(directory / 'custody_ledger', limits(128 * MIB, 0), [name])
    custody_ledger.reserve('native_custody_bounded96MiB_plus_proc', name, 'metadata', 100 * MIB)
    result = dict(life_id=name, status='SOURCE_CUSTODY_HELD', model_calls=0, observed_unix=time.time())
    try:
        selected = discovery['birth_candidates'][0]
        native_life = dict(life_id=name, node=life['node'], storage_root=life['proposed_storage_root'],
            process_plan_root=life['process_plan_root'], inventory_identity=discovery['native_identity'], birth_plan=selected)
        observation = native_custody.observe_life(native_life)
        original_ref = common.write(directory / 'OBSERVATION_ORIGINAL.json', observation)
        common.require(observation['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
            and observation.get('identity_rechecked') is True
            and identity_same(discovery['native_identity'], observation['native_identity']), 'fresh_identity_completed_frontier_required')
        if not observation.get('registry_plan_birth_context_matches'):
            matches = [entry['reference'] for entry in observation.get('original_plan_candidates', [])
                if entry['root_matches'] and entry['birth_context_matches']]
            common.require(bool(matches), 'original_INITIAL_birth_match_missing')
            selected = matches[0]
            observation = dict(observation, registry_birth_plan=selected, registry_plan_birth_context_matches=True,
                original_observation_ref=original_ref, birth_selection='EXACT_INITIAL_MATCH_FROM_SAME_BOUNDED_OBSERVATION')
        if name == 'C5':
            common.require(request.get('exact_recovery_release_verified') is True, 'C5_exact_recovery_release_witness_missing')
        if life['process_plan_root'] != life['proposed_storage_root']:
            common.require(request.get('exact_storage_alias_verified') is True, 'storage_alias_witness_missing')
        observed_ref = common.write(directory / 'FRESH_CUSTODY.json', observation)
        frozen = time.time()
        first_sleep = observation['last_completed_sleep'] + 1
        source_root = Path(life['proposed_storage_root'])
        journal = {field: observation['journal'][field] for field in ('path', 'sha256')}
        authority = dict(schema=queue.SCHEMA, status='MAIN_SOURCE_READ_COPY_GO', life_id=name,
            source_root=str(source_root), birth_plan={field:selected[field] for field in ('path','sha256')},
            journal=journal, milestones=[0, first_sleep, first_sleep+1, first_sleep+2],
            metadata_read_cap=request['metadata_read_cap'] - 128 * MIB,
            adapter_read_cap=request['adapter_read_cap'], registration_observation=observed_ref,
            frozen_unix=frozen, permissions=['metadata_discovery', 'adapter_only_copy'], read_end_unix=common.END,
            preparation_scope=request['scope_ref'], global_allocation=request['allocation_ref'], gpu_GO=False)
        authority_ref = common.write(directory / 'MAIN_SOURCE_READ_COPY_GO.json', authority)
        root = ROOT / 'lives' / name
        queue_plan = dict(schema=queue.SCHEMA, queue_root=str(root), life_id=name,
            source_root=str(source_root), birth_plan=authority['birth_plan'], journal=journal,
            source_authority=authority_ref, first_sleep=first_sleep, sleep_count=3, frozen_unix=frozen,
            probes=list(queue.PROBES), conditions=list(queue.CONDITIONS), base_sha256=queue.BASE,
            model_call_cap=24, generated_token_cap=12288, metadata_read_cap=authority['metadata_read_cap'],
            adapter_read_cap=authority['adapter_read_cap'])
        queue_ref = common.write(directory / 'QUEUE_PLAN.json', queue_plan)
        queue.initialize(queue_ref['path'])
        witness_record = Path(observation['completed_boundary']['record']['record']['path'])
        reader = queue.Reader(queue_plan, root, source_root, [witness_record, Path(selected['path'])], 'metadata')
        record, record_ref = reader.document(witness_record)
        birth, birth_ref = reader.document(selected['path'])
        common.require(birth_ref == authority['birth_plan'], 'selected_birth_hash_reverified')
        state = record['document']['resume_state']
        common.require(state['sha256'] == protocol.digest(state['state']), 'private_witness_state_hash')
        context = {field:birth[field] for field in ('birth_prompt','system_prompt')}
        history = state['state']['history']
        common.require(all(history[field] == context[field] for field in context), 'private_witness_original_context')
        events = history['events']
        common.require(all(event.get('split') == 'TRAIN' and event.get('origin') == 'TRAIN_COLLECTION' for event in events), 'TRAIN_only_witness')
        witnesses = [dict(event_index=index, text=event['text'], text_sha256=hashlib.sha256(event['text'].encode()).hexdigest())
            for index,event in enumerate(events) if event.get('actor') == 'child']
        evidence = common.write(root / 'TRAIN_WITNESSES.private.json', dict(witnesses=witnesses, context=context,
            parent_access=False, lexical='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE', source_record=record_ref))
        common.write(root / 'TRAIN_FREEZE.json', dict(status='PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE',
            evidence=evidence, record=record_ref, birth=birth_ref, frozen_unix=time.time(), model_calls=0))
        result.update(status='REGISTERED_PRIVATE_CUSTODY_NO_GPU_GO', frontier=first_sleep-1,
            fixed_sleeps=[first_sleep,first_sleep+1,first_sleep+2], frozen_unix=frozen,
            queue_ref=queue_ref, custody_ref=observed_ref, source_root=str(source_root))
    except Exception as error:
        result['error_type'] = type(error).__name__
        result['reason'] = str(error) if isinstance(error, ValueError) else 'CUSTODY_PREPARATION_FAILED_PRESERVED'
    common.write(directory / 'RESULT.json', result)
    print(json.dumps(result))


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('discover', 'enroll'))
    parser.add_argument('--request', required=True)
    arguments = parser.parse_args()
    request = common.read(arguments.request)
    common.scope(ROOT / 'control/PREPARATION_SCOPE.json', ROOT / 'control/PROPOSAL.json')
    common.require(common.ref(__file__)['sha256'] == request['source_sha256'], 'frozen_preparation_worker_source')
    (discover if arguments.action == 'discover' else enroll)(request)


if __name__ == '__main__':
    main()
