"""Read-only outcome accounting for the existing node3 lives."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918')
ARMS = ('conversational', 'frozen_c2', 'fresh_math', 'peer_math', 'peer_repo', 'p4', 'p32', 'lr03', 'lr3')


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 8192))
        matches = re.findall(rb',"index":(\d+),"journal_id":"[^"]+","kind":"([^"]+)"', handle.read())
    if not matches or int(matches[-1][0]) != int(path.stem):
        raise ValueError('outer_record_metadata_required')
    return matches[-1][1].decode()


def read_record(path):
    record = json.loads(path.read_bytes())
    canonical = json.dumps({key: value for key, value in record.items() if key != 'sha256'},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != record['sha256']:
        raise ValueError('record_content_binding')
    return record


def audit(root=ROOT):
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), arms={})
    for name in ARMS:
        arm = root / name
        outcomes, peers = [], []
        kinds = Counter()
        for path in sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json')):
            kind = metadata(path)
            kinds[kind] += 1
            if kind not in ('R184_ACT', 'R205_PEER_THINK_INPUT'):
                continue
            record = read_record(path)
            document = record['document']
            bound = dict(index=record['index'], sha256=record['sha256'], path=str(path))
            if kind == 'R184_ACT':
                outcomes.append(dict(bound, segment=document['segment'], outcome=document['outcome']))
            else:
                peers.append(dict(bound, sender=document['sender'], receiver=document['receiver'],
                    source_record_sha256=document['source_record_sha256'],
                    actual_THINK_render_verified=document['actual_THINK_render_verified'],
                    imported_training_rows=document['imported_training_rows']))
        result['arms'][name] = dict(record_kinds=dict(kinds), act_receipts=outcomes,
            outcome_counts=dict(Counter(item['outcome']['status'] for item in outcomes)),
            successful_executions=sum(item['outcome'].get('executed') is True for item in outcomes),
            peer_receipts=peers, peer_rendered=sum(item['actual_THINK_render_verified'] for item in peers),
            environment='PINNED_SOURCE_EXCERPT_ONLY_NO_EXECUTOR' if name == 'peer_repo'
                else 'PROSE_REASONING_NO_EXECUTOR_CONNECTED',
            prose_assertions_are_scientific_receipts=False)
    return result


if __name__ == '__main__':
    result = audit()
    stamp = datetime.fromisoformat(result['observed_utc']).strftime('%Y%m%dT%H%M%SZ')
    with (ROOT / ('R209_OUTCOMES_' + stamp + '.json')).open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
    print(json.dumps(result))
