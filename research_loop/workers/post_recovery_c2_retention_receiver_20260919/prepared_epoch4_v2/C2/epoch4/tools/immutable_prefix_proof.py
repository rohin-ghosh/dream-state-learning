"""Operator-pinned, same-boot local immutable-prefix proof; no implicit authority."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import re
import stat
import sys


SCHEMA = 'R233_IMMUTABLE_PREFIX_PROOF_V2'
GUARD_SCHEMA = 'R233_IMMUTABLE_PREFIX_OPERATOR_GUARD_V2'
SAME_NAMESPACE = 'SAME_MOUNT_NAMESPACE'
CROSS_NAMESPACE = 'SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE'
CONTEXT_ADMISSION_SCHEMA = 'R233_PREFIX_CONSUMER_CONTEXT_ADMISSION_V1'
MINIMUM_QUIET_NS = 3_000_000_000
TRUST = 'LOCAL_LINUX_SAME_BOOT_NO_ROLLBACK_NO_CONCURRENT_PREFIX_WRITERS_V1'
MAX_PROOF_BYTES = 64 * 1024 * 1024
MAX_GUARD_BYTES = 8 * 1024 * 1024
MAX_SOURCE_BYTES = 128 * 1024 * 1024
HASH = re.compile(r'[0-9a-f]{64}')
FILE_FIELDS = ('dev', 'ino', 'size', 'mtime_ns', 'ctime_ns', 'mode', 'nlink')
PROTECTED_METHODS = ('_advance', '_checkpoint', '_validate_entry', '_intent',
    '_inbox_event', '_read_json', '_read_bytes', '_ensure_open')
REQUIRED_SOURCES = {'gpu/checkpoint_tail_runtime.py', 'gpu/immutable_prefix_proof.py',
    'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py'}


def require(condition, reason):
    if not condition:
        raise ValueError('prefix_proof_' + reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key')
        result[key] = value
    return result


def decoded(raw):
    def invalid(value):
        raise ValueError('prefix_proof_nonfinite_json')
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=invalid)


def _fields(value, fields, reason):
    require(type(value) is dict and set(value) == set(fields), reason)


def _hash(value):
    require(type(value) is str and HASH.fullmatch(value) is not None, 'sha256_required')
    return value


def _path(value):
    require(type(value) is str and value.startswith('/') and str(Path(value)) == value
        and '..' not in Path(value).parts, 'canonical_absolute_path_required')
    return Path(value)


def _file_identity(value):
    require(stat.S_ISREG(value.st_mode), 'regular_file_required')
    return dict(zip(FILE_FIELDS, (value.st_dev, value.st_ino, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns, value.st_mode, value.st_nlink)))


def _validate_identity(value):
    _fields(value, FILE_FIELDS, 'file_identity_schema')
    require(all(type(item) is int and item >= 0 for item in value.values())
        and stat.S_ISREG(value['mode']) and value['nlink'] > 0, 'file_identity_values')


def _directory_identity(value):
    require(stat.S_ISDIR(value.st_mode), 'directory_required_no_symlinks')
    return dict(dev=value.st_dev, ino=value.st_ino, mode=value.st_mode)


@contextmanager
def _directory(path):
    path = _path(str(path))
    descriptors = []
    chain = []
    try:
        descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        descriptors.append(descriptor)
        chain.append(_directory_identity(os.fstat(descriptor)))
        for component in path.parts[1:]:
            descriptor = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                | os.O_CLOEXEC, dir_fd=descriptor)
            descriptors.append(descriptor)
            chain.append(_directory_identity(os.fstat(descriptor)))
        yield descriptor, chain
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _read(directory, name, limit):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
        dir_fd=directory)
    with os.fdopen(descriptor, 'rb') as stream:
        before = _file_identity(os.fstat(stream.fileno()))
        require(before['size'] <= limit, 'file_size_bound')
        raw = stream.read(limit + 1)
        after = _file_identity(os.fstat(stream.fileno()))
        current = _file_identity(os.stat(name, dir_fd=directory, follow_symlinks=False))
        require(before == after == current and len(raw) == before['size'], 'file_changed_during_read')
    return raw, before


def _read_path(path, limit):
    path = _path(str(path))
    with _directory(path.parent) as (descriptor, chain):
        raw, identity = _read(descriptor, path.name, limit)
    return raw, dict(path=str(path), chain=chain, identity=identity)


def _recheck_path(snapshot):
    path = _path(snapshot['path'])
    with _directory(path.parent) as (descriptor, chain):
        require(chain == snapshot['chain'], 'external_path_directory_changed')
        require(_file_identity(os.stat(path.name, dir_fd=descriptor, follow_symlinks=False))
            == snapshot['identity'], 'external_file_changed')


def read_pinned(path, expected_sha256, limit=MAX_GUARD_BYTES):
    _hash(expected_sha256)
    raw, snapshot = _read_path(path, limit)
    require(sha(raw) == expected_sha256, 'external_sha_mismatch')
    return decoded(raw), snapshot


def environment():
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(re.fullmatch(r'[0-9a-f-]{36}', boot) is not None, 'linux_boot_identity')
    namespace = os.stat('/proc/self/ns/mnt')
    return dict(boot_id=boot, mount_namespace=dict(dev=namespace.st_dev, ino=namespace.st_ino))


def validate_source(source):
    _fields(source, ('root', 'pins', 'epoch'), 'exact_source_schema')
    root = _path(source['root'])
    _fields(source['epoch'], ('path', 'sha256'), 'separate_source_epoch_pin_required')
    _hash(source['epoch']['sha256'])
    epoch_raw, epoch_snapshot = _read_path(source['epoch']['path'], MAX_GUARD_BYTES)
    require(sha(epoch_raw) == source['epoch']['sha256'], 'exact_separate_source_epoch')
    pins = source['pins']
    require(type(pins) is dict and REQUIRED_SOURCES <= pins.keys(), 'required_source_pins')
    snapshots = [epoch_snapshot]
    total = 0
    for relative, expected in sorted(pins.items()):
        require(type(relative) is str and relative == str(Path(relative)) and relative != '.'
            and not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'relative_source_path')
        _hash(expected)
        raw, snapshot = _read_path(root / relative, MAX_SOURCE_BYTES - total)
        require(sha(raw) == expected, 'exact_source_bytes')
        total += len(raw)
        snapshots.append(snapshot)
    for name, module in list(sys.modules.items()):
        if name in ('gpu', 'organism_v6') or name.startswith(('gpu.', 'organism_v6.')):
            filename = getattr(module, '__file__', None)
            if filename is None:
                continue
            require(str(filename).startswith(str(root) + '/'), 'loaded_module_outside_source')
            relative = str(Path(filename).relative_to(root))
            require(relative in pins, 'loaded_module_not_source_pinned')
    for snapshot in snapshots:
        _recheck_path(snapshot)
    return snapshots


def journal_class(source, journal_type):
    require(type(journal_type) is str and re.fullmatch(
        r'gpu\.[a-zA-Z0-9_]+:[a-zA-Z0-9_]+', journal_type), 'explicit_journal_type')
    module_name, class_name = journal_type.split(':')
    relative = module_name.replace('.', '/') + '.py'
    require(relative in source['pins'], 'journal_class_source_pinned')
    base = getattr(importlib.import_module(module_name), class_name)
    require(isinstance(base, type) and base.__module__ == module_name
        and base.__qualname__ == class_name, 'exact_journal_class')
    return base


def _check_journal_type(journal, binding):
    base = journal_class(binding['source'], binding['journal_type'])
    require(isinstance(journal, base), 'independent_journal_type_required')
    for name in PROTECTED_METHODS:
        require(inspect.getattr_static(type(journal), name) is inspect.getattr_static(base, name),
            'semantic_override_forbidden')
    for cls in type(journal).__mro__:
        if cls is object:
            continue
        filename = inspect.getsourcefile(cls)
        require(filename is not None and filename.startswith(binding['source']['root'] + '/'),
            'journal_mro_outside_source')
        relative = str(Path(filename).relative_to(binding['source']['root']))
        require(relative in binding['source']['pins'], 'journal_mro_not_source_pinned')


def _locations(journal):
    journal._ensure_open()
    with _directory(journal.root) as (descriptor, chain):
        require(_directory_identity(os.fstat(descriptor))
            == _directory_identity(os.fstat(journal._root_fd)), 'root_descriptor_binding')
        result = dict(root_chain=chain)
        for name, bound in (('records', journal._records_fd), ('inbox', journal._inbox_fd)):
            identity = _directory_identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
            require(identity == _directory_identity(os.fstat(bound)), 'directory_descriptor_binding')
            result[name] = identity
        for name, key in (('JOURNAL.json', 'manifest'), ('WRITER.lock', 'writer_lock')):
            result[key] = _file_identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
        require(result['writer_lock'] == _file_identity(os.fstat(journal._lock_fd)), 'writer_lock_binding')
    return result


def _pair(journal, index):
    return {suffix: _file_identity(os.stat(f'{index:020d}' + suffix,
        dir_fd=journal._records_fd, follow_symlinks=False)) for suffix in ('.json', '.intent.json')}


def _binding(journal, selection, source, journal_type):
    from gpu.checkpoint_tail_runtime import validate_selection
    selection = validate_selection(selection, journal.root)
    return dict(selection=selection, source=deepcopy(source), journal_type=journal_type,
        environment=environment(), trust=TRUST, metadata_policy=metadata_policy())


def _validate_binding(journal, selection, binding, consumer_context=None):
    from gpu.checkpoint_tail_runtime import validate_selection
    _fields(binding, ('selection', 'source', 'journal_type', 'environment', 'trust', 'metadata_policy'), 'binding_schema')
    require(binding['metadata_policy'] == metadata_policy(), 'exact_quiet_age_policy')
    selection = validate_selection(selection, journal.root)
    require(binding['trust'] == TRUST, 'same_trust_model_required')
    check_consumer_environment(binding, consumer_context)
    require(binding['selection'] == selection, 'exact_approved_selection')
    require(str(_path(selection['root'])) == str(journal.root), 'exact_root_path')
    require(selection['journal_id'] == journal._manifest['journal_id'], 'same_journal')
    validate_source(binding['source'])
    _check_journal_type(journal, binding)
    validate_source(binding['source'])


def _validate_records(journal, proof):
    from gpu.orch_r125_stream_journal import _digest
    selection = proof['binding']['selection']
    records = proof['records']
    require(type(records) is list and len(records) == selection['complete_index'] + 1,
        'exact_prefix_record_count')
    previous = _digest(journal._manifest)
    inbox = {}
    for index, record in enumerate(records):
        _fields(record, ('header', 'hashed', 'identities', 'inbox_document'), 'record_schema')
        header = record['header']
        _fields(header, ('schema', 'journal_id', 'index', 'kind', 'previous_sha256', 'sha256'), 'header_schema')
        require(header['schema'] == 'R125_STREAM_JOURNAL_V1'
            and header['journal_id'] == selection['journal_id'] and type(header['index']) is int
            and header['index'] == index and type(header['kind']) is str
            and re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', header['kind'])
            and header['previous_sha256'] == previous, 'header_chain')
        previous = _hash(header['sha256'])
        _fields(record['hashed'], ('bytes', 'raw_sha256'), 'raw_hash_schema')
        _hash(record['hashed']['raw_sha256'])
        _fields(record['identities'], ('.json', '.intent.json'), 'record_and_intent_required')
        for identity in record['identities'].values():
            _validate_identity(identity)
        require(type(record['hashed']['bytes']) is int and record['hashed']['bytes'] > 0
            and record['hashed']['bytes'] == record['identities']['.json']['size'], 'record_size_binding')
        if header['kind'] == 'INBOX':
            document = record['inbox_document']
            require(type(document) is dict, 'required_inbox_document')
            payload = dict(header, document=document)
            del payload['sha256']
            require(_digest(payload) == header['sha256'], 'cached_inbox_header_binding')
            journal._advance(dict(inbox=inbox), 'INBOX', document)
        else:
            require(record['inbox_document'] is None, 'no_other_cached_body')
    anchor = records[-1]['header']
    require(anchor['kind'] == 'SLEEP_COMPLETE' and anchor['sha256'] == selection['complete_sha256'],
        'exact_complete_anchor')
    return inbox


def _validate_resume(binding, resume, selection):
    from gpu.checkpoint_tail_runtime import validate_selection
    _fields(resume, ('selection', 'max_advance_records', 'max_advance_bytes'), 'resume_authority_schema')
    require(resume['selection'] == selection, 'exact_approved_resume_selection')
    selection = validate_selection(selection, binding['selection']['root'])
    origin = binding['selection']
    fixed_fields = set(origin) - {'complete_index', 'complete_sha256'}
    require(all(selection[key] == origin[key] for key in fixed_fields), 'same_policy_root_journal_life_bounds_sidecars')
    require(type(resume['max_advance_records']) is int and resume['max_advance_records'] >= 0
        and type(resume['max_advance_bytes']) is int and resume['max_advance_bytes'] >= 0,
        'explicit_nonnegative_advance_bounds')
    distance = selection['complete_index'] - origin['complete_index']
    require(0 <= distance <= resume['max_advance_records'], 'forward_only_bounded_complete_selection')
    require((distance == 0 and selection['complete_sha256'] == origin['complete_sha256'])
        or (distance > 0 and resume['max_advance_bytes'] > 0), 'exact_origin_or_explicit_forward_authority')
    return selection


def produce(journal, selection, source, journal_type):
    from gpu.checkpoint_tail_runtime import hash_record, _decoded_record
    binding = _binding(journal, selection, source, journal_type)
    _validate_binding(journal, binding['selection'], binding)
    locations = _locations(journal)
    sealing_started = clock_ns()
    aged_pairs = metadata_preflight(journal, binding['selection']['complete_index'], sealing_started)
    objects = source_objects(source)
    require_quiet_source(objects, sealing_started)
    require(journal._read_json(journal._root_fd, 'JOURNAL.json') == journal._manifest, 'manifest_changed')
    records = []
    for index in range(binding['selection']['complete_index'] + 1):
        identities = aged_pairs[index]
        header, hashed = hash_record(journal, index)
        inbox_document = _decoded_record(journal, header)['document'] if header['kind'] == 'INBOX' else None
        require(_pair(journal, index) == identities, 'prefix_changed_during_production')
        records.append(dict(header=header, hashed=hashed, identities=identities, inbox_document=inbox_document))
    proof = dict(schema=SCHEMA, binding=binding, locations=locations, records=records, source_objects=objects,
        sealing_clock=dict(started_wall_ns=sealing_started, finished_wall_ns=clock_ns()))
    _validate_records(journal, proof)
    require(_locations(journal) == locations, 'original_directories_or_manifest_changed')
    for index, record in enumerate(records):
        require(_pair(journal, index) == record['identities'], 'prefix_changed_during_production')
    validate_source(source)
    recheck_source_objects(source, objects)
    proof['sealing_clock']['finished_wall_ns'] = clock_ns()
    validate_sealing_clock(proof)
    require(len(encoded(proof)) <= MAX_PROOF_BYTES, 'proof_size_bound')
    return proof


def guard_candidate(proof, proof_path, proof_sha256, *, resume_selection=None,
        max_advance_records=0, max_advance_bytes=0, consumer_context_mode=SAME_NAMESPACE):
    _path(proof_path)
    _hash(proof_sha256)
    selection = proof['binding']['selection'] if resume_selection is None else resume_selection
    resume = dict(selection=deepcopy(selection), max_advance_records=max_advance_records,
        max_advance_bytes=max_advance_bytes)
    _validate_resume(proof['binding'], resume, selection)
    require(consumer_context_mode in (SAME_NAMESPACE, CROSS_NAMESPACE), 'known_consumer_context_mode')
    return dict(schema=GUARD_SCHEMA, consumer_context_mode=consumer_context_mode,
        proof_path=proof_path, proof_sha256=proof_sha256,
        binding=deepcopy(proof['binding']), resume=resume)


class VerifiedPrefix:
    def __init__(self, journal, selection, authority, admission=None):
        _fields(authority, ('guard_path', 'guard_sha256'), 'external_operator_guard_required')
        self.authority = deepcopy(authority)
        guard, guard_snapshot = read_pinned(authority['guard_path'], authority['guard_sha256'])
        _fields(guard, ('schema', 'proof_path', 'proof_sha256', 'binding', 'resume',
            'consumer_context_mode'), 'guard_schema')
        require(guard['schema'] == GUARD_SCHEMA, 'known_guard_schema')
        proof, proof_snapshot = read_pinned(guard['proof_path'], guard['proof_sha256'], MAX_PROOF_BYTES)
        _fields(proof, ('schema', 'binding', 'locations', 'records', 'source_objects', 'sealing_clock'), 'proof_schema')
        require(proof['schema'] == SCHEMA and proof['binding'] == guard['binding'], 'exact_guard_binding')
        self.consumer_context, admission_snapshots = authorize_consumer_context(guard, authority, admission)
        _validate_binding(journal, guard['binding']['selection'], guard['binding'], self.consumer_context)
        self.selection = _validate_resume(guard['binding'], guard['resume'], selection)
        self.journal = journal
        self.proof = proof
        self.guard = guard
        self.snapshots = (guard_snapshot, proof_snapshot, *admission_snapshots)
        self.inbox = _validate_records(journal, proof)
        self.prefix_count = len(proof['records'])
        extension_bytes = sum(_pair(journal, index)['.json']['size']
            for index in range(self.prefix_count, selection['complete_index'] + 1))
        require(extension_bytes <= guard['resume']['max_advance_bytes'], 'advance_byte_bound_exceeded')
        self.raw_extension_bytes = 0
        self.raw_tail_bytes = 0
        self.tail = {}
        self.finished = False
        self.recheck()

    def recheck(self):
        validate_sealing_clock(self.proof)
        recheck_source_objects(self.guard['binding']['source'], self.proof['source_objects'])
        require(_locations(self.journal) == self.proof['locations'], 'original_directories_or_manifest_changed')
        for index, record in enumerate(self.proof['records']):
            require(_pair(self.journal, index) == record['identities'], 'prefix_record_or_intent_changed')
        for index, identities in self.tail.items():
            require(_pair(self.journal, index) == identities, 'tail_changed_during_scan')
        for snapshot in self.snapshots:
            _recheck_path(snapshot)

    def record(self, index, hash_record):
        if index < len(self.proof['records']):
            record = self.proof['records'][index]
            return deepcopy(record['header']), dict(bytes=0, raw_sha256=record['hashed']['raw_sha256'])
        identities = _pair(self.journal, index)
        if index <= self.selection['complete_index']:
            self.raw_extension_bytes += identities['.json']['size']
            require(self.raw_extension_bytes <= self.guard['resume']['max_advance_bytes'], 'advance_byte_bound_exceeded')
        else:
            self.raw_tail_bytes += identities['.json']['size']
            require(self.raw_tail_bytes <= self.selection['max_tail_bytes'], 'tail_byte_bound_exceeded')
        header, hashed = hash_record(self.journal, index)
        require(_pair(self.journal, index) == identities, 'tail_changed_during_hash')
        self.tail[index] = identities
        return header, hashed

    def finish(self):
        validate_source(self.guard['binding']['source'])
        check_consumer_environment(self.guard['binding'], self.consumer_context)
        self.recheck()
        self.finished = True

    def receipt(self):
        require(self.finished, 'unfinished_scan')
        return dict(prefix_work='EXTERNALLY_PINNED_PREHASH_PLUS_METADATA_AND_RAW_EXTENSION',
            prefix_proof=dict(schema=SCHEMA, **self.authority, proof_path=self.guard['proof_path'],
                proof_sha256=self.guard['proof_sha256'], trust=TRUST,
                consumer_context=deepcopy(self.consumer_context),
                prevalidated_complete_index=self.proof['binding']['selection']['complete_index'],
                selected_complete_index=self.selection['complete_index'],
                raw_extension_records=self.selection['complete_index'] + 1 - self.prefix_count,
                raw_extension_bytes_hashed=self.raw_extension_bytes, raw_tail_bytes_hashed=self.raw_tail_bytes,
                prevalidated_raw_prefix_bytes=sum(record['hashed']['bytes'] for record in self.proof['records']),
                prefix_records_metadata_rechecked=len(self.proof['records']),
                full_raw_extension_verified=True, full_raw_tail_verified=True, implicit_fallback=False))


def prepare(journal, selection, authority, *, admission=None):
    return VerifiedPrefix(journal, selection, authority, admission=admission)


"""Appended to the exact v3 helper by source_port; not a standalone runtime."""


def _directory_metadata(value):
    require(stat.S_ISDIR(value.st_mode), 'immutable_source_directory_required')
    return dict(zip(FILE_FIELDS, (value.st_dev, value.st_ino, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns, value.st_mode, value.st_nlink)))


def _source_directory_paths(source):
    root = _path(source['root'])
    directories = {root}
    for relative in source['pins']:
        parent = (root / relative).parent
        while parent != root:
            require(root in parent.parents, 'source_directory_within_root')
            directories.add(parent)
            parent = parent.parent
    return sorted(directories, key=str)


def source_objects(source):
    files = validate_source(source)
    directories = []
    for path in _source_directory_paths(source):
        with _directory(path) as (descriptor, chain):
            directories.append(dict(path=str(path), chain=chain,
                identity=_directory_metadata(os.fstat(descriptor))))
    result = dict(files=files, directories=directories)
    recheck_source_objects(source, result)
    return result


def recheck_source_objects(source, objects):
    _fields(objects, ('files', 'directories'), 'source_objects_schema')
    expected_files = [source['epoch']['path']] + [str(Path(source['root']) / relative)
        for relative in sorted(source['pins'])]
    require(type(objects['files']) is list
        and [entry['path'] for entry in objects['files']] == expected_files,
        'every_source_and_epoch_identity_required')
    for snapshot in objects['files']:
        _fields(snapshot, ('path', 'chain', 'identity'), 'source_file_snapshot_schema')
        _validate_identity(snapshot['identity'])
        _recheck_path(snapshot)
    require(type(objects['directories']) is list
        and [entry['path'] for entry in objects['directories']]
            == [str(path) for path in _source_directory_paths(source)],
        'every_immutable_source_directory_required')
    for snapshot in objects['directories']:
        _fields(snapshot, ('path', 'chain', 'identity'), 'source_directory_snapshot_schema')
        with _directory(snapshot['path']) as (descriptor, chain):
            require(chain == snapshot['chain'], 'source_directory_chain_changed')
            require(_directory_metadata(os.fstat(descriptor)) == snapshot['identity'],
                'immutable_source_directory_metadata_changed')


def admission_clause(guard, authority):
    _fields(authority, ('guard_path', 'guard_sha256'), 'external_operator_guard_required')
    _path(authority['guard_path'])
    _hash(authority['guard_sha256'])
    require(guard['consumer_context_mode'] == CROSS_NAMESPACE, 'cross_namespace_guard_required')
    return dict(schema=CONTEXT_ADMISSION_SCHEMA, mode=CROSS_NAMESPACE, guard=deepcopy(authority),
        producer_binding_sha256=sha(encoded(guard['binding'])),
        proof=dict(path=guard['proof_path'], sha256=guard['proof_sha256']),
        source_epoch=deepcopy(guard['binding']['source']['epoch']), reservation_maximum_seconds=30,
        no_wall_extension=True)


def _read_admission(reference):
    _fields(reference, ('path', 'sha256', 'field_path'), 'independent_original_admission_required')
    path = reference['field_path']
    require(type(path) is list and 0 < len(path) <= 16
        and all(type(key) is str and bool(key) for key in path), 'explicit_admission_field_path')
    document, snapshot = read_pinned(reference['path'], reference['sha256'])
    for key in path:
        require(type(document) is dict and key in document, 'original_admission_clause_missing')
        document = document[key]
    return document, snapshot


def authorize_consumer_context(guard, authority, admission):
    producer = guard['binding']['environment']
    consumer = environment()
    mode = guard['consumer_context_mode']
    require(mode in (SAME_NAMESPACE, CROSS_NAMESPACE), 'known_consumer_context_mode')
    _fields(producer, ('boot_id', 'mount_namespace'), 'producer_environment_schema')
    _fields(producer['mount_namespace'], ('dev', 'ino'), 'producer_namespace_schema')
    require(all(type(value) is int and value >= 0 for value in producer['mount_namespace'].values()),
        'producer_namespace_identity')
    require(producer['boot_id'] == consumer['boot_id'], 'same_kernel_boot_required')
    snapshots = []
    if mode == SAME_NAMESPACE:
        require(admission is None, 'unexpected_admission_for_same_namespace_mode')
        require(producer == consumer, 'same_trusted_environment')
    else:
        clause, snapshot = _read_admission(admission)
        require(clause == admission_clause(guard, authority), 'exact_original_admission_context_scope')
        require(snapshot['path'] not in (authority['guard_path'], guard['proof_path']),
            'admission_must_be_independent_of_guard_and_proof')
        snapshots.append(snapshot)
    return dict(mode=mode, producer_environment=deepcopy(producer), consumer_environment=consumer,
        admission=deepcopy(admission)), snapshots


def check_consumer_environment(binding, context):
    actual = environment()
    if context is None:
        require(binding['environment'] == actual, 'same_trusted_environment')
        return
    require(binding['environment'] == context['producer_environment']
        and actual == context['consumer_environment'], 'consumer_context_changed_during_scan')
    require(actual['boot_id'] == binding['environment']['boot_id'], 'same_kernel_boot_required')
    if context['mode'] == SAME_NAMESPACE:
        require(actual == binding['environment'], 'same_trusted_environment')
    else:
        require(context['mode'] == CROSS_NAMESPACE and context['admission'] is not None,
            'independent_original_admission_required')


def clock_ns():
    import time
    return time.time_ns()


def metadata_policy():
    return dict(schema='R233_IMMUTABLE_METADATA_QUIET_AGE_V1', minimum_quiet_ns=MINIMUM_QUIET_NS,
        assumption='COHERENT_ATTRIBUTES_GRANULARITY_BELOW_WINDOW_NO_CLOCK_ROLLBACK')


def require_quiet_identity(identity, sealing_started):
    require(type(sealing_started) is int and sealing_started > 0, 'sealing_clock_required')
    require(all(type(identity[key]) is int and identity[key] >= 0 for key in ('mtime_ns', 'ctime_ns')),
        'quiet_age_timestamp_schema')
    require(max(identity['mtime_ns'], identity['ctime_ns']) <= sealing_started - MINIMUM_QUIET_NS,
        'immutable_file_too_young_or_future_timestamp')


def metadata_preflight(journal, complete_index, sealing_started):
    identities = {}
    for index in range(complete_index + 1):
        pair = _pair(journal, index)
        for identity in pair.values():
            require_quiet_identity(identity, sealing_started)
        identities[index] = pair
    return identities


def require_quiet_source(objects, sealing_started):
    for snapshot in objects['files'] + objects['directories']:
        require_quiet_identity(snapshot['identity'], sealing_started)


def validate_sealing_clock(proof):
    _fields(proof['sealing_clock'], ('started_wall_ns', 'finished_wall_ns'), 'sealing_clock_schema')
    started = proof['sealing_clock']['started_wall_ns']
    finished = proof['sealing_clock']['finished_wall_ns']
    require(type(started) is int and type(finished) is int and 0 < started <= finished <= clock_ns(),
        'sealing_clock_rollback_or_future_proof')
    require(proof['binding']['metadata_policy'] == metadata_policy(), 'exact_quiet_age_policy')
    for record in proof['records']:
        for identity in record['identities'].values():
            require_quiet_identity(identity, started)
    require_quiet_source(proof['source_objects'], started)
