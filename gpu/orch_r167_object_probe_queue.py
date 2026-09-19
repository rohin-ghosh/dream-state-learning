"""CPU-only prospective discovery/custody queue. No GPU or provider entrypoint.

New source-read/copy authority is mandatory. This does not reuse a consumed
R167 GO, alter its source, enroll a model, or call an original fixed readout.
"""

import argparse
import math
from pathlib import Path
import re
import time
import uuid

from gpu import orch_r167_object_survival_eval as protocol


SCHEMA = 'R167_PROSPECTIVE_CUSTODY_QUEUE_V1'
MAX_SLEEPS = 8
READ_CAP = 2 * 1024 ** 3
BASE = protocol.BASE
PROBES = protocol.PROBES
CONDITIONS = protocol.CONDITIONS
require = protocol.require
BATCH_SCHEMA = 'R167_FLEET_PROSPECTIVE_QUEUE_V1'


def load_batch(path):
    plan = protocol.read(path)
    require(set(plan) == {'schema', 'queue_root', 'frozen_unix', 'lives', 'unverified_coverage',
        'probes', 'conditions', 'future_sleeps', 'model_call_cap', 'generated_token_cap',
        'physical_slots', 'not_before_unix', 'hard_end_unix', 'lease_deadline_unix',
        'adapter_copy_cap', 'metadata_read_cap', 'resource_evidence', 'visibility'}, 'exact_batch_fields')
    require(plan['schema'] == BATCH_SCHEMA and type(plan['lives']) is list
            and 1 <= len(plan['lives']) <= 21, 'bounded_fleet_not_silent_subselection')
    require(plan['future_sleeps'] == 3 and plan['probes'] == list(PROBES)
            and plan['conditions'] == list(CONDITIONS), 'fixed_three_sleep_instrument')
    require(plan['model_call_cap'] == len(plan['lives']) * 24
            and plan['generated_token_cap'] == plan['model_call_cap'] * 512, 'fleet_aggregate_caps')
    require(plan['physical_slots'] == [0, 1] and plan['visibility'] == 'PRIVATE_EVALUATOR_ONLY_METADATA_TO_PARENTS',
            'no_extra_GPU_or_parent_visibility')
    times = [plan[name] for name in ('frozen_unix', 'not_before_unix', 'hard_end_unix', 'lease_deadline_unix')]
    require(all(finite(value) and value > 0 for value in times)
            and times[0] <= time.time() and times[0] <= times[1] < times[2] <= times[3], 'prospective_existing_lease_wall')
    require(type(plan['adapter_copy_cap']) is int and 0 < plan['adapter_copy_cap'] <= 16 * 1024 ** 3
            and type(plan['metadata_read_cap']) is int and 0 < plan['metadata_read_cap'] <= 8 * 1024 ** 3,
            'fleet_finite_copy_read_budget')
    root = protocol.regular(plan['queue_root'])
    require(root.is_absolute() and not root.is_relative_to(protocol.CAMPAIGN), 'new_fleet_generation_only')
    seen = set()
    for life in plan['lives']:
        require(set(life) == {'life_id', 'node', 'storage_root', 'process_plan_root', 'birth_plan',
                'inventory_identity', 'inventory_observed_unix', 'inventory_evidence', 'hold'}, 'metadata_only_life_fields')
        key(life['life_id'], 0, CONDITIONS[0])
        require(life['life_id'] not in seen, 'unique_life')
        seen.add(life['life_id'])
        source = protocol.regular(life['storage_root'])
        require(source.is_absolute() and not root.is_relative_to(source.parent)
                and not source.is_relative_to(root), 'separate_fleet_source')
        require(life['hold'] in ('FRESH_IDENTITY_CUSTODY_REQUIRED', 'RECOVERY_COMMIT_REQUIRED'), 'explicit_hold')
    require(len({(life['node'], life['storage_root']) for life in plan['lives']}) == len(seen), 'no_duplicate_root_alias')
    return plan, root


