"""Segment-specific CPU receiver; shares only the existing atomic intake lock."""

import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

from gpu import orch_combined_l1_continual_run as run
from gpu import orch_combined_l1_continual_sampled as sampled
from gpu import orch_combined_l1_exhaustion_feed as feed
from gpu.orch_combined_l1_continual_receive import receive
from gpu.orch_combined_l1_native_feed_node import inventory


def existing(root, batch_id, expected):
    assert re.fullmatch(feed.BATCH_PATTERN, batch_id)
    for area in ('CONTENT_QUEUE', 'SAMPLED_EXTRA_PENDING'):
        folder = root / area / batch_id
        if folder.exists():
            receipt = run.read(folder / 'CPU_BOUND.json')
            encoder = run.read(folder / 'NATIVE_ENCODER.json')
            assert receipt['status'] == encoder['status'] == 'PASS'
            assert receipt['manifest_sha256'] == expected == run.sha(folder / 'MANIFEST.json')
            assert receipt['packet_sha256'] == encoder['packet_sha256'] == run.sha(folder / 'BOUND_PACKET.json')
            assert receipt['rows_sha256'] == run.sha(folder / 'ROWS.json')
            assert receipt['exclusions_sha256'] == run.sha(folder / 'EXCLUSIONS.json')
            return folder, receipt
    return None, None


def process(root, envelope, expected):
    ready = run.read(root / 'EXHAUSTION_SEGMENT1_READY.json')
    assert ready['status'] == 'PASS' and ready['publication_logged'] is True
    assert ready['node_source_sha256'] == run.sha(__file__)
    assert ready['feed_source_sha256'] == run.sha(feed.__file__)
    assert ready['publisher_registry_sha256'] == feed.REGISTRY_SHA
    for relative, expected_source in ready['runtime_hashes'].items():
        assert run.sha(Path(__file__).resolve().parents[1] / relative) == expected_source
    deadline = run.read(root / 'LIFETIME.json')['training_deadline_unix']
    assert time.time() < deadline, 'training_ingestion_deadline'
    packet = envelope['packet']
    assert feed.common.digest(envelope['exclusions']) == ready['exclusions_digest'], 'frozen_exclusions_drift'
    assert re.fullmatch(feed.BATCH_PATTERN, packet['batch_id'])
    assert packet['provenance']['manifest_sha256'] == expected
    assert hashlib.sha256(base64.b64decode(envelope['manifest_bytes'])).hexdigest() == expected
    assert json.loads(base64.b64decode(envelope['manifest_bytes'])) == packet['provenance']['original_manifest']
    assert hashlib.sha256(base64.b64decode(envelope['rows_bytes'])).hexdigest() == packet['provenance']['rows_file_sha256']
    assert packet['provenance']['publisher_registry_sha256'] == feed.REGISTRY_SHA
    feed.registries(packet['proof']['exhaustion_segment1'])
    with (root / 'FEED_AUTO_INGEST.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        folder, receipt = existing(root, packet['batch_id'], expected)
        if folder is None:
            receive(root, envelope, native_validator=feed.native_check)
            folder, receipt = existing(root, packet['batch_id'], expected)
        assert folder is not None
        sampled.validate_packet(run.read(folder / 'BOUND_PACKET.json'), run.read(folder / 'EXCLUSIONS.json'))
        assert time.time() < deadline, 'training_ingestion_deadline'
        destination = root / 'CONTENT_QUEUE' / packet['batch_id']
        already_queued = folder == destination
        if not already_queued:
            assert not destination.exists()
            os.rename(folder, destination)
            run.policy.sync_directory(destination.parent)
        value = dict(batch_id=packet['batch_id'], manifest_sha256=expected,
            packet_sha256=receipt['packet_sha256'], accepted=receipt['accepted'], added=receipt['added'],
            publisher_registry_sha256=feed.REGISTRY_SHA, queued=True, already_queued=already_queued,
            actual_ingested=False, actual_presented=False, native_calls=0, reset=False,
            finished_unix=time.time(), deadline=deadline)
        run.write(root / 'EXHAUSTION_SEGMENT1_RECEIPTS' / (expected + '.json'), value)
        return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--manifest-sha')
    args = parser.parse_args()
    print(json.dumps(inventory(args.root) if args.inventory else process(args.root, json.load(sys.stdin), args.manifest_sha)))
