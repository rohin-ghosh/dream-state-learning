"""Publish the authorized game instruction without controlling the learner."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import time

from gpu.orch_r127_pilot_console import _inbox
from organism_v6.orch_r125_plain_context import has_scaffolding
from relay import load, write_once


POLICY = 'R229_GAME_CONTINUITY_INSTRUCTION_V1'
TEXT = ('Game instruction: the game is not changing. If no judgment has arrived, '
    'that is silence, not a verdict: keep guessing — write new captions every opportunity. '
    'This is an instruction, not a score or a claim about any earlier caption. '
    'Actual judgments will still report rank, acceptance and novelty separately.')


def publish(life, output):
    if has_scaffolding('Tool: ' + TEXT):
        raise ValueError('instruction_must_survive_renderer')
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'WRITER.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt_path = output / 'PUBLISHED.json'
        if receipt_path.exists():
            receipt, reference = load(receipt_path)
            inbox, source = load(Path(receipt['publication']['path']))
            if inbox['text'] != TEXT or source['sha256'] != receipt['publication']['sha256']:
                raise ValueError('existing_notice_binding_changed')
            return receipt
        notice = output / 'NOTICE.json'
        write_once(notice, dict(policy=POLICY, instruction=TEXT,
            authority='Rohin message 229 relayed by Fable, 2026-09-18 09:20 UTC',
            learner_signals=[], scoring_calls=0, training_changes=[]))
        source = dict(path=str(notice.resolve()), sha256=hashlib.sha256(notice.read_bytes()).hexdigest())
        existing = None
        for path in (life / 'stream/inbox').glob('*.json'):
            inbox, reference = load(path)
            if inbox.get('source_receipt') == source and inbox.get('text') == TEXT:
                existing = dict(id=inbox['id'], **reference)
                break
        publication = existing or _inbox(life, 'Tool', TEXT, source)
        receipt = dict(policy=POLICY, publication=publication, published_unix=time.time(),
            recovered_existing_inbox=existing is not None, learner_signals=[], scoring_calls=0,
            parent_status='unchanged', training_changes=[])
        write_once(receipt_path, receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--life', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(publish(arguments.life, arguments.output), sort_keys=True))


if __name__ == '__main__':
    main()
