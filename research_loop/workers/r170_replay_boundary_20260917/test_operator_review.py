"""Independent bound CPU probes, not receiving-host or signal-bearing approval."""

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from unittest import mock

import pytest


REPO = Path(__file__).resolve().parents[3]
LOWER = REPO / 'gpu/orch_r144_node3_target_handoff.py'
API = REPO / 'research_loop/workers/r144_node3_target_handoff_20260916t1541z_operator5/BOUNDARY_API.py'
LOWER_SHA256 = '014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c'
API_SHA256 = 'f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60'
OPERATOR = Path(__file__).with_name('OPERATOR.py')
OPERATOR_SHA256 = 'e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f'
CREATIVE = REPO / 'gpu/orch_r133_node3_handoff.py'
CREATIVE_SHA256 = 'c249b3d8cd413267556cf200acfcaf9668f8c3096c705ea2adc40b0054b1b692'

CLI_ENTRY_HOOK = '''
import json
import os
from pathlib import Path
import sys
from types import ModuleType

def denied(*arguments, **keywords):
    raise RuntimeError('review_subprocess_must_not_perform_external_actions')

for name in ('gpu.orch_r125_continual_native', 'gpu.orch_r133_retire_old_lanes',
             'gpu.orch_r133_code_feedback_guard'):
    module = ModuleType(name)
    for attribute in ('await_startup', 'publish_launch', 'reap_owned_child'):
        setattr(module, attribute, denied)
    sys.modules[name] = module

def audit(event, arguments):
    if event in ('subprocess.Popen', 'os.kill', 'os.killpg', 'os.system',
                 'os.exec', 'os.posix_spawn', 'socket.connect'):
        denied()
    if event == 'open' and str(arguments[0]).startswith('/dev/nvidia'):
        denied()

sys.addaudithook(audit)
expected_file = os.environ['R170_REVIEW_ENTRY_FILE']
expected_function = os.environ['R170_REVIEW_ENTRY_FUNCTION']

def entered(frame, event, argument):
    if (event == 'call' and frame.f_code.co_name == expected_function
            and frame.f_code.co_filename == expected_file):
        print(json.dumps(dict(entered=expected_function, file=expected_file,
                              argv=sys.argv, pid=os.getpid())), flush=True)
        os._exit(0)
    return entered

sys.settrace(entered)
'''


def frozen_namespace(path, checksum):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == checksum
    namespace = dict(__name__='independent_frozen_lower_review', __file__=str(path))
    exec(compile(raw, str(path), 'exec'), namespace)
    return namespace


@pytest.fixture
def lower():
    return frozen_namespace(LOWER, LOWER_SHA256)


@pytest.fixture
def boundary_api():
    return frozen_namespace(API, API_SHA256)


def test_operator4_and_operator5_boundary_API_are_identical():
    previous = REPO / 'research_loop/workers/r144_node3_target_handoff_20260916t1537z_operator4/BOUNDARY_API.py'
    assert previous.read_bytes() == API.read_bytes()
    assert hashlib.sha256(API.read_bytes()).hexdigest() == API_SHA256


def test_every_frozen_function_uses_its_own_compiled_namespace(lower, boundary_api):
    for namespace in (lower, boundary_api):
        tree = ast.parse(Path(namespace['__file__']).read_bytes())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                function = namespace[node.name]
                assert function.__globals__ is namespace
                assert function.__closure__ is None
    shallow_copy = dict(lower, lane_scope=lambda plan: 'replacement')
    assert shallow_copy['old_modules'].__globals__ is lower
    assert shallow_copy['old_modules'].__globals__['lane_scope'] is not shallow_copy['lane_scope']


