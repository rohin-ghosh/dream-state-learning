"""Inactive R116 candidate: eight gradient replicas, one existing F1 AdamW.

No process-group creation, device allocation, row encoding, publication, or launch.
The caller must reach an all-eight safe common boundary, verify native provenance
and held exclusions, and supply the same immutable encoded cohort/schedule on all
ranks. Supply the raw training engine, not a readonly collection decoder whose
verification asserts the entire adapter is unchanged. ``source_manifest_sha256``
binds that caller-verified manifest. ``prepare_native_cohort`` provides the
read-only source/encoding adapter; it does not authorize activation. Use a finite
process-group timeout and Gloo CPU collectives, including for CUDA engines.

``ParallelSleep(...).run(max_steps=..., check=lease_check)`` is collective, as are
``checkpoint()`` and ``restore(owner_checkpoint_or_None)``. Only group-local rank0
(F1) supplies an existing AdamW; workers supply None. No DDP wrapper or gradient hooks
that perform additional distributed reductions may wrap the supplied model.

This is average-gradient batch8 AdamW, NOT eight serial AdamW updates. An explicit
partial final batch uses only its active ranks as the averaging denominator;
inactive ranks participate in collectives but do no forwards or backward passes.
Never pad/repeat/drop rows. A complete schedule covers all42 anchors, NEW rows
exactly16 times, and REHEARSAL rows once. Fewer than42 child presentations or
multi-anchor serial allocations fail before mutation: retain the serial backend
for those cohorts, not silently trim anchor coverage. Metrics report partial batches.
Checkpoint at successful step boundaries; a failed step requires restoring a prior
checkpoint, not retrying a possibly half-applied AdamW update.
"""

from collections import Counter
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import sys


WORLD_SIZE = 8
ANCHORS = 42
FORMAT = 'R116_PARALLEL_SLEEP_GLOO_V2'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def integration_contract():
    return dict(status='PROSPECTIVE_CPU_CANDIDATE_NOT_ACTIVATION',
        rank_order=['F1','F2','F3','F4','A1','A2','A3','A4'], backend='gloo', collective_tensors='CPU',
        activation='Main only, after current serial checkpoint/readout and all-eight safe boundary; never mid-sleep',
        caller_owns=['process_group_with_finite_timeout','rank_local_raw_engines','same_F1_AdamW',
                    'native_atomic_checkpoint_and_publication','source_closure','leases','FINAL_scheduler'],
        engine_fields=['torch','model','device','verify_base'],
        model_contract='Existing enabled fp32 LoRA; frozen base; no DDP/reducing hooks or readonly decoder wrapper',
        optimizer_contract='Exactly rank0 existing AdamW owns exactly those same LoRA parameter objects; workers None',
        row_adapter='prepare_native_cohort: verify native captures, same replay encoder and exact42 BASE inventory; retain encoding rejections',
        checkpoint_contract='Collective checkpoint: only rank0 gets CPU payload containing LoRA, same optimizer state, cursor, schema/binding, eight RNG states. Caller atomically saves before publication.',
        restore_contract='Collective restore(owner_payload on rank0, None elsewhere), in-place copy, existing optimizer object and all rank RNG; no automatic recovery/replay',
        boundary_contract='run max_steps and lease callback must agree on all ranks; failed collective poisons segment; no publish or retry without explicit recovery',
        comparison='Average-gradient batch8 AdamW, not serial-equivalent; partial tail divides by active ranks, no padding',
        native_gpu_tested=False, measured_speedup=None)


