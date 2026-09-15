"""Node-local CPU-only matched F2 cohort and sleep-0 request preparation."""

import argparse
import json
import os
from pathlib import Path

from organism_v6 import orch_math_feedback_uptake_r111 as policy


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)


def sleep0(cohort):
    return dict(phase='sleep0', label='PRE_EXPERIENCE_BASE_READOUT_NOT_A_WEIGHT_SLEEP',
        completed=False, native_calls=0, parent_calls=0, weight_updates=0,
        fresh_process=True, parent_free=True, context_free=True, batch_size=8,
        decoder=policy.decoder('held'), tasks=[dict(id=task['id'],
            question_sha256=task['question_sha256'], messages=policy.messages('held', task['question']),
            messages_sha256=policy.digest(policy.messages('held', task['question']))) for task in cohort['held']])


def prepare(root, repository, registry_path):
    policy.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'cpu_only_no_provider_or_gpu')
    policy.require(str(root).startswith('/localhome/local-rohing/orch_math_feedback_uptake_r111_f2_')
        and root.resolve() == root, 'node_only_raw_cohort')
    registry = json.loads(registry_path.read_text())
    policy.require(len(registry['excluded_ids']) >= 5846 and len(registry['excluded_question_sha256']) >= 5838,
        'inherited_pools_required')
    common = policy.contract(repository)
    cohort = policy.cohort(registry['excluded_ids'], registry['excluded_question_sha256'])
    baseline = sleep0(cohort)
    root.mkdir(parents=True, exist_ok=True)
    write_new(root / 'COHORT.json', cohort)
    write_new(root / 'COMMON_CONTRACT.json', common)
    write_new(root / 'SLEEP0_PLAN.json', baseline)
    (root / 'F2.md').write_text(policy.parent_template(repository))
    members = {name:dict(binding, common_contract_sha256=policy.digest(common),
        cohort_sha256=policy.sha(root / 'COHORT.json'), sleep0_plan_sha256=policy.sha(root / 'SLEEP0_PLAN.json'),
        parent_model_only_scientific_difference=True, native_calls=0, parent_calls=0)
        for name, binding in policy.MEMBERS.items()}
    write_new(root / 'MEMBERS.json', members)
    return dict(status='CPU_PREPARED_NOT_NATIVE_LAUNCH_READY', native_calls=0, parent_calls=0,
        root=str(root), common_contract=common, common_contract_sha256=policy.digest(common),
        cohort_sha256=policy.sha(root / 'COHORT.json'), inherited_registry_sha256=policy.sha(registry_path),
        inherited_ids=len(registry['excluded_ids']), inherited_questions=len(registry['excluded_question_sha256']),
        sleep0_plan_sha256=policy.sha(root / 'SLEEP0_PLAN.json'), sleep0_completed=False,
        held_ids=[task['id'] for task in cohort['held']],
        held_set_sha256=policy.digest(cohort['held']),
        held_question_sha256={task['id']:task['question_sha256'] for task in cohort['held']},
        members=members, parent_template_sha256=policy.sha(root / 'F2.md'),
        blockers=['Fable watcher-relayed explicit Rohin GO for GPU and provider',
            'Cicero physical5 natural-cycle release; keep current life running',
            'Native integration of shared broker wire, missing continuation and batched sleep0',
            'Bind existing retention/audit/capability and shared judge before associated calls',
            'Exact fresh native source/base/proc/UUID/CVD admission'],
        raw_rows_local=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('root', 'repository', 'registry'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.repository, args.registry), indent=2, sort_keys=True))
