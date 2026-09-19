"""Stage and test Main's four-file R227 release without altering running lives."""

from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from r205_prepare import ROOT, PYTHON, read, require, sha, write
from r226_caption_roots import ASSIGNMENTS


POLICY = 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1'
FILTERS = ('code_target_filter', 'learn_review_filter', 'prose_target_filter',
    'content_target_filter', 'question_target_filter', 'fabricated_speaker_filter')
NAMES = tuple(ASSIGNMENTS) + ('r213_math_a', 'r213_math_b_fork', 'r213_math_c')


def policy_plan(original, source):
    plan = deepcopy(original)
    for config in (plan, plan['think_act_learn']):
        config['learn_row_policy'] = POLICY
        for key in FILTERS:
            config.pop(key, None)
    plan['source_root'] = str(source)
    if 'startup_context' in plan:
        relative = Path(original['startup_context']['path']).relative_to(original['source_root'])
        plan['startup_context']['path'] = str(source / relative)
    return plan


def stage(name):
    require(name in NAMES, 'eight_owned_node3_identities')
    arm = ROOT / name
    active_path = arm / 'ACTIVE_RUNTIME.json'
    active_bytes = active_path.read_bytes()
    active = read(active_path)
    original_source, original_control = Path(active['source']), Path(active['control'])
    original_plan = read(original_control / 'PLAN.json')
    original_plan_sha256 = sha(original_control / 'PLAN.json')
    source, control = arm / 'source_r227_policy_ready', arm / 'control_r227_policy_ready'
    require(not source.exists() and not control.exists(), 'one_new_immutable_receiving_attempt')
    control.mkdir(mode=0o700)
    shutil.copytree(original_source, source)
    overlay = ROOT / 'r227_policy_overlay'
    manifest = read(overlay / 'MANIFEST.json')
    before = {relative: sha(original_source / relative) for relative in manifest
        if (original_source / relative).exists()}
    for relative, expected in manifest.items():
        require(sha(overlay / relative) == expected, 'Main_release_receiving_hash')
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay / relative, destination)
    shutil.copy2(ROOT / 'test_r227_policy_stage.py', source / 'tests/test_r227_policy_stage.py')
    shutil.copy2(ROOT / 'r227_policy_stage.py', source / 'tests/r227_policy_stage.py')
    plan = policy_plan(original_plan, source)
    sys.path.insert(0, str(source))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import validate_config
    from organism_v6.orch_r125_continual_stream import experiment_binding, verify_experiment_resume
    validate_plan(plan)
    validate_config(plan['think_act_learn'])
    verify_experiment_resume(plan, experiment_binding(original_plan))
    require(plan['birth_prompt'] == original_plan['birth_prompt'], 'immutable_birth_prompt')
    if 'startup_context' in plan:
        require(sha(Path(plan['startup_context']['path'])) == plan['startup_context']['sha256'],
            'unchanged_startup_bytes')
    for key in ('hard_end_unix', 'lease_end_unix', 'root', 'gpu_uuid', 'physical',
            'new_presentations', 'rehearsal_presentations', 'plasticity'):
        require(plan.get(key) == original_plan.get(key), 'same_recipe_wall_identity_' + key)
    write(control / 'PLAN.json', plan)
    tests = ['test_orch_r227_learning_policy', 'test_r227_policy_stage',
        'test_orch_r184_think_act_learn', 'test_orch_r205_reading_policy',
        'test_orch_r194_code_target_filter', 'test_orch_r195_learn_review_filter']
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='1', PYTHONPATH=os.pathsep.join((str(source), str(source / 'tests'), str(ROOT))))
    with (control / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'R227_receiving_regressions_imports_provenance')
    require(active_path.read_bytes() == active_bytes, 'active_pointer_never_changed')
    require(all(sha(original_source / relative) == expected for relative, expected in before.items()),
        'running_source_never_changed')
    require(sha(original_control / 'PLAN.json') == original_plan_sha256,
        'active_control_unchanged')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(control / 'RECEIVING_CPU.json', dict(passed=True, observed_utc=datetime.now(timezone.utc).isoformat(),
        source_pins=pins, tests=tests, log_sha256=sha(control / 'CPU.log'), overlay=manifest,
        source=str(source), plan_sha256=sha(control / 'PLAN.json'),
        learn_row_policy=POLICY, active_semantic_filters=[],
        experiment_binding_unchanged=True, live_source_unchanged=True, active_pointer_unchanged=True,
        old_active_runtime=active, activated=False, LOADED=None, SLEEP_RECIPE=None,
        blocker='No existing live reader adopts source modules or plan changes; no pause/restart authorized.'))
    write(control / 'READY.json', dict(status='RECEIVING_CPU_PASS_NOT_ADOPTED', observed_unix=time.time(),
        policy=POLICY, plan_sha256=sha(control / 'PLAN.json'),
        receiving_cpu_sha256=sha(control / 'RECEIVING_CPU.json'),
        live_activation_claimed=False, dispatch_controller_armed=False))
    print(name, 'RECEIVING_CPU_PASS_NOT_ADOPTED', flush=True)


if __name__ == '__main__':
    stage(sys.argv[1])