def batch_initialize(path):
    plan, root = load_batch(path)
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    (root / 'bindings').mkdir(mode=0o700)
    cells = [dict(life_id=life['life_id'], ordinal=ordinal, condition=condition, calls=3,
        status='UNBOUND_MISSING_NOT_NEGATIVE', checkpoint=None)
        for life in plan['lives'] for ordinal in range(4) for condition in CONDITIONS]
    protocol.write(root / 'REGISTERED.json', dict(plan=protocol.ref(path), cells=cells,
        registered_unix=time.time(), status='BATCH_METADATA_ONLY_NOT_GPU_GO', model_calls=0))
    return batch_status(path)


def batch_registered(path):
    plan, root = load_batch(path)
    require(protocol.read(root / 'REGISTERED.json')['plan'] == protocol.ref(path), 'immutable_fleet_registry')
    return plan, root


def batch_bind(path, life_plan_path):
    batch, root = batch_registered(path)
    plan, life_root, source, authority = load(life_plan_path, True)
    matches = [life for life in batch['lives'] if life['life_id'] == plan['life_id']]
    require(len(matches) == 1, 'registered_life_only')
    life = matches[0]
    require(str(source) == life['storage_root'] and plan['birth_plan'] == life['birth_plan']
            and plan['sleep_count'] == 3 and plan['frozen_unix'] >= batch['frozen_unix']
            and life_root == root / 'lives' / plan['life_id'], 'exact_registered_life_birth_next_three')
    require(authority['read_end_unix'] <= batch['hard_end_unix'], 'bounded_fleet_source_window')
    observation = protocol.bound(authority['registration_observation'])
    require(observation['observed_unix'] >= batch['frozen_unix'], 'fresh_frontier_not_historical_census')
    if life['hold'] == 'RECOVERY_COMMIT_REQUIRED':
        release = protocol.bound(authority['recovery_release'])
        require(release['status'] == 'EXACT_RECOVERY_COMMITTED' and release['source_root'] == str(source)
                and release['native_identity'] == observation['native_identity']
                and release['observed_unix'] <= observation['observed_unix'], 'no_uncommitted_recovery_sampling')
    with protocol.lock(root / 'queue.lock'):
        existing = [protocol.bound(protocol.read(binding)['plan']) for binding in (root / 'bindings').glob('*.json')]
        require(sum(item['adapter_read_cap'] for item in existing) + plan['adapter_read_cap'] <= batch['adapter_copy_cap']
                and sum(item['metadata_read_cap'] for item in existing) + plan['metadata_read_cap'] <= batch['metadata_read_cap'],
                'fleet_cumulative_source_budget')
        binding = root / 'bindings' / (plan['life_id'] + '.json')
        require(not binding.exists(), 'immutable_life_enrollment_no_retry')
        protocol.write(binding, dict(plan=protocol.ref(life_plan_path), life_id=plan['life_id'],
            observed_unix=time.time(), model_calls=0))
        initialize(life_plan_path)
    return dict(status='SOURCE_QUEUE_BOUND_NOT_GPU_ENROLLED', life_id=plan['life_id'], model_calls=0)


def batch_status(path):
    plan, root = batch_registered(path)
    rows = []
    for life in plan['lives']:
        binding = root / 'bindings' / (life['life_id'] + '.json')
        row = dict(life_id=life['life_id'], hold=life['hold'], registered_checkpoints=4,
            captured_checkpoints=0, missing_or_unobserved_checkpoints=4, condition_proposals=0)
        if binding.exists():
            reference = protocol.read(binding)['plan']
            protocol.bound(reference)
            if (root / 'lives' / life['life_id'] / 'REGISTERED.json').exists():
                row.update(status(reference['path']))
            else:
                row['status'] = 'BINDING_INITIALIZATION_INCOMPLETE_PRESERVED'
        rows.append(row)
    return dict(status='FLEET_METADATA_ONLY_NOT_GPU_GO', lives=len(rows), rows=rows,
        registered_checkpoints=len(rows) * 4, condition_slots=len(rows) * 8,
        model_call_cap=plan['model_call_cap'], generated_token_cap=plan['generated_token_cap'],
        captured_checkpoints=sum(row['captured_checkpoints'] for row in rows), model_calls=0,
        unverified_coverage=plan['unverified_coverage'])


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def milestones(plan):
    return [0, *range(plan['first_sleep'], plan['first_sleep'] + plan['sleep_count'])]


