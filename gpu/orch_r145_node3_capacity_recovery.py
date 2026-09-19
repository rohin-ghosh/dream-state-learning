"""Fail-closed, child-only R145 memory repair; no standalone GPU entry point.

Apply only to new copies of the pinned node3 native. Admission, restoration,
exact generation replay and pending-sleep accounting remain prerequisites.
Anchors retain their original full-sequence forward, including masked suffixes.
"""

import ast
from copy import deepcopy
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import marshal
import os
from pathlib import Path
import random
import textwrap
import time


SCHEMA = 'R145_NODE3_CHILD_SUFFIX_CAPACITY_V1'
NATIVE_SHA = '6b46401e5f8ff92d95e018b481d2303a55a3ce7c8e617aec65faa64bbc8381c7'
LAUNCHER_SHA = '9f78c7983e4cc0c6142f9500ee0f95af2878120639db4557074a932742373e0c'
HELPER = 'gpu.orch_r145_node3_capacity_recovery'
RUNTIME_FILENAME = 'orch_r145_node3_capacity_runtime.json'
VERSIONS = dict(transformers='5.5.3', peft='0.20.0', torch='2.13.0', tokenizers='0.22.2')
DEVICES = {5: 'GPU-bc211959-642d-664b-3581-42a0dbe434e9',
           6: 'GPU-1a83d900-1e95-c7b4-9b12-8117399697f8'}
LANES = {
    5: dict(name='creative_none', saved_cycle=16, saved_steps=752, start=906, end=918,
            requests=(909, 912), eligibility=916, abandoned=917,
            commit_sha256='6d2813c2416f285e439c466fad40d1c7b959998265f2e6346184e2696fbd0413'),
    6: dict(name='support_none', saved_cycle=13, saved_steps=572, start=698, end=709,
            requests=(700, 703), eligibility=707, abandoned=708,
            commit_sha256='978a2b7b9a2fe8fa0572f47834a850652e27000e05744effc2698d24227aba51'),
}
LOSS_TOLERANCE = dict(atol=2e-5, rtol=1e-5)
GRAD_TOLERANCE = dict(atol=5e-5, rtol=5e-3)
MAX_BASELINE_TOKENS = 2048
MIN_HEADROOM_BYTES = 2 * 1024**3
OLD_ENCODING = """        encoded = {row['source_sha256']:encode_own(row, self.tokenizer, self.plan['context_limit'])
                   for row in new_rows+old_rows}
"""
OLD_FORWARD = """                        loss = self.engine.model(input_ids=inputs, labels=labels,
                            attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
"""
NEW_FORWARD = """                        if label.startswith('ANCHOR:'):
                            loss = self.engine.model(input_ids=inputs, labels=labels,
                                attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
                        else:
                            window = r145_capacity.child_window(sample)
                            loss = self.engine.model(input_ids=inputs, labels=labels[:, -window['logits_to_keep']:],
                                logits_to_keep=window['logits_to_keep'],
                                attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
"""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def save_once(path, value):
    path = Path(path)
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), 'no_evidence_symlinks')
    with path.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def encoded_contract(sample, *, anchor=False, context_limit=None):
    inputs, labels, target = tuple(sample.input_ids), tuple(sample.labels), tuple(sample.target_ids)
    require(inputs and len(inputs) == len(labels) and target, 'nonempty_equal_length_encoded_row')
    require(all(type(token) is int and token >= 0 for token in inputs + target), 'native_integer_tokens')
    require(all(type(label) is int and label >= -100 for label in labels), 'integer_labels')
    if context_limit is not None:
        require(type(context_limit) is int and 0 < len(inputs) <= context_limit, 'no_context_truncation')
    selected = [index for index, label in enumerate(labels) if label != -100]
    require(selected and selected[0] > 0, 'causal_target_requires_masked_predecessor')
    first, end = selected[0], selected[-1] + 1
    require(selected == list(range(first, end)) and labels[first:end] == target
            and inputs[first:end] == target, 'exact_contiguous_native_target')
    require(all(label == -100 for label in labels[:first] + labels[end:]), 'only_target_supervised')
    require(anchor or end == len(inputs), 'child_target_must_end_sequence')
    return dict(input_tokens=len(inputs), target_tokens=len(target), prefix_tokens=first,
                masked_suffix_tokens=len(inputs) - end, anchor=anchor)


def child_window(sample):
    layout = encoded_contract(sample)
    keep = layout['target_tokens'] + 1
    return dict(logits_to_keep=keep, labels=tuple(sample.labels)[-keep:])


