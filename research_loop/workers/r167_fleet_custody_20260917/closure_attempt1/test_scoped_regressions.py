import hashlib
import importlib.util
import json
from pathlib import Path

import native_custody
import pytest


def test_original_birth_fields_not_context_object(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'collect_metadata.py'
    spec = importlib.util.spec_from_file_location('isolated_fleet_collector', source)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    plan = tmp_path / 'PLAN.json'
    raw = json.dumps(dict(root=str(tmp_path), system_prompt='system-only fixture',
                          birth_prompt='birth-only fixture')).encode()
    plan.write_bytes(raw)
    row = dict(life_id='C1', storage_root=str(tmp_path), process_plan_root=str(tmp_path),
               inventory_identity=dict(pid=1, start_ticks='1'),
               birth_plan=dict(path=str(plan), sha256=hashlib.sha256(raw).hexdigest()))
    result = collector.collect(row, [], 'fixture-boot')
    assert result['findings']['birth_plan']['birth_context_present'] is True
    assert result['findings']['birth_plan']['registry_sha256_matches'] is True
    assert 'system-only fixture' not in json.dumps(result)
    assert 'birth-only fixture' not in json.dumps(result)


def test_prior_source_budget_is_not_reset(tmp_path):
    path = tmp_path / 'metadata.json'
    path.write_text('{}')
    reader = native_custody.Reader()
    reader.metadata_bytes = 32 * 1024 * 1024 - 1
    with pytest.raises(ValueError, match='metadata_cap'):
        reader.raw(path)


def test_prior_TRAIN_budget_is_not_reset(tmp_path):
    path = tmp_path / 'record.json'
    path.write_text('{}')
    reader = native_custody.Reader()
    reader.journal_bytes = 64 * 1024 * 1024 - 1
    with pytest.raises(ValueError, match='TRAIN_read_cap'):
        reader.raw(path, record=True)