def key(life_id, sleep, condition):
    require(type(life_id) is str and re.fullmatch(r'[a-zA-Z0-9_-]{1,96}', life_id), 'exact_life_id')
    require(type(sleep) is int and sleep >= 0 and condition in CONDITIONS, 'exact_sleep_condition')
    return protocol.digest(dict(life_id=life_id, sleep=sleep, condition=condition))


def load(plan_path, source_read=False):
    plan = protocol.read(plan_path)
    fields = {'schema', 'queue_root', 'life_id', 'source_root', 'birth_plan', 'journal', 'source_authority',
              'first_sleep', 'sleep_count', 'frozen_unix', 'probes', 'conditions', 'base_sha256',
              'model_call_cap', 'generated_token_cap', 'metadata_read_cap', 'adapter_read_cap'}
    require(set(plan) == fields and plan['schema'] == SCHEMA, 'exact_queue_plan_no_extra_channels')
    require(type(plan['first_sleep']) is int and plan['first_sleep'] > 0
            and type(plan['sleep_count']) is int and 1 <= plan['sleep_count'] <= MAX_SLEEPS, 'finite_every_sleep_window')
    require(plan['probes'] == list(PROBES) and plan['conditions'] == list(CONDITIONS)
            and plan['base_sha256'] == BASE, 'unchanged_three_probes_conditions_base')
    calls = (plan['sleep_count'] + 1) * 6
    require(plan['model_call_cap'] == calls and plan['generated_token_cap'] == calls * 512, 'predeclared_call_token_budget')
    require(finite(plan['frozen_unix']) and 0 < plan['frozen_unix'] <= time.time(), 'honest_prospective_freeze_time')
    root, source = protocol.regular(plan['queue_root']), protocol.regular(plan['source_root'])
    require(root.is_absolute() and source.is_absolute() and not root.is_relative_to(source.parent)
            and not source.is_relative_to(root) and not root.is_relative_to(protocol.CAMPAIGN), 'separate_new_custody_root')
    require(Path(plan['journal']['path']) == source / 'stream/JOURNAL.json'
            and protocol.regular(plan['birth_plan']['path']).is_absolute(), 'exact_source_metadata_paths')
    key(plan['life_id'], 0, CONDITIONS[0])
    for name in ('metadata_read_cap', 'adapter_read_cap'):
        require(type(plan[name]) is int and 0 < plan[name] <= READ_CAP, 'fixed_source_read_budget')
    authority = protocol.bound(plan['source_authority'])
    require(authority['schema'] == SCHEMA and authority['status'] == 'MAIN_SOURCE_READ_COPY_GO'
            and authority['life_id'] == plan['life_id'] and authority['source_root'] == str(source)
            and authority['birth_plan'] == plan['birth_plan'] and authority['journal'] == plan['journal']
            and authority['milestones'] == milestones(plan)
            and authority['metadata_read_cap'] == plan['metadata_read_cap']
            and authority['adapter_read_cap'] == plan['adapter_read_cap'], 'exact_new_source_owner_scope')
    observation = protocol.bound(authority['registration_observation'])
    require(observation['source_root'] == str(source) and observation['life_id'] == plan['life_id']
            and observation['status'] == 'IDENTITY_AND_COMPLETED_FRONTIER_VERIFIED'
            and type(observation['last_completed_sleep']) is int
            and observation['last_completed_sleep'] + 1 == plan['first_sleep']
            and finite(observation['observed_unix'])
            and 0 < observation['observed_unix'] <= plan['frozen_unix']
            and authority['frozen_unix'] == plan['frozen_unix'], 'prospective_identity_frontier_binding')
    identity = observation['native_identity']
    require(type(identity['pid']) is int and identity['pid'] > 0
            and str(identity['start_ticks']).isdigit() and bool(identity['boot_id']), 'exact_native_identity')
    require(authority['permissions'] == ['metadata_discovery', 'adapter_only_copy']
            and finite(authority['read_end_unix']), 'read_copy_only_not_GPU_authority')
    if source_read:
        require(time.time() < authority['read_end_unix'], 'source_read_authority_expired')
    return plan, root, source, authority


