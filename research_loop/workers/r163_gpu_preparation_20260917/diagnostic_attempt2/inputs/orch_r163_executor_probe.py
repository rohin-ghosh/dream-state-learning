"""State-restoring numerical probe on an explicitly supplied validation child."""

from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import random
import time

from gpu.orch_r161_native_executor import NativeExecutor
from gpu.orch_r125_continual_native import write_once
from organism_v6.pcfl_vertical_train import _state_hash


SCHEMA = 'R163_EXECUTOR_NUMERICAL_PROBE_V1'
LOSS_TOLERANCE = dict(atol=2e-5, rtol=1e-5)
GRADIENT_TOLERANCE = dict(atol=5e-5, rtol=5e-3)
UPDATE_TOLERANCE = dict(atol=1e-7, rtol=5e-3)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def cpu_copy(torch, value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_copy(torch, item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(cpu_copy(torch, item) for item in value)
    return deepcopy(value)


def saved_state(child):
    torch = child.torch
    return dict(adapter=cpu_copy(torch, child.parameters),
        optimizer=cpu_copy(torch, child.optimizer.state_dict()), steps=child.optimizer_steps,
        cpu=torch.get_rng_state().clone(), cuda=[state.clone() for state in torch.cuda.get_rng_state_all()],
        python=random.getstate(), training=child.engine.model.training,
        requires_grad={name: value.requires_grad for name, value in child.engine.model.named_parameters()},
        gradients={name: None if value.grad is None else cpu_copy(torch, value.grad)
                   for name, value in child.parameters.items()})


def restore_state(child, state):
    torch = child.torch
    with torch.no_grad():
        for name, parameter in child.parameters.items():
            parameter.copy_(state['adapter'][name].to(parameter.device))
    child.optimizer.load_state_dict(deepcopy(state['optimizer']))
    child.optimizer_steps = state['steps']
    child.engine.model.train(state['training'])
    for name, parameter in child.engine.model.named_parameters():
        parameter.requires_grad_(state['requires_grad'][name])
    for name, parameter in child.parameters.items():
        gradient = state['gradients'][name]
        parameter.grad = None if gradient is None else gradient.to(parameter.device).clone()
    torch.set_rng_state(state['cpu'])
    torch.cuda.set_rng_state_all(state['cuda'])
    random.setstate(state['python'])


def compare_tree(torch, observed, expected, tolerance):
    if isinstance(expected, torch.Tensor):
        require(isinstance(observed, torch.Tensor) and observed.dtype == expected.dtype,
                'same_tensor_type_and_dtype')
        torch.testing.assert_close(observed.detach().cpu(), expected.detach().cpu(), **tolerance)
    elif isinstance(expected, dict):
        require(isinstance(observed, dict) and observed.keys() == expected.keys(), 'same_mapping_inventory')
        for key in expected:
            compare_tree(torch, observed[key], expected[key], tolerance)
    elif isinstance(expected, (tuple, list)):
        require(type(observed) is type(expected) and len(observed) == len(expected), 'same_sequence_inventory')
        for actual, wanted in zip(observed, expected):
            compare_tree(torch, actual, wanted, tolerance)
    else:
        require(observed == expected, 'same_scalar_state')


def memory_start(executor):
    if executor.device == 'cpu':
        return
    executor.child.torch.cuda.synchronize()
    executor.child.torch.cuda.reset_peak_memory_stats()


def memory_end(executor):
    if executor.device == 'cpu':
        return None
    torch = executor.child.torch
    torch.cuda.synchronize()
    free, total = torch.cuda.mem_get_info()
    return dict(peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_reserved_bytes=torch.cuda.max_memory_reserved(), free_bytes=free, total_bytes=total)


def paired_diagnostics(torch, actual, reference, batch, reference_losses, actual_losses):
    gradients = []
    for name in reference['gradients']:
        expected, observed = reference['gradients'][name], actual['gradients'][name]
        if expected is None or observed is None:
            gradients.append(dict(name=name, reference_missing=expected is None, suffix_missing=observed is None))
            continue
        difference = (observed-expected).abs()
        finite = bool(torch.isfinite(difference).all())
        gradients.append(dict(name=name, shape=list(expected.shape), finite_difference=finite,
            max_absolute_difference=float(difference.max()) if finite else None))
    rng = lambda state: _state_hash({key: state[key] for key in ('cpu', 'cuda', 'python')})
    return dict(batch_sha256=batch.sha256, label=batch.components[0].label,
        target_tokens=len(batch.components[0].target_ids), reference_losses=reference_losses,
        suffix_losses=actual_losses, reference_rng_sha256=rng(reference), suffix_rng_sha256=rng(actual),
        gradients=gradients)


def full_label_update(executor, batch):
    child, torch = executor.child, executor.child.torch
    components = executor._components(batch)
    losses = []
    try:
        child.engine.model.train()
        for parameter in child.parameters.values():
            parameter.requires_grad_(True)
        child.optimizer.zero_grad(set_to_none=True)
        for component in components:
            child.check('probe_full_label_component')
            inputs = torch.tensor([component.input_ids], dtype=torch.long, device=executor.device)
            labels = torch.tensor([component.labels], dtype=torch.long, device=executor.device)
            context = torch.autocast(device_type='cuda', dtype=torch.bfloat16) if executor.device != 'cpu' else nullcontext()
            with context:
                loss = child.engine.model(input_ids=inputs, labels=labels,
                    attention_mask=torch.ones_like(inputs), use_cache=False).loss
            require(loss.ndim == 0 and bool(torch.isfinite(loss)), 'finite_reference_loss')
            (loss * component.objective_weight).backward()
            losses.append(float(loss.detach().cpu()))
        require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
                    for parameter in child.parameters.values()), 'finite_reference_gradients')
        child.optimizer.step()
        child.optimizer_steps += 1
    finally:
        child.engine.model.requires_grad_(False)
        child.engine.model.eval()
    return losses


