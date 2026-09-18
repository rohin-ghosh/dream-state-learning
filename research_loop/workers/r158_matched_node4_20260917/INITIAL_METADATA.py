"""Read-only CPU metadata of the hash-bound R158 common initializer checkpoint."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            checksum.update(block)
    return checksum.hexdigest()


def read(path):
    require(not any(part.is_symlink() for part in (path, *path.parents)), 'unlinked_checkpoint_path')
    return json.loads(path.read_bytes())


def adapter_header(path):
    with path.open('rb') as stream:
        size_bytes = stream.read(8)
        require(len(size_bytes) == 8, 'safetensors_length_header')
        size = struct.unpack('<Q', size_bytes)[0]
        require(0 < size <= 4 * 1024 * 1024 and size + 8 <= path.stat().st_size, 'bounded_safetensors_header')
        data = stream.read(size)
    header = json.loads(data)
    tensors = {name: value for name, value in header.items() if name != '__metadata__'}
    require(tensors, 'nonempty_adapter_header')
    counts = {}
    for value in tensors.values():
        shape, dtype = value['shape'], value['dtype']
        require(isinstance(shape, list) and all(type(count) is int and count > 0 for count in shape)
                and dtype in ('F32', 'F16', 'BF16'), 'bounded_floating_adapter_shapes')
        count = math.prod(shape)
        entry = counts.setdefault(dtype, dict(tensors=0, numel=0, bytes=0))
        entry['tensors'] += 1
        entry['numel'] += count
        entry['bytes'] += count * (4 if dtype == 'F32' else 2)
        offsets = value['data_offsets']
        require(len(offsets) == 2 and all(type(offset) is int and offset >= 0 for offset in offsets)
                and offsets[1] - offsets[0] == count * (4 if dtype == 'F32' else 2)
                and offsets[1] <= path.stat().st_size - size - 8, 'header_shape_storage_agreement')
    return dict(tensor_count=len(tensors), dtypes=counts, total_numel=sum(value['numel'] for value in counts.values()),
                tensor_values_read=False, header_sha256=hashlib.sha256(data).hexdigest())


def inspect(base, expected_cohort_sha256):
    require(base.parent == Path('/localhome/local-rohing') and base.name.startswith('orch_r158_matched_node4_')
            and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'scoped_CPU_metadata_only')
    require(sha(base / 'COHORT.json') == expected_cohort_sha256, 'exact_cohort')
    cohort = read(base / 'COHORT.json')
    initial = base / 'common_initial'
    require(cohort['initial_directory'] == str(initial), 'exact_initial_directory')
    commit = read(initial / 'COMMIT.json')
    initialized = read(initial / 'INITIALIZED.json')
    require(initialized['cohort_sha256'] == expected_cohort_sha256
            and initialized['checkpoint_commit_sha256'] == sha(initial / 'COMMIT.json'), 'actual_initialized_binding')
    require(commit['optimizer_steps'] == 0 and initialized['optimizer_updates'] == 0
            and initialized['generation_calls'] == 0, 'no_initial_training_or_generation')
    adapter = initial / 'adapter'
    require(commit['adapter_path'] == str(adapter), 'bound_adapter_directory')
    files = {path.name: sha(path) for path in adapter.iterdir() if path.is_file()}
    require(files == commit['adapter_files'], 'all_saved_adapter_bytes')
    headers = {path.name: adapter_header(path) for path in adapter.glob('*.safetensors')}
    require(headers, 'actual_safe_adapter_header')
    optimizer = initial / 'optimizer_rng.pt'
    require(commit['optimizer_rng_path'] == str(optimizer)
            and sha(optimizer) == commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng'],
            'saved_optimizer_RNG_file_binding')
    import torch
    payload = torch.load(optimizer, map_location='cpu', weights_only=True)
    require(payload['optimizer_steps'] == 0 and payload['optimizer']['state'] == {}, 'saved_empty_AdamW_state')
    require(not torch.cuda.is_initialized(), 'no_CUDA_initialization')
    numel = sum(value['total_numel'] for value in headers.values())
    return dict(schema='R158_INITIAL_ADAPTER_ADAMW_METADATA_V1', observed_unix=time.time(),
        cohort_sha256=expected_cohort_sha256, initialized_sha256=sha(initial / 'INITIALIZED.json'),
        commit_sha256=sha(initial / 'COMMIT.json'), adapter_headers=headers,
        total_adapter_numel=numel, source_estimate_numel=20185088, matches_source_estimate=numel == 20185088,
        saved_optimizer_steps=payload['optimizer_steps'], saved_AdamW_state_entries=len(payload['optimizer']['state']),
        saved_optimizer_group_count=len(payload['optimizer']['param_groups']),
        saved_parameter_name_count=len(payload['parameter_names']),
        estimated_two_FP32_moment_bytes=numel * 8, estimate_not_measured_residual_free_memory=True,
        reference_two_GiB_floor_bytes=2 * 1024 ** 3, GPU_calls=0, optimizer_updates_performed=0,
        adapter_values_returned=False, RNG_values_returned=False, evaluation_contents_read=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--cohort-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.base, args.cohort_sha256)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(result, sort_keys=True))
