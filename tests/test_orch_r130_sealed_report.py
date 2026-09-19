"""Synthetic-only CPU tests for sealed report reduction."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from gpu import orch_r130_sealed_report as report


def task():
    return dict(task_id='synthetic', family='synthetic', messages=[dict(role='user', content='synthetic')],
        scoring=dict(type='exact', answer='synthetic-key', response_format='text'))


def record(correct=True, valid=True, parse=True, confidence=None):
    return dict(status='COMPLETE', response_valid=valid,
        score=dict(parse_valid=parse, correct=correct, brier=confidence))


def test_paired_excludes_missing_invalid_and_behavior():
    item = task()
    behavior = dict(item, task_id='behavior', scoring=dict(type='behavior'))
    left = {'synthetic': record(False)}
    right = {'synthetic': record(True)}
    result = report.paired([item, behavior], left, right)
    assert result['expected_scored_pairs'] == result['jointly_valid_pairs'] == 1
    assert result['gained'] == result['accuracy_delta_on_jointly_valid'] == 1
    for bad in ({}, {'synthetic': record(valid=False)}, {'synthetic': record(parse=False)}):
        result = report.paired([item], left, bad)
        assert result['jointly_valid_pairs'] == 0
        assert result['excluded_pairs'] == 1
        assert result['accuracy_delta_on_jointly_valid'] is None


def test_confidence_optional_and_paired_only():
    left = {'synthetic': record(confidence=0.8)}
    right = {'synthetic': record(confidence=0.2)}
    result = report.paired([task()], left, right)
    assert result['brier_delta_on_jointly_valid_confidence'] == pytest.approx(-0.6)
    right['synthetic']['score']['brier'] = None
    assert report.paired([task()], left, right)['confidence_pairs'] == 0


def test_wilson_empty_small_and_complete():
    assert report.wilson(0, 0) is None
    assert report.wilson(1, 1)[0] < 0.21
    assert report.wilson(0, 1)[1] > 0.79
    with pytest.raises(ValueError):
        report.wilson(2, 1)


def test_private_exclusive_writes(tmp_path):
    path = tmp_path / 'sealed'
    report.write_private(path, 'private synthetic')
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        report.write_private(path, 'replacement')
    assert path.read_text() == 'private synthetic'


def test_hash_gate_writes_nothing(tmp_path):
    config = tmp_path / 'config.json'
    config.write_text('{}')
    before = config.read_bytes()
    with pytest.raises(ValueError):
        report.build(config, tmp_path / 'sealed_scientific_report_test')
    assert config.read_bytes() == before
    assert list(tmp_path.iterdir()) == [config]


def test_report_scientific_limits():
    curve = dict(created_utc='synthetic', corpus_sha256='a' * 64, runner_sha256='b' * 64,
        checkpoints=[], paired_comparisons=[])
    original = deepcopy(curve)
    rendered = report.render(curve)
    assert 'not semantic thought units' in rendered
    assert 'neither consciousness nor a general learning/improvement claim is established' in rendered
    assert 'Do not transmit' in rendered
    assert 'independent random population samples' in rendered
    assert 'identity-based reader ACL' in rendered
    assert curve == original


def test_tampered_checkpoint_rejected_before_contents(tmp_path):
    path = tmp_path / 'COMPLETE.json'
    path.write_text(json.dumps({'synthetic': True}))
    with pytest.raises(ValueError):
        report.load_checkpoint(dict(complete_path=str(path), complete_sha256='a' * 64), 'b' * 64)


def test_build_synthetic_snapshot_readonly_and_safe_receipt(tmp_path, monkeypatch):
    def dump(path, value):
        path.write_text(json.dumps(value))
        return report.sha(path)

    source = tmp_path / 'source/gpu'
    source.mkdir(parents=True)
    (source / 'orch_r130_checkpoint_benchmark.py').write_bytes(Path(report.runner.__file__).read_bytes())
    lineage_path = tmp_path / 'lineages.json'
    lineages = [dict(lineage_id=name, cohort='original', initial_commit_sha256=letter * 64)
        for name, letter in [('legacy', 'a'), ('pilot', 'b'), ('kernel', 'c')]]
    lineage_sha = dump(lineage_path, dict(schema=report.scheduler.LINEAGES_SCHEMA, lineages=lineages))
    registry_path = tmp_path / 'registry.json'
    registry_sha = dump(registry_path, dict(checkpoints=[dict(label=name + '_initial',
        checkpoint_commit_sha256=letter * 64) for name, letter in [('legacy', 'a'), ('pilot', 'b'), ('kernel', 'c')]]))
    ledger = tmp_path / 'ledger'
    ledger.mkdir()
    config_path = tmp_path / 'config.json'
    config_sha = dump(config_path, dict(operator_root=str(tmp_path), registry_path=str(registry_path),
        lineages_path=str(lineage_path), lineages_sha256=lineage_sha,
        source_root=str(source.parent), ledger_root=str(ledger)))
    monkeypatch.setattr(report, 'CONFIG_SHA256', config_sha)
    monkeypatch.setattr(report.scheduler, 'REGISTRY_SHA256', registry_sha)
    monkeypatch.setattr(report.scheduler, 'seed_completed', lambda *args: set())
    monkeypatch.setattr(report.scheduler, 'ledger_state', lambda *args: None)
    def synthetic_load(row, initial):
        return (dict(row, is_initial=True, optimizer_steps=0, families={}), [task()], [], {})
    monkeypatch.setattr(report, 'load_checkpoint', synthetic_load)
    inputs = {path: path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()}
    output = tmp_path / 'sealed_scientific_report_test'
    receipt = report.build(config_path, output)
    assert receipt['completed_checkpoint_count'] == 3
    assert 'synthetic-key' not in json.dumps(receipt)
    assert all(path.read_bytes() == raw for path, raw in inputs.items())
    assert output.stat().st_mode & 0o777 == 0o700
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in output.iterdir())
    assert all(report.sha(output / name) == checksum for name, checksum in receipt['artifacts'].items())
    with pytest.raises(ValueError):
        report.build(config_path, output)
