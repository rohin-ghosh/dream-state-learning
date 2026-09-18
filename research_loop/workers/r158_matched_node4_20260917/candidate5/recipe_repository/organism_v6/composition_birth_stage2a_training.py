"""Bounded, in-memory Stage2A training mechanics, not execution authorization.

The caller supplies an already prepared model, all 512 paired batches, the
planned LoRA inventory, and existing preparation/initialization/lineage bindings.
Nothing is loaded, initialized as an adapter, serialized to disk, or launched.
Torch is imported only on the native path. Runtime/model/tokenizer provenance
authentication and the decision to open D2 remain the parent's responsibility.

Use one trainer per arm. ``train_stage('D1')`` ends at update 256; ``checkpoint``
returns detached CPU copies, including AdamW moments and CPU/all initialized
CUDA RNG states. A new trainer accepts that checkpoint, never a weight-only
continuation. D2 is a separate explicit call ending at 512. Checkpoint digests
detect corruption, not authenticity. No native or scientific qualification is
implied by synthetic fixtures or these source-only mechanics.

Still required on an independently authorized existing native stack: the tiny
CPU continuity tests, pinned Qwen/PEFT bf16 and trainable-inventory validation,
paired CUDA RNG receipts, and an exact parent-owned checkpoint storage roundtrip.
"""

from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import re
from types import MappingProxyType

from organism_v6 import composition_birth_stage2a_tape as tape
from organism_v6 import composition_birth_stage2a_tokenization as tokenization


STATUS = "PARTIAL_SOURCE_ONLY"
SCIENCE_GATES = MappingProxyType(dict.fromkeys(tokenization.SCIENCE_GATES, False))
TARGET_MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
OPTIMIZER_RECIPE = MappingProxyType(dict(
    lr=3e-5, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01,
    amsgrad=False, maximize=False, capturable=False, differentiable=False,
    foreach=False, fused=False,
))
RECIPE = MappingProxyType(dict(
    optimizer="torch.optim.AdamW", **OPTIMIZER_RECIPE, rank=8, alpha=16,
    dropout=0.05, target_modules=TARGET_MODULES, bias="none", task_type="CAUSAL_LM",
    forward_dtype="bfloat16", batch_size=4, gradient_accumulation=1,
    gradient_checkpointing=True, padding_side="right", max_context=16384,
    packing=False, truncation=False, splitting=False, skipped_batches=False,
    scheduler=False, warmup=False, gradient_scaler=False, gradient_clipping=False,
))
_LORA_NAME = re.compile(
    r"(.+\.layers\.)([0-9]+)\.(self_attn|mlp)\.(" + "|".join(TARGET_MODULES)
    + r")\.lora_([AB])\.([^.]+)\.weight"
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("ascii")).hexdigest()


def _sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_recipe(recipe):
    """Pure validation; bools cannot stand in for numeric recipe pins."""
    _require(isinstance(recipe, (dict, MappingProxyType)) and set(recipe) == set(RECIPE),
             "exact_recipe_keys_required")
    for key, expected in RECIPE.items():
        _require(type(recipe[key]) is type(expected) and recipe[key] == expected,
                 "recipe_drift:" + key)


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    shape: tuple[int, int]
    dtype: str


def validate_trainable_roster(roster, *, layer_count, adapter_name):
    """Validate explicit ordered names, not a substring-selected parameter set.

    bf16 forward does not specify PEFT's adapter storage promotion. The caller
    must pin each adapter's actual float32 or bfloat16 storage in this roster;
    native validation and resumption require that exact dtype, never a cast.
    """
    _require(type(layer_count) is int and layer_count > 0, "invalid_layer_count")
    _require(type(adapter_name) is str and re.fullmatch(r"[A-Za-z0-9_-]+", adapter_name),
             "invalid_adapter_name")
    _require(type(roster) is tuple and len(roster) == layer_count * 14,
             "all_layer_lora_roster_required")
    seen, prefixes = set(), set()
    for spec in roster:
        _require(type(spec) is ParameterSpec and type(spec.name) is str, "parameter_spec_required")
        match = _LORA_NAME.fullmatch(spec.name)
        _require(match is not None, "non_lora_trainable_name")
        prefix, layer, group, module, side, adapter = match.groups()
        _require(layer == str(int(layer)) and int(layer) < layer_count and adapter == adapter_name,
                 "lora_layer_or_adapter_drift")
        _require(group == ("self_attn" if module.endswith("_proj") and module in TARGET_MODULES[:4]
                           else "mlp"), "lora_module_group_drift")
        _require(type(spec.shape) is tuple and len(spec.shape) == 2
                 and all(type(size) is int and size > 0 for size in spec.shape)
                 and spec.shape[0 if side == "A" else 1] == 8, "lora_shape_or_rank_drift")
        _require(spec.dtype in ("torch.float32", "torch.bfloat16"), "lora_storage_dtype_required")
        key = (int(layer), module, side)
        _require(key not in seen, "duplicate_lora_parameter")
        seen.add(key)
        prefixes.add(prefix)
    _require(len(prefixes) == 1, "mixed_lora_model_prefixes")
    return roster


