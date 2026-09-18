"""Prospective suffix-logit patch; requires an explicit successful GPU proof."""

import ast
import hashlib
import json
import math
from pathlib import Path

from gpu.orch_r145_suffix_loss import loss_window


POLICY = 'R145_CHILD_SUFFIX_LOGITS_UNCHANGED_TARGETS_V1'
RUNTIME_FILE = 'orch_r145_node3_capacity_runtime.json'
INSERTION = '        child_exposures, anchor_exposures = 0, 0\n'
OLD_FORWARD = """                        loss = self.engine.model(input_ids=inputs, labels=labels,
                            attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
"""
NEW_FORWARD = """                        loss = self.engine.model(input_ids=inputs,
                            **r145_loss_arguments(label, sample, labels),
                            attention_mask=self.torch.ones_like(inputs), use_cache=False).loss
"""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bound(path, expected):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)), 'no_proof_symlinks')
    raw = path.read_bytes()
    require(digest_bytes(raw) == expected, 'exact_proof_bytes')
    return json.loads(raw)


def validate_gpu_proof(proof, runtime_sha256):
    from gpu.orch_r145_node3_capacity_recovery import GRAD_TOLERANCE, LOSS_TOLERANCE, SCHEMA
    require(proof.get('schema') == SCHEMA and proof.get('status') == 'PASS'
            and proof.get('train_only') is True and proof.get('state_restored') is True
            and proof.get('optimizer_updates') == 0
            and proof.get('exact_learning_trajectory_claim') is False
            and proof.get('runtime_pin_sha256') == runtime_sha256,
            'successful_state_restoring_real_GPU_probe_required')
    require(proof.get('loss_tolerance') == LOSS_TOLERANCE
            and proof.get('gradient_tolerance') == GRAD_TOLERANCE,
            'unchanged_predeclared_numerical_tolerances')
    comparisons = proof.get('comparisons', [])
    require(comparisons and all(item.get('exact_rng') is True for item in comparisons),
            'actual_paired_gradient_loss_RNG_comparisons_required')
    for comparison in comparisons:
        original = comparison.get('original_memory', {})
        prospective = comparison.get('prospective_memory', {})
        require(original.get('full_input_tokens', 0) == prospective.get('full_input_tokens')
                and original.get('full_input_tokens', 0) > 0
                and 0 < prospective.get('peak_allocated_bytes', 0) <= original.get('peak_allocated_bytes', 0),
                'same_full_context_measured_peak_not_increased')
        for name in ('original_losses', 'prospective_losses'):
            losses = comparison.get(name, [])
            require(len(losses) == 5 and all(type(value) in (int, float) and math.isfinite(value)
                    for value in losses), 'finite_child_plus_four_anchor_losses')
        require(math.isfinite(comparison.get('max_gradient_absolute_error', float('nan'))),
                'finite_adapter_gradient_comparison')
    longest = proof.get('longest_child_prospective_only', {})
    require(longest.get('source_sha256') and longest.get('original_long_forward_attempted') is False
            and longest.get('memory', {}).get('free_after_bytes', 0) >= 2 * 1024**3,
            'actual_longest_TRAIN_row_capacity_required')


def prepare_sleep(model, native_file, runtime_sha256):
    from gpu.orch_r145_node3_capacity_recovery import verify_model
    expected = read_bound(Path(native_file).with_name(RUNTIME_FILE), runtime_sha256)
    verify_model(model, expected)


def loss_arguments(label, sample, labels):
    if label.startswith('ANCHOR:'):
        return {'labels': labels}
    require(label in ('NEW', 'REHEARSAL'), 'known_child_presentation_kind')
    window = loss_window(sample)
    return {'labels': labels[:, -window['logits_to_keep']:],
            'logits_to_keep': window['logits_to_keep']}


def patch_source(source, source_sha256, runtime_sha256, gpu_proof_path, gpu_proof_sha256):
    from gpu.orch_r144_target_patch import without_sleep
    require(digest_bytes(source.encode()) == source_sha256, 'exact_frozen_native_source')
    proof = read_bound(gpu_proof_path, gpu_proof_sha256)
    validate_gpu_proof(proof, runtime_sha256)
    require('orch_r145_suffix_boundary' not in source
            and source.count(INSERTION) == source.count(OLD_FORWARD) == 1,
            'unpatched_exact_sleep_forward_required')
    addition = (
        '        from gpu.orch_r145_suffix_boundary import prepare_sleep as r145_prepare_sleep\n'
        '        from gpu.orch_r145_suffix_boundary import loss_arguments as r145_loss_arguments\n'
        f'        r145_prepare_sleep(self.engine.model, __file__, {runtime_sha256!r})\n'
        f"        record('CHECKPOINT_METADATA', dict(runtime_memory_policy={POLICY!r},\n"
        f'            runtime_sha256={runtime_sha256!r}, GPU_validation_sha256={gpu_proof_sha256!r}))\n'
    )
    modified = source.replace(INSERTION, addition + INSERTION).replace(OLD_FORWARD, NEW_FORWARD)
    require(without_sleep(ast.parse(modified)) == without_sleep(ast.parse(source)),
            'only_sleep_behavior_changed')
    require(modified.replace(addition + INSERTION, INSERTION).replace(NEW_FORWARD, OLD_FORWARD) == source,
            'every_other_source_byte_preserved')
    compile(modified, '<r145-prospective-suffix-native>', 'exec')
    return modified
