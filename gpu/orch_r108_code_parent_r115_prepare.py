"""Freeze code-only F3 inputs; preparation does not load a model or dispatch."""

import ast
import json
from pathlib import Path
import shutil
import time

from gpu import orch_r108_code_parent_r115_run as run
from gpu import orch_r108_code_parent_r115_guard as guard


ROOT = Path(__file__).resolve().parents[1]


def closure(initial):
    pending, found = list(initial), set()
    while pending:
        relative = pending.pop()
        path = ROOT / relative
        if relative in found or not path.is_file():
            continue
        found.add(relative)
        if path.suffix != '.py':
            continue
        for item in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(item, ast.Import):
                names = [alias.name for alias in item.names]
            elif isinstance(item, ast.ImportFrom) and item.level == 0 and item.module:
                names = [item.module] + [item.module + '.' + alias.name for alias in item.names]
            for name in names:
                parts = name.split('.')
                pending.append('/'.join(parts) + '.py')
                for count in range(1, len(parts) + 1):
                    pending.append('/'.join(parts[:count]) + '/__init__.py')
    return sorted(found)


def prepare(destination):
    destination = Path(destination)
    destination.mkdir(exist_ok=False)
    started = time.time()
    deadline = started + 8 * 3600
    cohort = {split: run.policy.tasks(split) for split in ('TRAIN', 'DEV', 'FINAL')}
    files = closure(['gpu/orch_r108_code_parent_r115_guard.py',
        'gpu/orch_r108_code_parent_r115_engine.py', 'gpu/orch_r108_code_parent_r115_prepare.py',
        'gpu/astra_goal_quality_train.py', 'organism_v6/pcfl_vertical_train.py',
        'tests/test_orch_r108_code_parent_r115_native.py', *run.broker.source_pins(),
        'research_notes/PARENTING_PRINCIPLES_ROHIN_2026-09-15.md',
        'research_notes/R114_SHARED_JUDGE_PROMPT.md'])
    for relative in files:
        target = destination / 'source' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    hashes = {relative: run.sha(destination / 'source' / relative) for relative in files}
    for physical in (2, 6):
        life = f'orch_r108_code_parent_r115_node5_{physical}_20260915_attempt1'
        native_root = '/localhome/local-rohing/' + life
        target = destination / str(physical)
        target.mkdir()
        config = dict(schema=run.broker.SCHEMA, branch='F3', family='code',
            remote_root=native_root, life_id=life, deadline_unix=deadline,
            max_parent_calls=1000, max_budget_usd=2, max_output_tokens=8192,
            train_tasks={task['task_id']: task['content_sha256'] for task in cohort['TRAIN']},
            excluded_task_ids=[task['task_id'] for split in ('DEV', 'FINAL') for task in cohort[split]],
            cohort_sha256=run.policy.digest(cohort['TRAIN']),
            principles_sha256=run.broker.PRINCIPLES_V2_SHA256,
            source_files=run.broker.source_pins(), min_available_bytes=1024**3,
            fallback_parent_fields=run.broker.FALLBACK_PARENT_FIELDS['F3'])
        run.broker.validate_config(config)
        plan = dict(life_id=life, physical=physical, gpu_uuid=guard.DEVICES[physical],
            authorized='R115_WATCHER_RELAYED_ROHIN_DONE', started_unix=started,
            hard_deadline_unix=deadline, lease_end_unix=run.broker.NODE5_HARD_WALL_UNIX + 21600,
            native_cap=8192, parent_cap=1000, cycles=100,
            parent_model=run.broker.MODEL if physical == 2 else 'openai/openai/gpt-6-astra',
            model_dir='/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
            lambda_actual='NOT_APPLIED', optimizer_steps=0, sleep_count=0,
            mode='R116_AUTHORIZED_ELICITATION_ONLY_FALLBACK', cohort_sha256=run.policy.digest(cohort))
        launch = dict(schema='ORCH_R111_FABLE_LAUNCH_V1', authorized=True,
            authorization='WATCHER_RELAYED_ROHIN_DONE', source_reference='R115 DONE and R116 direct launch order',
            config_sha256=run.broker.digest(config), not_before_unix=started)
        for name, value in [('PLAN', plan), ('BROKER_CONFIG', config), ('BROKER_LAUNCH', launch),
            ('COHORT', cohort), ('SOURCE_SHA256', hashes),
            ('CPU_READY', dict(passed=True, tests=10, suite='tests/test_orch_r108_code_parent_r115_native.py',
                status='LOCAL_CPU_PASS_PRIOR_TO_R116', native_model_calls=0, provider_calls=0))]:
            run.write_new(target / (name + '.json'), value)
    return dict(destination=str(destination), source_files=len(hashes), deadline_unix=deadline,
        configs={str(physical):str(destination / str(physical) / 'BROKER_CONFIG.json') for physical in (2, 6)})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    print(json.dumps(prepare(parser.parse_args().destination), sort_keys=True))
