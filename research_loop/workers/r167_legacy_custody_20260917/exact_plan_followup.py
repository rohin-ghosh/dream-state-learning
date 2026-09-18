"""Bounded known control PLAN/GUARD references and relative native-source pins."""


def exact_followup(previous, structure):
    reader = Reader()
    for key in ('metadata_bytes', 'journal_bytes', 'record_count'):
        setattr(reader, key, structure['cumulative_reads'][key])
    result = dict(life_id=previous['life_id'], source_bindings=[], control_plans=[])
    try:
        before, unused = identity(previous['native_identity']['pid'])
        require(all(before[key] == previous['native_identity'][key]
            for key in ('pid', 'start_ticks', 'argv_sha256', 'boot_id', 'cwd')), 'same_native')
        for entry in previous['native_configurations']:
            config, reference = reader.document(entry['reference']['path'])
            require(reference['sha256'] == entry['reference']['sha256'], 'unchanged_guard')
            expected = config.get('source_pins', {}).get('gpu/orch_r125_continual_native.py')
            if expected is not None:
                for source in previous['native_source_pins']:
                    raw = reader.raw(source['path'])
                    actual = hashlib.sha256(raw).hexdigest()
                    require(actual == expected == source['sha256'], 'guard_native_source_pin')
                    result['source_bindings'].append(dict(source=source, guard=reference,
                        relative_path='gpu/orch_r125_continual_native.py', verified=True))
        root = Path(previous['source_root'])
        manifest, unused = reader.document(root / 'stream/JOURNAL.json')
        initial_record, unused = record(reader, root, 0, manifest)
        context = {key: initial_record['document']['state']['state']['history'][key]
            for key in ('system_prompt', 'birth_prompt')}
        directories = structure['control_directory_names']
        require(len(directories) <= 8, 'bounded_known_control_directories')
        for name in directories:
            directory = root.parent / name
            plan_path = directory / 'PLAN.json'
            if not plan_path.is_file():
                continue
            plan, plan_reference = reader.document(plan_path)
            entry = dict(plan=plan_reference, root_matches=plan.get('root') == str(root),
                exact_birth_context_matches=all(plan.get(key) == value for key, value in context.items()))
            guard_path = directory / 'GUARD.json'
            if guard_path.is_file():
                guard, guard_reference = reader.document(guard_path)
                entry['guard'] = guard_reference
                entry['resume'] = guard.get('resume')
                entry['guard_plan_matches'] = guard.get('plan_path') == str(plan_path) and guard.get('plan_sha256') == plan_reference['sha256']
            result['control_plans'].append(entry)
        after, unused = identity(before['pid'])
        require(all(before[key] == after[key] for key in ('pid', 'start_ticks', 'argv_sha256', 'boot_id')),
            'same_native_after_read')
        result['identity_rechecked'] = True
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, reason=str(error))
    result['cumulative_reads'] = dict(metadata_bytes=reader.metadata_bytes,
        journal_bytes=reader.journal_bytes, record_count=reader.record_count)
    return result


if __name__ == '__main__':
    request = json.loads(sys.argv[1])
    print(json.dumps(dict(observed_unix=time.time(), lives=[exact_followup(item['previous'], item['structure'])
        for item in request['lives']]), sort_keys=True))
