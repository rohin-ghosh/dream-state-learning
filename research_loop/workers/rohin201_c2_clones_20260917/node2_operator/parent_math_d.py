"""Sparse Astra guidance for three clone cycles, then no queued guidance."""

import json
from pathlib import Path
import sys
import time

from receive_math_d import ROOT, SOURCE, read, write, require


FOLLOWUPS = {
    52: 'Which observation from your last attempt deserves more thinking, and which claim still needs checking? Choose your next mathematical action from that evidence; do not treat my agreement or your confidence as a result.',
    53: 'What correction has actually changed your next attempt? Try one small check of your own reasoning, then decide what is worth retaining. After this cycle I will withdraw further guidance for the next three cycles; carry the practice yourself.',
}


def due_messages(completed, published):
    return [completed] if completed in FOLLOWUPS and completed not in published else []


def main():
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r127_pilot_console import publish_parent
    plan = read(ROOT / 'control/PLAN.json')
    initial = read(ROOT / 'FIRST_INPUTS.json')
    receipts = ROOT / 'parent_receipts'
    receipts.mkdir(mode=0o700)
    write(receipts / 'STARTED.json', dict(started_unix=time.time(), pid=__import__('os').getpid(),
        source_context_record=5846, guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57],
        no_future_Rohin_relay=True, no_async_publication_queue=True,
        parent_style='Sparse static Astra-D questions; not a claimed adaptive external model',
        first_inputs=initial))
    published = {}
    seen = set()
    while time.time() < min(plan['hard_end_unix'], initial['published_unix'] + 7200):
        if (ROOT / 'control/EXIT.json').exists():
            break
        paths = sorted((ROOT / 'raw/stream/records').glob('*.json'))
        for path in paths[-36:]:
            if path.name.endswith('.intent.json') or path.name in seen:
                continue
            seen.add(path.name)
            with path.open('rb') as handle:
                handle.seek(max(0, path.stat().st_size - 4096))
                tail = handle.read()
            if b'"kind":"R184_LEARN_COMPLETE"' not in tail:
                continue
            record = read(path)
            completed = record['document']['cycle']
            for cycle in due_messages(completed, published):
                publication = publish_parent(ROOT / 'raw', 'Astra', FOLLOWUPS[cycle])
                publication.update(after_complete_cycle=cycle, intended_cycle=cycle + 1,
                    published_unix=time.time(), source_record_sha256=record['sha256'])
                write(receipts / f'GUIDANCE_AFTER_{cycle}.json', publication)
                published[cycle] = publication
            if completed >= 54:
                write(receipts / 'WITHDRAWN.json', dict(observed_unix=time.time(), after_complete_cycle=completed,
                    no_future_parent_publications=True, pending_automatic_guidance=0,
                    published_followups=published, source_record_sha256=record['sha256']))
                return
        time.sleep(0.2)
    write(receipts / 'EXIT.json', dict(observed_unix=time.time(), published_followups=published,
        pending_automatic_guidance=0, reason='Clone exited or bounded parent wall'))


if __name__ == '__main__':
    main()
