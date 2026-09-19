"""Admitted initialization-only capacity validation, never stream training data."""

from copy import deepcopy
import os
from pathlib import Path
import socket
import time

from gpu import orch_r125_continual_native as native
from gpu import orch_r145_node3_capacity_recovery as capacity
from gpu.orch_r145_suffix_boundary import loss_arguments, read_bound, validate_gpu_proof


SCHEMA = 'R151_MATCHED_INITIAL_CAPACITY_V1'
RUNTIME_SHA256 = 'c66a91b631937236d614095c07785f90242e4d476c45b7fa8fe5d65a8f277d2d'
PRIOR_GPU_SHA256 = '3d4e5ed2e7acf7501ab21a1361c511f5db9fe4ad25f96dd1e691fbc47277b281'
MIN_HEADROOM_BYTES = 2 * 1024**3
PROBE_SECONDS = 300


def shape_sample(tokenizer, input_tokens, target_tokens):
    from gpu.astra_pchain2_native import EncodedRow
    native.require(type(input_tokens) is int and type(target_tokens) is int
        and 0 < target_tokens < input_tokens, 'bounded_capacity_shape')
    pattern = tokenizer.encode('Observe a situation, consider another explanation, and check what follows.',
                               add_special_tokens=False)
    native.require(pattern and all(type(token) is int and token >= 0 for token in pattern)
        and not set(pattern).intersection(tokenizer.all_special_ids), 'ordinary_synthetic_capacity_tokens')
    inputs = tuple(pattern[index % len(pattern)] for index in range(input_tokens))
    target = inputs[-target_tokens:]
    return EncodedRow(inputs, (-100,) * (input_tokens-target_tokens) + target, target)


def initializer_profile(plan, hostname):
    node5 = (hostname == 'ipp2-ovx-p1-10' and plan.get('physical') == 0
             and plan.get('gpu_uuid') == 'GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a')
    source = Path(plan.get('source_root', ''))
    node4 = (hostname == 'a4u8g-0105' and plan.get('physical') == 5
             and plan.get('gpu_uuid') == 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30'
             and source.name == 'source' and source.parent.parent == Path('/localhome/local-rohing')
             and source.parent.name.startswith('orch_r158_matched_node4_'))
    native.require(plan.get('matched_arm') == 'parented_learning'
                   and type(plan.get('physical')) is int and (node5 or node4),
                   'designated_node5_or_node4_initializer_only')
    return 'R158_NODE4' if node4 else 'R151_NODE5'


def validate_environment(child, plan_path):
    plan = child.plan
    initializer_profile(plan, socket.gethostname())
    native.require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == native.sha(plan_path)
        and os.environ.get('R150_COHORT_SHA256') == plan['matched_cohort']['sha256'], 'actual_admitted_initialization')
    native.require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid']
        and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True'
        and 'PYTORCH_ALLOC_CONF' not in os.environ and child.torch.cuda.device_count() == 1,
        'single_confined_GPU_and_allocator')
    native.require(plan['context_limit'] == 16384 and plan['segment_tokens'] == 512
        and child.optimizer_steps == 0 and not child.optimizer.state, 'fresh_common_16k_512_configuration')
    source = Path(plan['source_root'])/'gpu'
    expected = read_bound(source/'orch_r145_node3_capacity_runtime.json', RUNTIME_SHA256)
    prior = read_bound(source/'R145_GPU_PROOF.json', PRIOR_GPU_SHA256)
    validate_gpu_proof(prior, RUNTIME_SHA256)
    capacity.verify_model(child.engine.model, expected)
    native.require(isinstance(child.optimizer, child.torch.optim.AdamW), 'actual_AdamW_initialization')