def validate_rows(encoded, anchors, context_limit):
    require(set(anchors) == {'code', 'math', 'simulated_tools', 'concise_answer'}
            and all(anchors.values()), 'four_nonempty_original_anchor_families')
    children = {key: encoded_contract(sample, context_limit=context_limit)
                for key, sample in encoded.items()}
    anchor_layouts = {}
    for family, records in sorted(anchors.items()):
        layouts = []
        for record in records:
            require(record.get('split') == 'TRAIN', 'TRAIN_anchors_only')
            layouts.append(encoded_contract(record['encoded'], anchor=True, context_limit=context_limit))
        anchor_layouts[family] = layouts
    return dict(children=children, anchors=anchor_layouts, child_count=len(children),
                anchor_count=sum(map(len, anchor_layouts.values())),
                max_anchor_tokens=max(item['input_tokens'] for group in anchor_layouts.values() for item in group),
                anchor_forward='ORIGINAL_FULL_INPUTS_FULL_LABELS_NO_LOGITS_TO_KEEP',
                target_filter_patch_applied=False)


def without_sleep(source):
    tree = ast.parse(source)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'NativeChild']
    require(len(classes) == 1, 'one_native_class')
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == 'sleep']
    require(len(methods) == 1, 'one_native_sleep')
    methods[0].body = [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def patch_source(source, runtime_sha256):
    require(hashlib.sha256(source.encode()).hexdigest() == NATIVE_SHA, 'exact_original_frozen_native_required')
    require(len(runtime_sha256) == 64 and all(char in '0123456789abcdef' for char in runtime_sha256),
            'exact_installed_runtime_pin_required')
    require(HELPER not in source and 'orch_r144_sleep_targets' not in source, 'capacity_only_no_R144_layer')
    require(source.count(OLD_ENCODING) == source.count(OLD_FORWARD) == 1, 'exact_training_blocks')
    addition = (f'        from gpu import orch_r145_node3_capacity_recovery as r145_capacity\n'
                f'        r145_capacity.prepare_sleep(self, encoded, anchors, {runtime_sha256!r})\n')
    modified = source.replace(OLD_ENCODING, OLD_ENCODING + addition).replace(OLD_FORWARD, NEW_FORWARD)
    require(without_sleep(modified) == without_sleep(source), 'only_sleep_AST_changes')
    require(modified.replace(OLD_ENCODING + addition, OLD_ENCODING).replace(NEW_FORWARD, OLD_FORWARD) == source,
            'exact_reversible_patch')
    compile(modified, '<r145-child-only-isolated-native>', 'exec')
    return modified


def forward_contract(source):
    tree = ast.parse(textwrap.dedent(source))
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    require(len(definitions) == 1, 'one_Qwen2_forward')
    forward = definitions[0]
    require('logits_to_keep' in [arg.arg for arg in forward.args.args + forward.args.kwonlyargs],
            'installed_explicit_logits_to_keep')
    allowed = set()
    calls = []
    for node in ast.walk(forward):
        if (isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == 'labels'
                and len(node.ops) == 1 and isinstance(node.ops[0], ast.IsNot)
                and len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Constant)
                and node.comparators[0].value is None):
            allowed.add(id(node.left))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'
                and node.func.attr == 'loss_function'):
            calls.append(node)
            for keyword in node.keywords:
                if keyword.arg == 'labels' and isinstance(keyword.value, ast.Name) and keyword.value.id == 'labels':
                    allowed.add(id(keyword.value))
    uses = {id(node) for node in ast.walk(forward) if isinstance(node, ast.Name)
            and node.id == 'labels' and isinstance(node.ctx, ast.Load)}
    require(len(calls) == 1 and len(allowed) == 2 and uses == allowed, 'labels_used_only_in_causal_loss')


def function_pin(function):
    chain = []
    seen = set()
    while True:
        require(inspect.isfunction(function) and id(function) not in seen, 'known_python_forward_implementation')
        seen.add(id(function))
        chain.append(dict(module=function.__module__, qualname=function.__qualname__,
                          code_sha256=hashlib.sha256(marshal.dumps(function.__code__)).hexdigest()))
        if not hasattr(function, '__wrapped__'):
            return chain
        function = function.__wrapped__


