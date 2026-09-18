"""Targeted original-birth metadata checks, sharing the first census read budget."""


def followup(previous):
    reader = Reader()
    reader.metadata_bytes = previous['reads']['metadata_bytes']
    reader.journal_bytes = previous['reads']['journal_bytes']
    reader.record_count = previous['reads']['record_count']
    result = dict(life_id=previous['life_id'], source_root=previous['source_root'])
    try:
        root = Path(previous['source_root'])
        before, unused = identity(previous['native_identity']['pid'])
        require(all(before[key] == previous['native_identity'][key]
            for key in ('pid', 'start_ticks', 'argv_sha256', 'boot_id')), 'same_observed_native')
        manifest, unused = reader.document(root / 'stream/JOURNAL.json')
        birth_record, unused = record(reader, root, 0, manifest)
        state = birth_record['document']['state']['state']
        context = {key: state['history'][key] for key in ('system_prompt', 'birth_prompt')}
        initial, initial_ref = reader.document(root / 'checkpoints/initial/COMMIT.json')
        result['birth_experiment_matches_initial'] = state.get('experiment') == initial.get('experiment')
        result['initial_experiment_context_matches_history'] = {
            key: initial.get('experiment', {}).get(key) == value for key, value in context.items()}
        plan_paths = [Path(previous['registry_birth_plan']['path'])] + [Path(item['reference']['path'])
            for item in previous['original_plan_candidates']]
        candidates = []
        for path in plan_paths:
            plan, reference = reader.document(path)
            candidates.append(dict(reference=reference, fields={key: dict(
                plan_sha256=hashlib.sha256(plan.get(key, '').encode()).hexdigest(),
                history_sha256=hashlib.sha256(value.encode()).hexdigest(),
                plan_bytes=len(plan.get(key, '').encode()), history_bytes=len(value.encode()),
                exact_equal=plan.get(key) == value, stripped_equal=plan.get(key, '').strip() == value.strip(),
                initial_experiment_equal=initial.get('experiment', {}).get(key) == plan.get(key))
                for key, value in context.items()},
                initial_experiment_matches_plan=bool(initial.get('experiment')) and all(
                    plan.get(key) == value for key, value in initial.get('experiment', {}).items()
                    if key != 'seed_initialization')))
        result['plan_comparisons'] = candidates
        result['nearby_plan_names'] = {str(directory): [name for name in names(directory)
            if name.endswith('.json') and ('PLAN' in name.upper() or 'CONFIG' in name.upper())]
            for directory in (root.parent, root.parent / 'control1') if directory.is_dir()}
        pin_bindings = []
        for entry in previous['native_configurations']:
            config, unused = reader.document(entry['reference']['path'])
            require(unused['sha256'] == entry['reference']['sha256'], 'same_guard_config')
            pins = config.get('source_pins', {})
            for source in previous['native_source_pins']:
                if isinstance(pins, dict):
                    expected = pins.get(source['path'])
                else:
                    expected = next((item['sha256'] for item in pins
                        if item.get('path') == source['path']), None)
                if expected is not None:
                    actual_raw = reader.raw(source['path'])
                    actual_sha = hashlib.sha256(actual_raw).hexdigest()
                    pin_bindings.append(dict(source=source, guard=entry['reference'],
                        expected_sha256=expected, actual_sha256=actual_sha,
                        matches=expected == actual_sha == source['sha256']))
        result['guard_native_source_bindings'] = pin_bindings
        after, unused = identity(before['pid'])
        require(all(before[key] == after[key] for key in ('pid', 'start_ticks', 'argv_sha256', 'boot_id')),
            'same_native_after_metadata')
        result['identity_rechecked'] = True
    except Exception as error:
        result['error'] = dict(type=type(error).__name__, reason=str(error))
    result['cumulative_reads'] = dict(metadata_bytes=reader.metadata_bytes,
        journal_bytes=reader.journal_bytes, record_count=reader.record_count)
    return result


if __name__ == '__main__':
    request = json.loads(sys.argv[1])
    print(json.dumps(dict(observed_unix=time.time(), lives=[followup(item) for item in request['lives']]),
        sort_keys=True))
