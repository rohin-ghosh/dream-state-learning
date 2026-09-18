"""Native adapter-loading and tokenizer seams; no tasks or campaign launcher."""

from dataclasses import dataclass, replace
import os
from pathlib import Path
from types import SimpleNamespace

from gpu import astra_experienced_event_microloop as source
from gpu import astra_experienced_event_cue_sleep as development
from gpu import astra_reader_audit_lesson_train as masks
from organism_v6 import orch_guided_bridge as bridge
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout


require = bridge.require
_USED_PROCESSES = set()
_IMPORT_PID = os.getpid()


def process_identity():
    status = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return (Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            os.getpid(), int(status[19]))


def state_hash(parameters):
    from organism_v6.pcfl_vertical_train import _state_hash

    return _state_hash(parameters)


def is_lora(name):
    return '.lora_A.' in name or '.lora_B.' in name


@dataclass(frozen=True)
class StageContext:
    private_guidance: tuple = ()
    transient_context: tuple = ()
    sleep_prompt: str | None = None

    def validate(self, binding):
        require(type(self.private_guidance) is tuple
                and all(type(text) is str and text for text in self.private_guidance),
                'explicit_guidance_inventory_required')
        require(type(self.transient_context) is tuple
                and (self.sleep_prompt is None or type(self.sleep_prompt) is str),
                'explicit_context_inventory_required')
        require(bool(self.private_guidance) == binding.parent_present, 'parent_visibility_drift')
        if binding.phase == 'sealed_readout':
            require(self.transient_context == () and self.sleep_prompt is None,
                    'clean_readout_context_required')


def observe_adapter(engine, expected):
    parameters = dict(engine.model.named_parameters())
    selected = {name: parameter for name, parameter in parameters.items() if is_lora(name)}
    require(bool(selected), 'mounted_existing_lora_required')
    require(set(engine.model.peft_config) == {'default'}
            and list(engine.model.active_adapters) == ['default'], 'one_active_default_adapter_required')
    require(not any(getattr(module, 'disable_adapters', False) is True
                    for module in engine.model.modules()), 'mounted_adapter_disabled')
    config = engine.model.peft_config['default']
    require(config.r == 8 and config.lora_alpha == 16 and config.lora_dropout == 0.05
            and set(config.target_modules) == set(source.native.TARGET_MODULES)
            and config.bias == 'none' and not config.modules_to_save
            and not config.use_dora and not config.use_rslora,
            'existing_rank8_native_recipe_required')
    mounted_base = {}
    for name, parameter in engine.model.state_dict(keep_vars=True).items():
        if is_lora(name):
            continue
        require(name.startswith('base_model.model.'), 'unexpected_peft_base_namespace')
        original = name.removeprefix('base_model.model.').replace('.base_layer.', '.')
        require(original not in mounted_base, 'ambiguous_mounted_base_namespace')
        mounted_base[original] = parameter
    require(set(mounted_base) == set(engine.base_references), 'mounted_base_key_drift')
    observed_base = state_hash(mounted_base)
    files = tuple((name, bridge.file_sha256(Path(expected.path) / name)) for name, unused in expected.files)
    observed = bridge.AdapterIdentity(expected.path, state_hash(selected), observed_base, files)
    observed.verify()
    return observed


@dataclass
class LoadedStage:
    engine: object
    binding: bridge.StageBinding
    context: StageContext
    process: tuple
    observed: bridge.AdapterIdentity
    optimizer: object = None

    def verify_unchanged(self):
        require(process_identity() == self.process, 'stage_moved_to_another_process')
        self.context.validate(self.binding)
        current = observe_adapter(self.engine, self.binding.adapter)
        require(current == self.observed, 'loaded_stage_state_changed')
        require(not any(parameter.requires_grad for unused, parameter in self.engine.model.named_parameters()),
                'readonly_stage_has_trainable_parameters')
        return current


def load_stage(binding, *, model_dir, device, gpu_uuid, context, check,
               predecessor_processes=(), engine_factory=None, tokenizer_loader=None):
    require(os.getpid() == _IMPORT_PID, 'native_stage_requires_exec_not_inherited_fork')
    require(binding.phase in ('collection', 'training', 'sealed_readout'), 'known_native_phase_required')
    require(binding.phase != 'training' or binding.arm != bridge.ARMS[1], 'frozen_training_forbidden')
    require(Path(model_dir).is_absolute() and Path(model_dir).is_dir(), 'explicit_local_model_directory_required')
    require(device == 'cuda:0' and type(gpu_uuid) is str and bool(gpu_uuid), 'explicit_single_gpu_binding_required')
    binding.adapter.verify()
    for reference in binding.receipt_refs:
        reference.read()
    context.validate(binding)
    require(type(predecessor_processes) is tuple and all(type(item) is tuple and len(item) == 3
            and type(item[0]) is str and type(item[1]) is int and type(item[2]) is int
            for item in predecessor_processes), 'explicit_predecessor_processes_required')
    current_process = process_identity()
    fresh = current_process not in _USED_PROCESSES and current_process not in predecessor_processes
    if binding.fresh_process:
        require(fresh and (binding.cycle == 0 or bool(predecessor_processes)), 'fresh_readout_process_required')
    _USED_PROCESSES.add(current_process)
    options = SimpleNamespace(model_dir=str(model_dir), device=device, gpu_uuid=gpu_uuid,
                              phase='readout', adapter_dir=binding.adapter.path,
                              expected_base_sha256=binding.adapter.base_sha256)
    tokenizer = (tokenizer_loader or source.native.load_local_tokenizer)(options.model_dir)
    engine = (engine_factory or source.Engine)(options, tokenizer, check=check)
    observed = observe_adapter(engine, binding.adapter)
    require(not any(parameter.requires_grad for unused, parameter in engine.model.named_parameters()),
            'initial_loaded_actor_must_be_frozen')
    binding.verify_loaded(adapter=observed, base_sha256=observed.base_sha256,
                          parent_present=bool(context.private_guidance), fresh_process=fresh,
                          transient_context=context.transient_context, sleep_prompt=context.sleep_prompt)
    return LoadedStage(engine, binding, context, current_process, observed)


