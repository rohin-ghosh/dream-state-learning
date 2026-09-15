"""Native-only idempotent publication after unchanged source and encoder checks."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_continual_sampled as sampled
from gpu.orch_combined_l1_continual_receive import receive


def admitted_manifest(root, batch_id, manifest_sha):
    assert isinstance(batch_id, str) and re.fullmatch(r'orch_continual_batch_segment2_native_\d{3}', batch_id)
    for area in ('CONTENT_QUEUE', 'SAMPLED_EXTRA_PENDING'):
        folder = root / area / batch_id
        if folder.exists():
            receipt = run.read(folder / 'CPU_BOUND.json')
            encoder = run.read(folder / 'NATIVE_ENCODER.json')
            assert receipt['status'] == encoder['status'] == 'PASS'
            assert receipt['manifest_sha256'] == manifest_sha == run.sha(folder / 'MANIFEST.json')
            assert receipt['packet_sha256'] == encoder['packet_sha256'] == run.sha(folder / 'BOUND_PACKET.json')
            assert receipt['rows_sha256'] == run.sha(folder / 'ROWS.json')
            assert receipt['exclusions_sha256'] == run.sha(folder / 'EXCLUSIONS.json')
            return folder, receipt
    return None, None


def inventory(root):
    entries = []
    for area in ('CONTENT_QUEUE', 'SAMPLED_EXTRA_PENDING'):
        for folder in sorted((root / area).glob('*')):
            if (folder / 'CPU_BOUND.json').exists():
                value = run.read(folder / 'CPU_BOUND.json')
                entries.append(dict(batch_id=folder.name, area=area,
                    manifest_sha256=value['manifest_sha256'], status=value['status']))
    return dict(training_deadline=run.read(root / 'LIFETIME.json')['training_deadline_unix'],
        native_unix=time.time(), entries=entries)


def process(root, envelope, expected_sha):
    ready = run.read(root / 'FEED_AUTO_READY.json')
    assert ready['status'] == 'PASS' and ready['node_source_sha256'] == run.sha(__file__)
    assert ready['publication_logged'] is True
    deadline = run.read(root / 'LIFETIME.json')['training_deadline_unix']
    assert time.time() < deadline, 'training_ingestion_deadline'
    packet = envelope['packet']
    assert packet['provenance']['manifest_sha256'] == expected_sha
    batch_id = packet['batch_id']
    with (root / 'FEED_AUTO_INGEST.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        folder, receipt = admitted_manifest(root, batch_id, expected_sha)
        if folder is None:
            receive(root, envelope)
            folder, receipt = admitted_manifest(root, batch_id, expected_sha)
        assert folder is not None
        sampled.validate_packet(run.read(folder / 'BOUND_PACKET.json'), run.read(folder / 'EXCLUSIONS.json'))
        assert time.time() < deadline, 'training_ingestion_deadline'
        destination = root / 'CONTENT_QUEUE' / batch_id
        already_queued = folder == destination
        if not already_queued:
            assert not destination.exists()
            os.rename(folder, destination)
        value = dict(batch_id=batch_id, manifest_sha256=expected_sha,
            packet_sha256=receipt['packet_sha256'], accepted=receipt['accepted'],
            added=receipt['added'], queued=True, already_queued=already_queued,
            actual_ingested=False, actual_presented=False, native_calls=0, reset=False,
            finished_unix=time.time(), deadline=deadline)
        run.write(root / 'FEED_AUTO_RECEIPTS' / (expected_sha + '.json'), value)
        return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--manifest-sha')
    args = parser.parse_args()
    value = inventory(args.root) if args.inventory else process(args.root, json.load(sys.stdin), args.manifest_sha)
    print(json.dumps(value, indent=2))
