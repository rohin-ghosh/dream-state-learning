"""Bounded read-only evidence of future results, Tool delivery and rendering."""

import hashlib
import json
from pathlib import Path
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load(path):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 33554432
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def main():
    root = Path('/localhome/local-rohing/orch_r233_p3_scorer_recovery_20260918/attempt4')
    config, _ = load(root / 'FEEDBACK_CONFIG.private.json')
    life, ledger = Path(config['life']), Path(config['ledger'])
    rows, pending = [], []
    for path in sorted((root / 'feedback').glob('DELIVERED_*.json')):
        delivery, _ = load(path)
        matches = []
        for publication_path in (ledger / 'published').glob('*.json'):
            publication, _ = load(publication_path)
            if publication['publication']['id'] == delivery['inbox_id']:
                matches.append(publication)
        assert len(matches) == 1
        publication = matches[0]
        inbox, inbox_sha = load(Path(publication['publication']['path']))
        assert inbox_sha == publication['publication']['sha256'] and inbox['actor'] == 'environment' and inbox['speaker'] == 'Tool'
        result, result_sha = load(Path(publication['result']['path']))
        assert result_sha == delivery['result_sha256'] == publication['result']['sha256']
        projection, projection_sha = load(Path(inbox['source_receipt']['path']))
        assert projection_sha == inbox['source_receipt']['sha256'] and projection['text'] == inbox['text']
        feedback = result['report'].get('feedback', [])
        scored = [item for item in feedback if item.get('result', {}).get('ok') and type(item['result'].get('rank')) is int]
        row = dict(delivery, inbox_sha256=inbox_sha, projection_sha256=projection_sha,
            result_unix=result['unix'], error=result['report'].get('error'), scored_entries=len(scored),
            accepted_entries=sum(item['result'].get('accepted') is True for item in scored),
            new_pixels=sum(item['result'].get('status') == 'new_pixel' for item in scored),
            raw_payload_included=False, first_rendered_request=None)
        rows.append(row)
        pending.append((inbox['text'], row))
    head = max(int(path.stem) for path in (life / 'stream/records').glob('*.json') if path.stem.isdigit())
    start = min((row['origin']['record_index'] for row in rows), default=head)
    assert head-start <= 512, 'bounded_recovery_window_not_full_history'
    for index in range(start, head+1):
        record, checksum = load(life / 'stream/records' / f'{index:020d}.json')
        assert record['sha256'] == digest({key:value for key,value in record.items() if key != 'sha256'})
        if record['kind'] != 'REQUEST':
            continue
        messages = [message.get('content', '') for message in record['document'].get('messages', []) if message.get('role') == 'user']
        for text, row in pending:
            if row['first_rendered_request'] is None and any(isinstance(content, str) and text in content for content in messages):
                row['first_rendered_request'] = dict(index=index,record_sha256=record['sha256'],file_sha256=checksum,
                    started_unix=record['document'].get('started_unix'))
                row['rendering'] = 'VERIFIED_ACTUAL_REQUEST'
    print(json.dumps(dict(unix=time.time(),rows=rows,head=head,scoring_calls=0,learner_signals=[])))


if __name__ == '__main__':
    main()
