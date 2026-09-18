"""Read only guard source-pin structure and original control directory names."""


def project(previous, budget):
    reader = Reader()
    reader.metadata_bytes = budget['metadata_bytes']
    reader.journal_bytes = budget['journal_bytes']
    reader.record_count = budget['record_count']
    result = dict(life_id=previous['life_id'], guard_pin_structures=[])
    for entry in previous['native_configurations']:
        config, reference = reader.document(entry['reference']['path'])
        require(reference['sha256'] == entry['reference']['sha256'], 'same_guard_config')
        pins = config.get('source_pins')
        if pins:
            result['guard_pin_structures'].append(dict(reference=reference,
                type=type(pins).__name__, sample=list(pins.items())[:2] if isinstance(pins, dict) else pins[:2]))
    root = Path(previous['source_root'])
    result['control_directory_names'] = [name for name in names(root.parent)
        if 'control' in name.lower() and (root.parent / name).is_dir()]
    result['cumulative_reads'] = dict(metadata_bytes=reader.metadata_bytes,
        journal_bytes=reader.journal_bytes, record_count=reader.record_count)
    return result


if __name__ == '__main__':
    request = json.loads(sys.argv[1])
    print(json.dumps(dict(observed_unix=time.time(), lives=[project(item['previous'], item['budget'])
        for item in request['lives']]), sort_keys=True))