def initialized(plan_path, source_read=False):
    result = load(plan_path, source_read)
    plan, root, _, _ = result
    require(protocol.read(root / 'REGISTERED.json')['plan'] == protocol.ref(plan_path), 'immutable_registered_plan')
    return result


def initialize(plan_path):
    plan, root, _, _ = load(plan_path)
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name in ('reads', 'observations', 'boundaries', 'captures', 'admission_proposals'):
        (root / name).mkdir(mode=0o700)
    slots = [dict(key=key(plan['life_id'], sleep, condition), life_id=plan['life_id'], sleep=sleep,
                  condition=condition, model_calls=3) for sleep in milestones(plan) for condition in CONDITIONS]
    protocol.write(root / 'REGISTERED.json', dict(schema=SCHEMA, plan=protocol.ref(plan_path), slots=slots,
        registered_unix=time.time(), model_calls=0, no_child_blocking=True))
    return dict(status='REGISTERED_METADATA_ONLY', slots=len(slots), model_calls=0)


def read_totals(root):
    result = dict(metadata=0, adapter=0)
    for path in (root / 'reads').glob('*.json'):
        entry = protocol.read(path)
        require(entry['kind'] in result and type(entry['reserved_bytes']) is int
                and entry['reserved_bytes'] >= 0, 'valid_persisted_read_charge')
        result[entry['kind']] += entry['reserved_bytes']
    return result


class Reader:
    def __init__(self, plan, root, source, paths, kind):
        self.paths = {protocol.regular(path) for path in paths}
        metadata = {Path(plan['journal']['path']), Path(plan['birth_plan']['path'])}
        metadata.update(checkpoint_path(source, sleep) for sleep in milestones(plan))
        for path in self.paths:
            if kind == 'metadata':
                require(path in metadata or (path.parent == source / 'stream/records'
                    and re.fullmatch(r'[0-9]{20}(?:\.intent)?\.json', path.name)), 'metadata_only_allowlist')
            else:
                require(kind == 'adapter' and any(path.parent == checkpoint_path(source, sleep).parent / 'adapter'
                    for sleep in milestones(plan)) and path.name in
                    {'adapter_model.safetensors', 'adapter_config.json', 'README.md'}, 'adapter_only_allowlist')
        amount = sum(path.stat().st_size for path in self.paths)
        require(read_totals(root)[kind] + amount <= plan[kind + '_read_cap'], 'cumulative_source_read_budget_exhausted')
        self.deadline = protocol.bound(plan['source_authority'])['read_end_unix']
        protocol.write(root / 'reads' / (uuid.uuid4().hex + '.json'), dict(kind=kind, reserved_bytes=amount,
            observed_unix=time.time()))
        self.reader = protocol.BoundedReader(Path('/'), amount)
        self.cache = {}

    def raw(self, path):
        path = protocol.regular(path)
        require(path in self.paths and time.time() < self.deadline, 'allowlisted_unexpired_source_read')
        if path not in self.cache:
            self.cache[path] = self.reader.raw(path)
        return self.cache[path]

    def document(self, path):
        raw = self.raw(path)
        return protocol.parse(raw), dict(path=str(path), sha256=protocol.hashlib.sha256(raw).hexdigest())


def checkpoint_path(source, sleep):
    return source / 'checkpoints' / ('initial' if sleep == 0 else f'sleep_{sleep:06d}') / 'COMMIT.json'


def checkpoint(document, source, sleep):
    directory = checkpoint_path(source, sleep).parent
    require(document['schema'] == 'R125_NATIVE_CONTINUITY_V1' and document['base_sha256'] == BASE,
            'original_native_checkpoint_schema_base')
    require(Path(document['adapter_path']) == directory / 'adapter', 'checkpoint_wrong_source_or_sleep')
    require({'adapter_model.safetensors', 'adapter_config.json'} <= set(document['adapter_files'])
            <= {'adapter_model.safetensors', 'adapter_config.json', 'README.md'}, 'exact_adapter_allowlist')
    require(protocol.digest(document['adapter_files']) == document['checkpoint_sha256']['adapter'], 'adapter_inventory_digest')