def prepare_native_cohort(*, shared, anchor_module, root, tokenizer, anchors, anchor_root,
                          expected_config_sha256, expected_state_sha256, source_files,
                          context_limit=16384):
    """Read-only adapter; caller passes pinned modules and the actual F1 anchor order.

    May inspect a serial cohort while it runs, but this is NOT an activation
    certificate. Every rank must obtain the same binding before training.
    """
    root, anchor_root = Path(root), Path(anchor_root)
    def checked(path, expected):
        path = Path(path)
        require(not path.is_symlink() and file_sha(path) == expected, 'native_source_hash_mismatch')
    for path, expected in source_files.items():
        checked(path, expected)
    for module in (shared, shared.replay, anchor_module, anchor_module.policy):
        require(str(Path(module.__file__).resolve()) in source_files, 'pinned_validator_source_required')
    checked(root/'CONFIG.json', expected_config_sha256)
    checked(root/'STATE.json', expected_state_sha256)
    config, state = shared.read(root/'CONFIG.json'), shared.read(root/'STATE.json')
    require(state['config_sha256'] == expected_config_sha256 and config['owner'] == 'F1'
            and config['new_presentations'] == 16 and config['rehearsal_presentations'] == 1
            and config['anchor_loss_weight'] == .25, 'same_shared_recipe_required')
    shared.checked_checkpoint(state['checkpoint'])
    require(set(config['branches']) == set(shared.BRANCHES), 'all_eight_branches_required')
    receipts, seen = {}, set()
    def generation_rows(generation, current):
        result = []
        for branch in shared.BRANCHES:
            path = root/f'generation_{generation:06d}'/(branch+'.json')
            receipt = shared.read(path)
            receipts[str(path)] = file_sha(path)
            require(receipt['branch'] == branch and receipt['generation'] == generation
                    and len(receipt['episode_ids']) == 2, 'exact_branch_generation_receipt')
            if current:
                require(receipt['checkpoint_sha256'] == state['checkpoint']['path_sha256'], 'current_common_child')
            for row in receipt['rows']:
                shared.validate_row(row, config['branches'][branch], config['excluded_ids'],
                    generation=generation, checkpoint_sha256=receipt['checkpoint_sha256'])
                require(row['episode_id'] in receipt['episode_ids'], 'row_in_submitted_episode')
                result.append((branch,row))
        return result
    new_rows = generation_rows(state['generation'], True)
    old_rows = []
    for branch, rows in config['initial_history'].items():
        for row in rows:
            shared.validate_row(row,config['branches'][branch],config['excluded_ids'])
            old_rows.append((branch,row))
    for generation in range(state['generation']):
        old_rows.extend(generation_rows(generation,False))
    encoded, decisions = dict(NEW=[],REHEARSAL=[]), []
    for kind, rows in (('NEW',new_rows),('REHEARSAL',old_rows)):
        for branch, row in rows:
            require(row['source_call_sha256'] not in seen, 'capture_duplicate_or_old_resubmitted_new')
            seen.add(row['source_call_sha256'])
            decision = dict(kind=kind,branch=branch,source_call_sha256=row['source_call_sha256'],
                            source_call_path=row['source_call_path'],target_sha256=row['target_sha256'])
            try:
                item = freeze_encoded(shared.replay.encode_row(row,tokenizer,context_limit))
                encoded[kind].append(item)
                decision.update(status='ENCODED',index=len(encoded[kind])-1,encoded_sha256=digest(item.__dict__),
                                native_target_tokens=len(item.target_ids))
            except ValueError as error:
                decision.update(status='REJECTED_ENCODING',reason=str(error))
            decisions.append(decision)
    inventory, anchor_receipt = anchor_module.build_inventory(anchor_root,tokenizer,context_limit,
        expected_manifest_sha256=config['anchor_sha256'])
    verified = {row['task_id']:row for family in inventory.values() for row in family}
    require(len(anchors) == len(verified) == ANCHORS and
            {row['task_id'] for row in anchors} == set(verified), 'same_actual42_anchor_inventory')
    encoded_anchors = []
    for row in anchors:
        actual, expected = freeze_encoded(row['encoded']), freeze_encoded(verified[row['task_id']]['encoded'])
        require(actual == expected and row['source_call_sha256'] == verified[row['task_id']]['source_call_sha256'],
                'actual_anchor_encoding_and_source')
        encoded_anchors.append(actual)
    allocations = tuple(shared.schedule(len(encoded['NEW']),len(encoded['REHEARSAL'])))
    validate_schedule(allocations,len(encoded['NEW']),len(encoded['REHEARSAL']),len(encoded_anchors))
    for path, expected in receipts.items():
        checked(path,expected)
    checked(root/'CONFIG.json', expected_config_sha256)
    checked(root/'STATE.json', expected_state_sha256)
    manifest = dict(format=FORMAT,root=str(root),generation=state['generation'],
        config_sha256=expected_config_sha256,state_sha256=expected_state_sha256,
        checkpoint=state['checkpoint'],source_files=dict(source_files),submission_files=receipts,
        decisions=decisions,anchor_receipt=anchor_receipt,anchor_order=[row['task_id'] for row in anchors],
        encoded_anchors_sha256=digest([row.__dict__ for row in encoded_anchors]),
        schedule_sha256=digest(allocations),context_limit=context_limit,activation_authorized=False)
    return dict(encoded_new=tuple(encoded['NEW']),encoded_old=tuple(encoded['REHEARSAL']),
        encoded_anchors=tuple(encoded_anchors),schedule=allocations,source_manifest_sha256=digest(manifest),manifest=manifest)


