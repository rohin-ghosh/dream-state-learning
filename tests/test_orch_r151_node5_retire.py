from contextlib import contextmanager
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from gpu import orch_r151_node5_retire as retirement


NOW = 1789590582


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return retirement.reference(path)


@pytest.fixture
def route_root(tmp_path, monkeypatch):
    root = tmp_path / 'old_F1'
    folder = root / 'cycle_0001'
    adapter = folder / 'checkpoint/adapter'
    adapter.mkdir(parents=True)
    (adapter / 'adapter.bin').write_bytes(b'unchanged-adapter')
    optimizer = folder / 'checkpoint/optimizer_rng.pt'
    optimizer.write_bytes(b'opaque-optimizer-rng-never-deserialized')
    checkpoint = folder / 'checkpoint/CHECKPOINT.json'
    checkpoint_ref = put(checkpoint, dict(complete=True, cycle=1, sleeps=1,
        optimizer_rng_sha256=retirement.sha(optimizer),
        adapter=dict(path=str(adapter), files=[['adapter.bin', retirement.sha(adapter / 'adapter.bin')]])))
    history = put(root / 'HISTORY.json', [])
    put(root / retirement.route.PLAN, dict(next_cycle=1, history=history,
        inherited_metrics=dict(optimizer_steps=0, child_token_exposures=0, anchor_token_exposures=0)))
    put(root / 'OWN_CARRY.json', dict(checkpoint_sha256=checkpoint_ref['sha256'], reflection='TRAIN carry'))
    put(folder / 'COMPLETE.json', dict(cycle=1, sleeps=1))
    put(folder / 'SLEEP.json', dict(sleeps=1, checkpoint_sha256=checkpoint_ref['sha256'],
        updates=1, child_token_exposure_including_eos=2, anchor_token_exposure_including_eos=3))
    call = put(folder / 'CALL_000001.json', dict(response='TRAIN response', finished_unix=NOW,
        parent_delivery_ids=[], head_settings={}))
    put(folder / 'ROWS.json', [dict(source_call_path=call['path'], source_call_sha256=call['sha256'])])
    (root / 'RESERVATIONS.jsonl').write_text(json.dumps(dict(kind='NATIVE', cycle=1, number=1)) + '\n')
    for output in (root / 'readout_0001', root / 'open_readouts/readout_0001'):
        put(output / 'PROCESS_RESULT.json', dict(status='COMPLETE', returncode=0, finished_unix=NOW))
        put(output / 'LAUNCH.json', dict(pid=2000000000, checkpoint=str(checkpoint), parent_free=True, context_free=True))
        put(output / 'COMPLETE.json', dict(forbidden_readout_payload='MUST_NOT_READ_OR_RETURN'))
    put(root / 'historical_failed/CRASH.json', dict(status='FAILED', evidence='keep'))
    put(root / 'historical_failed/PENDING.json', dict(status='STARTED', evidence='keep'))
    (root / 'R121_PARENT_DELIVERY').mkdir()
    monkeypatch.setitem(retirement.TARGETS, 0, dict(retirement.TARGETS[0], root=root))
    return root


