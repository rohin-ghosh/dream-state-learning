"""Node-only CPU F2 v4 preparation, preserving the unrun v3 task selections."""

import argparse
import json
import os
from pathlib import Path

from gpu import orch_math_feedback_uptake_r111_prepare as initial
from organism_v6 import orch_math_feedback_uptake_r114 as policy


def prepare(root, repository, predecessor):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_no_dispatch')
    policy.require(root.parent == Path('/localhome/local-rohing') and root.resolve() == root
        and root.name == policy.AREA.name, 'node_only_new_revision')
    policy.require(predecessor == root.parent / policy.previous.AREA.name, 'exact_v3_predecessor')
    read = lambda name: json.loads((predecessor / name).read_text())
    train, dev, final = read('TRAIN.json'), read('DEV8.json'), read('sealed/FINAL8.json')
    policy.require(policy.digest(dev) == '49feeb421c0ff2fd97c358b7d9770d9372f5c62cdfb6348118c836714d3bdbc1', 'frozen_dev')
    policy.require(policy.digest(final) == 'b3642ffe0e6e501ca805e323d28cdf1f159296872b78f798f65180417dc044ee', 'frozen_final')
    common = policy.contract(repository)
    root.mkdir(exist_ok=False)
    sealed = root / 'sealed'
    sealed.mkdir(mode=0o700)
    for name, value in [('TRAIN.json', train), ('DEV8.json', dev), ('sealed/FINAL8.json', final),
            ('COMMON_CONTRACT.json', common), ('FOCUSED_DEV2_PLAN.json', policy.focused_tasks(dev)),
            ('CYCLE_PLAN.json', policy.cycle_plan(1))]:
        initial.write_new(root / name, value)
    os.chmod(sealed / 'FINAL8.json', 0o600)
    dev_plan = read('DEV_SLEEP0_PLAN.json')
    final_plan = read('sealed/FINAL_SLEEP0_PLAN.json')
    final_plan.update(subsequent_schedule='2026-09-15T17:00:00Z_only',
        hard_stop='2026-09-15T17:02:00Z', morning_native_calls_reserved=8)
    initial.write_new(root / 'DEV_SLEEP0_PLAN.json', dev_plan)
    initial.write_new(sealed / 'FINAL_SLEEP0_PLAN.json', final_plan)
    os.chmod(sealed / 'FINAL_SLEEP0_PLAN.json', 0o600)
    return dict(status='R114_CPU_PREPARED_NOT_NATIVE_READY', native_calls=0, parent_calls=0,
        weight_updates=0, optimizer_steps=0, child_training_token_exposures=0,
        sleep_implemented=False, actual_anchor_lambda=None, sleep0_completed=False,
        root=str(root), predecessor=str(predecessor), common_contract=common,
        common_contract_sha256=policy.digest(common), dev_ids=[task['id'] for task in dev],
        dev_set_sha256=policy.digest(dev), dev_file_sha256=policy.sha(root / 'DEV8.json'),
        final_set_sha256=policy.digest(final), final_file_sha256=policy.sha(sealed / 'FINAL8.json'),
        final_task_bytes_omitted=True, train_file_sha256=policy.sha(root / 'TRAIN.json'),
        dev_sleep0_plan_sha256=policy.sha(root / 'DEV_SLEEP0_PLAN.json'),
        final_sleep0_plan_sha256=policy.sha(sealed / 'FINAL_SLEEP0_PLAN.json'),
        focused_ids=[task['id'] for task in dev[:2]],
        focused_plan_sha256=policy.sha(root / 'FOCUSED_DEV2_PLAN.json'),
        sealed_permissions_not_same_uid_isolation=True, native_visibility_integration_pending=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'repository', 'predecessor'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.repository, args.predecessor), indent=2, sort_keys=True))