@dataclass(frozen=True)
class Encoded:
    input_ids: tuple
    labels: tuple
    target_ids: tuple


def freeze_encoded(row):
    result = Encoded(tuple(row.input_ids), tuple(row.labels), tuple(row.target_ids))
    require(len(result.input_ids) == len(result.labels), 'encoded_length_mismatch')
    require(all(type(token) is int and token >= 0 for token in result.input_ids), 'invalid_input_tokens')
    require(all(type(token) is int for token in result.labels), 'invalid_label_tokens')
    require(result.target_ids and all(type(token) is int for token in result.target_ids), 'empty_or_invalid_targets')
    prefix = len(result.input_ids) - len(result.target_ids)
    require(prefix > 0, 'causal_prefix_required')
    require(result.labels == (-100,) * prefix + result.target_ids, 'prefix_mask_or_targets_changed')
    require(result.input_ids[prefix:] == result.target_ids, 'targets_not_native_suffix')
    return result


def make_schedule(new_count, old_count, anchor_count=ANCHORS):
    require(type(new_count) is int and new_count > 0 and type(old_count) is int and old_count >= 0,
            'invalid_cohort_counts')
    require(anchor_count == ANCHORS, 'exact_42_anchors_required')
    items = [('NEW', index) for presentation in range(16) for index in range(new_count)]
    items.extend(('REHEARSAL', index) for index in range(old_count))
    require(len(items) >= ANCHORS, 'one_anchor_per_child_cannot_cover_42')
    return tuple(dict(kind=kind, index=index, anchors=[position % ANCHORS],
                      child_weight=.75, anchor_weight=.25)
                 for position, (kind, index) in enumerate(items))


def validate_schedule(allocations, new_count, old_count, anchor_count):
    require(new_count > 0 and old_count >= 0 and anchor_count == ANCHORS, 'invalid_sleep_inventory')
    result = []
    for item in allocations:
        require(item['kind'] in ('NEW', 'REHEARSAL') and type(item['index']) is int, 'invalid_child_selection')
        limit = new_count if item['kind'] == 'NEW' else old_count
        require(0 <= item['index'] < limit, 'child_index_out_of_range')
        require(item['child_weight'] == .75 and item['anchor_weight'] == .25, 'fixed_75_25_weights')
        require(len(item['anchors']) == 1, 'exactly_one_anchor_per_rank')
        anchor = item['anchors'][0]
        require(type(anchor) is int and 0 <= anchor < anchor_count, 'anchor_index_out_of_range')
        result.append((item['kind'], item['index'], anchor))
    require(result, 'nonempty_schedule_required')
    expected = Counter({('NEW', index): 16 for index in range(new_count)})
    expected.update({('REHEARSAL', index): 1 for index in range(old_count)})
    require(Counter((kind, index) for kind, index, anchor in result) == expected, 'exact_new16_old1_required')
    require({anchor for kind, index, anchor in result} == set(range(ANCHORS)), 'all42_anchor_coverage_required')
    return tuple(result)


