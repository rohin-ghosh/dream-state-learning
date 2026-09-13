from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '/data/home/rohing/dream-state')
from gpu import astra_pcfl_interface_dev as driver

base = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_a3c_20260913_attempt1')
root = base / 'unpacked/pcfl_interface_a3c_structured_framed_smoke_20260913_attempt1'
directory = root / 'A3C_STRUCTURED_FRAMED_SMOKE'
outer = root.with_name(root.name + '.outer')
read = lambda path: json.loads(path.read_text())
checksum = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert checksum(Path(driver.__file__)) == '461aef9a62919dd3b28acdc40b167715c262a3e69f39b0835dfc6702c61d661c'
assert checksum(base / 'evidence.tar') == '560c502d9f94a89f756a2bfe2363d92b55649717beede405b4640c0b2964958e'
with tarfile.open(base / 'evidence.tar') as archive:
    files = [member for member in archive if member.isfile()]
    assert len(files) == len({member.name for member in files})
    for member in files:
        assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
        with archive.extractfile(member) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == checksum(base / 'unpacked' / member.name)
completed = read(directory / 'completed.json')
report = read(directory / 'records/report.json')
roster = read(root / 'roster.json')
collection = read(outer / 'collection.json')
assert collection['status'] == 'COMPLETED' and not collection['errors'] and collection['returncode'] == 0
assert read(outer / 'worker_release.json')['value']['owned_group_released'] is True
for name, digest in completed['files'].items():
    assert checksum(directory / name) == digest, name
stops, suffixes = Counter(), []
for index, attempt in enumerate(report['attempts']):
    raw = read(directory / 'actor' / f'call_{index:04d}.raw.json')['raw']
    response = read(directory / 'actor' / f'call_{index:04d}.response.json')
    render = read(directory / 'actor' / f'call_{index:04d}.render.json')
    expected = driver.sampling_for(roster['stage'], attempt['request'], attempt['limits'])
    assert render['sampling'] == expected
    assert response['response'] == attempt['response']
    assert response['response']['text'] == raw['text']
    assert response['response']['output_tokens'] == len(raw['output_token_ids'])
    assert response['response']['prompt_tokens'] == len(raw['prompt_token_ids'])
    driver._validate_structured_frame(response['decoded'], raw, expected)
    assert re.fullmatch(driver.THINK_ROUTE_REGEX, raw['text'])
    stops[str(raw['stop_reason'])] += 1
    if raw['stop_reason'] == '\n':
        suffixes.append(len(response['decoded']) - len(raw['text']))
first = [report['attempts'][result['slots'][0]['attempt_index']]['response']['text'] for result in report['results']]
first_count = sum(bool(re.fullmatch(r'THINK [^\r\n]+', text)) and bool(text[6:].strip()) for text in first)
previous_root = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_a3b_20260913_attempt1/unpacked/pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1')
previous = read(previous_root / 'roster.json')
assert previous['limits'] == roster['limits']
for old, new in zip(previous['tasks'], roster['tasks'], strict=True):
    assert old['messages'] == new['messages'] and old['seed'] == new['seed']
output = {'status': 'POST_OUTCOME_NATIVE_STRUCTURED_FRAME_AUDIT_PASS', 'calls': report['calls'],
    'archive_files_verified': len(files), 'first_exact_think': first_count,
    'joint_physical_gate_passed': first_count >= 7 and report['summary']['thought_interface_tasks'] >= 7,
    'thought_turns': sum(result['thinks'] for result in report['results']),
    'strict_terminals': sum(bool(result['score'] and result['score']['strict']) for result in report['results']),
    'legal_routes': sum(bool(result['score'] and result['score']['legal']) for result in report['results']),
    'stop_reasons': dict(stops), 'lf_suffix_character_counts': suffixes,
    'prompt_tokens': sum(attempt['response']['prompt_tokens'] for attempt in report['attempts']),
    'output_tokens': sum(attempt['response']['output_tokens'] for attempt in report['attempts']),
    'same_a3b_prompts_seeds_budgets': True, 'summary': report['summary'],
    'replay': read(directory / 'replay.json'), 'outer_elapsed_seconds': collection['elapsed_seconds'],
    'completed_file_sha256': checksum(directory / 'completed.json')}
destination = Path(sys.argv[2] if len(sys.argv) > 2 else '/tmp/astra_pcfl_a3c_audit_20260913_attempt1.json')
with destination.open('x') as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(output, indent=2))
