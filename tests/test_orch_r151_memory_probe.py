"""CPU contracts for admitted memory validation, not a real-model proof."""

from copy import deepcopy
from contextlib import nullcontext
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r150_matched_native as matched
from gpu import orch_r151_memory_probe as probe
from gpu.orch_r145_suffix_loss import loss_window
from test_orch_r150_matched_native import cohort_fixture, save_checkpoint, SyntheticRunnerChild


class Tokenizer:
    all_special_ids = [0, 1, 2]

    def encode(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return [17, 21, 35]


@pytest.mark.parametrize('inputs,targets', [(2048, 128), (16384, 512), (17, 1)])
def test_synthetic_capacity_shape_is_exact_and_causally_masked(inputs, targets):
    sample = probe.shape_sample(Tokenizer(), inputs, targets)
    assert len(sample.input_ids) == len(sample.labels) == inputs
    assert sample.labels[:inputs-targets] == (-100,)*(inputs-targets)
    assert sample.input_ids[-targets:] == sample.labels[-targets:] == sample.target_ids
    assert loss_window(sample)['logits_to_keep'] == targets+1


@pytest.mark.parametrize('inputs,targets', [(0, 1), (3, 3), (4, 0), (True, 1), (4, True)])
def test_invalid_capacity_shape_rejected(inputs, targets):
    with pytest.raises(ValueError, match='bounded_capacity_shape'):
        probe.shape_sample(Tokenizer(), inputs, targets)


def test_special_tokens_are_not_synthetic_inputs():
    tokenizer = Tokenizer()
    tokenizer.all_special_ids = [17]
    with pytest.raises(ValueError, match='ordinary_synthetic'):
        probe.shape_sample(tokenizer, 20, 5)


def proof_fixture(tmp_path):
    plans, cohort = cohort_fixture(tmp_path)
    for member in plans:
        member.update(initialization_validation_schema=probe.SCHEMA, segment_tokens=512)
    cohort = matched.cohort_document(plans, cohort['initial_directory'])
    cohort_path = tmp_path/'COHORT.json'
    cohort_path.write_text(json.dumps(cohort))
    for member in plans:
        member['matched_cohort']['sha256'] = matched.native.sha(cohort_path)
    plan = plans[0]
    save_checkpoint(Path(cohort['initial_directory']), plan)
    directory = Path(cohort['initial_directory'])/'capacity_validation'
    directory.mkdir(parents=True)
    path = directory/'RESULT.json'
    memory = dict(full_input_tokens=2048, target_tokens=128, logits_tokens=2048,
        peak_allocated_bytes=1024**3, peak_reserved_bytes=2*1024**3,
        free_after_bytes=4*1024**3, total_bytes=8*1024**3)
    proof = dict(schema=probe.SCHEMA, status='PASS', state_restored=True, restoration_status='VERIFIED', optimizer_updates=0,
        generation_calls=0, stream_data_written=False, synthetic_shape_only=True, scientific_evaluation=False,
        plan_sha256='a'*64, context_limit=plan['context_limit'], segment_tokens=plan['segment_tokens'],
        runtime_sha256=probe.RUNTIME_SHA256, prior_GPU_proof_sha256=probe.PRIOR_GPU_SHA256,
        loss_tolerance=deepcopy(probe.capacity.LOSS_TOLERANCE), gradient_tolerance=deepcopy(probe.capacity.GRAD_TOLERANCE),
        anchor_receipt_sha256='b'*64, exact_learning_trajectory_claim=False,
        minimum_headroom_bytes=probe.MIN_HEADROOM_BYTES,
        bounded_comparison=dict(original_losses=[1.0]*5, suffix_losses=[1.0]*5,
            original_memory=memory, suffix_memory=dict(memory, logits_tokens=129),
            exact_rng=True, max_gradient_absolute_error=0.0),
        maximum_shape=dict(memory, full_input_tokens=16384, target_tokens=512, logits_tokens=513),
        maximum_losses=[1.0]*5, started_unix=1000, deadline_unix=1300, measurement_finished_unix=1010,
        finished_unix=1011, elapsed_seconds=11, cleanup_elapsed_seconds=1,
        work_budget_seconds=300, cleanup_allowance_seconds=0)
    matched.native.write_once(path, proof)
    initialized = dict(source_plan_sha256='a'*64, initialization_validation=dict(
        status='PASS', schema=probe.SCHEMA, path=str(path), sha256=matched.native.sha(path)))
    return plan, cohort, proof, initialized, path


def test_required_capacity_receipt_bound_to_common_initialization(tmp_path):
    plan, cohort, unused_proof, initialized, unused_path = proof_fixture(tmp_path)
    matched.verify_initialization_validation(plan, cohort, initialized)
    for change in ({}, {'status': 'NOT_REQUESTED'}, {'status': 'FAIL'}, dict(initialized['initialization_validation'], sha256='0'*64)):
        changed = dict(initialized, initialization_validation=change)
        with pytest.raises(ValueError, match='required_initial_GPU|bound_initial_capacity'):
            matched.verify_initialization_validation(plan, cohort, changed)


@pytest.mark.parametrize('field,value', [('state_restored', False), ('optimizer_updates', 1),
    ('optimizer_updates', False), ('generation_calls', 1), ('stream_data_written', True),
    ('scientific_evaluation', True), ('synthetic_shape_only', False), ('context_limit', 32768),
    ('segment_tokens', 123), ('plan_sha256', 'b'*64), ('status', 'FAIL')])
def test_inadequate_capacity_proof_not_adopted_even_with_matching_hash(tmp_path, field, value):
    plan, cohort, proof, initialized, path = proof_fixture(tmp_path)
    proof[field] = value
    path.write_text(__import__('json').dumps(proof))
    initialized['initialization_validation']['sha256'] = matched.native.sha(path)
    with pytest.raises(ValueError, match='successful_same_initial_configuration'):
        matched.verify_initialization_validation(plan, cohort, initialized)


@pytest.mark.parametrize('field,value', [('full_input_tokens', 15935), ('target_tokens', 15),
    ('logits_tokens', 15), ('free_after_bytes', 2*1024**3-1)])
def test_actual_maximum_shape_and_headroom_required(tmp_path, field, value):
    plan, cohort, proof, initialized, path = proof_fixture(tmp_path)
    proof['maximum_shape'][field] = value
    path.write_text(__import__('json').dumps(proof))
    initialized['initialization_validation']['sha256'] = matched.native.sha(path)
    with pytest.raises(ValueError, match='actual_maximum_shape'):
        matched.verify_initialization_validation(plan, cohort, initialized)


def test_callback_runs_after_save_before_publication_and_failure_preserves_partial(tmp_path, monkeypatch):
    plans, cohort = cohort_fixture(tmp_path)
    plan = plans[0]
    plan_path = tmp_path/'PLAN.json'
    matched.native.write_once(plan_path, plan)
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    child = SyntheticRunnerChild(plan)
    child.native = SimpleNamespace(process_identity=lambda: {'fixture': True})
    monkeypatch.setattr(matched, 'MatchedChild', lambda actual: child)
    verify = Mock(return_value={'fixture': True})
    monkeypatch.setattr(matched, 'verify_loaded_initial', verify)
    initial = Path(cohort['initial_directory'])

    def failed_probe(actual_child, actual_plan, actual_directory):
        assert actual_child is child and actual_plan == plan_path and actual_directory == initial
        assert (initial/'COMMIT.json').is_file() and not (initial/'INITIALIZED.json').exists()
        raise ValueError('capacity failure')

    with pytest.raises(ValueError, match='capacity failure'):
        matched.initialize(plan_path, validate_child=failed_probe)
    assert (initial/'COMMIT.json').exists() and not (initial/'INITIALIZED.json').exists()
    verify.assert_not_called()


def test_only_designated_admitted_device_can_enter_probe(tmp_path):
    plans, unused_cohort = cohort_fixture(tmp_path)
    for plan in plans:
        child = SimpleNamespace(plan=plan)
        with pytest.raises(ValueError, match='designated_node5_or_node4_initializer'):
            probe.validate_environment(child, tmp_path/'unused')


def designated_plan(node4=True):
    return dict(matched_arm='parented_learning', physical=5 if node4 else 0,
        gpu_uuid='GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30' if node4 else 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
        source_root='/localhome/local-rohing/orch_r158_matched_node4_fixture/source')


@pytest.mark.parametrize('node4,hostname,expected', [
    (True, 'a4u8g-0105', 'R158_NODE4'),
    (False, 'ipp2-ovx-p1-10', 'R151_NODE5'),
])
def test_exact_host_device_initializer_profiles(node4, hostname, expected):
    assert probe.initializer_profile(designated_plan(node4), hostname) == expected


@pytest.mark.parametrize('field,value', [
    ('physical', 0), ('physical', 6), ('physical', 7), ('physical', True),
    ('gpu_uuid', 'GPU-other'), ('matched_arm', 'parented_frozen'),
    ('matched_arm', 'unparented_learning'), ('source_root', '/tmp/source'),
    ('source_root', '/localhome/local-rohing/other/source'),
    ('source_root', '/localhome/local-rohing/orch_r158_matched_node4_fixture/elsewhere'),
])
def test_wrong_node4_initializer_profile_rejected(field, value):
    plan = designated_plan()
    plan[field] = value
    with pytest.raises(ValueError, match='designated_node5_or_node4_initializer'):
        probe.initializer_profile(plan, 'a4u8g-0105')


@pytest.mark.parametrize('node4,hostname', [
    (True, 'ipp2-ovx-p1-10'), (False, 'a4u8g-0105'),
    (True, 'other'), (False, 'other'),
])
def test_initializer_host_cannot_cross_profiles(node4, hostname):
    with pytest.raises(ValueError, match='designated_node5_or_node4_initializer'):
        probe.initializer_profile(designated_plan(node4), hostname)


def test_actual_node4_environment_still_requires_bound_admission(tmp_path, monkeypatch):
    plan_path = tmp_path / 'PLAN.json'
    plan_path.write_text('{}')
    child = SimpleNamespace(plan=designated_plan())
    monkeypatch.setattr(probe.socket, 'gethostname', lambda: 'a4u8g-0105')
    monkeypatch.delenv('R125_ADMISSION_PLAN_SHA256', raising=False)
    with pytest.raises(ValueError, match='actual_admitted_initialization'):
        probe.validate_environment(child, plan_path)


MEMORY_FIELDS = ('full_input_tokens', 'target_tokens', 'logits_tokens', 'peak_allocated_bytes',
                 'peak_reserved_bytes', 'free_after_bytes', 'total_bytes')
MEMORY_PATHS = ('bounded_comparison.original_memory', 'bounded_comparison.suffix_memory', 'maximum_shape')
TIMING_FIELDS = ('started_unix', 'deadline_unix', 'measurement_finished_unix', 'finished_unix',
                 'elapsed_seconds', 'cleanup_elapsed_seconds', 'work_budget_seconds', 'cleanup_allowance_seconds')
REQUIRED_PROOF_PATHS = (
    'schema', 'status', 'state_restored', 'restoration_status', 'optimizer_updates', 'generation_calls', 'stream_data_written',
    'synthetic_shape_only', 'scientific_evaluation', 'plan_sha256', 'context_limit', 'segment_tokens',
    'runtime_sha256', 'prior_GPU_proof_sha256', 'loss_tolerance', 'gradient_tolerance',
    'loss_tolerance.atol', 'loss_tolerance.rtol', 'gradient_tolerance.atol', 'gradient_tolerance.rtol',
    'anchor_receipt_sha256', 'exact_learning_trajectory_claim', 'minimum_headroom_bytes', 'bounded_comparison',
    'bounded_comparison.original_losses', 'bounded_comparison.suffix_losses', 'bounded_comparison.exact_rng',
    'bounded_comparison.max_gradient_absolute_error', 'maximum_losses', *MEMORY_PATHS, *TIMING_FIELDS,
    *(f'{path}.{field}' for path in MEMORY_PATHS for field in MEMORY_FIELDS))


def changed_proof(tmp_path, path, value=None, *, remove=False):
    plan, cohort, proof, initialized, receipt_path = proof_fixture(tmp_path)
    container = proof
    components = path.split('.')
    for component in components[:-1]:
        container = container[component]
    if remove:
        del container[components[-1]]
    else:
        container[components[-1]] = value
    receipt_path.write_text(json.dumps(proof))
    initialized['initialization_validation']['sha256'] = matched.native.sha(receipt_path)
    return plan, cohort, initialized


@pytest.mark.parametrize('path', REQUIRED_PROOF_PATHS)
def test_every_required_proof_field_is_mandatory_after_rehash(tmp_path, path):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, remove=True))


