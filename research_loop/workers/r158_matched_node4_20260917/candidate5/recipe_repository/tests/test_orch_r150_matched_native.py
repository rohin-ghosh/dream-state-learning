"""CPU-only provenance and runner tests; synthetic tensors are not GPU evidence."""

from copy import deepcopy
import json
from pathlib import Path
import random
import signal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r150_matched_native as matched
from gpu.orch_r125_continual_native import NativeChild, digest, experiment_binding
from gpu.orch_r150_matched_journal import MatchedJournal
from gpu import orch_r150_readout_custody as readout_custody
from organism_v6.orch_r125_plain_context import VERSION
from organism_v6.orch_r150_matched_stream import MatchedStream
from test_orch_r125_continual_native import make_plan


@pytest.fixture
def recovery_fixture(tmp_path, monkeypatch):
    original_root = tmp_path / 'orch_r158_matched_node4_20260917_attempt3'
    original_root.mkdir()
    original_plans, unused = cohort_fixture(original_root)
    devices = ['GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30',
               'GPU-06b31c8f-7a96-d812-23f3-df3444d95397',
               'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98']
    for index, plan in enumerate(original_plans):
        plan.update(physical=index + 5, gpu_uuid=devices[index],
                    source_root=str(original_root / 'source'),
                    initialization_validation_schema='R151_MATCHED_INITIAL_CAPACITY_V1')
    original_cohort = matched.cohort_document(original_plans, original_root / 'common_initial')
    (original_root / 'COHORT.json').write_text(json.dumps(original_cohort))
    for plan in original_plans:
        plan['matched_cohort']['sha256'] = matched.native.sha(original_root / 'COHORT.json')
    matched.native.write_once(original_root / 'parented_learning.PLAN.json', original_plans[0])
    checkpoint = save_checkpoint(original_root / 'common_initial', original_plans[0])
    failed = dict(schema='R151_MATCHED_INITIAL_CAPACITY_V1', status='FAIL',
        error='designated_node5_initializer_only', error_type='ValueError',
        plan_sha256=matched.native.sha(original_root / 'parented_learning.PLAN.json'),
        generation_calls=0, optimizer_updates=0, stream_data_written=False,
        scientific_evaluation=False, state_restored=False, restoration_status='UNVERIFIED')
    matched.native.write_once(original_root / 'common_initial/capacity_validation/RESULT.json', failed)
    matched.native.write_once(original_root / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json',
        dict(status='SERVICE_EXIT_VERIFIED', cgroup_empty_verified=True, service_returncode=1))
    monkeypatch.setattr(matched, 'INITIALIZATION_SOURCE_ROOT', original_root)
    new_root = tmp_path / 'orch_r158_matched_node4_20260917_attempt4'
    source_path = tmp_path / 'INITIALIZATION_SOURCE.json'

    def bind():
        pins = {name: (relative, matched.native.sha(original_root / relative))
                for name, (relative, unused_sha) in matched.INITIALIZATION_SOURCE_FILES.items()}
        monkeypatch.setattr(matched, 'INITIALIZATION_SOURCE_FILES', pins)
        source = dict(schema='R158_SAVED_INITIALIZATION_SOURCE_V1',
            **{name: dict(path=str(original_root / relative), sha256=checksum)
               for name, (relative, checksum) in pins.items()})
        source_path.write_text(json.dumps(source))
        return dict(path=str(source_path), sha256=matched.native.sha(source_path))

    reference = bind()
    plans = [dict(deepcopy(plan), root=str(new_root / plan['matched_arm']),
                  source_root=str(new_root / 'source'), initialization_source=deepcopy(reference))
             for plan in original_plans]

    def bind_cohort():
        cohort = matched.cohort_document(plans, new_root / 'common_initial')
        new_root.mkdir(exist_ok=True)
        cohort_path = new_root / 'COHORT.json'
        cohort_path.write_text(json.dumps(cohort))
        for plan in plans:
            plan['matched_cohort'] = dict(path=str(cohort_path), sha256=matched.native.sha(cohort_path))
        return cohort

    cohort = bind_cohort()
    return SimpleNamespace(original=original_root, new=new_root, plans=plans, cohort=cohort,
                           source=source_path, checkpoint=checkpoint, rebind=bind, bind_cohort=bind_cohort)


def test_saved_initialization_reference_shared_all_arms_and_absent_legacy(recovery_fixture):
    fixture = recovery_fixture
    for plan in fixture.plans:
        assert matched.validate_plan(plan) == (plan, fixture.cohort)
    changed = deepcopy(fixture.plans)
    del changed[1]['initialization_source']
    with pytest.raises(ValueError, match='identical_common'):
        matched.cohort_document(changed, fixture.new / 'another_initial')
    legacy = dict(fixture.plans[0])
    del legacy['initialization_source']
    assert 'initialization_source' not in matched.common_configuration(legacy)