def runtime_kind(executor):
    require(isinstance(executor, NativeExecutor), 'concrete_native_executor_required')
    require(executor.execution_kind in ('VALIDATION_ONLY', 'CPU_TEST_ONLY')
            and executor.fork_binding['mode'] == 'learning', 'isolated_validation_learning_fork_only')
    require(not executor.uncertain and executor.child.plan.get('r163_validation_only') is True,
            'explicit_non_science_validation_plan')
    if executor.execution_kind == 'CPU_TEST_ONLY':
        require(executor.device == 'cpu' and not executor.child.torch.cuda.is_initialized(), 'CPU_probe_only')
        return False
    child = executor.child
    require(executor.device == 'cuda:0' and child.torch.cuda.device_count() == 1, 'one_admitted_GPU')
    config = child.engine.model.config
    require(config.model_type == 'qwen2' and config.hidden_size == 3584
            and config.num_hidden_layers == 28 and config.vocab_size == 152064, 'actual_Qwen25_7B_shape')
    adapters = child.engine.model.peft_config
    require(len(adapters) == 1 and all(value.r == 8 and value.lora_alpha == 16
            and value.lora_dropout == 0.05 for value in adapters.values()), 'rank8_native_adapter')
    require(child.engine.model.is_gradient_checkpointing, 'gradient_checkpointing_enabled')
    child.engine.verify_base()
    return True


