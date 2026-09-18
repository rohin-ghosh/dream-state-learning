"""CPU-only checkpoint/context restore check inside the clone's private bind."""

import json
from pathlib import Path
import sys
import time

from receive_math_d import ROOT, SOURCE, SNAPSHOT, read, sha, require


def equal(left, right, torch):
    if torch.is_tensor(left):
        return torch.equal(left, right)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[key], right[key], torch) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(equal(first, second, torch) for first, second in zip(left, right))
    return left == right


def main():
    sys.path.insert(0, str(SOURCE))
    import torch
    from gpu.orch_r125_stream_journal import StreamJournal
    from gpu.orch_r125_continual_native import NativeChild
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan = read(ROOT / 'control/PLAN.json')
    logical = Path(plan['root'])
    require(logical.stat().st_ino == (ROOT / 'raw').stat().st_ino, 'private_bind_maps_exact_new_clone')
    require(not torch.cuda.is_initialized(), 'CPU_only_restore')
    with StreamJournal(logical / 'stream') as journal:
        audit = journal.audit()
        require(audit['record_count'] == 5847 and audit['head_sha256'] == read(SNAPSHOT / 'MANIFEST.json')['console_record']['sha256'], 'exact_frozen_console_head')
        saved = journal.latest_checkpoint()
        stream = ContinualStream.restore(saved['document'], expected_sha256=saved['expected_sha256'])
        require(stream.pending is None and stream.sleep_frontier == len(stream.rows) == 153, 'saved_boundary_no_new_training_rows')
        require(len(stream.sleep_receipts) == 51, 'complete51')
        require(len(stream.history.events) == 521, 'separate_masked_context521_events')
        complete = read(SNAPSHOT / 'complete/SLEEP_COMPLETE.json')['document']['resume_state']['state']
        context = read(SNAPSHOT / 'console/CONTEXT_COMMITTED.json')['document']['state']['state']
        require(complete['rows'] == context['rows'] and context['history']['events'][:504] == complete['history']['events'], 'masked_context_unchanged_training_prefix')
        checkpoint = read(logical / 'checkpoints/sleep_000051/COMMIT.json')
        NativeChild.verify_checkpoint(checkpoint)
        payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
        require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] == 4908, 'exact4908_optimizer')
        groups = payload['optimizer']['param_groups']
        require(len(groups) == 1 and groups[0]['lr'] == 3e-5, 'fixed_learning_rate')
        parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][identifier]['exp_avg'])) for identifier in groups[0]['params']]
        optimizer = torch.optim.AdamW(parameters, lr=3e-5, foreach=False, fused=False)
        optimizer.load_state_dict(payload['optimizer'])
        require(equal(payload['optimizer'], optimizer.state_dict(), torch), 'optimizer_restore_exact_on_CPU')
        require(not torch.cuda.is_initialized(), 'no_CUDA_initialization')
        proof = dict(status='PASS', observed_unix=time.time(), audit=audit, optimizer_steps=4908,
            optimizer_restored_exact=True, console_masking_preserved=True, cuda_initialized=False,
            learning_rate=3e-5, historical_rows=153, history_events=521, completed_sleeps=51,
            snapshot_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json'),
            context_record_sha256=audit['head_sha256'], source_root=str(SOURCE),
            tool_root=str(ROOT / 'raw'), original_C2_modified=False)
    with (ROOT / 'RESTORE_CPU.json').open('x') as output:
        json.dump(proof, output, sort_keys=True, indent=2)
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