def installed_runtime_pins():
    versions = {name: importlib.metadata.version(name) for name in VERSIONS}
    require(versions == VERSIONS, 'unknown_installed_runtime_version')
    imported = {name: str(importlib.import_module(name).__version__) for name in VERSIONS}
    require(imported == dict(VERSIONS, torch='2.13.0+cu130'), 'unknown_imported_runtime_version')
    from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM, Qwen2Model
    from transformers.loss.loss_utils import ForCausalLMLoss
    from peft import PeftModelForCausalLM
    from peft.tuners.lora.layer import Linear as LoraLinear
    from torch.nn import Linear
    from torch.nn.functional import cross_entropy
    from torch.utils.checkpoint import checkpoint
    forward_contract(inspect.getsource(inspect.unwrap(Qwen2ForCausalLM.forward)))
    modules = ['transformers.models.qwen2.modeling_qwen2', 'transformers.loss.loss_utils',
               'transformers.modeling_utils', 'peft.peft_model', 'peft.tuners.lora.layer',
               'peft.tuners.lora.model', 'torch.nn.functional', 'torch.utils.checkpoint']
    files = {name: file_sha(importlib.import_module(name).__file__) for name in modules}
    functions = dict(qwen_forward=function_pin(Qwen2ForCausalLM.forward),
                     qwen_model_forward=function_pin(Qwen2Model.forward),
                     peft_forward=function_pin(PeftModelForCausalLM.forward),
                     lora_linear_forward=function_pin(LoraLinear.forward),
                     linear_forward=function_pin(Linear.forward), cross_entropy=function_pin(cross_entropy),
                     checkpoint=function_pin(checkpoint), loss=function_pin(ForCausalLMLoss))
    return dict(schema=SCHEMA, versions=versions, imported_versions=imported, files=files, functions=functions)


def verify_model(model, expected):
    require(installed_runtime_pins() == expected, 'actual_installed_functions_and_files_match_pins')
    from transformers.models.qwen2.modeling_qwen2 import Qwen2ForCausalLM, Qwen2Model
    from transformers.loss.loss_utils import ForCausalLMLoss
    from peft import PeftModelForCausalLM
    from peft.tuners.lora.layer import Linear as LoraLinear
    from torch.nn import Linear
    require(type(model) is PeftModelForCausalLM, 'only_actual_PeftModelForCausalLM')
    base = model.get_base_model()
    require(type(base) is Qwen2ForCausalLM and type(base.model) is Qwen2Model, 'only_actual_Qwen2')
    for instance, implementation in ((model, PeftModelForCausalLM), (base, Qwen2ForCausalLM),
                                     (base.model, Qwen2Model)):
        require(getattr(instance.forward, '__func__', None) is implementation.forward,
                'no_instance_forward_override')
    require(base.loss_function is ForCausalLMLoss, 'original_ForCausalLMLoss_only')
    require(type(base.lm_head) is Linear
            and getattr(base.lm_head.forward, '__func__', None) is Linear.forward, 'original_lm_head_forward')
    for module in model.modules():
        if isinstance(module, LoraLinear):
            require(type(module) is LoraLinear and getattr(module.forward, '__func__', None) is LoraLinear.forward,
                    'no_adapter_forward_override')
    require(base.config.model_type == 'qwen2' and not model.active_peft_config.is_prompt_learning,
            'unchanged_Qwen2_LoRA_not_prompt_learning')


def owned_plan(plan):
    physical = plan['physical']
    require(type(physical) is int and physical in LANES and plan['gpu_uuid'] == DEVICES[physical],
            'only_physical5_6')
    lane = LANES[physical]
    expected = '/localhome/local-rohing/orch_r133_node3_' + lane['name'] + '_20260916_attempt1/run1'
    require(plan['root'] == expected, 'exact_owned_same_life_root')
    return lane


def prepare_sleep(child, encoded, anchors, runtime_sha256):
    owned_plan(child.plan)
    pin_path = Path(__file__).with_name(RUNTIME_FILENAME)
    require(file_sha(pin_path) == runtime_sha256, 'source_bound_installed_runtime_pin_file')
    verify_model(child.engine.model, json.loads(pin_path.read_text()))
    return validate_rows(encoded, anchors, child.plan['context_limit'])


def rng_state(torch):
    return dict(python=random.getstate(), cpu=torch.get_rng_state().clone(),
                cuda=[state.clone() for state in torch.cuda.get_rng_state_all()])


def restore_rng(torch, state):
    random.setstate(state['python'])
    torch.set_rng_state(state['cpu'])
    torch.cuda.set_rng_state_all(state['cuda'])


def rng_fingerprint(state):
    return digest(dict(python=state['python'], cpu=state['cpu'].tolist(),
                       cuda=[value.tolist() for value in state['cuda']]))


