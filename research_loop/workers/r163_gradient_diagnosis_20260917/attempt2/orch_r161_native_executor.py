"""Explicit NativeChild executor with checkpoint admission; no model loading or packet selection."""

from contextlib import contextmanager, nullcontext
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import random
import re
import stat

from gpu import orch_r125_continual_native as native
from gpu.astra_pchain2_native import EncodedRow
from gpu.orch_r145_suffix_boundary import loss_arguments
from organism_v6.pcfl_vertical_train import _state_hash


CONTRACT = 'EXACT_ENCODED_BATCH_075_4X00625_NEW16_PREVIOUS1_V1'
FAMILIES = ('code', 'concise_answer', 'math', 'simulated_tools')
require = native.require


def _reference(reference):
    require(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'exact_checkpoint_reference')
    path = reference['path']
    require(type(path) is str and Path(path).is_absolute() and str(Path(path)) == path
            and '..' not in Path(path).parts, 'absolute_lexical_checkpoint_path')
    require(type(reference['sha256']) is str and re.fullmatch('[0-9a-f]{64}', reference['sha256']),
            'checkpoint_reference_sha256')
    return Path(path)


@contextmanager
def _directory(path):
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in path.parts[1:]:
            next_descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        yield descriptor
    finally:
        os.close(descriptor)