def is_lora(name):
    return '.lora_A.' in name or '.lora_B.' in name


def cpu_copy(value):
    if hasattr(value, 'detach'):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_copy(item) for key, item in value.items()}
    if isinstance(value, list):
        return [cpu_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(cpu_copy(item) for item in value)
    return deepcopy(value)


class ParallelSleep:
    """All methods run on the same eight caller-owned processes, in lockstep."""

    def __init__(self, engine, optimizer, *, group, encoded_new, encoded_old,
                 encoded_anchors, schedule, source_manifest_sha256, distributed=None):
        self.engine, self.optimizer, self.group = engine, optimizer, group
        self.torch = engine.torch
        self.dist = distributed if distributed is not None else engine.torch.distributed
        self.rank = self.dist.get_rank(group)
        self.world_size = self.dist.get_world_size(group)
        self.root = self.dist.get_global_rank(group, 0) if group is not None else 0
        self.cursor, self.failed = 0, False
        self._collective('preflight', lambda: self._prepare(
            encoded_new, encoded_old, encoded_anchors, schedule, source_manifest_sha256))
        common = self._collective('replica_identity', lambda: dict(
            binding=self.binding, schema=self.schema, adapter=self._adapter_digest()))
        gathered = self._gather(common)
        require(all(item == common for item in gathered), 'replicas_cohort_schema_or_adapter_mismatch')

    def _gather(self, value):
        output = [None] * self.world_size
        self.dist.all_gather_object(output, value, group=self.group)
        return output

    def _collective(self, label, action):
        error, result = None, None
        try:
            result = action()
        except Exception as exception:
            error = type(exception).__name__ + ': ' + str(exception)
        errors = self._gather(error)
        if any(error is not None for error in errors):
            raise RuntimeError(label + ': ' + repr({rank: error for rank, error in enumerate(errors) if error}))
        return result

    def _prepare(self, encoded_new, encoded_old, encoded_anchors, allocations, source_hash):
        require(self.world_size == WORLD_SIZE, 'exactly_eight_replicas_required')
        require(str(self.dist.get_backend(self.group)).lower() == 'gloo', 'gloo_CPU_collective_group_required')
        require(isinstance(source_hash, str) and re.fullmatch('[0-9a-f]{64}', source_hash), 'manifest_sha256_required')
        require(not isinstance(self.engine.model, self.torch.nn.parallel.DistributedDataParallel), 'unwrapped_engine_required')
        require((self.rank == 0 and isinstance(self.optimizer, self.torch.optim.AdamW))
                or (self.rank != 0 and self.optimizer is None), 'only_F1_existing_AdamW_workers_none')
        self.rows = dict(NEW=tuple(map(freeze_encoded, encoded_new)),
                         REHEARSAL=tuple(map(freeze_encoded, encoded_old)))
        self.anchors = tuple(map(freeze_encoded, encoded_anchors))
        self.schedule = validate_schedule(allocations, len(self.rows['NEW']), len(self.rows['REHEARSAL']), len(self.anchors))
        self.parameters = tuple(self.engine.model.named_parameters())
        self.lora = tuple((name, parameter) for name, parameter in self.parameters if is_lora(name))
        require(self.lora, 'existing_lora_required')
        require(all(not parameter.requires_grad for name, parameter in self.parameters if not is_lora(name)), 'base_must_be_frozen')
        require(all(parameter.dtype == self.torch.float32 for name, parameter in self.lora), 'native_fp32_lora_required')
        require(all(bool(self.torch.isfinite(parameter).all()) for name, parameter in self.lora), 'nonfinite_lora')
        require(not any(getattr(module, 'disable_adapters', False) is True for module in self.engine.model.modules()),
                'existing_adapter_must_be_enabled')
        self._optimizer_identity_check()
        self.schema = tuple((name, tuple(parameter.shape), str(parameter.dtype)) for name, parameter in self.lora)
        self.binding = digest(dict(source_manifest_sha256=source_hash, schedule=self.schedule,
                                   rows={kind: [row.__dict__ for row in rows] for kind, rows in self.rows.items()},
                                   anchors=[row.__dict__ for row in self.anchors]))
        self.source_manifest_sha256 = source_hash
        self.engine.verify_base()

    def _optimizer_identity_check(self):
        if self.rank == 0:
            owned = [parameter for group in self.optimizer.param_groups for parameter in group['params']]
            expected = {id(parameter) for name, parameter in self.lora}
            require(len(owned) == len(expected) and {id(parameter) for parameter in owned} == expected,
                    'optimizer_must_own_exact_existing_lora_objects')

    def _adapter_digest(self):
        result = hashlib.sha256()
        for name, parameter in self.lora:
            result.update(name.encode())
            result.update(parameter.detach().cpu().contiguous().view(self.torch.uint8).numpy().tobytes())
        return result.hexdigest()

    def _identity_check(self):
        current = tuple(self.engine.model.named_parameters())
        require(len(current) == len(self.parameters) and all(
            name == previous_name and parameter is previous
            for (name, parameter), (previous_name, previous) in zip(current, self.parameters)),
            'engine_parameter_identity_changed')
        self._optimizer_identity_check()

    def _backward(self):
        self._identity_check()
        self.engine.model.zero_grad(set_to_none=True)
        if self.rank >= self._active_batch_size():
            return
        kind, index, anchor = self.schedule[self.cursor * WORLD_SIZE + self.rank]
        for row, weight in ((self.rows[kind][index], .75), (self.anchors[anchor], .25)):
            inputs = self.torch.tensor([row.input_ids], dtype=self.torch.long, device=self.engine.device)
            labels = self.torch.tensor([row.labels], dtype=self.torch.long, device=self.engine.device)
            context = self.torch.autocast(device_type='cuda', dtype=self.torch.bfloat16) if self.device_type == 'cuda' else nullcontext()
            with context:
                loss = self.engine.model(input_ids=inputs, attention_mask=self.torch.ones_like(inputs), labels=labels).loss * weight
            require(bool(self.torch.isfinite(loss)), 'nonfinite_weighted_loss')
            loss.backward()
        require(all(parameter.grad is None or (not parameter.grad.is_sparse and bool(self.torch.isfinite(parameter.grad).all()))
                    for name, parameter in self.lora), 'nonfinite_or_sparse_lora_gradient')

    def _reduce(self):
        gradients = self._collective('stage_gradients_CPU', lambda: tuple(
            self._cpu_gradient(parameter) for name, parameter in self.lora))
        used = self.torch.tensor([int(parameter.grad is not None) for name, parameter in self.lora],
                                 dtype=self.torch.int32, device='cpu')
        self.dist.reduce(used, dst=self.root, op=self.dist.ReduceOp.SUM, group=self.group)
        for position, ((name, parameter), gradient) in enumerate(zip(self.lora,gradients)):
            self.dist.reduce(gradient, dst=self.root, op=self.dist.ReduceOp.SUM, group=self.group)
            if self.rank == 0:
                parameter.grad = gradient.div_(self._active_batch_size()).to(parameter.device) if used[position].item() else None

    def _cpu_gradient(self, parameter):
        if parameter.grad is None:
            return self.torch.zeros_like(parameter, device='cpu')
        return parameter.grad.detach().to(device='cpu',copy=True).contiguous()

    def _active_batch_size(self):
        return min(WORLD_SIZE, len(self.schedule) - self.cursor * WORLD_SIZE)

    @property
    def total_steps(self):
        return (len(self.schedule) + WORLD_SIZE - 1) // WORLD_SIZE

    def _step(self):
        if self.rank == 0:
            require(all(parameter.grad is None or bool(self.torch.isfinite(parameter.grad).all()) for name, parameter in self.lora),
                    'nonfinite_averaged_gradient')
            self.optimizer.step()
            require(all(bool(self.torch.isfinite(parameter).all()) for name, parameter in self.lora), 'nonfinite_owner_update')

    def _broadcast_parameters(self):
        buffers = self._collective('stage_parameters_CPU', lambda: tuple(
            parameter.detach().to(device='cpu',copy=True).contiguous() for name, parameter in self.lora))
        with self.torch.no_grad():
            for (name, parameter), buffer in zip(self.lora,buffers):
                self.dist.broadcast(buffer, src=self.root, group=self.group)
                parameter.copy_(buffer.to(parameter.device))

    @property
    def device_type(self):
        return self.torch.device(self.engine.device).type

    def run(self, *, max_steps, check=None):
        """Bounded segment; ``check`` runs collectively before every optimizer step."""
        def validate():
            require(not self.failed, 'failed_segment_restore_required')
            require(type(max_steps) is int and max_steps > 0, 'positive_step_bound_required')
            self._identity_check()
            require(all(not parameter.requires_grad for name, parameter in self.parameters if not is_lora(name)), 'base_must_be_frozen')
        self._collective('run_preflight', validate)
        bound = min(self.cursor + max_steps, self.total_steps)
        require(all(item == (self.cursor, bound) for item in self._gather((self.cursor, bound))), 'rank_cursor_or_bound_mismatch')
        flags = [(parameter, parameter.requires_grad) for name, parameter in self.parameters]
        modes = [(module, module.training) for module in self.engine.model.modules()]
        config = getattr(self.engine.model, 'config', None)
        cache = getattr(config, 'use_cache', None)
        checkpointing = getattr(self.engine.model, 'is_gradient_checkpointing', False)
        start = self.cursor
        try:
            def activate():
                self.engine.model.train()
                for name, parameter in self.lora:
                    parameter.requires_grad_(True)
                if cache is not None:
                    config.use_cache = False
                if hasattr(self.engine.model, 'gradient_checkpointing_enable') and not checkpointing:
                    self.engine.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            self._collective('activate', activate)
            while self.cursor < bound:
                self._collective('lease_or_boundary_check', check or (lambda: None))
                self._collective('backward', self._backward)
                self._reduce()
                self._collective('owner_step', self._step)
                self._broadcast_parameters()
                self.cursor += 1
            self._collective('verify_frozen_base', self.engine.verify_base)
        except Exception:
            self.failed = True
            raise
        finally:
            self.engine.model.zero_grad(set_to_none=True)
            for parameter, flag in flags:
                parameter.requires_grad_(flag)
            for module, mode in modes:
                module.training = mode
            if cache is not None:
                config.use_cache = cache
            if hasattr(self.engine.model, 'gradient_checkpointing_disable') and not checkpointing:
                self.engine.model.gradient_checkpointing_disable()
        result = self.metrics()
        result['segment_optimizer_steps'] = self.cursor - start
        return result

    def metrics(self):
        completed = self.schedule[:self.cursor * WORLD_SIZE]
        partial = len(completed) % WORLD_SIZE
        return dict(backend=FORMAT, batch_size=WORLD_SIZE, nominal_batch_size=WORLD_SIZE,
                    collective_backend='gloo',collective_tensor_device='cpu',gpu_transport_benchmarked=False,
                    completed_full_batches=len(completed) // WORLD_SIZE, completed_partial_batch_size=partial,
                    scheduled_final_batch_size=len(self.schedule) % WORLD_SIZE or WORLD_SIZE,
                    last_completed_batch_size=(partial or WORLD_SIZE) if completed else 0,
                    gradient_average_denominator='active_ranks_in_logical_batch', padding_exposures=0,
                    optimizer_owner='F1/group_rank0', optimizer_count=1,
                    gradient_workers=7, optimizer_steps=self.cursor, serial_equivalent_presentations=len(completed),
                    serial_adamw_equivalent=False, total_scheduled_optimizer_steps=self.total_steps,
                    optimizer_steps_avoided_vs_serial=len(completed) - self.cursor,
                    child_token_exposures=sum(len(self.rows[kind][index].target_ids) for kind, index, anchor in completed),
                    anchor_token_exposures=sum(len(self.anchors[anchor].target_ids) for kind, index, anchor in completed),
                    new_row_exposures=sum(kind == 'NEW' for kind, index, anchor in completed),
                    rehearsal_row_exposures=sum(kind == 'REHEARSAL' for kind, index, anchor in completed),
                    encoded_new_rows=len(self.rows['NEW']), encoded_rehearsal_rows=len(self.rows['REHEARSAL']),
                    child_loss_weight=.75, anchor_loss_weight=.25, new_presentations=16, rehearsal_presentations=1,
                    schedule_binding_sha256=self.binding, source_manifest_sha256=self.source_manifest_sha256,
                    complete=self.cursor == self.total_steps)

    def _rng(self):
        numpy = sys.modules.get('numpy')
        return dict(python=random.getstate(), cpu=self.torch.get_rng_state().clone(),
                    cuda=self.torch.cuda.get_rng_state(self.engine.device).cpu() if self.device_type == 'cuda' else None,
                    numpy=deepcopy(numpy.random.get_state()) if numpy is not None else None)

    def _restore_rng(self, state):
        random.setstate(state['python'])
        self.torch.set_rng_state(state['cpu'])
        if state['cuda'] is not None:
            self.torch.cuda.set_rng_state(state['cuda'], self.engine.device)
        if state['numpy'] is not None:
            import numpy
            numpy.random.set_state(state['numpy'])

    def checkpoint(self):
        """Return a CPU payload on rank0 only; caller owns native atomic storage."""
        self._collective('checkpoint_boundary', lambda: require(not self.failed, 'failed_segment_restore_required'))
        rng = self._gather(self._collective('capture_rng', self._rng))
        positions = self._gather(self.cursor)
        require(all(position == self.cursor for position in positions), 'checkpoint_cursor_mismatch')
        def capture():
            self._identity_check()
            if self.rank == 0:
                return dict(format=FORMAT, binding=self.binding, schema=self.schema, cursor=self.cursor,
                            lora={name: cpu_copy(parameter) for name, parameter in self.lora},
                            optimizer=cpu_copy(self.optimizer.state_dict()), rng=rng, metrics=self.metrics())
        return self._collective('capture_checkpoint', capture)

    def restore(self, checkpoint):
        """Restore existing objects; owner optimizer never moves to the workers."""
        def validate():
            self._identity_check()
            require(self.rank == 0 or checkpoint is None, 'checkpoint_payload_owner_only')
            if self.rank == 0:
                require(checkpoint['format'] == FORMAT and checkpoint['binding'] == self.binding
                        and checkpoint['schema'] == self.schema, 'checkpoint_binding_mismatch')
                require(type(checkpoint['cursor']) is int and 0 <= checkpoint['cursor'] <= self.total_steps,
                        'invalid_checkpoint_cursor')
                require(len(checkpoint['rng']) == WORLD_SIZE, 'all_rank_rng_required')
                require(set(checkpoint['lora']) == {name for name, parameter in self.lora}, 'checkpoint_lora_keys')
                for name, parameter in self.lora:
                    value = checkpoint['lora'][name]
                    require(value.shape == parameter.shape and value.dtype == parameter.dtype
                            and bool(self.torch.isfinite(value).all()), 'checkpoint_lora_schema_or_finite')
        self._collective('restore_preflight', validate)
        try:
            def load_owner():
                if self.rank == 0:
                    self.optimizer.load_state_dict(deepcopy(checkpoint['optimizer']))
                    with self.torch.no_grad():
                        for name, parameter in self.lora:
                            parameter.copy_(checkpoint['lora'][name])
            self._collective('restore_owner', load_owner)
            self._broadcast_parameters()
            metadata = [dict(cursor=checkpoint['cursor'], rng=checkpoint['rng']) if self.rank == 0 else None]
            self.dist.broadcast_object_list(metadata, src=self.root, group=self.group)
            self.cursor = metadata[0]['cursor']
            self._collective('restore_rng', lambda: self._restore_rng(metadata[0]['rng'][self.rank]))
            self._collective('restore_base', self.engine.verify_base)
            self.failed = False
        except Exception:
            self.failed = True
            raise
