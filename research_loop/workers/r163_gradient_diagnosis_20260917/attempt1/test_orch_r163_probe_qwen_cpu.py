"""CPU-only diagnosis of the bound R163 full/suffix stochastic update paths."""

from contextlib import nullcontext
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import time
from types import SimpleNamespace

import pytest

torch = pytest.importorskip('torch')
peft = pytest.importorskip('peft')
from transformers import Qwen2Config, Qwen2ForCausalLM

from gpu import orch_r125_continual_native as native
from gpu import orch_r161_native_executor as executor_module
from gpu import orch_r163_executor_probe as probe
from organism_v6.pcfl_vertical_train import _state_hash


@dataclass(frozen=True)
class Component:
    label: str
    input_ids: tuple
    labels: tuple
    target_ids: tuple
    objective_weight: float


@dataclass(frozen=True)
class Batch:
    components: tuple

    @property
    def sha256(self):
        return native.digest(asdict(self))


def rng_state():
    return dict(cpu=hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
        python=hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
        cuda=[hashlib.sha256(state.numpy().tobytes()).hexdigest() for state in torch.cuda.get_rng_state_all()])


def tensor_comparison(actual, reference, tolerance):
    records = []
    for name, expected in reference.items():
        observed = actual[name]
        if expected is None or observed is None:
            records.append(dict(name=name, equal=observed is expected, elements=0, mismatches=0,
                                max_absolute_error=0.0))
            continue
        close = torch.isclose(observed, expected, **tolerance)
        records.append(dict(name=name, equal=bool(close.all()), elements=observed.numel(),
            mismatches=int((~close).sum()), max_absolute_error=float((observed-expected).abs().max())))
    return dict(pass_tolerance=all(record['equal'] for record in records),
        exact=_state_hash(actual) == _state_hash(reference),
        total_elements=sum(record['elements'] for record in records),
        mismatched_elements=sum(record['mismatches'] for record in records),
        worst=max(records, key=lambda record: record['max_absolute_error']), parameters=records)


