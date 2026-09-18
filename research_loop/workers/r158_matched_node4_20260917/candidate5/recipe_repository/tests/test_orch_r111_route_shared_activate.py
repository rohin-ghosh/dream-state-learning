import json
from pathlib import Path

import pytest

from gpu import orch_r111_route_boundary as boundary
from gpu import orch_r111_route_shared_activate as activate


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def staged_fixture(tmp_path, monkeypatch):
    root = tmp_path / 'life'
    common = tmp_path / 'shared'
    source = tmp_path / 'source'
    bounds = dict(native_calls=32768, parent_calls=16384, cycles=512, hard_end_unix=1789596240)
    plan = dict(bounds=bounds, parent_wait_seconds=120)
    put(root / 'PLAN.json', plan)
    put(root / 'PUBLICATION.json', dict(board_reference='standing owned slot', cpu_tests_passed=True))
    ready_path = root / 'READY.json'
    ready = dict(branch='A1', common_root=str(common), root=str(root), successor_source=str(source),
                 inherited_bounds=bounds, tests_receipt=dict(path='CPU.json', sha256='fixture'))
    put(ready_path, ready)
    ready_reference = boundary.reference(ready_path)
    release_reference = dict(path=str(root / 'release.json'), sha256='fixture')
    certificate = dict(release=release_reference, predecessors=[dict(pid=2147483647)],
                       preserved_files={'PLAN.json': boundary.sha(root / 'PLAN.json')})
    put(root / 'R118_SHARED_HANDOFF_BRANCH.json', certificate)
    put(root / 'R118_SHARED_SUCCESSOR_PLAN_TEMPLATE.json', dict(ready=ready_reference,
        original_plan=boundary.reference(root / 'PLAN.json'), plan=plan))
    put(common / 'HANDOFF.json', dict(branches={'A1': dict(release=release_reference)}))
    put(common / 'ADOPTION.json', dict(readiness={'A1': ready_reference}, branch_bounds={'A1': bounds},
        handoff=boundary.reference(common / 'HANDOFF.json')))
    bindings = {branch: dict(branch=branch, root=str(common), adoption_path=str(common / 'ADOPTION.json'),
        adoption_sha256=boundary.sha(common / 'ADOPTION.json')) for branch in ('F1','F2','F3','F4','A1','A2','A3','A4')}
    put(common / 'INITIALIZED.json', dict(schema='R118_SHARED_INITIALIZED_V1', bindings=bindings))
    monkeypatch.setattr(activate.client, 'Session', lambda *unused: None)
    return root, common, boundary.reference(common / 'INITIALIZED.json')


def test_no_staging_before_actual_Main_initialization(tmp_path):
    with pytest.raises(FileNotFoundError):
        activate.stage(tmp_path, dict(path=str(tmp_path / 'not-created.json'), sha256='missing'))
    assert not (tmp_path / 'R118_SHARED_BOUND_METADATA').exists()


def test_stage_binds_actual_adoption_without_modifying_current_PLAN(staged_fixture):
    root, common, initialized = staged_fixture
    before = (root / 'PLAN.json').read_bytes()
    result = activate.stage(root, initialized)
    staged = boundary.read(result['path'])
    plan = boundary.read(staged['replacements']['PLAN.json']['path'])
    assert plan['shared_learner']['branch'] == 'A1'
    assert plan['parent_wait_seconds'] == 120
    assert plan['route_boundary_release'] == boundary.read(root / 'R118_SHARED_HANDOFF_BRANCH.json')['release']
    assert staged['launched'] is False
    assert (root / 'PLAN.json').read_bytes() == before


def test_incomplete_Main_bindings_prevent_any_staging(staged_fixture):
    root, common, initialized = staged_fixture
    document = boundary.read(common / 'INITIALIZED.json')
    del document['bindings']['F4']
    put(common / 'INITIALIZED.json', document)
    with pytest.raises(ValueError, match='all_eight_Main_bindings'):
        activate.stage(root, boundary.reference(common / 'INITIALIZED.json'))
    assert not (root / 'R118_SHARED_BOUND_METADATA').exists()


def test_metadata_replacement_preserves_original_bytes_and_supports_verified_resume(staged_fixture):
    root, common, initialized = staged_fixture
    result = activate.stage(root, initialized)
    staged = boundary.read(result['path'])
    originals = {name: (root / name).read_bytes() for name in staged['originals']}
    archives = activate.replace_preserving(root, staged)
    for name, reference in archives.items():
        assert Path(reference['path']).read_bytes() == originals[name]
        assert boundary.sha(root / name) == staged['replacements'][name]['sha256']
    assert activate.replace_preserving(root, staged) == archives


def test_foreign_metadata_edit_prevents_replacement(staged_fixture):
    root, common, initialized = staged_fixture
    result = activate.stage(root, initialized)
    put(root / 'PLAN.json', dict(foreign=True))
    with pytest.raises(ValueError, match='no_foreign_metadata_edits'):
        activate.replace_preserving(root, boundary.read(result['path']))
    assert boundary.read(root / 'PLAN.json') == dict(foreign=True)


def test_historical_terminal_blocks_launch_without_deletion_or_plan_change(staged_fixture):
    root, common, initialized = staged_fixture
    result = activate.stage(root, initialized)
    original_plan = (root / 'PLAN.json').read_bytes()
    put(root / 'TERMINAL.json', dict(status='historical_terminal_preserve'))
    terminal_bytes = (root / 'TERMINAL.json').read_bytes()
    with pytest.raises(ValueError, match='no_terminal_masking'):
        activate.launch(root, result)
    assert (root / 'TERMINAL.json').read_bytes() == terminal_bytes
    assert (root / 'PLAN.json').read_bytes() == original_plan
    assert not (root / 'SHARED_TERMINAL.json').exists()
    assert not (root / 'R118_SHARED_DISPATCH_ATTEMPT.json').exists()