@pytest.mark.parametrize('path,value', [
    ('runtime_sha256', '0'*64), ('prior_GPU_proof_sha256', '1'*64),
    ('schema', 'OTHER_SCHEMA'), ('restoration_status', 'FAILED'), ('restoration_status', 'UNVERIFIED'),
    ('measurement_error', {'error': 'failed'}), ('cleanup_errors', []), ('acceptance_error', {}),
    ('error', 'failed'), ('error_type', 'ValueError'), ('generation_calls', False),
    ('loss_tolerance', {'atol': 999, 'rtol': 999}), ('gradient_tolerance', {'atol': 999, 'rtol': 999}),
    ('loss_tolerance', []), ('gradient_tolerance.rtol', float('nan')),
    ('bounded_comparison', None), ('bounded_comparison', []), ('bounded_comparison.exact_rng', False),
    ('bounded_comparison.exact_rng', 1), ('bounded_comparison.suffix_losses', [2.0]*5),
    ('bounded_comparison.original_memory.full_input_tokens', 128),
    ('bounded_comparison.original_memory.target_tokens', 129),
    ('bounded_comparison.original_memory.logits_tokens', 129),
    ('bounded_comparison.suffix_memory.full_input_tokens', 129),
    ('bounded_comparison.suffix_memory.target_tokens', 127),
    ('bounded_comparison.suffix_memory.logits_tokens', 2048),
    ('bounded_comparison.suffix_memory.peak_allocated_bytes', 2*1024**3),
    ('bounded_comparison.suffix_memory.total_bytes', 9*1024**3),
    ('maximum_shape.total_bytes', 9*1024**3), ('maximum_shape.free_after_bytes', 9*1024**3),
    ('maximum_shape.peak_allocated_bytes', 3*1024**3), ('maximum_shape.peak_reserved_bytes', 9*1024**3),
    ('maximum_shape', None), ('minimum_headroom_bytes', 1), ('minimum_headroom_bytes', False),
    ('anchor_receipt_sha256', 'g'*64), ('exact_learning_trajectory_claim', True),
    ('work_budget_seconds', 301), ('cleanup_allowance_seconds', 1), ('deadline_unix', 1301),
    ('finished_unix', 1300), ('measurement_finished_unix', 999), ('measurement_finished_unix', 1012),
    ('elapsed_seconds', 12), ('cleanup_elapsed_seconds', 2),
])
def test_contradictory_capacity_proof_is_refused_after_rehash(tmp_path, path, value):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, value))