def validate_boundary(record, commit, sleep, context):
    body = record['document']
    wrapped = body.get('state') if sleep == 0 else body.get('resume_state')
    require(wrapped and wrapped['sha256'] == protocol.digest(wrapped['state']), 'bound_TRAIN_state')
    state = wrapped['state']
    history = state['history']
    require(all(history[name] == context[name] for name in context)
            and all(event.get('split') == 'TRAIN' and event.get('origin') == 'TRAIN_COLLECTION'
                    for event in history['events']), 'original_birth_and_TRAIN_only_context')
    require(state['model_state_sha256'] == protocol.digest(commit['checkpoint_sha256']), 'exact_model_checkpoint_binding')
    if sleep == 0:
        require(record['index'] == 0 and not state['rows'] and commit['optimizer_steps'] == 0,
                'untouched_initial_boundary')
    else:
        receipt = {name: value for name, value in body.items() if name != 'resume_state'}
        require(record['kind'] == 'SLEEP_COMPLETE' and body['cycle'] == sleep and body['status'] == 'COMPLETE'
                and body['checkpoint'] == commit and len(state['sleep_receipts']) == sleep
                and state['sleep_receipts'][-1] == receipt
                and state['sleep_frontier'] == len(state['rows']), 'completed_sleep_not_orphan_commit')


def discover(plan_path, max_records=256):
    require(type(max_records) is int and 1 <= max_records <= 256, 'bounded_discovery_chunk')
    plan, root, source, _ = initialized(plan_path, True)
    with protocol.lock(root / 'queue.lock'):
        prior = sorted((root / 'observations').glob('*.json'))
        cursor = protocol.read(prior[-1]) if prior else None
        start = cursor['next_index'] if cursor else 0
        paths = [Path(plan['journal']['path']), Path(plan['birth_plan']['path'])]
        if cursor and cursor['last_record']:
            paths.append(Path(cursor['last_record']['path']))
        pending = cursor.get('pending_boundaries', []) if cursor else []
        for entry in pending:
            paths.extend((Path(entry['record']['path']), Path(entry['intent']['path'])))
        pairs = []
        for index in range(start, start + max_records):
            directory = source / 'stream' / 'records'
            record, intent = directory / f'{index:020d}.json', directory / f'{index:020d}.intent.json'
            if not record.exists() or not intent.exists():
                break
            paths.extend((record, intent))
            pairs.append((record, intent))
        commits = {sleep: checkpoint_path(source, sleep) for sleep in milestones(plan)
                   if checkpoint_path(source, sleep).exists()}
        paths.extend(commits.values())
        reader = Reader(plan, root, source, paths, 'metadata')
        manifest, journal_ref = reader.document(plan['journal']['path'])
        birth, birth_ref = reader.document(plan['birth_plan']['path'])
        require(journal_ref == plan['journal'] and birth_ref == plan['birth_plan'], 'immutable_source_headers')
        context = {name: birth[name] for name in ('system_prompt', 'birth_prompt')}
        require(all(type(text) is str and 0 < len(text.encode()) <= 16384 for text in context.values()), 'bounded_original_context')
        previous = cursor['last_chain_sha256'] if cursor else protocol.digest(manifest)
        last_record = cursor['last_record'] if cursor else None
        if last_record:
            require(reader.document(last_record['path'])[1] == last_record, 'changed_cursor_anchor')
        commit_docs = {sleep: reader.document(path) for sleep, path in commits.items()}
        for sleep, (document, _) in commit_docs.items():
            checkpoint(document, source, sleep)
        added = 0
        candidates = []
        for entry in pending:
            record, record_ref = reader.document(entry['record']['path'])
            intent, intent_ref = reader.document(entry['intent']['path'])
            require(record_ref == entry['record'] and intent_ref == entry['intent'], 'changed_pending_witness')
            protocol.verify_record(record, intent, manifest, record['index'], record['previous_sha256'])
            candidates.append((record, record_ref, intent_ref))
        for offset, (record_path, intent_path) in enumerate(pairs):
            record, record_ref = reader.document(record_path)
            intent, intent_ref = reader.document(intent_path)
            previous = protocol.verify_record(record, intent, manifest, start + offset, previous)
            last_record = record_ref
            candidates.append((record, record_ref, intent_ref))
        next_pending = []
        for record, record_ref, intent_ref in candidates:
            sleep = 0 if record['index'] == 0 else record['document'].get('cycle') if record['kind'] == 'SLEEP_COMPLETE' else None
            if sleep not in milestones(plan):
                continue
            if sleep not in commit_docs:
                next_pending.append(dict(record=record_ref, intent=intent_ref))
                continue
            commit, commit_ref = commit_docs[sleep]
            if sleep > 0:
                require(finite(commit['created_unix']) and commit['created_unix'] > plan['frozen_unix'],
                        'preexisting_checkpoint_not_prospective')
            validate_boundary(record, commit, sleep, context)
            target = root / 'boundaries' / f'{sleep:06d}.json'
            value = dict(schema=SCHEMA, life_id=plan['life_id'], sleep=sleep, commit=commit_ref,
                record=record_ref, intent=intent_ref, birth_plan=birth_ref, context_sha256=protocol.digest(context),
                source_root=str(source), source_authority=plan['source_authority'])
            if target.exists():
                require(protocol.read(target) == value, 'no_changed_duplicate_boundary')
            else:
                protocol.write(target, value)
                added += 1
        observation = dict(status='VERIFIED_RETAINED_PREFIX_ONLY', next_index=start + len(pairs),
            last_chain_sha256=previous, last_record=last_record, pending_boundaries=next_pending, observed_unix=time.time(),
            read_bytes=reader.reader.bytes, source_authority=plan['source_authority'], added=added,
            complete_history_absence_claim=False, model_calls=0)
        protocol.write(root / 'observations' / f'{len(prior):08d}.json', observation)
    return dict(status='DISCOVERY_COMPLETE_METADATA_ONLY', added=added, verified_through_index=start + len(pairs) - 1,
                source_bytes=reader.reader.bytes, model_calls=0)