@pytest.mark.parametrize('field,value', [('seed', 9), ('anchor_lambda', 0.5),
    ('model_dir', '/another/model'), ('new_presentations', 8), ('context_limit', 32768),
    ('initialization_validation_schema', None), ('hard_end_unix', 1)])
def test_recovery_rejects_changed_recipe(recovery_fixture, field, value):
    plan = dict(recovery_fixture.plans[0], **{field: value})
    with pytest.raises(ValueError, match='exact_initialization_recipe'):
        matched.validate_initialization_source(plan)


@pytest.mark.parametrize('name', list(matched.INITIALIZATION_SOURCE_FILES))
def test_recovery_rejects_tampered_original_receipts(recovery_fixture, name):
    fixture = recovery_fixture
    path = fixture.original / matched.INITIALIZATION_SOURCE_FILES[name][0]
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError, match='immutable_initialization_reference'):
        matched.validate_initialization_source(fixture.plans[0])


@pytest.mark.parametrize('relative', ['common_initial/INITIALIZED.json', *matched.ARMS])
def test_recovery_rejects_original_admission_or_birth(recovery_fixture, relative):
    fixture = recovery_fixture
    (fixture.original / relative).write_text('{}')
    with pytest.raises(ValueError, match='never_admitted_or_born'):
        matched.validate_initialization_source(fixture.plans[0])


@pytest.mark.parametrize('name,key,value', [('capacity', 'error', 'CUDA out of memory'),
    ('capacity', 'optimizer_updates', 1), ('capacity', 'generation_calls', 1),
    ('capacity', 'stream_data_written', True), ('capacity', 'state_restored', True),
    ('capacity', 'maximum_shape', {}), ('lifecycle', 'cgroup_empty_verified', False),
    ('lifecycle', 'service_returncode', 0), ('commit', 'optimizer_steps', 1)])
def test_recovery_rejects_wrong_failure_even_if_reference_rebound(recovery_fixture, name, key, value):
    fixture = recovery_fixture
    path = fixture.original / matched.INITIALIZATION_SOURCE_FILES[name][0]
    document = json.loads(path.read_text())
    document[key] = value
    path.write_text(json.dumps(document))
    fixture.plans[0]['initialization_source'] = fixture.rebind()
    with pytest.raises(ValueError):
        matched.validate_initialization_source(fixture.plans[0])


def test_saved_initialization_reference_rejects_symlink_and_null(recovery_fixture):
    fixture = recovery_fixture
    with pytest.raises(ValueError, match='exact_initialization_reference'):
        matched.validate_initialization_source(dict(fixture.plans[0], initialization_source=None))
    linked = fixture.source.with_suffix('.linked')
    linked.symlink_to(fixture.source)
    reference = dict(path=str(linked), sha256=matched.native.sha(linked))
    with pytest.raises(ValueError, match='regular_initialization_reference'):
        matched.validate_initialization_source(dict(fixture.plans[0], initialization_source=reference))


@pytest.mark.parametrize('failure', [None, 'before', 'capacity', 'after'])
def test_initialize_recovery_restores_never_regenerates_and_checks_both_sides(recovery_fixture, monkeypatch, failure):
    fixture = recovery_fixture
    plan = fixture.plans[0]
    plan_path = fixture.new / 'parented_learning.PLAN.json'
    matched.native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    calls = []
    observation = dict(checkpoint_file_hashes=fixture.checkpoint['checkpoint_sha256'])

    def constructor(actual_plan, checkpoint):
        assert actual_plan == plan
        assert checkpoint['checkpoint_sha256'] == fixture.checkpoint['checkpoint_sha256']
        calls.append('restore')
        return SimpleNamespace(native=SimpleNamespace(process_identity=lambda: {'CPU_fixture': True}))

    def verify(child, checkpoint):
        phase = 'before' if calls == ['restore'] else 'after'
        calls.append(phase)
        NativeChild.verify_checkpoint(checkpoint)
        if failure == phase:
            raise ValueError('synthetic_' + phase)
        return deepcopy(observation)

    def capacity(child, actual_path, destination):
        assert calls == ['restore', 'before']
        calls.append('capacity')
        if failure == 'capacity':
            raise ValueError('synthetic_capacity')
        return dict(status='PASS')

    original_bytes = {str(path.relative_to(fixture.original)): path.read_bytes()
                      for path in fixture.original.rglob('*') if path.is_file()}
    monkeypatch.setattr(matched, 'MatchedChild', constructor)
    monkeypatch.setattr(matched, 'verify_loaded_initial', verify)
    monkeypatch.setattr(matched, 'verify_initialization_validation', Mock())
    if failure:
        with pytest.raises(ValueError, match='synthetic_' + failure):
            matched.initialize(plan_path, validate_child=capacity)
        assert not (fixture.new / 'common_initial/INITIALIZED.json').exists()
    else:
        assert matched.initialize(plan_path, validate_child=capacity) == observation
        initialized = matched.native.read(fixture.new / 'common_initial/INITIALIZED.json')
        assert initialized['initialization_source'] == plan['initialization_source']
        assert initialized['recovered_initial_state_before_validation'] == observation
        assert calls == ['restore', 'before', 'capacity', 'after']
    assert original_bytes == {str(path.relative_to(fixture.original)): path.read_bytes()
                              for path in fixture.original.rglob('*') if path.is_file()}
    with pytest.raises(ValueError, match='never_recreated'):
        matched.initialize(plan_path, validate_child=capacity)


