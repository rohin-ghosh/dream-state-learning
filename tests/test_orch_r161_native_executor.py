"""Real Torch CPU fixtures, not Qwen validation or scientific training."""

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
from io import BytesIO
import json
import os
import pickle
from pathlib import Path
from types import SimpleNamespace
import random
import time

import pytest

torch = pytest.importorskip('torch')
peft = pytest.importorskip('peft')
from safetensors.torch import load as load_safetensors, save as save_safetensors

from gpu import orch_r125_continual_native as native
from gpu import orch_r161_native_executor as executor_module
from organism_v6.pcfl_vertical_train import _state_hash


@dataclass(frozen=True)
class Component:
    label: str
    input_ids: tuple = (1, 2, 3, 4)
    labels: tuple = (-100, -100, 3, 4)
    target_ids: tuple = (3, 4)
    objective_weight: float = 0.0625


class ToyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = torch.nn.Embedding(13, 4)
        self.layer = torch.nn.Linear(4, 4, bias=False)
        self.output = torch.nn.Linear(4, 13, bias=False)
        self.calls = []
        self.fail = False

    def forward(self, input_ids, attention_mask, use_cache, labels, logits_to_keep=None):
        self.calls.append(dict(inputs=input_ids.detach().clone(), labels=labels.detach().clone(),
                               logits_to_keep=logits_to_keep, use_cache=use_cache))
        hidden = self.embedding(input_ids)
        logits = self.output(hidden + self.layer(hidden))
        if logits_to_keep is not None:
            logits = logits[:, -logits_to_keep:]
        loss = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 13), labels[:, 1:].reshape(-1))
        if self.fail:
            loss = loss * float('nan')
        return SimpleNamespace(loss=loss)

