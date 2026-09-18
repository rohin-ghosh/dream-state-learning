import json
from pathlib import Path

import pytest

import native_custody as custody


def test_symlink_components_and_files_refuse(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    (real / 'value.json').write_text('{}')
    (tmp_path / 'alias').symlink_to(real, target_is_directory=True)
    (tmp_path / 'value.json').symlink_to(real / 'value.json')
    for path in (tmp_path / 'alias/value.json', tmp_path / 'value.json'):
        with pytest.raises(OSError):
            custody.Reader().raw(path)


def test_per_file_cap_before_read(tmp_path):
    path = tmp_path / 'value.json'
    with path.open('wb') as stream:
        stream.truncate(1024 * 1024 + 1)
    with pytest.raises(ValueError, match='per_file_cap'):
        custody.Reader().raw(path)


def test_total_TRAIN_and_record_caps(tmp_path):
    path = tmp_path / 'value.json'
    path.write_text('{}')
    reader = custody.Reader()
    reader.journal_bytes = 64 * 1024 * 1024
    with pytest.raises(ValueError, match='TRAIN_read_cap'):
        reader.raw(path, record=True)
    reader.journal_bytes = 0
    reader.record_count = 256
    with pytest.raises(ValueError, match='TRAIN_read_cap'):
        reader.raw(path, record=True)


def test_record_and_intent_binding(tmp_path):
    manifest = dict(schema='R125_STREAM_JOURNAL_V1', journal_id='a' * 32)
    directory = tmp_path / 'stream/records'
    directory.mkdir(parents=True)
    document = dict(**manifest, index=0, previous_sha256=custody.digest(manifest),
        kind='COMMITTED', document=dict(kind='BIRTH'))
    document['sha256'] = custody.digest(document)
    intent = dict(**manifest, index=0, previous_sha256=document['previous_sha256'],
        record_sha256=document['sha256'])
    record_path = directory / ('0' * 20 + '.json')
    intent_path = directory / ('0' * 20 + '.intent.json')
    record_path.write_text(json.dumps(document))
    intent_path.write_text(json.dumps(intent))
    actual, reference = custody.record(custody.Reader(), tmp_path, 0, manifest)
    assert actual == document and reference['index'] == 0
    document['document']['kind'] = 'changed'
    record_path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='record_content_binding'):
        custody.record(custody.Reader(), tmp_path, 0, manifest)


def test_directory_cap(monkeypatch):
    class Entries:
        def __enter__(self):
            return iter([type('Entry', (), {'name': 'test'})()] * 20001)

        def __exit__(self, *args):
            pass
    monkeypatch.setattr(custody.os, 'scandir', lambda path: Entries())
    with pytest.raises(ValueError, match='directory_entry_cap'):
        custody.names(Path('/unused'))