def make_executor(tmp_path, dtype, checkpointing, dropout, nonzero_b):
    torch.manual_seed(941)
    random.seed(941)
    config = Qwen2Config(vocab_size=257, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
        num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=128,
        attention_dropout=0.0, use_cache=False)
    config._attn_implementation = 'sdpa'
    base = Qwen2ForCausalLM(config)
    buffer_dtypes = {name: value.dtype for name, value in base.named_buffers()}
    base.to(dtype=dtype)
    for name, value in tuple(base.named_buffers()):
        parent, unused, attribute = name.rpartition('.')
        setattr(base.get_submodule(parent), attribute, value.to(buffer_dtypes[name]))
    model = peft.get_peft_model(base, peft.LoraConfig(r=8, lora_alpha=16, lora_dropout=dropout,
        bias='none', task_type='CAUSAL_LM',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
    if checkpointing:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
    model.requires_grad_(False)
    model.eval()
    parameters = {name: parameter for name, parameter in model.named_parameters() if '.lora_' in name}
    if nonzero_b:
        with torch.no_grad():
            for name, parameter in parameters.items():
                if '.lora_B.' in name:
                    parameter.copy_((torch.arange(parameter.numel()).reshape(parameter.shape) % 7 - 3) * 0.001)
    frozen = {name: parameter for name, parameter in model.named_parameters() if '.lora_' not in name}
    base_hash = _state_hash(frozen)

    def verify_base():
        assert _state_hash(frozen) == base_hash

    child = object.__new__(native.NativeChild)
    child.plan = dict(root=str(tmp_path), context_limit=128, hard_end_unix=time.time()+600)
    child.torch, child.parameters, child.experiment = torch, parameters, None
    child.native = SimpleNamespace(is_lora=lambda name: '.lora_' in name, state_hash=_state_hash)
    child.engine = SimpleNamespace(model=model, verify_base=verify_base)
    child.optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, betas=(0.9, 0.999),
        eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
    child.optimizer_steps = 0
    binding = dict(fork_root=str(tmp_path), mode='learning', authority_sha256='a'*64,
                   initializer_commit_sha256='b'*64)
    executor = executor_module.NativeExecutor(child, fork_binding=binding, execution_kind='CPU_TEST_ONLY', device='cpu')
    components = []
    for index, (label, length, target_count) in enumerate([
        ('NEW', 64, 1), ('ANCHOR:code', 23, 9), ('ANCHOR:concise_answer', 17, 7),
        ('ANCHOR:math', 31, 11), ('ANCHOR:simulated_tools', 19, 8),
    ]):
        tokens = tuple(1 + (position*7 + index*11) % 255 for position in range(length))
        targets = tokens[-target_count:]
        components.append(Component(label, tokens, (-100,)*(length-target_count)+targets, targets,
                                    0.75 if index == 0 else 0.0625))
    return executor, Batch(tuple(components))


def compare_runs(actual, reference):
    actual_rng = actual['state']
    reference_rng = reference['state']
    before_backward_actual = [event['rng'] for event in actual['trace'] if event['phase'] == 'before_backward']
    before_backward_reference = [event['rng'] for event in reference['trace'] if event['phase'] == 'before_backward']
    dropout_actual = [event for event in actual['trace'] if event['phase'] == 'dropout']
    dropout_reference = [event for event in reference['trace'] if event['phase'] == 'dropout']
    exact_end_rng = (torch.equal(actual_rng['cpu'], reference_rng['cpu'])
        and _state_hash(actual_rng['cuda']) == _state_hash(reference_rng['cuda'])
        and actual_rng['python'] == reference_rng['python'])
    return dict(losses_pass=bool(torch.isclose(torch.tensor(actual['losses']), torch.tensor(reference['losses']),
                                             **probe.LOSS_TOLERANCE).all()),
        loss_max_absolute_error=max(abs(observed-expected) for observed, expected in zip(actual['losses'], reference['losses'])),
        gradients=tensor_comparison(actual_rng['gradients'], reference_rng['gradients'], probe.GRADIENT_TOLERANCE),
        adapter=tensor_comparison(actual_rng['adapter'], reference_rng['adapter'], probe.UPDATE_TOLERANCE),
        exact_optimizer=_state_hash(actual_rng['optimizer']) == _state_hash(reference_rng['optimizer']),
        exact_start_rng=actual['start_rng'] == reference['start_rng'], exact_end_rng=exact_end_rng,
        exact_before_backward_rng=before_backward_actual == before_backward_reference,
        exact_dropout_trace=dropout_actual == dropout_reference,
        same_base_before=actual['base_before'] == reference['base_before'],
        same_buffers_before=actual['buffers_before'] == reference['buffers_before'])


@pytest.mark.parametrize('dtype_name,checkpointing,dropout,nonzero_b', [
    ('float32', True, 0.05, False), ('bfloat16', True, 0.05, False),
    ('float32', False, 0.05, False), ('bfloat16', False, 0.05, False),
    ('float32', True, 0.0, False), ('bfloat16', True, 0.0, False),
    ('bfloat16', True, 0.05, True),
])
def test_full_full_and_full_suffix_stochastic_parity(tmp_path, monkeypatch, dtype_name, checkpointing, dropout, nonzero_b):
    assert not torch.cuda.is_initialized()
    dtype = getattr(torch, dtype_name)
    if dtype == torch.bfloat16:
        try:
            with torch.autocast(device_type='cpu', dtype=torch.bfloat16):
                torch.ones(2, 2).matmul(torch.ones(2, 2))
        except (RuntimeError, TypeError) as error:
            pytest.skip('CPU BF16 unsupported: '+str(error))
    context = (lambda: torch.autocast(device_type='cpu', dtype=torch.bfloat16)) if dtype == torch.bfloat16 else nullcontext
    monkeypatch.setattr(probe, 'nullcontext', context)
    monkeypatch.setattr(executor_module, 'nullcontext', context)
    executor, batch = make_executor(tmp_path, dtype, checkpointing, dropout, nonzero_b)
    child = executor.child
    baseline = probe.saved_state(child)
    active_trace = []
    original_backward = torch.autograd.backward
    original_step = child.optimizer.step

    def traced_backward(*args, **kwargs):
        active_trace.append(dict(phase='before_backward', rng=rng_state()))
        result = original_backward(*args, **kwargs)
        active_trace.append(dict(phase='after_backward', rng=rng_state()))
        return result

    def traced_step(*args, **kwargs):
        active_trace.append(dict(phase='before_step', rng=rng_state()))
        result = original_step(*args, **kwargs)
        active_trace.append(dict(phase='after_step', rng=rng_state()))
        return result

    monkeypatch.setattr(torch.autograd, 'backward', traced_backward)
    monkeypatch.setattr(child.optimizer, 'step', traced_step)
    handles = []
    for name, module in child.engine.model.named_modules():
        if '.lora_dropout.' not in name:
            continue

        def trace_dropout(module, inputs, name=name):
            active_trace.append(dict(phase='dropout', module=name, training=module.training,
                shape=list(inputs[0].shape), dtype=str(inputs[0].dtype), input_sha256=_state_hash(inputs[0]), rng=rng_state()))

        handles.append(module.register_forward_pre_hook(trace_dropout))
    runs = {}
    try:
        for label, implementation in [('full_first', 'full'), ('full_repeat', 'full'),
                                      ('suffix_first', 'suffix'), ('suffix_repeat', 'suffix')]:
            probe.restore_state(child, baseline)
            assert _state_hash(probe.saved_state(child)) == _state_hash(baseline)
            active_trace = []
            run = dict(start_rng=rng_state(),
                base_before=_state_hash({name: value for name, value in child.engine.model.named_parameters() if '.lora_' not in name}),
                buffers_before=_state_hash(dict(child.engine.model.named_buffers())))
            if implementation == 'full':
                run['losses'] = probe.full_label_update(executor, batch)
            else:
                executor.update(batch)
                run['losses'] = [component['loss'] for component in executor.last_update['losses']]
            run.update(state=probe.saved_state(child), trace=active_trace)
            runs[label] = run
    finally:
        for handle in handles:
            handle.remove()
        probe.restore_state(child, baseline)
    comparisons = {name: compare_runs(runs[actual], runs[reference]) for name, actual, reference in [
        ('full_full', 'full_repeat', 'full_first'), ('full_suffix', 'suffix_first', 'full_first'),
        ('full_suffix_warm', 'suffix_first', 'full_repeat'), ('suffix_suffix', 'suffix_repeat', 'suffix_first')
    ]}
    document = dict(schema='R163_QWEN_CPU_GRADIENT_DIAGNOSIS_V1', dtype=dtype_name, checkpointing=checkpointing,
        lora_dropout=dropout, nonzero_lora_B=nonzero_b, rank=8, alpha=16, batch=asdict(batch),
        loss_tolerance=probe.LOSS_TOLERANCE, gradient_tolerance=probe.GRADIENT_TOLERANCE,
        update_tolerance=probe.UPDATE_TOLERANCE, comparisons=comparisons,
        state_restored=_state_hash(probe.saved_state(child)) == _state_hash(baseline),
        real_7b_validated=False, cuda_initialized=torch.cuda.is_initialized(),
        traces={name: dict(trace=run['trace'], losses=run['losses'], start_rng=run['start_rng']) for name, run in runs.items()})
    (tmp_path/'DIAGNOSTIC.json').write_text(json.dumps(document, indent=2, sort_keys=True)+'\n')
    for name, comparison in comparisons.items():
        print(json.dumps(dict(dtype=dtype_name, checkpointing=checkpointing, dropout=dropout, nonzero_B=nonzero_b,
            comparison=name, losses_pass=comparison['losses_pass'], gradients_pass=comparison['gradients']['pass_tolerance'],
            grad_max_abs=comparison['gradients']['worst']['max_absolute_error'],
            exact_start_rng=comparison['exact_start_rng'], exact_before_backward_rng=comparison['exact_before_backward_rng'],
            exact_end_rng=comparison['exact_end_rng'], exact_dropout_trace=comparison['exact_dropout_trace'])))
    assert document['state_restored'] and not document['cuda_initialized']
    assert comparisons['full_full']['gradients']['pass_tolerance']
    assert comparisons['full_suffix']['gradients']['pass_tolerance']
