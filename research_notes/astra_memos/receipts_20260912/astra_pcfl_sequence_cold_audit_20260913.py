from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

base = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_sequence_cold_screen_20260913_attempt1')
read = lambda path: json.loads(path.read_text())
checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
with tarfile.open(base / 'evidence.tar') as archive:
    files = [member for member in archive if member.isfile()]
    assert len(files) == len({member.name for member in files})
    for member in files:
        assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        with archive.extractfile(member) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == checksum(base / 'unpacked' / member.name)
material = read(base / 'unpacked/astra_pcfl_event_sequence_material_20260913_attempt4.json')
output = {'status': 'COLD_CAPTURE_AND_ARCHIVE_AUDIT_PASS', 'archive_files_verified': len(files),
          'states': {}, 'retention_fraction': None, 'retention_reason': 'NO_PRE_CORRECT_A',
          'warm_descendants_executed': False, 'acquisition_pass': False, 'general_G3_claim': False}
for state in ('NO_WRITE', 'S_A'):
    root = base / ('unpacked/pcfl_event_sequence_readout_' + state + '_20260913_attempt1')
    directory = root / 'readout'
    collection = read(root / 'collection.json')
    completed = read(directory / 'completed.json')
    scores = read(directory / 'scores.json')
    identity = read(directory / 'actor/identity.json')
    assert collection['status'] == 'COMPLETED' and collection['returncode'] == 0 and collection['errors'] == []
    assert collection['gpu_released'] is True and identity['pid'] == collection['worker_identity']['pid']
    assert completed['kind'] == 'NATIVE' and completed['state'] == state and completed['calls'] == 16
    assert completed['fits'] == completed['updates'] == 0 and completed['truncated'] == 0
    for name, digest in completed['files'].items():
        assert checksum(directory / name) == digest, name
    route = completed['route']
    assert route == identity['identity']['route']
    if state == 'NO_WRITE':
        assert route['arm'] == 'NO_WRITE_C0' and route['lora_request'] is None
    else:
        assert route['arm'] == 'AUTH_WRITE' and route['lora_request']['id'] == 1
        assert checksum(directory / 'adapter/adapter_model.safetensors') == '82d98aed28fe4bcd0a6c18e49111b48ff0b92b37c3ef9459e1993edd38e661b2'
    finishes = Counter()
    prompt_tokens = output_tokens = misses = event_prefixes = usable_false = 0
    for index, row in enumerate(material['spec']['roster']):
        response = read(directory / f'response_{index:04d}.json')
        raw = read(directory / 'actor' / f'call_{index:04d}.raw.json')['raw']
        returned = read(directory / 'actor' / f'call_{index:04d}.response.json')
        requested = read(directory / 'actor' / f'call_{index:04d}.request.json')
        score = scores['results'][index]
        target = material['spec']['records'][index % 8]['target']
        assert requested['row'] == row and response['id'] == score['id'] == row['id']
        assert returned['response'] == response and response['text'] == raw['text'] == score['raw']
        assert response['route'] == raw['route'] == route
        assert response['output_tokens'] == len(raw['output_token_ids'])
        assert response['prompt_tokens'] == len(raw['prompt_token_ids'])
        assert score['strict_stop'] == (raw['finish_reason'] == 'stop' and raw['text'] == target)
        assert score['strict_stop'] is False
        finishes[raw['finish_reason']] += 1
        misses += raw['text'] == 'MISS'
        event_prefixes += raw['text'].startswith('EVENT ')
        usable_false += score['score']['usable_false_row']
        prompt_tokens += response['prompt_tokens']
        output_tokens += response['output_tokens']
    assert completed['tokens'] == {'prompt': prompt_tokens, 'output': output_tokens}
    output['states'][state] = {'calls': 16, 'panels': completed['panels'], 'finish_reasons': dict(finishes),
        'exact_MISS': misses, 'EVENT_prefix': event_prefixes, 'scorer_usable_false_rows': usable_false,
        'tokens': completed['tokens'], 'elapsed_seconds': {'outer': collection['elapsed_seconds'], **completed['elapsed_seconds']},
        'completed_file_sha256': checksum(directory / 'completed.json')}
destination = Path('/tmp/astra_pcfl_sequence_cold_audit_20260913_attempt1.json')
with destination.open('x') as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(output, indent=2))