def _token_tuple(value, *, nonempty=True):
    return (type(value) is tuple and (bool(value) or not nonempty)
            and all(type(token) is int and token >= 0 for token in value))


def _validate_row(row, arm):
    _require(type(row) is tokenization.TokenizedArm and row.record.arm == arm, "typed_arm_row_required")
    tokenization._validate_record(row.record)
    for values in (row.context_ids, row.target_ids, row.suffix_ids, row.input_ids):
        _require(_token_tuple(values), "invalid_row_token_ids")
    _require(type(row.eos_token_id) is int and type(row.pad_token_id) is int
             and min(row.eos_token_id, row.pad_token_id) >= 0
             and row.eos_token_id != row.pad_token_id, "invalid_special_ids")
    _require(len(row.target_ids) >= 2 and row.target_ids[-1] == row.eos_token_id
             and row.target_ids.count(row.eos_token_id) == 1
             and row.pad_token_id not in row.target_ids, "target_content_plus_one_eos_required")
    _require(row.suffix_roundtrip_bytes == b"\n"
             and not {row.eos_token_id, row.pad_token_id}.intersection(row.suffix_ids),
             "exact_masked_template_lf_required")
    _require(row.input_ids == row.context_ids + row.target_ids + row.suffix_ids
             and len(row.input_ids) <= 16384, "row_truncation_or_context_overflow")
    _require(type(row.labels) is tuple
             and all(type(label) is int for label in row.labels)
             and row.labels == (-100,) * len(row.context_ids) + row.target_ids
             + (-100,) * len(row.suffix_ids), "content_eos_only_loss_mask_required")
    _require(type(row.attention_mask) is tuple
             and all(type(mask) is int for mask in row.attention_mask)
             and row.attention_mask == (1,) * len(row.input_ids), "unpadded_row_attention_required")
    _require(type(row.record.unit.target_bytes) is bytes
             and sha256(row.record.unit.target_bytes).hexdigest() == row.record.unit.target_sha256,
             "target_hash_drift")
    _require(row.sequence_roundtrip_bytes == row.context_roundtrip_bytes
             + row.target_roundtrip_bytes + b"\n", "sequence_roundtrip_drift")
    _require(row.target_roundtrip_bytes == row.record.unit.target_bytes + b"<|im_end|>",
             "target_roundtrip_drift")
    _require(row.count_basis in tokenization.COUNT_BASES, "unknown_tokenization_basis")


