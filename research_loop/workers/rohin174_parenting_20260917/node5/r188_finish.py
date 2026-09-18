"""Continue only the already restored, never-dispatched R188 same-root recovery."""

import importlib.util
import os
from pathlib import Path
import sys
import time


def main():
    root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location('recovery', root/'recover_v3.py')
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    source = root/'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r125_cpu_experiment import verify_gate, digest
    stop = recovery.read(root/'STOPPED.json')
    intent = recovery.read(root/'ARCHIVE_INTENT.json')
    logical, archive = Path(intent['original']), Path(intent['archive'])
    recovery.require(archive.stat().st_ino == intent['inode'], 'same_complete_original_archive')
    recovery.require(not (root/'control').exists() and not (root/'STARTED.json').exists(), 'no_prior_dispatch')
    records = sorted((logical/'stream/records').glob('[0-9]'*20+'.json'))
    recovery.require(len(records) == 5129 and recovery.read(records[-1])['sha256'] == 'adcbefb57e9598fe75dfadd294dec0ef6aa1530faefbc4574b8b47c7cd834cc9', 'same_fixed_prefix_no_model_records')
    packet = Path('/localhome/local-rohing/orch_r184_C2_sleep41_1789684294308387719')
    for name, expected in recovery.read(packet/'PRESERVATION_RECEIPT.json')['checkpoint_files'].items():
        recovery.require(recovery.sha(logical/'checkpoints/sleep_000041'/name) == expected, 'unchanged_checkpoint')
    for item in intent['inputs']:
        if item['include']:
            recovery.require(recovery.sha(logical/'stream/inbox'/item['name']) == item['sha256'], 'exact_reconciled_input')
    protected_other_owner = []
    for path in archive.rglob('*'):
        if path.is_symlink():
            protected_other_owner.append(dict(path=str(path.relative_to(archive)),preserved_symlink_without_following=True))
            continue
        if path.name == 'WRITER.lock':
            continue
        if path.stat().st_uid != os.getuid():
            protected_other_owner.append(dict(path=str(path.relative_to(archive)),uid=path.stat().st_uid,mode=path.stat().st_mode))
            continue
        path.chmod(0o555 if path.is_dir() else 0o444)
    archive.chmod(0o555)
    recovery.write(root/'RESTORED.json', dict(archive=str(archive),root=str(logical),source_cutoff=5128,
        source_sleep=41,restored_optimizer_steps=4428,discarded_recorded_updates=stop['discarded_recorded_updates'],
        possible_unlogged_inflight=stop['possible_unlogged_inflight_update'],inputs=intent['inputs'],
        preserved_foreign_owned_artifact_permissions=protected_other_owner,retrospective_tool_execution=False,
        label='R188_LOSS_LABELLED_SAME_LIFE_NOT_UNBROKEN',observed_unix=time.time()))
    old_config = recovery.read('/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/GUARD.json')
    plan = recovery.read(old_config['plan_path'])
    gate_root = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate'
    gate_sha = '8b4579d9c99c2f4d54fbd738ff965bc9472ed9f08ff6fae5f4dbfeadceaf1150'
    recovery.require(digest(verify_gate(gate_root)) == gate_sha, 'actual_NODE5_gate')
    recovery.finish_runtime(root, source, logical, plan, gate_root, gate_sha, old_config, guard)


if __name__ == '__main__':
    main()