def load_collection(plan, **kwargs):
    return load_stage(plan.binding('collection'), **kwargs)


def load_training(plan, **kwargs):
    binding = plan.binding('training')
    recipe = plan.contract.manifest(plan.lineage.arm)['recipe']
    loaded = load_stage(binding, **kwargs)
    engine = loaded.engine
    engine.torch.manual_seed(recipe['seed'])
    parameters = development.enable_existing_adapter(engine)
    require(state_hash(parameters) == loaded.observed.state_sha256, 'enable_training_changed_adapter')
    require(not any(parameter.requires_grad for name, parameter in engine.model.named_parameters()
                    if not is_lora(name)), 'base_must_remain_frozen')
    kwargs = dict(recipe['optimizer_kwargs'], betas=tuple(recipe['optimizer_kwargs']['betas']))
    loaded.optimizer = engine.torch.optim.AdamW(list(parameters.values()), lr=recipe['learning_rate'], **kwargs)
    require(not loaded.optimizer.state, 'fresh_optimizer_required_no_restore')
    engine.model.train()
    return loaded


def load_readout(binding, **kwargs):
    require(binding.phase == 'sealed_readout', 'output_readout_binding_required')
    return load_stage(binding, **kwargs)


def encode_child_captures(captures, capture_hashes, collection_binding, tokenizer, *,
                          private_guidance, max_context, max_supervised_tokens):
    require(len(captures) == len(capture_hashes) and bool(captures), 'nonempty_exact_capture_hashes_required')
    require(type(max_context) is int and max_context > 0 and type(max_supervised_tokens) is int
            and max_supervised_tokens > 1, 'explicit_untruncated_token_budgets_required')
    require(tokenizer.eos_token == '<|im_end|>' and type(tokenizer.eos_token_id) is int
            and source.native._encode(tokenizer, tokenizer.eos_token) == (tokenizer.eos_token_id,),
            'exact_qwen_eot_required')
    projected, encoded = [], []
    for capture, digest in zip(captures, capture_hashes):
        row = bridge.project_child_capture(capture, digest, collection_binding, private_guidance=private_guidance)
        prefix, target = row['prefix'], row['assistant']
        messages = prefix + [dict(role='assistant', content=target)]
        context = tokenizer.apply_chat_template(prefix, tokenize=False, add_generation_prompt=True, return_dict=False)
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, return_dict=False)
        require(full == context + target + tokenizer.eos_token + '\n', 'exact_native_template_boundary_required')
        prefix_ids = source.native._encode(tokenizer, context)
        target_ids = source.native._encode(tokenizer, target)
        suffix_ids = source.native._encode(tokenizer, '\n')
        require(not set(tokenizer.all_special_ids).intersection(target_ids), 'child_target_special_token_forbidden')
        supervised = target_ids + (tokenizer.eos_token_id,)
        sequence = source.native._encode(tokenizer, full)
        require(len(sequence) <= max_context and len(supervised) <= max_supervised_tokens,
                'untruncated_declared_sequence_budget_required')
        require(source.native._decode(tokenizer, sequence) == full
                and source.native._decode(tokenizer, prefix_ids) == context
                and source.native._decode(tokenizer, supervised) == target + tokenizer.eos_token
                and source.native._decode(tokenizer, suffix_ids) == '\n', 'exact_native_token_roundtrip_required')
        require(tuple(tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=False,
                return_dict=False, truncation=False, padding=False)) == sequence, 'native_template_token_ids_drift')
        native_row = source.native.EncodedRow(sequence,
            (-100,) * len(prefix_ids) + supervised + (-100,) * len(suffix_ids), supervised)
        bridge.validate_encoding_boundary(native_row, prefix_ids=prefix_ids, target_ids=target_ids,
            suffix_ids=suffix_ids, eos_token_id=tokenizer.eos_token_id, validate_masks=masks.validate_masks)
        projected.append(row)
        encoded.append(native_row)
    return tuple(projected), tuple(encoded)


def assemble_replay(legacy_encoded, new_encoded, layout, *, legacy_reference, eos_token_id):
    require(isinstance(layout, GoalReplayLayout) and len(legacy_encoded) == 222
            and len(new_encoded) == layout.new_trajectory_rows, 'declared_legacy_and_new_layout_required')
    require(tuple(legacy_encoded) == tuple(legacy_reference), 'legacy_reference_encoding_drift')
    encoded = tuple(legacy_encoded) + tuple(new_encoded)
    masks.validate_masks(encoded, eos_token_id)
    return encoded


def training_batch(encoded, layout, update, *, pad_id, replay_arm='FULL_TARGET'):
    require(len(encoded) == layout.row_count, 'declared_replay_row_count_required')
    indexes = layout.training_indexes(update)
    masked = set(layout.masked_row_indexes(replay_arm))
    selected = [replace(encoded[index], labels=(-100,) * len(encoded[index].labels))
                if index in masked else encoded[index] for index in indexes]
    batch = source.native.collate(selected, pad_id=pad_id)
    reference, active, scale = development.loss_normalization(encoded, indexes, batch)
    return indexes, batch, reference, active, scale
