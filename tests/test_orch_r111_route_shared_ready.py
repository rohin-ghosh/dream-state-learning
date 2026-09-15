from pathlib import Path
from unittest.mock import patch

import pytest

from gpu import orch_r111_route_shared_ready as ready
from gpu import orch_r116_shared_learner as coordinator


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / 'life'
    source = tmp_path / 'source'
    for name in ready.SOURCE_FILES:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture source\n')
    sources = {name: coordinator.sha(source / name) for name in ready.SOURCE_FILES}
    test_receipt = tmp_path / 'CPU.json'
    coordinator.write(test_receipt, dict(source_files=sources, passed=True, cuda_initialized=False))
    coordinator.write(root / 'COHORT.json', dict(train=[dict(id='TRAIN1'), dict(id='TRAIN2')], held=[dict(id='DEV')]))
    coordinator.write(root / 'SEALED_FINAL.json', dict(tasks=[dict(id='FINAL')]))
    coordinator.write(root / 'PLAN.json', dict(root=str(root), physical=4,
        cohort_sha256=coordinator.sha(root / 'COHORT.json'), final_sha256=coordinator.sha(root / 'SEALED_FINAL.json'),
        bounds=dict(native_calls=32768, parent_calls=16384, hard_end_unix=9999999999)))
    return root, source, test_receipt


def test_readiness_publishes_ids_and_bounds_without_mutating_live_plan(fixture):
    root, source, tests = fixture
    original = (root / 'PLAN.json').read_bytes()
    with patch.object(coordinator, 'initialize', side_effect=AssertionError('readiness cannot initialize')):
        result = ready.publish(root, source, tests)
    assert result['branch'] == 'A1' and result['train_ids'] == ['TRAIN1', 'TRAIN2']
    assert result['excluded_ids'] == ['DEV', 'FINAL']
    assert result['active_shared_client'] is False
    assert result['boundary_checkpoint'] is None
    assert (root / 'PLAN.json').read_bytes() == original


def test_unbound_successor_fails_before_publication(fixture):
    root, source, tests = fixture
    (source / ready.SOURCE_FILES[0]).write_text('different source')
    with pytest.raises(ValueError, match='bound_native_CPU_tests'):
        ready.publish(root, source, tests)
    assert not (root / 'SHARED_CLIENT_READY.json').exists()


def test_source_ids_cannot_change_after_provenance(fixture):
    root, source, tests = fixture
    coordinator.write(root / 'COHORT.json', dict(train=[dict(id='FINAL')]), replace=True)
    with pytest.raises(ValueError, match='cohort_source_binding'):
        ready.publish(root, source, tests)


def test_duplicate_ready_publication_is_not_silent_overwrite(fixture):
    root, source, tests = fixture
    ready.publish(root, source, tests)
    before = (root / 'SHARED_CLIENT_READY.json').read_bytes()
    with pytest.raises(FileExistsError):
        ready.publish(root, source, tests)
    assert (root / 'SHARED_CLIENT_READY.json').read_bytes() == before
