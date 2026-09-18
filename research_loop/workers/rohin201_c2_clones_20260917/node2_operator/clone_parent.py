"""Reference-bound sparse parent with receipt-based withdrawal and no queue."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def write(path, document):
    with path.open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def due(completed, published):
    return completed in (52, 53) and completed not in published


def main():
    config = read(ROOT / 'PARENT_CONFIG.json')
    reference = Path(config['reference_path']).read_bytes()
    if hashlib.sha256(reference).hexdigest() != config['reference_sha256']:
        raise ValueError('exact_full_clean_parent_reference')
    if len(reference) != 17358:
        raise ValueError('complete_clean_reference_not_an_excerpt')
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu.orch_r127_pilot_console import publish_parent
    receipts = ROOT / 'parent_receipts'
    receipts.mkdir(mode=0o700, exist_ok=True)
    write(receipts / 'REFERENCE_BOUND_STARTED.json', dict(pid=os.getpid(), observed_unix=time.time(),
        reference_path=config['reference_path'], reference_sha256=config['reference_sha256'],
        reference_bytes=len(reference), reference_read_in_full=True, reference_bulk_pasted_to_child=False,
        parent_style='Operator-authored sparse questions informed by clean human/C2 reference; no adaptive-model claim',
        no_creative_test_or_future_original_C2_relay=True, guided_cycles=[52, 53, 54],
        withdrawn_cycles=[55, 56, 57], no_async_publication_queue=True))
    published = {cycle for cycle in (52, 53) if (receipts / f'GUIDANCE_AFTER_{cycle}.json').exists()}
    seen = set()
    plan = read(ROOT / 'control/PLAN.json')
    first = read(ROOT / 'FIRST_INPUTS.json')
    while time.time() < min(plan['hard_end_unix'], first['published_unix'] + 7200):
        if (ROOT / 'control/EXIT.json').exists():
            break
        for path in sorted((ROOT / 'raw/stream/records').glob('*.json'))[-60:]:
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
            if completed >= 54:
                write(receipts / 'WITHDRAWN_REFERENCE_BOUND.json', dict(observed_unix=time.time(),
                    after_complete_cycle=completed, pending_automatic_guidance=0,
                    published_followups=sorted(published), no_future_parent_publications=True))
                return
            if due(completed, published):
                publication = publish_parent(ROOT / 'raw', 'Astra', config['followups'][str(completed)])
                publication.update(after_complete_cycle=completed, intended_cycle=completed + 1,
                    published_unix=time.time(), source_record_sha256=record['sha256'],
                    parent_reference_sha256=config['reference_sha256'])
                write(receipts / f'GUIDANCE_AFTER_{completed}.json', publication)
                published.add(completed)
        time.sleep(0.2)
    write(receipts / 'REFERENCE_BOUND_EXIT.json', dict(observed_unix=time.time(),
        pending_automatic_guidance=0, published_followups=sorted(published)))


if __name__ == '__main__':
    main()