def tensor_tree_fingerprint(torch, value):
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        return dict(dtype=str(tensor.dtype), shape=list(tensor.shape),
                    sha256=hashlib.sha256(tensor.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
    if isinstance(value, dict):
        return [[repr(key), tensor_tree_fingerprint(torch, item)]
                for key, item in sorted(value.items(), key=lambda pair: repr(pair[0]))]
    if isinstance(value, (list, tuple)):
        return [tensor_tree_fingerprint(torch, item) for item in value]
    require(value is None or type(value) in (str, int, float, bool), 'known_optimizer_state_type')
    return value


def cpu_snapshot(torch, value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {key: cpu_snapshot(torch, item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(cpu_snapshot(torch, item) for item in value)
    if isinstance(value, list):
        return [cpu_snapshot(torch, item) for item in value]
    return deepcopy(value)


def bounded_train_probe(child, encoded, anchors, runtime_sha256, output):
    """In-admission, before exact replay; no optimizer steps or journal writes.

Only complete actual TRAIN rows are used, never prefixes or synthetic shortened
versions. Baseline comparisons use bounded rows; longest-child stress is
prospective-only. Every exit restores RNG, adapter, optimizer and model mode.
"""
    layout = prepare_sleep(child, encoded, anchors, runtime_sha256)
    torch, model = child.torch, child.engine.model
    require(os.environ.get('R125_ADMISSION_PLAN_SHA256') == getattr(child, 'r145_admitted_plan_sha256', None)
            and bool(os.environ.get('R125_ADMISSION_PLAN_SHA256')), 'must_be_inside_original_admitted_recovery')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == child.plan['gpu_uuid']
            and os.environ.get('PYTORCH_CUDA_ALLOC_CONF') == 'expandable_segments:True'
            and 'PYTORCH_ALLOC_CONF' not in os.environ and torch.cuda.device_count() == 1,
            'original_single_device_allocator_environment')
    require(layout['max_anchor_tokens'] <= MAX_BASELINE_TOKENS, 'actual_anchor_lengths_must_be_bounded')
    require(encoded and isinstance(child.optimizer, torch.optim.AdamW), 'original_AdamW_and_actual_rows')
    require(all(parameter.grad is None for parameter in child.parameters.values()), 'probe_starts_without_gradients')
    rows = sorted(encoded.items(), key=lambda pair: (len(pair[1].input_ids), pair[0]))
    bounded = [pair for pair in rows if len(pair[1].input_ids) <= MAX_BASELINE_TOKENS]
    require(bounded, 'bounded_actual_TRAIN_row_required_no_truncation')
    selected = {bounded[0][0]: bounded[0][1], bounded[-1][0]: bounded[-1][1]}
    original_rng = rng_state(torch)
    require(all(not parameter.requires_grad for name, parameter in model.named_parameters()
                if name not in child.parameters), 'original_frozen_base_before_probe')
    original_optimizer = cpu_snapshot(torch, child.optimizer.state_dict())
    optimizer_sha = digest(tensor_tree_fingerprint(torch, original_optimizer))
    original_adapter = {name: parameter.detach().cpu().clone() for name, parameter in child.parameters.items()}
    adapter_sha = child.adapter_hash()
    original_steps = child.optimizer_steps
    flags = [(parameter, parameter.requires_grad) for parameter in model.parameters()]
    modes = [(module, module.training) for module in model.modules()]
    deadline = min(child.plan['hard_end_unix'], time.time() + 240)
    proof = dict(schema=SCHEMA, status='RUNNING', train_only=True, layout=layout,
                 loss_tolerance=LOSS_TOLERANCE, gradient_tolerance=GRAD_TOLERANCE,
                 exact_learning_trajectory_claim=False, optimizer_updates=0, comparisons=[],
                 runtime_pin_sha256=runtime_sha256, started_unix=time.time())
    save_once(Path(output) / 'TRAIN_PROBE_STARTED.json', proof)

    def run(sample, optimized):
        child.check('r145_bounded_TRAIN_probe')
        require(time.time() < deadline, 'bounded_probe_wall')
        model.train()
        child.optimizer.zero_grad(set_to_none=True)
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        free, total = torch.cuda.mem_get_info()
        logits_tokens = len(sample.target_ids) + 1 if optimized else len(sample.input_ids)
        estimated_logits_bytes = logits_tokens * model.get_base_model().config.vocab_size * 16
        require(free > estimated_logits_bytes + MIN_HEADROOM_BYTES, 'baseline_capacity_preflight_no_identical_OOM')
        torch.cuda.reset_peak_memory_stats()
        batch = [('NEW', sample, 0.75)]
        for family, records in sorted(anchors.items()):
            batch.append(('ANCHOR:' + family, max(records, key=lambda row: len(row['encoded'].input_ids))['encoded'], 0.0625))
        losses = []
        for kind, item, weight in batch:
            require(time.time() < deadline, 'bounded_probe_wall')
            inputs = torch.tensor([item.input_ids], dtype=torch.long, device='cuda:0')
            kwargs = dict(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False)
            if optimized and not kind.startswith('ANCHOR:'):
                window = child_window(item)
                kwargs.update(labels=torch.tensor([window['labels']], dtype=torch.long, device='cuda:0'),
                              logits_to_keep=window['logits_to_keep'])
            else:
                kwargs['labels'] = torch.tensor([item.labels], dtype=torch.long, device='cuda:0')
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                loss = model(**kwargs).loss
            require(bool(torch.isfinite(loss)), 'finite_probe_loss')
            (loss * weight).backward()
            losses.append(float(loss.detach()))
            del loss, inputs, kwargs
        gradients = {}
        for name, parameter in child.parameters.items():
            require(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()), 'finite_all_adapter_gradients')
            gradients[name] = parameter.grad.detach().cpu().clone()
        require(all(parameter.grad is None for name, parameter in model.named_parameters()
                    if name not in child.parameters), 'base_has_no_gradients')
        torch.cuda.synchronize()
        free_after, _ = torch.cuda.mem_get_info()
        memory = dict(peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                      peak_reserved_bytes=torch.cuda.max_memory_reserved(), free_after_bytes=free_after,
                      total_bytes=total, full_input_tokens=len(sample.input_ids), logits_tokens=logits_tokens)
        return losses, gradients, rng_fingerprint(rng_state(torch)), memory

    try:
        for parameter in child.parameters.values():
            parameter.requires_grad_(True)
        for row_sha, sample in selected.items():
            restore_rng(torch, original_rng)
            losses_before, grads_before, rng_before, memory_before = run(sample, False)
            restore_rng(torch, original_rng)
            losses_after, grads_after, rng_after, memory_after = run(sample, True)
            torch.testing.assert_close(torch.tensor(losses_after), torch.tensor(losses_before), **LOSS_TOLERANCE)
            require(rng_before == rng_after, 'paired_exact_python_CPU_CUDA_RNG')
            maximum = 0.0
            for name in grads_before:
                torch.testing.assert_close(grads_after[name], grads_before[name], **GRAD_TOLERANCE)
                maximum = max(maximum, float((grads_after[name] - grads_before[name]).abs().max()))
            require(memory_after['peak_allocated_bytes'] <= memory_before['peak_allocated_bytes'], 'measured_peak_not_increased')
            proof['comparisons'].append(dict(source_sha256=row_sha, original_losses=losses_before,
                prospective_losses=losses_after, max_gradient_absolute_error=maximum,
                exact_rng=True, original_memory=memory_before, prospective_memory=memory_after))
        restore_rng(torch, original_rng)
        _, _, _, memory = run(rows[-1][1], True)
        require(memory['free_after_bytes'] >= MIN_HEADROOM_BYTES, 'longest_child_plus_anchors_headroom')
        proof['longest_child_prospective_only'] = dict(source_sha256=rows[-1][0], memory=memory,
            original_long_forward_attempted=False)
        proof['status'] = 'PASS'
    except BaseException as error:
        proof.update(status='FAIL', error_type=type(error).__name__, error=str(error), no_automatic_retry=True)
        raise
    finally:
        child.optimizer.zero_grad(set_to_none=True)
        with torch.no_grad():
            for name, parameter in child.parameters.items():
                parameter.copy_(original_adapter[name])
        child.optimizer.load_state_dict(original_optimizer)
        child.optimizer_steps = original_steps
        for parameter, enabled in flags:
            parameter.requires_grad_(enabled)
        for module, training in modes:
            module.training = training
        restore_rng(torch, original_rng)
        require(child.adapter_hash() == adapter_sha
                and digest(tensor_tree_fingerprint(torch, child.optimizer.state_dict())) == optimizer_sha
                and rng_fingerprint(rng_state(torch)) == rng_fingerprint(original_rng), 'probe_state_exactly_restored')
        child.engine.verify_base()
        proof.update(state_restored=True, optimizer_sha256=optimizer_sha, adapter_sha256=adapter_sha,
                     rng_sha256=rng_fingerprint(original_rng), finished_unix=time.time())
        save_once(Path(output) / 'TRAIN_PROBE_RESULT.json', proof)
    return proof