def run_probe(executor, paired_batches, longest_batch, output):
    real_model = runtime_kind(executor)
    child, torch = executor.child, executor.child.torch
    paired_batches = tuple(paired_batches)
    require(1 <= len(paired_batches) <= 4, 'bounded_paired_probes')
    require(all(len(batch.components[0].input_ids) <= 1024 for batch in paired_batches),
            'full_logit_reference_length_ceiling')
    require(len(longest_batch.components[0].input_ids) == child.plan['context_limit'],
            'test_actual_context_limit')
    require(all(len(part.input_ids) <= 1024 for batch in (*paired_batches, longest_batch)
                for part in batch.components[1:]), 'bounded_full_anchor_lengths')
    output = Path(output)
    require(output.is_absolute() and output == output.resolve()
            and output.is_relative_to(Path(executor.fork_binding['fork_root'])) and not output.exists(),
            'fresh_fork_local_probe_directory')
    output.mkdir()
    baseline = saved_state(child)
    before = executor.snapshot()
    comparisons = []
    receipt = dict(schema=SCHEMA, status='RUNNING', real_7b_validated=False,
        started_unix=time.time(), execution_kind=executor.execution_kind,
        loss_tolerance=LOSS_TOLERANCE, gradient_tolerance=GRADIENT_TOLERANCE,
        update_tolerance=UPDATE_TOLERANCE, context_limit=child.plan['context_limit'],
        synthetic_validation_not_qualified_training=True, scientific_optimizer_updates=0)
    try:
        for index, batch in enumerate(paired_batches):
            receipt.update(phase='PAIRED_UPDATE', pair_index=index, current_batch_sha256=batch.sha256)
            restore_state(child, baseline)
            memory_start(executor)
            reference_losses = full_label_update(executor, batch)
            reference = saved_state(child)
            reference_memory = memory_end(executor)
            receipt['phase'] = 'REFERENCE_REPEAT'
            restore_state(child, baseline)
            require(executor.snapshot() == before, 'exact_reference_repeat_starting_state')
            repeated_losses = full_label_update(executor, batch)
            repeated = saved_state(child)
            repeat_diagnostics = paired_diagnostics(torch, repeated, reference, batch,
                reference_losses, repeated_losses)
            receipt['reference_repeat'] = dict(batch_sha256=batch.sha256,
                reference_losses=reference_losses, repeated_losses=repeated_losses,
                reference_rng_sha256=repeat_diagnostics['reference_rng_sha256'],
                repeated_rng_sha256=repeat_diagnostics['suffix_rng_sha256'],
                gradients=repeat_diagnostics['gradients'], passed=False)
            torch.testing.assert_close(torch.tensor(repeated_losses), torch.tensor(reference_losses), **LOSS_TOLERANCE)
            require(repeat_diagnostics['reference_rng_sha256'] == repeat_diagnostics['suffix_rng_sha256'],
                    'reference_repeat_RNG_mismatch')
            compare_tree(torch, repeated['gradients'], reference['gradients'], GRADIENT_TOLERANCE)
            compare_tree(torch, repeated['adapter'], reference['adapter'], UPDATE_TOLERANCE)
            compare_tree(torch, repeated['optimizer'], reference['optimizer'], GRADIENT_TOLERANCE)
            require(repeated['steps'] == reference['steps'] == baseline['steps']+1,
                    'reference_repeat_single_optimizer_step')
            receipt['reference_repeat']['passed'] = True
            receipt['phase'] = 'PAIRED_UPDATE'
            restore_state(child, baseline)
            require(executor.snapshot() == before, 'exact_paired_starting_state')
            memory_start(executor)
            executor.update(batch)
            actual = saved_state(child)
            actual_memory = memory_end(executor)
            actual_losses = [component['loss'] for component in executor.last_update['losses']]
            receipt['current_pair'] = paired_diagnostics(torch, actual, reference, batch,
                reference_losses, actual_losses)
            torch.testing.assert_close(torch.tensor(actual_losses), torch.tensor(reference_losses), **LOSS_TOLERANCE)
            require(receipt['current_pair']['reference_rng_sha256'] == receipt['current_pair']['suffix_rng_sha256'],
                    'paired_forward_backward_RNG_mismatch')
            compare_tree(torch, actual['gradients'], reference['gradients'], GRADIENT_TOLERANCE)
            compare_tree(torch, actual['adapter'], reference['adapter'], UPDATE_TOLERANCE)
            compare_tree(torch, actual['optimizer'], reference['optimizer'], GRADIENT_TOLERANCE)
            compare_tree(torch, actual['cpu'], reference['cpu'], dict(atol=0, rtol=0))
            compare_tree(torch, actual['cuda'], reference['cuda'], dict(atol=0, rtol=0))
            require(actual['python'] == reference['python'] and actual['steps'] == baseline['steps']+1,
                    'same_rng_and_single_optimizer_step')
            snapshot = executor.snapshot()
            checkpoint = executor.checkpoint(output/f'paired_{index:02d}')
            require(executor.verify_checkpoint(checkpoint) == snapshot, 'actual_saved_update_roundtrip')
            comparisons.append(dict(batch_sha256=batch.sha256, reference_losses=reference_losses,
                suffix_losses=actual_losses, exact_rng=True, checkpoint=checkpoint,
                reference_repeat_verified=True,
                full_context_tokens=len(batch.components[0].input_ids),
                reference_memory=reference_memory, suffix_memory=actual_memory))
        restore_state(child, baseline)
        receipt.update(phase='LONGEST_UPDATE', current_batch_sha256=longest_batch.sha256)
        memory_start(executor)
        executor.update(longest_batch)
        longest_memory = memory_end(executor)
        longest_state = executor.snapshot()
        require(longest_state['optimizer_steps'] == baseline['steps']+1, 'one_longest_optimizer_update')
        longest_checkpoint = executor.checkpoint(output/'longest')
        require(executor.verify_checkpoint(longest_checkpoint) == longest_state,
                'actual_longest_saved_update_roundtrip')
        if real_model:
            require(longest_memory['free_bytes'] >= 2*1024**3, 'two_GiB_headroom_after_context_limit_update')
        receipt.update(comparisons=comparisons, longest=dict(batch_sha256=longest_batch.sha256,
            full_context_tokens=len(longest_batch.components[0].input_ids), memory=longest_memory,
            checkpoint=longest_checkpoint, full_label_comparison_attempted=False))
        restore_state(child, baseline)
        frozen = NativeExecutor(child, fork_binding=dict(executor.fork_binding, mode='frozen'),
            execution_kind=executor.execution_kind, device=executor.device)
        try:
            frozen.update(paired_batches[0])
        except ValueError as error:
            require(str(error) == 'frozen_executor_never_updates', 'expected_frozen_refusal')
        else:
            raise ValueError('frozen_executor_performed_update')
        require(frozen.snapshot() == before and not frozen.uncertain, 'frozen_state_unchanged')
        receipt['frozen_no_update_verified'] = True
        receipt['phase'] = 'RESTORE_FINAL'
    except BaseException as error:
        receipt.update(status='FAIL', error_type=type(error).__name__, error=str(error)[:512])
        raise
    finally:
        try:
            restore_state(child, baseline)
            require(executor.snapshot() == before, 'probe_restores_exact_initial_state')
            receipt['state_restored'] = True
        except BaseException as error:
            receipt.update(status='FAIL', state_restored=False, restore_error=str(error)[:512])
            executor.uncertain = True
            raise
        finally:
            receipt.update(finished_unix=time.time(), executor_uncertain=executor.uncertain)
            if receipt['status'] == 'RUNNING':
                receipt.update(status='PASS', real_7b_validated=real_model)
            write_once(output/'PROBE.json', receipt)
    return receipt