@pytest.mark.parametrize('failure', ['source', 'fresh_validation', 'identity', 'lock'])
def test_source_and_CPU_and_identity_precede_lock_or_pidfd(lower, failure):
    events = []
    checksum = 'a' * 64
    request = dict(operator_sha256=checksum, cpu_path='/fixture/CPU.json', cpu_sha256=checksum,
        old_config='/fixture/OLD.json', old_config_sha256=checksum, new_config_sha256=checksum,
        source_binding='/fixture/STAGED_SOURCE.json', processes=dict(actor=dict(pid=11)))
    documents = {'STAGED.json': request, 'GUARD.json': dict(plan_path='/fixture/PLAN.json'),
                 'PLAN.json': dict(source_root='/fixture/new_source')}
    helper = SimpleNamespace(read=lambda path: documents[Path(path).name], sha=lambda path: checksum)

    def check(phase, result=None):
        events.append(phase)
        if phase == failure:
            raise ValueError('review_' + phase)
        return result

    opening = mock.Mock(side_effect=lambda *args: check('lock'))
    signaler = mock.Mock(side_effect=AssertionError('no_real_signal'))
    pidfds = mock.Mock(side_effect=AssertionError('no_real_pidfd'))
    lower.update(api=lambda: helper,
        old_modules=lambda path: check('old_modules', ({}, {}, None)),
        verify_source=lambda *args: check('source'),
        validate_fresh=lambda *args: check('fresh_validation', {'status': 'PASS'}),
        old_processes=lambda *args: check('identity', request['processes']),
        os=SimpleNamespace(open=opening, pidfd_open=pidfds, O_CREAT=1, O_RDWR=2,
                           O_CLOEXEC=4, O_NOFOLLOW=8),
        signal=SimpleNamespace(pidfd_send_signal=signaler))
    with pytest.raises(ValueError, match='review_' + failure):
        lower['handoff'](Path('/fixture/control'), 30)
    expected = ['old_modules', 'source', 'fresh_validation', 'identity', 'lock']
    assert events == expected[:expected.index(failure) + 1]
    assert opening.call_count == (1 if failure == 'lock' else 0)
    pidfds.assert_not_called()
    signaler.assert_not_called()


def test_frozen_monitor_accepts_baseline_without_targeted_dose(lower, boundary_api, tmp_path):
    output = tmp_path / 'control'
    records = tmp_path / 'life/stream/records'
    output.mkdir()
    records.mkdir(parents=True)
    writer = boundary_api['write']
    policy = dict(minor=1, uid=2524, gid=2524, unit='fixture-only')
    plan_path = tmp_path / 'PLAN.json'
    writer(plan_path, dict(root=str(tmp_path / 'life'), source_root=str(tmp_path / 'source')))
    writer(output / 'GUARD.json', dict(plan_path=str(plan_path), device_containment=policy))
    writer(output / 'STAGED.json', dict(physical=1))
    writer(output / 'CONTAINMENT_VERIFIED.json', dict(policy=policy,
        denied_foreign_minors=[minor for minor in range(8) if minor != 1]))
    writer(output / 'LAUNCH.json', dict(pid=10, guard_sha256=boundary_api['sha'](output / 'GUARD.json')))
    documents = [
        ('LOADED', dict(resume=True, optimizer_steps=4000, adapter_sha256='adapter', pid=11)),
        ('TARGET_ELIGIBILITY', dict(runtime_policy=lower['POLICY'], raw_modified=False)),
        ('SLEEP_COMPLETE', dict(status='COMPLETE', cycle=41)),
    ]
    for index, (kind, document) in enumerate(documents, start=2):
        record = dict(kind=kind, document=document)
        record['sha256'] = boundary_api['digest'](record)
        writer(records / f'{index:020d}.json', record)
    actor = dict(argv=['fixture', str(output / 'GUARD.json')],
        environment=[boundary_api['ALLOCATOR']], cwd=str(tmp_path / 'source'), parent=10)
    boundary_api['identity'] = lambda pid: deepcopy(actor)
    lower['api'] = lambda: SimpleNamespace(**boundary_api)
    unlock = mock.Mock()
    result = lower['monitor'](output, dict(record_path=str(records / f'{1:020d}.json'),
        optimizer_steps=4000, adapter_state_sha256='adapter', cycle=40), unlock)
    assert result['status'] == 'TARGET_POLICY_NEW_SLEEP_COMPLETE'
    unlock.assert_called_once_with()
    assert not (tmp_path / 'life/r168_targeted_replay').exists()
    assert all('r168_targeted_replay' not in document for kind, document in documents)


