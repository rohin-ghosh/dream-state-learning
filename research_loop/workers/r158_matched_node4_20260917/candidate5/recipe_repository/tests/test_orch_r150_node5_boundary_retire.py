from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from gpu import orch_r150_node5_boundary_retire as retirement


NOW = 1789588560


def ref(name):
    return retirement.reference(retirement.BASE+'/r150_metadata_fixture/'+name, 'a'*64)


def complete_metadata():
    document = retirement.contract()
    document['observed_unix'] = NOW
    child = document['child']
    child.update(ready=True, cpu_passed=True, lease_scope_verified=True, expected_duration_seconds=60,
        plan=ref('PLAN.json'), source_manifest=ref('SOURCE_MANIFEST.json'), cpu_gate=ref('CPU_GATE.json'))
    document['main_go'] = dict(authorized=True, published_by='MAIN', physicals=[0, 3, 4],
        receipt=ref('MAIN_GO.json'), not_before_unix=NOW-1, expires_unix=NOW+300,
        **{key: deepcopy(child[key]) for key in ('plan', 'source_manifest', 'cpu_gate')})
    for lane in document['lanes']:
        lane.update(observed_unix=NOW, children_reaped=True, active_work_count=0, future_charges=0)
        boundary = lane['boundary']
        boundary.update(cycle=111, sleep=111, complete=True)
        boundary['preserved'] = {key: ref(key+'.json') for key in boundary['preserved']}
        if lane['physical'] == 3:
            boundary.update(optimizer_used=False, failed_predispatch_charges=[4456])
        else:
            boundary['readouts'] = {scope: dict(status='COMPLETE', returncode=0, reaped=True,
                sleep=111, checkpoint_sha256='a'*64, process_result=ref(scope+'/PROCESS_RESULT.json'),
                complete=ref(scope+'/COMPLETE.json')) for scope in ('dev', 'open')}
    return document


def test_complete_metadata_never_authorizes_execution_or_hides_runtime_blockers():
    result = retirement.assess(complete_metadata(), NOW)
    assert result['blockers'] == []
    assert result['status'] == 'METADATA_PREREQUISITES_MET_RUNTIME_BLOCKED'
    assert result['execution_permitted'] is False
    assert result['signals_sent'] == result['remote_mutations'] == 0
    assert 'F4_current_runtime_RNG_capture_not_implemented' in result['runtime_blockers']
    assert 'original_privileged_scan_required_after_actual_exit' in result['runtime_blockers']
    assert result['protected_physicals'] == [1, 2, 5, 6, 7]


def test_contract_is_unready_and_has_exact_known_owners():
    document = retirement.contract()
    assert document['main_go'] is None
    assert document['scope'] == [0, 3, 4]
    assert [lane['owner']['pid'] for lane in document['lanes']] == [2664733, 4148447, 3356568]
    assert retirement.assess(document, NOW)['status'] == 'BLOCKED'


@pytest.mark.parametrize('scope', [[0, 3, 5], [0, 3, 4, 2], [0, 3, 3], [False, 3, 4], None])
def test_protected_or_ambiguous_scope_rejected(scope):
    document = complete_metadata()
    document['scope'] = scope
    assert 'only_exact_0_3_4_scope' in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('field,value', [('pid', 155897), ('start_ticks', '1'), ('uid', 0),
    ('boot_id', 'another-boot'), ('cmdline_sha256', 'b'*64)])
def test_original_identity_drift_never_waived(field, value):
    document = complete_metadata()
    document['lanes'][0]['owner'][field] = value
    assert 'physical0:owner_drift' in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('field', ['plan', 'source_manifest', 'cpu_gate'])
def test_MAIN_GO_must_join_exact_ready_child(field):
    document = complete_metadata()
    document['main_go'][field]['sha256'] = 'b'*64
    assert 'MAIN_GO_ready_child_'+field+'_join' in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('permission', [None, {}, {'authorized': True, 'published_by': 'watcher'}])
def test_no_inferred_MAIN_GO(permission):
    document = complete_metadata()
    document['main_go'] = permission
    assert 'MAIN_GO_missing' in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('field,value,reason', [
    ('active_work_count', 1, 'started_learning_or_readout'),
    ('active_work_count', False, 'started_learning_or_readout'),
    ('future_charges', 1, 'successor_already_charged'),
    ('children_reaped', False, 'started_child_not_reaped'),
    ('observed_unix', NOW-121, 'stale_owner_boundary'),
    ('observed_unix', NOW+1, 'stale_owner_boundary'),
    ('uuid', retirement.UUIDS[4], 'UUID_drift'),
])
def test_started_work_and_stale_metadata_are_not_a_boundary(field, value, reason):
    document = complete_metadata()
    document['lanes'][0][field] = value
    assert 'physical0:'+reason in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('scope', ['dev', 'open'])
@pytest.mark.parametrize('field,value', [('status', 'CRASHED_READOUT_CONTINUE_LIFE'),
    ('status', 'READOUT_WALL_CONTINUE_LIFE'), ('returncode', 1), ('returncode', False),
    ('reaped', False), ('sleep', 110), ('checkpoint_sha256', 'b'*64), ('complete', None)])
