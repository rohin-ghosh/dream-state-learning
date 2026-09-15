"""Two explicitly relocated BASE-context forks on a40r physical 4 and 5."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE_SOURCE = Path('/localhome/local-rohing/orch_r119_code_old_forks_20260915_v3/source')
if BASE_SOURCE.exists():
    import gpu
    gpu.__path__.append(str(BASE_SOURCE / 'gpu'))
    sys.path.append(str(BASE_SOURCE))

from gpu import orch_r119_code_old_fork as fork
from gpu import orch_r119_code_old_admission as admission

MODULE = 'gpu.orch_r123_base_code_refill'
SEED = Path('/localhome/local-rohing/orch_r119_code_old_forks_20260915_v3/a40r_6')


def configure():
    fork.ALLOCATIONS = {'a40r': (4, 5)}
    fork.MODULE = MODULE


def derive(seed, root, physical, gpu_uuid, source_root):
    fork.require(seed['wrapper'] == 'a40r' and seed['physical'] == 6
                 and seed['adapter'] is None, 'existing_BASE_seed_only')
    fork.require(physical in (4, 5) and gpu_uuid.startswith('GPU-')
                 and gpu_uuid != seed['gpu_uuid'], 'new_owned_physical_only')
    plan = deepcopy(seed)
    plan.update(root=str(root), physical=physical, gpu_uuid=gpu_uuid,
                source_root=str(source_root), guard_module=MODULE,
                life_id=f'R123_BASE_CODE_CONTEXT_FORK_a40r_{physical}')
    plan.pop('predecessor_guard_failures', None)
    plan['relocated_context_fork'] = dict(seed_root=str(SEED), same_host_history=False,
        semantics='Frozen BASE with copied prior TRAIN context, not a resumed math optimizer')
    return plan


def prepare(root, physical, tests):
    configure()
    seed = fork.read(SEED / 'PLAN.json')
    for path, digest in seed['source_files'].items():
        fork.require(fork.ref(path)['sha256'] == digest, 'unchanged_verified_source')
    for binding in seed['inputs'].values():
        fork.checked(binding)
    test_result = fork.read(tests)
    fork.require(test_result['passed'] is True, 'own_CPU_tests_before_prepare')
    output = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
                                     '--format=csv,noheader,nounits'], text=True)
    devices = {int(line.split(',')[0]): line.split(',')[1].strip()
               for line in output.splitlines()}
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    source_root = Path(__file__).resolve().parents[1]
    plan = derive(seed, root, physical, devices[physical], source_root)
    for filename in ('COHORT_PRIVATE.json', 'RESERVATIONS.json'):
        shutil.copyfile(SEED / filename, root / filename)
    for key, filename in (('cohort', 'COHORT_PRIVATE.json'), ('reservations', 'RESERVATIONS.json')):
        plan['inputs'][key] = fork.ref(root / filename)
    plan['source_files'][str(Path(__file__).resolve())] = fork.ref(__file__)['sha256']
    plan['source_files'][str(source_root / 'gpu/__init__.py')] = fork.ref(source_root / 'gpu/__init__.py')['sha256']
    plan['seed_plan'] = fork.ref(SEED / 'PLAN.json')
    for name in ('parent_queue', 'parent_claude', 'parent_transcripts', 'delayed_interventions',
                 'campaign_code_parent/cells'):
        (root / name).mkdir(parents=True, exist_ok=False)
    fork.write(root / 'CPU_TESTS.json', test_result)
    fork.write(root / 'PLAN.json', plan)
    fork.plan_for(root)
    return dict(root=str(root), plan=fork.ref(root / 'PLAN.json'), physical=physical,
                parent_nonblocking=True, optimizer_updates=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'service', 'scan', 'guard', 'native'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--physical', type=int, choices=(4, 5))
    parser.add_argument('--tests', type=Path)
    arguments = parser.parse_args()
    configure()
    if arguments.phase == 'prepare':
        print(json.dumps(prepare(arguments.root, arguments.physical, arguments.tests)))
    elif arguments.phase == 'scan':
        print(json.dumps(admission.scan(arguments.root)))
    elif arguments.phase == 'service':
        print(json.dumps(fork.bound_scan(arguments.root, service=True)))
    else:
        getattr(fork, arguments.phase)(arguments.root)