@pytest.fixture
def bound_request(tmp_path, monkeypatch, route_root):
    monkeypatch.setattr(retirement, 'BASE', tmp_path)
    monkeypatch.setattr(retirement.time, 'time', lambda: NOW)
    native = tmp_path / 'old-source/native.py'
    native.parent.mkdir()
    native.write_text('SOURCE = "frozen"\n')
    required = {str(native): retirement.sha(native),
        str(route_root / retirement.route.PLAN): retirement.sha(route_root / retirement.route.PLAN)}
    monkeypatch.setattr(retirement, 'required_pins', lambda physical: required)
    pins = dict(required)
    for source in (retirement.__file__, retirement.route.__file__, retirement.grid.__file__):
        pins[str(Path(source).resolve())] = retirement.sha(source)
    suite = retirement.reference(Path(__file__).resolve())
    cpu_ref = put(tmp_path / 'CPU_TESTS.json', dict(passed=True, source_pins=pins, suite=suite))
    child_source = tmp_path / 'replacement_source/native.py'
    child_source.parent.mkdir()
    child_source.write_text('NEW_MATCHED_LIFE = True\n')
    capsule_path = child_source.parent / 'capsule.py'
    capsule_path.write_text('CAPSULE = "CPU fixture only"\n')
    files = {path.name: retirement.sha(path) for path in (child_source, capsule_path)}
    source_manifest = put(tmp_path / 'REPLACEMENT_SOURCES.json', dict(files=files))
    common = dict(source_root=str(child_source.parent), hard_end_unix=retirement.COHORT_HARD_END,
        lease_end_unix=retirement.LEASE_END, initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
    members = {arm: dict(physical=physical, gpu_uuid=retirement.TARGETS[physical]['uuid'],
        root=str(tmp_path / 'cohort' / arm), parent_enabled=arm != 'unparented_learning')
        for arm, physical in retirement.ARM_PHYSICALS.items()}
    cohort = put(tmp_path / 'cohort/COHORT.json', dict(schema='R150_MATCHED_CONTINUAL_COHORT_V1',
        common=common, members=members, initial_directory=str(tmp_path / 'cohort/common_initial'),
        initial_optimizer_steps=0, fresh_histories=True, evaluations_gate_continuation=False))
    plans = {arm: put(tmp_path / 'cohort' / (arm + '.PLAN.json'), dict(common, **member,
        matched_arm=arm, matched_cohort=cohort)) for arm, member in members.items()}
    tests = put(tmp_path / 'REPLACEMENT_TESTS.json', dict(status='PASS',
        source_manifest_sha256=source_manifest['sha256'], matched_cohort_sha256=cohort['sha256'], suite=suite))
    generic = put(tmp_path / 'GENERIC_R131.json', dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1',
        hard_end_unix=retirement.COHORT_HARD_END, lease_end_unix=retirement.LEASE_END,
        safety_margin_seconds=600, lease_extended=False))
    monkeypatch.setattr(retirement, 'GENERIC_LEASE_SHA256', generic['sha256'])
    budget = put(tmp_path / 'cohort/LEASE_BUDGET.json', dict(schema='R151_EXISTING_NODE5_COHORT_BUDGET_V1',
        derived_from=generic, hard_end_unix=retirement.COHORT_HARD_END, lease_end_unix=retirement.LEASE_END,
        safety_margin_seconds=600, lease_extended=False, existing_life_wall_changed=False,
        physical_devices=[0, 3, 4], host_sha256=hashlib.sha256(retirement.HOST.encode()).hexdigest()))
    allocation = put(tmp_path / 'ALLOCATION.json', dict(plan_sha256=plans['parented_learning']['sha256'],
        physical=0, gpu_uuid=retirement.TARGETS[0]['uuid'], cpu_tests_passed=True, builder_entry_pushed=True,
        declared_unix=NOW))
    intake = put(tmp_path / 'INTAKE.json', dict(CPU_fixture_only=True))
    (tmp_path / 'launch_attempts').mkdir()
    config = dict(phase='initialize', matched_arm='parented_learning', resume=False,
        attempt_dir=str(tmp_path / 'launch_attempts/initialize_0'),
        matched_cohort_sha256=cohort['sha256'], hard_end_unix=retirement.COHORT_HARD_END,
        host_sha256=hashlib.sha256(retirement.HOST.encode()).hexdigest(), boot_id=retirement.BOOT, source_pins=files)
    for name, value in (('plan', plans['parented_learning']), ('lease', budget), ('source_manifest', source_manifest),
            ('cpu_gate', tests), ('allocation', allocation), ('intake', intake), ('capsule', retirement.reference(capsule_path))):
        config[name + '_path'], config[name + '_sha256'] = value['path'], value['sha256']
    config_ref = put(tmp_path / 'INITIALIZE_CONFIG.json', config)
    replacement = put(tmp_path / 'REPLACEMENT_READY.json', dict(schema='R151_SELECTED_DONOR_READY_V2',
        status='READY_FOR_SELECTED_PHASE', phase='initialize', selected_physical=0,
        new_matched_life=True, resume=False, old_artifacts_untouched=True, blockers=[], physicals=[0, 3, 4],
        observed_unix=NOW, hard_end_unix=retirement.COHORT_HARD_END, source_manifest=source_manifest,
        plans=plans, cohort=cohort, tests=tests, lease_budget=budget, config=config_ref,
        post_exit_fresh_admission_required=True))
    document = dict(schema='R151_NODE5_RETIRE_REQUEST_V2', physical=0, replacement_phase='initialize',
        actor=retirement.expected_actor(0), stage=str(tmp_path / 'attempt1'), source_pins=pins,
        cpu_tests=cpu_ref, replacement=replacement, wait_seconds=1, pause_seconds=1,
        exit_seconds=1, remaining_seconds=30)
    return dict(request=document, request_path=tmp_path / 'REQUEST.json', go_path=tmp_path / 'GO.json')


def authorize(fixture):
    request = fixture['request']
    request_ref = put(fixture['request_path'], request)
    go_ref = put(fixture['go_path'], dict(authorized=True, published_by='Main',
        action='retire_old_episodic_actor', request=request_ref, replacement=request['replacement'],
        physical=request['physical'], actor=request['actor'], replacement_phase=request['replacement_phase'],
        launch_authorized=False,
        not_before_unix=NOW - 1, expires_unix=NOW + 60))
    return request_ref, go_ref


def update_ref(reference, **changes):
    document = retirement.read(reference['path'])
    document.update(changes)
    return put(Path(reference['path']), document)


def set_phase(fixture, phase, physical=0):
    request = fixture['request']
    replacement = retirement.checked(request['replacement'])
    arm = next(arm for arm, slot in retirement.ARM_PHYSICALS.items() if slot == physical)
    plan_ref = replacement['plans'][arm]
    config = retirement.checked(replacement['config'])
    config.update(phase=phase, matched_arm=arm, plan_path=plan_ref['path'], plan_sha256=plan_ref['sha256'],
        attempt_dir=str(Path(config['attempt_dir']).parent / f'{phase}_{physical}'))
    allocation_ref = update_ref(dict(path=config['allocation_path'], sha256=config['allocation_sha256']),
        plan_sha256=plan_ref['sha256'], physical=physical, gpu_uuid=retirement.TARGETS[physical]['uuid'])
    config['allocation_sha256'] = allocation_ref['sha256']
    config_ref = put(Path(replacement['config']['path']), config)
    request.update(physical=physical, actor=retirement.expected_actor(physical), replacement_phase=phase,
        replacement=update_ref(request['replacement'], phase=phase, selected_physical=physical, config=config_ref))


def saved_initial(fixture):
    request = fixture['request']
    replacement = retirement.checked(request['replacement'])
    cohort = retirement.checked(replacement['cohort'])
    initial = Path(cohort['initial_directory'])
    commit_ref = put(initial / 'COMMIT.json', dict(optimizer_steps=0))
    proof_ref = put(initial / 'capacity_validation/RESULT.json', dict(status='PASS',
        schema='R151_MATCHED_INITIAL_CAPACITY_V1', state_restored=True, optimizer_updates=0))
    initialized_ref = put(initial / 'INITIALIZED.json', dict(cohort_sha256=replacement['cohort']['sha256'],
        source_plan_sha256=replacement['plans']['parented_learning']['sha256'],
        checkpoint_commit_sha256=commit_ref['sha256'], initialization_validation=dict(proof_ref,
            status='PASS', schema='R151_MATCHED_INITIAL_CAPACITY_V1')))
    request['replacement'] = update_ref(request['replacement'], initialization=initialized_ref)
    return initial


