"""Node4-only local parent configuration tests; no provider or node access."""

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from gpu import orch_r158_matched_parents as setup
from organism_v6.orch_r125_plain_context import VERSION
from test_orch_r125_continual_native import make_plan


REPOSITORY = Path(__file__).resolve().parents[1]


def save(path, document):
    path.write_text(json.dumps(document, sort_keys=True))
    return path


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(setup.parent.time, 'time', lambda: setup.node4.WALL-7200)
    for module, name in ((setup.parent, 'remote'), (setup.parent, 'strong'), (setup.parent, 'serve'),
                         (setup.previous, 'build_bundle'), (setup.node4, 'prepare'), (setup.node4, 'execute')):
        monkeypatch.setattr(module, name, Mock(side_effect=AssertionError('execution forbidden')))
    monkeypatch.setattr('subprocess.run', Mock(side_effect=AssertionError('subprocess forbidden')))
    root = setup.node4.BASE/'orch_r158_matched_node4_cpu_fixture'
    common = make_plan(root)
    common.update(context_limit=16384, segment_tokens=512, hard_end_unix=setup.node4.WALL,
        lease_end_unix=setup.LEASE_END, startup_context=None, presentation_version=VERSION,
        presleep_variant='free_distillation', readout_revision=1,
        initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
    plans = {arm: dict(deepcopy(common), root=str(root/arm), matched_arm=arm,
        physical=physical, gpu_uuid=setup.node4.DEVICES[physical], parent_enabled=arm != 'unparented_learning')
        for arm, physical in setup.node4.ARMS.items()}
    cohort = setup.matched.cohort_document(list(plans.values()), root/'common_initial')
    cohort_path = save(tmp_path/'COHORT.json', cohort)
    plan_paths = {}
    for arm, plan in plans.items():
        plan['matched_cohort'] = dict(path=str(root/'COHORT.json'), sha256=setup.parent.sha(cohort_path))
        plan_paths[arm] = save(tmp_path/(arm+'.PLAN.json'), plan)
    programme, principles = tmp_path/'programme.md', tmp_path/'principles.md'
    programme.write_text('Attend to actual TRAIN activity without hidden answers.')
    principles.write_text('Ask useful questions; leave the learner free to investigate.')
    template = dict(schema='R133_PROGRAMME_PARENT_V1', programme='raw_parented',
        programme_path=str(programme), programme_sha256=setup.parent.sha(programme),
        principles_path=str(principles), principles_sha256=setup.parent.sha(principles),
        parent_style='Socratic', parent_reasoning_effort='low', branch='OLD_FROZEN', node='ovx3',
        cadence_label='SPARSE', cadence_responses=8, schedule_on='response', start_after_request_count=99)
    budget = dict(schema='R158_EXISTING_NODE4_COHORT_BUDGET_V1',
        derived_from=dict(path=str(setup.node4.LEASE_PATH), sha256=setup.node4.LEASE_SHA256),
        hard_end_unix=setup.node4.WALL, lease_end_unix=setup.LEASE_END, safety_margin_seconds=21600,
        lease_extended=False, existing_life_wall_changed=False, purchase_performed=False,
        physical_devices=[5, 6, 7], host_sha256=setup.node4.HOST_SHA256)
    return dict(cohort=cohort_path, cohort_sha256=setup.parent.sha(cohort_path), plans=plan_paths,
        template=save(tmp_path/'TEMPLATE.json', template), budget=save(tmp_path/'BUDGET.json', budget),
        output=tmp_path/'parents', programme=programme, principles=principles)


def prepare(fixture):
    return setup.prepare(REPOSITORY, fixture['cohort'], fixture['cohort_sha256'], fixture['plans'],
        fixture['template'], fixture['budget'], setup.parent.sha(fixture['budget']), fixture['output'])


def revise_plans(fixture, change):
    plans = {arm: json.loads(path.read_text()) for arm, path in fixture['plans'].items()}
    change(plans)
    initial = json.loads(fixture['cohort'].read_text())['initial_directory']
    cohort = setup.matched.cohort_document(list(plans.values()), initial)
    save(fixture['cohort'], cohort)
    fixture['cohort_sha256'] = setup.parent.sha(fixture['cohort'])
    for arm, plan in plans.items():
        plan['matched_cohort']['sha256'] = fixture['cohort_sha256']
        save(fixture['plans'][arm], plan)


def test_two_identical_node4_persistent_parents_and_no_third_parent(fixture):
    before = {path: path.read_bytes() for path in [fixture['cohort'], fixture['budget'], fixture['template'],
                                                *fixture['plans'].values()]}
    reference = prepare(fixture)
    assert setup.verify(reference['path'], reference['sha256'])['status'] == 'VERIFIED_CPU_ONLY_NOT_REGISTERED'
    document = setup.read_pinned(reference)
    assert document['schema'] == setup.SCHEMA
    assert document['provider_calls'] == document['GPU_calls'] == document['remote_writes'] == document['launches'] == 0
    assert document['registration']['runtime_verified'] is False
    assert document['registration']['require_admitted_births'] is True
    assert document['node_contract']['remote_identity_verified'] is False
    assert document['parent_contract']['asynchronous'] is True
    assert document['parent_contract']['parenting_success_claim'] is False
    assert 'gpu/ovx3_ssh.sh' not in document['source_pins']
    assert document['source_pins'][setup.WRAPPER] == dict(path=str(REPOSITORY/setup.WRAPPER), sha256=setup.WRAPPER_SHA256)
    assert set(document['configs']) == {'parented_learning', 'parented_frozen'}
    configs = {arm: setup.read_pinned(value) for arm, value in document['configs'].items()}
    learning, frozen = configs['parented_learning'], configs['parented_frozen']
    assert {field for field in learning if learning[field] != frozen[field]} == {'root'}
    assert learning['node'] == 'a40r' and learning['branch'] == 'R158_MATCHED'
    assert learning['parent_reasoning_effort'] == 'low' and learning['parent_style'] == 'Socratic'
    assert learning['schedule_on'] == 'request' and learning['cadence_responses'] == 1
    assert learning['cadence_label'] == 'PERSISTENT' and learning['minimum_duration_seconds'] == 3600
    assert learning['poll_interval_seconds'] == 0.25
    assert learning['start_after_response_count'] == learning['start_after_request_count'] == 0
    assert learning['hard_end_unix'] == setup.node4.WALL
    state = dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=[dict(actor='child', text='What should I try?')])
    assert setup.parent.prompt(learning, state) == setup.parent.prompt(frozen, state)
    assert 'OLD_FROZEN' not in '\n'.join(setup.parent.prompt(learning, state))
    assert 'parented_learning' not in '\n'.join(setup.parent.prompt(learning, state))
    for arm, physical in setup.node4.ARMS.items():
        assert document['arms'][arm]['physical'] == physical
        assert document['arms'][arm]['gpu_uuid'] == setup.node4.DEVICES[physical]
    assert document['arms']['unparented_learning']['config_file'] is None
    assert document['arms']['unparented_learning']['parent_enabled'] is False
    assert not (fixture['output']/'unparented_learning.PARENT.json').exists()
    assert all(path.read_bytes() == original for path, original in before.items())
    assert all(path.stat().st_mode & 0o777 == 0o400 for path in fixture['output'].iterdir())
    setup.previous.build_bundle.assert_not_called()
    setup.parent.serve.assert_not_called()