def validate_batches(batches, *, master):
    """Check every D1/D2 slot before any update; return a binding digest.

    This checks the prepared representation, not tokenizer authentication or
    upstream semantic/contamination qualification. Repeated units must retain
    exactly the same source/tokenization record within each arm.
    """
    expected = tape.build_presentation_tape(master=master, unit_ids=tape.unit_identifiers())
    _require(type(batches) is tuple and len(batches) == 512, "complete_512_update_plan_required")
    rows, special_ids, entries = {}, set(), []
    for batch, presentation in zip(batches, expected):
        _require(type(batch) is tokenization.PairedBatch
                 and type(batch.presentation) is tape.PresentationBatch
                 and all(type(value) is int for value in (
                     batch.presentation.update_number, batch.presentation.presentation_index,
                     batch.presentation.rng_start_seed))
                 and batch.presentation == presentation, "planned_tape_or_seed_drift")
        _require(type(batch.target_hashes) is tuple and len(batch.target_hashes) == 4
                 and type(batch.target_token_counts) is tuple and len(batch.target_token_counts) == 4
                 and all(type(count) is int for count in batch.target_token_counts), "batch_targets_required")
        for arm, prepared in (("CLOSED", batch.closed), ("ATOM_LOCAL", batch.atom_local)):
            _require(type(prepared) is tokenization.ArmBatch and prepared.arm == arm
                     and type(prepared.records) is tuple and len(prepared.records) == 4,
                     "exact_batch_four_no_packing_required")
            _require(type(prepared.padding_length) is int and 1 <= prepared.padding_length <= 16384,
                     "invalid_padding_width")
            for field in (prepared.input_ids, prepared.labels, prepared.attention_mask):
                _require(type(field) is tuple and len(field) == 4, "batch_four_tensor_rows_required")
            for slot, row in enumerate(prepared.records):
                _require(type(row) is tokenization.TokenizedArm, "typed_arm_row_required")
                unit_id = presentation.unit_ids[slot]
                key = (arm, unit_id)
                if key not in rows:
                    _validate_row(row, arm)
                    rows[key] = row
                else:
                    _require(row == rows[key], "repeated_unit_record_drift")
                _require(row.record.unit.unit_id == unit_id
                         and row.record.unit.target_sha256 == batch.target_hashes[slot]
                         and len(row.target_ids) == batch.target_token_counts[slot], "batch_slot_or_target_drift")
                padding = prepared.padding_length - len(row.input_ids)
                _require(padding >= 0, "batch_truncation_forbidden")
                for actual, desired in (
                    (prepared.input_ids[slot], row.input_ids + (row.pad_token_id,) * padding),
                    (prepared.labels[slot], row.labels + (-100,) * padding),
                    (prepared.attention_mask[slot], row.attention_mask + (0,) * padding),
                ):
                    _require(type(actual) is tuple and all(type(value) is int for value in actual)
                             and actual == desired, "right_padding_or_loss_mask_drift")
                special_ids.add((row.eos_token_id, row.pad_token_id))
        for closed, atom in zip(batch.closed.records, batch.atom_local.records):
            _require(closed.record.unit == atom.record.unit
                     and closed.target_ids == atom.target_ids
                     and closed.target_roundtrip_bytes == atom.target_roundtrip_bytes
                     and closed.identifier_tokenization == atom.identifier_tokenization
                     and closed.suffix_ids == atom.suffix_ids, "paired_target_or_suffix_drift")
        entries.append((asdict(presentation), batch.closed.padding_length, batch.atom_local.padding_length))
    _require(len(rows) == 512 and len(special_ids) == 1, "roster_or_special_id_drift")
    commands = Counter(row.record.unit.command.split()[0] for (arm, _), row in rows.items() if arm == "CLOSED")
    _require(commands == {"READ": 96, "STEP": 64, "THINK": 64, "STOP": 32}, "target_command_roster_drift")
    return _digest(dict(entries=entries, rows=[(key, _digest(_plain(asdict(row))))
                                              for key, row in sorted(rows.items())]))


def _plain(value):
    if type(value) is bytes:
        return {"bytes_hex": value.hex()}
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _torch():
    import torch
    return torch


def tensor_sha256(tensor):
    """Hash shape, dtype and exact storage bytes (including bf16)."""
    torch = _torch()
    value = tensor.detach().cpu().contiguous()
    result = sha256(_digest([str(value.dtype), list(value.shape)]).encode("ascii"))
    raw = value.reshape(-1).view(torch.uint8)
    for start in range(0, raw.numel(), 1024 * 1024):
        chunk = raw[start:start + 1024 * 1024]
        try:
            result.update(chunk.numpy().tobytes())
        except RuntimeError:
            result.update(bytes(chunk.tolist()))
    return result.hexdigest()


def adapter_sha256(model, roster):
    """Compute the same digest for caller-owned initialization and checkpoints."""
    parameters = dict(model.named_parameters())
    return _digest([(spec.name, tensor_sha256(parameters[spec.name])) for spec in roster])


