"""Read-only, transcript-free verification of rendered Tool publications."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from relay import digest, journal_paths, load


def audit(life, relay_output):
    publications = [load(path)[0] for path in (relay_output / 'published').glob('*.json')]
    publications.sort(key=lambda document: document['published_unix'])
    starts = [load(path)[0] for path in relay_output.glob('STARTED_*.json')]
    start_after = min((entry['journal_start_after'] for entry in starts), default=0)
    pending = []
    for entry in publications:
        inbox, reference = load(Path(entry['publication']['path']))
        if reference['sha256'] != entry['publication']['sha256']:
            raise ValueError('published_inbox_changed')
        if inbox['actor'] != 'environment' or inbox['speaker'] != 'Tool':
            raise ValueError('tool_attribution_required')
        projection, source = load(Path(inbox['source_receipt']['path']))
        if source != inbox['source_receipt'] or projection['text'] != inbox['text']:
            raise ValueError('projection_binding_changed')
        text = inbox['text']
        pending.append((text, dict(inbox_id=inbox['id'], inbox_sha256=reference['sha256'],
            projection_sha256=source['sha256'], result_sha256=entry['result']['sha256'],
            origin=entry['origin'], chunk=entry['chunk'], published_unix=entry['published_unix'],
            text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            ranked_caption_count=text.count('\nRank '),
            no_judgment_count=text.count('No judgment:'), first_rendered_request=None)))
    latest_request = None
    for path in journal_paths(life):
        if int(path.stem) <= start_after:
            continue
        record, reference = load(path)
        if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
            raise ValueError('journal_record_hash_mismatch')
        if record['kind'] != 'REQUEST':
            continue
        document = record['document']
        request = dict(index=record['index'], record_sha256=record['sha256'],
            file_sha256=reference['sha256'], started_unix=document.get('started_unix'))
        latest_request = request
        texts = [message.get('content', '') for message in document.get('messages', [])
            if message.get('role') == 'user']
        for text, row in pending:
            if row['first_rendered_request'] is None and any(
                    isinstance(content, str) and text in content for content in texts):
                row['first_rendered_request'] = request
    rows = [row for text, row in pending]
    return dict(schema='R228_FEEDBACK_RENDER_AUDIT_V1',
        observed_utc=datetime.now(timezone.utc).isoformat(),
        publication_count=len(rows), rendered_count=sum(row['first_rendered_request'] is not None for row in rows),
        ranked_caption_count=sum(row['ranked_caption_count'] for row in rows),
        no_judgment_count=sum(row['no_judgment_count'] for row in rows),
        latest_request=latest_request, rows=rows, learner_signals=[], scoring_calls=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--life', required=True, type=Path)
    parser.add_argument('--relay-output', required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(audit(arguments.life, arguments.relay_output), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
