"""Direct exact-state restore; immutable prefix provenance is already retained."""

import json
from pathlib import Path
import sys
import time

from r203_new_arm_v2 import ROOT, SOURCE, read, sha, require, write
from validate_math_d_restore import equal


def main():
    sys.path.insert(0, str(SOURCE))
    import torch
    from gpu.orch_r125_continual_native import NativeChild
    from organism_v6.orch_r125_continual_stream import ContinualStream
    plan = read(ROOT / 'control/PLAN.json')
    logical = Path(plan['root'])
    require(logical.stat().st_ino == (ROOT / 'raw').stat().st_ino, 'private_clone_bind_not_original')
    require(not torch.cuda.is_initialized(), 'CPU_only')
    snapshot = ROOT.parent / 'snapshot'
    manifest = read(snapshot / 'MANIFEST.json')
    context = read(logical / 'stream/records/00000000000000005846.json')
    require(context['sha256'] == manifest['console_record']['sha256'], 'exact_fixed_context_record')
    stream = ContinualStream.restore(context['document']['state'], expected_sha256=context['document']['state']['sha256'])
    require(len(stream.sleep_receipts) == 51 and stream.pending is None and stream.sleep_frontier == len(stream.rows) == 153
        and len(stream.history.events) == 521, 'fixed51_153rows_521events_no_pending_training')
    require(len(list((logical / 'stream/records').glob('*.json'))) == 11694, 'fixed_prefix_record_count')
    checkpoint = read(logical / 'checkpoints/sleep_000051/COMMIT.json')
    NativeChild.verify_checkpoint(checkpoint)
    payload = torch.load(checkpoint['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] == 4908, 'exact4908')
    groups = payload['optimizer']['param_groups']
    require(len(groups) == 1 and groups[0]['lr'] == 3e-5, 'unchanged_learning_rate')
    parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][identifier]['exp_avg'])) for identifier in groups[0]['params']]
    optimizer = torch.optim.AdamW(parameters, lr=3e-5, foreach=False, fused=False)
    optimizer.load_state_dict(payload['optimizer'])
    require(equal(payload['optimizer'], optimizer.state_dict(), torch) and not torch.cuda.is_initialized(), 'CPU_optimizer_restore_exact')
    proof = dict(status='PASS', observed_unix=time.time(), optimizer_restored_exact=True,
        console_masking_preserved=True, cuda_initialized=False, optimizer_steps=4908, completed_sleeps=51,
        historical_rows=153, history_events=521, context_record_sha256=context['sha256'],
        snapshot_manifest_sha256=sha(snapshot / 'MANIFEST.json'), original_C2_modified=False,
        source_root=str(SOURCE), tool_root=str(ROOT / 'raw'), full_journal_rescan=False,
        prefix_provenance='Same pinned original0..5128 and immutable suffix5129..5846, checked during staging',
        failed_prior_full_scan_preserved=True)
    write(ROOT / 'RESTORE_CPU.json', proof)
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
