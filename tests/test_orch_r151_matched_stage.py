"""CPU-only exact source transformation and prospective plan assembly checks."""

import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
from unittest.mock import Mock

import pytest

from gpu import orch_r151_matched_stage as stage
from gpu import orch_r150_guard_patch
from gpu import orch_r150_matched_native as matched


REPOSITORY = Path(__file__).resolve().parents[1]


def original_guard():
    source = (REPOSITORY/'gpu/orch_r125_continual_guard.py').read_text()
    if hashlib.sha256(source.encode()).hexdigest() != orch_r150_guard_patch.ORIGINAL_SHA256:
        source = stage.revert_guard(source)
    return source


def memory_receipts():
    root = REPOSITORY/'gpu'
    if not (root/'R145_GPU_PROOF.json').exists():
        root = REPOSITORY/'research_loop/workers/r151_stage_20260916t2030z/memory'
    paths = root/'orch_r145_node3_capacity_runtime.json', root/'R145_GPU_PROOF.json'
    if not all(path.is_file() for path in paths):
        pytest.skip('Explicit validated memory metadata fixtures absent')
    return paths


def test_guard_changes_only_fixed_initializer_callback_after_existing_gates():
    original = original_guard()
    patched = stage.patch_guard(original)
    assert stage.revert_guard(patched) == original
    intermediate = orch_r150_guard_patch.patch_source(original)
    assert patched.replace(stage.NEW_INITIALIZE, stage.OLD_INITIALIZE) == intermediate
    assert hashlib.sha256(patched.encode()).hexdigest() == 'c1358b5b478b7be8fbfde1beab43f0b7ca60db6ee019b5a7085a81844977bc85'
    tree = ast.parse(patched)
    entry = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
    calls = [node for node in ast.walk(entry) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'initialize']
    assert len(calls) == 1 and len(calls[0].keywords) == 1
    assert calls[0].keywords[0].arg == 'validate_child' and calls[0].keywords[0].value.id == 'initial_capacity'
    assert patched.index("os.environ['R125_ADMISSION_PLAN_SHA256']") < patched.index(stage.NEW_INITIALIZE)
    assert "'fresh_clear_admission'" in patched and "'native_GPU_binding'" in patched


@pytest.mark.parametrize('change', ['second_patch', 'other_callback', 'removed_check', 'changed_import'])
def test_guard_rejects_any_unbound_derivative(change):
    patched = stage.patch_guard(original_guard())
    if change == 'second_patch':
        with pytest.raises(ValueError):
            stage.patch_guard(patched)
        return
    alternatives = dict(other_callback=patched.replace('validate_child=initial_capacity', 'validate_child=other'),
        removed_check=patched.replace("'fresh_clear_admission'", "'relaxed'"),
        changed_import=patched.replace('gpu.orch_r151_memory_probe', 'other.module'))
    with pytest.raises(ValueError):
        stage.revert_guard(alternatives[change])


def mini_repository(tmp_path):
    repository = tmp_path/'repository'
    for package in ('gpu', 'organism_v6', 'tests', 'research_notes'):
        (repository/package).mkdir(parents=True)
    for name in ('orch_r125_continual_guard.py', 'orch_r125_continual_native.py'):
        source = REPOSITORY/'gpu'/name
        text = source.read_text()
        if name == 'orch_r125_continual_guard.py':
            text = original_guard()
        elif 'orch_r145_suffix_boundary' in text:
            pytest.skip('This fixture needs the unpatched working native source')
        (repository/'gpu'/name).write_text(text)
    (repository/'gpu/not_copied.env').write_text('synthetic excluded configuration')
    (repository/'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').write_text(
        (REPOSITORY/'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').read_text())
    return repository


def test_memory_safe_source_staging_keeps_inputs_immutable(tmp_path):
    repository = mini_repository(tmp_path)
    before = stage.source_files(repository)
    destination = tmp_path/'source'
    runtime, proof = memory_receipts()
    result = stage.stage_source(repository, destination, runtime, proof)
    assert stage.source_files(repository) == before
    assert result['GPU_calls'] == result['donor_retirements'] == 0
    assert not (destination/'gpu/not_copied.env').exists()
    assert 'r145_loss_arguments' in (destination/'gpu/orch_r125_continual_native.py').read_text()
    assert stage.revert_guard((destination/'gpu/orch_r125_continual_guard.py').read_text()) == original_guard()
    for relative, expected in result['files'].items():
        assert matched.native.sha(destination/relative) == expected
    with pytest.raises(ValueError, match='new_source_outside'):
        stage.stage_source(repository, destination, runtime, proof)


def test_corrupt_memory_receipt_refused_before_source_creation(tmp_path):
    repository = mini_repository(tmp_path)
    runtime, proof = memory_receipts()
    corrupted = tmp_path/'corrupt.json'
    corrupted.write_text('{}')
    with pytest.raises(ValueError, match='same_validated_runtime'):
        stage.stage_source(repository, tmp_path/'source', corrupted, proof)
    assert not (tmp_path/'source').exists()


def test_input_symlink_is_never_packaged(tmp_path):
    repository = mini_repository(tmp_path)
    (repository/'gpu/linked.py').symlink_to(repository/'gpu/orch_r125_continual_native.py')
    with pytest.raises(ValueError, match='canonical_staging_paths'):
        stage.source_files(repository)


def test_source_race_fails_without_manifest_publication(tmp_path, monkeypatch):
    repository = mini_repository(tmp_path)
    runtime, proof = memory_receipts()
    original = stage.source_files(repository)
    monkeypatch.setattr(stage, 'source_files', Mock(side_effect=[original, {}]))
    with pytest.raises(ValueError, match='source_inputs_unchanged'):
        stage.stage_source(repository, tmp_path/'source', runtime, proof)
    assert not (tmp_path/'source/STAGED_SOURCE.json').exists()


def test_cohort_requires_capacity_proof_on_all_arms_and_does_not_allocate(tmp_path, monkeypatch):
    repository = mini_repository(tmp_path)
    runtime, proof = memory_receipts()
    source = tmp_path/'source'
    stage.stage_source(repository, source, runtime, proof)
    lease = tmp_path/'LEASE.json'
    document = dict(lease_extended=False, safety_margin_seconds=600,
        hard_end_unix=stage.time.time()+3600, lease_end_unix=stage.time.time()+4200)
    document['lease_end_unix'] = document['hard_end_unix']+600
    matched.native.write_once(lease, document)
    monkeypatch.setattr(stage, 'LEASE_SHA256', matched.native.sha(lease))
    monkeypatch.setattr(stage, 'BASE', tmp_path)
    output = tmp_path/'orch_r151_fixture'
    result = stage.prepare_cohort(source, output, lease)
    assert result['GPU_calls'] == result['donor_retirements'] == 0
    assert not (output/'common_initial').exists()
    for arm, reference in result['plans'].items():
        plan = matched.native.read(reference['path'])
        assert plan['physical'] == stage.ARM_DEVICES[arm] and plan['max_sleeps'] is None
        assert plan['initialization_validation_schema'] == 'R151_MATCHED_INITIAL_CAPACITY_V1'
        assert plan['parent_enabled'] is (arm != 'unparented_learning')
        assert plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
        assert not Path(plan['root']).exists()
        assert matched.validate_plan(plan)[0] == plan
        with pytest.raises(ValueError, match='required_initial_GPU_capacity'):
            matched.verify_initialization_validation(plan, matched.native.read(output/'COHORT.json'), {})
