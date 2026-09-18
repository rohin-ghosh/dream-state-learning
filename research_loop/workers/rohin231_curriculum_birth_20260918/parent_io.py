"""Bounded canonical journal reads and attributed publication to this birth only."""

import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')


def main():
    request = json.load(sys.stdin)
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu.orch_r125_stream_journal import _digest
    stream = ROOT / 'raw/stream'
    if not (stream / 'JOURNAL.json').exists():
        print(json.dumps(dict(ready=False)))
        return
    manifest = json.loads((stream / 'JOURNAL.json').read_bytes())
    if request['action'] == 'publish':
        from gpu.orch_r127_pilot_console import publish_parent
        assert manifest['journal_id'] == request['journal_id']
        delivery = request['delivery_id']
        assert len(delivery) == 64 and all(letter in '0123456789abcdef' for letter in delivery)
        receipt_path = ROOT / 'control' / ('PARENT_' + delivery + '.json')
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_bytes())
            assert receipt['text_sha256'] == hashlib.sha256(request['text'].encode()).hexdigest()
        else:
            marker = receipt_path.with_suffix('.dispatch')
            marker.mkdir()
            publication = publish_parent(ROOT / 'raw', 'Astra', request['text'])
            receipt = dict(publication=publication, journal_id=manifest['journal_id'],
                text_sha256=hashlib.sha256(request['text'].encode()).hexdigest(),
                delivered_unix=time.time(), provider_response_sha256=request['provider_response_sha256'])
            with receipt_path.open('x') as output:
                json.dump(receipt, output, sort_keys=True)
        print(json.dumps(receipt))
        return
    assert request['action'] == 'poll'
    start = request.get('next_index', 0)
    previous = _digest(manifest) if start == 0 else request['previous_sha256']
    records = []
    for index in range(start, start + 160):
        path = stream / 'records' / f'{index:020d}.json'
        if not path.exists():
            break
        record = json.loads(path.read_bytes())
        assert record['index'] == index and record['journal_id'] == manifest['journal_id']
        assert record['previous_sha256'] == previous
        assert record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'})
        previous = record['sha256']
        kind, document = record['kind'], record['document']
        kept = dict(index=index, kind=kind, sha256=previous)
        if kind in ('REQUEST', 'RESPONSE', 'R184_STAGE', 'INBOX', 'LOADED', 'TERMINAL', 'R184_ACT'):
            kept['document'] = document
        elif kind == 'COMMITTED':
            kept['document'] = dict(kind=document.get('kind'), committed=True)
        elif kind == 'SLEEP_COMPLETE':
            kept['document'] = dict(total_optimizer_steps=document.get('total_optimizer_steps'))
        records.append(kept)
    print(json.dumps(dict(ready=True, journal_id=manifest['journal_id'], records=records,
        next_index=start + len(records), previous_sha256=previous, observed_unix=time.time())))


if __name__ == '__main__':
    main()
