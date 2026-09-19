"""Dormant training-memory candidate; no runtime deployment in this module."""


def loss_window(sample):
    inputs, labels, target = tuple(sample.input_ids), tuple(sample.labels), tuple(sample.target_ids)
    if not target or len(inputs) != len(labels) or len(target) >= len(inputs):
        raise ValueError('nonempty_target_and_prefix_required')
    prefix = len(inputs) - len(target)
    if any(label != -100 for label in labels[:prefix]) or labels[prefix:] != target:
        raise ValueError('exact_masked_prefix_contiguous_target_required')
    if inputs[prefix:] != target:
        raise ValueError('unchanged_native_target_required')
    keep = len(target) + 1
    return dict(logits_to_keep=keep, labels=labels[-keep:])