@pytest.mark.parametrize('path', [f'{path}.{field}' for path in MEMORY_PATHS for field in MEMORY_FIELDS])
@pytest.mark.parametrize('value', [None, True, -1, 1.5, '2048', float('nan'), float('inf'), float('-inf')])
def test_memory_counts_are_nonnegative_integers_after_rehash(tmp_path, path, value):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, value))


@pytest.mark.parametrize('path', [f'{path}.{field}' for path in MEMORY_PATHS
                                for field in ('peak_allocated_bytes', 'peak_reserved_bytes', 'total_bytes')])
def test_measured_peaks_and_device_capacity_are_positive(tmp_path, path):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, 0))


@pytest.mark.parametrize('path', ['bounded_comparison.original_losses', 'bounded_comparison.suffix_losses', 'maximum_losses'])
@pytest.mark.parametrize('value', [None, {}, [], [1.0]*4, [1.0]*6, [True]*5, ['1']*5,
                                 [1.0]*4+[float('nan')], [1.0]*4+[float('inf')], [float('-inf')]*5, [10**400]*5])
def test_all_five_losses_are_finite_numbers_after_rehash(tmp_path, path, value):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, value))


@pytest.mark.parametrize('value', [None, True, '0', -1, float('nan'), float('inf'), float('-inf'), 10**400])
def test_gradient_error_must_be_finite_nonnegative_numeric_evidence(tmp_path, value):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, 'bounded_comparison.max_gradient_absolute_error', value))


