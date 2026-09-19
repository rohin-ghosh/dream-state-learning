"""Owner-bound local validation; only authenticated projections cross the wire."""

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time


MAX_RECORD_BYTES = 33554432
MAX_TRANSFER_BYTES = 67108864
MAX_RECORDS = 289
MAX_DISPATCH_DELAY_SECONDS = 110
SCHEMA = 'R233_OWNER_VALIDATED_NATIVE_PROJECTION_V1'
WIRE_SCHEMA = 'R233_OWNER_CUSTODY_PROJECTED_WIRE_V1'
BINDING_SCHEMA = 'R233_PROJECTED_TRANSPORT_BINDING_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def byte_digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: require(False, 'finite_JSON_numbers'))


def is_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(character in '0123456789abcdef' for character in value)


def bounded(raw):
    require(type(raw) is bytes and len(raw) <= MAX_TRANSFER_BYTES, 'unchanged_64MiB_transfer_bound')
    return raw


def source_digest():
    return digest({name:byte_digest(Path(__file__).with_name(name).read_bytes())
        for name in ('__init__.py', 'contract.py', 'custody.py', 'receiver.py', 'cli.py', 'relay.py', 'continuation.py')})


def open_directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'absolute_confined_directory')
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            next_descriptor = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_at(directory, name, limit, *, owner_uid=None, private=False):
    require(Path(name).name == name and name not in ('.', '..'), 'single_file_component')
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
            'bounded_single_link_regular_file')
        if owner_uid is not None:
            require(before.st_uid == owner_uid, 'bound_file_owner')
        if private:
            require(stat.S_IMODE(before.st_mode) == 0o600, 'strict_owner_file_0600')
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
        require(len(raw) == before.st_size and len(raw) <= limit and
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
            'immutable_bounded_read')
        return raw
    finally:
        os.close(descriptor)


def identity(pid):
    require(type(pid) is int and pid > 0, 'exact_native_pid')
    root = Path('/proc', str(pid))
    fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'native_alive')
    return dict(pid=pid, start_ticks=fields[19], command_sha256=byte_digest((root/'cmdline').read_bytes()),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), uid=root.stat().st_uid)


def validate_binding(binding, now=None):
    now = time.time() if now is None else now
    keys = {'schema', 'session_id', 'transport_epoch', 'deadline_unix', 'prior_deadline_unix',
        'lease_boundary_unix', 'registry', 'native_identity', 'anchors', 'validator_sha256',
        'judge_epoch_sha256', 'mirror_root', 'authority_sha256'}
    require(type(binding) is dict and set(binding) == keys and binding['schema'] == BINDING_SCHEMA,
        'exact_owner_binding_schema')
    for field in ('transport_epoch', 'validator_sha256', 'judge_epoch_sha256', 'authority_sha256'):
        require(is_sha(binding[field]), 'bound_owner_source_and_epoch')
    for field in ('deadline_unix', 'prior_deadline_unix', 'lease_boundary_unix'):
        require(type(binding[field]) in (int, float) and math.isfinite(binding[field]), 'finite_original_deadline')
    require(now < binding['deadline_unix'] == binding['prior_deadline_unix'] <= binding['lease_boundary_unix'] - 21600,
        'unchanged_live_deadline_and_lease_margin')
    row = binding['registry']
    require(row['session_id'] == binding['session_id'] and row['host_alias'] == 'ovx2'
        and row['native_pid'] == binding['native_identity']['pid'], 'same_node3_session_and_native')
    require(type(row['minimum_origin_record_index']) is int and row['minimum_origin_record_index'] >= 0,
        'original_future_frontier')
    require(type(binding['anchors']) is list and 1 <= len(binding['anchors']) <= 32, 'bound_source_anchors')
    for reference in binding['anchors']:
        require(set(reference) == {'path', 'sha256'} and is_sha(reference['sha256']), 'exact_anchor_reference')
    return row


def validate_request(request, row):
    require(type(request) is dict and set(request) == {'origin', 'metrics'}, 'unchanged_native_request')
    origin = request['origin']
    require(type(origin) is dict and set(origin) == {'kind', 'record_index', 'record_sha256'}
        and origin['kind'] == 'TRAIN_CHILD_RESPONSE' and type(origin['record_index']) is int
        and origin['record_index'] >= row['minimum_origin_record_index'] and is_sha(origin['record_sha256']),
        'original_future_native_origin')
    metrics = request['metrics']
    require(type(metrics) is dict and set(metrics) == {'THINK', 'ACT', 'LEARN'}
        and all(type(value) is int and value >= 0 for value in metrics.values()), 'original_stage_token_metrics')


def check_native(binding):
    expected = binding['native_identity']
    require(identity(expected['pid']) == expected, 'exact_live_native_incarnation')
    for reference in binding['anchors']:
        path = Path(reference['path'])
        directory = open_directory(path.parent)
        try:
            raw = read_at(directory, path.name, MAX_RECORD_BYTES, owner_uid=expected['uid'])
            require(byte_digest(raw) == reference['sha256'], 'unchanged_source_anchor')
        finally:
            os.close(directory)