def test_frozen_saved_evidence_calls_restore_experiment_and_checkpoint_verifier(boundary_api, tmp_path):
    checkpoint_directory = tmp_path / 'checkpoints/sleep_000040'
    checkpoint_directory.mkdir(parents=True)
    record_path = tmp_path / 'saved_record.json'
    bundle = dict(adapter='a' * 64, optimizer='b' * 64, rng='b' * 64)
    checkpoint = dict(checkpoint_sha256=bundle, experiment='own-experiment',
                      optimizer_steps=4000, adapter_state_sha256='adapter')
    boundary_api['write'](checkpoint_directory / 'COMMIT.json', checkpoint)
    boundary_api['write'](record_path, {})
    plan = dict(root=str(tmp_path), hard_end_unix=1000)
    saved = dict(path=str(record_path), state={'own_history': 'unchanged'}, state_sha256='state', cycle=40)
    stream = SimpleNamespace(model_state_sha256=boundary_api['digest'](bundle),
                             experiment='own-experiment', deadline_unix=1000)
    restore = mock.Mock(return_value=stream)
    experiment = mock.Mock()
    verify = mock.Mock()
    original = SimpleNamespace(native=SimpleNamespace(ContinualStream=SimpleNamespace(restore=restore),
        verify_experiment_resume=experiment, NativeChild=SimpleNamespace(verify_checkpoint=verify)))
    result = boundary_api['saved_evidence'](plan, saved, original)
    restore.assert_called_once_with(dict(state=saved['state'], sha256='state'), expected_sha256='state')
    experiment.assert_called_once_with(plan, 'own-experiment')
    verify.assert_called_once_with(checkpoint)
    assert result['bundle_sha256'] == bundle and result['optimizer_steps'] == 4000
    verify.side_effect = ValueError('review_corrupt_optimizer_rng')
    with pytest.raises(ValueError, match='review_corrupt_optimizer_rng'):
        boundary_api['saved_evidence'](plan, saved, original)


def test_frozen_resume_uses_reverse_exact_pidfds_and_tolerates_exited_process(boundary_api):
    descriptors = dict(supervisor=71, timer=72, actor=73)
    paused = list(descriptors)
    send = mock.Mock(side_effect=[ProcessLookupError(), None, None])
    boundary_api['signal'] = SimpleNamespace(pidfd_send_signal=send, SIGCONT=18)
    boundary_api['resume_paused'](paused, descriptors)
    assert [call.args for call in send.call_args_list] == [(73, 18), (72, 18), (71, 18)]
    assert paused == []


def test_inherited_nonlookup_CONT_error_interrupts_remaining_cleanup(boundary_api):
    descriptors = dict(supervisor=71, timer=72, actor=73)
    paused = list(descriptors)
    send = mock.Mock(side_effect=PermissionError('review_CONT_failure'))
    boundary_api['signal'] = SimpleNamespace(pidfd_send_signal=send, SIGCONT=18)
    with pytest.raises(PermissionError, match='review_CONT_failure'):
        boundary_api['resume_paused'](paused, descriptors)
    send.assert_called_once_with(73, 18)
    assert paused == ['supervisor', 'timer', 'actor']


@pytest.mark.parametrize('changes', [dict(clear=False), dict(clear=1), dict(scanner_euid=2524),
    dict(blocking_reasons=['foreign_fd']), dict(gpu={'uuid': 'foreign', 'index': 1}),
    dict(gpu={'uuid': 'own', 'index': 2})])
def test_frozen_admission_refuses_unclear_or_foreign_physical1(boundary_api, changes):
    report = dict(clear=True, scanner_euid=0, blocking_reasons=[], gpu=dict(uuid='own', index=1))
    with pytest.raises(ValueError, match='fresh_privileged_exact_UUID_physical_admission'):
        boundary_api['admission'](dict(report, **changes), dict(physical=1, gpu_uuid='own'))


@pytest.mark.parametrize('marker', ['LAUNCH.json', 'CONTAINED_COMMAND.json', 'ADMISSION_TIME.json'])
def test_frozen_readmission_never_accepts_past_possible_dispatch(boundary_api, tmp_path, marker):
    (tmp_path / marker).touch()
    with pytest.raises(ValueError, match='readmit_only_before_any_native_dispatch'):
        boundary_api['admission_retry_eligible'](tmp_path)


@pytest.fixture
def candidate(tmp_path):
    directory = tmp_path / 'operator'
    directory.mkdir()
    (directory / 'OPERATOR.py').write_bytes(OPERATOR.read_bytes())
    (directory / 'FAMILY.py').write_bytes(LOWER.read_bytes())
    (directory / 'BOUNDARY_API.py').write_bytes(API.read_bytes())
    operator = frozen_namespace(directory / 'OPERATOR.py', OPERATOR_SHA256)
    return operator, operator['family_namespace']()


