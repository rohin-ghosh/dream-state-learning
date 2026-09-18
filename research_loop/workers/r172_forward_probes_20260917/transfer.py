"""Private, once-only transfer; no provider, GPU, remote or learner entrypoint.

The controller must pass its existing campaign Ledger, not a new hop budget.
Each export source read, outgoing wire hop, incoming hop and existing-file
verification is charged independently. Local staging uses receive(role='staging');
an onward export is another charged hop. No CLI creates or resets a ledger.
Frozen preparation1 and previous receipts are not migrated by this module.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import tarfile
import time
from types import FunctionType, SimpleNamespace
import uuid

import prep_common as common


ROOT = common.REMOTE_ROOT
SCHEMA = 'R172_EXACT_PRIVATE_TRANSFER_V1'
MIB = 1024 ** 2
CAPTURE_FILES = ('COMMIT.original.json', 'BIRTH.private.json', 'MANIFEST.json', 'BOUNDARY.json', 'COMPLETE.json')
REGISTRATION_FILES = ('REGISTERED.json', 'TRAIN_FREEZE.json', 'TRAIN_WITNESSES.private.json')
CONTROL_FILES = ('QUEUE_PLAN.json', 'MAIN_SOURCE_READ_COPY_GO.json', 'FRESH_CUSTODY.json')
ADAPTER_FILES = ('adapter_model.safetensors', 'adapter_config.json', 'README.md')


def identity(life_id, sleep):
    common.require(type(life_id) is str and re.fullmatch(r'[a-zA-Z0-9_-]{1,96}', life_id), 'exact_life_id')
    common.require(type(sleep) is int and sleep >= 0, 'exact_sleep')


def member_path(name, life_id, sleep):
    identity(life_id, sleep)
    common.require(type(name) is str, 'relative_transfer_member')
    path = Path(name)
    common.require(not path.is_absolute() and '..' not in path.parts and str(path) == name,
        'relative_transfer_member')
    capture = Path('lives') / life_id / 'captures' / f'{sleep:06d}'
    if path.parent == capture / 'adapter':
        common.require(path.name in ADAPTER_FILES, 'adapter_only')
    elif path.parent == capture:
        common.require(path.name in CAPTURE_FILES, 'capture_metadata_only')
    elif path.parent == Path('lives') / life_id:
        common.require(path.name in REGISTRATION_FILES, 'exact_private_witness_metadata')
    else:
        common.require(path.parent == Path('source_controls') / life_id and path.name in CONTROL_FILES,
            'exact_registration_metadata')
    return path


def required_members(life_id, sleep):
    capture = Path('lives') / life_id / 'captures' / f'{sleep:06d}'
    return {str(capture / name) for name in CAPTURE_FILES} | {
        str(capture / 'adapter' / name) for name in ADAPTER_FILES[:2]} | {
        str(Path('lives') / life_id / name) for name in REGISTRATION_FILES} | {
        str(Path('source_controls') / life_id / name) for name in CONTROL_FILES}


def kind(name):
    return 'adapter' if Path(name).parent.name == 'adapter' else 'metadata'


def reference(path, raw):
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def accounting(ledger, life_id):
    common.require(isinstance(ledger, common.Ledger) and (ledger.root / 'reservations').is_dir(),
        'existing_campaign_ledger_required_no_new_budget')
    common.require(life_id in ledger.lives and ledger.limits['metadata'] <= 32 * common.GIB
        and ledger.limits['adapter'] <= 16 * common.GIB and ledger.limits['per_life'] <= 2 * common.GIB,
        'existing_preparation_read_limits')
    common.require(time.time() < common.END, 'read_window_ended')


def validate_header(header, life_id, sleep, custody_root):
    common.require(header['schema'] == SCHEMA and header['proposal_sha256'] == common.PROPOSAL_SHA
        and header['private_evaluator_only'] is True, 'exact_private_proposal')
    common.require(header['life_id'] == life_id and type(header['sleep']) is int and header['sleep'] == sleep,
        'exact_requested_transfer')
    common.require(type(header['files']) is list and 13 <= len(header['files']) <= 14, 'bounded_capture_members')
    expected = {}
    for entry in header['files']:
        common.require(set(entry) == {'name', 'bytes', 'sha256'}, 'exact_transfer_entry')
        name = str(member_path(entry['name'], life_id, sleep))
        common.require(name not in expected and type(entry['bytes']) is int and entry['bytes'] >= 0
            and type(entry['sha256']) is str and re.fullmatch('[0-9a-f]{64}', entry['sha256']),
            'finite_unique_hashed_transfer_entry')
        common.require(kind(name) == 'adapter' or entry['bytes'] <= 32 * MIB, 'bounded_private_metadata_member')
        expected[name] = entry
    common.require(required_members(life_id, sleep) <= set(expected), 'complete_capture_adapter_custody_inventory_required')
    common.require(sum(entry['bytes'] for entry in expected.values()) <= 2 * common.GIB, 'bounded_exact_stream')
    capture = f'lives/{life_id}/captures/{sleep:06d}/COMPLETE.json'
    common.require(header['capture'] == dict(path=str(custody_root / capture), sha256=expected[capture]['sha256']),
        'capture_receipt_hash_join')
    return expected


def validate_closure(metadata, expected, life_id, sleep, custody_root, proposal, source_read=False):
    from gpu import orch_r167_object_probe_queue as queue

    cache = {str(custody_root / name): raw for name, raw in metadata.items()}

    def cached_read(path):
        common.require(str(path) in cache, 'untransferred_reference_forbidden')
        return queue.protocol.parse(cache[str(path)])

    def cached_ref(path):
        common.require(str(path) in cache, 'untransferred_reference_forbidden')
        return reference(path, cache[str(path)])

    def cached_bound(bound):
        common.require(cached_ref(bound['path']) == bound, 'cached_original_reference_hash')
        return cached_read(bound['path'])

    protocol = SimpleNamespace(**vars(queue.protocol))
    protocol.read, protocol.ref, protocol.bound = cached_read, cached_ref, cached_bound
    environment = dict(queue.load.__globals__, protocol=protocol)
    load = FunctionType(queue.load.__code__, environment, queue.load.__name__, queue.load.__defaults__)
    environment['load'] = load
    initialized = FunctionType(queue.initialized.__code__, environment, queue.initialized.__name__,
        queue.initialized.__defaults__)
    plan_path = custody_root / 'source_controls' / life_id / 'QUEUE_PLAN.json'
    plan, life_root, source, authority = initialized(plan_path, source_read)
    common.require(life_root == custody_root / 'lives' / life_id and plan['life_id'] == life_id
        and plan['sleep_count'] == 3 and sleep in queue.milestones(plan), 'declared_enrolled_milestone')
    enrolled = [life for life in proposal['lives'] if life['life_id'] == life_id]
    common.require(len(enrolled) == 1 and enrolled[0]['proposed_storage_root'] == str(source), 'declared_original_life_root')
    registration = cached_read(life_root / 'REGISTERED.json')
    slots = [dict(key=queue.key(life_id, ordinal, condition), life_id=life_id, sleep=ordinal,
        condition=condition, model_calls=3) for ordinal in queue.milestones(plan) for condition in queue.CONDITIONS]
    common.require(registration['schema'] == queue.SCHEMA and registration['slots'] == slots
        and registration['model_calls'] == 0 and registration['no_child_blocking'] is True,
        'exact_registered_milestone_slots')
    prefix = life_root / 'captures' / f'{sleep:06d}'
    manifest = cached_read(prefix / 'MANIFEST.json')
    commit = cached_read(prefix / 'COMMIT.original.json')
    queue.checkpoint(commit, source, sleep)
    adapter_files = {Path(name).name: entry['sha256'] for name, entry in expected.items() if kind(name) == 'adapter'}
    common.require(commit['adapter_files'] == adapter_files, 'streamed_adapter_inventory_matches_original_COMMIT')
    common.require(manifest == dict(schema='R130_CHECKPOINT_MANIFEST_V1', adapter_path='adapter',
        commit_path='COMMIT.original.json', commit_sha256=cached_ref(prefix / 'COMMIT.original.json')['sha256']),
        'exact_original_manifest_commit_join')
    captured = cached_read(prefix / 'COMPLETE.json')
    common.require(captured['status'] == 'IMMUTABLE_ADAPTER_BIRTH_CUSTODY' and captured['model_calls'] == 0,
        'completed_source_capture_required')
    for field, filename in (('manifest', 'MANIFEST.json'), ('birth', 'BIRTH.private.json'), ('boundary', 'BOUNDARY.json')):
        common.require(captured[field] == cached_ref(prefix / filename), 'capture_receipt_exact_bound_metadata')
    boundary = cached_read(prefix / 'BOUNDARY.json')
    birth = cached_read(prefix / 'BIRTH.private.json')
    common.require(set(birth) == {'system_prompt', 'birth_prompt'} and all(type(value) is str for value in birth.values()),
        'original_birth_context_only')
    common.require(boundary['schema'] == queue.SCHEMA and boundary['life_id'] == life_id
        and type(boundary['sleep']) is int and boundary['sleep'] == sleep and boundary['source_root'] == str(source)
        and boundary['birth_plan'] == plan['birth_plan'] and boundary['source_authority'] == plan['source_authority']
        and boundary['context_sha256'] == common.digest(birth)
        and boundary['commit'] == dict(path=str(queue.checkpoint_path(source, sleep)),
            sha256=cached_ref(prefix / 'COMMIT.original.json')['sha256']), 'original_boundary_hash_joins')
    for field in ('record', 'intent'):
        bound = boundary[field]
        common.require(set(bound) == {'path', 'sha256'} and Path(bound['path']).parent == source / 'stream/records'
            and re.fullmatch('[0-9a-f]{64}', bound['sha256']), 'bounded_original_record_reference')
    common.require((sleep == 0 and commit['optimizer_steps'] == 0) or
        (sleep > 0 and queue.finite(commit['created_unix']) and commit['created_unix'] > plan['frozen_unix']),
        'prospective_or_untouched_initial_checkpoint')
    frozen = cached_read(life_root / 'TRAIN_FREEZE.json')
    witness = cached_read(life_root / 'TRAIN_WITNESSES.private.json')
    observation = cached_bound(authority['registration_observation'])
    original_record = observation['completed_boundary']['record']['record']
    common.require(queue.finite(frozen['frozen_unix']) and queue.finite(captured['observed_unix'])
        and plan['frozen_unix'] <= frozen['frozen_unix'] <= captured['observed_unix'] <= time.time(),
        'honest_preoutput_freeze_and_capture_time')
    common.require(frozen['status'] == 'PREOUTPUT_ORIGINAL_LANGUAGE_TRAIN_EVIDENCE'
        and frozen['evidence'] == cached_ref(life_root / 'TRAIN_WITNESSES.private.json')
        and frozen['record'] == witness['source_record'] == original_record and frozen['birth'] == plan['birth_plan']
        and frozen['model_calls'] == 0 and witness['parent_access'] is False and witness['context'] == birth
        and witness['lexical'] == 'NOT_APPLIED_NONCOVERAGE_NOT_NEGATIVE', 'private_TRAIN_freeze_original_joins')
    indices = []
    for entry in witness['witnesses']:
        common.require(type(entry['event_index']) is int and entry['event_index'] >= 0 and type(entry['text']) is str
            and hashlib.sha256(entry['text'].encode()).hexdigest() == entry['text_sha256'], 'exact_private_TRAIN_witness')
        indices.append(entry['event_index'])
    common.require(indices == sorted(set(indices)), 'ordered_unique_TRAIN_witnesses')
    return plan


class SourceLedger:
    def __init__(self, ledger, life_root, caps):
        common.require(set(caps) == {'metadata', 'adapter'} and all(type(value) is int and 0 < value <= 2 * common.GIB
            for value in caps.values()), 'prior_source_caps_required')
        self.ledger, self.life_root, self.caps = ledger, life_root, caps

    def reserve(self, operation, life_id, kind, amount, discovery=False):
        from gpu import orch_r167_object_probe_queue as queue
        common.require(queue.read_totals(self.life_root)[kind] + amount <= self.caps[kind], 'source_export_read_budget')
        charged = self.ledger.reserve(operation, life_id, kind, amount, discovery)
        common.write(self.life_root / 'reads' / (uuid.uuid4().hex + '.json'), dict(kind=kind, reserved_bytes=amount,
            operation=operation, campaign_charge=charged, failures_charged=True, observed_unix=time.time()))
        return charged


def tar_header(name, size):
    info = tarfile.TarInfo(name)
    info.size, info.mode = size, 0o600
    return info.tobuf(format=tarfile.USTAR_FORMAT)


def padding(size):
    return (-size) % tarfile.BLOCKSIZE


def footer(size):
    return 1024 + (-(size + 1024)) % tarfile.RECORDSIZE


def write_wire(output, raw):
    remaining = memoryview(raw)
    while remaining:
        common.require(time.time() < common.END, 'read_window_ended')
        written = output.write(remaining)
        common.require(type(written) is int and 0 < written <= len(remaining), 'failed_transfer_output')
        remaining = remaining[written:]


def export(life_id, sleep, output, *, ledger=None, source_caps=None, root=None, custody_root=None):
    identity(life_id, sleep)
    accounting(ledger, life_id)
    root = Path(ROOT if root is None else root)
    custody_root = Path(root if custody_root is None else custody_root)
    common.require(root.is_absolute() and root == root.resolve(), 'canonical_transfer_root')
    life_root = root / 'lives' / life_id
    operation = root / 'exports' / f'{life_id}_{sleep:06d}'
    operation.mkdir(parents=True, mode=0o700, exist_ok=False)
    common.write(operation / 'ONCE.json', dict(started_unix=time.time(), no_retry=True))
    try:
        with common.lock(life_root / 'queue.lock'):
            source_ledger = SourceLedger(ledger, life_root, source_caps or {})
            reader = common.Reader(source_ledger, life_id, f'export:{operation}', [root])
            unused, proposal = common.scope(root / 'control/PREPARATION_SCOPE.json', root / 'control/PROPOSAL.json', reader)
            capture = life_root / 'captures' / f'{sleep:06d}'
            common.require((capture / 'COMPLETE.json').is_file() and not (capture / 'FAILED.json').exists(),
                'complete_capture_required')
            names = required_members(life_id, sleep)
            for path in capture.rglob('*'):
                if path.is_dir():
                    common.require(path == capture / 'adapter', 'no_extra_capture_directory')
                else:
                    names.add(str(member_path(str(path.relative_to(root)), life_id, sleep)))
            metadata = {name: reader.raw(root / name) for name in sorted(names) if kind(name) == 'metadata'}
            commit = json.loads(metadata[f'lives/{life_id}/captures/{sleep:06d}/COMMIT.original.json'])
            entries = []
            for name in sorted(names):
                if kind(name) == 'metadata':
                    size, checksum = len(metadata[name]), reference(name, metadata[name])['sha256']
                else:
                    descriptor = common.safe_file(root / name)
                    try:
                        size = os.fstat(descriptor).st_size
                    finally:
                        os.close(descriptor)
                    checksum = commit['adapter_files'][Path(name).name]
                entries.append(dict(name=name, bytes=size, sha256=checksum))
            complete = f'lives/{life_id}/captures/{sleep:06d}/COMPLETE.json'
            header = dict(schema=SCHEMA, life_id=life_id, sleep=sleep, files=entries,
                capture=reference(custody_root / complete, metadata[complete]), proposal_sha256=common.PROPOSAL_SHA,
                private_evaluator_only=True)
            expected = validate_header(header, life_id, sleep, custody_root)
            plan = validate_closure(metadata, expected, life_id, sleep, custody_root, proposal, source_read=True)
            common.require(all(plan[name + '_read_cap'] == source_caps[name] for name in source_caps),
                'exact_prior_source_caps')
            raw_header = common.canonical(header)
            common.require(len(raw_header) <= MIB, 'bounded_transfer_header')
            total = 512 + len(raw_header) + padding(len(raw_header)) + sum(512 + row['bytes'] + padding(row['bytes']) for row in entries)
            adapter_bytes = sum(row['bytes'] for row in entries if kind(row['name']) == 'adapter')
            for category, amount in (('metadata', total + footer(total) - adapter_bytes), ('adapter', adapter_bytes)):
                ledger.reserve(f'export-wire:{operation}:{category}', life_id, category, amount)
            write_wire(output, tar_header('TRANSFER_HEADER.json', len(raw_header)) + raw_header + bytes(padding(len(raw_header))))
            for entry in entries:
                name = entry['name']
                write_wire(output, tar_header(name, entry['bytes']))
                if kind(name) == 'metadata':
                    write_wire(output, metadata[name])
                else:
                    descriptor = common.safe_file(root / name)
                    with os.fdopen(descriptor, 'rb', buffering=0) as source:
                        before = os.fstat(source.fileno())
                        common.require(before.st_size == entry['bytes'], 'source_changed_before_export')
                        source_ledger.reserve(f'export-adapter:{operation}:{name}', life_id, 'adapter', before.st_size)
                        checksum, remaining = hashlib.sha256(), before.st_size
                        while remaining:
                            common.require(time.time() < common.END, 'read_window_ended')
                            raw = source.read(min(MIB, remaining))
                            common.require(bool(raw), 'short_adapter_export')
                            checksum.update(raw)
                            write_wire(output, raw)
                            remaining -= len(raw)
                        after = os.fstat(source.fileno())
                        current = os.stat(root / name, follow_symlinks=False)
                        common.require(root / name == (root / name).resolve() and all(
                            getattr(before, field) == getattr(after, field) == getattr(current, field) for field in
                            ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))
                            and checksum.hexdigest() == entry['sha256'], 'source_changed_during_export')
                write_wire(output, bytes(padding(entry['bytes'])))
            write_wire(output, bytes(footer(total)))
            output.flush()
        common.write(operation / 'COMPLETE.json', dict(status='PRIVATE_STREAM_EXPORTED_ONCE', observed_unix=time.time(), model_calls=0))
    except BaseException as error:
        common.write(operation / 'FAILED.json', dict(status='FAILED_EXPORT_PRESERVED_NO_RETRY', error_type=type(error).__name__))
        raise


def stream_member(reader):
    block = reader.exact(512)
    common.require(block[257:263] == b'ustar\0', 'plain_ustar_only_no_extensions')
    info = tarfile.TarInfo.frombuf(block, 'utf-8', 'strict')
    common.require(info.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and not info.linkname
        and info.size >= 0, 'no_special_transfer_member')
    return info


def receive(stream, root=ROOT, *, life_id=None, sleep=None, ledger=None, custody_root=ROOT, role='receiving'):
    identity(life_id, sleep)
    accounting(ledger, life_id)
    root, custody_root = Path(root), Path(custody_root)
    common.require(root.is_absolute() and root == root.resolve() and custody_root.is_absolute()
        and '..' not in custody_root.parts, 'canonical_transfer_root')
    disk = common.DiskLedger(root, role)
    operation = root / f'{role}_transfers' / f'{life_id}_{sleep:06d}'
    with common.lock(disk.directory / 'disk.lock'):
        operation.mkdir(parents=True, mode=0o700, exist_ok=False)
        common.write(operation / 'ONCE.json', dict(life_id=life_id, sleep=sleep, started_unix=time.time(), no_retry=True))
        try:
            disk._reserve_locked(str(operation) + ':control', 2 * MIB)
        except BaseException as error:
            common.write(operation / 'FAILED.json', dict(status='FAILED_TRANSFER_PRESERVED_NO_RETRY', error_type=type(error).__name__))
            raise
    try:
        local_reader = common.Reader(ledger, life_id, f'{role}-local:{operation}', [root])
        unused, proposal = common.scope(root / 'control/PREPARATION_SCOPE.json', root / 'control/PROPOSAL.json', local_reader)
        common.require(life_id in {life['life_id'] for life in proposal['lives']}, 'declared_24_identity')
        reader = common.ChargedStream(stream, ledger, life_id, f'{role}-wire:{operation}')
        first = stream_member(reader)
        common.require(first.name == 'TRANSFER_HEADER.json' and first.size <= MIB, 'bounded_transfer_header')
        from gpu import orch_r167_object_survival_eval as protocol
        header_raw = reader.exact(first.size)
        header = protocol.parse(header_raw)
        common.require(reader.exact(padding(first.size)) == bytes(padding(first.size)), 'zero_tar_padding')
        expected = validate_header(header, life_id, sleep, custody_root)
        disk_bytes = sum(((row['bytes'] + 4095) // 4096) * 4096 for row in expected.values()) + 16 * MIB
        disk.reserve(str(operation) + ':payload', disk_bytes)
        common.write(operation / 'HEADER.json', header_raw)
        metadata, pending = {}, []
        capture_name = f'lives/{life_id}/captures/{sleep:06d}/COMPLETE.json'
        with common.lock(root / 'transfer_publish.lock'):
            seen = set()
            for unused in expected:
                info = stream_member(reader)
                common.require(info.name in expected and info.name not in seen, 'no_duplicate_or_extra_transfer_member')
                entry = expected[info.name]
                common.require(info.size == entry['bytes'], 'exact_stream_size')
                target = root / member_path(info.name, life_id, sleep)
                common.require(target == target.resolve(), 'exact_stream_path')
                if target.exists():
                    shared = target.parent in (root / 'lives' / life_id, root / 'source_controls' / life_id)
                    common.require(shared, 'identical_existing_registration_only')
                    existing = local_reader.raw(target)
                    common.require(len(existing) == entry['bytes'] and reference(target, existing)['sha256'] == entry['sha256'],
                        'identical_existing_registration_only')
                staged = operation / 'payload' / info.name
                staged.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
                checksum, remaining, parts = hashlib.sha256(), info.size, []
                with staged.open('xb', buffering=0) as destination:
                    os.chmod(staged, 0o600)
                    while remaining:
                        raw = reader.exact(min(MIB, remaining), kind(info.name))
                        checksum.update(raw)
                        write_wire(destination, raw)
                        if kind(info.name) == 'metadata':
                            parts.append(raw)
                        remaining -= len(raw)
                    os.fsync(destination.fileno())
                common.require(checksum.hexdigest() == entry['sha256'], 'receiving_stream_hash')
                common.require(reader.exact(padding(info.size)) == bytes(padding(info.size)), 'zero_tar_padding')
                if kind(info.name) == 'metadata':
                    metadata[info.name] = b''.join(parts)
                if not target.exists():
                    pending.append((staged, target))
                seen.add(info.name)
            common.require(seen == set(expected), 'complete_stream_file_set')
            trailer = footer(reader.bytes)
            common.require(reader.exact(trailer) == bytes(trailer), 'exact_zero_archive_termination')
            ledger.reserve(f'{role}-wire-eof:{operation}', life_id, 'metadata', 1)
            common.require(stream.read(1) == b'', 'trailing_transfer_data_forbidden')
            validate_closure(metadata, expected, life_id, sleep, custody_root, proposal)
            for staged, target in sorted(pending, key=lambda pair: str(pair[1].relative_to(root)) == capture_name):
                target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
                os.link(staged, target)
                descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            result = dict(status='EXACT_RECEIVING_COPY_VERIFIED' if role == 'receiving' else 'EXACT_STAGING_COPY_VERIFIED',
                life_id=life_id, sleep=sleep, capture=header['capture'], proposal_sha256=header['proposal_sha256'],
                files=header['files'], observed_unix=time.time(), model_calls=0, role=role,
                verification='EXACT_TRANSPORT_CLOSURE_AND_ORIGINAL_REFERENCE_JOINS_NOT_NEW_SAVED_STATE_OR_GPU_ADMISSION')
            common.write(operation / 'COMPLETE.json', result)
        return {field: result[field] for field in ('status', 'life_id', 'sleep', 'observed_unix', 'model_calls')}
    except BaseException as error:
        common.write(operation / 'FAILED.json', dict(status='FAILED_TRANSFER_PRESERVED_NO_RETRY', error_type=type(error).__name__))
        raise


if __name__ == '__main__':
    raise SystemExit('HOLD: controller must supply the existing campaign ledger, exact identity and source caps; no automatic remote hop or new budget')