def _read_file(directory, name, limit):
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= limit, 'bounded_regular_checkpoint_file')
        chunks, remaining = [], before.st_size + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024**2))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b''.join(chunks)
        after = os.fstat(descriptor)
        require(len(raw) == before.st_size and (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'checkpoint_changed_during_read')
        return raw
    finally:
        os.close(descriptor)


def _bound(raw, expected, message):
    require(hashlib.sha256(raw).hexdigest() == expected, message)
    return raw


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_checkpoint_JSON_key')
            result[key] = value
        return result

    def invalid(value):
        raise ValueError('nonfinite_checkpoint_JSON')

    result = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    require(type(result) is dict, 'checkpoint_JSON_object')
    return result


def _serialized_config(model):
    from peft import PeftModel
    require(isinstance(model, PeftModel) and set(model.peft_config) == {'default'}, 'single_default_PEFT_adapter')
    config = model.peft_config['default']
    require(config.peft_type == 'LORA' and config.bias == 'none' and not config.modules_to_save
            and not config.use_dora and not config.lora_bias, 'plain_LoRA_serialization_contract')
    document = deepcopy(config.to_dict())
    set_fields = tuple(key for key, value in document.items() if isinstance(value, set))
    for key in set_fields:
        document[key] = sorted(document[key])
    document['inference_mode'] = True
    if document['base_model_name_or_path'] is None:
        document['base_model_name_or_path'] = model.base_model.model.__dict__.get('name_or_path')
    if config.task_type is None:
        base_class = model._get_base_model_class(is_prompt_tuning=False)
        document['auto_mapping'] = dict(base_model_class=base_class.__name__, parent_library=base_class.__module__)
    return json.loads(json.dumps(document)), set_fields


def _optimizer_recipe(group):
    require(group['lr'] == 3e-5 and tuple(group['betas']) == (0.9, 0.999)
            and group['eps'] == 1e-8 and group['weight_decay'] == 0.01
            and group.get('foreach') is False and group.get('fused') is False
            and not group.get('amsgrad', False) and not group.get('maximize', False)
            and not group.get('differentiable', False) and not group.get('capturable', False),
            'fixed_native_AdamW_recipe')


def _adapter_tensors(files):
    import torch
    from safetensors.torch import load
    restored = {}
    for name, tensor in load(files['adapter_model.safetensors']).items():
        require(name.endswith(('.lora_A.weight', '.lora_B.weight')), 'exact_serialized_adapter_inventory')
        require(tensor.dtype == torch.float32 and tensor.ndim == 2, 'serialized_adapter_dtype_shape')
        require(bool(torch.isfinite(tensor).all()), 'finite_serialized_adapter')
        restored[name.removesuffix('.weight') + '.default.weight'] = tensor
    require(restored, 'nonempty_serialized_adapter_inventory')
    return restored


def _checkpoint_document(path, raw):
    document = _json(raw)
    require(document['schema'] == native.SCHEMA and document['base_sha256'] == native.BASE_SHA256,
            'checkpoint_schema_and_base')
    require(document['adapter_path'] == str(path.parent/'adapter')
            and document['optimizer_rng_path'] == str(path.parent/'optimizer_rng.pt'),
            'checkpoint_payload_paths_bound_to_COMMIT')
    inventory = document['adapter_files']
    required = {'adapter_config.json', 'adapter_model.safetensors'}
    require(type(inventory) is dict and required <= set(inventory) <= required | {'README.md'},
            'exact_safe_PEFT_file_inventory')
    hashes = document['checkpoint_sha256']
    require(native.digest(inventory) == hashes['adapter'] and hashes['optimizer'] == hashes['rng'],
            'checkpoint_inventory_hash_join')
    return document


def _checkpoint_files(directory, document):
    inventory = document['adapter_files']
    adapter_directory = os.open('adapter', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        require(set(os.listdir(adapter_directory)) == set(inventory), 'exact_adapter_directory_inventory')
        files = {name: _bound(_read_file(adapter_directory, name,
                    512 * 1024**2 if name == 'adapter_model.safetensors' else 1024**2), expected,
                    'adapter_file_binding') for name, expected in inventory.items()}
    finally:
        os.close(adapter_directory)
    optimizer_bytes = _bound(_read_file(directory, 'optimizer_rng.pt', 512 * 1024**2),
                            document['checkpoint_sha256']['optimizer'], 'optimizer_RNG_file_binding')
    return files, optimizer_bytes


def _decoded_checkpoint(document, files, optimizer_bytes):
    import torch
    _json(files['adapter_config.json'])
    restored = _adapter_tensors(files)
    require(_state_hash(restored) == document['adapter_state_sha256'], 'decoded_adapter_state_binding')
    payload = torch.load(BytesIO(optimizer_bytes), map_location='cpu', weights_only=True)
    require(payload.get('experiment') == document.get('experiment'), 'saved_experiment_identity')
    names = payload['parameter_names']
    require(type(names) is list and len(names) == len(set(names)) and set(names) == set(restored),
            'saved_optimizer_parameter_inventory')
    steps = payload['optimizer_steps']
    require(type(steps) is int and steps >= 0 and steps == document['optimizer_steps'],
            'checkpoint_optimizer_step_join')
    optimizer = payload['optimizer']
    groups = optimizer['param_groups']
    require(len(groups) == 1 and groups[0]['params'] == list(range(len(names))), 'saved_optimizer_parameter_order')
    _optimizer_recipe(groups[0])
    states = optimizer['state']
    require(set(states) == (set(range(len(names))) if steps else set()), 'saved_optimizer_state_inventory')
    for index, values in states.items():
        require(set(values) == {'step', 'exp_avg', 'exp_avg_sq'}, 'saved_AdamW_state_fields')
        step = values['step']
        require(torch.is_tensor(step) and step.numel() == 1 and float(step) == steps, 'saved_actual_AdamW_step')
        for key in ('exp_avg', 'exp_avg_sq'):
            tensor = values[key]
            require(torch.is_tensor(tensor) and tensor.shape == restored[names[index]].shape
                    and tensor.dtype == torch.float32 and bool(torch.isfinite(tensor).all()),
                    'finite_exact_AdamW_moments')
        require(bool((values['exp_avg_sq'] >= 0).all()), 'nonnegative_AdamW_second_moment')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random(0).setstate(payload['python_rng'])
    require(type(payload['cuda_rng']) is list and all(torch.is_tensor(state) and state.dtype == torch.uint8
            and state.ndim == 1 and state.numel() > 0 for state in payload['cuda_rng']), 'saved_CUDA_RNG_inventory')
    return restored, payload


def _committed_reference(fork_binding, commit_reference, raw):
    path = _reference(commit_reference)
    root = Path(fork_binding['fork_root'])
    require(path.parent.parent == root and re.fullmatch(r'batch[0-9]{4}', path.parent.name)
            and path.name == 'COMMIT.json', 'fork_local_authority_commit_only')
    if raw is None:
        with _directory(path.parent) as directory:
            raw = _read_file(directory, path.name, 32 * 1024**2)
    document = _json(_bound(raw, commit_reference['sha256'], 'bound_authority_commit'))
    require(document['schema'] == 'R161_REVIEWED_PACKET_FIT_V1' and document['status'] == 'COMMITTED'
            and document['authority_sha256'] == fork_binding['authority_sha256']
            and type(document['batch_index']) is int
            and document['batch_index'] == int(path.parent.name[5:]), 'committed_checkpoint_authority_join')
    reference = document['checkpoint']
    require(_reference(reference) == path.parent/'checkpoint'/'COMMIT.json', 'committed_checkpoint_path_join')
    return reference, raw


@dataclass(frozen=True)
class AdmittedCheckpoint:
    binding_bytes: bytes
    reference_bytes: bytes
    document_bytes: bytes
    adapter_files: tuple
    optimizer_bytes: bytes
    authority_reference_bytes: bytes | None = None
    authority_commit_bytes: bytes | None = None

    def decode(self):
        binding, reference = _json(self.binding_bytes), _json(self.reference_bytes)
        path = _reference(reference)
        if self.authority_reference_bytes is None:
            require(reference['sha256'] == binding['initializer_commit_sha256'],
                    'explicit_initializer_path_hash_binding')
        else:
            require(type(self.authority_commit_bytes) is bytes, 'admitted_authority_bytes_required')
            admitted, unused = _committed_reference(binding, _json(self.authority_reference_bytes),
                                                    self.authority_commit_bytes)
            require(admitted == reference, 'admitted_successor_reference_join')
        document = _checkpoint_document(path, _bound(self.document_bytes, reference['sha256'],
                                                    'bound_checkpoint_reference'))
        files = dict(self.adapter_files)
        require(len(files) == len(self.adapter_files) and set(files) == set(document['adapter_files']),
                'admitted_file_inventory')
        for name, expected in document['adapter_files'].items():
            _bound(files[name], expected, 'adapter_file_binding')
        _bound(self.optimizer_bytes, document['checkpoint_sha256']['optimizer'], 'optimizer_RNG_file_binding')
        restored, payload = _decoded_checkpoint(document, files, self.optimizer_bytes)
        return document, files, restored, payload

    def fingerprint(self):
        document, unused_files, unused_restored, payload = self.decode()
        return fingerprint_payload(payload, document)


def _admit_bytes(fork_binding, reference, commit_reference=None, commit_bytes=None):
    path = _reference(reference)
    require(path.name == 'COMMIT.json', 'checkpoint_COMMIT_required')
    with _directory(path.parent) as directory:
        raw = _bound(_read_file(directory, path.name, 1024**2), reference['sha256'], 'bound_checkpoint_reference')
        document = _checkpoint_document(path, raw)
        files, optimizer_bytes = _checkpoint_files(directory, document)
    admitted = AdmittedCheckpoint(json.dumps(fork_binding).encode(), json.dumps(reference).encode(), raw,
        tuple(files.items()), optimizer_bytes,
        json.dumps(commit_reference).encode() if commit_reference is not None else None, commit_bytes)
    admitted.decode()
    return admitted


def admit_initializer_checkpoint(*, fork_binding, reference):
    _reference(reference)
    require(reference['sha256'] == fork_binding['initializer_commit_sha256'], 'explicit_initializer_path_hash_binding')
    return _admit_bytes(fork_binding, reference)


def admit_committed_checkpoint(*, fork_binding, commit_reference):
    reference, raw = _committed_reference(fork_binding, commit_reference, None)
    return _admit_bytes(fork_binding, reference, commit_reference, raw)


def fingerprint_payload(payload, checkpoint):
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'], 'checkpoint_optimizer_step_join')
    return dict(adapter_sha256=checkpoint['adapter_state_sha256'],
        optimizer_sha256=_state_hash(dict(optimizer=payload['optimizer'],
            parameter_names=payload['parameter_names'])),
        rng_sha256=_state_hash(dict(cpu=payload['cpu_rng'], cuda=payload['cuda_rng'],
            python=payload['python_rng'])),
        optimizer_steps=payload['optimizer_steps'], base_sha256=checkpoint['base_sha256'], base_frozen=True)


class NativeExecutor:
    contract = CONTRACT

    def __init__(self, child, *, fork_binding, execution_kind='VALIDATION_ONLY', device='cuda:0',
                 initializer_reference=None):
        require(execution_kind in ('CPU_TEST_ONLY', 'VALIDATION_ONLY', 'EXTERNALLY_VALIDATED_EXECUTOR'),
                'explicit_executor_purpose')
        require((execution_kind == 'CPU_TEST_ONLY' and device == 'cpu')
                or (execution_kind != 'CPU_TEST_ONLY' and device == 'cuda:0'), 'purpose_device_binding')
        require(set(fork_binding) == {'fork_root', 'mode', 'authority_sha256', 'initializer_commit_sha256'}
                and fork_binding['mode'] in ('learning', 'frozen'), 'exact_fork_binding')
        root = Path(fork_binding['fork_root'])
        require(root.is_absolute() and root == root.resolve(), 'canonical_fork_root')
        require(child.plan['root'] == str(root), 'resident_child_belongs_to_fork')
        require(all(type(fork_binding[key]) is str and re.fullmatch('[0-9a-f]{64}', fork_binding[key])
                    for key in ('authority_sha256', 'initializer_commit_sha256')), 'fork_binding_hashes')
        self.child, self.fork_binding = child, deepcopy(fork_binding)
        self._admitted = {}
        if initializer_reference is not None:
            path = _reference(initializer_reference)
            require(path.name == 'COMMIT.json' and initializer_reference['sha256']
                    == fork_binding['initializer_commit_sha256'], 'explicit_initializer_path_hash_binding')
            self._admitted[str(path)] = initializer_reference['sha256']
        self.execution_kind, self.device = execution_kind, device
        self.uncertain = False
        self.last_update = None
        self._restore_used = False
        self._adapter_config, self._config_set_fields = _serialized_config(child.engine.model)
        self._check_parameters()

    def _check_parameters(self):
        child = self.child
        child.check('reviewed_executor')
        require(_serialized_config(child.engine.model)[0] == self._adapter_config, 'resident_adapter_config_changed')
        parameters = dict(child.engine.model.named_parameters())
        selected = {name: value for name, value in parameters.items() if child.native.is_lora(name)}
        require(selected and set(selected) == set(child.parameters)
                and all(selected[name] is child.parameters[name] for name in selected), 'exact_LoRA_parameter_inventory')
        require(all(not parameter.requires_grad for name, parameter in parameters.items()
                    if not child.native.is_lora(name)), 'base_parameters_frozen')
        require(all(parameter.dtype == child.torch.float32 for parameter in selected.values()), 'FP32_LoRA_only')
        require(isinstance(child.optimizer, child.torch.optim.AdamW), 'actual_AdamW_optimizer')
        groups = child.optimizer.param_groups
        require(len(groups) == 1 and [id(value) for value in groups[0]['params']]
                == [id(value) for value in child.parameters.values()], 'exact_optimizer_parameter_order')
        _optimizer_recipe(groups[0])

    def _check_post_step(self):
        self._check_parameters()
        child, torch = self.child, self.child.torch
        require(type(child.optimizer_steps) is int and child.optimizer_steps > 0, 'post_step_optimizer_counter')
        require(set(child.optimizer.state) == set(child.parameters.values()), 'post_step_exact_optimizer_state_inventory')
        for parameter in child.parameters.values():
            require(bool(torch.isfinite(parameter).all()), 'post_step_finite_adapter_parameters')
            values = child.optimizer.state[parameter]
            require(set(values) == {'step', 'exp_avg', 'exp_avg_sq'}, 'post_step_exact_AdamW_state_fields')
            step = values['step']
            require(torch.is_tensor(step) and step.ndim == 0 and bool(torch.isfinite(step))
                    and float(step) == child.optimizer_steps, 'post_step_actual_AdamW_step')
            for key in ('exp_avg', 'exp_avg_sq'):
                tensor = values[key]
                require(torch.is_tensor(tensor) and tensor.shape == parameter.shape
                        and tensor.dtype == parameter.dtype and tensor.device == parameter.device
                        and bool(torch.isfinite(tensor).all()), 'post_step_finite_exact_AdamW_moments')
            require(bool((values['exp_avg_sq'] >= 0).all()), 'post_step_nonnegative_AdamW_second_moment')

    def snapshot(self):
        self._check_parameters()
        child = self.child
        child.engine.verify_base()
        return fingerprint_payload(dict(optimizer=child.optimizer.state_dict(),
            parameter_names=list(child.parameters), optimizer_steps=child.optimizer_steps,
            cpu_rng=child.torch.get_rng_state(), cuda_rng=child.torch.cuda.get_rng_state_all(),
            python_rng=random.getstate()),
            dict(adapter_state_sha256=child.adapter_hash(), optimizer_steps=child.optimizer_steps,
                 base_sha256=native.BASE_SHA256))

    def _components(self, batch):
        child = self.child
        components = tuple(batch.components)
        require(len(components) == 5 and components[0].label in ('NEW', 'REHEARSAL')
                and components[0].objective_weight == 0.75, 'one_own_component_at_075')
        require(tuple(part.label for part in components[1:]) == tuple('ANCHOR:'+family for family in FAMILIES)
                and all(part.objective_weight == 0.0625 for part in components[1:]), 'four_fixed_anchor_weights')
        for component in components:
            inputs, labels = tuple(component.input_ids), tuple(component.labels)
            require(0 < len(inputs) == len(labels) <= child.plan['context_limit'], 'exact_untrimmed_context')
            require(all(type(token) is int and token >= 0 for token in inputs)
                    and all(type(token) is int and (token == -100 or token >= 0) for token in labels),
                    'integer_token_and_mask_inventory')
            require(tuple(token for token in labels if token != -100) == tuple(component.target_ids)
                    and component.target_ids, 'target_matches_original_unmasked_labels')
            require(all(label == -100 or label == token for token, label in zip(inputs, labels)),
                    'labels_match_original_input_tokens')
            if not component.label.startswith('ANCHOR:'):
                from gpu.orch_r145_suffix_loss import loss_window
                loss_window(EncodedRow(inputs, labels, tuple(component.target_ids)))
        return components

    def update(self, batch):
        require(not self.uncertain, 'uncertain_executor_never_retried')
        require(self.fork_binding['mode'] == 'learning', 'frozen_executor_never_updates')
        self._check_parameters()
        components = self._components(batch)
        child, torch = self.child, self.child.torch
        self.uncertain = True
        losses = []
        try:
            for parameter in child.parameters.values():
                parameter.requires_grad_(True)
            child.engine.model.train()
            child.optimizer.zero_grad(set_to_none=True)
            for component in components:
                child.check('reviewed_microbatch')
                sample = EncodedRow(tuple(component.input_ids), tuple(component.labels), tuple(component.target_ids))
                inputs = torch.tensor([sample.input_ids], dtype=torch.long, device=self.device)
                labels = torch.tensor([sample.labels], dtype=torch.long, device=self.device)
                context = (torch.autocast(device_type='cuda', dtype=torch.bfloat16)
                           if self.device == 'cuda:0' else nullcontext())
                with context:
                    result = child.engine.model(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                        use_cache=False, **loss_arguments(component.label, sample, labels))
                    loss = result.loss
                require(loss.ndim == 0 and bool(torch.isfinite(loss)), 'finite_scalar_component_loss')
                (loss * component.objective_weight).backward()
                losses.append(dict(label=component.label, loss=float(loss.detach().cpu()),
                    objective_weight=component.objective_weight, target_tokens=len(component.target_ids)))
            self._check_parameters()
            require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                        for parameter in child.parameters.values()), 'finite_all_adapter_gradients')
            child.optimizer.step()
            child.optimizer_steps += 1
            self._check_post_step()
            self.last_update = dict(batch_sha256=batch.sha256, optimizer_step=child.optimizer_steps, losses=losses)
        finally:
            child.engine.model.requires_grad_(False)
            child.engine.model.eval()
        self.uncertain = False
        return dict(batch_sha256=batch.sha256, optimizer_step=child.optimizer_steps)

    def admit_committed_checkpoint(self, commit_reference):
        require(not self.uncertain, 'uncertain_executor_cannot_admit_checkpoint')
        reference, unused = _committed_reference(self.fork_binding, commit_reference, None)
        self._admitted[reference['path']] = reference['sha256']
        return deepcopy(reference)

    def _verify_adapter(self, files, *, match_resident=True):
        saved_config = _json(files['adapter_config.json'])
        for key in self._config_set_fields:
            require(type(saved_config.get(key)) is list and all(type(value) is str for value in saved_config[key])
                    and len(set(saved_config[key])) == len(saved_config[key]), 'saved_adapter_config_set')
            saved_config[key] = sorted(saved_config[key])
        require(saved_config == self._adapter_config, 'saved_adapter_config_identity')
        restored = _adapter_tensors(files)
        require(set(restored) == set(self.child.parameters), 'exact_serialized_adapter_inventory')
        for name, tensor in restored.items():
            parameter = self.child.parameters[name]
            require(tensor.dtype == parameter.dtype and tensor.shape == parameter.shape,
                    'serialized_adapter_dtype_shape')
        observed = _state_hash(restored)
        require(not match_resident or observed == self.child.adapter_hash(), 'serialized_adapter_matches_resident_tensors')
        return observed

    def _verify_checkpoint(self, path, directory, raw):
        document = _checkpoint_document(path, raw)
        child = self.child
        require(document.get('experiment') == child.experiment, 'checkpoint_experiment_identity')
        files, optimizer_bytes = _checkpoint_files(directory, document)
        adapter_hash = self._verify_adapter(files)
        require(adapter_hash == document['adapter_state_sha256'], 'decoded_adapter_state_binding')
        unused_restored, payload = _decoded_checkpoint(document, files, optimizer_bytes)
        require(payload['parameter_names'] == list(child.parameters), 'saved_optimizer_parameter_order')
        require(payload.get('experiment') == child.experiment, 'saved_experiment_identity')
        return fingerprint_payload(payload, dict(document, adapter_state_sha256=adapter_hash))

    def restore_admitted_checkpoint(self, admitted):
        require(not self.uncertain, 'uncertain_executor_cannot_restore')
        require(not self._restore_used and self.last_update is None and self.child.optimizer_steps == 0
                and not self.child.optimizer.state, 'restore_only_into_fresh_executor')
        require(type(admitted) is AdmittedCheckpoint and _json(admitted.binding_bytes) == self.fork_binding,
                'restore_exact_fork_admission')
        reference = _json(admitted.reference_bytes)
        if admitted.authority_reference_bytes is None:
            require(self._admitted.get(reference['path']) == reference['sha256'], 'restore_initializer_not_admitted')
        document, files, restored, payload = admitted.decode()
        child = self.child
        self._check_parameters()
        require(document.get('experiment') == child.experiment, 'restore_experiment_identity')
        require(payload['parameter_names'] == list(child.parameters), 'saved_optimizer_parameter_order')
        require(len(payload['cuda_rng']) == (0 if self.device == 'cpu' else 1), 'restore_exact_RNG_device_inventory')
        self._verify_adapter(files, match_resident=False)
        before = fingerprint_payload(payload, document)
        self.uncertain = True
        self._restore_used = True
        from peft import set_peft_model_state_dict
        serialized = {name.removesuffix('.default.weight') + '.weight': tensor for name, tensor in restored.items()}
        result = set_peft_model_state_dict(child.engine.model, serialized, adapter_name='default')
        require(not result.unexpected_keys and not set(child.parameters).intersection(result.missing_keys),
                'exact_PEFT_state_load')
        child.optimizer.load_state_dict(payload['optimizer'])
        child.optimizer.zero_grad(set_to_none=True)
        child.optimizer_steps = payload['optimizer_steps']
        child.engine.model.requires_grad_(False)
        child.engine.model.eval()
        child.torch.set_rng_state(payload['cpu_rng'])
        child.torch.cuda.set_rng_state_all(payload['cuda_rng'])
        random.setstate(payload['python_rng'])
        require(self.snapshot() == before, 'exact_admitted_checkpoint_restore')
        self._admitted[reference['path']] = reference['sha256']
        self.uncertain = False
        return before

    def verify_checkpoint(self, reference):
        require(not self.uncertain, 'uncertain_executor_cannot_verify_checkpoint')
        path = _reference(reference)
        require(self._admitted.get(str(path)) == reference['sha256'], 'checkpoint_not_admitted_before_read')
        self._check_parameters()
        with _directory(path.parent) as directory:
            raw = _bound(_read_file(directory, path.name, 1024**2), reference['sha256'], 'bound_checkpoint_reference')
            return self._verify_checkpoint(path, directory, raw)

    def checkpoint(self, directory):
        require(not self.uncertain, 'uncertain_executor_cannot_checkpoint')
        directory = Path(directory)
        root = Path(self.fork_binding['fork_root'])
        require(directory.is_absolute() and directory == directory.resolve() and directory.is_relative_to(root)
                and not directory.exists(), 'new_fork_local_checkpoint')
        self.uncertain = True
        before = self.snapshot()
        self.child.checkpoint(directory)
        path = directory/'COMMIT.json'
        with _directory(directory) as descriptor:
            raw = _read_file(descriptor, path.name, 1024**2)
            reference = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())
            require(self.snapshot() == before and self._verify_checkpoint(path, descriptor, raw) == before,
                    'exact_nonmutating_saved_state')
        self._admitted[str(path)] = reference['sha256']
        self.uncertain = False
        return reference
