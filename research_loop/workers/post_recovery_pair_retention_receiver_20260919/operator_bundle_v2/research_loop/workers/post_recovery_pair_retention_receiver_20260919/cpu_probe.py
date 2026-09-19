"""Explicit CPU-only checkpoint or read-only checkpoint+tail probe; never dispatch."""

import argparse
import contextlib
import json
import os
from pathlib import Path
import random
import sys
import threading


def probe(source, candidate, plan, mode, selection=None):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_probe_environment_required')
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    from gpu import r232_recovery as recovery
    checkpoint = candidate['checkpoint']
    if mode == 'guard':
        from gpu.orch_r125_continual_guard import validate
        config, validated = validate(selection['guard_path'])
        native.require(validated == plan and config['resume'] is True, 'actual_receiving_guard_and_plan')
        return dict(validated=True, guard_sha256=native.sha(selection['guard_path']), admission_bypassed=False)
    if mode == 'checkpoint':
        import torch
        native.NativeChild.verify_checkpoint(checkpoint)
        payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
        native.require(payload['optimizer_steps'] == checkpoint['optimizer_steps'], 'saved_optimizer_counter')
        native.require(payload['optimizer']['param_groups'] and payload['parameter_names'], 'optimizer_structure')
        native.require((checkpoint['optimizer_steps'] == 0) if plan['physical'] == 1
            else checkpoint['optimizer_steps'] > 0, 'pair_control_unchanged')
        torch.Generator(device='cpu').set_state(payload['cpu_rng'])
        random.Random().setstate(payload['python_rng'])
        native.require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
            and payload['cuda_rng'][0].numel() > 0 and not torch.cuda.is_initialized(), 'saved_cuda_rng_no_GPU_init')
        native.require(candidate['resume_state']['state']['model_state_sha256']
            == native.digest(checkpoint['checkpoint_sha256']), 'saved_state_model_binding')
        return dict(adapter_verified=True, optimizer_verified=True, python_cpu_cuda_rng_verified=True,
            working_state_verified=True, no_GPU_calls=True)
    from gpu.checkpoint_tail_runtime import scan
    recovery.frozen.INITIAL = native.read(recovery.ROOTS[1] / 'raw/checkpoints/initial/COMMIT.json')
    base = recovery.FrozenJournal if plan['physical'] == 1 else recovery.LearnerJournal
    journal = object.__new__(base)
    journal.root = Path(selection['root'])
    journal.inbox = journal.root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = journal._failed = False
    try:
        journal._root_fd = journal._open(journal.root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        state = scan(journal, selection)
        native.require(all(state[key] is None for key in ('request', 'response', 'sleep_request'))
            and state['latest']['expected_sha256'] == candidate['resume_state']['sha256'], 'same_resolved_pair_state')
        native.require(state['index'] == candidate['head_index'] + 1
            and state['previous'] == candidate['head_sha256'], 'unraced_tail_probe')
        return dict(journal.checkpoint_tail_receipt, read_only=True, writer_lock_acquired=False, journal_writes=0)
    finally:
        journal.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('checkpoint', 'tail', 'guard'))
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_bytes())
    with contextlib.redirect_stdout(sys.stderr):
        result = probe(request['source'], request['candidate'], request['plan'], args.mode, request.get('selection'))
    print(json.dumps(result, sort_keys=True, allow_nan=False))
