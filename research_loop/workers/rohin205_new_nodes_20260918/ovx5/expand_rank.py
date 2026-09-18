"""Function-preserving rank8->16 expansion; additional B columns start at zero."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def main(source, destination):
    import torch
    from safetensors.torch import load_file, save_file
    config = json.loads((source / 'adapter_config.json').read_bytes())
    assert config['r'] == 8 and config['lora_alpha'] == 16
    assert not any(config.get(name) for name in ['rank_pattern', 'alpha_pattern', 'use_rslora', 'use_dora'])
    destination.mkdir(mode=0o700)
    config.update(r=16, lora_alpha=32)
    (destination / 'adapter_config.json').write_text(json.dumps(config, indent=2, sort_keys=True))
    tensors = load_file(str(source / 'adapter_model.safetensors'), device='cpu')
    generator = torch.Generator(device='cpu').manual_seed(209)
    expanded = {}
    for name, tensor in tensors.items():
        if 'lora_A.' in name:
            assert tensor.shape[0] == 8
            value = torch.empty((16, tensor.shape[1]), dtype=tensor.dtype)
            value[:8].copy_(tensor)
            bound = 1 / math.sqrt(tensor.shape[1])
            value[8:].uniform_(-bound, bound, generator=generator)
        elif 'lora_B.' in name:
            assert tensor.shape[1] == 8
            value = torch.zeros((tensor.shape[0], 16), dtype=tensor.dtype)
            value[:, :8].copy_(tensor)
        else:
            value = tensor
        expanded[name] = value
    checks = 0
    for name, tensor in tensors.items():
        if 'lora_A.' in name:
            other = name.replace('lora_A.', 'lora_B.')
            assert torch.equal(expanded[name][:8], tensor)
            assert torch.equal(expanded[other][:, :8], tensors[other]) and torch.count_nonzero(expanded[other][:, 8:]) == 0
            checks += 1
    assert checks > 0
    save_file(expanded, str(destination / 'adapter_model.safetensors'))
    receipt = dict(schema='R209_FUNCTION_PRESERVING_RANK_EXPANSION_V1', source_rank=8, target_rank=16,
        source_alpha=16, target_alpha=32, lora_scale_unchanged=2, seed=209, checked_pairs=checks,
        added_A='deterministic_Kaiming_uniform', added_B='zero', scalar_head_unchanged=True,
        original_A_B_blocks_bitwise_preserved=True, training_updates=0)
    (destination / 'EXPANSION.json').write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    arguments = parser.parse_args()
    main(arguments.source, arguments.destination)