def test_candidate_changes_only_five_declared_functions_and_one_scope_constant(candidate):
    operator, family = candidate
    expected = dict(__name__='r170_saved_boundary_family', __file__=operator['__file__'])
    exec(compile(LOWER.read_bytes(), operator['__file__'], 'exec'), expected)
    defined = [node.name for node in ast.parse(LOWER.read_bytes()).body if isinstance(node, ast.FunctionDef)]
    changed = {name for name in defined if family[name].__code__ != expected[name].__code__}
    assert changed == {'lane_scope', 'verify_source', 'old_modules', 'saved_evidence', 'validate_new'}
    for name in set(defined) - changed:
        assert family[name].__globals__ is family
        assert family[name].__closure__ is None
        assert family[name].__defaults__ == expected[name].__defaults__
        assert family[name].__kwdefaults__ == expected[name].__kwdefaults__
    for name, wrapper in [('old_modules', 'original_modules'), ('saved_evidence', 'original_saved'),
                          ('validate_new', 'original_validation')]:
        closure = dict(zip(family[name].__code__.co_freevars,
                           [cell.cell_contents for cell in family[name].__closure__]))
        assert closure[wrapper].__code__ == expected[name].__code__
        assert closure[wrapper].__globals__ is family
    for name in ('API_SHA', 'PATCH_SHA', 'HELPER_SHA', 'POLICY', 'BASE', 'PYTHON', 'GUARD_MODULE',
                 'PROGRAMMES_MODULE', 'CREATIVE_MODULE', 'OTHER_ROOTS', 'OTHER_UUIDS'):
        assert family[name] == expected[name]
    assert family['STAGED_SOURCE_ROOT'] == operator['STAGE']
    helper = family['api']()
    assert Path(helper.__file__) == Path(operator['__file__']).with_name('BOUNDARY_API.py')
    assert helper.saved_evidence.__code__.co_code == frozen_namespace(API, API_SHA256)['saved_evidence'].__code__.co_code


