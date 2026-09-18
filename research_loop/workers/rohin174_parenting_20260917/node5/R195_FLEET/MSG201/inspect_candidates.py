"""Read recent TRAIN responses for recommendations only; never retire a life."""

from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


ALLOWED = {'run1', 'pilot', 'C1', 'C3', 'C4', 'C5'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode()).hexdigest()


def meta(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        raw = handle.read()
    return json.loads(b'{' + raw[raw.rfind(b',"index":') + 1:])


def inspect(items):
    assert len(items) == 6 and {item['label'] for item in items} == ALLOWED
    rows = []
    for item in items:
        root = Path(item['storage_root'])
        assert 'C2' not in str(root) and 'repo_reader' not in str(root)
        process = Path('/proc') / str(item['native']['pid'])
        fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        assert fields[19] == item['native']['start_ticks'] and fields[0] not in ('Z', 'X')
        assert hashlib.sha256((process / 'cmdline').read_bytes()).hexdigest() == item['native']['argv_sha256']
        assert os.readlink(process / 'cwd') == item['source_root']
        paths = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))
        head = meta(paths[-1])
        responses = []
        complete = None
        for path in reversed(paths):
            metadata = meta(path)
            if metadata['kind'] not in ('RESPONSE', 'SLEEP_COMPLETE'):
                continue
            if metadata['kind'] == 'SLEEP_COMPLETE' and complete is not None:
                continue
            envelope = json.loads(path.read_bytes())
            assert envelope['sha256'] == digest({key: value for key, value in envelope.items() if key != 'sha256'})
            document = envelope['document']
            if metadata['kind'] == 'SLEEP_COMPLETE':
                checkpoint = document['checkpoint']
                complete = dict(index=metadata['index'], record_sha256=metadata['sha256'],
                    cycle=document['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
                    adapter_state_sha256=checkpoint['adapter_state_sha256'],
                    saved_state_sha256=document['resume_state']['sha256'], status=document['status'])
            else:
                raw = document['response']['raw']
                assert isinstance(raw, str)
                blocks = re.findall(r'```[^\n]*\n(.*?)```', raw, re.DOTALL)
                responses.append(dict(index=metadata['index'], record_sha256=metadata['sha256'],
                    record_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    source_path=str(path), finished_unix=document['finished_unix'],
                    raw=raw, raw_chars=len(raw), raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                    token_count=len(document['response'].get('token_ids', [])),
                    truncated=document['response'].get('truncated'),
                    fullwidth_code=any(any('\uff01' <= char <= '\uff5e' for char in block) for block in blocks)))
            if len(responses) == 30 and complete is not None:
                break
        responses.reverse()
        counts = Counter(row['raw_sha256'] for row in responses)
        top = []
        for raw_sha, count in counts.most_common(4):
            matching = [row for row in responses if row['raw_sha256'] == raw_sha]
            top.append(dict(count=count, raw_sha256=raw_sha, indices=[row['index'] for row in matching], raw=matching[0]['raw']))
        fields_after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
        assert fields_after[19] == fields[19] and fields_after[0] not in ('Z', 'X')
        rows.append(dict(label=item['label'], native=item['native'], root=str(root), head=head,
            latest_complete=complete, sample_count=len(responses), unique_exact_texts=len(counts),
            largest_exact_repeat=counts.most_common(1)[0][1],
            fullwidth_code_responses=sum(row['fullwidth_code'] for row in responses),
            truncated_responses=sum(bool(row['truncated']) for row in responses),
            post_latest_complete_response_indices=[row['index'] for row in responses if row['index'] > complete['index']],
            most_repeated=top, responses=responses, identity_unchanged=True))
    return dict(observed_unix=time.time(), rows=rows, recommendation_only=True,
                signals=0, retirements=0, gpu_calls=0, publications=0, remote_writes=0,
                protected_not_resampled=['C2', 'repo_reader'], rollout_paused=True)


def main():
    if '--remote' in sys.argv:
        print(json.dumps(inspect(json.load(sys.stdin))))
        return
    here = Path(__file__).resolve().parent
    inventory_path = here.parent / 'INVENTORY_20260918T021156Z.json'
    items = [row for row in json.loads(inventory_path.read_bytes())['rows'] if row['label'] in ALLOWED]
    script = Path(__file__).read_text()
    result = subprocess.run(['bash', str(here.parents[5] / 'gpu/ovx3_ssh.sh'),
        'python3 -B -c ' + shlex.quote(script) + ' --remote'], input=json.dumps(items),
        capture_output=True, text=True, timeout=100)
    if result.returncode:
        raise RuntimeError('read_only_candidate_observation_failed:' + result.stderr[-200:])
    report = json.loads(result.stdout)
    output = here / ('CANDIDATES_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    with output.open('x') as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write('\n')
    output.chmod(0o444)
    print(json.dumps(dict(receipt=str(output), rows=[{key: row[key] for key in (
        'label', 'sample_count', 'unique_exact_texts', 'largest_exact_repeat', 'fullwidth_code_responses',
        'truncated_responses', 'latest_complete')} for row in report['rows']])))


if __name__ == '__main__':
    main()
