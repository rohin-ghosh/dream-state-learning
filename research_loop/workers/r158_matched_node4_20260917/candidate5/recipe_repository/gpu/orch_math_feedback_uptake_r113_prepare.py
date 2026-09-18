"""CPU-only v3 preparation; sealed FINAL task bytes never enter public receipts."""

import argparse
import json
import os
from pathlib import Path

from gpu import orch_math_feedback_uptake_r111_prepare as previous
from organism_v6 import orch_math_feedback_uptake_r113 as policy


def read(path):
    return json.loads(Path(path).read_text())


def prepare(root, repository, predecessor):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only')
    policy.require(root.name == 'orch_math_feedback_uptake_r113_f2_20260915_attempt1'
        and root.parent == Path('/localhome/local-rohing') and root.resolve() == root, 'node_only_sealed_storage')
    old = read(predecessor / 'COHORT.json')
    registry = read(predecessor / 'EXCLUSION_REGISTRY.json')
    identifiers, questions = set(registry['excluded_ids']), set(registry['excluded_question_sha256'])
    for group in old['train'] + [old['held']]:
        for task in group:
            identifiers.add(task['id'])
            questions.add(task['question_sha256'])
    dev = [dict(task, split='DEV') for task in old['held']]
    final = policy.final_cohort(identifiers, questions)
    common = policy.contract(repository)
    root.mkdir(parents=True, exist_ok=True)
    sealed = root / 'sealed'
    sealed.mkdir(mode=0o700)
    previous.write_new(root / 'TRAIN.json', old['train'])
    previous.write_new(root / 'DEV8.json', dev)
    previous.write_new(sealed / 'FINAL8.json', final)
    os.chmod(sealed / 'FINAL8.json', 0o600)
    previous.write_new(root / 'COMMON_CONTRACT.json', common)
    dev_plan = previous.sleep0(dict(held=dev))
    dev_plan.update(split='DEV', subsequent_schedule='every_cycle', head_visible=True,
        taskset_sha256=policy.digest(dev))
    final_plan = previous.sleep0(dict(held=final))
    final_plan.update(split='FINAL', subsequent_schedule='2026-09-16T06:00:00Z_only',
        parent_head_exchange_visible=False, taskset_sha256=policy.digest(final))
    previous.write_new(root / 'DEV_SLEEP0_PLAN.json', dev_plan)
    previous.write_new(sealed / 'FINAL_SLEEP0_PLAN.json', final_plan)
    os.chmod(sealed / 'FINAL_SLEEP0_PLAN.json', 0o600)
    return dict(status='R113_CPU_PREPARED_NOT_NATIVE_READY', native_calls=0, parent_calls=0,
        root=str(root), predecessor=str(predecessor), predecessor_cohort_sha256=policy.sha(predecessor / 'COHORT.json'),
        common_contract=common, common_contract_sha256=policy.digest(common),
        train_sha256=policy.sha(root / 'TRAIN.json'), dev_ids=[task['id'] for task in dev],
        dev_set_sha256=policy.digest(dev), dev_file_sha256=policy.sha(root / 'DEV8.json'),
        dev_sleep0_plan_sha256=policy.sha(root / 'DEV_SLEEP0_PLAN.json'),
        final_count=8, final_set_sha256=policy.digest(final), final_file_sha256=policy.sha(sealed / 'FINAL8.json'),
        final_sleep0_plan_sha256=policy.sha(sealed / 'FINAL_SLEEP0_PLAN.json'),
        final_ids_questions_answers_results_omitted=True, dev_final_train_disjoint=True,
        sleep0_completed=False, morning_final_completed=False, weight_updates=0,
        filesystem_permissions_not_a_claim_of_isolation_between_same_uid_workers=True,
        final_export_guard_requires_actual_native_integration=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'repository', 'predecessor'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.repository, args.predecessor), indent=2, sort_keys=True))
