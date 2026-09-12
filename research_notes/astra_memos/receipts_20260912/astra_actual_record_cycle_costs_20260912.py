import hashlib
import json
from collections import defaultdict
from pathlib import Path


BASE = Path('/tmp')
OUTPUT = BASE / 'astra_actual_record_cycle_costs_20260912.json'
CAPSULES = {
    'formation': ('astra_rulegame_v3_formation_terminal_20260912', '05b9177bb83e800f4f9c10bbc5e34c27c7dd68e2fabe9c18c006c12e6971f90e'),
    'write': ('astra_rulegame_record_write_terminal_20260912', '26243e9a6436a859f7ed7a6ec1250a9e3a06496ec61c8eb3f85afe4d1ea308b4'),
    'readout': ('astra_rulegame_record_readout_terminal_20260912', 'f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458'),
}


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(calls):
    elapsed = [call['seconds'] for call in calls]
    return {
        'calls': len(calls),
        **{key: sum(call[key] for call in calls) for key in ('input_tokens', 'output_tokens', 'output_ceiling', 'seconds')},
        'p50_seconds': percentile(elapsed, .5),
        'p95_seconds': percentile(elapsed, .95),
        'max_seconds': max(elapsed),
    }


def main():
    result = {'method': 'Cost fields only; no scientific outcome reduction. Call latency = response.ended - request.started, empirical type-7 linear percentiles. Full reservation includes observation delay, not measured GPU utilization.', 'phases': {}}
    for phase, (stem, expected) in CAPSULES.items():
        archive = BASE / (stem + '.tgz')
        extraction = BASE / stem
        validation_path = BASE / (stem + '.tgz.validation.json')
        validation = load(validation_path)
        assert sha(archive) == expected == validation['sha256']
        for name, digest in validation['files'].items():
            path = extraction / name
            assert path.resolve().is_relative_to(extraction.resolve())
            assert sha(path) == digest, name
        release = load(next(extraction.rglob('main_release.json')))
        supervisors = [load(path) for path in extraction.rglob('supervision.json')]
        workers = sum(item['reserved_seconds'] for item in supervisors)
        assert all(item['ok'] for item in supervisors)
        assert release['full_release']
        record = {
            'capsule_sha256': expected, 'validation_sha256': sha(validation_path),
            'metadata_files_verified': len(validation['files']), 'capsule_bytes': archive.stat().st_size,
            'metadata_bytes': sum((extraction / name).stat().st_size for name in validation['files']),
            'worker_seconds': workers, 'controller_seconds': release.get('controller_seconds'),
            'full_reservation_seconds': release['full_reservation_seconds'],
            'collection_seconds': validation['collection_seconds'], 'release_utc': release['release_utc'],
        }
        calls = []
        groups = defaultdict(list)
        startup = {}
        for directory in sorted(extraction.rglob('calls')):
            cell = 'formation' if phase == 'formation' else directory.parent.parent.name
            process_path = directory.parent.parent / 'process.json'
            if phase == 'formation':
                process_path = directory.parent.parent / 'worker/process.json'
            startup[cell] = load(directory.parent / 'backend.ready.json')['ready'] - load(process_path)['started']
            for request_path in sorted(directory.glob('*.request.json')):
                request = load(request_path)
                response = load(request_path.with_name(request_path.name.replace('.request.', '.response.')))
                item = {
                    'path': str(request_path.relative_to(extraction)), 'cell': cell,
                    'role': request['request']['role'],
                    'input_tokens': len(response['response']['prompt_token_ids']),
                    'output_tokens': len(response['response']['output_token_ids']),
                    'output_ceiling': request['request']['max_tokens'],
                    'seconds': response['ended'] - request['started'],
                }
                assert item['seconds'] >= 0
                calls.append(item)
                groups[cell].append(item)
                groups[cell + '/' + item['role']].append(item)
        if calls:
            record.update(raw_calls=calls, totals=summarize(calls), groups={key: summarize(items) for key, items in groups.items()}, process_to_backend_ready_seconds=startup)
        if phase == 'write':
            fits = {}
            for path in sorted(extraction.rglob('train_manifest.json')):
                manifest = load(path)
                arm = path.parent.parent.name
                receipt = load(path.parent.parent / 'receipt.json')
                tokens = load(next(extraction.rglob(arm + '.tokens.json')))
                assert manifest['steps'] == manifest['epochs_run'] == 12
                fits[arm] = {
                    **{key: manifest[key] for key in ('steps', 'epochs_run', 'tokens', 'train_seconds', 'wall_seconds', 'train_tokens_seen', 'tokens_per_s', 'lora', 'truncation')},
                    'input_presentations': manifest['tokens']['total'] * manifest['epochs_run'],
                    'target_presentations': manifest['tokens']['target'] * manifest['epochs_run'],
                    'padded_input_positions': sum(map(len, tokens['batch']['input_ids'])) * manifest['steps'],
                    'saved_tensors': len(receipt['saved_tensors']),
                    'tensor_payload_bytes': max(item['data_offsets'][1] for item in receipt['saved_tensors'].values()),
                    'saved_dtypes': sorted({item['dtype'] for item in receipt['saved_tensors'].values()}),
                    'adapter_sha256': receipt['files']['adapter_model.safetensors'],
                }
            record['fits'] = fits
        result['phases'][phase] = record
    phases = result['phases']
    assert phases['formation']['totals']['calls'] == 60
    prior_path = BASE / 'astra_rulegame_record_readout_independent_analysis_20260912.json'
    prior = load(prior_path)['costs']['raw_totals']
    for ours, previous in [('calls', 'requests'), ('input_tokens', 'native_input_tokens'), ('output_tokens', 'native_output_tokens'), ('output_ceiling', 'output_token_ceiling'), ('seconds', 'generation_seconds')]:
        assert abs(phases['readout']['totals'][ours] - prior[previous]) < 1e-7
    result['prior_analysis_sha256'] = sha(prior_path)
    result['full_reservation_minutes_sum'] = sum(item['full_reservation_seconds'] for item in phases.values()) / 60
    result['worker_minutes_sum'] = sum(item['worker_seconds'] for item in phases.values()) / 60
    pair_minutes = (phases['write']['full_reservation_seconds'] + phases['readout']['full_reservation_seconds']) / 60
    result['conditional_proxies'] = {
        'three_fit_readout_pairs_minutes': 3 * pair_minutes,
        'three_pairs_with_new_formation_each_minutes': 3 * result['full_reservation_minutes_sum'],
        'process_pair_record_analog_minutes': pair_minutes,
        'process_pair_analog_nontraining_minutes': pair_minutes - sum(fit['train_seconds'] for fit in phases['write']['fits'].values()) / 60,
        'scope': 'Linear observed-charge proxies only, not prediction intervals; process native lengths not known.',
    }
    with OUTPUT.open('x') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')
    for phase, record in phases.items():
        print(phase, record.get('totals'), 'workers', record['worker_seconds'])
        for group, summary in record.get('groups', {}).items():
            print(group, summary['calls'], summary['p50_seconds'], summary['p95_seconds'])
    print('minutes', result['full_reservation_minutes_sum'], result['conditional_proxies'])


if __name__ == '__main__':
    main()