class JournalWindow:
    def __init__(self, binding):
        self.binding = binding
        self.row = binding['registry']
        self.directory = open_directory(Path(self.row['life_root'])/'stream/records')
        self.references = {}
        self.stages = {}
        self.boundary = None

    def close(self):
        os.close(self.directory)

    def read(self, index):
        require(type(index) is int and index >= 0, 'nonnegative_record_index')
        raw = read_at(self.directory, f'{index:020d}.json', MAX_RECORD_BYTES,
            owner_uid=self.binding['native_identity']['uid'])
        record = decode(raw)
        require(record['index'] == index and record['journal_id'] == self.row['journal']['journal_id']
            and record['sha256'] == digest({key:value for key,value in record.items() if key != 'sha256'}),
            'complete_original_record_hash_and_journal')
        reference = dict(index=index, kind=record['kind'], sha256=record['sha256'],
            previous_sha256=record['previous_sha256'], file_sha256=byte_digest(raw), bytes=len(raw))
        if index in self.references:
            require(self.references[index] == reference, 'immutable_original_record')
        self.references[index] = reference
        require(len(self.references) <= MAX_RECORDS, 'original_289_record_bound')
        return record

    def stage(self, origin, stage):
        record = self.read(origin['record_index'])
        require(record['kind'] == 'RESPONSE' and record['sha256'] == origin['record_sha256'], 'same_child_RESPONSE')
        source_sha = digest(record['document'])
        previous, committed = record, []
        for index in range(record['index'] + 1, record['index'] + 33):
            current = self.read(index)
            require(current['previous_sha256'] == previous['sha256'], 'contiguous_child_stage_chain')
            document = current['document']
            if current['kind'] == 'COMMITTED':
                require(document['source_sha256'] == source_sha, 'same_committed_response')
                committed.append(index)
            if current['kind'] == 'R184_STAGE':
                require(committed and document['stage'] == stage and document['source_sha256'] == source_sha,
                    'committed_source_stage')
                self.stages[stage] = dict(origin=origin, source_sha256=source_sha,
                    committed_indices=committed, stage_index=index)
                raw = record['document']['response']['raw']
                require(type(raw) is str, 'exact_generated_text')
                return raw
            require(current['kind'] not in ('REQUEST', 'RESPONSE'), 'no_other_generation_before_stage')
            previous = current
        raise ValueError('source_commit_not_found')

    def think(self, origin):
        anchor = self.read(origin['record_index'])
        previous, source, stage_index = anchor, None, None
        for index in range(anchor['index'] - 1, max(-1, anchor['index'] - 257), -1):
            record = self.read(index)
            require(previous['previous_sha256'] == record['sha256'], 'same_life_contiguous_THINK_ancestry')
            if record['kind'] in ('LOADED', 'SLEEP_COMPLETE', 'R184_LEARN_COMPLETE', 'TERMINAL'):
                self.boundary = dict(index=index, kind=record['kind'], reason='original_stop_boundary')
                return None
            if record['kind'] == 'R184_STAGE':
                if record['document'].get('stage') != 'THINK' or source is not None:
                    self.boundary = dict(index=index, kind=record['kind'], reason='original_stage_boundary')
                    return None
                source, stage_index = record['document']['source_sha256'], index
            if source is not None and record['kind'] == 'RESPONSE':
                require(stage_index - index <= 32 and digest(record['document']) == source, 'same_latest_THINK_response')
                think_origin = dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=record['sha256'])
                return dict(raw=self.stage(think_origin, 'THINK'), origin=think_origin, stage='THINK',
                    source_sha256=source, journal_id=record['journal_id'])
            previous = record
        self.boundary = dict(index=min(self.references), kind='SCAN_LIMIT', reason='original_256_or_start_boundary')
        return None


def collect(binding, request):
    row = validate_binding(binding)
    validate_request(request, row)
    require(binding['validator_sha256'] == source_digest(), 'pinned_projection_validator')
    check_native(binding)
    window = JournalWindow(binding)
    try:
        raw = window.stage(request['origin'], 'ACT')
        think = window.think(request['origin'])
        records = [window.references[index] for index in sorted(window.references)]
        for previous, current in zip(records, records[1:]):
            require(current['index'] == previous['index'] + 1 and current['previous_sha256'] == previous['sha256'],
                'full_contiguous_validated_window')
        for reference in records:
            window.read(reference['index'])
        check_native(binding)
        validate_binding(binding)
        validated = time.time()
        receipt = dict(schema=SCHEMA, binding_sha256=digest(binding), session_id=binding['session_id'],
            transport_epoch=binding['transport_epoch'], validator_sha256=binding['validator_sha256'],
            native_identity=binding['native_identity'], request=request, raw_act=raw, think=think,
            records=records, stages=window.stages, think_boundary=window.boundary,
            locally_validated_original_bytes=sum(item['bytes'] for item in records),
            deadline_unix=binding['deadline_unix'], validated_unix=validated,
            dispatch_not_after_unix=min(binding['deadline_unix'], validated + MAX_DISPATCH_DELAY_SECONDS))
        bounded(canonical(receipt))
        return receipt
    finally:
        window.close()


