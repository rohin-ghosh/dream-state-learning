import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REPORT = ROOT / 'research_loop/workers/replication_sprint_20260919/operations/SAMPLING_V3_FINAL_REPORT.json'
REMOTE = '''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

total_read = 0
def read(path):
    global total_read
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), 'regular_source'
    size = path.stat().st_size
    assert size <= 2000000, 'single_source_limit'
    assert total_read + size <= 25000000, 'total_source_limit'
    raw = path.read_bytes()
    total_read += len(raw)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

output = {'observed_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'all18_completed_development_cells_child_outputs_only', 'cells': [], 'private_reference_panels_read': False, 'parent_publications': 0, 'provider_calls': 0, 'source_mutations': 0}
for selected in selections:
    cell, cell_sha = read(selected['path'])
    assert cell_sha == selected['sha256'], 'unchanged_completed_cell'
    assert cell['seed'] == selected['seed'] and cell['contest_id'] == selected['contest_id']
    row = dict(selected, events=[])
    for number, expected in enumerate(cell['events'], 1):
        path = Path(selected['path']).parent / f'{number:04d}.json'
        document, file_sha = read(path)
        assert document['event'] == expected, 'same_event'
        generation = document['generation']
        assert generation['messages'] == document['request'], 'actual_prompt_identity'
        assert digest(document['request']) == expected['origin']['request_sha256']
        assert digest(generation) == expected['origin']['response_sha256']
        assert hashlib.sha256(generation['raw'].encode()).hexdigest() == expected['origin']['text_sha256']
        assert len(generation['token_ids']) == expected['actual_generated_tokens']
        if number == 1:
            row['scene_text_as_shown_to_child'] = document['request'][1]['content']
        judgments = []
        for result in expected['score']['results']:
            outcome = result['result']
            judgments.append({'caption_sha256': result['caption_sha256'], **{key: outcome.get(key) for key in ('rank', 'accepted', 'status', 'cached')}})
        row['events'].append({'number': number, 'path': str(path), 'file_sha256': file_sha, 'stage': expected['origin']['stage'], 'text_sha256': expected['origin']['text_sha256'], 'generated_tokens': expected['actual_generated_tokens'], 'prompt_tokens': expected['prompt_tokens'], 'terminal': expected['terminal'], 'truncated': expected['truncated'], 'raw_child_output': generation['raw'], 'judgments': judgments, 'started_unix': generation['started_unix'], 'finished_unix': generation['finished_unix']})
    output['cells'].append(row)
output['source_bytes_read'] = total_read
print(json.dumps(output, ensure_ascii=False))
'''


def main():
    report_bytes = REPORT.read_bytes()
    report = json.loads(report_bytes)
    selections = [dict(arm=row['arm'], seed=row['seed'], contest_id=cell['contest_id'], path=cell['path'], sha256=cell['sha256']) for row in report['rows'] for cell in row['cells']]
    assert len(selections) == 18
    result = subprocess.run(['bash', 'gpu/ovx4_ssh.sh', 'python3', '-'], cwd=ROOT,
        input='selections = ' + repr(selections) + '\n' + REMOTE,
        text=True, capture_output=True, timeout=40, check=True)
    assert len(result.stdout.encode()) < 2000000
    document = json.loads(result.stdout)
    document['report_sha256'] = hashlib.sha256(report_bytes).hexdigest()
    document['capture_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output = HERE / 'CHILD_OUTPUTS.json'
    with output.open('x') as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'path': str(output.relative_to(ROOT)), 'cells': len(document['cells']), 'events': sum(len(cell['events']) for cell in document['cells']), 'source_bytes_read': document['source_bytes_read'], 'projection_bytes': output.stat().st_size}))


if __name__ == '__main__':
    main()
