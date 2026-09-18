"""Source-bound development examples, never a child attempt or a fresh score."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import time

from gpu.orch_r127_pilot_console import _inbox
from organism_v6.orch_r125_plain_context import has_scaffolding
from relay import digest, journal_paths, load, write_once


def publish(life, output, packet_path, context_path):
    packet, packet_reference = load(packet_path)
    text = context_path.read_text()
    context_hash = hashlib.sha256(text.encode()).hexdigest()
    if context_hash != packet['child_context']['sha256']:
        raise ValueError('exact_seed_context_required')
    if packet['usage']['count_as_new_attempts'] or packet['usage']['count_as_new_exploration']:
        raise ValueError('seeds_are_not_own_discoveries')
    if has_scaffolding('Tool: ' + text):
        raise ValueError('seed_context_must_render')
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'WRITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        projection = output / 'PROJECTION.json'
        document = dict(schema='R230_SEED_CONTEXT_PUBLICATION_V1',
            authority='Rohin message 230 relayed by Fable, 2026-09-18 09:40 UTC',
            text=text, packet=packet_reference, context_sha256=context_hash,
            treatment_id=packet['treatment_id'], usage=packet['usage'],
            learner_signals=[], scoring_calls=0, training_changes=[])
        write_once(projection, document)
        _, source = load(projection)
        receipt_path = output / 'PUBLISHED.json'
        if receipt_path.exists():
            receipt, _ = load(receipt_path)
            inbox, reference = load(Path(receipt['publication']['path']))
            if inbox['source_receipt'] != source or inbox['text'] != text or reference['sha256'] != receipt['publication']['sha256']:
                raise ValueError('existing_seed_publication_changed')
            return receipt
        publication = None
        for path in (life / 'stream/inbox').glob('*.json'):
            inbox, reference = load(path)
            if inbox.get('source_receipt') == source and inbox.get('text') == text:
                publication = dict(id=inbox['id'], **reference)
                break
        frontier = max((int(path.stem) for path in journal_paths(life)), default=0)
        publication = publication or _inbox(life, 'Tool', text, source)
        receipt = dict(schema=document['schema'], treatment_id=packet['treatment_id'],
            packet_sha256=packet_reference['sha256'], context_sha256=context_hash,
            publication=publication, journal_start_after=frontier, published_unix=time.time(),
            scoring_calls=0, learner_signals=[], training_changes=[],
            first_request='pending', own_discovery_count=0)
        write_once(receipt_path, receipt)
        return receipt


def audit(life, output):
    receipt, _ = load(output / 'PUBLISHED.json')
    inbox, reference = load(Path(receipt['publication']['path']))
    if inbox['actor'] != 'environment' or inbox['speaker'] != 'Tool' or reference['sha256'] != receipt['publication']['sha256']:
        raise ValueError('authenticated_Tool_context_required')
    first = None
    latest = None
    for path in journal_paths(life):
        if int(path.stem) <= receipt['journal_start_after']:
            continue
        record, _ = load(path)
        if record['sha256'] != digest({key: value for key, value in record.items() if key != 'sha256'}):
            raise ValueError('journal_hash_mismatch')
        if record['kind'] != 'REQUEST':
            continue
        latest = record['index']
        if any(message.get('role') == 'user' and inbox['text'] in message.get('content', '')
               for message in record['document'].get('messages', [])):
            first = dict(index=record['index'], sha256=record['sha256'],
                started_unix=record['document'].get('started_unix'))
            break
    return dict(schema='R230_SEED_CONTEXT_RENDER_V1', observed_unix=time.time(),
        treatment_id=receipt['treatment_id'], inbox_id=inbox['id'],
        inbox_sha256=reference['sha256'], context_sha256=receipt['context_sha256'],
        packet_sha256=receipt['packet_sha256'], first_rendered_request=first,
        latest_request=latest, published_unix=receipt['published_unix'],
        learner_signals=[], scoring_calls=0, training_changes=[], own_discovery_count=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('publish', 'audit'))
    parser.add_argument('--life', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--packet', type=Path)
    parser.add_argument('--context', type=Path)
    arguments = parser.parse_args()
    if arguments.action == 'publish':
        if arguments.packet is None or arguments.context is None:
            parser.error('publish requires --packet and --context')
        result = publish(arguments.life, arguments.output, arguments.packet, arguments.context)
    else:
        result = audit(arguments.life, arguments.output)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
