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


@pytest.fixture
def fixture_v2(fixture):
    root, source, tests = fixture
    for name in ready.V2_SOURCE_FILES:
        path = source / name
        if not path.exists():
            path.write_text('fixture publisher\n')
    dependency = source / 'gpu/nested_dependency.py'
    dependency.write_text('fixture transitive dependency\n')
    closure = source / 'SOURCE_CLOSURE_V2.json'
    coordinator.write(closure, dict(schema='R118_ROUTE_SOURCE_CLOSURE_V2', root=str(source),
        files={str(path.relative_to(source)): coordinator.sha(path) for path in source.rglob('*.py')}))
    coordinator.write(tests, dict(source_files={name: coordinator.sha(source / name) for name in ready.V2_SOURCE_FILES},
        passed=True, cuda_initialized=False, native_cpu=True, tests_failed=0, tests_skipped=0,
        closure_manifest=dict(path=str(closure), sha256=coordinator.sha(closure)),
        entrypoint=dict(module='gpu.orch_r111_route_pair_shared', help_exit_code=0,
                        sha256=coordinator.sha(source / 'gpu/orch_r111_route_pair_shared.py'))), replace=True)
    plan = coordinator.read(root / 'PLAN.json')
    plan['parent_wait_seconds'] = 120
    coordinator.write(root / 'PLAN.json', plan, replace=True)
    coordinator.write(root / 'SHARED_CLIENT_READY.json', dict(schema='HISTORICAL_V1', unchanged=True))
    return root, source, tests


def test_v2_publishes_separately_preserving_v1_and_live_plan(fixture_v2):
    root, source, tests = fixture_v2
    previous = (root / 'SHARED_CLIENT_READY.json').read_bytes()
    original_plan = (root / 'PLAN.json').read_bytes()
    with patch.object(coordinator, 'initialize', side_effect=AssertionError('no initialization')):
        result = ready.publish(root, source, tests, version=2)
    assert result['schema'] == 'R116_SHARED_CLIENT_READY_V2'
    assert result['executable']['source'] == str(source / 'gpu/orch_r111_route_pair_shared.py')
    assert result['source_closure']['files'] == 6
    assert result['source_closure']['path'] == str(source / 'SOURCE_CLOSURE_V2.json')
    assert coordinator.sha(result['source_closure']['path']) == result['source_closure']['sha256']
    assert result['predecessor_ready']['sha256'] == coordinator.sha(root / 'SHARED_CLIENT_READY.json')
    assert result['boundary_controller_armed'] is False
    assert result['parent_wait_seconds_unchanged'] == 120
    assert (root / 'SHARED_CLIENT_READY_V2.json').exists()
    assert (root / 'SHARED_CLIENT_READY.json').read_bytes() == previous
    assert (root / 'PLAN.json').read_bytes() == original_plan


@pytest.mark.parametrize('change', ['modify_dependency', 'add_dependency', 'remove_dependency', 'skip_native_test'])
def test_v2_rejects_incomplete_or_drifting_native_closure(fixture_v2, change):
    root, source, tests = fixture_v2
    dependency = source / 'gpu/nested_dependency.py'
    if change == 'modify_dependency':
        dependency.write_text('drift')
    elif change == 'add_dependency':
        (source / 'gpu/extra.py').write_text('unbound')
    elif change == 'remove_dependency':
        dependency.unlink()
    else:
        receipt = coordinator.read(tests)
        receipt['tests_skipped'] = 1
        coordinator.write(tests, receipt, replace=True)
    with pytest.raises(ValueError, match='closure|executable'):
        ready.publish(root, source, tests, version=2)
    assert not (root / 'SHARED_CLIENT_READY_V2.json').exists()


def test_v2_duplicate_is_rejected_without_overwriting_either_version(fixture_v2):
    root, source, tests = fixture_v2
    ready.publish(root, source, tests, version=2)
    old = (root / 'SHARED_CLIENT_READY.json').read_bytes()
    new = (root / 'SHARED_CLIENT_READY_V2.json').read_bytes()
    with pytest.raises(FileExistsError):
        ready.publish(root, source, tests, version=2)
    assert (root / 'SHARED_CLIENT_READY.json').read_bytes() == old
    assert (root / 'SHARED_CLIENT_READY_V2.json').read_bytes() == new


@pytest.mark.parametrize('attribute', ['failures', 'errors', 'skipped'])
def test_native_freeze_rejects_any_failed_or_skipped_suite(tmp_path, attribute):
    from gpu import orch_r111_route_shared_freeze as freeze

    receipt = tmp_path / 'junit.xml'
    receipt.write_text(f'<testsuites><testsuite tests="5" {attribute}="1"/></testsuites>')
    with pytest.raises(ValueError, match='all_native_CPU_tests_pass_no_skips'):
        freeze.summarize_junit(receipt)


def test_native_freeze_counts_actual_junit_suites(tmp_path):
    from gpu import orch_r111_route_shared_freeze as freeze

    receipt = tmp_path / 'junit.xml'
    receipt.write_text('<testsuites><testsuite tests="5"/><testsuite tests="3"/></testsuites>')
    assert freeze.summarize_junit(receipt) == dict(tests=8, failures=0, errors=0, skipped=0)


def test_v2_revision_preserves_prior_ready_bytes(fixture_v2):
    root, source, tests = fixture_v2
    ready.publish(root, source, tests, version=2)
    before = (root / 'SHARED_CLIENT_READY_V2.json').read_bytes()
    result = ready.publish(root, source, tests, version=2, revision=1)
    assert result['revision'] == 1
    assert result['predecessor_v2_revision']['sha256'] == coordinator.sha(root / 'SHARED_CLIENT_READY_V2.json')
    assert (root / 'SHARED_CLIENT_READY_V2.json').read_bytes() == before
    assert (root / 'SHARED_CLIENT_READY_V2_R1.json').exists()