def capture(plan_path, sleep):
    plan, root, source, _ = initialized(plan_path, True)
    require(type(sleep) is int and sleep in milestones(plan), 'registered_checkpoint_only')
    with protocol.lock(root / 'queue.lock'):
        boundary_path = root / 'boundaries' / f'{sleep:06d}.json'
        boundary = protocol.read(boundary_path)
        source_commit = checkpoint_path(source, sleep)
        metadata_paths = [source_commit, Path(boundary['record']['path']), Path(boundary['intent']['path']), Path(plan['birth_plan']['path'])]
        metadata = Reader(plan, root, source, metadata_paths, 'metadata')
        commit, commit_ref = metadata.document(source_commit)
        require(commit_ref == boundary['commit'], 'source_commit_changed_before_copy')
        checkpoint(commit, source, sleep)
        record, record_ref = metadata.document(boundary['record']['path'])
        _, intent_ref = metadata.document(boundary['intent']['path'])
        birth, birth_ref = metadata.document(plan['birth_plan']['path'])
        require(record_ref == boundary['record'] and intent_ref == boundary['intent']
                and birth_ref == boundary['birth_plan'], 'source_witness_changed_before_copy')
        context = {name: birth[name] for name in ('system_prompt', 'birth_prompt')}
        require(protocol.digest(context) == boundary['context_sha256'], 'birth_custody')
        validate_boundary(record, commit, sleep, context)
        directory = root / 'captures' / f'{sleep:06d}'
        require(not directory.exists(), 'prior_capture_preserved_no_automatic_retry')
        directory.mkdir(mode=0o700, exist_ok=False)
        try:
            adapter_paths = [source_commit.parent / 'adapter' / name for name in commit['adapter_files']]
            payload = Reader(plan, root, source, adapter_paths, 'adapter')
            (directory / 'adapter').mkdir(mode=0o700)
            for path in adapter_paths:
                raw = payload.raw(path)
                require(protocol.hashlib.sha256(raw).hexdigest() == commit['adapter_files'][path.name], 'exact_immutable_adapter_bytes')
                protocol.write(directory / 'adapter' / path.name, raw)
            original = protocol.write(directory / 'COMMIT.original.json', metadata.raw(source_commit))
            birth_copy = protocol.write(directory / 'BIRTH.private.json', context)
            manifest = protocol.write(directory / 'MANIFEST.json', dict(schema='R130_CHECKPOINT_MANIFEST_V1',
                adapter_path='adapter', commit_path='COMMIT.original.json', commit_sha256=original['sha256']))
            witness = protocol.write(directory / 'BOUNDARY.json', boundary)
            complete_ref = protocol.write(directory / 'COMPLETE.json', dict(status='IMMUTABLE_ADAPTER_BIRTH_CUSTODY', manifest=manifest,
                birth=birth_copy, boundary=witness, observed_unix=time.time(), model_calls=0, optimizer_rng_read=False))
            for condition in CONDITIONS:
                proposal = root / 'admission_proposals' / (key(plan['life_id'], sleep, condition) + '.json')
                protocol.write(proposal, dict(schema=SCHEMA, status='READY_FOR_NEW_EXACT_GPU_AUTHORITY_NOT_GO',
                    key=key(plan['life_id'], sleep, condition), life_id=plan['life_id'], sleep=sleep, condition=condition,
                    manifest=manifest, birth=birth_copy, boundary=witness, capture=complete_ref, plan=protocol.ref(plan_path), calls=3,
                    max_new_tokens=512, prompts=list(PROBES), fresh_process_per_condition=True, context_per_prompt='birth_only',
                    pending=['receiving_runtime_and_lease', 'CPU_provenance', 'exact_Main_execution_GO', 'fresh_admission']))
        except BaseException as error:
            protocol.write(directory / 'FAILED.json', dict(status='FAILED_COPY_PRESERVED', error_type=type(error).__name__))
            raise
    return dict(status='CAPTURED_NO_ENROLLMENT_NO_GPU', sleep=sleep, condition_proposals=2, model_calls=0)


