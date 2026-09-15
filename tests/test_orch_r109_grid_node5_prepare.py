import ast
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from gpu import orch_r109_grid_node5_prepare as prep


SNAPSHOT = Path(__file__).resolve().parents[1]
TEST_UUID = 'GPU-11111111-2222-3333-4444-555555555555'
TEST_HOST = 'a'*64


def definitions(raw):
    return {node.name:ast.dump(node) for node in ast.parse(raw).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


@pytest.mark.parametrize('index', [6, 7])
def test_derived_science_functions_and_caps_unchanged(index):
    raw, document = prep.render(SNAPSHOT, index, TEST_UUID, TEST_HOST)
    assert document['ready_for_GPU'] is False and document['pending']
    assert document['native_per_lane'] == 1858 and document['parent_per_lane'] == 298
    assert document['pair_native_cap'] == 3716 and document['pair_parent_cap'] == 596
    assert document['pair_gpu_hours_cap'] == 16
    assert document['hard_end_utc'] == '2026-09-15T17:02:00Z'
    for name in ('organism_v6/orch_r109_grid.py', 'gpu/orch_r109_grid_run.py',
            'gpu/orch_r109_grid_broker.py'):
        assert definitions(raw[name]) == definitions((SNAPSHOT/name).read_bytes())
    allocation = document['allocation']
    assert allocation['index'] == index and allocation['lease_end'] == prep.LEASE_END
    assert prep.HARD_END <= allocation['lease_end']-21600
    policy = {}
    exec(raw['organism_v6/orch_r109_grid.py'], policy)
    assert policy['LANES'] == {'ovx3': allocation}
    assert policy['bounds']()['native_per_lane'] == 1858
    assert policy['bounds']()['parent_per_lane'] == 298
    assert prep.native_root(index).encode() in raw['gpu/orch_r109_grid_run.py']
    assert prep.native_root(index).encode() in raw['gpu/orch_r109_grid_broker.py']


def test_distinct_roots_and_matched_roster():
    derived = [prep.render(SNAPSHOT, index, TEST_UUID, TEST_HOST) for index in (6, 7)]
    namespaces = []
    for raw, document in derived:
        namespace = {}
        exec(raw['organism_v6/orch_r109_grid.py'], namespace)
        namespaces.append(namespace)
    assert prep.native_root(6) != prep.native_root(7)
    assert namespaces[0]['roster']() == namespaces[1]['roster']()
    assert derived[0][1]['allocation']['style'] == 'supportive'
    assert derived[1][1]['allocation']['style'] == 'critical'
    assert derived[0][1]['allocation']['order'] == list(reversed(derived[1][1]['allocation']['order']))


@pytest.mark.parametrize('index', [0, 1, 2, 3, 4, 5, 8, True, '6'])
def test_refuses_other_allocations(index):
    with pytest.raises(ValueError, match='allocated_pair'):
        prep.render(SNAPSHOT, index, TEST_UUID, TEST_HOST)


@pytest.mark.parametrize('uuid,host', [('',TEST_HOST), ('pending',TEST_HOST), (TEST_UUID,''),
    (TEST_UUID,'native-hostname')])
def test_requires_identity_shape_without_inventing_discovery(uuid, host):
    with pytest.raises(ValueError, match='required'):
        prep.render(SNAPSHOT, 6, uuid, host)


def test_refuses_source_drift_and_never_writes_parent(tmp_path):
    for name in prep.PINS:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((SNAPSHOT/name).read_bytes())
    path = tmp_path/'organism_v6/orch_r109_grid.py'
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError, match='immutable_source_pin'):
        prep.render(tmp_path, 6, TEST_UUID, TEST_HOST)


def test_materializer_refuses_existing_output_and_bad_manifest(tmp_path):
    with pytest.raises(ValueError, match='new_output_only'):
        prep.materialize(SNAPSHOT, tmp_path, 6, TEST_UUID, TEST_HOST)
    (tmp_path/'SOURCE_SHA256.json').write_text('{}')
    with pytest.raises(ValueError, match='exact_parent_manifest'):
        prep.materialize(tmp_path, tmp_path/'new', 6, TEST_UUID, TEST_HOST)
    assert not (tmp_path/'new').exists()


def test_render_does_not_mutate_live_registry():
    from organism_v6 import orch_r109_grid as policy
    before = deepcopy(policy.LANES)
    pins = {name:hashlib.sha256((SNAPSHOT/name).read_bytes()).hexdigest() for name in prep.PINS}
    prep.render(SNAPSHOT, 6, TEST_UUID, TEST_HOST)
    assert policy.LANES == before
    assert pins == prep.PINS
