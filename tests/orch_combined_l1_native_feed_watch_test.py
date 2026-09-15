"""Bounded publisher discovery and exactly-once handoff preserve admission."""

import json
import time

import pytest

from gpu.orch_combined_l1_native_feed import allowed_number, discover
from gpu.orch_combined_l1_native_feed_watch import pending
from gpu.orch_combined_l1_native_feed_node import admitted_manifest


@pytest.mark.parametrize('number,allowed', [(27, True), (40, True), (41, True),
    (999, True), (1000, False), (26, False), (True, False), ('41', False), (-1, False)])
def test_native_publisher_sequence_stays_bounded(number, allowed):
    assert allowed_number(number) is allowed


def test_discovery_only_finds_complete_accepted_future_manifests(tmp_path):
    for number, accepted in ((40, True), (41, True), (42, False), (43, 'true')):
        folder = tmp_path / f'orch_continual_batch_snapshot_{number:03d}'
        folder.mkdir()
        (folder / 'MANIFEST.json').write_text(json.dumps(dict(batch_author_accepted=accepted,
            batch_id=f'batch{number}', row_count=64)))
    malformed = tmp_path / 'orch_continual_batch_snapshot_044'
    malformed.mkdir()
    (malformed / 'MANIFEST.json').write_text('{')
    found = discover(tmp_path)
    assert [entry['number'] for entry in found] == [41]
    assert len(found[0]['manifest_sha256']) == 64


def test_poll_does_not_repeat_queued_or_failed_manifest_but_recovers_pending():
    discovered = [dict(number=number, batch_id=f'batch{number}', manifest_sha256=str(number))
        for number in range(41, 49)]
    inventory = dict(entries=[dict(batch_id='batch41', manifest_sha256='41', area='CONTENT_QUEUE'),
        dict(batch_id='batch43', manifest_sha256='43', area='SAMPLED_EXTRA_PENDING')])
    assert [entry['number'] for entry in pending(discovered, inventory, {'42'})] == [43, 44, 45, 46]


def test_known_manifest_rebinding_is_fatal_not_a_new_batch():
    with pytest.raises(ValueError, match='rebound'):
        pending([dict(number=41, batch_id='same', manifest_sha256='new')],
            dict(entries=[dict(batch_id='same', manifest_sha256='old', area='CONTENT_QUEUE')]), set())


@pytest.mark.parametrize('batch_id', ['..', '.', '../escape', '/tmp', 'foreign_batch', 'orch_continual_batch_segment2_native_1000'])
def test_node_handoff_rejects_paths_and_foreign_batch_names(tmp_path, batch_id):
    with pytest.raises(AssertionError):
        admitted_manifest(tmp_path, batch_id, 'hash')


def test_existing_incomplete_receipt_cannot_be_treated_as_admitted(tmp_path):
    folder = tmp_path / 'CONTENT_QUEUE/orch_continual_batch_segment2_native_041'
    folder.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        admitted_manifest(tmp_path, folder.name, 'hash')


def test_ready_packet_moves_once_and_does_not_reencode_or_reset(tmp_path, monkeypatch):
    from gpu import orch_combined_l1_native_feed_node as node
    folder = tmp_path / 'SAMPLED_EXTRA_PENDING/orch_continual_batch_segment2_native_041'
    folder.mkdir(parents=True)
    (tmp_path / 'CONTENT_QUEUE').mkdir()
    for name in ('MANIFEST.json', 'ROWS.json', 'EXCLUSIONS.json', 'BOUND_PACKET.json'):
        (folder / name).write_text('{}')
    expected = node.run.sha(folder / 'MANIFEST.json')
    receipt = dict(status='PASS', manifest_sha256=expected,
        rows_sha256=node.run.sha(folder / 'ROWS.json'),
        exclusions_sha256=node.run.sha(folder / 'EXCLUSIONS.json'),
        packet_sha256=node.run.sha(folder / 'BOUND_PACKET.json'), accepted=64, added=64)
    node.run.write(folder / 'CPU_BOUND.json', receipt)
    node.run.write(folder / 'NATIVE_ENCODER.json', receipt)
    node.run.write(tmp_path / 'LIFETIME.json', dict(training_deadline_unix=time.time() + 60))
    node.run.write(tmp_path / 'FEED_AUTO_READY.json', dict(status='PASS', publication_logged=True,
        node_source_sha256=node.run.sha(node.__file__)))
    def unexpected(*args):
        pytest.fail('already validated packet must not be reencoded')
    monkeypatch.setattr(node, 'receive', unexpected)
    monkeypatch.setattr(node.sampled, 'validate_packet', lambda *args: None)
    envelope = dict(packet=dict(batch_id=folder.name, provenance=dict(manifest_sha256=expected)))
    first = node.process(tmp_path, envelope, expected)
    second = node.process(tmp_path, envelope, expected)
    assert not first['already_queued'] and second['already_queued']
    assert first['reset'] is second['reset'] is False
    assert len(list((tmp_path / 'CONTENT_QUEUE').iterdir())) == 1
    node.run.write(tmp_path / 'LIFETIME.json', dict(training_deadline_unix=0))
    with pytest.raises(AssertionError, match='training_ingestion_deadline'):
        node.process(tmp_path, envelope, expected)


def test_presentation_monitor_uses_actual_indexes_not_ingested_flag():
    from gpu.orch_combined_l1_feed_progress import new_positions, next_exposure
    assert new_positions(dict(rows=[0, 128, 3481, 3857])) == []
    assert new_positions(dict(rows=[0, 128, 3482, 3856])) == [3482, 3856]
    assert next_exposure(2020, 3635) == 3460
    assert next_exposure(2276, 3635) == 3460
    assert next_exposure(2276, 3635 + 64) != 3460