def test_gradient_scalar_is_not_an_absolute_only_equivalence_gate(tmp_path):
    matched.verify_initialization_validation(*changed_proof(tmp_path, 'bounded_comparison.max_gradient_absolute_error', 0.001))


@pytest.mark.parametrize('path', TIMING_FIELDS)
@pytest.mark.parametrize('value', [None, True, '1000', -1, float('nan'), float('inf')])
def test_timing_evidence_is_finite_typed_and_bounded(tmp_path, path, value):
    with pytest.raises(ValueError):
        matched.verify_initialization_validation(*changed_proof(tmp_path, path, value))


class ProbeTensor:
    def __init__(self, values, backward=None):
        self.values = deepcopy(values)
        self.backward_action = backward
        self.grad = None
        self.requires_grad = False

    def clone(self):
        return ProbeTensor(self.values)

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return deepcopy(self.values)

    def __getitem__(self, slices):
        rows, columns = slices
        return ProbeTensor([row[columns] for row in self.values[rows]])

    def __float__(self):
        return float(self.values)

    def __bool__(self):
        return bool(self.values)

    def __mul__(self, weight):
        return ProbeTensor(self.values*weight, self.backward_action)

    def __sub__(self, other):
        return ProbeTensor(self.values-other.values)

    def abs(self):
        return ProbeTensor(abs(self.values))

    def max(self):
        return self

    def all(self):
        return self

    def backward(self):
        self.backward_action()

    def copy_(self, other):
        self.values = deepcopy(other.values)

    def requires_grad_(self, flag):
        self.requires_grad = flag