def initial_capacity(child, plan_path, directory):
    started = time.time()
    deadline = min(child.plan['hard_end_unix'], started+PROBE_SECONDS)
    from gpu.orch_r107_base_anchors_inventory import build_inventory

    proof = dict(schema=SCHEMA, status='RUNNING', started_unix=started, deadline_unix=deadline,
        work_budget_seconds=PROBE_SECONDS, cleanup_allowance_seconds=0,
        cleanup_policy='BEST_EFFORT_WITHIN_EXISTING_EXPERIMENT_WALL_NO_PASS_EXTENSION',
        plan_sha256=native.sha(plan_path), runtime_sha256=RUNTIME_SHA256, prior_GPU_proof_sha256=PRIOR_GPU_SHA256,
        synthetic_shape_only=True, stream_data_written=False, scientific_evaluation=False,
        generation_calls=0, optimizer_updates=0, context_limit=child.plan['context_limit'],
        segment_tokens=child.plan['segment_tokens'],
        loss_tolerance=deepcopy(capacity.LOSS_TOLERANCE), gradient_tolerance=deepcopy(capacity.GRAD_TOLERANCE),
        minimum_headroom_bytes=MIN_HEADROOM_BYTES, exact_learning_trajectory_claim=False)
    directory = Path(directory)/'capacity_validation'
    directory.mkdir(exist_ok=False)
    native.write_once(directory/'STARTED.json', proof)
    snapshots_ready = False
    measurement_error = None
    cleanup_errors = []
    acceptance_error = None

    def check_deadline():
        native.require(started <= time.time() < deadline, 'capacity_probe_deadline')

    def error_detail(error):
        return dict(error_type=type(error).__name__, error=str(error))

    def cleanup_step(step, action):
        try:
            action()
        except BaseException as error:
            cleanup_errors.append(error)
            proof.setdefault('cleanup_errors', []).append(dict(step=step, **error_detail(error)))

    def forward(sample, suffix):
        check_deadline()
        child.check('r151_initial_capacity')
        model.train()
        child.optimizer.zero_grad(set_to_none=True)
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        losses = []
        samples = [('NEW', sample, 0.75)] + [('ANCHOR:'+family, anchor, 0.25/4)
                                             for family, anchor in selected]
        for label, encoded, weight in samples:
            check_deadline()
            inputs = torch.tensor([encoded.input_ids], dtype=torch.long, device='cuda:0')
            labels = torch.tensor([encoded.labels], dtype=torch.long, device='cuda:0')
            arguments = loss_arguments(label, encoded, labels) if suffix else dict(labels=labels)
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False, **arguments).loss
            native.require(bool(torch.isfinite(loss)), 'finite_capacity_loss')
            (loss*weight).backward()
            losses.append(float(loss.detach()))
            del loss, inputs, labels, arguments
        gradients = {}
        for name, parameter in child.parameters.items():
            native.require(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()),
                           'finite_capacity_adapter_gradients')
            gradients[name] = parameter.grad.detach().cpu().clone()
        native.require(all(parameter.grad is None for name, parameter in model.named_parameters()
                           if name not in child.parameters), 'capacity_base_without_gradients')
        torch.cuda.synchronize()
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        memory = dict(full_input_tokens=len(sample.input_ids), target_tokens=len(sample.target_ids),
            logits_tokens=len(sample.target_ids)+1 if suffix else len(sample.input_ids),
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_reserved_bytes=torch.cuda.max_memory_reserved(), free_after_bytes=free_bytes, total_bytes=total_bytes)
        fingerprint = capacity.rng_fingerprint(capacity.rng_state(torch))
        proof.setdefault('completed_passes', []).append(dict(losses=losses, memory=memory, suffix=suffix))
        check_deadline()
        return losses, gradients, fingerprint, memory

    try:
        validate_environment(child, plan_path)
        torch, model = child.torch, child.engine.model
        anchors, anchor_receipt = build_inventory(child.plan['anchors'], child.tokenizer, child.plan['context_limit'])
        native.require(set(anchors) == {'code', 'math', 'simulated_tools', 'concise_answer'}
            and all(anchors.values()), 'actual_four_TRAIN_anchor_families')
        proof['anchor_receipt_sha256'] = native.digest(anchor_receipt)
        selected = [(family, max(rows, key=lambda row: len(row['encoded'].input_ids))['encoded'])
                    for family, rows in sorted(anchors.items())]
        bounded = shape_sample(child.tokenizer, 2048, 128)
        maximum = shape_sample(child.tokenizer, child.plan['context_limit'], child.plan['segment_tokens'])
        original_rng = capacity.rng_state(torch)
        original_optimizer = capacity.cpu_snapshot(torch, child.optimizer.state_dict())
        original_optimizer_sha = native.digest(capacity.tensor_tree_fingerprint(torch, original_optimizer))
        original_adapter = {name: parameter.detach().cpu().clone() for name, parameter in child.parameters.items()}
        original_adapter_sha = child.adapter_hash()
        flags = [(parameter, parameter.requires_grad) for parameter in model.parameters()]
        modes = [(module, module.training) for module in model.modules()]
        native.require(all(parameter.grad is None for parameter in model.parameters()), 'capacity_starts_without_gradients')
        snapshots_ready = True
        check_deadline()
        for parameter in child.parameters.values():
            parameter.requires_grad_(True)
        capacity.restore_rng(torch, original_rng)
        old_losses, old_gradients, old_rng, old_memory = forward(bounded, False)
        capacity.restore_rng(torch, original_rng)
        new_losses, new_gradients, new_rng, new_memory = forward(bounded, True)
        torch.testing.assert_close(torch.tensor(new_losses), torch.tensor(old_losses), **capacity.LOSS_TOLERANCE)
        native.require(old_rng == new_rng, 'capacity_paired_RNG_equality')
        maximum_error = 0.0
        for name, expected_gradient in old_gradients.items():
            torch.testing.assert_close(new_gradients[name], expected_gradient, **capacity.GRAD_TOLERANCE)
            maximum_error = max(maximum_error, float((new_gradients[name]-expected_gradient).abs().max()))
        native.require(new_memory['peak_allocated_bytes'] <= old_memory['peak_allocated_bytes'],
                       'capacity_suffix_peak_not_increased')
        proof['bounded_comparison'] = dict(original_losses=old_losses, suffix_losses=new_losses,
            original_memory=old_memory, suffix_memory=new_memory, exact_rng=True,
            max_gradient_absolute_error=maximum_error)
        check_deadline()
        del old_gradients, new_gradients
        capacity.restore_rng(torch, original_rng)
        maximum_losses, gradients, unused_rng, memory = forward(maximum, True)
        del gradients
        proof.update(maximum_shape=memory, maximum_losses=maximum_losses)
        native.require(memory['free_after_bytes'] >= MIN_HEADROOM_BYTES, 'maximum_shape_has_headroom')
        check_deadline()
    except BaseException as error:
        measurement_error = error
        proof.update(measurement_error=error_detail(error))
    finally:
        proof['measurement_finished_unix'] = time.time()
        proof.update(state_restored=False, restoration_status='UNVERIFIED')
        if snapshots_ready:
            def restore_adapter():
                with torch.no_grad():
                    for name, parameter in child.parameters.items():
                        parameter.copy_(original_adapter[name])

            def verify_restored():
                native.require(child.adapter_hash() == original_adapter_sha and child.optimizer_steps == 0
                    and native.digest(capacity.tensor_tree_fingerprint(torch, child.optimizer.state_dict())) == original_optimizer_sha
                    and capacity.rng_fingerprint(capacity.rng_state(torch)) == capacity.rng_fingerprint(original_rng)
                    and all(parameter.grad is None for parameter in model.parameters())
                    and all(parameter.requires_grad is flag for parameter, flag in flags)
                    and all(module.training is mode for module, mode in modes),
                    'common_initial_state_restored_after_capacity_probe')

            cleanup_step('zero_grad', lambda: child.optimizer.zero_grad(set_to_none=True))
            cleanup_step('adapter', restore_adapter)
            cleanup_step('optimizer', lambda: child.optimizer.load_state_dict(original_optimizer))
            for parameter, flag in flags:
                cleanup_step('requires_grad', lambda: parameter.requires_grad_(flag))
            for module, mode in modes:
                cleanup_step('training_mode', lambda: setattr(module, 'training', mode))
            cleanup_step('RNG', lambda: capacity.restore_rng(torch, original_rng))
            cleanup_step('empty_cache', torch.cuda.empty_cache)
            cleanup_step('verify_base', child.engine.verify_base)
            cleanup_step('verify_restored', verify_restored)
            proof.update(state_restored=not cleanup_errors,
                         restoration_status='FAILED' if cleanup_errors else 'VERIFIED')
        try:
            check_deadline()
        except BaseException as error:
            acceptance_error = error
            proof['acceptance_error'] = error_detail(error)
        finished = time.time()
        proof.update(finished_unix=finished, elapsed_seconds=finished-started,
                     cleanup_elapsed_seconds=finished-proof['measurement_finished_unix'])
        if acceptance_error is None and not started <= finished < deadline:
            acceptance_error = ValueError('capacity_probe_deadline')
            proof['acceptance_error'] = error_detail(acceptance_error)
        failure = measurement_error or (cleanup_errors[0] if cleanup_errors else None) or acceptance_error
        proof['status'] = 'FAIL' if failure is not None else 'PASS'
        if failure is not None:
            proof.update(**error_detail(failure), automatic_retry=False)
    try:
        native.write_once(directory/'RESULT.json', proof)
    except BaseException as error:
        raise error from failure
    if failure is not None:
        if measurement_error is not None and cleanup_errors:
            raise measurement_error from cleanup_errors[0]
        raise failure
    return dict(status=proof['status'], schema=SCHEMA, path=str(directory/'RESULT.json'),
                sha256=native.sha(directory/'RESULT.json'), state_restored=True,
                scientific_evaluation=False, stream_data_written=False, optimizer_updates=0)
