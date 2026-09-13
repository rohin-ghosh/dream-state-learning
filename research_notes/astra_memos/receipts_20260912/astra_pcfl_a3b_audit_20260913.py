from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '/data/home/rohing/dream-state')
from gpu import astra_pcfl_interface_dev as driver

root = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_a3b_20260913_attempt1/unpacked/pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1')
stage = 'A3B_NEWLINE_FRAMED_SMOKE'
directory = root / stage
read = lambda path: json.loads(path.read_text())
checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if checksum(Path(driver.__file__)) != 'b07004bfc1f27e025ee4f611ac3c7d51219ea8bda751b1f399b6e87ac9ced8de':
    raise ValueError('analysis source drift')
completed = read(directory / 'completed.json')
report = read(directory / 'records/report.json')
for name, digest in completed['files'].items():
    if checksum(directory / name) != digest:
        raise ValueError('inventory mismatch: ' + name)
stops, suffixes = Counter(), []
for index, attempt in enumerate(report['attempts']):
    raw = read(directory / 'actor' / f'call_{index:04d}.raw.json')['raw']
    response = read(directory / 'actor' / f'call_{index:04d}.response.json')
    render = read(directory / 'actor' / f'call_{index:04d}.render.json')
    expected = driver.sampling_for(stage, attempt['request'], attempt['limits'])
    if render['sampling'] != expected or response['response']['text'] != raw['text']:
        raise ValueError('native sampling/response drift')
    driver._validate_frame(response['decoded'], raw, expected)
    stops[str(raw['stop_reason'])] += 1
    if raw['stop_reason'] == '\n':
        suffixes.append(len(response['decoded']) - len(raw['text']))
first = [report['attempts'][result['slots'][0]['attempt_index']]['response']['text'] for result in report['results']]
output = {'status': 'POST_OUTCOME_NATIVE_FRAME_AUDIT_PASS', 'calls': report['calls'],
    'first_exact_think': sum(bool(re.fullmatch(r"THINK [^\r\n]+", raw)) and any(not char.isspace() for char in raw[6:]) for raw in first),
    'thought_turns': sum(result['thinks'] for result in report['results']),
    'legal_routes': sum(bool(result['score'] and result['score']['legal']) for result in report['results']),
    'stop_reasons': dict(stops), 'lf_suffix_character_counts': suffixes,
    'prompt_tokens': sum(attempt['response']['prompt_tokens'] for attempt in report['attempts']),
    'output_tokens': sum(attempt['response']['output_tokens'] for attempt in report['attempts']),
    'summary': report['summary'], 'replay': read(directory / 'replay.json'),
    'completed_file_sha256': checksum(directory / 'completed.json')}
destination = Path(sys.argv[2] if len(sys.argv) > 2 else '/tmp/astra_pcfl_a3b_audit_20260913_attempt1.json')
with destination.open('x') as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(output, indent=2))