def rebind_budget(fixture, **changes):
    request = fixture['request']
    replacement = retirement.checked(request['replacement'])
    budget_ref = update_ref(replacement['lease_budget'], **changes)
    config_ref = update_ref(replacement['config'], lease_path=budget_ref['path'], lease_sha256=budget_ref['sha256'])
    request['replacement'] = update_ref(request['replacement'], lease_budget=budget_ref, config=config_ref)


@pytest.mark.parametrize('physical', [False, True, 1, 2, 5, 6, 7, -1, 8, '0', None])
def test_protected_or_ambiguous_scope_is_impossible(physical):
    with pytest.raises(retirement.Blocked, match='only_old'):
        retirement.target(physical)


def test_contract_is_not_authorization():
    document = retirement.contract(3)
    assert document['replacement'] is document['cpu_tests'] is None
    assert document['Main_later_exact_GO_required'] is True
    assert 'NEVER captured current sampling RNG' in document['F4_availability_limitation']
    assert document['protected_physicals'] == [1, 2, 5, 6, 7]


def test_valid_actual_file_bindings(bound_request):
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    assert request['physical'] == 0
    assert permission['authorized'] is True
    assert stamps[str(Path(retirement.__file__).resolve())]
    assert not Path(request['stage']).exists()


def test_designated_0_bootstrap_needs_no_initial_or_branch_directories(bound_request, monkeypatch):
    replacement = retirement.checked(bound_request['request']['replacement'])
    cohort = retirement.checked(replacement['cohort'])
    outputs = [cohort['initial_directory'], *(member['root'] for member in cohort['members'].values())]
    outputs.append(retirement.checked(replacement['config'])['attempt_dir'])
    assert all(not Path(path).exists() for path in outputs)
    def forbidden():
        pytest.fail('another donor timer is not a designated0 initialization prerequisite')
    monkeypatch.setattr(retirement, 'timer_metadata', forbidden)
    bound_request['request']['replacement'] = update_ref(bound_request['request']['replacement'],
        later_run_blockers=['F4_timer_and_phase_process_custody_not_proven'])
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    assert request['replacement_phase'] == 'initialize'
    assert set(request['_absent_outputs']) == set(outputs)
    assert all(not Path(path).exists() for path in outputs)


def test_new_cohort_0354_budget_does_not_extend_donor_2204_wall(bound_request):
    bound_request['request']['remaining_seconds'] = retirement.HARD_END - NOW + 600
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    assert request['_replacement_wall'] == retirement.COHORT_HARD_END > retirement.HARD_END
    assert permission['expires_unix'] <= retirement.HARD_END
    assert retirement.HARD_END == 1789596240


def test_long_cohort_cannot_retire_donor_after_its_own_wall(bound_request, monkeypatch):
    request_ref, go_ref = authorize(bound_request)
    monkeypatch.setattr(retirement.time, 'time', lambda: retirement.HARD_END + 1)
    with pytest.raises(retirement.Blocked, match='GO_expired_or_future'):
        retirement.validate_bindings(request_ref, go_ref)


def test_donor_needs_its_own_pause_exit_margin_even_with_later_cohort_wall(bound_request):
    request_ref, go_ref = authorize(bound_request)
    go_ref = update_ref(go_ref, expires_unix=NOW + 1.5)
    with pytest.raises(retirement.Blocked, match='donor_retirement_window_exhausted'):
        retirement.validate_bindings(request_ref, go_ref)


@pytest.mark.parametrize('change', [dict(lease_extended=True), dict(existing_life_wall_changed=True),
    dict(hard_end_unix=retirement.COHORT_HARD_END + 1), dict(lease_end_unix=retirement.LEASE_END + 1),
    dict(physical_devices=[0, 3, 5]), dict(safety_margin_seconds=0), dict(host_sha256='wrong-host'),
    dict(schema='R131_EXISTING_LEASE_RUNTIME_BUDGET_V1')])
def test_phase_budget_is_actual_scoped_derivation_not_donor_extension(bound_request, change):
    rebind_budget(bound_request, **change)
    with pytest.raises(retirement.Blocked):
        retirement.validate_bindings(*authorize(bound_request))


def test_generic_lease_reference_must_be_actual_pinned_R131_bytes(bound_request):
    replacement = retirement.checked(bound_request['request']['replacement'])
    budget = retirement.checked(replacement['lease_budget'])
    prior = dict(budget['derived_from'], sha256='0' * 64)
    rebind_budget(bound_request, derived_from=prior)
    with pytest.raises(retirement.Blocked, match='actual_generic_R131'):
        retirement.validate_bindings(*authorize(bound_request))


def test_generic_lease_bytes_cannot_change_behind_readiness(bound_request):
    replacement = retirement.checked(bound_request['request']['replacement'])
    budget = retirement.checked(replacement['lease_budget'])
    update_ref(budget['derived_from'], lease_extended=True)
    with pytest.raises(retirement.Blocked, match='bound_file_changed'):
        retirement.validate_bindings(*authorize(bound_request))


@pytest.mark.parametrize('which', ['initial', 'parented_learning', 'parented_frozen', 'unparented_learning'])
def test_initialize_rejects_precreated_output_roots(bound_request, which):
    replacement = retirement.checked(bound_request['request']['replacement'])
    cohort = retirement.checked(replacement['cohort'])
    root = Path(cohort['initial_directory'] if which == 'initial' else cohort['members'][which]['root'])
    root.mkdir()
    with pytest.raises(retirement.Blocked, match='fresh_phase_output_already_exists'):
        retirement.validate_bindings(*authorize(bound_request))


def test_missing_output_must_still_be_absent_at_later_signal_check(bound_request):
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    Path(request['_absent_outputs'][0]).mkdir()
    with pytest.raises(retirement.Blocked, match='fresh_phase_output_already_exists'):
        retirement.remaining(request, permission)


@pytest.mark.parametrize('physical', [3, 4])
def test_only_designated_0_may_initialize(bound_request, physical):
    set_phase(bound_request, 'initialize', physical)
    with pytest.raises(retirement.Blocked, match='designated_0_initialize_only'):
        retirement.validate_bindings(*authorize(bound_request))


