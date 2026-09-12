import collections
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(root):
    report = read(root / 'supplementary_report.json')
    done = read(root / 'COMPLETED.json')
    manifest = read(root / 'probe.json')
    audit = read(root / 'MAIN_TERMINAL_AUDIT.json')
    assert file_hash(root / 'supplementary_report.json') == done['report_sha256'] == audit['report_sha256']
    assert audit['native_reduction_equal'] and audit['released'] and audit['cleanup_count'] == 3
    assert file_hash(root / 'requests.json') == manifest['requests_sha256']
    requests = {row['request_id']: row for row in read(root / 'requests.json')}
    assert len(requests) == 768
    result, choices, seen = {}, {}, set()
    for state in manifest['states']:
        directory = root / state
        assert file_hash(directory / 'records.jsonl') == read(directory / 'DONE.json')['records_sha256']
        records = [json.loads(line) for line in (directory / 'records.jsonl').read_text().splitlines()]
        assert len(records) == 256
        assert collections.Counter(row['operation'] for row in records) == {'generate': 128, 'score': 128}
        generated = []
        for record in records:
            request = requests[record['request_id']]
            assert record['request_id'] not in seen and request['state'] == record['state'] == state
            seen.add(record['request_id'])
            if record['operation'] != 'generate':
                continue
            output = record['output']
            assert output['text'].strip() in ('ACT: -mem2reg', 'ACT: -gvn')
            generated.append(dict(index=request['audit']['index'], slot=request['audit']['slot'],
                mode=request['audit']['mode'], template=request['audit']['template'],
                targets=request['audit']['targets'], choice=int(output['text'].strip() == 'ACT: -gvn'),
                tokens=len(output['generated_ids']), truncated=output['truncated']))
        generated.sort(key=lambda row: row['index'])
        assert [row['index'] for row in generated] == list(range(128))
        choices[state] = [row['choice'] for row in generated]
        mappings = {}
        for mapping in ('W+', 'W-'):
            correct = sum(row['choice'] == row['targets'][mapping] for row in generated)
            assert correct == 128 * report['states'][state]['by_mapping'][mapping]['generation_accuracy']
            details = []
            for template in sorted({row['template'] for row in generated}):
                selected = [row for row in generated if row['template'] == template]
                assert len(selected) == 16
                details.append(dict(template=template, n=16,
                    correct=sum(row['choice'] == row['targets'][mapping] for row in selected)))
            key_details = []
            for slot in range(8):
                for mode in range(2):
                    selected = [row for row in generated if row['slot'] == slot and row['mode'] == mode]
                    assert len(selected) == 8
                    key_details.append(dict(slot=slot, mode=mode, n=8,
                        correct=sum(row['choice'] == row['targets'][mapping] for row in selected)))
            mappings[mapping] = dict(correct=correct, n=128, templates=details, keys=key_details,
                held_correct=64 * report['states'][state]['by_mapping'][mapping]['original_held_generation_BA'],
                held_n=64)
        result[state] = dict(mappings=mappings,
            actions=dict(collections.Counter('-gvn' if row['choice'] else '-mem2reg' for row in generated)),
            actual_generated_tokens=sum(row['tokens'] for row in generated),
            truncated=sum(row['truncated'] for row in generated),
            generation_seconds=sum(row['seconds'] for row in records if row['operation'] == 'generate'),
            scoring_seconds=sum(row['seconds'] for row in records if row['operation'] == 'score'))
    assert set(requests) == seen
    plus, minus = manifest['states'][1:]
    return dict(root_index=manifest['root_index'], source_report_sha256=done['report_sha256'],
        states=result, runner_elapsed_seconds=done['finished']-manifest['started'],
        plus_minus_action_disagreements=sum(left != right for left, right in zip(choices[plus], choices[minus])),
        action_changes_from_OFF={state: sum(left != right for left, right in zip(choices['OFF'], choices[state]))
                                 for state in (plus, minus)},
        interpretation='Exact seen training contexts; not retention or generalization. Held counts are native-replayed descriptive comparison, not an independent sample. Tokens count emitted IDs including terminal EOS, not score forwards or launch caps.')


roots = [Path(path) for path in sys.argv[1:-1]]
analyses = [analyze(root) for root in roots]
assert len({entry['root_index'] for entry in analyses}) == len(analyses)
output = dict(status='RAW_GENERATION_COUNTS_AGREE_WITH_NATIVE_REDUCTION', roots=analyses,
    analysis_sha256=file_hash(Path(__file__)))
with Path(sys.argv[-1]).open('x') as stream:
    json.dump(output, stream, sort_keys=True, indent=2, allow_nan=False)
print(json.dumps(dict(status=output['status'], roots=[row['root_index'] for row in analyses])))