def test_recovery_requires_callback_before_copy_or_constructor(recovery_fixture, monkeypatch):
    fixture = recovery_fixture
    plan = fixture.plans[0]
    plan_path = fixture.new / 'parented_learning.PLAN.json'
    matched.native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    constructor = Mock()
    monkeypatch.setattr(matched, 'MatchedChild', constructor)
    with pytest.raises(ValueError, match='requires_actual_capacity_callback'):
        matched.initialize(plan_path)
    constructor.assert_not_called()
    assert not (fixture.new / 'common_initial').exists()


def test_recovery_initialized_provenance_cannot_be_omitted(recovery_fixture):
    fixture = recovery_fixture
    with pytest.raises(ValueError, match='bound_recovered_initialization_provenance'):
        matched.verify_initialization_validation(fixture.plans[0], fixture.cohort, {})


def save_checkpoint(directory, plan, *, steps=0, rng=0):
    directory.mkdir(parents=True, exist_ok=False)
    adapter = directory/'adapter'
    adapter.mkdir()
    (adapter/'adapter_model.safetensors').write_bytes(f'CPU synthetic adapter {steps}'.encode())
    (adapter/'adapter_config.json').write_text('{"r": 8}')
    optimizer = directory/'optimizer_rng.pt'
    optimizer.write_text(json.dumps(dict(steps=steps, rng=rng)))
    files = {path.name: matched.native.sha(path) for path in adapter.iterdir()}
    checkpoint = dict(base_sha256=matched.native.BASE_SHA256, adapter_path=str(adapter),
        optimizer_rng_path=str(optimizer), adapter_files=files, adapter_state_sha256=digest(steps),
        optimizer_steps=steps, checkpoint_sha256=dict(adapter=digest(files),
            optimizer=matched.native.sha(optimizer), rng=matched.native.sha(optimizer)),
        experiment=experiment_binding(plan))
    matched.native.write_once(directory/'COMMIT.json', checkpoint)
    NativeChild.verify_checkpoint(checkpoint)
    return checkpoint


def cohort_fixture(root):
    plan = make_plan(root)
    plan.update(context_limit=16384, presentation_version=VERSION, startup_context=None,
        presleep_variant='free_distillation', readout_revision=1, max_sleeps=1)
    plans = [dict(deepcopy(plan), matched_arm=arm, parent_enabled=arm != 'unparented_learning',
        root=str(root/arm), gpu_uuid=f'GPU-CPU-fixture-{index}', physical=index)
        for index, arm in enumerate(matched.ARMS)]
    cohort = matched.cohort_document(plans, root/'common_initial')
    path = root/'COHORT.json'
    matched.native.write_once(path, cohort)
    for plan in plans:
        plan['matched_cohort'] = dict(path=str(path), sha256=matched.native.sha(path))
    return plans, cohort


