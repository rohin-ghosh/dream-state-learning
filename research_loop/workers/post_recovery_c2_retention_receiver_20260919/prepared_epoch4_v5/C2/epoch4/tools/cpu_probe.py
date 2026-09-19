"""CPU-only C2 checkpoint and read-only tail verification in a fresh interpreter."""

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import threading


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def file_hash(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file(), 'regular_evidence_file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mailbox_pins(root):
    require(root.is_dir() and not root.is_symlink(), 'original_inbox_directory')
    return {path.name: file_hash(path) for path in root.iterdir()}


def readonly_tail(source, candidate, selection, prefix_arguments=None):
    from gpu.orch_r125_stream_journal import StreamJournal
    from gpu.checkpoint_tail_runtime import scan

    class ReadOnlyJournal(StreamJournal):
        @staticmethod
        def _publish(*arguments, **keywords):
            raise AssertionError('C2_CPU_probe_never_publishes')

        def record(self, *arguments, **keywords):
            raise AssertionError('C2_CPU_probe_never_records')

    journal = object.__new__(ReadOnlyJournal if prefix_arguments is None else StreamJournal)
    journal.root = Path(selection['root'])
    journal.inbox = journal.root / 'inbox'
    journal._owner = os.getpid()
    journal._mutex = threading.RLock()
    journal._fds = []
    journal._closed = journal._failed = False
    journal._checkpoint_tail = selection
    inbox_before = mailbox_pins(journal.inbox)
    sidecars_before = {item['name']: file_hash(journal.root / item['name'])
        for item in selection['sidecars']}
    try:
        journal._root_fd = journal._open(journal.root, os.O_RDONLY | os.O_DIRECTORY)
        journal._lock_fd = journal._open('WRITER.lock', os.O_RDONLY, journal._root_fd)
        journal._records_fd = journal._open('records', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._inbox_fd = journal._open('inbox', os.O_RDONLY | os.O_DIRECTORY, journal._root_fd)
        journal._manifest = journal._read_json(journal._root_fd, 'JOURNAL.json')
        state = scan(journal, selection, **(prefix_arguments or {}))
        require(all(state[key] is None for key in ('request', 'response', 'sleep_request'))
            and candidate['resume_state']['state']['pending'] is None
            and state['latest']['expected_sha256'] == candidate['resume_state']['sha256'], 'same_resolved_C2_state')
        require(state['index'] == candidate['head_index'] + 1 and state['previous'] == candidate['head_sha256'],
            'unraced_complete_tail_candidate')
        require(mailbox_pins(journal.inbox) == inbox_before
            and {name: file_hash(journal.root / name) for name in sidecars_before} == sidecars_before,
            'inbox_and_correction_ledger_preserved')
        return dict(journal.checkpoint_tail_receipt, read_only=True, writer_lock_acquired=False,
            journal_writes=0, pending=None, sidecars_verified=True, inbox_preserved=True,
            sidecar_pins=sidecars_before, inbox_pins=inbox_before,
            learned_C2=True, source=str(source))
    finally:
        journal.close()


def checkpoint_probe(native, candidate):
    import torch
    require(not torch.cuda.is_initialized(), 'no_GPU_initialized')
    checkpoint = candidate['checkpoint']
    native.NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] > 0, 'learned_C2_not_frozen_pair_control')
    names = payload['parameter_names']
    optimizer = payload['optimizer']
    parameters = [parameter for group in optimizer['param_groups'] for parameter in group['params']]
    require(names and all(isinstance(name, str) for name in names) and len(names) == len(set(names))
        and len(parameters) == len(names) and len(parameters) == len(set(parameters))
        and set(optimizer['state']) == set(parameters), 'exact_saved_optimizer_parameter_structure')
    for parameter in parameters:
        saved = optimizer['state'][parameter]
        require({'step', 'exp_avg', 'exp_avg_sq'} <= set(saved)
            and saved['exp_avg'].shape == saved['exp_avg_sq'].shape
            and int(saved['step']) == payload['optimizer_steps'], 'saved_AdamW_state_and_steps')
        for key in ('exp_avg', 'exp_avg_sq'):
            require(saved[key].device.type == 'cpu' and bool(torch.isfinite(saved[key]).all()), 'finite_CPU_optimizer_state')
    torch.Generator(device='cpu').set_state(payload['cpu_rng'])
    random.Random().setstate(payload['python_rng'])
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
        and payload['cuda_rng'][0].dtype == torch.uint8 and payload['cuda_rng'][0].numel() > 0,
        'saved_cuda_RNG_bytes_checked_not_replayed_on_GPU')
    require(candidate['resume_state']['state']['model_state_sha256'] == native.digest(checkpoint['checkpoint_sha256'])
        and not torch.cuda.is_initialized(), 'saved_working_state_no_GPU_load')
    return dict(adapter_verified=True, optimizer_verified=True, python_cpu_cuda_rng_verified=True,
        working_state_verified=True, no_GPU_calls=True, learned_C2=True,
        saved_cuda_rng_validation='CPU_tensor_bytes_only_not_GPU_restore')


def probe(source, candidate, plan, mode, selection=None, prefix_context=None):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_probe_environment_required')
    require(plan['physical'] == 1 and plan['hard_end_unix'] == 1789927200
        and plan['think_act_learn']['trial_id'] == 'C2_R216_current_conversation_maintenance', 'learned_C2_identity')
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_native as native
    if mode == 'checkpoint':
        return checkpoint_probe(native, candidate)
    if mode == 'tail':
        if prefix_context is None:
            return readonly_tail(source, candidate, selection)
        from gpu.orch_r125_continual_guard import validate
        from gpu.c2_prefix_authority import admitted_prefix, reader_arguments
        guard_path = prefix_context["receiver"]["guard_path"]
        config, validated = validate(guard_path)
        require(validated == plan and plan["source_root"] == str(source), "same_original_CPU_guard_plan")
        with admitted_prefix(config, plan, guard_path=guard_path):
            arguments = reader_arguments(plan, prefix_context, selection)
            return readonly_tail(source, candidate, selection, arguments)
    require(mode == 'guard', 'supported_CPU_probe_mode')
    from gpu.orch_r125_continual_guard import validate
    config, validated = validate(selection['guard_path'])
    require(validated == plan and config['resume'] is True, 'actual_receiving_guard_and_plan')
    return dict(validated=True, guard_sha256=native.sha(selection['guard_path']), admission_bypassed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('checkpoint', 'tail', 'guard'))
    parser.add_argument('--request', type=Path, required=True)
    arguments = parser.parse_args()
    request = json.loads(arguments.request.read_bytes())
    with contextlib.redirect_stdout(sys.stderr):
        result = probe(request['source'], request['candidate'], request['plan'], arguments.mode,
            request.get('selection'), request.get('prefix_context'))
    print(json.dumps(result, sort_keys=True, allow_nan=False))
