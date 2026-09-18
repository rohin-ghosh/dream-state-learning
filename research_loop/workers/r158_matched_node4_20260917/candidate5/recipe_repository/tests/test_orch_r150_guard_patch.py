"""Non-material CPU staging regressions; no subprocesses, scans, or GPUs."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r125_continual_native as native
from gpu import orch_r150_guard_patch as patcher
from gpu import orch_r150_matched_native as matched


ROOT = Path(__file__).resolve().parents[1]
GUARD = Path('gpu/orch_r125_continual_guard.py')
FROZEN = ROOT/'research_notes/analysis/orch_r140_raw3_english_20260916'


@pytest.fixture
def original():
    return (ROOT/GUARD).read_bytes().decode('utf-8')


def test_exact_two_block_transformation_and_byte_reversal(original):
    before = (ROOT/GUARD).read_bytes()
    result = patcher.patch_source(original)
    assert hashlib.sha256(before).hexdigest() == patcher.ORIGINAL_SHA256
    assert result == original.replace(patcher.OLD_VALIDATION, patcher.NEW_VALIDATION).replace(
        patcher.OLD_DISPATCH, patcher.NEW_DISPATCH)
    assert patcher.revert_source(result).encode('utf-8') == before
    assert (ROOT/GUARD).read_bytes() == before
    assert patcher.patch_source(original) == result
    assert patcher.OLD_DISPATCH not in result
    assert "os.environ['R125_ADMISSION_PLAN_SHA256'] = config['plan_sha256']" in result


@pytest.mark.parametrize('snapshot,metadata', [('source1', 'SOURCE.json'), ('source2', 'SOURCE2.json')])
def test_known_local_frozen_source_and_receipt(snapshot, metadata, original):
    fixture, receipt = FROZEN/snapshot/GUARD, FROZEN/metadata
    if not fixture.exists() or not receipt.exists():
        pytest.skip('optional preserved R140 frozen fixture unavailable')
    frozen = fixture.read_bytes()
    assert frozen == original.encode('utf-8')
    assert json.loads(receipt.read_text())['files'][str(GUARD)] == patcher.ORIGINAL_SHA256
    assert patcher.revert_source(patcher.patch_source(frozen.decode())).encode() == frozen


def test_non_target_functions_and_module_nodes_identical(original):
    result = patcher.patch_source(original)
    before, after = ast.parse(original), ast.parse(result)
    assert len(before.body) == len(after.body)
    for old, new in zip(before.body, after.body):
        if isinstance(old, ast.FunctionDef) and old.name in ('validate', 'native_entry'):
            continue
        assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
        assert ast.get_source_segment(original, old) == ast.get_source_segment(result, new)
    old_native = next(node for node in before.body if getattr(node, 'name', None) == 'native_entry')
    new_native = next(node for node in after.body if getattr(node, 'name', None) == 'native_entry')
    assert [ast.dump(node) for node in old_native.body[:-1]] == [
        ast.dump(node) for node in new_native.body[:len(old_native.body)-1]]


@pytest.mark.parametrize('mutation', [
    lambda source: '',
    lambda source: source + '\n',
    lambda source: source.replace('\n', '\r\n'),
    lambda source: source + patcher.OLD_DISPATCH,
    lambda source: source + patcher.OLD_VALIDATION,
    lambda source: source + '\ndef native_entry(config_path):\n    pass\n',
    lambda source: source.replace('def native_entry(', 'def another_entry('),
    lambda source: source.replace('<= 120', '<= 1200'),
    lambda source: source.replace('os.geteuid() == 0', 'True'),
    lambda source: source.replace("actual == config['source_pins']", 'True'),
    lambda source: source.replace('orch_rich_hot_a100_minor_scan', 'arbitrary_module'),
    lambda source: source.replace('orch_r125_continual_native as child', 'arbitrary_module as child'),
    lambda source: source + "\nMODULE = 'arbitrary_module'\n",
    lambda source: source.replace(patcher.OLD_DISPATCH, patcher.NEW_DISPATCH),
    lambda source: source.replace(patcher.OLD_VALIDATION, patcher.NEW_VALIDATION),
    lambda source: patcher.patch_source(source),
])
def test_reject_unsupported_duplicate_weakened_and_prepatched_source(original, mutation):
    with pytest.raises(ValueError):
        patcher.patch_source(mutation(original))


@pytest.mark.parametrize('mutation', [
    lambda source: source + '\n',
    lambda source: source + patcher.NEW_DISPATCH,
    lambda source: source.replace('matched.initialize(', 'child.initialize('),
    lambda source: source.replace('orch_r150_matched_native', 'arbitrary_module'),
    lambda source: source.replace("ticks == launch['parent_start_ticks']", 'True'),
    lambda source: source.replace("os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']", 'True'),
    lambda source: source.replace("    os.environ['R125_ADMISSION_PLAN_SHA256'] = config['plan_sha256']\n", ''),
])
def test_reversal_rejects_any_extra_change(original, mutation):
    with pytest.raises(ValueError):
        patcher.revert_source(mutation(patcher.patch_source(original)))


@pytest.mark.parametrize('value', [None, b'source', 123])
def test_text_only_api(value):
    for operation in (patcher.patch_source, patcher.revert_source):
        with pytest.raises(TypeError, match='guard_source_must_be_text'):
            operation(value)


def write_json(path, document):
    Path(path).write_text(json.dumps(document, sort_keys=True)+'\n')


class RecordingEnvironment(dict):
    def __init__(self, events, **values):
        super().__init__(values)
        self.events = events

    def __setitem__(self, key, value):
        self.events.append(('environment', key, value))
        super().__setitem__(key, value)


@pytest.fixture
def runtime(tmp_path, monkeypatch, original):
    events = []
    real_native_validation, real_matched_validation = native.validate_plan, matched.validate_plan
    source = tmp_path/'new-frozen-source'
    module_path = source/GUARD
    module_path.parent.mkdir(parents=True)
    transformed = patcher.patch_source(original)
    module_path.write_text(transformed)
    dependency = source/'dependency.py'
    dependency.write_text('VALUE = 1\n')
    attempt = tmp_path/'attempt'
    attempt.mkdir()
    (attempt/'DISPATCH_ONCE').mkdir()
    cohort_path = tmp_path/'cohort.json'
    write_json(cohort_path, {'fixture': 'CPU only'})
    plan = dict(source_root=str(source), hard_end_unix=700, lease_end_unix=1100,
                gpu_uuid='GPU-synthetic', physical=0, matched_arm='parented_learning',
                matched_cohort=dict(path=str(cohort_path), sha256=native.sha(cohort_path)))
    plan_path = tmp_path/'plan.json'
    write_json(plan_path, plan)
    lease_path = tmp_path/'lease.json'
    write_json(lease_path, dict(hard_end_unix=700, lease_end_unix=1100))
    allocation_path = tmp_path/'allocation.json'
    allocation = dict(plan_sha256=native.sha(plan_path), gpu_uuid=plan['gpu_uuid'], physical=0,
                      cpu_tests_passed=True, builder_entry_pushed=True, declared_unix=90)
    write_json(allocation_path, allocation)
    config = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=str(plan_path), plan_sha256=native.sha(plan_path),
                  source_pins={str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')},
                  host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(), hard_end_unix=700,
                  next_reserved_unix=820, lease_path=str(lease_path), lease_sha256=native.sha(lease_path),
                  allocation_path=str(allocation_path), allocation_sha256=native.sha(allocation_path),
                  attempt_dir=str(attempt), phase='run', resume=False,
                  matched_arm=plan['matched_arm'], matched_cohort_sha256=plan['matched_cohort']['sha256'])
    config_path = tmp_path/'guard.json'
    write_json(config_path, config)
    report = dict(scanner_euid=0, clear=True, blocking_reasons=[], gpu=dict(uuid=plan['gpu_uuid']))
    write_json(attempt/'ADMISSION.json', report)
    launch = dict(pid=4321, parent_start_ticks='9876', guard_sha256=native.sha(config_path),
                  admission_sha256=native.sha(attempt/'ADMISSION.json'), admission_verified_unix=99)
    write_json(attempt/'LAUNCH.json', launch)
    process_stat = tmp_path/'parent-stat'
    process_stat.write_text('4321 (timeout fixture) '+' '.join(['S']*19+['9876']))
    guard = ModuleType('r150_cpu_frozen_guard')
    guard.__file__ = str(module_path)
    exec(compile(transformed, str(module_path), 'exec'), guard.__dict__)
    real_require = native.require

    def require(condition, label):
        events.append(('require', label))
        real_require(condition, label)

    def validate_native(document):
        events.append(('validate', 'child'))
        return document

    def validate_matched(document):
        events.append(('validate', 'matched'))
        return document, {'fixture': 'CPU only'}

    def dispatch(kind):
        def record(*args, **kwargs):
            events.append(('dispatch', kind, args, kwargs))
        return Mock(side_effect=record)

    monkeypatch.setattr(native, 'require', require)
    child_validation = Mock(side_effect=validate_native)
    matched_validation = Mock(side_effect=validate_matched)
    monkeypatch.setattr(native, 'validate_plan', child_validation)
    monkeypatch.setattr(matched, 'validate_plan', matched_validation)
    original_run = Mock(side_effect=AssertionError('original dispatch forbidden'))
    monkeypatch.setattr(native, 'run', original_run)
    initialize, run = dispatch('initialize'), dispatch('run')
    monkeypatch.setattr(matched, 'initialize', initialize)
    monkeypatch.setattr(matched, 'run', run)
    environment = RecordingEnvironment(events, CUDA_VISIBLE_DEVICES=plan['gpu_uuid'],
                                       R125_ADMISSION_PLAN_SHA256='caller-plan', R150_COHORT_SHA256='caller-cohort')
    guard.os = SimpleNamespace(environ=environment, getppid=lambda: 4321, geteuid=lambda: 0)
    guard.time = SimpleNamespace(time=lambda: 100)
    guard.Path = lambda *parts: process_stat if parts[0] == '/proc' else Path(*parts)
    guard.await_startup = Mock(side_effect=lambda *args: events.append(('startup',)))
    guard.subprocess = SimpleNamespace(
        check_output=Mock(side_effect=AssertionError('no privileged scans')),
        Popen=Mock(side_effect=AssertionError('no processes')))
    return SimpleNamespace(guard=guard, config=config, config_path=config_path, plan=plan, plan_path=plan_path,
                           source=source, dependency=dependency, attempt=attempt, launch=launch, report=report,
                           allocation=allocation, events=events, environment=environment, initialize=initialize,
                           run=run, original_run=original_run, child_validation=child_validation,
                           matched_validation=matched_validation, process_stat=process_stat,
                           caller_environment=dict(environment), real_native_validation=real_native_validation,
                           real_matched_validation=real_matched_validation)


def bind_config(runtime):
    write_json(runtime.config_path, runtime.config)
    runtime.launch['guard_sha256'] = native.sha(runtime.config_path)
    write_json(runtime.attempt/'LAUNCH.json', runtime.launch)


def assert_no_dispatch_or_environment_write(runtime):
    runtime.initialize.assert_not_called()
    runtime.run.assert_not_called()
    runtime.original_run.assert_not_called()
    assert not any(event[0] in ('environment', 'dispatch') for event in runtime.events)
    for key in ('R125_ADMISSION_PLAN_SHA256', 'R150_COHORT_SHA256'):
        assert runtime.environment[key] == runtime.caller_environment[key]


@pytest.mark.parametrize('phase,arm,resume', [
    ('initialize', 'parented_learning', False),
    *[('run', arm, resume) for arm in matched.ARMS for resume in (False, True)],
])
def test_dispatch_follows_every_original_admission_and_overwrites_caller_environment(runtime, phase, arm, resume):
    runtime.plan['matched_arm'] = arm
    write_json(runtime.plan_path, runtime.plan)
    runtime.config.update(phase=phase, matched_arm=arm, resume=resume, plan_sha256=native.sha(runtime.plan_path))
    runtime.allocation['plan_sha256'] = runtime.config['plan_sha256']
    write_json(runtime.config['allocation_path'], runtime.allocation)
    runtime.config['allocation_sha256'] = native.sha(runtime.config['allocation_path'])
    bind_config(runtime)
    runtime.guard.native_entry(runtime.config_path)
    assert runtime.events.index(('validate', 'child')) < runtime.events.index(('validate', 'matched'))
    assert runtime.events.index(('validate', 'matched')) < runtime.events.index(('require', 'frozen_source_location'))
    assert runtime.events[-4:-1] == [
        ('require', 'native_GPU_binding'),
        ('environment', 'R125_ADMISSION_PLAN_SHA256', runtime.config['plan_sha256']),
        ('environment', 'R150_COHORT_SHA256', runtime.config['matched_cohort_sha256'])]
    labels = [event[1] for event in runtime.events if event[0] == 'require']
    assert labels[-4:] == ['actual_timeout_parent', 'launch_process_and_config_binding',
                           'fresh_clear_admission', 'native_GPU_binding']
    assert runtime.events.index(('startup',)) < runtime.events.index(('require', 'actual_timeout_parent'))
    if phase == 'initialize':
        runtime.initialize.assert_called_once_with(runtime.config['plan_path'])
        runtime.run.assert_not_called()
    else:
        runtime.run.assert_called_once_with(runtime.config['plan_path'], resume=resume)
        runtime.initialize.assert_not_called()
    runtime.original_run.assert_not_called()


@pytest.mark.parametrize('field,value,label', [
    ('phase', None, 'r150_explicit_phase'), ('phase', 'scan', 'r150_explicit_phase'),
    ('resume', None, 'r150_explicit_resume_boolean'), ('resume', 0, 'r150_explicit_resume_boolean'),
    ('resume', 'false', 'r150_explicit_resume_boolean'),
    ('matched_cohort_sha256', None, 'r150_exact_cohort_binding'),
    ('matched_cohort_sha256', '0'*64, 'r150_exact_cohort_binding'),
    ('matched_arm', None, 'r150_exact_arm_binding'),
    ('matched_arm', 'unparented_learning', 'r150_exact_arm_binding'),
])
def test_explicit_config_bindings_required(runtime, field, value, label):
    if value is None:
        del runtime.config[field]
    else:
        runtime.config[field] = value
    bind_config(runtime)
    with pytest.raises(ValueError, match=label):
        runtime.guard.native_entry(runtime.config_path)
    runtime.guard.await_startup.assert_not_called()
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('arm,resume', [
    ('parented_learning', True), ('parented_frozen', False), ('unparented_learning', False),
])
def test_initialize_only_designated_fresh_learning_arm(runtime, arm, resume):
    runtime.plan['matched_arm'] = arm
    write_json(runtime.plan_path, runtime.plan)
    runtime.config.update(phase='initialize', matched_arm=arm, resume=resume,
                          plan_sha256=native.sha(runtime.plan_path))
    bind_config(runtime)
    with pytest.raises(ValueError, match='r150_designated_fresh_initializer'):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('validator', ['child_validation', 'matched_validation'])
def test_validation_failure_precedes_startup_and_environment(runtime, validator):
    getattr(runtime, validator).side_effect = ValueError('validator_rejected')
    with pytest.raises(ValueError, match='validator_rejected'):
        runtime.guard.native_entry(runtime.config_path)
    if validator == 'child_validation':
        runtime.matched_validation.assert_not_called()
    runtime.guard.await_startup.assert_not_called()
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('tamper', [False, True])
def test_real_matched_validator_checks_exact_cohort_bytes(runtime, monkeypatch, tamper):
    from organism_v6.orch_r125_plain_context import VERSION

    root = runtime.config_path.parent
    runtime.plan.update(schema=native.SCHEMA, base_sha256=native.BASE_SHA256,
        system_prompt=native.SYSTEM, birth_prompt=native.BIRTH, compaction_invitation=native.COMPACTION_INVITATION,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25, seed=0, segments_per_sleep=2,
        segment_tokens=16, context_limit=16384, max_sleeps=2, startup_context=None, presentation_version=VERSION,
        presleep_variant='free_distillation', readout_revision=1, model_dir=str(root/'model'),
        anchors=str(root/'anchors'), root=str(root/'parented_learning'), parent_enabled=True,
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16))
    plans = [dict(deepcopy(runtime.plan), matched_arm=arm, parent_enabled=arm != 'unparented_learning',
                  root=str(root/arm), physical=index, gpu_uuid=f'GPU-fixture-{index}')
             for index, arm in enumerate(matched.ARMS)]
    runtime.plan.update(plans[0])
    cohort = matched.cohort_document(plans, root/'common-initial')
    cohort_path = Path(runtime.plan['matched_cohort']['path'])
    write_json(cohort_path, cohort)
    runtime.plan['matched_cohort']['sha256'] = native.sha(cohort_path)
    write_json(runtime.plan_path, runtime.plan)
    runtime.config.update(plan_sha256=native.sha(runtime.plan_path),
                          matched_cohort_sha256=runtime.plan['matched_cohort']['sha256'])
    runtime.allocation.update(plan_sha256=runtime.config['plan_sha256'], gpu_uuid=runtime.plan['gpu_uuid'])
    write_json(runtime.config['allocation_path'], runtime.allocation)
    runtime.config['allocation_sha256'] = native.sha(runtime.config['allocation_path'])
    bind_config(runtime)
    runtime.child_validation.side_effect = runtime.real_native_validation
    runtime.matched_validation.side_effect = runtime.real_matched_validation
    monkeypatch.setattr(native, 'time', SimpleNamespace(time=lambda: 100))
    if tamper:
        cohort_path.write_text(json.dumps(cohort, indent=2))
        with pytest.raises(ValueError, match='immutable_matched_cohort'):
            runtime.guard.validate(runtime.config_path)
    else:
        assert runtime.guard.validate(runtime.config_path) == (runtime.config, runtime.plan)
    assert runtime.child_validation.call_count == 2
    runtime.matched_validation.assert_called_once()
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('field,value,label', [
    ('schema', 'other', 'guard_schema'), ('plan_sha256', '0'*64, 'guard_plan_bytes'),
    ('source_pins', {}, 'entire_python_source_closure'), ('host_sha256', '0'*64, 'hashed_node_binding'),
    ('hard_end_unix', 701, 'one_bound_wall'), ('lease_sha256', '0'*64, 'lease_receipt_bytes'),
    ('next_reserved_unix', 819, 'preserve_next_reservation'),
    ('allocation_sha256', '0'*64, 'posted_allocation_and_CPU_provenance'),
    ('attempt_dir', 'relative', 'attempt_outside_source'),
])
def test_original_config_checks_still_reject_before_environment(runtime, field, value, label):
    runtime.config[field] = value
    bind_config(runtime)
    with pytest.raises(ValueError, match=label):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('field,value', [
    ('plan_sha256', '0'*64), ('gpu_uuid', 'GPU-other'), ('physical', 1),
    ('cpu_tests_passed', False), ('builder_entry_pushed', False), ('declared_unix', 101),
])
def test_rehashed_allocation_cannot_bypass_original_provenance(runtime, field, value):
    runtime.allocation[field] = value
    write_json(runtime.config['allocation_path'], runtime.allocation)
    runtime.config['allocation_sha256'] = native.sha(runtime.config['allocation_path'])
    bind_config(runtime)
    label = 'allocation_not_future' if field == 'declared_unix' else 'posted_allocation_and_CPU_provenance'
    with pytest.raises(ValueError, match=label):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('field,value', [('lease_end_unix', 1099), ('lease_end_unix', 1101),
                                      ('hard_end_unix', 699)])
def test_rehashed_lease_cannot_bypass_original_margin(runtime, field, value):
    lease = dict(lease_end_unix=1100, hard_end_unix=700)
    lease[field] = value
    write_json(runtime.config['lease_path'], lease)
    runtime.config['lease_sha256'] = native.sha(runtime.config['lease_path'])
    bind_config(runtime)
    with pytest.raises(ValueError, match='existing_lease_margin_preserved'):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


def test_original_source_location_check_cannot_be_rebound(runtime):
    runtime.plan['source_root'] = str(runtime.source.parent/'elsewhere')
    write_json(runtime.plan_path, runtime.plan)
    runtime.config['plan_sha256'] = native.sha(runtime.plan_path)
    bind_config(runtime)
    with pytest.raises(ValueError, match='frozen_source_location'):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('change', ['edit', 'add', 'delete', 'patched_guard'])
def test_full_source_closure_is_still_exact(runtime, change):
    if change == 'edit':
        runtime.dependency.write_text('VALUE = 2\n')
    elif change == 'add':
        (runtime.source/'extra.py').write_text('VALUE = 1\n')
    elif change == 'delete':
        runtime.dependency.unlink()
    else:
        (runtime.source/GUARD).write_text('guard modified after pinning\n')
    with pytest.raises(ValueError, match='entire_python_source_closure'):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('field,value', [('phase', 'initialize'), ('matched_cohort_sha256', '0'*64),
                                      ('matched_arm', 'parented_frozen'), ('resume', True)])
def test_launch_config_hash_binds_new_fields(runtime, field, value):
    runtime.config[field] = value
    write_json(runtime.config_path, runtime.config)
    validated_plan = deepcopy(runtime.plan)
    validated_plan['matched_arm'] = runtime.config['matched_arm']
    validated_plan['matched_cohort']['sha256'] = runtime.config['matched_cohort_sha256']
    runtime.guard.validate = Mock(return_value=(runtime.config, validated_plan))
    with pytest.raises(ValueError, match='launch_process_and_config_binding'):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('caller_admitted', [False, True])
@pytest.mark.parametrize('failure,label', [
    ('startup', 'startup_not_published'), ('dispatch_once', 'actual_timeout_parent'),
    ('pid', 'actual_timeout_parent'), ('ticks', 'launch_process_and_config_binding'),
    ('config_sha', 'launch_process_and_config_binding'), ('report_sha', 'fresh_clear_admission'),
    ('scanner_euid', 'fresh_clear_admission'), ('clear', 'fresh_clear_admission'),
    ('blocking_reasons', 'fresh_clear_admission'), ('gpu', 'fresh_clear_admission'),
    ('stale', 'fresh_clear_admission'), ('future', 'fresh_clear_admission'), ('device', 'native_GPU_binding'),
])
def test_every_native_admission_failure_prevents_dispatch_even_with_caller_env(runtime, failure, label,
                                                                             caller_admitted):
    if caller_admitted:
        runtime.caller_environment.update(R125_ADMISSION_PLAN_SHA256=runtime.config['plan_sha256'],
                                          R150_COHORT_SHA256=runtime.config['matched_cohort_sha256'])
        dict.update(runtime.environment, runtime.caller_environment)
    if failure == 'startup':
        runtime.guard.await_startup.side_effect = ValueError(label)
    elif failure == 'dispatch_once':
        (runtime.attempt/'DISPATCH_ONCE').rmdir()
    elif failure == 'pid':
        runtime.launch['pid'] = 9999
    elif failure == 'ticks':
        runtime.launch['parent_start_ticks'] = 'different'
    elif failure == 'config_sha':
        runtime.launch['guard_sha256'] = '0'*64
    elif failure == 'report_sha':
        runtime.launch['admission_sha256'] = '0'*64
    elif failure in ('stale', 'future'):
        runtime.launch['admission_verified_unix'] = -21 if failure == 'stale' else 101
    elif failure == 'device':
        dict.__setitem__(runtime.environment, 'CUDA_VISIBLE_DEVICES', 'GPU-other')
    else:
        runtime.report[failure] = {'scanner_euid': 1000, 'clear': False, 'blocking_reasons': ['occupied'],
                                   'gpu': {'uuid': 'GPU-other'}}[failure]
        write_json(runtime.attempt/'ADMISSION.json', runtime.report)
        runtime.launch['admission_sha256'] = native.sha(runtime.attempt/'ADMISSION.json')
    write_json(runtime.attempt/'LAUNCH.json', runtime.launch)
    with pytest.raises(ValueError, match=label):
        runtime.guard.native_entry(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)


@pytest.mark.parametrize('euid,devices', [(1000, ''), (0, 'GPU-synthetic')])
def test_privileged_scan_precondition_unchanged(runtime, euid, devices):
    runtime.guard.os.geteuid = lambda: euid
    dict.__setitem__(runtime.environment, 'CUDA_VISIBLE_DEVICES', devices)
    with pytest.raises(ValueError, match='privileged_CPU_scan'):
        runtime.guard.scan(runtime.config_path)
    assert_no_dispatch_or_environment_write(runtime)