def test_exact_common_configuration_and_bound_members(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    for plan in plans:
        assert matched.validate_plan(plan) == (plan, cohort)
    for field, value in [('seed', 8), ('context_limit', 32768), ('max_sleeps', 7)]:
        changed = deepcopy(plans)
        changed[1][field] = value
        with pytest.raises(ValueError, match='identical_common'):
            matched.cohort_document(changed, tmp_path/'initial2')
        with pytest.raises(ValueError, match='common_plan_binding'):
            matched.validate_plan(changed[1])
    with pytest.raises(ValueError, match='exact_parent_condition'):
        matched.validate_plan(dict(plans[2], parent_enabled=True))
    with pytest.raises(ValueError, match='cohort_allocation_binding'):
        matched.validate_plan(dict(plans[0], gpu_uuid='GPU-foreign'))
    changed = deepcopy(plans)
    changed[1]['physical'] = changed[0]['physical']
    with pytest.raises(ValueError, match='distinct_lives_and_GPUs'):
        matched.cohort_document(changed, tmp_path/'different_initial')
    with pytest.raises(ValueError, match='immutable_matched_cohort'):
        matched.validate_plan(dict(plans[0], matched_cohort=dict(plans[0]['matched_cohort'], sha256='0'*64)))


def test_cohort_refuses_nested_or_overlapping_roots(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    for initial in [Path(plans[0]['root'])/'initial', tmp_path]:
        with pytest.raises(ValueError, match='shared_initial'):
            matched.cohort_document(plans, initial)
    changed = deepcopy(plans)
    changed[1]['root'] = changed[0]['root']+'/nested'
    with pytest.raises(ValueError, match='nonoverlapping'):
        matched.cohort_document(changed, Path(cohort['initial_directory']))
    with pytest.raises(ValueError, match='canonical_cohort_paths'):
        matched.cohort_document(plans, tmp_path/'unused'/'..'/'initial')
    with pytest.raises(ValueError, match='initial_outside_source_tree'):
        matched.cohort_document(plans, Path(plans[0]['source_root'])/'initial')


def test_common_startup_is_pinned_and_not_a_false_learning_promise(tmp_path):
    plans, unused_cohort = cohort_fixture(tmp_path)
    source = Path(plans[0]['source_root'])
    source.mkdir()
    text = (Path(__file__).resolve().parents[1]/'research_notes/R150_MATCHED_STARTUP_2026-09-16.txt').read_text()
    startup = source/'STARTUP.txt'
    startup.write_text(text)
    for plan in plans:
        plan['birth_prompt'] = text
        plan['startup_context'] = dict(version='R127_STARTUP_V1', path=str(startup), sha256=matched.native.sha(startup))
    cohort_path = tmp_path/'STARTUP_COHORT.json'
    matched.native.write_once(cohort_path, matched.cohort_document(plans, tmp_path/'other_initial'))
    for plan in plans:
        plan['matched_cohort'] = dict(path=str(cohort_path), sha256=matched.native.sha(cohort_path))
        assert matched.validate_plan(plan)[0] == plan
    assert 'weight updates may be enabled or held fixed' in text
    assert 'not an enabled shell' in text
    startup.write_text(text+'unexpected prompt edit')
    with pytest.raises(ValueError, match='pinned_startup_source'):
        matched.validate_plan(plans[0])


def test_matched_validation_rejects_unsupported_legacy_presentation(tmp_path):
    plans, unused_cohort = cohort_fixture(tmp_path)
    for plan in plans:
        with pytest.raises(ValueError, match='matched_plain_presentation_required'):
            matched.validate_plan(dict(plan, presentation_version=None, context_limit=8192))


def test_initial_clone_changes_paths_not_model_or_optimizer_bytes(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    initial = Path(cohort['initial_directory'])
    original = save_checkpoint(initial, plans[0])
    (initial/'unrelated_history.json').write_text('must not be cloned')
    clones = [matched.copy_initial_checkpoint(initial/'COMMIT.json', Path(plan['root'])/'checkpoints/initial')
              for plan in plans]
    for clone in clones:
        assert clone['checkpoint_sha256'] == original['checkpoint_sha256']
        for key in original:
            if key not in ('adapter_path', 'optimizer_rng_path'):
                assert clone[key] == original[key]
        destination = Path(clone['adapter_path']).parent
        assert set(path.name for path in destination.iterdir()) == {
            'adapter', 'optimizer_rng.pt', 'COMMIT.json', 'CLONE_PROVENANCE.json'}
        assert not (destination/'unrelated_history.json').exists()
    with pytest.raises(ValueError, match='new_life_checkpoint_destination'):
        matched.copy_initial_checkpoint(initial/'COMMIT.json', Path(clones[0]['adapter_path']).parent)


@pytest.mark.parametrize('target', ['commit', 'ancestor', 'adapter', 'optimizer', 'adapter_file'])
def test_initial_clone_rejects_symlinks(tmp_path, target):
    plans, cohort = cohort_fixture(tmp_path)
    initial = Path(cohort['initial_directory'])
    original = save_checkpoint(initial, plans[0])
    source_commit = initial/'COMMIT.json'
    if target == 'ancestor':
        linked = tmp_path/'linked'
        linked.symlink_to(initial, target_is_directory=True)
        source_commit = linked/'COMMIT.json'
    else:
        source = {'commit': source_commit, 'adapter': Path(original['adapter_path']),
            'optimizer': Path(original['optimizer_rng_path']),
            'adapter_file': Path(original['adapter_path'])/'adapter_model.safetensors'}[target]
        saved = source.with_name(source.name+'.saved')
        source.rename(saved)
        source.symlink_to(saved, target_is_directory=target == 'adapter')
        if target == 'adapter_file':
            saved.rename(tmp_path/'original_adapter')
            source.unlink()
            source.symlink_to(tmp_path/'original_adapter')
    with pytest.raises(ValueError, match='symlinks|regular_initial|exact_regular_adapter_file'):
        matched.copy_initial_checkpoint(source_commit, tmp_path/'new_clone')


def test_partial_clone_never_publishes_commit_or_retries_over_evidence(tmp_path, monkeypatch):
    plans, cohort = cohort_fixture(tmp_path)
    initial = Path(cohort['initial_directory'])
    save_checkpoint(initial, plans[0])
    destination = tmp_path/'failed_clone'
    monkeypatch.setattr(matched.shutil, 'copyfileobj', Mock(side_effect=OSError('copy failed')))
    with pytest.raises(OSError, match='copy failed'):
        matched.copy_initial_checkpoint(initial/'COMMIT.json', destination)
    assert destination.exists() and not (destination/'COMMIT.json').exists()
    with pytest.raises(ValueError, match='new_life_checkpoint_destination'):
        matched.copy_initial_checkpoint(initial/'COMMIT.json', destination)


def test_clone_rejects_noninitial_optimizer(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    initial = Path(cohort['initial_directory'])
    save_checkpoint(initial, plans[0], steps=1)
    with pytest.raises(ValueError, match='fresh_initial_optimizer_only'):
        matched.copy_initial_checkpoint(initial/'COMMIT.json', tmp_path/'invalid_clone')


def test_saved_boundary_uses_receipt_not_unordered_directory_search(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    plan = plans[0]
    root = Path(plan['root'])
    checkpoint = save_checkpoint(root/'checkpoints/sleep_000001', plan, steps=7)
    stream = SimpleNamespace(sleep_receipts=[dict(checkpoint=checkpoint)],
        model_state_sha256=digest(checkpoint['checkpoint_sha256']))
    save_checkpoint(root/'checkpoints/zzz_partial_future', plan, steps=8)
    assert matched.boundary_checkpoint(stream, root) == checkpoint
    changed = deepcopy(checkpoint)
    changed['optimizer_steps'] += 1
    stream.sleep_receipts = [dict(checkpoint=changed)]
    with pytest.raises(ValueError, match='exact_latest_receipt_COMMIT'):
        matched.boundary_checkpoint(stream, root)
    stream.sleep_receipts = [dict(checkpoint=checkpoint)]
    stream.model_state_sha256 = '0'*64
    with pytest.raises(ValueError, match='latest_receipt_model_state'):
        matched.boundary_checkpoint(stream, root)


def test_birth_plain_context_same_across_arms_and_actual_initial_binding(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    checkpoint = save_checkpoint(Path(cohort['initial_directory']), plans[0])
    states = []
    for plan in plans:
        stream = matched.birth_stream(plan, checkpoint, MatchedStream)
        states.append(stream.checkpoint()['state'])
        assert stream.arm == plan['matched_arm']
        assert stream.model_state_sha256 == digest(checkpoint['checkpoint_sha256'])
    for state in states[1:]:
        assert state['history'] == states[0]['history']
        assert state['presentation'] == states[0]['presentation']
        assert state['rows'] == []


@pytest.mark.parametrize('attribute,value,error', [
    ('context_limit', 32768, 'restored_presentation'),
    ('segment_tokens', 32, 'restored_runtime'),
    ('segments_per_sleep', 8, 'restored_runtime'),
    ('deadline_unix', 0, 'restored_runtime'),
    ('allow_eviction', False, 'restored_runtime'),
    ('presentation', {'version': VERSION, 'system_prompt': 'DIFFERENT', 'birth_prompt': 'DIFFERENT'},
     'restored_presentation'),
])
def test_resume_checks_full_runtime_before_model_load(tmp_path, attribute, value, error):
    plans, cohort = cohort_fixture(tmp_path)
    checkpoint = save_checkpoint(Path(cohort['initial_directory']), plans[0])
    stream = matched.birth_stream(plans[0], checkpoint, MatchedStream)
    matched.verify_stream_plan(stream, plans[0])
    setattr(stream, attribute, value)
    with pytest.raises(ValueError, match=error):
        matched.verify_stream_plan(stream, plans[0])


def test_wall_timer_refuses_expired_nested_and_restores_after_failure(monkeypatch):
    monkeypatch.setattr(matched.time, 'time', lambda: 100)
    with pytest.raises(ValueError, match='before_model_load'):
        with matched.wall_timer(99):
            pytest.fail('expired operation ran')
    monkeypatch.setattr(matched.signal, 'getitimer', lambda kind: (10.0, 0.0))
    with pytest.raises(ValueError, match='no_nested_wall_timer'):
        with matched.wall_timer(101):
            pytest.fail('nested operation ran')
    monkeypatch.setattr(matched.signal, 'getitimer', lambda kind: (0.0, 0.0))
    setter = Mock()
    handlers = Mock(return_value='previous')
    monkeypatch.setattr(matched.signal, 'setitimer', setter)
    monkeypatch.setattr(matched.signal, 'signal', handlers)
    with pytest.raises(RuntimeError, match='model failed'):
        with matched.wall_timer(105):
            raise RuntimeError('model failed')
    assert setter.call_args_list[0].args == (signal.ITIMER_REAL, 5)
    assert setter.call_args_list[-1].args == (signal.ITIMER_REAL, 0)
    assert handlers.call_args_list[-1].args == (signal.SIGALRM, 'previous')


def test_frozen_child_never_trains_or_claims_anchor_exposure():
    child = object.__new__(matched.MatchedChild)
    child.plan = dict(matched_arm='parented_frozen')
    child.optimizer_steps = 0
    child.optimizer = SimpleNamespace(state={})
    child.engine = SimpleNamespace(verify_base=Mock(), model=SimpleNamespace(
        parameters=lambda: [SimpleNamespace(requires_grad=False)]))
    child.adapter_hash = lambda: digest('unchanged')
    receipt = child.sleep([dict(source_sha256=digest('row'))], [], ['unused_anchor'], Mock())
    assert receipt['kind'] == 'FROZEN_CONTROL_BOUNDARY'
    assert receipt['optimizer_steps'] == receipt['child_token_exposures'] == receipt['anchor_token_exposures'] == 0
    assert receipt['configured_anchor_lambda'] == 0.25 and receipt['anchor_mix_applied'] is False
    child.optimizer.state['unexpected_moment'] = 1
    with pytest.raises(ValueError, match='never_updates_optimizer'):
        child.sleep([{}], [], [], Mock())


class FakeTensor:
    def __init__(self, values):
        self.values = list(values)

    def tolist(self):
        return self.values


def test_loaded_initial_checks_adapter_AdamW_parameter_order_and_all_RNG(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    checkpoint = save_checkpoint(Path(cohort['initial_directory']), plans[0])
    cpu_rng, cuda_rng = FakeTensor([3, 4]), FakeTensor([5, 6])
    optimizer = dict(state={}, param_groups=[dict(params=[0, 1], lr=3e-5)])
    payload = dict(optimizer_steps=0, optimizer=deepcopy(optimizer), parameter_names=['left', 'right'],
        cpu_rng=cpu_rng, cuda_rng=[cuda_rng], python_rng=random.getstate())
    child = SimpleNamespace(verify_checkpoint=NativeChild.verify_checkpoint, optimizer_steps=0,
        optimizer=SimpleNamespace(state={}, state_dict=lambda: optimizer),
        parameters={'left': None, 'right': None}, adapter_hash=lambda: checkpoint['adapter_state_sha256'],
        torch=SimpleNamespace(load=lambda *args, **kwargs: payload,
            equal=lambda actual, expected: actual.tolist() == expected.tolist(),
            get_rng_state=lambda: cpu_rng, cuda=SimpleNamespace(get_rng_state_all=lambda: [cuda_rng])))
    observed = matched.verify_loaded_initial(child, checkpoint)
    assert observed['optimizer_state_entries'] == 0 and observed['parameter_count'] == 2
    for field, value, error in [('parameter_names', ['right', 'left'], 'parameter_order'),
                              ('cpu_rng', FakeTensor([99]), 'CPU_RNG'),
                              ('cuda_rng', [FakeTensor([99])], 'single_GPU_RNG'),
                              ('python_rng', random.Random(903).getstate(), 'python_RNG'),
                              ('optimizer_steps', 1, 'AdamW_state')]:
        saved = payload[field]
        payload[field] = value
        with pytest.raises(ValueError, match=error):
            matched.verify_loaded_initial(child, checkpoint)
        payload[field] = saved
    child.adapter_hash = lambda: digest('wrong adapter')
    with pytest.raises(ValueError, match='initial_adapter'):
        matched.verify_loaded_initial(child, checkpoint)


class SyntheticRunnerChild:
    def __init__(self, plan, checkpoint=None):
        self.plan = plan
        self.optimizer_steps = checkpoint['optimizer_steps'] if checkpoint else 0
        self.engine = SimpleNamespace(runtime={'fixture': 'CPU-only'})
        self.tokenizer = object()
        self.generated = 0

    def adapter_hash(self):
        return digest(self.optimizer_steps)

    def count_tokens(self, messages):
        return sum(len(message['content'].split())+4 for message in messages)

    def generate(self, messages, **kwargs):
        self.generated += 1
        return dict(raw='A synthetic observation worth retaining.', token_ids=[17, 19, 2],
            terminal=True, truncated=False)

    def checkpoint(self, directory):
        return save_checkpoint(directory, self.plan, steps=self.optimizer_steps, rng=self.generated)

    def sleep(self, new_rows, old_rows, anchors, record):
        before = self.adapter_hash()
        if self.plan['matched_arm'] == 'parented_frozen':
            return dict(kind='FROZEN_CONTROL_BOUNDARY', optimizer_steps=0, cumulative_optimizer_steps=0,
                before_adapter_sha256=before, after_adapter_sha256=before, frozen_base_verified=True,
                child_token_exposures=0, anchor_token_exposures=0, presentations=[])
        self.optimizer_steps += 2
        return dict(optimizer_steps=2, total_optimizer_steps=self.optimizer_steps,
            before_adapter_sha256=before, after_adapter_sha256=self.adapter_hash(), frozen_base_verified=True)


@pytest.mark.parametrize('arm', matched.ARMS)
def test_runner_same_generation_compaction_boundary_and_readout_isolation(tmp_path, monkeypatch, arm):
    plans, cohort = cohort_fixture(tmp_path)
    plan = next(plan for plan in plans if plan['matched_arm'] == arm)
    initial = Path(cohort['initial_directory'])
    save_checkpoint(initial, plans[0])
    observation = {'fixture': 'same synthetic state'}
    matched.native.write_once(initial/'INITIALIZED.json', dict(cohort_sha256=plan['matched_cohort']['sha256'],
        checkpoint_commit_sha256=matched.native.sha(initial/'COMMIT.json'), observed_initial_state=observation))
    plan_path = tmp_path/f'{arm}.json'
    matched.native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    monkeypatch.setattr(matched, 'MatchedChild', SyntheticRunnerChild)
    monkeypatch.setattr(matched, 'verify_loaded_initial', lambda child, checkpoint: observation)
    monkeypatch.setattr('gpu.orch_r107_base_anchors_inventory.build_inventory', lambda *args: ([], {'fixture': True}))
    readouts = []

    def synthetic_readout(child, actual_plan_path, checkpoint, cycle):
        readouts.append(cycle)
        output = Path(plan['root'])/'readouts'/f'{cycle:06d}'
        output.mkdir(parents=True)
        (output/'CPU_CANARY.txt').write_text('SEALED_EVAL_CANARY_NOT_A_REAL_TASK')
        matched.native.write_once(output.parent/f'{matched.native.readout_name(plan, cycle)}_DISPATCH.json',
            dict(cycle=cycle, checkpoint_sha256=matched.native.sha(Path(checkpoint['adapter_path']).parent/'COMMIT.json'),
                 parent_present=False, history_shared=False))

    monkeypatch.setattr(matched.native, 'fresh_readout', synthetic_readout)
    matched.run(plan_path)
    with MatchedJournal(Path(plan['root'])/'stream', arm=arm,
                        cohort_sha256=plan['matched_cohort']['sha256']) as journal:
        latest = journal.latest_checkpoint()
    state = latest['document']['state']
    assert len(state['rows']) == 3 and state['sleep_frontier'] == 3
    assert len(state['sleep_receipts']) == 1 and readouts == [0, 1]
    assert 'SEALED_EVAL_CANARY' not in json.dumps(state)
    assert all(row['actor'] == 'child' and row['split'] == 'TRAIN' for row in state['rows'])
    assert state['sleep_receipts'][0]['optimizer_steps'] == (0 if arm == 'parented_frozen' else 2)
    stream = MatchedStream.restore(latest['document'], expected_sha256=latest['expected_sha256'],
        expected_arm=arm, expected_cohort_sha256=plan['matched_cohort']['sha256'])
    assert matched.boundary_checkpoint(stream, Path(plan['root'])) == state['sleep_receipts'][-1]['checkpoint']
    monkeypatch.setattr(SyntheticRunnerChild, 'generate', Mock(side_effect=AssertionError('budget exceeded')))
    matched.run(plan_path, resume=True)
    with MatchedJournal(Path(plan['root'])/'stream', arm=arm,
                        cohort_sha256=plan['matched_cohort']['sha256']) as journal:
        assert journal.latest_checkpoint()['document']['state'] == state
    assert readouts == [0, 1]


def test_initializer_is_bound_once_and_never_generates(tmp_path, monkeypatch):
    plans, cohort = cohort_fixture(tmp_path)
    plan = plans[0]
    plan_path = tmp_path/'INITIALIZER_PLAN.json'
    matched.native.write_once(plan_path, plan)
    factory = Mock()
    monkeypatch.setattr(matched, 'MatchedChild', factory)
    monkeypatch.delenv('R125_ADMISSION_PLAN_SHA256', raising=False)
    monkeypatch.delenv('R150_COHORT_SHA256', raising=False)
    with pytest.raises(ValueError, match='admitted_plan_environment'):
        matched.initialize(plan_path)
    assert not factory.called
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    child = SyntheticRunnerChild(plan)
    child.native = SimpleNamespace(process_identity=lambda: {'fixture': 'CPU-only'})
    child.generate = Mock(side_effect=AssertionError('initializer generated'))
    factory.return_value = child
    monkeypatch.setattr(matched, 'verify_loaded_initial', lambda *args: {'fixture': 'checked'})
    assert matched.initialize(plan_path) == {'fixture': 'checked'}
    receipt = matched.native.read(Path(cohort['initial_directory'])/'INITIALIZED.json')
    assert receipt['generation_calls'] == receipt['optimizer_updates'] == 0
    assert receipt['cohort_sha256'] == plan['matched_cohort']['sha256']
    child.generate.assert_not_called()
    with pytest.raises(ValueError, match='never_recreated'):
        matched.initialize(plan_path)
    assert factory.call_count == 1


def test_resume_unresolved_readout_refuses_model_construction(tmp_path, monkeypatch):
    plans, cohort = cohort_fixture(tmp_path)
    plan = plans[0]
    initial = Path(cohort['initial_directory'])
    save_checkpoint(initial, plan)
    checkpoint = matched.copy_initial_checkpoint(initial/'COMMIT.json', Path(plan['root'])/'checkpoints/initial')
    matched.native.write_once(initial/'INITIALIZED.json', dict(cohort_sha256=plan['matched_cohort']['sha256'],
        checkpoint_commit_sha256=matched.native.sha(initial/'COMMIT.json')))
    plan_path = tmp_path/'RESUME_PLAN.json'
    matched.native.write_once(plan_path, plan)
    stream = matched.birth_stream(plan, checkpoint, MatchedStream)
    with MatchedJournal(Path(plan['root'])/'stream', arm=plan['matched_arm'],
        cohort_sha256=plan['matched_cohort']['sha256'], create=True) as journal:
        journal.record('COMMITTED', dict(kind='BIRTH', state=stream.checkpoint()))
    location = readout_custody.paths(plan, 0)['dispatch']
    location.parent.mkdir()
    location.write_text('{"fixture": "unreconciled owned readout process"}')
    factory = Mock(side_effect=AssertionError('model loaded before readout cleanup'))
    monkeypatch.setattr(matched, 'MatchedChild', factory)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    with pytest.raises(ValueError, match='readout_custody_unresolved_before_model_load'):
        matched.run(plan_path, resume=True)
    factory.assert_not_called()


@pytest.mark.parametrize('arm', matched.ARMS)
@pytest.mark.parametrize('resume', [False, True])
@pytest.mark.parametrize('field,value', [('bounded_comparison', {}),
    ('bounded_comparison.exact_rng', False), ('runtime_sha256', '0'*64),
    ('loss_tolerance.atol', 999), ('maximum_shape.free_after_bytes', float('inf'))])
def test_invalid_rehashed_capacity_proof_blocks_every_arm_before_constructor(tmp_path, monkeypatch, arm, resume, field, value):
    from test_orch_r151_memory_probe import changed_proof

    initial_plan, cohort, initialized = changed_proof(tmp_path, field, value)
    plan = dict(initial_plan, matched_arm=arm, **cohort['members'][arm])
    initial = Path(cohort['initial_directory'])
    initialized.update(cohort_sha256=plan['matched_cohort']['sha256'],
        checkpoint_commit_sha256=matched.native.sha(initial/'COMMIT.json'))
    matched.native.write_once(initial/'INITIALIZED.json', initialized)
    plan_path = tmp_path/f'{arm}.json'
    matched.native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    factory = Mock(side_effect=AssertionError('constructor ran before capacity validation'))
    monkeypatch.setattr(matched, 'MatchedChild', factory)
    with pytest.raises(ValueError, match='capacity'):
        matched.run(plan_path, resume=resume)
    factory.assert_not_called()
    assert not Path(plan['root']).exists()
