"""Source-only fleet custody/capture; no model, judge, or GPU dispatch interface."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import time

from gpu import orch_r167_object_probe_queue as queue


protocol = queue.protocol
SCHEMA = 'R167_FLEET_SOURCE_GENERATION2_V1'
GIB = 1024 ** 3
MIB = 1024 ** 2
OBSERVATION_RESERVATION = 96 * MIB
HEADROOM = 256 * MIB
require = protocol.require


def reference(value):
    return {name: value[name] for name in ('path', 'sha256')}


def stat_life(life):
    source = protocol.regular(life['storage_root'])
    directory = protocol.regular(source / 'stream/records')
    metadata_bytes = 0
    files = 0
    for entry in directory.iterdir():
        require(files < 20000, 'bounded_journal_inventory')
        require(re.fullmatch(r'[0-9]{20}(?:\.intent)?\.json', entry.name), 'TRAIN_record_names_only')
        info = entry.lstat()
        require(stat.S_ISREG(info.st_mode), 'no_source_symlink')
        metadata_bytes += info.st_size
        files += 1
    initial = queue.checkpoint_path(source, 0)
    initial_adapter_bytes = 0
    for filename in ('adapter_model.safetensors', 'adapter_config.json', 'README.md'):
        path = protocol.regular(initial.parent / 'adapter' / filename)
        if path.exists():
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode), 'no_adapter_symlink')
            initial_adapter_bytes += info.st_size
    require(initial.is_file() and initial_adapter_bytes > 0, 'initial_baseline_missing')
    return dict(life_id=life['life_id'], source_root=str(source), observed_unix=time.time(),
        journal_stat_bytes=metadata_bytes, journal_file_count=files,
        initial_adapter_stat_bytes=initial_adapter_bytes, source_content_bytes_read=0)


def allocation(statistics, prior):
    require(set(prior) == {'metadata', 'adapter'} and all(type(value) is int and value >= 0
            for value in prior.values()), 'explicit_prior_read_charges')
    metadata = prior['metadata'] + statistics['journal_stat_bytes'] + OBSERVATION_RESERVATION + HEADROOM
    adapter = prior['adapter'] + statistics['initial_adapter_stat_bytes'] * 8 + 16 * MIB
    require(metadata <= 2 * GIB and adapter <= 2 * GIB, 'per_life_2GiB_cap')
    return dict(metadata_read_cap=metadata, adapter_read_cap=adapter, prior_charges=prior,
        observation_reservation=OBSERVATION_RESERVATION, metadata_headroom=HEADROOM,
        adapter_hops_reserved=2, checkpoints_reserved=4, stat_evidence=statistics)


def validate(path):
    plan = protocol.read(path)
    require(plan['schema'] == SCHEMA, 'exact_new_generation')
    original = protocol.bound(plan['original_registry'])
    require(plan['call_cap'] == original['model_call_cap'] == 504
        and plan['token_cap'] == original['generated_token_cap'] == 258048
        and plan['physical_slots'] == original['physical_slots'] == [0, 1]
        and plan['hard_end_unix'] == original['hard_end_unix'] == 1789659000,
        'unchanged_instrument_schedule_caps')
    require(plan['metadata_cap'] == plan['adapter_cap'] == 16 * GIB, 'new_read_ceiling_only')
    require(plan['probes'] == list(queue.PROBES) and plan['conditions'] == list(queue.CONDITIONS), 'fixed_probes')
    for name in ('scope', 'amendment'):
        require(protocol.sha(plan[name]['path']) == plan[name]['sha256'], 'exact_Main_scope_bytes')
    source = Path(__file__).resolve().parent
    require(str(source) == plan['runtime_root'], 'actual_frozen_pipeline_source')
    for name, checksum in plan['sources'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and protocol.sha(source / name) == checksum, 'immutable_source_pin')
    require(protocol.sha(__file__) == plan['sources']['fleet_source_pipeline.py']
        and Path(queue.__file__).resolve() == source / 'gpu/orch_r167_object_probe_queue.py', 'actual_queue_source')
    require(len(plan['lives']) == 21 and [life['life_id'] for life in plan['lives']] ==
        [life['life_id'] for life in original['lives']], 'all21_preserved_no_selection')
    for life, registered in zip(plan['lives'], original['lives']):
        require(all(life[field] == registered[field] for field in ('life_id', 'node', 'storage_root', 'process_plan_root')),
            'same_registered_identity_roots')
        if life['status'] != 'SOURCE_CANDIDATE':
            require(life['status'] == 'MISSING_CUSTODY_NOT_NEGATIVE', 'missing_not_negative')
            continue
        require(life['allocation'] == allocation(life['allocation']['stat_evidence'], life['allocation']['prior_charges']),
            'stat_based_finite_allocations')
        require(life['birth_plan']['path'].startswith('/localhome/local-rohing/'), 'explicit_birth_source')
        for evidence in life['evidence']:
            protocol.bound(evidence)
    eligible = [life for life in plan['lives'] if life['status'] == 'SOURCE_CANDIDATE']
    missing = [life for life in plan['lives'] if life['status'] != 'SOURCE_CANDIDATE']
    require(sum(life['allocation']['metadata_read_cap'] for life in eligible)
        + sum(life['prior_charges']['metadata'] for life in missing) <= plan['metadata_cap']
        and sum(life['allocation']['adapter_read_cap'] for life in eligible)
        + sum(life['prior_charges']['adapter'] for life in missing) <= plan['adapter_cap'], 'aggregate_read_caps')
    require(plan['registration_model_calls'] == 0 and plan['GPU_authorized'] is False, 'source_only_not_GPU_GO')
    return plan


def namespace(plan, life):
    root = protocol.regular(plan['queue_root'])
    source = protocol.regular(life['storage_root'])
    require(root.is_absolute() and root.name == 'orch_r167_fleet_20260917_generation2'
        and not root.is_relative_to(source) and not source.is_relative_to(root), 'private_new_namespace')
    return root / 'lives' / life['life_id']


def exact_identity(expected, actual):
    return all(str(expected[field]) == str(actual[field]) for field in ('pid', 'start_ticks', 'boot_id'))


def original_language_witnesses(record, context):
    wrapped = record['document']['resume_state']
    require(wrapped['sha256'] == protocol.digest(wrapped['state']), 'TRAIN_state_digest')
    history = wrapped['state']['history']
    require(all(history[field] == context[field] for field in context), 'unchanged_original_birth')
    events = history['events']
    require(all(event.get('split') == 'TRAIN' and event.get('origin') == 'TRAIN_COLLECTION' for event in events),
        'no_evaluation_or_parent_history')
    witnesses = [dict(event_index=index, text=event['text'], text_sha256=hashlib.sha256(event['text'].encode()).hexdigest())
        for index, event in enumerate(events) if event.get('actor') == 'child']
    return dict(schema=SCHEMA, witnesses=witnesses, original_language_preserved=True,
        lexical_instrument='NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE',
        semantic_status='TRAIN_ONLY_EVIDENCE_FROZEN_BEFORE_OUTPUTS_NOT_ADJUDICATED',
        context=context, probes=list(queue.PROBES), source_record_sha256=protocol.digest(record),
        parent_access=False)


def prepare_life(plan, life):
    import native_custody
    require(protocol.sha(native_custody.__file__) == plan['sources']['native_custody.py'], 'actual_custody_helper')
    require(time.time() < plan['hard_end_unix'], 'source_scope_expired')
    root = namespace(plan, life)
    root.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    control = root.parent.parent / 'source_controls' / life['life_id']
    control.mkdir(parents=True, mode=0o700, exist_ok=False)
    protocol.write(control / 'ONCE.json', dict(life_id=life['life_id'], started_unix=time.time(), model_calls=0))
    protocol.write(control / 'OBSERVATION_READ_RESERVED.json', dict(kind='metadata',
        reserved_bytes=OBSERVATION_RESERVATION, failures_charged=True))
    observation = native_custody.observe_life(dict(life, prior_metadata_bytes=0))
    observed_ref = protocol.write(control / 'FRESH_CUSTODY.json', observation)
    require(observation['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
        and observation.get('identity_rechecked') is True
        and observation.get('registry_plan_birth_context_matches') is True
        and exact_identity(life['inventory_identity'], observation['native_identity']), 'fresh_exact_identity_birth_custody')
    frozen = time.time()
    first_sleep = observation['last_completed_sleep'] + 1
    authority = dict(schema=queue.SCHEMA, status='MAIN_SOURCE_READ_COPY_GO', life_id=life['life_id'],
        source_root=life['storage_root'], birth_plan=life['birth_plan'], journal=reference(observation['journal']),
        milestones=[0, first_sleep, first_sleep+1, first_sleep+2],
        metadata_read_cap=life['allocation']['metadata_read_cap'], adapter_read_cap=life['allocation']['adapter_read_cap'],
        registration_observation=observed_ref, frozen_unix=frozen,
        permissions=['metadata_discovery', 'adapter_only_copy'], read_end_unix=plan['hard_end_unix'])
    authority_ref = protocol.write(control / 'MAIN_SOURCE_READ_COPY_GO.json', authority)
    queue_plan = dict(schema=queue.SCHEMA, queue_root=str(root), life_id=life['life_id'], source_root=life['storage_root'],
        birth_plan=life['birth_plan'], journal=authority['journal'], source_authority=authority_ref,
        first_sleep=first_sleep, sleep_count=3, frozen_unix=frozen, probes=list(queue.PROBES), conditions=list(queue.CONDITIONS),
        base_sha256=queue.BASE, model_call_cap=24, generated_token_cap=12288,
        metadata_read_cap=authority['metadata_read_cap'], adapter_read_cap=authority['adapter_read_cap'])
    queue_ref = protocol.write(control / 'QUEUE_PLAN.json', queue_plan)
    queue.initialize(queue_ref['path'])
    for kind in ('metadata', 'adapter'):
        charged = life['allocation']['prior_charges'][kind] + (OBSERVATION_RESERVATION if kind == 'metadata' else 0)
        protocol.write(root / 'reads' / ('CARRIED_' + kind + '.json'), dict(kind=kind, reserved_bytes=charged,
            prior_charges=life['allocation']['prior_charges'][kind], observed_ref=observed_ref))
    boundary = observation['completed_boundary']['record']['record']
    reader = queue.Reader(queue_plan, root, Path(life['storage_root']),
        [Path(boundary['path']), Path(life['birth_plan']['path'])], 'metadata')
    record, record_ref = reader.document(boundary['path'])
    birth, birth_ref = reader.document(life['birth_plan']['path'])
    require(record_ref == reference(boundary) and birth_ref == life['birth_plan'], 'unchanged_evidence_at_freeze')
    context = {field: birth[field] for field in ('system_prompt', 'birth_prompt')}
    evidence = original_language_witnesses(record, context)
    evidence_ref = protocol.write(root / 'TRAIN_WITNESSES.private.json', evidence)
    protocol.write(root / 'TRAIN_FREEZE.json', dict(status='PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE',
        evidence=evidence_ref, record=record_ref, birth=birth_ref, frozen_unix=time.time(), model_calls=0))
    return queue_ref


def capture_available(queue_path):
    queue_plan, root, unused_source, unused_authority = queue.initialized(queue_path, True)
    queue.discover(queue_path, max_records=32)
    for sleep in queue.milestones(queue_plan):
        if (root / 'boundaries' / f'{sleep:06d}.json').exists() and not (root / 'captures' / f'{sleep:06d}').exists():
            queue.capture(queue_path, sleep)
    return queue.status(queue_path)


def run_node(path, node):
    plan = validate(path)
    lives = [life for life in plan['lives'] if life['node'] == node and life['status'] == 'SOURCE_CANDIDATE']
    require(lives and len({life['hostname_sha256'] for life in lives}) == 1
        and hashlib.sha256(socket.gethostname().encode()).hexdigest() == lives[0]['hostname_sha256'], 'exact_source_node')
    os.umask(0o077)
    root = Path(plan['queue_root'])
    operation = root / 'operations' / node
    operation.mkdir(parents=True, mode=0o700, exist_ok=False)
    protocol.write(operation / 'ONCE.json', dict(plan=protocol.ref(path), started_unix=time.time(), model_calls=0))
    active = {}
    for life in lives:
        try:
            queue_ref = prepare_life(plan, life)
            active[life['life_id']] = queue_ref
            report = capture_available(queue_ref['path'])
            protocol.write(operation / (life['life_id'] + '.INITIAL_PROGRESS.json'), report)
            print(json.dumps(dict(report, life_id=life['life_id'], operation='QUEUE_STARTED')), flush=True)
        except Exception as error:
            failure = dict(life_id=life['life_id'], status='MISSING_CUSTODY_OR_COPY_FAILURE_NO_RETRY',
                error_type=type(error).__name__, error_class=str(error) if type(error) is ValueError else type(error).__name__)
            protocol.write(operation / (life['life_id'] + '.FAILED.json'), failure)
            active.pop(life['life_id'], None)
            print(json.dumps(failure), flush=True)
    sequence = 0
    while active and time.time() < plan['hard_end_unix']:
        progressed = False
        for life_id, queue_ref in list(active.items()):
            try:
                report = capture_available(queue_ref['path'])
                protocol.write(operation / f'{sequence:08d}.{life_id}.STATUS.json', report)
                sequence += 1
                if report['captured_checkpoints'] == 4:
                    active.pop(life_id)
                queue_root = Path(protocol.read(queue_ref['path'])['queue_root'])
                latest = protocol.read(sorted((queue_root / 'observations').glob('*.json'))[-1])
                progressed |= (Path(protocol.read(queue_ref['path'])['source_root']) / 'stream/records' /
                    f"{latest['next_index']:020d}.intent.json").exists()
            except Exception as error:
                protocol.write(operation / (life_id + '.FAILED.json'), dict(status='MISSING_COPY_FAILURE_NO_RETRY',
                    error_type=type(error).__name__, error_class=str(error) if type(error) is ValueError else type(error).__name__))
                active.pop(life_id)
        if active:
            time.sleep(1 if progressed else 30)
    protocol.write(operation / 'TERMINAL.json', dict(status='SOURCE_QUEUE_WINDOW_TERMINAL',
        remaining_lives=list(active), model_calls=0, observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('stat', 'validate', 'run_node'))
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--node')
    args = parser.parse_args()
    if args.action == 'stat':
        request = protocol.read(args.plan)
        rows = []
        for life in request['lives']:
            try:
                rows.append(stat_life(life))
            except Exception as error:
                rows.append(dict(life_id=life['life_id'], status='STAT_REFUSED', error_type=type(error).__name__))
        print(json.dumps(dict(rows=rows, hostname_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest())))
    elif args.action == 'validate':
        plan = validate(args.plan)
        print(json.dumps(dict(status='CPU_SOURCE_READY_NOT_GPU_GO', lives=21, calls_cap=plan['call_cap'])))
    else:
        run_node(args.plan, args.node)


if __name__ == '__main__':
    main()
