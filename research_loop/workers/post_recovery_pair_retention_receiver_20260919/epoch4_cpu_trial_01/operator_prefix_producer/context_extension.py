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