@pytest.mark.parametrize('ordering', [False, True])
def test_candidate_guard_exactly_equals_reviewed_driver_for_valid_refs(candidate, tmp_path, ordering):
    from gpu import orch_r168_targeted_replay_driver as driver

    operator, family = candidate
    source = (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes()
    reference = dict(path=str(tmp_path / 'EXTERNAL.json'), sha256='a' * 64)
    if ordering:
        reference = dict(reversed(list(reference.items())))
    original_reference = deepcopy(reference)
    patched = operator['patched_guard'](source, reference)
    assert patched == driver.patch_guard(source, reference)
    assert reference == original_reference
    original_tree, patched_tree = ast.parse(source), ast.parse(patched)
    original_entry = next(node for node in original_tree.body
                          if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
    patched_entry = next(node for node in patched_tree.body
                         if isinstance(node, ast.FunctionDef) and node.name == 'native_entry')
    assert ast.dump(original_entry.body[-1]) != ast.dump(patched_entry.body[-1])
    patched_entry.body[-1] = original_entry.body[-1]
    assert ast.dump(original_tree) == ast.dump(patched_tree)


@pytest.mark.xfail(strict=True, reason='candidate guard clone omits reviewed driver reference validation')
@pytest.mark.parametrize('reference', [dict(path='relative', sha256='a' * 64),
                                      dict(path='/tmp/reference', sha256='invalid')])
def test_candidate_guard_clone_also_refuses_invalid_references(candidate, reference):
    from gpu import orch_r168_targeted_replay_driver as driver

    operator, family = candidate
    source = (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes()
    with pytest.raises(ValueError):
        driver.patch_guard(source, reference)
    with pytest.raises(ValueError):
        operator['patched_guard'](source, reference)


@pytest.fixture
def source_fixture(candidate, tmp_path):
    operator, family = candidate
    old_source = tmp_path / 'old_source'
    stage = tmp_path / 'stage'
    destination = stage / 'physical1/source'
    life = tmp_path / 'life'
    (old_source / 'gpu').mkdir(parents=True)
    (destination / 'gpu').mkdir(parents=True)
    life.mkdir()
    operator.update(OLD_SOURCE=old_source, STAGE=stage, LIFE=life)
    family['STAGED_SOURCE_ROOT'] = stage

    def write(path, document):
        path.write_bytes(json.dumps(document, sort_keys=True).encode())
        return dict(path=str(path), sha256=operator['sha'](path))

    native_name = 'gpu/orch_r125_continual_native.py'
    guard_name = 'gpu/orch_r125_continual_guard.py'
    original_sources = {native_name: (REPO / 'research_loop/workers/r168_replay_candidates_20260917/NATIVE_cdb542.py').read_bytes(),
                        guard_name: (REPO / guard_name).read_bytes(), 'gpu/unchanged.py': b'UNCHANGED = True\n'}
    for name, raw in original_sources.items():
        (old_source / name).write_bytes(raw)
        (destination / name).write_bytes(raw)
    old_pins = {name: operator['sha'](old_source / name) for name in original_sources}
    for name in operator['REPLAY_PINS']:
        (destination / name).write_bytes((REPO / name).read_bytes())
    old_plan = dict(physical=1, gpu_uuid=operator['UUID'], root=str(life), source_root=str(old_source),
        hard_end_unix=10000, lease_end_unix=11000, new_presentations=16, rehearsal_presentations=1,
        anchor_lambda=0.25, presleep_variant='reread_select', context_limit=16384)
    new_plan = dict(old_plan, source_root=str(destination))
    old_plan_ref = write(tmp_path / 'OLD_PLAN.json', old_plan)
    new_plan_ref = write(tmp_path / 'NEW_PLAN.json', new_plan)
    allocation = dict(plan_sha256=old_plan_ref['sha256'], unchanged_budget=10000)
    old_allocation_ref = write(tmp_path / 'OLD_ALLOCATION.json', allocation)
    new_allocation_ref = write(tmp_path / 'NEW_ALLOCATION.json', dict(allocation, plan_sha256=new_plan_ref['sha256']))
    old_config = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=old_plan_ref['path'], plan_sha256=old_plan_ref['sha256'], source_pins=old_pins,
        attempt_dir=str(tmp_path / 'old_attempt'), resume=True, allocation_path=old_allocation_ref['path'],
        allocation_sha256=old_allocation_ref['sha256'], lease_end_unix=11000,
        device_containment=dict(minor=1, uid=2524, gid=2524, unit='old_unit'))
    new_config = dict(deepcopy(old_config), plan_path=new_plan_ref['path'], plan_sha256=new_plan_ref['sha256'],
        attempt_dir=str(tmp_path / 'new_attempt'), allocation_path=new_allocation_ref['path'],
        allocation_sha256=new_allocation_ref['sha256'],
        device_containment=dict(old_config['device_containment'], unit='new_unit'))
    selection = dict(source_cycle=40, target_cycle=41, boundary_state_sha256='state',
        boundary_ref=dict(path=str(life / 'stream/records/saved.json'), sha256='a' * 64), selected=[dict(
            segment=118, source_sha256='1d721f3be5a40bac051f0c132451d7bb1e6bec428eec63327b26f64432ae17d7',
            row_sha256='564f8a4f585ecc2eb4bfb16fb0efb390cf8014050fd761dadc93b4773ecd7e6d',
            selection_kind='OBJECT_REPLAY', extra_presentations=4)])
    stage_directory = stage / 'physical1'
    driver_binding = dict(life_root=str(life), resume=True, plan_ref=new_plan_ref,
        runtime_ref=write(stage_directory / 'RUNTIME.json', {}),
        main_go_ref=write(stage_directory / 'GO.json', {}))
    binding_path = stage_directory / 'PROPOSED_GUARD.json'

    def rebind():
        driver_binding['selection_ref'] = write(stage_directory / 'SELECTION.json', selection)
        binding_ref = write(stage_directory / 'DRIVER_BINDING.json', driver_binding)
        (destination / guard_name).write_bytes(operator['patched_guard'](original_sources[guard_name], binding_ref))
        new_config['source_pins'] = dict(old_pins, **operator['REPLAY_PINS'])
        new_config['source_pins'][guard_name] = operator['sha'](destination / guard_name)
        proposed_ref = write(binding_path, new_config)
        write(stage_directory / 'STAGED_SOURCE.json', dict(guard_sha256=proposed_ref['sha256'], driver_binding=binding_ref))

    rebind()
    return SimpleNamespace(operator=operator, family=family, old_plan=old_plan, new_plan=new_plan,
        old_config=old_config, new_config=new_config, old_source=old_source, destination=destination,
        binding_path=binding_path, selection=selection, driver_binding=driver_binding, rebind=rebind)


def verify_fixture(fixture):
    return fixture.operator['verify_source'](fixture.family, fixture.binding_path,
        fixture.old_config, fixture.old_plan, fixture.new_config, fixture.new_plan)


def test_candidate_exact_source_delta_preserves_all_unmodified_files(source_fixture):
    assert verify_fixture(source_fixture) is None
    assert source_fixture.operator['sha'](source_fixture.destination / 'gpu/orch_r125_continual_native.py') == source_fixture.operator['NATIVE_SHA']


@pytest.mark.parametrize('key,value', [('hard_end_unix', 10001), ('lease_end_unix', 12000),
    ('anchor_lambda', 0.5), ('context_limit', 8192), ('new_presentations', 17),
    ('rehearsal_presentations', 2), ('presleep_variant', 'no_distillation'), ('physical', 2)])
def test_candidate_refuses_other_recipe_or_lease_changes(source_fixture, key, value):
    source_fixture.new_plan[key] = value
    with pytest.raises(ValueError, match='all_training_and_plan_semantics_unchanged'):
        verify_fixture(source_fixture)


@pytest.mark.parametrize('name', ['gpu/unchanged.py', 'gpu/orch_r125_continual_native.py',
    'gpu/orch_r125_continual_guard.py', 'gpu/orch_r168_targeted_replay_driver.py'])
def test_candidate_refuses_source_byte_drift(source_fixture, name):
    with (source_fixture.destination / name).open('ab') as stream:
        stream.write(b'\n')
    with pytest.raises(ValueError):
        verify_fixture(source_fixture)


@pytest.mark.parametrize('change', ['missing', 'extra'])
def test_candidate_refuses_changed_source_pin_set(source_fixture, change):
    pins = source_fixture.new_config['source_pins']
    if change == 'missing':
        pins.pop('gpu/unchanged.py')
    else:
        pins['gpu/extra.py'] = 'a' * 64
    with pytest.raises(ValueError, match='exact_source_closure_delta'):
        verify_fixture(source_fixture)


def test_unlisted_python_file_is_rejected_by_retained_guard_closure(source_fixture):
    fixture = source_fixture
    (fixture.destination / 'gpu/unlisted.py').write_text('UNLISTED = True\n')
    assert verify_fixture(fixture) is None
    tree = ast.parse((fixture.destination / 'gpu/orch_r125_continual_guard.py').read_bytes())
    validate = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'validate')
    namespace = dict(__file__=str(fixture.destination / 'gpu/orch_r125_continual_guard.py'), Path=Path,
        child=SimpleNamespace(read=lambda path: fixture.new_config if Path(path) == fixture.binding_path
                              else fixture.new_plan, sha=fixture.operator['sha'],
                              require=fixture.operator['require'], validate_plan=lambda plan: plan))
    exec(compile(ast.Module(body=[validate], type_ignores=[]), '<retained_guard_validate>', 'exec'), namespace)
    with pytest.raises(ValueError, match='entire_python_source_closure'):
        namespace['validate'](fixture.binding_path)


@pytest.mark.parametrize('physical', [0, 2, 3, 4, 5, 6, 7, True, 1.0])
def test_candidate_scope_cannot_select_another_physical_or_bool(source_fixture, physical):
    fixture = source_fixture
    with pytest.raises(ValueError, match='only_existing_creative_physical1'):
        fixture.operator['scope'](dict(fixture.old_plan, physical=physical))


@pytest.mark.parametrize('changes', [dict(gpu_uuid='foreign'), dict(root='/foreign/life'),
    dict(source_root='/foreign/source'), dict(preupdate_recovery={'enabled': True}),
    dict(authorized_wall_extension={'enabled': True})])
def test_candidate_scope_cannot_change_current_life_source_or_recovery(source_fixture, changes):
    with pytest.raises(ValueError):
        source_fixture.operator['scope'](dict(source_fixture.old_plan, **changes))


def test_candidate_foreign_original_guard_refuses_before_imports(candidate):
    operator, family = candidate
    with pytest.raises(ValueError, match='only_original_guard_path'):
        family['old_modules']('/foreign/GUARD.json')


@pytest.mark.parametrize('field,value', [('extra_presentations', 5), ('segment', 119),
    ('selection_kind', 'STRATEGY_REPLAY'), ('source_sha256', 'b' * 64), ('row_sha256', 'c' * 64)])
def test_candidate_refuses_rebound_wrong_selection_not_just_old_hash(source_fixture, field, value):
    source_fixture.selection['selected'][0][field] = value
    source_fixture.rebind()
    with pytest.raises(ValueError, match='one_exact_own_row_four_extras'):
        verify_fixture(source_fixture)


def test_candidate_refuses_future_cycle_beyond_immediate_next(source_fixture):
    source_fixture.selection['target_cycle'] = 42
    source_fixture.rebind()
    with pytest.raises(ValueError, match='one_immediate_next_sleep'):
        verify_fixture(source_fixture)


@pytest.mark.parametrize('mutation', ['none', 'cycle', 'state', 'path'])
def test_candidate_missed_boundary_refuses_before_lower_bundle_or_pause(source_fixture, mutation):
    fixture = source_fixture
    verifier = mock.Mock(return_value={'saved': True})
    fixture.family['api'] = lambda: SimpleNamespace(saved_evidence=verifier)
    saved = dict(cycle=40, state_sha256='state', path=fixture.selection['boundary_ref']['path'])
    if mutation == 'none':
        saved = None
    else:
        key, value = {'cycle': ('cycle', 41), 'state': ('state_sha256', 'changed'),
                      'path': ('path', '/different/record.json')}[mutation]
        saved[key] = value
    with pytest.raises(ValueError, match='selected_exact_boundary_no_missed_cycle'):
        fixture.family['saved_evidence'](fixture.old_plan, saved, object())
    verifier.assert_not_called()


def test_candidate_exact_saved_boundary_delegates_original_verifier(source_fixture):
    fixture = source_fixture
    verifier = mock.Mock(return_value={'original_bundle_verified': True})
    fixture.family['api'] = lambda: SimpleNamespace(saved_evidence=verifier)
    saved = dict(cycle=40, state_sha256='state', path=fixture.selection['boundary_ref']['path'])
    original = object()
    assert fixture.family['saved_evidence'](fixture.old_plan, saved, original) == {'original_bundle_verified': True}
    verifier.assert_called_once_with(fixture.old_plan, saved, original)


@pytest.mark.parametrize('reply', ['{"driver_admitted_CPU_only": true}', '{}'])
def test_candidate_receiving_preflight_uses_admit_not_run(source_fixture, reply):
    fixture = source_fixture
    family = fixture.family
    family['new_modules'] = lambda path: (fixture.new_config, fixture.new_plan, object())
    family['contained_command'] = lambda *args: ['bound_command_stub']
    family['environment'] = lambda source: dict(PYTHONPATH=source, CUDA_VISIBLE_DEVICES='')
    family['api'] = lambda: SimpleNamespace(allocator_command=lambda command: command, sha=lambda path: 'a' * 64)
    call = mock.Mock(return_value=reply)
    fixture.operator['subprocess'] = SimpleNamespace(check_output=call)
    if reply == '{}':
        with pytest.raises(ValueError, match='actual_receiving_driver_preflight'):
            family['validate_new'](fixture.binding_path)
    else:
        assert family['validate_new'](fixture.binding_path)['driver_admitted_CPU_only'] is True
    arguments = call.call_args.args[0]
    assert arguments[:3] == [str(family['PYTHON']), '-B', '-c']
    script = ast.parse(arguments[3])
    calls = [node for node in ast.walk(script) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
             and node.func.value.id == 'driver']
    assert len(calls) == 1 and calls[0].func.attr == '_admit'
    assert call.call_args.kwargs['cwd'] == str(fixture.destination)
    assert call.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'] == ''


@pytest.fixture
def cli_chain(candidate, boundary_api, tmp_path):
    operator, family = candidate
    source = tmp_path / 'cli_source'
    package = source / 'gpu'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    wrapper_path = package / CREATIVE.name
    wrapper_path.write_bytes(CREATIVE.read_bytes())
    guard_path = package / 'orch_r125_continual_guard.py'
    reference = dict(path=str(tmp_path / 'DRIVER.json'), sha256='a' * 64)
    guard_path.write_bytes(operator['patched_guard'](
        (REPO / 'gpu/orch_r125_continual_guard.py').read_bytes(), reference))
    output = tmp_path / 'cli_attempt'
    output.mkdir()
    config_path = output / 'GUARD.json'
    config_path.write_text('{}')
    plan = dict(physical=1, gpu_uuid=operator['UUID'], source_root=str(source), hard_end_unix=2000)
    config = dict(attempt_dir=str(output), device_containment=dict(
        minor=1, uid=2524, gid=2524, unit='orch-r136-native-' + 'a' * 32))
    documents = {'ADMISSION.json': dict(clear=True, scanner_euid=0, blocking_reasons=[],
        gpu=dict(uuid=operator['UUID'])), 'ADMISSION_TIME.json': dict(verified_unix=1000)}
    native = ModuleType('gpu.orch_r125_continual_native')
    native.require = operator['require']
    native.read = lambda path: documents[Path(path).name]
    guard = ModuleType('gpu.orch_r125_continual_guard')
    guard.validate = lambda path: (config, plan)
    feedback = ModuleType('gpu.orch_r133_code_feedback_guard')
    feedback.publish_launch = mock.Mock(side_effect=AssertionError('no_actual_launch'))
    feedback.reap_owned_child = mock.Mock()
    gpu = ModuleType('gpu')
    gpu.__path__ = []
    modules = {'gpu': gpu, native.__name__: native, guard.__name__: guard,
        feedback.__name__: feedback,
        'gpu.orch_r133_retire_old_lanes': ModuleType('gpu.orch_r133_retire_old_lanes')}
    with mock.patch.dict(sys.modules, modules):
        creative = frozen_namespace(wrapper_path, CREATIVE_SHA256)
        original = SimpleNamespace(programmes=SimpleNamespace(**creative))
        baseline = family['contained_command'](plan, config, original, config_path, 1000)
        allocated = boundary_api['allocator_command'](baseline)
        assert '--action' not in allocated
        assert '--property=DevicePolicy=strict' in allocated
        assert 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True' in allocated
        payload_start = allocated.index('-m') - 2
        wrapper_command = allocated[payload_start:]
        assert wrapper_command == [str(family['PYTHON']), '-B', '-m', family['CREATIVE_MODULE'],
                                   'contained-native', '--config', str(config_path)]
        captured = mock.Mock(side_effect=RuntimeError('captured_native_command_without_spawning'))
        creative.update(time=SimpleNamespace(time=lambda: 1000),
            verify_device_containment=lambda *args: {}, write=lambda *args: None,
            subprocess=SimpleNamespace(Popen=captured, PIPE=-1, STDOUT=-2))
        with pytest.raises(RuntimeError, match='captured_native_command_without_spawning'):
            creative['contained_native'](config_path)
        feedback.publish_launch.assert_not_called()
        feedback.reap_owned_child.assert_called_once_with(None)
    timer_command = captured.call_args.args[0]
    assert timer_command[:4] == ['timeout', '--signal=TERM', '--kill-after=5s', '990s']
    assert timer_command[4:] == [str(family['PYTHON']), '-B', '-m', family['GUARD_MODULE'],
                                'native', '--config', str(config_path)]
    supervisor_command = [str(family['PYTHON']), '-B', operator['__file__'], '--action',
                          'supervise', '--output', str(output)]
    return SimpleNamespace(source=source, output=output, operator=operator,
        commands={'supervise': supervisor_command, 'contained-native': wrapper_command,
                  'native': timer_command[4:]},
        entries={'supervise': (operator['__file__'], 'supervise'),
                 'contained-native': (str(wrapper_path), 'contained_native'),
                 'native': (str(guard_path), 'native_entry')})


@pytest.mark.parametrize('transition', ['supervise', 'contained-native', 'native', 'contained'])
def test_actual_subprocess_CLI_dispatch_for_exact_physical1_chain(cli_chain, tmp_path, transition):
    hooks = tmp_path / 'cli_hooks'
    hooks.mkdir()
    (hooks / 'sitecustomize.py').write_text(CLI_ENTRY_HOOK)
    if transition == 'contained':
        command = [sys.executable, '-B', cli_chain.operator['__file__'], '--action', 'contained',
                   '--output', str(cli_chain.output)]
        entry_file, entry_function = cli_chain.entries['supervise']
    else:
        command = cli_chain.commands[transition]
        entry_file, entry_function = cli_chain.entries[transition]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=os.pathsep.join((str(hooks), str(cli_chain.source))),
        R170_REVIEW_ENTRY_FILE=entry_file, R170_REVIEW_ENTRY_FUNCTION=entry_function)
    completed = subprocess.run([sys.executable, *command[1:]], cwd=cli_chain.source,
        env=environment, text=True, capture_output=True, timeout=15, check=False)
    if transition == 'contained':
        assert completed.returncode == 2
        assert 'invalid choice' in completed.stderr and "'contained'" in completed.stderr
        assert completed.stdout == ''
    else:
        assert completed.returncode == 0, completed.stderr
        receipt = json.loads(completed.stdout)
        assert receipt['entered'] == entry_function and receipt['file'] == entry_file
        assert receipt['pid'] != os.getpid()
        expected_arguments = command[4:] if '-m' in command else command[3:]
        assert receipt['argv'][1:] == expected_arguments
    assert not list(cli_chain.output.glob('SUPERVISOR_FAILED*'))
    assert not list(cli_chain.output.glob('*ONCE'))
    assert not list(cli_chain.output.glob('LAUNCH*'))