@pytest.mark.parametrize('arm', setup.matched.ARMS)
@pytest.mark.parametrize('field,value', [('physical', 0), ('physical', True), ('gpu_uuid', 'GPU-foreign'),
    ('root', '/localhome/local-rohing/orch_r151_old/child')])
def test_rehashed_wrong_node_allocation_or_old_root_refused(fixture, arm, field, value):
    revise_plans(fixture, lambda plans: plans[arm].update({field: value}))
    with pytest.raises(ValueError, match='node4'):
        prepare(fixture)
    assert not fixture['output'].exists()


@pytest.mark.parametrize('field,value', [('hard_end_unix', float('inf')), ('hard_end_unix', float('nan')),
    ('hard_end_unix', setup.node4.WALL+1), ('lease_end_unix', setup.LEASE_END+1),
    ('source_root', '/localhome/local-rohing/orch_r151_old/source'), ('context_limit', 8192),
    ('segment_tokens', 16), ('initialization_validation_schema', None), ('preupdate_recovery', {})])
def test_rehashed_common_plan_contradictions_refused(fixture, field, value):
    def change(plans):
        for plan in plans.values():
            plan[field] = value
    with pytest.raises(ValueError):
        revise_plans(fixture, change)
        prepare(fixture)
    assert not fixture['output'].exists()