def _tree_copy(value):
    torch = _torch()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: _tree_copy(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(_tree_copy(item) for item in value)
    return value


def _tree_hash(value):
    torch = _torch()
    if isinstance(value, torch.Tensor):
        return {"tensor_sha256": tensor_sha256(value)}
    if isinstance(value, dict):
        return [[key, _tree_hash(item)] for key, item in value.items()]
    if isinstance(value, (tuple, list)):
        return [_tree_hash(item) for item in value]
    return value


def _rng_state():
    torch = _torch()
    return dict(cpu=torch.get_rng_state().clone(),
                cuda=tuple(state.clone() for state in torch.cuda.get_rng_state_all())
                if torch.cuda.is_initialized() else ())


def _rng_hashes(state):
    return dict(cpu=tensor_sha256(state["cpu"]),
                cuda=tuple(tensor_sha256(item) for item in state["cuda"]))


def _validate_rng(state):
    torch = _torch()
    _require(type(state) is dict and set(state) == {"cpu", "cuda"}
             and type(state["cuda"]) is tuple, "complete_rng_checkpoint_required")
    generators = tuple(torch.cuda.default_generators) if torch.cuda.is_initialized() else ()
    _require(len(state["cuda"]) == len(generators), "cuda_rng_topology_drift")
    for saved, device in ((state["cpu"], "cpu"),) + tuple(
            (saved, generator.device) for saved, generator in zip(state["cuda"], generators)):
        _require(isinstance(saved, torch.Tensor) and saved.device.type == "cpu"
                 and saved.dtype == torch.uint8 and saved.ndim == 1, "invalid_rng_tensor")
        try:
            torch.Generator(device=device).set_state(saved)
        except RuntimeError as error:
            raise ValueError("invalid_rng_state") from error


def _restore_rng(state):
    torch = _torch()
    torch.set_rng_state(state["cpu"])
    if state["cuda"]:
        torch.cuda.set_rng_state_all(list(state["cuda"]))


def _validate_model(model, roster, layer_count, adapter_name):
    torch = _torch()
    named = tuple((name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad)
    _require(tuple(name for name, _ in named) == tuple(spec.name for spec in roster), "exact_trainable_names_required")
    _require(len({id(parameter) for _, parameter in named}) == len(named), "aliased_trainables")
    devices = {parameter.device for _, parameter in named}
    _require(len(devices) == 1 and next(iter(devices)).type in ("cpu", "cuda"), "single_prepared_device_required")
    device = next(iter(devices))
    _require(device.type != "cuda" or torch.cuda.is_initialized(), "cuda_must_already_be_initialized")
    for spec, (_, parameter) in zip(roster, named):
        _require(tuple(parameter.shape) == spec.shape and str(parameter.dtype) == spec.dtype
                 and bool(torch.isfinite(parameter).all()), "trainable_shape_dtype_or_finiteness_drift")
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            _require(".lora_" not in name, "unplanned_frozen_adapter")
            _require(not parameter.is_floating_point() or parameter.dtype == torch.bfloat16,
                     "prepared_base_must_be_bfloat16")
    _require(model.config.num_hidden_layers == layer_count and model.is_gradient_checkpointing
             and model.config.use_cache is False, "prepared_checkpointing_or_layer_config_drift")
    _require(set(model.peft_config) == {adapter_name} and list(model.active_adapters) == [adapter_name],
             "one_active_prepared_adapter_required")
    config = model.peft_config[adapter_name]
    for key, expected in dict(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                              task_type="CAUSAL_LM", init_lora_weights=True).items():
        _require(getattr(config, key, None) == expected, "lora_config_drift:" + key)
    _require(set(config.target_modules) == set(TARGET_MODULES), "lora_target_modules_drift")
    for key in ("use_rslora", "use_dora", "rank_pattern", "alpha_pattern", "modules_to_save"):
        _require(not getattr(config, key, None), "unsupported_lora_config:" + key)
    for spec in roster:
        if ".lora_A." not in spec.name:
            continue
        module = model.get_submodule(spec.name.split(".lora_A.")[0])
        _require(module.r[adapter_name] == 8 and module.lora_alpha[adapter_name] == 16
                 and module.scaling[adapter_name] == 2
                 and module.lora_dropout[adapter_name].p == 0.05
                 and not module.disable_adapters and not module.merged, "effective_lora_recipe_drift")
    return named, device


def _validate_model_batches(model, batches):
    vocabulary_size = model.get_input_embeddings().weight.shape[0]
    seen = set()
    for batch in batches:
        for prepared in (batch.closed, batch.atom_local):
            _require(prepared.padding_length <= model.config.max_position_embeddings,
                     "prepared_model_context_overflow")
            for row in prepared.records:
                key = (prepared.arm, row.record.unit.unit_id)
                if key not in seen:
                    _require(max(row.input_ids + (row.pad_token_id,)) < vocabulary_size,
                             "prepared_token_outside_model_vocabulary")
                    seen.add(key)


def validate_stage_cursor(completed_updates, cursor):
    """Pure boundary validation; cursor counts consumed examples, not batches."""
    _require(type(completed_updates) is int and completed_updates in (256, 512)
             and type(cursor) is int and cursor == 4 * completed_updates,
             "checkpoint_stage_or_cursor_drift")


def _validate_optimizer_state(state_dict, roster, completed):
    torch = _torch()
    _require(type(state_dict) is dict and set(state_dict) == {"state", "param_groups"}, "optimizer_checkpoint_required")
    groups, states = state_dict["param_groups"], state_dict["state"]
    _require(type(groups) is list and len(groups) == 1 and type(states) is dict, "one_adamw_group_required")
    group = groups[0]
    _require(type(group) is dict and group.get("params") == list(range(len(roster))), "optimizer_parameter_order_drift")
    _require(set(group) <= set(OPTIMIZER_RECIPE) | {"params", "decoupled_weight_decay"}, "unknown_optimizer_options")
    if "decoupled_weight_decay" in group:
        _require(group["decoupled_weight_decay"] is True, "adamw_weight_decay_drift")
    for key, expected in OPTIMIZER_RECIPE.items():
        _require(type(group.get(key)) is type(expected) and group[key] == expected, "optimizer_recipe_drift:" + key)
    _require(set(states) == (set(range(len(roster))) if completed else set()), "missing_or_extra_optimizer_moments")
    for index, spec in enumerate(roster):
        if not completed:
            break
        state = states[index]
        _require(type(state) is dict and set(state) == {"step", "exp_avg", "exp_avg_sq"}, "exact_adamw_state_required")
        step = state["step"]
        _require(isinstance(step, torch.Tensor) and step.shape == torch.Size([])
                 and step.device.type == "cpu" and step.dtype == torch.float32
                 and step.item() == completed, "optimizer_step_counter_drift")
        for key in ("exp_avg", "exp_avg_sq"):
            value = state[key]
            _require(isinstance(value, torch.Tensor) and tuple(value.shape) == spec.shape
                     and str(value.dtype) == spec.dtype and bool(torch.isfinite(value).all()),
                     "optimizer_moment_shape_dtype_or_finiteness_drift")
        _require(bool((state["exp_avg_sq"] >= 0).all()), "negative_second_moment")


class StatefulTrainer:
    """One explicit lineage, two bounded stages, no file/launch/scoring hooks.

    Both arms must be supplied the same planned batches and initial adapter
    digest, but distinct caller-owned models and lineage IDs. This class does
    not create or authenticate that shared initialization. A failed numerical
    update poisons this instance; it cannot skip/retry or emit a checkpoint.
    """

    def __init__(self, model, *, arm, master, batches, trainable_roster, layer_count,
                 adapter_name, lineage_id, preparation_sha256, initial_adapter_sha256,
                 recipe=RECIPE, checkpoint=None):
        validate_recipe(recipe)
        validate_trainable_roster(trainable_roster, layer_count=layer_count, adapter_name=adapter_name)
        batch_digest = validate_batches(batches, master=master)
        _require(arm in ("CLOSED", "ATOM_LOCAL"), "fitted_arm_required")
        _require(type(lineage_id) is str and bool(lineage_id) and lineage_id.isascii(), "explicit_lineage_required")
        _require(_sha(preparation_sha256) and _sha(initial_adapter_sha256), "explicit_preparation_and_initialization_bindings_required")
        self.model, self.arm, self.batches = model, arm, batches
        self._master = master
        self.roster = trainable_roster
        self._model_config = (layer_count, adapter_name)
        self.named, self.device = _validate_model(model, trainable_roster, layer_count, adapter_name)
        _validate_model_batches(model, batches)
        self.binding = dict(arm=arm, lineage_id=lineage_id, preparation_sha256=preparation_sha256,
                            initial_adapter_sha256=initial_adapter_sha256, batches_sha256=batch_digest,
                            roster=[asdict(spec) for spec in trainable_roster], recipe=dict(RECIPE),
                            torch_version=str(_torch().__version__), device=str(self.device))
        self.completed_updates, self.receipts, self._failed = 0, [], False
        if checkpoint is not None:
            self._validate_checkpoint(checkpoint)
        else:
            _require(adapter_sha256(model, self.roster) == initial_adapter_sha256,
                     "initial_adapter_bytes_differ_from_caller_binding")
        self.optimizer = _torch().optim.AdamW([parameter for _, parameter in self.named], **OPTIMIZER_RECIPE)
        _validate_optimizer_state(self.optimizer.state_dict(), self.roster, 0)
        if checkpoint is not None:
            self.optimizer.load_state_dict(_tree_copy(checkpoint["optimizer"]))
            _validate_optimizer_state(self.optimizer.state_dict(), self.roster, checkpoint["completed_updates"])
            _require(_tree_hash(self.optimizer.state_dict()) == _tree_hash(checkpoint["optimizer"]),
                     "optimizer_restore_changed_bytes")
            with _torch().no_grad():
                for name, parameter in self.named:
                    parameter.copy_(checkpoint["adapter"][name])
            _restore_rng(checkpoint["rng"])
            self.completed_updates = checkpoint["completed_updates"]
            self.receipts = _tree_copy(checkpoint["receipts"])
        self._boundary = self._snapshot()

    @property
    def cursor(self):
        return self.completed_updates * 4

    def _snapshot(self):
        return dict(adapter={name: parameter.detach().cpu().clone() for name, parameter in self.named},
                    optimizer=_tree_copy(self.optimizer.state_dict()), rng=_rng_state())

    def _validate_checkpoint(self, checkpoint):
        torch = _torch()
        keys = {"format", "binding", "completed_updates", "cursor", "adapter", "optimizer", "rng", "receipts", "sha256"}
        _require(type(checkpoint) is dict and set(checkpoint) == keys and checkpoint["format"] == "stage2a-state-v1",
                 "complete_stateful_checkpoint_required")
        _require(checkpoint["binding"] == self.binding, "checkpoint_lineage_or_plan_binding_drift")
        completed = checkpoint["completed_updates"]
        validate_stage_cursor(completed, checkpoint["cursor"])
        _require(checkpoint["sha256"] == _digest(_tree_hash({key: value for key, value in checkpoint.items()
                                                            if key != "sha256"})), "checkpoint_digest_mismatch")
        adapter = checkpoint["adapter"]
        _require(type(adapter) is dict and tuple(adapter) == tuple(spec.name for spec in self.roster),
                 "checkpoint_adapter_roster_drift")
        for spec in self.roster:
            value = adapter[spec.name]
            _require(isinstance(value, torch.Tensor) and value.device.type == "cpu"
                     and tuple(value.shape) == spec.shape and str(value.dtype) == spec.dtype
                     and bool(torch.isfinite(value).all()), "invalid_checkpoint_adapter_tensor")
        _validate_optimizer_state(checkpoint["optimizer"], self.roster, completed)
        _validate_rng(checkpoint["rng"])
        receipts = checkpoint["receipts"]
        _require(type(receipts) is list and len(receipts) == completed, "complete_loss_receipts_required")
        for update, receipt in enumerate(receipts, 1):
            batch = self.batches[update - 1]
            prepared = batch.closed if self.arm == "CLOSED" else batch.atom_local
            _require(type(receipt) is dict and type(receipt.get("update_number")) is int
                     and receipt["update_number"] == update and receipt.get("arm") == self.arm
                     and type(receipt.get("loss")) is float and math.isfinite(receipt["loss"]), "invalid_loss_receipt")
            expected = dict(presentation_index=batch.presentation.presentation_index,
                            unit_ids=batch.presentation.unit_ids, target_hashes=batch.target_hashes,
                            target_token_counts=batch.target_token_counts,
                            prefix_token_counts=tuple(len(row.context_ids) for row in prepared.records),
                            accounting=dict(prepared.accounting), rng_start_seed=batch.presentation.rng_start_seed,
                            masks_identical_claim=False)
            _require(all(type(receipt.get(key)) is type(value) and receipt[key] == value
                         for key, value in expected.items()), "receipt_tape_or_accounting_drift")
            for key in ("pre_forward_rng", "post_forward_rng", "post_update_rng"):
                hashes = receipt.get(key)
                _require(type(hashes) is dict and set(hashes) == {"cpu", "cuda"}
                         and _sha(hashes["cpu"]) and type(hashes["cuda"]) is tuple
                         and len(hashes["cuda"]) == len(checkpoint["rng"]["cuda"])
                         and all(_sha(value) for value in hashes["cuda"]), "invalid_rng_receipt")
        _require(receipts[-1]["post_update_rng"] == _rng_hashes(checkpoint["rng"]),
                 "checkpoint_boundary_rng_receipt_drift")

    def checkpoint(self):
        """Return an owned copy of the exact training boundary, not ambient RNG.

        Evaluation or another arm can consume global RNG after a stage. That
        must not replace this lineage's saved end-of-update state.
        """
        _require(not self._failed and self.completed_updates in (256, 512), "completed_stage_checkpoint_required")
        checkpoint = dict(format="stage2a-state-v1", binding=_tree_copy(self.binding),
                          completed_updates=self.completed_updates, cursor=self.cursor,
                          **_tree_copy(self._boundary), receipts=_tree_copy(self.receipts))
        checkpoint["sha256"] = _digest(_tree_hash(checkpoint))
        return checkpoint

    def train_stage(self, stage):
        """Run exactly 256 real batched forwards/backwards/steps, or fail closed."""
        _require(not self._failed, "failed_lineage_cannot_retry")
        _require((stage, self.completed_updates) in (("D1", 0), ("D2", 256)), "invalid_stage_transition")
        named, device = _validate_model(self.model, self.roster, *self._model_config)
        _require(validate_batches(self.batches, master=self._master) == self.binding["batches_sha256"],
                 "out_of_band_plan_mutation")
        _require(device == self.device and tuple(id(parameter) for _, parameter in named)
                 == tuple(id(parameter) for _, parameter in self.named), "replaced_live_trainables")
        _require(type(self.optimizer) is _torch().optim.AdamW and len(self.optimizer.param_groups) == 1
                 and tuple(id(parameter) for parameter in self.optimizer.param_groups[0]["params"])
                 == tuple(id(parameter) for _, parameter in self.named), "live_optimizer_parameter_order_drift")
        _require(_tree_hash(self._snapshot()["adapter"]) == _tree_hash(self._boundary["adapter"])
                 and _tree_hash(self.optimizer.state_dict()) == _tree_hash(self._boundary["optimizer"]),
                 "out_of_band_lineage_mutation")
        _validate_optimizer_state(self.optimizer.state_dict(), self.roster, self.completed_updates)
        _validate_rng(self._boundary["rng"])
        _restore_rng(self._boundary["rng"])
        torch = _torch()
        end = 256 if stage == "D1" else 512
        try:
            for batch in self.batches[self.completed_updates:end]:
                prepared = batch.closed if self.arm == "CLOSED" else batch.atom_local
                inputs = {key: torch.tensor(getattr(prepared, key), dtype=torch.long, device=self.device)
                          for key in ("input_ids", "labels", "attention_mask")}
                self.model.train()
                self.optimizer.zero_grad(set_to_none=True)
                seed = batch.presentation.rng_start_seed
                with torch.autocast(device_type=self.device.type, dtype=torch.bfloat16):
                    torch.manual_seed(seed)
                    if torch.cuda.is_initialized():
                        torch.cuda.manual_seed_all(seed)
                    pre_forward = _rng_hashes(_rng_state())
                    output = self.model(**inputs, use_cache=False)
                    post_forward = _rng_hashes(_rng_state())
                    loss = output.loss
                _require(isinstance(loss, torch.Tensor) and loss.ndim == 0 and loss.requires_grad
                         and bool(torch.isfinite(loss)), "finite_scalar_training_loss_required")
                loss.backward()
                _require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                             for _, parameter in self.named), "missing_or_nonfinite_lora_gradient")
                self.optimizer.step()
                update = batch.presentation.update_number
                _validate_optimizer_state(self.optimizer.state_dict(), self.roster, update)
                _require(all(bool(torch.isfinite(parameter).all()) for _, parameter in self.named),
                         "nonfinite_adapter_after_step")
                self.completed_updates = update
                self.receipts.append(dict(
                    arm=self.arm, update_number=update, presentation_index=batch.presentation.presentation_index,
                    unit_ids=batch.presentation.unit_ids, target_hashes=batch.target_hashes,
                    target_token_counts=batch.target_token_counts,
                    prefix_token_counts=tuple(len(row.context_ids) for row in prepared.records),
                    accounting=dict(prepared.accounting), loss=float(loss.detach().item()),
                    rng_start_seed=seed, pre_forward_rng=pre_forward, post_forward_rng=post_forward,
                    post_update_rng=_rng_hashes(_rng_state()), masks_identical_claim=False,
                ))
            self.optimizer.zero_grad(set_to_none=True)
            self._boundary = self._snapshot()
        except BaseException:
            self._failed = True
            raise
        return _tree_copy(self.receipts[-256:])