def test_GO_is_bound_to_phase_not_just_target(bound_request):
    request_ref, go_ref = authorize(bound_request)
    with pytest.raises(retirement.Blocked, match='Main_later_exact_GO'):
        retirement.validate_bindings(request_ref, update_ref(go_ref, replacement_phase='run'))


def test_selected_config_cannot_dispatch_run_in_initialize_phase(bound_request):
    request = bound_request['request']
    replacement = retirement.checked(request['replacement'])
    request['replacement'] = update_ref(request['replacement'], config=update_ref(replacement['config'], phase='run'))
    with pytest.raises(retirement.Blocked, match='selected_phase_config_binding'):
        retirement.validate_bindings(*authorize(bound_request))


def test_fresh_admission_is_mandatory_even_for_initialize(bound_request):
    request = bound_request['request']
    request['replacement'] = update_ref(request['replacement'], post_exit_fresh_admission_required=False)
    with pytest.raises(retirement.Blocked, match='selected_phase_code_readiness'):
        retirement.validate_bindings(*authorize(bound_request))


def test_run_cannot_bootstrap_without_actual_initialization(bound_request):
    set_phase(bound_request, 'run', 4)
    with pytest.raises(retirement.Blocked, match='bound_common_initialization_required'):
        retirement.validate_bindings(*authorize(bound_request))


def test_later_run_allows_other_branch_to_be_live_but_selected_root_must_be_absent(bound_request):
    set_phase(bound_request, 'run', 4)
    initial = saved_initial(bound_request)
    replacement = retirement.checked(bound_request['request']['replacement'])
    cohort = retirement.checked(replacement['cohort'])
    Path(cohort['members']['parented_learning']['root']).mkdir()
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    assert initial.exists()
    assert request['_absent_outputs'] == [cohort['members']['parented_frozen']['root'],
        retirement.checked(replacement['config'])['attempt_dir']]
    assert not Path(request['_absent_outputs'][0]).exists()


def test_initialize_cannot_reuse_an_existing_initialization_receipt(bound_request):
    saved_initial(bound_request)
    with pytest.raises(retirement.Blocked, match='initialize_does_not_adopt'):
        retirement.validate_bindings(*authorize(bound_request))


def test_run_requires_common_initial_hash_binding_not_just_existing_file(bound_request):
    set_phase(bound_request, 'run', 4)
    initial = saved_initial(bound_request)
    put(initial / 'COMMIT.json', dict(optimizer_steps=1))
    with pytest.raises(retirement.Blocked, match='run_requires_actual_common_initial_checkpoint'):
        retirement.validate_bindings(*authorize(bound_request))


def test_run_capacity_proof_must_preserve_initial_state(bound_request):
    set_phase(bound_request, 'run', 4)
    saved_initial(bound_request)
    request = bound_request['request']
    replacement = retirement.checked(request['replacement'])
    initialized = retirement.checked(replacement['initialization'])
    validation = initialized['initialization_validation']
    proof_ref = update_ref({key: validation[key] for key in ('path', 'sha256')}, state_restored=False)
    initialized_ref = update_ref(replacement['initialization'], initialization_validation=dict(validation, **proof_ref))
    request['replacement'] = update_ref(request['replacement'], initialization=initialized_ref)
    with pytest.raises(retirement.Blocked, match='run_requires_restored_common_initial_state'):
        retirement.validate_bindings(*authorize(bound_request))


def test_new_schema_rejects_ambiguous_legacy_readiness(bound_request):
    bound_request['request']['schema'] = 'R151_NODE5_RETIRE_REQUEST_V1'
    with pytest.raises(retirement.Blocked, match='exact_request_scope'):
        retirement.validate_bindings(*authorize(bound_request))


def test_preused_phase_attempt_blocks_before_donor_arming(bound_request):
    replacement = retirement.checked(bound_request['request']['replacement'])
    attempt = Path(retirement.checked(replacement['config'])['attempt_dir'])
    attempt.mkdir()
    with pytest.raises(retirement.Blocked, match='fresh_phase_output_already_exists'):
        retirement.validate_bindings(*authorize(bound_request))
    assert not Path(bound_request['request']['stage']).exists()


@pytest.mark.parametrize('change', [dict(authorized=False), dict(published_by='watcher'),
    dict(physical=4), dict(physical=False), dict(launch_authorized=True), dict(action='launch'),
    dict(replacement=None), dict(request=None), dict(actor={})])
def test_GO_must_join_exact_scope_bytes_and_ready_replacement(bound_request, change):
    request_ref, go_ref = authorize(bound_request)
    go_ref = update_ref(go_ref, **change)
    with pytest.raises(retirement.Blocked, match='Main_later_exact_GO'):
        retirement.validate_bindings(request_ref, go_ref)


@pytest.mark.parametrize('change', [dict(expires_unix=NOW), dict(expires_unix=retirement.HARD_END + 1),
    dict(not_before_unix=NOW + 1), dict(expires_unix='forever')])
def test_GO_time_bounds(bound_request, change):
    request_ref, go_ref = authorize(bound_request)
    with pytest.raises(retirement.Blocked):
        retirement.validate_bindings(request_ref, update_ref(go_ref, **change))


@pytest.mark.parametrize('key,value', [('pause_seconds', 31), ('exit_seconds', 11),
    ('wait_seconds', 121), ('wait_seconds', False), ('remaining_seconds', 0)])
def test_operator_is_bounded(bound_request, key, value):
    bound_request['request'][key] = value
    with pytest.raises(retirement.Blocked, match='bounded_request_times'):
        retirement.validate_bindings(*authorize(bound_request))


def test_GO_bytes_cannot_be_changed_after_binding(bound_request):
    request_ref, go_ref = authorize(bound_request)
    update_ref(go_ref, authorized=False)
    with pytest.raises(retirement.Blocked, match='bound_file_changed'):
        retirement.validate_bindings(request_ref, go_ref)