def status(plan_path):
    plan, root, _, _ = initialized(plan_path)
    complete = sum((root / 'captures' / f'{sleep:06d}' / 'COMPLETE.json').exists() for sleep in milestones(plan))
    proposals = list((root / 'admission_proposals').glob('*.json'))
    ready = 0
    for path in proposals:
        proposal = protocol.read(path)
        capture_ref = proposal['capture']
        protocol.bound(capture_ref)
        if not (Path(capture_ref['path']).parent / 'FAILED.json').exists():
            ready += 1
    require(len(proposals) <= (plan['sleep_count'] + 1) * 2, 'bounded_deduplicated_condition_proposals')
    return dict(status='METADATA_ONLY', registered_checkpoints=plan['sleep_count'] + 1,
        bound_checkpoints=len(list((root / 'boundaries').glob('*.json'))), captured_checkpoints=complete,
        condition_proposals=ready, preserved_proposal_artifacts=len(proposals), model_call_cap=plan['model_call_cap'], model_calls=0,
        read_bytes_reserved=read_totals(root), missing_or_unobserved_checkpoints=plan['sleep_count'] + 1 - complete)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('initialize', 'discover', 'capture', 'status',
        'batch_initialize', 'batch_bind', 'batch_status'))
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--sleep', type=int)
    parser.add_argument('--life-plan', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == 'capture':
            result = capture(args.plan, args.sleep)
        elif args.action == 'batch_bind':
            result = batch_bind(args.plan, args.life_plan)
        else:
            result = globals()[args.action](args.plan)
        print(protocol.json.dumps(result, sort_keys=True))
        return 0
    except BaseException:
        print(protocol.json.dumps(dict(status='REFUSED_OR_FAILED_METADATA_ONLY', model_calls=0)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