def capacity_harness(tmp_path, monkeypatch, *, late=None, failure=None, forward_failure=False):
    plans, cohort = cohort_fixture(tmp_path)
    for plan in plans:
        plan.update(segment_tokens=512, initialization_validation_schema=probe.SCHEMA, hard_end_unix=9999)
    cohort = matched.cohort_document(plans, cohort['initial_directory'])
    cohort_path = tmp_path/'COHORT.json'
    cohort_path.write_text(json.dumps(cohort))
    plan = plans[0]
    plan['matched_cohort']['sha256'] = matched.native.sha(cohort_path)
    plan_path = tmp_path/'PLAN.json'
    matched.native.write_once(plan_path, plan)
    clock = SimpleNamespace(now=1000)
    monkeypatch.setattr(probe.time, 'time', lambda: clock.now)
    monkeypatch.setattr(probe, 'validate_environment', Mock())
    child = SyntheticRunnerChild(plan)
    child.tokenizer = Tokenizer()
    child.parameters = {'left': ProbeTensor(2.0), 'right': ProbeTensor(3.0)}
    child.parameters['right'].requires_grad = True
    base = ProbeTensor(4.0)
    parameters = [*child.parameters.values(), base]
    leaf = SimpleNamespace(training=True)
    calls = []
    state = dict(optimizer=dict(state={}, param_groups=[dict(params=[0, 1], lr=3e-5)]), cpu=[3, 4], cuda=[5, 6])
    original = deepcopy(state)
    python_rng = random.getstate()

    class Model:
        training = False

        def parameters(self):
            return parameters

        def named_parameters(self):
            return [*child.parameters.items(), ('base', base)]

        def modules(self):
            return [self, leaf]

        def train(self):
            self.training = leaf.training = True

        def __call__(self, **arguments):
            calls.append(arguments)
            random.random()
            state['cpu'][0] += 1
            state['cuda'][0] += 1
            if late == 'final_forward' and len(calls) == 15:
                clock.now = 1301
            if forward_failure and len(calls) == 2:
                child.parameters['left'].values = 99
                state['optimizer']['param_groups'][0]['lr'] = 99
                raise ValueError('injected forward failure')

            def backward():
                for parameter in child.parameters.values():
                    parameter.grad = ProbeTensor(0.5)

            return SimpleNamespace(loss=ProbeTensor(1.0, backward))

    def zero_grad(**kwargs):
        if failure == 'zero_grad' and len(calls) == 15:
            raise RuntimeError('injected zero_grad failure')
        for parameter in parameters:
            parameter.grad = None

    def load_optimizer(saved):
        if failure == 'optimizer':
            raise RuntimeError('injected optimizer failure')
        state['optimizer'] = deepcopy(saved)

    def restore_cpu(saved):
        if failure == 'RNG' and len(calls) > 0 and (forward_failure or len(calls) == 15):
            raise RuntimeError('injected RNG failure')
        state['cpu'] = saved.tolist()

    def empty_cache():
        if failure == 'empty_cache' and len(calls) == 15:
            raise RuntimeError('injected empty_cache failure')

    def verify_base():
        if late == 'verification':
            clock.now = 1301
        if failure == 'verify_base':
            raise RuntimeError('injected verify_base failure')

    def assert_close(actual, expected, **tolerance):
        assert actual.values == expected.values
        if late == 'comparison':
            clock.now = 1301

    child.torch = SimpleNamespace(Tensor=ProbeTensor, tensor=lambda values, **kwargs: ProbeTensor(values),
        long='long', bfloat16='bfloat16', ones_like=lambda value: value,
        autocast=lambda **kwargs: nullcontext(), no_grad=nullcontext,
        isfinite=lambda value: ProbeTensor(math.isfinite(float(value))),
        get_rng_state=lambda: ProbeTensor(state['cpu']), set_rng_state=restore_cpu,
        cuda=SimpleNamespace(get_rng_state_all=lambda: [ProbeTensor(state['cuda'])],
            set_rng_state_all=lambda saved: state.update(cuda=saved[0].tolist()), synchronize=Mock(),
            empty_cache=empty_cache, reset_peak_memory_stats=Mock(),
            mem_get_info=lambda: (4*1024**3, 8*1024**3), max_memory_allocated=lambda: 1024**3,
            max_memory_reserved=lambda: 2*1024**3), testing=SimpleNamespace(assert_close=Mock(side_effect=assert_close)))
    child.engine = SimpleNamespace(model=Model(), verify_base=Mock(side_effect=verify_base))
    child.optimizer = SimpleNamespace(state={}, state_dict=lambda: deepcopy(state['optimizer']),
        zero_grad=zero_grad, load_state_dict=load_optimizer, step=Mock(side_effect=AssertionError('optimizer step')))
    child.adapter_hash = lambda: matched.digest({name: parameter.values for name, parameter in child.parameters.items()})
    child.check = Mock()
    child.generate = Mock(side_effect=AssertionError('generation'))
    child.native = SimpleNamespace(process_identity=lambda: {'fixture': 'CPU-only'})
    if failure == 'adapter':
        child.parameters['left'].copy_ = Mock(side_effect=RuntimeError('injected adapter failure'))
    if failure == 'verify_restored':
        child.adapter_hash = lambda: matched.digest('changed' if calls else 'original')
    if late == 'synchronization':
        def synchronize():
            if len(calls) == 15:
                clock.now = 1301
        child.torch.cuda.synchronize = synchronize
    if late == 'snapshot':
        def adapter_hash():
            clock.now = 1301
            return matched.digest('synthetic adapter')
        child.adapter_hash = adapter_hash

    def inventory(*args):
        if late == 'preparation':
            clock.now = 1301
        return ({family: [dict(encoded=probe.shape_sample(child.tokenizer, 20, 5))]
                 for family in ('code', 'math', 'simulated_tools', 'concise_answer')}, {'fixture': 'synthetic'})

    monkeypatch.setattr('gpu.orch_r107_base_anchors_inventory.build_inventory', inventory)
    monkeypatch.setattr(matched, 'MatchedChild', lambda actual_plan: child)
    monkeypatch.setattr(matched, 'wall_timer', lambda deadline: nullcontext())
    monkeypatch.setattr(matched, 'verify_loaded_initial', Mock(return_value={'fixture': 'CPU-only'}))
    monkeypatch.setenv('R125_ADMISSION_PLAN_SHA256', matched.native.sha(plan_path))
    monkeypatch.setenv('R150_COHORT_SHA256', plan['matched_cohort']['sha256'])
    return SimpleNamespace(child=child, plan_path=plan_path, initial=Path(cohort['initial_directory']),
        clock=clock, calls=calls, state=state, original=original, python_rng=python_rng, base=base, leaf=leaf)