def test_source_bytes_cannot_be_changed_after_CPU_gate(bound_request):
    source = next(iter(bound_request['request']['source_pins']))
    Path(source).write_text('CHANGED\n')
    with pytest.raises(retirement.Blocked, match='bound_file_changed'):
        retirement.validate_bindings(*authorize(bound_request))


def test_operator_helper_pins_cannot_be_omitted(bound_request):
    del bound_request['request']['source_pins'][str(Path(retirement.route.__file__).resolve())]
    with pytest.raises(retirement.Blocked, match='operator_and_helpers'):
        retirement.validate_bindings(*authorize(bound_request))


def test_tests_bind_source_bytes_not_only_passed_boolean(bound_request):
    request = bound_request['request']
    request['cpu_tests'] = update_ref(request['cpu_tests'], source_pins={})
    with pytest.raises(retirement.Blocked, match='CPU_gate'):
        retirement.validate_bindings(*authorize(bound_request))


@pytest.mark.parametrize('change', [dict(status='PLANNED'), dict(resume=True), dict(new_matched_life=False),
    dict(old_artifacts_untouched=False), dict(blockers=['not staged']), dict(physicals=[0, 3, 5]),
    dict(observed_unix=NOW - 121), dict(observed_unix=NOW + 1), dict(hard_end_unix=retirement.COHORT_HARD_END + 1)])
def test_all_replacements_must_really_be_bound_ready_NEW_lives(bound_request, change):
    request = bound_request['request']
    request['replacement'] = update_ref(request['replacement'], **change)
    with pytest.raises(retirement.Blocked):
        retirement.validate_bindings(*authorize(bound_request))


def test_three_plans_required_before_any_arm_without_requiring_free_donors(bound_request):
    request = bound_request['request']
    replacement = retirement.checked(request['replacement'])
    plans = dict(replacement['plans'])
    del plans['unparented_learning']
    request['replacement'] = update_ref(request['replacement'], plans=plans)
    with pytest.raises(retirement.Blocked, match='all_three'):
        retirement.validate_bindings(*authorize(bound_request))
    assert not Path(request['stage']).exists()


def test_replacement_cannot_relabel_old_root_as_new(bound_request, route_root):
    request = bound_request['request']
    replacement = retirement.checked(request['replacement'])
    old = retirement.checked(replacement['plans']['parented_learning'])
    old['root'] = str(route_root)
    replacement['plans']['parented_learning'] = put(Path(replacement['plans']['parented_learning']['path']), old)
    request['replacement'] = update_ref(request['replacement'], plans=replacement['plans'])
    with pytest.raises(retirement.Blocked, match='never_reuses_old'):
        retirement.validate_bindings(*authorize(bound_request))


def test_replacement_readiness_expires_while_waiting(bound_request, monkeypatch):
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    permission['expires_unix'] = NOW + 200
    monkeypatch.setattr(retirement.time, 'time', lambda: NOW + 121)
    with pytest.raises(retirement.Blocked, match='replacement_readiness_stale'):
        retirement.remaining(request, permission)


def test_replacement_shorter_window_rechecked(bound_request, monkeypatch):
    request, permission, stamps = retirement.validate_bindings(*authorize(bound_request))
    request['_replacement_wall'] = NOW + 35
    monkeypatch.setattr(retirement.time, 'time', lambda: NOW + 5)
    with pytest.raises(retirement.Blocked, match='replacement_window_exhausted'):
        retirement.remaining(request, permission)


def test_never_overwrites_or_retries_attempt(bound_request):
    Path(bound_request['request']['stage']).mkdir()
    with pytest.raises(retirement.Blocked, match='one_attempt'):
        retirement.validate_bindings(*authorize(bound_request))


def test_complete_route_snapshot_reuses_saved_state_and_preserves_failed_history(route_root):
    candidate = retirement.prepare_boundary(0)
    assert candidate['cycle'] == 1
    assert candidate['snapshot']['optimizer_rng']['path'].endswith('optimizer_rng.pt')
    assert candidate['snapshot']['logical_life_reset'] is False
    assert str(route_root / 'historical_failed/CRASH.json') in candidate['inventory']
    assert str(route_root / 'historical_failed/PENDING.json') in candidate['inventory']
    assert any(path.endswith('/adapter.bin') for path in candidate['preserved_stamps'])


def test_never_reads_readout_COMPLETE_or_raw_payload(route_root, monkeypatch):
    original = retirement.read
    def safe_read(path):
        assert not (Path(path).parent.name.startswith('readout_') and Path(path).name == 'COMPLETE.json')
        return original(path)
    monkeypatch.setattr(retirement, 'read', safe_read)
    candidate = retirement.prepare_boundary(0)
    assert 'MUST_NOT_READ_OR_RETURN' not in json.dumps(candidate)


@pytest.mark.parametrize('change', [dict(status='CRASHED_READOUT_CONTINUE_LIFE'),
    dict(status='READOUT_WALL_CONTINUE_LIFE'), dict(returncode=1), dict(returncode=False), dict(finished_unix=None)])
def test_failed_or_incomplete_readouts_block(route_root, change):
    path = route_root / 'open_readouts/readout_0001/PROCESS_RESULT.json'
    update_ref(retirement.reference(path), **change)
    with pytest.raises(retirement.Blocked, match='readout_failed'):
        retirement.prepare_boundary(0)


def test_live_or_reused_readout_pid_blocks(route_root):
    path = route_root / 'readout_0001/LAUNCH.json'
    update_ref(retirement.reference(path), pid=os.getpid())
    with pytest.raises(retirement.Blocked, match='readout_pid_not_reaped'):
        retirement.prepare_boundary(0)


def test_readout_checkpoint_join_blocks_wrong_sleep(route_root):
    path = route_root / 'readout_0001/LAUNCH.json'
    update_ref(retirement.reference(path), checkpoint='wrong')
    with pytest.raises(retirement.Blocked, match='readout_checkpoint_join'):
        retirement.prepare_boundary(0)