def validate_receipt(receipt, binding):
    row = validate_binding(binding)
    keys = {'schema', 'binding_sha256', 'session_id', 'transport_epoch', 'validator_sha256', 'native_identity',
        'request', 'raw_act', 'think', 'records', 'stages', 'think_boundary', 'locally_validated_original_bytes',
        'deadline_unix', 'validated_unix', 'dispatch_not_after_unix'}
    require(type(receipt) is dict and set(receipt) == keys and receipt['schema'] == SCHEMA, 'exact_projection_receipt')
    require(receipt['binding_sha256'] == digest(binding) and receipt['session_id'] == binding['session_id']
        and receipt['transport_epoch'] == binding['transport_epoch'] and receipt['native_identity'] == binding['native_identity']
        and receipt['validator_sha256'] == binding['validator_sha256'] and receipt['deadline_unix'] == binding['deadline_unix'],
        'same_owner_bound_source_session_epoch')
    require(binding['validator_sha256'] == source_digest(), 'pinned_receiver_validator_source')
    require(type(receipt['validated_unix']) in (int, float) and math.isfinite(receipt['validated_unix'])
        and 0 < receipt['validated_unix'] <= time.time() < receipt['deadline_unix'], 'valid_original_validation_time')
    require(receipt['dispatch_not_after_unix'] == min(binding['deadline_unix'],
        receipt['validated_unix'] + MAX_DISPATCH_DELAY_SECONDS) and time.time() < receipt['dispatch_not_after_unix'],
        'expired_prepared_receipt_no_automatic_replay')
    validate_request(receipt['request'], row)
    bounded(canonical(receipt))
    records = receipt['records']
    require(type(records) is list and 1 <= len(records) <= MAX_RECORDS, 'bounded_attested_record_count')
    for record in records:
        require(set(record) == {'index', 'kind', 'sha256', 'previous_sha256', 'file_sha256', 'bytes'}
            and type(record['index']) is int and type(record['bytes']) is int and 0 < record['bytes'] <= MAX_RECORD_BYTES
            and is_sha(record['sha256']) and is_sha(record['file_sha256']), 'bounded_attested_original_record')
    for previous, current in zip(records, records[1:]):
        require(current['index'] == previous['index'] + 1 and current['previous_sha256'] == previous['sha256'],
            'contiguous_attested_originals')
    require(receipt['locally_validated_original_bytes'] == sum(item['bytes'] for item in records), 'exact_local_byte_accounting')
    require(type(receipt['raw_act']) is str, 'exact_raw_ACT')
    think = receipt['think']
    expected_stages = {'ACT'} if think is None else {'ACT', 'THINK'}
    require(set(receipt['stages']) == expected_stages, 'exact_attested_stages')
    indexed = {record['index']:record for record in records}
    for stage, proof in receipt['stages'].items():
        require(set(proof) == {'origin', 'source_sha256', 'committed_indices', 'stage_index'} and is_sha(proof['source_sha256']),
            'exact_attested_stage_proof')
        origin = proof['origin']
        require(indexed[origin['record_index']]['kind'] == 'RESPONSE'
            and indexed[origin['record_index']]['sha256'] == origin['record_sha256'], 'same_attested_RESPONSE')
        require(0 < proof['stage_index'] - origin['record_index'] <= 32 and
            indexed[proof['stage_index']]['kind'] == 'R184_STAGE' and proof['committed_indices'], 'bounded_committed_stage')
        require(all(origin['record_index'] < index < proof['stage_index'] and indexed[index]['kind'] == 'COMMITTED'
            for index in proof['committed_indices']), 'attested_COMMITTED_identities')
    require(receipt['stages']['ACT']['origin'] == receipt['request']['origin'], 'same_attested_ACT')
    require(records[-1]['index'] == receipt['stages']['ACT']['stage_index'], 'exact_attested_ACT_window_end')
    if think is not None:
        require(set(think) == {'raw', 'origin', 'stage', 'source_sha256', 'journal_id'} and type(think['raw']) is str
            and think['stage'] == 'THINK' and think['journal_id'] == row['journal']['journal_id']
            and think['origin'] == receipt['stages']['THINK']['origin']
            and think['source_sha256'] == receipt['stages']['THINK']['source_sha256']
            and receipt['stages']['THINK']['stage_index'] < receipt['request']['origin']['record_index']
            and records[0]['index'] == think['origin']['record_index']
            and receipt['request']['origin']['record_index'] - think['origin']['record_index'] <= 256
            and receipt['think_boundary'] is None, 'exact_latest_own_THINK_projection')
    else:
        require(type(receipt['think_boundary']) is dict and set(receipt['think_boundary']) == {'index', 'kind', 'reason'},
            'attested_original_no_THINK_boundary')
        require(receipt['think_boundary']['index'] == records[0]['index'], 'exact_attested_no_THINK_window_start')
    return receipt