@pytest.mark.parametrize('field,value', [('hard_end_unix', setup.node4.WALL+1), ('hard_end_unix', float('inf')),
    ('lease_end_unix', setup.LEASE_END+1), ('safety_margin_seconds', 120), ('safety_margin_seconds', True),
    ('physical_devices', [0, 1, 2]), ('host_sha256', '0'*64), ('lease_extended', True),
    ('existing_life_wall_changed', True), ('purchase_performed', True), ('derived_from', {'sha256': '0'*64})])
def test_budget_is_exactly_node4_without_extension_even_when_rehashed(fixture, field, value):
    budget = json.loads(fixture['budget'].read_text())
    budget[field] = value
    save(fixture['budget'], budget)
    with pytest.raises(ValueError, match='node4'):
        prepare(fixture)
    assert not fixture['output'].exists()


@pytest.mark.parametrize('seconds', [3599, 3600, 3601])
def test_full_hour_must_remain_at_prepare_and_verify(fixture, monkeypatch, seconds):
    reference = prepare(fixture)
    monkeypatch.setattr(setup.parent.time, 'time', lambda: setup.node4.WALL-seconds)
    if seconds > 3600:
        assert setup.verify(reference['path'], reference['sha256'])['runtime_verified'] is False
    else:
        with pytest.raises(ValueError, match='time_for_full_persistent_segment'):
            setup.verify(reference['path'], reference['sha256'])
        fixture['output'] = fixture['output'].with_name('too_late')
        with pytest.raises(ValueError, match='time_for_full_persistent_segment'):
            prepare(fixture)


@pytest.mark.parametrize('effort', [None, 'medium', 'high', 'xhigh'])
def test_only_explicit_low_effort_is_accepted(fixture, effort):
    template = json.loads(fixture['template'].read_text())
    template['parent_reasoning_effort'] = effort
    save(fixture['template'], template)
    with pytest.raises(ValueError, match='explicit_identical_low_effort'):
        prepare(fixture)


@pytest.mark.parametrize('target', ['cohort', 'budget', 'template', 'programme', 'principles', 'config', 'plan'])
def test_verify_rejects_input_or_config_byte_drift(fixture, target):
    reference = prepare(fixture)
    path = (fixture['output']/'parented_learning.PARENT.json' if target == 'config'
            else fixture['plans']['parented_frozen'] if target == 'plan' else fixture[target])
    path.chmod(0o600)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError, match='immutable_input_pin|fixed_parent_source'):
        setup.verify(reference['path'], reference['sha256'])


@pytest.mark.parametrize('target', [setup.WRAPPER, 'gpu/orch_r133_programme_parent.py', 'gpu/orch_r158_matched_node4.py'])
def test_source_and_exact_wrapper_drift_fail_without_execution(fixture, monkeypatch, target):
    reference = prepare(fixture)
    original = setup.pin

    def changed(path):
        result = original(path)
        if Path(path) == REPOSITORY/target:
            result['sha256'] = '0'*64
        return result

    monkeypatch.setattr(setup, 'pin', changed)
    with pytest.raises(ValueError, match='exact_node4_a40r_wrapper|exact_prepared_contract'):
        setup.verify(reference['path'], reference['sha256'])


@pytest.mark.parametrize('field,value', [('node', 'ovx3'), ('branch', 'parented_frozen'),
    ('schedule_on', 'response'), ('parent_reasoning_effort', 'high'), ('cadence_responses', 2)])
def test_rehashed_parent_config_cannot_change_contract(fixture, field, value):
    reference = prepare(fixture)
    document = setup.read_pinned(reference)
    config_path = Path(document['configs']['parented_learning']['path'])
    config = setup.read_pinned(document['configs']['parented_learning'])
    config[field] = value
    config_path.chmod(0o600)
    save(config_path, config)
    document['configs']['parented_learning'] = setup.pin(config_path)
    manifest = Path(reference['path'])
    manifest.chmod(0o600)
    save(manifest, document)
    with pytest.raises(ValueError, match='exact_bound_parent_config'):
        setup.verify(manifest, setup.parent.sha(manifest))


def test_output_never_overwrites_and_unparented_config_cannot_be_added(fixture):
    reference = prepare(fixture)
    with pytest.raises(ValueError, match='new_canonical_local_output'):
        prepare(fixture)
    document = setup.read_pinned(reference)
    document['configs']['unparented_learning'] = document['configs']['parented_learning']
    manifest = Path(reference['path'])
    manifest.chmod(0o600)
    save(manifest, document)
    with pytest.raises(ValueError, match='exact_two_parent_configs'):
        setup.verify(manifest, setup.parent.sha(manifest))