def assert_restored(harness):
    assert harness.state == harness.original
    assert random.getstate() == harness.python_rng
    assert harness.child.parameters['left'].values == 2.0 and harness.child.parameters['right'].values == 3.0
    assert harness.child.parameters['left'].requires_grad is False
    assert harness.child.parameters['right'].requires_grad is True
    assert harness.base.requires_grad is False and harness.base.grad is None
    assert all(parameter.grad is None for parameter in harness.child.parameters.values())
    assert harness.child.engine.model.training is False and harness.leaf.training is True
    harness.child.optimizer.step.assert_not_called()
    harness.child.generate.assert_not_called()


def test_actual_probe_control_flow_restores_state_and_publishes_complete_proof(tmp_path, monkeypatch):
    harness = capacity_harness(tmp_path, monkeypatch)
    matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == 'PASS' and proof['state_restored'] is True
    assert proof['restoration_status'] == 'VERIFIED' and len(proof['completed_passes']) == 3
    assert len(harness.calls) == 15
    for index, inputs, logits in [(0, 2048, None), (5, 2048, 129), (10, 16384, 513)]:
        call = harness.calls[index]
        assert len(call['input_ids'].values[0]) == inputs
        assert call.get('logits_to_keep') == logits
        assert len(call['labels'].values[0]) == (logits or inputs)
    assert all(call['use_cache'] is False for call in harness.calls)
    assert harness.child.torch.testing.assert_close.call_count == 3
    assert_restored(harness)