@pytest.fixture
def case(tmp_path):
    torch.manual_seed(941)
    random.seed(941)
    model = peft.get_peft_model(ToyModel(), peft.LoraConfig(r=2, lora_alpha=4,
        lora_dropout=0.0, target_modules=['layer'], bias='none'))
    model.requires_grad_(False)
    parameters = {name: value for name, value in model.named_parameters() if '.lora_' in name}
    base = {name: value for name, value in model.named_parameters() if '.lora_' not in name}
    original_base = _state_hash(base)

    def verify_base():
        assert _state_hash(base) == original_base

    child = object.__new__(native.NativeChild)
    child.plan = dict(root=str(tmp_path), context_limit=16, hard_end_unix=time.time()+60)
    child.torch, child.parameters, child.experiment = torch, parameters, None
    child.native = SimpleNamespace(is_lora=lambda name: '.lora_' in name, state_hash=_state_hash)
    child.engine = SimpleNamespace(model=model, verify_base=verify_base)
    child.optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, betas=(0.9, 0.999),
        eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
    child.optimizer_steps = 0
    binding = dict(fork_root=str(tmp_path), mode='learning', authority_sha256='a'*64,
                   initializer_commit_sha256='b'*64)
    executor = executor_module.NativeExecutor(child, fork_binding=binding,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    batch = SimpleNamespace(sha256='c'*64, components=(Component('NEW', objective_weight=0.75),
        *(Component('ANCHOR:'+family) for family in executor_module.FAMILIES)))
    return SimpleNamespace(child=child, model=model, executor=executor, batch=batch, binding=binding)


def test_real_cpu_update_and_exact_saved_state(case, tmp_path):
    before = case.executor.snapshot()
    result = case.executor.update(case.batch)
    after = case.executor.snapshot()
    assert result == dict(batch_sha256='c'*64, optimizer_step=1)
    assert after['optimizer_steps'] == 1
    assert after['adapter_sha256'] != before['adapter_sha256']
    assert after['optimizer_sha256'] != before['optimizer_sha256']
    assert len(case.model.calls) == 5
    assert case.model.calls[0]['logits_to_keep'] == 3
    assert case.model.calls[0]['labels'].tolist() == [[-100, 3, 4]]
    assert all(call['logits_to_keep'] is None and call['labels'].tolist() == [[-100, -100, 3, 4]]
               for call in case.model.calls[1:])
    assert all(call['inputs'].tolist() == [[1, 2, 3, 4]] and call['use_cache'] is False for call in case.model.calls)
    assert [row['objective_weight'] for row in case.executor.last_update['losses']] == [0.75]+[0.0625]*4
    assert not case.model.training and not any(value.requires_grad for value in case.model.parameters())
    checkpoint = case.executor.checkpoint(tmp_path/'checkpoint')
    assert case.executor.verify_checkpoint(checkpoint) == after == case.executor.snapshot()


def test_frozen_forbids_update_and_preserves_rng(case, tmp_path):
    case.executor.fork_binding['mode'] = 'frozen'
    before = case.executor.snapshot()
    with pytest.raises(ValueError, match='frozen_executor'):
        case.executor.update(case.batch)
    case.executor.checkpoint(tmp_path/'frozen_checkpoint')
    assert case.executor.snapshot() == before
    assert not case.model.calls


def test_suffix_weighted_step_matches_full_label_reference(case):
    model = deepcopy(case.model)
    parameters = [value for name, value in model.named_parameters() if '.lora_' in name]
    for parameter in parameters:
        parameter.requires_grad_(True)
    optimizer = torch.optim.AdamW(parameters, lr=3e-5, betas=(0.9, 0.999),
        eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
    optimizer.zero_grad(set_to_none=True)
    for component in case.batch.components:
        inputs = torch.tensor([component.input_ids], dtype=torch.long)
        loss = model(input_ids=inputs, labels=torch.tensor([component.labels]),
            attention_mask=torch.ones_like(inputs), use_cache=False).loss
        (loss * component.objective_weight).backward()
    optimizer.step()
    case.executor.update(case.batch)
    for name, value in case.model.named_parameters():
        torch.testing.assert_close(value, dict(model.named_parameters())[name], rtol=0, atol=1e-8)


def test_cleanup_failure_keeps_executor_uncertain(case, monkeypatch):
    def fail_eval():
        raise RuntimeError('CPU cleanup fault')
    monkeypatch.setattr(case.model, 'eval', fail_eval)
    with pytest.raises(RuntimeError, match='cleanup fault'):
        case.executor.update(case.batch)
    assert case.executor.uncertain and case.child.optimizer_steps == 1
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.update(case.batch)


def test_uncertain_update_cannot_retry_or_checkpoint(case, tmp_path):
    case.model.get_base_model().fail = True
    with pytest.raises(ValueError, match='finite_scalar'):
        case.executor.update(case.batch)
    assert case.executor.uncertain
    assert case.child.optimizer_steps == 0
    assert not any(value.requires_grad for value in case.model.parameters())
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.update(case.batch)
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.checkpoint(tmp_path/'failed_checkpoint')


@pytest.mark.parametrize('bad', [
    Component('NEW', labels=(-100, 2, 3, 4), objective_weight=0.75),
    Component('NEW', objective_weight=0.5),
    Component('PARENT', objective_weight=0.75),
    Component('NEW', input_ids=(1, 2, 3, 5), objective_weight=0.75),
])
def test_bad_batch_refused_before_updates(case, bad):
    batch = SimpleNamespace(sha256='c'*64, components=(bad, *case.batch.components[1:]))
    with pytest.raises(ValueError):
        case.executor.update(batch)
    assert case.child.optimizer_steps == 0 and not case.model.calls


def test_anchor_masked_suffix_is_preserved(case):
    anchor = Component('ANCHOR:code', labels=(-100, 2, 3, -100), target_ids=(2, 3))
    batch = SimpleNamespace(sha256='d'*64, components=(case.batch.components[0], anchor, *case.batch.components[2:]))
    case.executor.update(batch)
    assert case.model.calls[1]['labels'].tolist() == [[-100, 2, 3, -100]]
    assert case.model.calls[1]['logits_to_keep'] is None


def test_optimizer_recipe_change_refused(case):
    case.child.optimizer.param_groups[0]['lr'] = 1e-4
    with pytest.raises(ValueError, match='fixed_native_AdamW_recipe'):
        case.executor.update(case.batch)
    assert not case.model.calls


@pytest.mark.parametrize('flag', ['maximize', 'differentiable', 'capturable', 'amsgrad'])
def test_optimizer_modes_refused(case, flag):
    case.child.optimizer.param_groups[0][flag] = True
    with pytest.raises(ValueError, match='fixed_native_AdamW_recipe'):
        case.executor.update(case.batch)
    assert not case.model.calls


def test_checkpoint_failure_latches_uncertainty(case, tmp_path, monkeypatch):
    def fail_checkpoint(directory):
        directory.mkdir()
        raise RuntimeError('CPU serialization failure')
    monkeypatch.setattr(case.child, 'checkpoint', fail_checkpoint)
    with pytest.raises(RuntimeError, match='serialization failure'):
        case.executor.checkpoint(tmp_path/'failed_checkpoint')
    assert case.executor.uncertain
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.update(case.batch)
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.checkpoint(tmp_path/'other_checkpoint')


def test_base_gradient_enable_refused(case):
    case.model.embedding.weight.requires_grad_(True)
    with pytest.raises(ValueError, match='base_parameters_frozen'):
        case.executor.update(case.batch)


def test_saved_rng_tamper_rejected(case, tmp_path):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    payload = tmp_path/'checkpoint'/'optimizer_rng.pt'
    payload.write_bytes(payload.read_bytes()+b'tampered')
    with pytest.raises(ValueError, match='optimizer_RNG_file_binding'):
        case.executor.verify_checkpoint(reference)


def test_wrong_native_root_and_purpose_refused(case, tmp_path):
    binding = deepcopy(case.binding)
    binding['fork_root'] = str(tmp_path/'different')
    with pytest.raises(ValueError, match='resident_child_belongs'):
        executor_module.NativeExecutor(case.child, fork_binding=binding,
            execution_kind='CPU_TEST_ONLY', device='cpu')
    with pytest.raises(ValueError, match='purpose_device_binding'):
        executor_module.NativeExecutor(case.child, fork_binding=case.binding,
            execution_kind='EXTERNALLY_VALIDATED_EXECUTOR', device='cpu')


def test_foreign_or_uncommitted_reference_rejected_before_any_read(case, tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(executor_module.os, 'open', lambda *args, **kwargs: opened.append(args))
    for path in (tmp_path.parent/'foreign'/'COMMIT.json', tmp_path/'uncommitted'/'COMMIT.json'):
        with pytest.raises(ValueError, match='not_admitted_before_read'):
            case.executor.verify_checkpoint(dict(path=str(path), sha256='e'*64))
    assert not opened


def test_explicit_common_initializer_path_and_hash(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'initializer')
    child = case.child
    fork = tmp_path/'fresh_fork'
    fork.mkdir()
    child.plan['root'] = str(fork)
    binding = dict(case.binding, fork_root=str(fork), initializer_commit_sha256=reference['sha256'])
    executor = executor_module.NativeExecutor(child, fork_binding=binding, initializer_reference=reference,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    assert executor.verify_checkpoint(reference) == executor.snapshot()
    with pytest.raises(ValueError, match='initializer_path_hash_binding'):
        executor_module.NativeExecutor(child, fork_binding=binding,
            initializer_reference=dict(reference, sha256='f'*64), execution_kind='CPU_TEST_ONLY', device='cpu')
    opened = []
    monkeypatch.setattr(executor_module.os, 'open', lambda *args, **kwargs: opened.append(args))
    with pytest.raises(ValueError, match='not_admitted_before_read'):
        executor.verify_checkpoint(dict(reference, path=str(fork/'COMMIT.json')))
    assert not opened


def committed_reference(case, tmp_path, checkpoint_reference, **changes):
    path = tmp_path/'batch0000'/'COMMIT.json'
    document = dict(schema='R161_REVIEWED_PACKET_FIT_V1', status='COMMITTED', batch_index=0,
        authority_sha256=case.binding['authority_sha256'], checkpoint=checkpoint_reference)
    document.update(changes)
    path.write_text(json.dumps(document))
    return dict(path=str(path), sha256=native.sha(path))


def test_only_authority_bound_committed_fork_reference_is_admitted(case, tmp_path):
    checkpoint = case.executor.checkpoint(tmp_path/'batch0000'/'checkpoint')
    executor = executor_module.NativeExecutor(case.child, fork_binding=case.binding,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    with pytest.raises(ValueError, match='not_admitted_before_read'):
        executor.verify_checkpoint(checkpoint)
    commit = committed_reference(case, tmp_path, checkpoint)
    assert executor.admit_committed_checkpoint(commit) == checkpoint
    assert executor.verify_checkpoint(checkpoint) == executor.snapshot()


@pytest.mark.parametrize('changes', [dict(status='FAILED'), dict(authority_sha256='f'*64),
    dict(batch_index=1), dict(checkpoint=dict(path='/tmp/foreign/COMMIT.json', sha256='f'*64))])
def test_wrong_commit_authority_or_checkpoint_path_rejected(case, tmp_path, changes):
    checkpoint = case.executor.checkpoint(tmp_path/'batch0000'/'checkpoint')
    executor = executor_module.NativeExecutor(case.child, fork_binding=case.binding,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    commit = committed_reference(case, tmp_path, checkpoint, **changes)
    with pytest.raises(ValueError, match='committed_checkpoint_'):
        executor.admit_committed_checkpoint(commit)
    with pytest.raises(ValueError, match='not_admitted_before_read'):
        executor.verify_checkpoint(checkpoint)


@pytest.mark.parametrize('relative', ['COMMIT.json', 'optimizer_rng.pt', 'adapter/adapter_model.safetensors', 'adapter'])
def test_checkpoint_symlinks_are_not_followed(case, tmp_path, relative):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    path = tmp_path/'checkpoint'/relative
    moved = tmp_path/('moved_'+path.name)
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises(OSError):
        case.executor.verify_checkpoint(reference)


def test_checkpoint_parent_symlink_is_not_followed(case, tmp_path):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    path = tmp_path/'checkpoint'
    moved = tmp_path/'moved_checkpoint'
    path.rename(moved)
    path.symlink_to(moved, target_is_directory=True)
    with pytest.raises(OSError):
        case.executor.verify_checkpoint(reference)


def test_hash_checked_bytes_are_the_only_deserialized_bytes(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    read_file = executor_module._read_file
    reads = []
    original_load = torch.load
    loads = []

    def replace_after_read(directory, name, limit):
        raw = read_file(directory, name, limit)
        reads.append(name)
        if name == 'COMMIT.json':
            (tmp_path/'checkpoint'/name).write_bytes(b'not the admitted JSON')
        if name == 'optimizer_rng.pt':
            (tmp_path/'checkpoint'/name).write_bytes(b'not the admitted weights')
        return raw

    def bytes_only(stream, **kwargs):
        assert isinstance(stream, BytesIO) and kwargs['weights_only'] is True
        loads.append(hashlib.sha256(stream.getvalue()).hexdigest())
        return original_load(stream, **kwargs)

    before = case.executor.snapshot()
    monkeypatch.setattr(executor_module, '_read_file', replace_after_read)
    monkeypatch.setattr(torch, 'load', bytes_only)
    assert case.executor.verify_checkpoint(reference) == before
    assert reads.count('COMMIT.json') == reads.count('optimizer_rng.pt') == 1
    assert len(reads) == len(set(reads)) and len(loads) == 1


def test_directory_replacement_does_not_redirect_payload_reads(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    read_file = executor_module._read_file

    def replace_directory(directory, name, limit):
        raw = read_file(directory, name, limit)
        if name == 'COMMIT.json':
            os.rename(tmp_path/'checkpoint', tmp_path/'original_checkpoint')
            (tmp_path/'checkpoint').mkdir()
            (tmp_path/'checkpoint'/'optimizer_rng.pt').write_bytes(b'foreign payload must not be read')
        return raw

    monkeypatch.setattr(executor_module, '_read_file', replace_directory)
    assert case.executor.verify_checkpoint(reference) == case.executor.snapshot()


def test_optimizer_hash_mismatch_rejected_before_deserialization(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    (tmp_path/'checkpoint'/'optimizer_rng.pt').write_bytes(b'not admitted pickle bytes')
    calls = []
    monkeypatch.setattr(torch, 'load', lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match='optimizer_RNG_file_binding'):
        case.executor.verify_checkpoint(reference)
    assert not calls


@pytest.mark.parametrize('fault', ['changed', 'missing', 'extra', 'dtype', 'shape', 'config', 'live_config'])
def test_faulty_real_peft_serializer_rejected_with_self_consistent_hashes(case, tmp_path, monkeypatch, fault):
    original_save = case.model.save_pretrained

    def faulty_save(directory, **kwargs):
        original_save(directory, **kwargs)
        path = directory/'adapter_model.safetensors'
        tensors = load_safetensors(path.read_bytes())
        name = next(iter(tensors))
        if fault == 'changed':
            tensors[name] = tensors[name] + 1
        elif fault == 'missing':
            del tensors[name]
        elif fault == 'extra':
            tensors['unexpected.weight'] = torch.zeros(1)
        elif fault == 'dtype':
            tensors[name] = tensors[name].to(torch.float64)
        elif fault == 'shape':
            tensors[name] = tensors[name].reshape(-1)
        else:
            config_path = directory/'adapter_config.json'
            config = json.loads(config_path.read_bytes())
            config['lora_alpha'] += 1
            config_path.write_text(json.dumps(config))
            if fault == 'live_config':
                case.model.peft_config['default'].lora_alpha += 1
        path.write_bytes(save_safetensors(tensors))

    before = case.child.adapter_hash()
    monkeypatch.setattr(case.model, 'save_pretrained', faulty_save)
    with pytest.raises(ValueError, match='serialized_adapter|adapter_config'):
        case.executor.checkpoint(tmp_path/'faulty_checkpoint')
    assert case.executor.uncertain and case.child.adapter_hash() == before
    document = native.read(tmp_path/'faulty_checkpoint'/'COMMIT.json')
    assert document['adapter_state_sha256'] == before
    case.child.verify_checkpoint(document)
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.update(case.batch)


def test_real_peft_saved_keys_restore_without_adapter_name(case, tmp_path):
    case.executor.update(case.batch)
    reference = case.executor.checkpoint(tmp_path/'checkpoint')
    tensors = load_safetensors((tmp_path/'checkpoint'/'adapter'/'adapter_model.safetensors').read_bytes())
    assert tensors and all('.default.' not in name for name in tensors)
    restored = deepcopy(case.model)
    for name, parameter in restored.named_parameters():
        if '.lora_' in name:
            parameter.data.zero_()
    peft.set_peft_model_state_dict(restored, tensors, adapter_name='default')
    restored_parameters = {name: value for name, value in restored.named_parameters() if '.lora_' in name}
    assert _state_hash(restored_parameters) == case.child.adapter_hash()
    assert case.executor.verify_checkpoint(reference) == case.executor.snapshot()


def test_tiny_qwen_causal_peft_checkpoint_contract(case, tmp_path):
    from transformers import Qwen2Config, Qwen2ForCausalLM
    config = Qwen2Config(vocab_size=13, hidden_size=16, intermediate_size=32,
        num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
        max_position_embeddings=32, use_cache=False)
    model = peft.get_peft_model(Qwen2ForCausalLM(config), peft.LoraConfig(r=8, lora_alpha=16,
        lora_dropout=0.05, bias='none', task_type='CAUSAL_LM',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
    assert all(parameter.device.type == 'cpu' for parameter in model.parameters())
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.enable_input_require_grads()
    model.requires_grad_(False)
    model.eval()
    child = case.child
    child.parameters = {name: value for name, value in model.named_parameters() if '.lora_' in name}
    base = {name: value for name, value in model.named_parameters() if '.lora_' not in name}
    before_base = _state_hash(base)

    def verify_base():
        assert _state_hash(base) == before_base

    child.engine = SimpleNamespace(model=model, verify_base=verify_base)
    child.optimizer = torch.optim.AdamW(list(child.parameters.values()), lr=3e-5, betas=(0.9, 0.999),
        eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
    executor = executor_module.NativeExecutor(child, fork_binding=case.binding,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    executor.update(case.batch)
    state = executor.snapshot()
    reference = executor.checkpoint(tmp_path/'batch0000'/'checkpoint')
    assert executor.verify_checkpoint(reference) == state == executor.snapshot()
    tensors = load_safetensors((tmp_path/'batch0000'/'checkpoint'/'adapter'/'adapter_model.safetensors').read_bytes())
    restored = deepcopy(model)
    for name, parameter in restored.named_parameters():
        if '.lora_' in name:
            parameter.data.zero_()
    peft.set_peft_model_state_dict(restored, tensors, adapter_name='default')
    assert _state_hash({name: value for name, value in restored.named_parameters() if '.lora_' in name}) == state['adapter_sha256']
    assert state['optimizer_steps'] == 1 and not torch.cuda.is_initialized()
    commit = committed_reference(case, tmp_path, reference)
    admitted = executor_module.admit_committed_checkpoint(fork_binding=case.binding, commit_reference=commit)
    resumed = fresh_executor(case)
    executor.update(case.batch)
    expected = executor.snapshot()
    assert resumed.restore_admitted_checkpoint(admitted) == state
    resumed.update(case.batch)
    assert resumed.snapshot() == expected


def test_duplicate_commit_keys_rejected(case, tmp_path):
    path = tmp_path/'COMMIT.json'
    path.write_bytes(b'{"schema":"one","schema":"two"}')
    reference = dict(path=str(path), sha256=native.sha(path))
    binding = dict(case.binding, initializer_commit_sha256=reference['sha256'])
    executor = executor_module.NativeExecutor(case.child, fork_binding=binding, initializer_reference=reference,
        execution_kind='CPU_TEST_ONLY', device='cpu')
    with pytest.raises(ValueError, match='duplicate_checkpoint_JSON_key'):
        executor.verify_checkpoint(reference)


def fresh_executor(case, *, binding=None, initializer_reference=None):
    model = deepcopy(case.child.engine.model)
    parameters = {name: value for name, value in model.named_parameters() if '.lora_' in name}
    base = {name: value for name, value in model.named_parameters() if '.lora_' not in name}
    original_base = _state_hash(base)
    for parameter in parameters.values():
        parameter.data.zero_()

    def verify_base():
        assert _state_hash(base) == original_base

    child = object.__new__(native.NativeChild)
    child.plan, child.native, child.torch = deepcopy(case.child.plan), case.child.native, torch
    child.experiment, child.parameters = deepcopy(case.child.experiment), parameters
    child.engine = SimpleNamespace(model=model, verify_base=verify_base)
    child.optimizer = torch.optim.AdamW(list(parameters.values()), lr=3e-5, betas=(0.9, 0.999),
        eps=1e-8, weight_decay=0.01, foreach=False, fused=False)
    child.optimizer_steps = 0
    return executor_module.NativeExecutor(child, fork_binding=binding or case.binding,
        initializer_reference=initializer_reference, execution_kind='CPU_TEST_ONLY', device='cpu')


def test_admitted_initializer_restores_all_state_without_reopening_files(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'initializer')
    binding = dict(case.binding, initializer_commit_sha256=reference['sha256'])
    admitted = executor_module.admit_initializer_checkpoint(fork_binding=binding, reference=reference)
    before = admitted.fingerprint()
    executor = fresh_executor(case, binding=binding, initializer_reference=reference)
    (tmp_path/'initializer'/'COMMIT.json').write_bytes(b'replaced after admission')
    (tmp_path/'initializer'/'optimizer_rng.pt').write_bytes(b'replaced after admission')

    def no_reopen(*args, **kwargs):
        raise AssertionError('checkpoint path reopened after admission')

    monkeypatch.setattr(executor_module, '_directory', no_reopen)
    monkeypatch.setattr(native, 'read', no_reopen)
    monkeypatch.setattr(native, 'sha', no_reopen)
    assert executor.restore_admitted_checkpoint(admitted) == before == executor.snapshot()
    assert not executor.uncertain and not torch.cuda.is_initialized()
    with pytest.raises(ValueError, match='restore_only_into_fresh_executor'):
        executor.restore_admitted_checkpoint(admitted)


def test_admitted_successor_restores_optimizer_and_same_next_update(case, tmp_path):
    case.executor.update(case.batch)
    reference = case.executor.checkpoint(tmp_path/'batch0000'/'checkpoint')
    commit = committed_reference(case, tmp_path, reference)
    admitted = executor_module.admit_committed_checkpoint(fork_binding=case.binding, commit_reference=commit)
    restored = fresh_executor(case)
    assert restored.restore_admitted_checkpoint(admitted) == case.executor.snapshot()
    case.executor.update(case.batch)
    expected = case.executor.snapshot()
    restored.update(case.batch)
    assert restored.snapshot() == expected


def test_preconstructor_admission_rejects_wrong_hash_or_foreign_commit_before_open(case, tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(executor_module.os, 'open', lambda *args, **kwargs: opened.append(args))
    with pytest.raises(ValueError, match='initializer_path_hash_binding'):
        executor_module.admit_initializer_checkpoint(fork_binding=case.binding,
            reference=dict(path=str(tmp_path/'foreign'/'COMMIT.json'), sha256='f'*64))
    with pytest.raises(ValueError, match='fork_local_authority_commit_only'):
        executor_module.admit_committed_checkpoint(fork_binding=case.binding,
            commit_reference=dict(path=str(tmp_path.parent/'foreign'/'COMMIT.json'), sha256='f'*64))
    assert not opened


def test_restore_failure_latches_uncertainty_and_never_retries(case, tmp_path, monkeypatch):
    reference = case.executor.checkpoint(tmp_path/'initializer')
    binding = dict(case.binding, initializer_commit_sha256=reference['sha256'])
    admitted = executor_module.admit_initializer_checkpoint(fork_binding=binding, reference=reference)
    executor = fresh_executor(case, binding=binding, initializer_reference=reference)

    def fail_optimizer(payload):
        raise RuntimeError('CPU optimizer restore failure')

    monkeypatch.setattr(executor.child.optimizer, 'load_state_dict', fail_optimizer)
    with pytest.raises(RuntimeError, match='optimizer restore failure'):
        executor.restore_admitted_checkpoint(admitted)
    assert executor.uncertain
    with pytest.raises(ValueError, match='uncertain_executor'):
        executor.restore_admitted_checkpoint(admitted)
    with pytest.raises(ValueError, match='uncertain_executor'):
        executor.update(case.batch)
    with pytest.raises(ValueError, match='uncertain_executor'):
        executor.checkpoint(tmp_path/'retry')


def test_admitted_byte_tamper_and_cross_fork_restore_rejected(case, tmp_path):
    reference = case.executor.checkpoint(tmp_path/'initializer')
    binding = dict(case.binding, initializer_commit_sha256=reference['sha256'])
    admitted = executor_module.admit_initializer_checkpoint(fork_binding=binding, reference=reference)
    executor = fresh_executor(case, binding=binding, initializer_reference=reference)
    with pytest.raises(ValueError, match='optimizer_RNG_file_binding'):
        executor.restore_admitted_checkpoint(replace(admitted, optimizer_bytes=b'tampered'))
    wrong_binding = dict(binding, authority_sha256='f'*64)
    with pytest.raises(ValueError, match='restore_exact_fork_admission'):
        executor.restore_admitted_checkpoint(replace(admitted, binding_bytes=json.dumps(wrong_binding).encode()))
    assert not executor.uncertain and executor.child.optimizer_steps == 0


class UnsafePickle:
    def __reduce__(self):
        return print, ('UNSAFE_PICKLE_WAS_EXECUTED',)


@pytest.mark.parametrize('fault', ['unsafe_pickle', 'actual_step', 'nonfinite_moment', 'maximize'])
def test_preconstructor_payload_validation(case, tmp_path, fault, capsys):
    case.executor.update(case.batch)
    reference = case.executor.checkpoint(tmp_path/'initializer')
    path = tmp_path/'initializer'/'optimizer_rng.pt'
    payload = torch.load(path, map_location='cpu', weights_only=True)
    if fault == 'unsafe_pickle':
        payload = UnsafePickle()
    elif fault == 'actual_step':
        payload['optimizer']['state'][0]['step'] += 1
    elif fault == 'nonfinite_moment':
        payload['optimizer']['state'][0]['exp_avg'].fill_(float('nan'))
    else:
        payload['optimizer']['param_groups'][0]['maximize'] = True
    torch.save(payload, path)
    document = native.read(tmp_path/'initializer'/'COMMIT.json')
    document['checkpoint_sha256']['optimizer'] = document['checkpoint_sha256']['rng'] = native.sha(path)
    (tmp_path/'initializer'/'COMMIT.json').write_text(json.dumps(document))
    reference['sha256'] = native.sha(tmp_path/'initializer'/'COMMIT.json')
    binding = dict(case.binding, initializer_commit_sha256=reference['sha256'])
    expected = pickle.UnpicklingError if fault == 'unsafe_pickle' else ValueError
    with pytest.raises(expected):
        executor_module.admit_initializer_checkpoint(fork_binding=binding, reference=reference)
    assert 'UNSAFE_PICKLE_WAS_EXECUTED' not in capsys.readouterr().out


@pytest.mark.parametrize('fault', [
    'adapter_nan', 'adapter_inf', 'exp_avg_nan', 'exp_avg_inf', 'exp_avg_sq_nan', 'exp_avg_sq_inf',
    'step_wrong', 'step_nan', 'step_inf', 'step_shape', 'step_non_tensor',
    'moment_shape', 'moment_dtype', 'moment_non_tensor', 'negative_second_moment',
    'missing_state', 'missing_moment',
])
def test_corruption_after_actual_AdamW_step_fails_and_latches_uncertainty(case, tmp_path, monkeypatch, fault):
    original_step = case.child.optimizer.step
    actual_steps = []

    def corrupt_after_real_step(*args, **kwargs):
        result = original_step(*args, **kwargs)
        actual_steps.append(1)
        parameter = list(case.child.parameters.values())[-1]
        values = case.child.optimizer.state[parameter]
        assert float(values['step']) == 1
        assert all(bool(torch.isfinite(value.grad).all()) for value in case.child.parameters.values())
        if fault.startswith('adapter_'):
            with torch.no_grad():
                parameter.reshape(-1)[0] = float(fault.removeprefix('adapter_'))
        elif fault.startswith('exp_avg_sq_'):
            values['exp_avg_sq'].reshape(-1)[0] = float(fault.removeprefix('exp_avg_sq_'))
        elif fault.startswith('exp_avg_'):
            values['exp_avg'].reshape(-1)[0] = float(fault.removeprefix('exp_avg_'))
        elif fault == 'step_wrong':
            values['step'] += 1
        elif fault in ('step_nan', 'step_inf'):
            values['step'].fill_(float(fault.removeprefix('step_')))
        elif fault == 'step_shape':
            values['step'] = torch.ones(2)
        elif fault == 'step_non_tensor':
            values['step'] = 1
        elif fault == 'moment_shape':
            values['exp_avg'] = values['exp_avg'].reshape(-1)
        elif fault == 'moment_dtype':
            values['exp_avg'] = values['exp_avg'].to(torch.float64)
        elif fault == 'moment_non_tensor':
            values['exp_avg'] = 0.0
        elif fault == 'negative_second_moment':
            values['exp_avg_sq'].reshape(-1)[0] = -1.0
        elif fault == 'missing_state':
            del case.child.optimizer.state[parameter]
        elif fault == 'missing_moment':
            del values['exp_avg']
        return result

    monkeypatch.setattr(case.child.optimizer, 'step', corrupt_after_real_step)
    with pytest.raises(ValueError, match='post_step_'):
        case.executor.update(case.batch)
    assert actual_steps == [1] and case.child.optimizer_steps == 1
    assert case.executor.uncertain and case.executor.last_update is None
    assert not case.model.training and not any(value.requires_grad for value in case.model.parameters())
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.update(case.batch)
    with pytest.raises(ValueError, match='uncertain_executor'):
        case.executor.checkpoint(tmp_path/'must_not_checkpoint_corrupt_step')
    assert actual_steps == [1]


def test_post_step_validation_accepts_real_AdamW_updates_and_actual_counters(case, monkeypatch):
    original_step = case.child.optimizer.step
    actual_steps = []

    def real_step(*args, **kwargs):
        result = original_step(*args, **kwargs)
        actual_steps.append(1)
        return result

    monkeypatch.setattr(case.child.optimizer, 'step', real_step)
    for expected_step in (1, 2):
        receipt = case.executor.update(case.batch)
        assert receipt['optimizer_step'] == expected_step and not case.executor.uncertain
        assert all(float(values['step']) == expected_step for values in case.child.optimizer.state.values())
    assert actual_steps == [1, 1]