def test_local_symlink_ancestors_and_evaluation_inputs_rejected(tmp_path):
    directory = tmp_path/'ordinary'
    directory.mkdir()
    path = save(directory/'input.json', {})
    link = tmp_path/'link'
    link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match='unlinked_local_input'):
        setup.pin(link/path.name)
    with pytest.raises(ValueError, match='no_evaluation_input'):
        setup.pin(tmp_path/'sealed_scores.json')


def test_expected_external_hashes_and_cohort_binding_are_required(fixture):
    with pytest.raises(ValueError, match='expected_budget_pin'):
        setup.prepare(REPOSITORY, fixture['cohort'], fixture['cohort_sha256'], fixture['plans'],
            fixture['template'], fixture['budget'], '0'*64, fixture['output'])
    path = fixture['plans']['parented_learning']
    plan = json.loads(path.read_text())
    plan['matched_cohort']['sha256'] = '0'*64
    save(path, plan)
    with pytest.raises(ValueError, match='immutable_matched_cohort'):
        prepare(fixture)


@pytest.mark.parametrize('change', ['missing_arm', 'mixed_seed', 'parent_for_unparented', 'old_cohort_root', 'runtime_cohort'])
def test_original_triplet_and_new_cohort_checks_remain_in_force(fixture, change):
    if change == 'missing_arm':
        fixture['plans'].pop('unparented_learning')
    elif change == 'old_cohort_root':
        cohort = json.loads(fixture['cohort'].read_text())
        cohort['initial_directory'] = '/localhome/local-rohing/orch_r151_old/common_initial'
        save(fixture['cohort'], cohort)
        fixture['cohort_sha256'] = setup.parent.sha(fixture['cohort'])
        for path in fixture['plans'].values():
            plan = json.loads(path.read_text())
            plan['matched_cohort']['sha256'] = fixture['cohort_sha256']
            save(path, plan)
    else:
        arm = 'unparented_learning' if change == 'parent_for_unparented' else 'parented_frozen'
        path = fixture['plans'][arm]
        plan = json.loads(path.read_text())
        if change == 'mixed_seed':
            plan['seed'] += 1
        elif change == 'parent_for_unparented':
            plan['parent_enabled'] = True
        else:
            plan['matched_cohort']['path'] = '/localhome/local-rohing/orch_r151_old/COHORT.json'
        save(path, plan)
    with pytest.raises(ValueError):
        prepare(fixture)
    assert not fixture['output'].exists()


def test_config_location_and_manifest_hash_are_bound(fixture):
    reference = prepare(fixture)
    with pytest.raises(ValueError, match='expected_manifest_pin'):
        setup.verify(reference['path'], '0'*64)
    document = setup.read_pinned(reference)
    config = setup.read_pinned(document['configs']['parented_learning'])
    elsewhere = save(fixture['output'].parent/'elsewhere.json', config)
    document['configs']['parented_learning'] = setup.pin(elsewhere)
    manifest = Path(reference['path'])
    manifest.chmod(0o600)
    save(manifest, document)
    with pytest.raises(ValueError, match='bound_config_location'):
        setup.verify(manifest, setup.parent.sha(manifest))


def test_cli_prepare_verify_only_and_correct_returned_command(fixture, capsys):
    arguments = ['prepare', '--repository', str(REPOSITORY), '--cohort', str(fixture['cohort']),
        '--cohort-sha256', fixture['cohort_sha256'], '--template', str(fixture['template']),
        '--budget', str(fixture['budget']), '--budget-sha256', setup.parent.sha(fixture['budget']),
        '--output', str(fixture['output'])]
    for arm, path in fixture['plans'].items():
        arguments += ['--'+arm.replace('_', '-')+'-plan', str(path)]
    setup.main(arguments)
    reference = json.loads(capsys.readouterr().out)
    assert 'gpu.orch_r158_matched_parents verify' in reference['verify_command']
    setup.main(['verify', '--manifest', reference['path'], '--sha256', reference['sha256']])
    assert json.loads(capsys.readouterr().out)['status'] == 'VERIFIED_CPU_ONLY_NOT_REGISTERED'
    with pytest.raises(SystemExit):
        setup.main(['serve'])
