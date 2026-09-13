from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '/data/home/rohing/dream-state')
from gpu import astra_pcfl_interface_dev as driver

base = Path('/data/home/rohing/dream-state/gpu_artifacts_local/pcfl_structured_action_20260913_attempt1')
archive_pin = 'a3745deee039131c037ac2e645e6ab54e6d437eaebd848b8452bc5cad7bdd37c'


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(value, message):
    if not value:
        raise ValueError(message)


require(checksum(base / 'evidence.tar') == archive_pin, 'archive hash')
require(checksum(Path(driver.__file__)) == 'b62f7f4ffbea11458342223b6118ee89ea60effde6294273f002a152f5e2fbfb', 'driver source drift')
output = {'schema': 'pcfl.structured_controls.posthoc_trace_summary.v1', 'archive_sha256': archive_pin,
          'analysis_kind': 'POST_OUTCOME_AGGREGATION_OF_UNCHANGED_ENDPOINTS', 'runs': [],
          'learning_claim': False, 'autonomy_claim': False, 'full_assay_qualified': False}
pair = []
for stage in driver.STRUCTURED_STAGES:
    root = base / 'unpacked' / ('pcfl_interface_' + stage.lower() + '_20260913_attempt1')
    outer = root.with_name(root.name + '.outer')
    stage_root = root / stage
    manifest = read(root / 'manifest.json')
    collection = read(outer / 'collection.json')
    completed = read(stage_root / 'completed.json')
    report = read(stage_root / 'records/report.json')
    for name, digest in completed['files'].items():
        require(checksum(stage_root / name) == digest, 'stage inventory drift: ' + name)
    for name, entry in collection['files'].items():
        require(checksum(outer / name) == entry['sha256'], 'outer inventory drift: ' + name)
    require(collection['status'] == 'COMPLETED' and collection['errors'] == [] and collection['returncode'] == 0, 'failed collection')
    require(collection['manifest_file_sha256'] == checksum(root / 'manifest.json'), 'manifest join')
    require(checksum(stage_root / 'completed.json') == checksum(outer / 'stage_completed.json'), 'completion copy')
    require(read(outer / 'worker_release.json')['value']['owned_group_released'] is True, 'unreleased worker')
    require(report['summary'] == completed['summary'] == collection['stage_summary'], 'summary join')
    require(report['calls'] == len(report['attempts']) == completed['actual_calls'], 'call denominator')
    tasks = manifest['roster']['tasks']
    require(len(tasks) == len(report['results']) == 8, 'task denominator')
    pair.append([(task['case_id'], task['seed'], task['messages']) for task in tasks])
    checks, read_kinds = [], Counter()
    for task, result in zip(tasks, report['results']):
        require(task['id'] == result['id'] and result['status'] == 'SCORED', 'task identity/status')
        if result['reason'] == 'ROUTE':
            require(driver.core.score_route(driver.core.from_data(task['cell']), task['goal'], result['raw']) == result['score'], 'raw route score drift')
        for service in result['services']:
            read_kinds[driver.core.parse_read(service['request'])[0]] += 1
            require(driver.core.read_query(task['queries'], service['request'])['raw'] == service['raw'], 'service byte drift')
        first = report['attempts'][result['slots'][0]['attempt_index']]['response']['text']
        checks.append({'case': task['case_id'], 'first_raw': first, 'reason': result['reason'],
                       'reads': result['reads'], 'served': result['served_reads'], 'score': result['score']})
    for index, attempt in enumerate(report['attempts']):
        request, limits = attempt['request'], attempt['limits']
        captured = read(stage_root / 'actor' / f'call_{index:04d}.raw.json')
        rendered = read(stage_root / 'actor' / f'call_{index:04d}.render.json')
        expected = driver.sampling_for(stage, request, limits)
        require(rendered['sampling'] == expected, 'sampling mismatch')
        require(captured['raw']['text'] == attempt['response']['text'], 'raw/response drift')
        if captured['raw']['finish_reason'] == 'stop':
            require(re.fullmatch(expected['structured_outputs']['regex'], captured['raw']['text']) is not None, 'stopped output outside regex')
    output['runs'].append({'stage': stage, 'manifest_sha256': checksum(root / 'manifest.json'),
        'report_sha256': checksum(stage_root / 'records/report.json'), 'collection_sha256': checksum(outer / 'collection.json'),
        'worker': collection['worker_identity'], 'outer_elapsed_seconds': collection['elapsed_seconds'],
        'summary': report['summary'], 'calls': report['calls'], 'possible_calls': report['possible_calls'],
        'reasons': dict(Counter(result['reason'] for result in report['results'])),
        'read_commands': sum(result['reads'] for result in report['results']), 'read_kinds': dict(read_kinds),
        'served_reads': sum(result['served_reads'] for result in report['results']),
        'miss_returns': sum(service['raw'] == 'MISS' for result in report['results'] for service in result['services']),
        'legal_routes': sum(bool(result['score'] and result['score']['legal']) for result in report['results']),
        'prompt_tokens': sum(attempt['response']['prompt_tokens'] for attempt in report['attempts']),
        'output_tokens': sum(result['actor_tokens'] for result in report['results']),
        'returned_tokens': sum(result['returned_tokens'] for result in report['results']), 'tasks': checks})
require(pair[0] == pair[1], 'paired public cases/prompts/seeds differ')
output['paired_public_prompts_and_seeds_equal'] = True
destination = Path(sys.argv[2] if len(sys.argv) > 2 else '/tmp/astra_pcfl_structured_analysis_20260913_attempt1.json')
with destination.open('x') as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps({'path': str(destination), 'sha256': checksum(destination),
                  'runs': [{key: value for key, value in run.items() if key != 'tasks'} for run in output['runs']]}, indent=2))