@pytest.mark.parametrize('late', ['preparation', 'snapshot', 'comparison', 'final_forward', 'synchronization', 'verification'])
def test_actual_probe_deadline_failure_never_initializes(tmp_path, monkeypatch, late):
    harness = capacity_harness(tmp_path, monkeypatch, late=late)
    with pytest.raises(ValueError, match='capacity_probe_deadline'):
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == 'FAIL' and proof['state_restored'] is True
    assert proof['started_unix'] == 1000 and proof['deadline_unix'] == 1300
    assert proof['finished_unix'] == 1301 and proof['elapsed_seconds'] == 301
    assert proof['cleanup_allowance_seconds'] == 0 and proof['automatic_retry'] is False
    assert (harness.initial/'COMMIT.json').is_file() and not (harness.initial/'INITIALIZED.json').exists()
    assert (harness.initial/'capacity_validation/STARTED.json').is_file()
    matched.verify_loaded_initial.assert_not_called()
    assert_restored(harness)


@pytest.mark.parametrize('failure', ['zero_grad', 'adapter', 'optimizer', 'RNG', 'empty_cache', 'verify_base', 'verify_restored'])
def test_actual_probe_cleanup_failures_publish_failed_unverified_receipt(tmp_path, monkeypatch, failure):
    harness = capacity_harness(tmp_path, monkeypatch, failure=failure)
    with pytest.raises((RuntimeError, ValueError)):
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == 'FAIL' and proof['state_restored'] is False
    assert proof['restoration_status'] == 'FAILED' and proof['automatic_retry'] is False
    assert failure in [error['step'] for error in proof['cleanup_errors']]
    assert proof['maximum_shape']['full_input_tokens'] == 16384
    assert len(proof['completed_passes']) == 3
    assert (harness.initial/'COMMIT.json').is_file() and not (harness.initial/'INITIALIZED.json').exists()
    matched.verify_loaded_initial.assert_not_called()
    harness.child.engine.verify_base.assert_called_once()