def test_finished_fresh_readout_is_more_than_marker_existence(scope, field, value):
    document = complete_metadata()
    document['lanes'][0]['boundary']['readouts'][scope][field] = value
    assert 'physical0:'+scope+'_fresh_readout_not_successfully_finished' in retirement.assess(document, NOW)['blockers']


@pytest.mark.parametrize('component', retirement.COMPONENTS['route'])
def test_every_route_preservation_component_required(component):
    document = complete_metadata()
    document['lanes'][0]['boundary']['preserved'].pop(component)
    assert 'physical0:preserve_'+component in retirement.assess(document, NOW)['blockers']


def test_grid_ancestral_rng_is_not_current_runtime_rng():
    document = complete_metadata()
    boundary = document['lanes'][1]['boundary']
    boundary['preserved']['optimizer_rng'] = ref('ancestral_optimizer_rng.pt')
    boundary['preserved'].pop('runtime_rng')
    boundary['failed_predispatch_charges'] = []
    result = retirement.assess(document, NOW)
    assert 'physical3:preserve_runtime_rng' in result['blockers']
    assert 'physical3:failed_charge4456_preserved' in result['blockers']


@pytest.mark.parametrize('wall', [retirement.HARD_END+1, 1789617240, NOW, float('nan'), float('inf'), True])
def test_other_lane_lease_and_invalid_walls_not_inherited(wall):
    document = complete_metadata()
    document['child']['hard_end_unix'] = wall
    assert 'incompatible_child_wall_no_extension' in retirement.assess(document, NOW)['blockers']


def test_expired_wall_and_inadequate_duration():
    document = complete_metadata()
    document['child']['expected_duration_seconds'] = retirement.HARD_END-NOW
    assert 'insufficient_remaining_window' in retirement.assess(document, NOW)['blockers']
    assert 'legacy_wall_expired_no_renewal' in retirement.assess(document, retirement.HARD_END)['blockers']
    assert 'physical3:TRAIN_window_closed' in retirement.assess(document, retirement.F4_TRAIN_END)['blockers']


@pytest.mark.parametrize('path', ['/tmp/unbound.json', retirement.BASE+'/../escape',
    retirement.BASE+'/bad\npath', retirement.BASE+'/bad\x00path'])
def test_invalid_bound_paths_rejected(path):
    assert not retirement.valid_ref(dict(path=path, sha256='a'*64))


def test_duplicate_lane_and_lease_hash_drift():
    document = complete_metadata()
    document['lanes'][0]['lease']['sha256'] = 'b'*64
    document['lanes'].append(deepcopy(document['lanes'][0]))
    result = retirement.assess(document, NOW)
    assert 'exact_three_unique_target_records' in result['blockers']
    assert 'physical0:lease_drift' in result['blockers']


def test_input_unchanged_and_no_payload_echo():
    document = complete_metadata()
    document['unexpected_sensitive_content'] = 'DO_NOT_ECHO'
    before = deepcopy(document)
    result = retirement.assess(document, NOW)
    assert document == before
    assert 'DO_NOT_ECHO' not in json.dumps(result)


def test_float_owner_identity_not_accepted_as_exact_integer():
    document = complete_metadata()
    document['lanes'][0]['owner']['pid'] = 2664733.0
    assert 'physical0:integer_owner_identity' in retirement.assess(document, NOW)['blockers']


def test_even_complete_planning_cli_returns_blocked(monkeypatch, capsys):
    import io
    monkeypatch.setattr(sys, 'argv', ['planner', 'assess'])
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(complete_metadata())))
    monkeypatch.setattr(retirement.time, 'time', lambda: NOW)
    assert retirement.main() == 2
    assert json.loads(capsys.readouterr().out)['execution_permitted'] is False


def test_cli_contract_and_assessment_only(tmp_path):
    script = Path(retirement.__file__).resolve()
    result = subprocess.run([sys.executable, '-B', str(script), 'contract'], cwd=tmp_path,
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)['schema'] == retirement.SCHEMA
    denied = subprocess.run([sys.executable, '-B', str(script), 'assess'], cwd=tmp_path,
        input=result.stdout, capture_output=True, text=True)
    assert denied.returncode == 2
    assert json.loads(denied.stdout)['execution_permitted'] is False
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('payload', ['{"schema":1,"schema":2}', '[]', 'not JSON'])
def test_cli_invalid_metadata_does_not_echo_content(payload, tmp_path):
    result = subprocess.run([sys.executable, '-B', retirement.__file__, 'assess'], cwd=tmp_path,
        input=payload, capture_output=True, text=True)
    assert result.returncode == 2
    assert json.loads(result.stdout) == dict(status='INVALID_METADATA', execution_permitted=False)


@pytest.mark.parametrize('action', ['retire', 'release', 'launch', 'arm', 'publish'])
def test_cli_has_no_mutating_actions(action, tmp_path):
    result = subprocess.run([sys.executable, '-B', retirement.__file__, action], cwd=tmp_path,
        capture_output=True, text=True)
    assert result.returncode == 2
    assert list(tmp_path.iterdir()) == []
