import json
from pathlib import Path

import pytest

from gpu import orch_rich_hot_node2_export as export


def source(tmp_path):
    root = tmp_path / 'native'
    (root / 'shard0').mkdir(parents=True)
    (root / 'reservations').mkdir()
    (root / 'PREPARE.json').write_text('{}')
    return root


def call(root, index=0, error=False):
    row = dict(index=index, shard=0, task_id=str(index), stage='final', condition='ORIGINAL_RICH',
               messages=[dict(role='user', content='question')], finished_unix=1, trainingAllowed=False)
    if error:
        row['error'] = dict(message='context_overflow')
    else:
        row['response'] = dict(raw='own target', messages=row['messages'])
        row['outcome'] = dict(category='registered_correct', content_tokens=501, admitted=False)
    path = root / 'shard0' / f'{index}_final.json'
    path.write_text(json.dumps(row))
    return path


def test_exact_raw_no_qualification_dedup_and_inflight(tmp_path):
    root = source(tmp_path)
    path = call(root)
    (root / 'reservations' / 'pending.json').write_text('{}')
    destination = tmp_path / 'supply'
    status = export.export(root, destination)
    manifest = export.read(Path(status['created_manifests'][0]))
    entry = manifest['rows'][0]
    assert (Path(status['created_manifests'][0]).parent / entry['file']).read_bytes() == path.read_bytes()
    assert manifest['trainingAllowed'] is False and entry['admitted'] is False
    assert status['completed_captures'] == status['raw_above_400'] == 1
    assert export.export(root, destination)['newly_published'] == 0


def test_changed_source_and_export_rejected(tmp_path):
    root = source(tmp_path)
    path = call(root)
    destination = tmp_path / 'supply'
    status = export.export(root, destination)
    original = path.read_bytes()
    path.write_bytes(original + b' ')
    with pytest.raises(ValueError, match='previous_capture_changed'):
        export.export(root, destination)
    path.write_bytes(original)
    manifest = Path(status['created_manifests'][0])
    entry = export.read(manifest)['rows'][0]
    (manifest.parent / entry['file']).write_bytes(b'corruption')
    with pytest.raises(ValueError, match='published_raw_changed'):
        export.export(root, destination)


def test_errors_preserved_bounded_batches_pending_dirs_ignored(tmp_path):
    root = source(tmp_path)
    call(root, error=True)
    call(root, 1)
    destination = tmp_path / 'supply'
    (destination / 'pending-crashed').mkdir(parents=True)
    status = export.export(root, destination, batch_size=1)
    assert len(status['created_manifests']) == 2
    assert status['categories'] == dict(execution_error=1, registered_correct=1)
    assert len(export.published(destination)) == 2


def test_incomplete_and_promoted_rows_fail_closed(tmp_path):
    root = source(tmp_path)
    path = call(root)
    row = export.read(path)
    row['trainingAllowed'] = True
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match='admitted'):
        export.export(root, tmp_path / 'supply')
    path.write_text('{}')
    with pytest.raises(ValueError, match='incomplete'):
        export.export(root, tmp_path / 'supply')


def test_separate_sidecar_required(tmp_path):
    root = source(tmp_path)
    with pytest.raises(ValueError, match='separate'):
        export.export(root, root / 'export')


def test_later_environment_receipts_are_separate_immutable_evidence(tmp_path):
    root = source(tmp_path)
    call(root)
    destination = tmp_path / 'supply'
    export.export(root, destination)
    assert export.export_evidence(root, destination) == []
    evidence = root / 'shard0' / 'evidence'
    evidence.mkdir()
    path = evidence / 'task.json'
    path.write_text('{"correct": false}')
    created = export.export_evidence(root, destination)
    assert len(created) == 1
    assert export.read(Path(created[0]))['trainingAllowed'] is False
    assert export.export_evidence(root, destination) == []
    path.write_text('{"correct": true}')
    with pytest.raises(ValueError, match='native_evidence_changed'):
        export.export_evidence(root, destination)


def test_provenance_drift_fails_closed(tmp_path):
    root = source(tmp_path)
    call(root)
    destination = tmp_path / 'supply'
    export.export(root, destination)
    (root / 'PREPARE.json').write_text('{"changed": true}')
    with pytest.raises(ValueError, match='frozen_provenance_changed'):
        export.export(root, destination)