@pytest.mark.parametrize('cleanup_failure', [None, 'optimizer', 'verify_base'])
def test_measurement_failure_preserves_original_and_cleanup_errors(tmp_path, monkeypatch, cleanup_failure):
    harness = capacity_harness(tmp_path, monkeypatch, forward_failure=True, failure=cleanup_failure)
    with pytest.raises(ValueError, match='injected forward failure') as raised:
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == 'FAIL' and proof['measurement_error']['error'] == 'injected forward failure'
    assert proof['state_restored'] is (cleanup_failure is None)
    assert not (harness.initial/'INITIALIZED.json').exists()
    if cleanup_failure:
        assert proof['cleanup_errors'][0]['step'] == cleanup_failure
        assert isinstance(raised.value.__cause__, RuntimeError)
    else:
        assert_restored(harness)


def test_result_write_failure_leaves_started_and_checkpoint_unresolved(tmp_path, monkeypatch):
    harness = capacity_harness(tmp_path, monkeypatch, forward_failure=True)
    write_once = matched.native.write_once

    def write(path, value):
        if Path(path).name == 'RESULT.json':
            raise OSError('injected terminal disk failure')
        return write_once(path, value)

    monkeypatch.setattr(matched.native, 'write_once', write)
    with pytest.raises(OSError, match='terminal disk failure') as raised:
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    assert isinstance(raised.value.__cause__, ValueError)
    assert (harness.initial/'capacity_validation/STARTED.json').is_file()
    assert (harness.initial/'COMMIT.json').is_file()
    assert not (harness.initial/'capacity_validation/RESULT.json').exists()
    assert not (harness.initial/'INITIALIZED.json').exists()
    assert_restored(harness)


@pytest.mark.parametrize('finish,passes', [(1299, True), (1300, False), (1301, False)])
def test_callback_acceptance_checks_exact_work_deadline(tmp_path, monkeypatch, finish, passes):
    harness = capacity_harness(tmp_path, monkeypatch)
    harness.child.engine.verify_base.side_effect = lambda: setattr(harness.clock, 'now', finish)
    if passes:
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    else:
        with pytest.raises(ValueError, match='capacity_probe_deadline'):
            matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == ('PASS' if passes else 'FAIL')
    assert (harness.initial/'INITIALIZED.json').exists() is passes
    assert_restored(harness)


def test_earlier_experiment_deadline_is_not_extended(tmp_path, monkeypatch):
    harness = capacity_harness(tmp_path, monkeypatch)
    harness.child.plan['hard_end_unix'] = 1050
    harness.child.engine.verify_base.side_effect = lambda: setattr(harness.clock, 'now', 1050)
    harness.initial.mkdir()
    with pytest.raises(ValueError, match='capacity_probe_deadline'):
        probe.initial_capacity(harness.child, harness.plan_path, harness.initial)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['deadline_unix'] == 1050 and proof['status'] == 'FAIL'
    assert_restored(harness)


def test_pre_snapshot_failure_publishes_unverified_result_without_retry(tmp_path, monkeypatch):
    harness = capacity_harness(tmp_path, monkeypatch)
    monkeypatch.setattr(probe, 'validate_environment', Mock(side_effect=ValueError('environment failed')))
    with pytest.raises(ValueError, match='environment failed'):
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
    proof = matched.native.read(harness.initial/'capacity_validation/RESULT.json')
    assert proof['status'] == 'FAIL' and proof['state_restored'] is False
    assert proof['restoration_status'] == 'UNVERIFIED' and proof['automatic_retry'] is False
    assert not harness.calls and not (harness.initial/'INITIALIZED.json').exists()
    assert (harness.initial/'capacity_validation/STARTED.json').is_file()
    with pytest.raises(ValueError, match='never_recreated'):
        matched.initialize(harness.plan_path, validate_child=probe.initial_capacity)
