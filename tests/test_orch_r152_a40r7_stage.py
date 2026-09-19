from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from gpu import orch_r152_a40r7_stage as stage
from gpu.orch_r144_target_patch import NEW_RECEIPT, OLD_ENCODING, OLD_RECEIPT


def test_repair_preserves_existing_suffix_loss_and_all_other_functions(monkeypatch):
    current = Path('gpu/orch_r125_continual_native.py').read_text()
    original = current.replace(NEW_RECEIPT, OLD_RECEIPT)
    original = original.replace('        child_exposures, anchor_exposures = 0, 0\n',
        OLD_ENCODING+'        child_exposures, anchor_exposures = 0, 0\n')
    monkeypatch.setattr(stage, 'OLD_NATIVE_SHA256', hashlib.sha256(original.encode()).hexdigest())
    monkeypatch.setattr(stage, 'PATCHED_NATIVE_SHA256', hashlib.sha256(current.encode()).hexdigest())
    assert stage.repair_native(original) == current
    with pytest.raises(ValueError, match='exact_failed_native_source'):
        stage.repair_native(original+'\n')


def test_plan_changes_only_source_and_identical_startup_path(tmp_path, monkeypatch):
    source = tmp_path/'new_source'
    source.mkdir()
    birth = source/'birth.txt'
    birth.write_text('same startup')
    original = dict(root=str(stage.BASE/'run1'), physical=7, gpu_uuid=stage.GPU_UUID,
        source_root=str(stage.OLD_SOURCE), hard_end_unix=1234, decoder={'temperature': 0.7},
        startup_context=dict(path=str(stage.OLD_SOURCE/'birth.txt'), sha256=stage.sha(birth)))
    before = deepcopy(original)
    result = stage.relocated_plan(original, source)
    assert original == before
    assert result == dict(original, source_root=str(source),
        startup_context=dict(original['startup_context'], path=str(birth)))
    birth.write_text('different')
    with pytest.raises(ValueError, match='same_startup_bytes'):
        stage.relocated_plan(original, source)


@pytest.mark.parametrize('field,value', [('physical', 4), ('root', '/different'),
    ('gpu_uuid', 'other'), ('source_root', '/different')])
def test_other_lives_are_not_recovery_targets(tmp_path, field, value):
    plan = dict(root=str(stage.BASE/'run1'), physical=7, gpu_uuid=stage.GPU_UUID,
        source_root=str(stage.OLD_SOURCE))
    plan[field] = value
    with pytest.raises(ValueError, match='same_failed_life_only'):
        stage.relocated_plan(plan, tmp_path)


@pytest.mark.parametrize('tag', ['', '../old', 'nested/path', 'with space'])
def test_stage_never_accepts_path_in_tag(tag):
    with pytest.raises(ValueError, match='safe_unique_tag'):
        stage.paths(tag)


def test_receipts_never_overwrite_and_inventory_rejects_symlinks(tmp_path):
    receipt = tmp_path/'receipt.json'
    stage.write(receipt, {'status': 'FIRST'})
    with pytest.raises(FileExistsError):
        stage.write(receipt, {'status': 'REPLACED'})
    assert stage.read(receipt) == {'status': 'FIRST'}
    (tmp_path/'linked.py').symlink_to(receipt)
    with pytest.raises(ValueError, match='no_source_symlinks'):
        stage.inventory(tmp_path)
