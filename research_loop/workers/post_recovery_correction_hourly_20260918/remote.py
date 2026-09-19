"""Documented read-only /proc, guard and original TRAIN journal introspection."""


def source_manifest(source):
    files = sorted(path for folder in ('gpu', 'organism_v6')
        for path in Path(source).joinpath(folder).glob('*.py'))
    if not files or len(files) > 2048:
        raise ValueError('bounded_source_manifest_required')
    hashes = {}
    total = 0
    for path in files:
        raw, unused = read_stable(path, 4 * 1024 * 1024)
        total += len(raw)
        if total > 32 * 1024 * 1024:
            raise ValueError('source_manifest_byte_limit')
        hashes[str(path.relative_to(source))] = hashlib.sha256(raw).hexdigest()
    return digest(hashes)


def identity(target):
    if time.time() >= target.get('until_unix', float('inf')):
        raise ValueError('source_observer_horizon_elapsed')
    process = Path('/proc') / str(target['pid'])
    fields = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    command = process.joinpath('cmdline').read_bytes().decode().rstrip('\0').split('\0')
    if fields[19] != str(target['start_ticks']) or fields[0] == 'Z' or '--config' not in command:
        raise ValueError('exact_source_process_required')
    if str(process.joinpath('cwd').resolve()) != target['source']:
        raise ValueError('exact_receiving_source_required')
    guard = Path(command[command.index('--config') + 1])
    if not guard.is_absolute():
        guard = Path(target['source']) / guard
    raw, unused = read_stable(guard)
    if hashlib.sha256(raw).hexdigest() != target['guard_sha256']:
        raise ValueError('immutable_guard_binding')
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    manifest = source_manifest(target['source'])
    if target.get('boot_id', boot_id) != boot_id or target.get('source_manifest_sha256', manifest) != manifest:
        raise ValueError('source_epoch_changed_new_owner_binding_required')
    return dict(pid=target['pid'], start_ticks=fields[19], guard_sha256=target['guard_sha256'],
        boot_id=boot_id, source_manifest_sha256=manifest,
        command_sha256=hashlib.sha256(json.dumps(command).encode()).hexdigest())


def inspect(target, references, probe=False):
    if time.time() >= target['until_unix']:
        raise ValueError('source_observer_horizon_elapsed')
    before = identity(target)
    records = Path(target['root']) / 'stream/records'
    loaded, unused = verified(records / f'{target["loaded_index"]:020d}.json', target['journal_id'])
    if loaded['kind'] != 'LOADED' or loaded['sha256'] != target['loaded_sha256'] or loaded['document']['pid'] != target['pid']:
        raise ValueError('actual_current_LOAD_and_pid')
    if probe:
        if identity(target) != before:
            raise ValueError('source_identity_changed_during_read')
        return dict(identity=before, loaded_sha256=loaded['sha256'], remote_writes=0, native_signals=0, model_calls=0)
    revalidated = []
    if len(references) > 80:
        raise ValueError('bounded_historical_reference_set')
    for reference in references:
        row, receipt = verified(records / f'{reference["index"]:020d}.json', target['journal_id'])
        if row['sha256'] != reference['sha256'] or row['kind'] != reference['kind']:
            raise ValueError('original_annotation_record_changed')
        if reference.get('response_text_sha256') and hashlib.sha256(row['document']['response']['raw'].encode()).hexdigest() != reference['response_text_sha256']:
            raise ValueError('original_child_text_projection_changed')
        revalidated.append({key: reference[key] for key in ('index', 'kind', 'sha256')})
    evidence = collect(target['root'], target['journal_id'], maximum=240)
    if identity(target) != before:
        raise ValueError('source_identity_changed_during_read')
    return dict(identity=before, historical_references=revalidated, evidence=evidence,
        remote_writes=0, native_signals=0, model_calls=0)
