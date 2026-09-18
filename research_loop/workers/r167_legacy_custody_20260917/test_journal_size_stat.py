import os
from pathlib import Path

import pytest

import journal_size_stat as census


def fixture(tmp_path):
    stream = tmp_path / 'stream'
    records = stream / 'records'
    records.mkdir(parents=True)
    (stream / 'JOURNAL.json').write_bytes(b'header')
    for index in range(3):
        (records / f'{index:020d}.json').write_bytes(b'record' * (index + 1))
        (records / f'{index:020d}.intent.json').write_bytes(b'intent')
    return records


def test_exact_stat_sums_without_reading_contents(tmp_path, monkeypatch):
    fixture(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError('no content reads')
    monkeypatch.setattr(Path, 'read_bytes', forbidden)
    monkeypatch.setattr(Path, 'read_text', forbidden)
    result = census.collect(tmp_path, 1)
    assert result['completed_prefix']['total_bytes'] == 6 + 6 + 12 + 6 + 6
    assert result['full_observed']['total_bytes'] == 6 + 6 + 12 + 18 + 18
    assert result['TRAIN_content_bytes_read'] == 0


def test_missing_frontier_intent_refuses(tmp_path):
    records = fixture(tmp_path)
    (records / f'{1:020d}.intent.json').unlink()
    with pytest.raises(ValueError, match='complete_names'):
        census.collect(tmp_path, 1)


def test_symlink_record_refuses(tmp_path):
    records = fixture(tmp_path)
    path = records / f'{1:020d}.json'
    path.unlink()
    path.symlink_to(records / f'{0:020d}.json')
    with pytest.raises(ValueError, match='regular_TRAIN'):
        census.collect(tmp_path, 1)


def test_budget_exceeded_reported_without_read_or_extension(tmp_path):
    records = fixture(tmp_path)
    with (records / f'{1:020d}.json').open('wb') as output:
        output.truncate(321 * 1024 * 1024)
    result = census.collect(tmp_path, 1)
    assert result['completed_prefix_exceeds_320MiB']
    assert result['completed_prefix_remaining_320MiB'] < 0
    assert not result['allocated_budget_changed']