def test_readout_metadata_change_cannot_be_accepted_as_new_guard_stamp(route_root, monkeypatch):
    original = retirement.read
    path = route_root / 'readout_0001/PROCESS_RESULT.json'
    def changing_read(actual):
        value = original(actual)
        if Path(actual) == path:
            put(path, dict(status='CRASHED', returncode=1, finished_unix=NOW))
        return value
    monkeypatch.setattr(retirement, 'read', changing_read)
    with pytest.raises(retirement.Blocked, match='prepared_evidence_changed'):
        retirement.route_boundary(route_root)


@pytest.mark.parametrize('row', [dict(kind='NATIVE', cycle=2), dict(kind='PARENT', cycle=2),
    dict(kind='NATIVE', sleep=2, phase='readout')])
def test_new_native_parent_or_readout_charge_blocks(route_root, row):
    with (route_root / 'RESERVATIONS.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    with pytest.raises(retirement.Blocked, match='new_charge'):
        retirement.prepare_boundary(0)


def test_no_waiting_for_COMPLETE_while_holding_ledger_lock(route_root):
    put(route_root / 'cycle_0002/SLEEP.json', dict(sleeps=2))
    with pytest.raises(retirement.Blocked, match='cycle_not_complete'):
        retirement.prepare_boundary(0)


def test_original_snapshot_rejects_optimizer_corruption(route_root):
    (route_root / 'cycle_0001/checkpoint/optimizer_rng.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='exact_optimizer_rng'):
        retirement.prepare_boundary(0)


def test_original_snapshot_rejects_unsaved_parent_context(route_root):
    put(route_root / 'R121_PARENT_DELIVERY/new.applied.json', dict(id='new', status='COMPLETE', parent_text='TRAIN'))
    with pytest.raises(ValueError, match='unrecorded_parent_context'):
        retirement.prepare_boundary(0)


def test_ledger_replacement_cannot_change_lock_inode(route_root):
    candidate = retirement.prepare_boundary(0)
    ledger = Path(candidate['ledger'])
    ledger.rename(route_root / 'old-ledger-preserved')
    ledger.write_text('')
    with pytest.raises(retirement.Blocked, match='ledger_inode_replaced'):
        with retirement.ledger_lock(candidate):
            pytest.fail('replaced ledger must not be locked as original')


def test_ledger_lock_is_nonblocking(route_root):
    candidate = retirement.prepare_boundary(0)
    with retirement.ledger_lock(candidate):
        with pytest.raises(BlockingIOError):
            with retirement.ledger_lock(candidate):
                pytest.fail('must never wait behind native ledger owner')


def test_inventory_protects_failed_artifacts_from_truncation(route_root):
    before = retirement.inventory(route_root)
    (route_root / 'historical_failed/CRASH.json').write_text('')
    with pytest.raises(retirement.Blocked, match='truncated'):
        retirement.preserved_inventory(before)


@pytest.fixture
def fake_runtime(monkeypatch):
    runtime = dict(signals=[], descriptors=[], paused=False, drift=False, lock_depth=0)
    monkeypatch.setattr(retirement, 'host_check', lambda: None)
    monkeypatch.setattr(retirement, 'gpu_check', lambda physical, **kwargs: None)
    monkeypatch.setattr(retirement, 'identity', lambda pid: retirement.expected_actor(
        next(physical for physical, lane in retirement.TARGETS.items() if lane['pid'] == pid)))
    def actor_check(physical, stopped=False):
        assert runtime['paused'] == stopped
        if runtime['drift']:
            raise retirement.Blocked('exact_actor_identity_changed')
        return retirement.expected_actor(physical)
    def send(descriptor, physical, signum):
        assert descriptor == 987654
        assert physical == 0
        if runtime['drift']:
            raise retirement.Blocked('identity_before_pidfd_signal')
        runtime['signals'].append(signum)
        if signum == signal.SIGSTOP:
            runtime['paused'] = True
        if signum == signal.SIGCONT:
            runtime['paused'] = False
    def pidfd_open(pid):
        assert pid == retirement.expected_actor(0)['pid']
        runtime['descriptors'].append(pid)
        return 987654
    actual_close = retirement.os.close
    monkeypatch.setattr(retirement, 'actor_check', actor_check)
    monkeypatch.setattr(retirement, 'send', send)
    monkeypatch.setattr(retirement, 'task_states', lambda pid: ['T' if runtime['paused'] else 'S'])
    monkeypatch.setattr(retirement.os, 'pidfd_open', pidfd_open)
    monkeypatch.setattr(retirement.os, 'close', lambda descriptor: None if descriptor == 987654 else actual_close(descriptor))
    monkeypatch.setattr(retirement.select, 'select', lambda *args: ([987654], [], []))
    original_lock = retirement.ledger_lock
    @contextmanager
    def tracked_lock(candidate):
        with original_lock(candidate):
            runtime['lock_depth'] += 1
            try:
                yield
            finally:
                runtime['lock_depth'] -= 1
    monkeypatch.setattr(retirement, 'ledger_lock', tracked_lock)
    for name in ('sha', 'inventory', 'preserved_inventory', 'prepare_boundary', 'write'):
        original = getattr(retirement, name)
        def outside_lock(*args, _original=original, **kwargs):
            assert runtime['lock_depth'] == 0, 'expensive IO inside native ledger lock'
            return _original(*args, **kwargs)
        monkeypatch.setattr(retirement, name, outside_lock)
    return runtime


def test_full_operator_source_snapshot_NO_actual_signals_or_launch(bound_request, fake_runtime, route_root):
    old_files = {str(path): path.read_bytes() for path in route_root.rglob('*') if path.is_file()}
    result = retirement.retire(*authorize(bound_request))
    assert result['status'] == 'RELEASED_OLD_EPISODIC_ACTOR'
    assert result['launch_authorized'] is False
    assert fake_runtime['signals'] == [signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT]
    assert fake_runtime['paused'] is False
    assert all(Path(path).read_bytes() == value for path, value in old_files.items())
    stage = Path(bound_request['request']['stage'])
    assert (stage / 'ARMED.json').exists() and (stage / 'BOUNDARY.json').exists()
    assert all((stage / 'sources' / digest).is_file() for digest in bound_request['request']['source_pins'].values())
    assert 'TRAIN response' not in json.dumps(result)


def test_bad_GO_cannot_create_stage_or_arm(bound_request, fake_runtime):
    request_ref, go_ref = authorize(bound_request)
    with pytest.raises(retirement.Blocked):
        retirement.retire(request_ref, update_ref(go_ref, authorized=False))
    assert fake_runtime['signals'] == []
    assert not Path(bound_request['request']['stage']).exists()


def test_identity_changed_after_pidfd_open_blocks_signals(bound_request, fake_runtime, monkeypatch):
    def changed(pid):
        fake_runtime['drift'] = True
        return 987654
    monkeypatch.setattr(retirement.os, 'pidfd_open', changed)
    with pytest.raises(retirement.Blocked, match='identity_changed'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == []


def test_new_charge_between_snapshot_and_lock_blocks_without_STOP(bound_request, fake_runtime, monkeypatch, route_root):
    original_open = retirement.os.pidfd_open
    def charge(pid):
        with (route_root / 'RESERVATIONS.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(kind='NATIVE', cycle=2)) + '\n')
        return original_open(pid)
    monkeypatch.setattr(retirement.os, 'pidfd_open', charge)
    with pytest.raises(retirement.Blocked, match='prepared_evidence_changed'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == []


def test_after_STOP_failure_resumes_only_same_actor(bound_request, fake_runtime, monkeypatch):
    original = retirement.actor_check
    def fail(physical, stopped=False):
        if stopped:
            raise retirement.Blocked('injected_post_stop_failure')
        return original(physical, stopped=stopped)
    monkeypatch.setattr(retirement, 'actor_check', fail)
    with pytest.raises(retirement.Blocked, match='injected_post_stop'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == [signal.SIGSTOP, signal.SIGCONT]
    assert fake_runtime['paused'] is False
    stage = Path(bound_request['request']['stage'])
    assert (stage / 'BLOCKED.json').exists() and not (stage / 'RELEASED.json').exists()


def test_TERM_timeout_never_escalates_or_retries(bound_request, fake_runtime, monkeypatch):
    monkeypatch.setattr(retirement.select, 'select', lambda *args: ([], [], []))
    with pytest.raises(retirement.Blocked, match='TERM_sent_exit_unconfirmed'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == [signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT]
    disposition = retirement.read(Path(bound_request['request']['stage']) / 'SIGNAL_DISPOSITION.json')
    assert disposition['term_sent'] is True and disposition['retry_authorized'] is False


def test_pidfd_send_rejects_every_broad_or_forceful_signal(monkeypatch):
    signals = []
    monkeypatch.setattr(retirement, 'identity', lambda pid: retirement.expected_actor(0))
    monkeypatch.setattr(retirement.signal, 'pidfd_send_signal', lambda *args: signals.append(args))
    with pytest.raises(retirement.Blocked, match='narrow_stop_only'):
        retirement.send(123, 0, signal.SIGKILL)
    assert signals == []


def test_pidfd_send_rechecks_exact_identity(monkeypatch):
    monkeypatch.setattr(retirement, 'identity', lambda pid: dict(retirement.expected_actor(0), start_ticks='reused'))
    with pytest.raises(retirement.Blocked, match='identity_before_pidfd'):
        retirement.send(123, 0, signal.SIGTERM)


def test_own_pause_can_be_restored_after_parent_exits_but_never_retired(monkeypatch):
    signals = []
    monkeypatch.setattr(retirement, 'identity', lambda pid: dict(retirement.expected_actor(0), ppid=1))
    monkeypatch.setattr(retirement.signal, 'pidfd_send_signal', lambda descriptor, signum: signals.append(signum))
    with pytest.raises(retirement.Blocked, match='identity_before_pidfd'):
        retirement.send(123, 0, signal.SIGTERM)
    retirement.send(123, 0, signal.SIGCONT)
    assert signals == [signal.SIGCONT]


def test_slow_snapshot_watchdog_restores_actor_without_ledger_lock(bound_request, fake_runtime, monkeypatch):
    bound_request['request']['pause_seconds'] = .02
    original = retirement.prepare_boundary
    def slow(physical):
        assert fake_runtime['paused'] and fake_runtime['lock_depth'] == 0
        time.sleep(.08)
        assert not fake_runtime['paused']
        return original(physical)
    monkeypatch.setattr(retirement, 'prepare_boundary', slow)
    with pytest.raises(retirement.Blocked, match='pause_budget_expired'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == [signal.SIGSTOP, signal.SIGCONT]
    disposition = retirement.read(Path(bound_request['request']['stage']) / 'SIGNAL_DISPOSITION.json')
    assert disposition['watchdog_expired'] is True and disposition['term_sent'] is False


def test_snapshot_failure_after_pause_does_not_leave_actor_stopped(bound_request, fake_runtime, monkeypatch):
    def broken(physical):
        assert fake_runtime['paused'] and fake_runtime['lock_depth'] == 0
        raise ValueError('invalid_saved_context')
    monkeypatch.setattr(retirement, 'prepare_boundary', broken)
    with pytest.raises(ValueError, match='invalid_saved_context'):
        retirement.retire(*authorize(bound_request))
    assert fake_runtime['signals'] == [signal.SIGSTOP, signal.SIGCONT]


def test_cpu_snapshot_checks_are_not_hidden_in_lock_function():
    source = inspect.getsource(retirement.ledger_lock)
    assert 'snapshot(' not in source and 'time.sleep' not in source
    source = Path(retirement.__file__).read_text()
    assert 'os.kill(' not in source and 'killpg' not in source and 'shutil.rmtree' not in source
    assert 'subprocess.Popen' not in source


def test_F4_limitation_not_rng_veto_and_timer_cannot_be_waived(monkeypatch):
    monkeypatch.setattr(retirement, 'host_check', lambda: None)
    monkeypatch.setattr(retirement, 'actor_check', lambda physical: None)
    monkeypatch.setattr(retirement, 'gpu_check', lambda physical: None)
    monkeypatch.setattr(retirement, 'f4_boundary', lambda root: dict(cycle=282, sampling_rng_captured=False,
        exact_continuation_possible=False))
    monkeypatch.setattr(retirement, 'timer_metadata', lambda: dict(exact_controller_present=True))
    result = retirement.inspect_lane(3)
    assert 'saved_boundary_not_verified' not in result['blockers']
    assert 'F4_timer_and_phase_process_custody_not_proven' in result['blockers']
    assert not any('RNG' in blocker or 'rng' in blocker for blocker in result['blockers'])
    with pytest.raises(retirement.Blocked, match='custody_not_proven'):
        retirement.prepare_boundary(3)


def test_F4_GO_cannot_waive_unproven_timer(bound_request, fake_runtime, monkeypatch):
    request = deepcopy(bound_request['request'])
    request['physical'], request['actor'] = 3, retirement.expected_actor(3)
    monkeypatch.setattr(retirement, 'validate_bindings', lambda *args: (request, {}, {}))
    monkeypatch.setattr(retirement, 'timer_metadata', lambda: dict(exact_controller_present=True))
    with pytest.raises(retirement.Blocked, match='custody_not_proven'):
        retirement.retire({}, {})
    assert fake_runtime['signals'] == []
    assert not Path(request['stage']).exists()


@pytest.fixture
def f4_root(tmp_path, monkeypatch):
    root = tmp_path / 'F4'
    carry = dict(TRAIN='private carry')
    put(root / 'CARRY.json', carry)
    put(root / 'cycles/0113/TRAIN_COMPLETE.json', dict(outcomes=[{}, {}], optimizer_steps=0, carry=carry))
    failed = root / 'calls/N04456.json'
    failed_ref = put(failed, dict(status='STARTED'))
    put(root / 'r140_continuation_v1/FAILED_PREDISPATCH.json', dict(failed_call=failed_ref,
        status='FAILED_PREDISPATCH_CONTEXT_OVERFLOW'))
    put(root / 'calls/N04457.json', dict(status='COMPLETE'))
    rows = [dict(kind='NATIVE', number=4456, cycle=112, split='TRAIN', attached_readout=False),
        dict(kind='NATIVE', number=4457, cycle=113, split='TRAIN', attached_readout=False)]
    (root / 'LEDGER.jsonl').write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
    adapter = root / 'ancestor_adapter'
    adapter.mkdir()
    (adapter / 'adapter.bin').write_bytes(b'frozen')
    checkpoint = root / 'ancestral_checkpoint/CHECKPOINT.json'
    checkpoint_ref = put(checkpoint, dict(adapter=dict(path=str(adapter),
        files=[['adapter.bin', retirement.sha(adapter / 'adapter.bin')]])))
    monkeypatch.setattr(retirement, 'F4_CHECKPOINT', checkpoint)
    monkeypatch.setattr(retirement.grid, 'FAILED_SHA', failed_ref['sha256'])
    monkeypatch.setattr(retirement.grid, 'OUTPUT', root / 'r140_continuation_v1')
    monkeypatch.setattr(retirement, 'required_pins', lambda physical: {str(checkpoint): checkpoint_ref['sha256']})
    return root


def test_F4_actual_completed_boundary_does_not_require_nonexistent_current_RNG(f4_root):
    boundary = retirement.f4_boundary(f4_root)
    assert boundary['cycle'] == 113
    assert boundary['sampling_rng_captured'] is False
    assert boundary['exact_continuation_possible'] is False
    assert boundary['retired_predispatch_charges'] == [4456]
    assert 'private carry' not in json.dumps(boundary)


def test_F4_failed_historical_charge_cannot_be_reset(f4_root):
    put(f4_root / 'calls/N04456.json', dict(status='COMPLETE'))
    with pytest.raises(retirement.Blocked, match='historical_failed_charge_changed'):
        retirement.f4_boundary(f4_root)


def test_F4_two_completed_episodes_and_carry_required(f4_root):
    put(f4_root / 'CARRY.json', dict(other='not the completed carry'))
    with pytest.raises(ValueError, match='two_episodes_durable_carry'):
        retirement.f4_boundary(f4_root)


def test_F4_new_charge_invalidates_completed_boundary(f4_root):
    with (f4_root / 'LEDGER.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(kind='NATIVE', number=4458, cycle=114)) + '\n')
    with pytest.raises(FileNotFoundError):
        retirement.f4_boundary(f4_root)


def test_F4_inflight_native_call_rejected(f4_root):
    put(f4_root / 'calls/N04457.json', dict(status='STARTED'))
    with pytest.raises(ValueError, match='no_unfinished_model_input'):
        retirement.f4_boundary(f4_root)


def test_metadata_duplicate_keys_and_nan_rejected(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{"authorized": false, "authorized": true}')
    with pytest.raises(retirement.Blocked, match='duplicate_metadata_key'):
        retirement.read(path)
    path.write_text('{"expires": NaN}')
    with pytest.raises(retirement.Blocked, match='nonfinite_metadata'):
        retirement.read(path)


def test_exclusive_receipts_preserve_existing_bytes(tmp_path):
    path = tmp_path / 'receipt.json'
    retirement.write(path, dict(first=True))
    with pytest.raises(FileExistsError):
        retirement.write(path, dict(first=False))
    assert retirement.read(path) == dict(first=True)


def test_CLI_contract_is_local_and_retire_requires_explicit_GO():
    command = [sys.executable, '-B', '-m', 'gpu.orch_r151_node5_retire']
    result = subprocess.run(command + ['contract', '--physical', '3'], text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)['Main_later_exact_GO_required'] is True
    result = subprocess.run(command + ['retire'], text=True, capture_output=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)['reason'] == 'exact_request_and_GO_bytes_required'
