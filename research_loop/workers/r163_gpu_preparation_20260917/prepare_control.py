"""Generate CPU-validated R163 candidate3 bindings, without dispatch."""

from pathlib import Path
import hashlib
import importlib
import json
import subprocess
import sys
import time
import uuid


ROOT = Path('/localhome/local-rohing/orch_r163_numerical_preparation_20260917_attempt1')
SOURCE = ROOT / 'selected_source_candidate3'
CONTROL = ROOT / 'control_candidate3'
GUARD_SHA = '4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n')


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def main():
    original = json.loads((ROOT / 'source/STAGED_SOURCE.json').read_bytes())['files']
    additions = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*')
                 if path.is_file() and str(path.relative_to(SOURCE)) not in original
                 and path.name != 'STAGED_SOURCE.json'}
    assert len(additions) == 6
    assert all(sha(SOURCE / name) == checksum for name, checksum in original.items()
               if name != 'gpu/orch_r125_continual_guard.py')
    assert sha(SOURCE / 'gpu/orch_r125_continual_guard.py') == GUARD_SHA
    assert all(not path.is_symlink() and path.stat().st_mode & 0o222 == 0 for path in SOURCE.rglob('*'))
    sys.path.insert(0, str(SOURCE))
    modules = {}
    for name in ('orch_r125_continual_native', 'orch_r125_continual_guard', 'orch_r133_node3_programmes',
                 'orch_r163_probe_driver', 'orch_r163_executor_probe', 'orch_r161_native_executor',
                 'astra_experienced_event_microloop', 'orch_guided_native',
                 'orch_r107_base_anchors_inventory', 'orch_r145_suffix_loss', 'orch_r108_guided_native'):
        modules[name] = importlib.import_module('gpu.' + name)
    import torch
    assert not torch.cuda.is_initialized()
    native = modules['orch_r125_continual_native']
    guard = modules['orch_r125_continual_guard']
    node3 = modules['orch_r133_node3_programmes']
    driver = modules['orch_r163_probe_driver']
    plan = json.loads((ROOT / 'PLAN.json').read_bytes())
    prior_plan = json.loads((ROOT / 'control_candidate2/PLAN.json').read_bytes())
    plan.update(source_root=str(SOURCE), hard_end_unix=prior_plan['hard_end_unix'])
    assert time.time() < plan['hard_end_unix'] <= time.time() + 1800
    assert plan['hard_end_unix'] + 21600 <= 1789668000
    native.validate_plan(plan)
    assert not Path(plan['root']).exists()
    write(CONTROL / 'PLAN.json', plan)
    manifest = dict(schema='R163_PROBE_SOURCE_PINS_V1',
                    files={str(path): sha(path) for path in SOURCE.rglob('*') if path.is_file()})
    manifest['files'][str(CONTROL / 'admitted_probe.py')] = sha(CONTROL / 'admitted_probe.py')
    write(CONTROL / 'SOURCE_PINS.json', manifest)
    driver.verify_sources(manifest)
    origins = driver.verify_imports(manifest)
    lease = Path('/localhome/local-rohing/orch_r118_node3_7_grid_20260915_attempt1/lease_budget_r119_learned/LEASE_BUDGET.json')
    allocation = dict(plan_sha256=sha(CONTROL / 'PLAN.json'), cpu_tests_passed=True,
                      gpu_uuid=plan['gpu_uuid'], physical=5, builder_entry_pushed=True,
                      builder_entry_pushed_semantics='legacy field means posted locally, NOT git pushed',
                      declared_unix=time.time(), purpose='R163_VALIDATION_ONLY_PREPARATION_NOT_RESERVATION',
                      main_GPU_GO_required=True,
                      CPU_evidence='6 receiving reviewed-driver tests; 7 local/receiving external-wrapper tests; actual imports/plan validation')
    write(CONTROL / 'ALLOCATION.json', allocation)
    config = dict(schema='R125_CONTINUAL_GUARD_V1', plan_path=str(CONTROL / 'PLAN.json'),
                  plan_sha256=sha(CONTROL / 'PLAN.json'),
                  source_pins={str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')},
                  host_sha256=hashlib.sha256(b'[REDACTED_HOST]').hexdigest(),
                  hard_end_unix=plan['hard_end_unix'], lease_path=str(lease), lease_sha256=sha(lease),
                  next_reserved_unix=1789689600, allocation_path=str(CONTROL / 'ALLOCATION.json'),
                  allocation_sha256=sha(CONTROL / 'ALLOCATION.json'), attempt_dir=str(ROOT / 'attempt1'),
                  resume=False, device_containment=dict(uid=2524, gid=2524, minor=5,
                  unit='orch-r133-node3-' + uuid.uuid4().hex))
    write(CONTROL / 'GUARD.json', config)
    assert guard.validate(CONTROL / 'GUARD.json') == (config, plan)
    command = node3.containment_command(plan, config['device_containment'],
        [sys.executable, '-B', str(CONTROL / 'admitted_probe.py'), 'native', '--main-go',
         str(CONTROL / 'MAIN_GO.json'), '--main-go-sha256', 'MAIN_SUPPLIED_EXACT_GO_SHA256'], 1800)
    assert '--property=DevicePolicy=strict' in command
    assert '--property=DeviceAllow=/dev/nvidia5 rw' in command
    assert all('--property=DeviceAllow=/dev/nvidia' + str(minor) + ' rw' not in command
               for minor in (0, 1, 2, 3, 4, 6, 7))
    spec = importlib.util.spec_from_file_location('r163_external_operator', CONTROL / 'admitted_probe.py')
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    expected = operator.binding(config)
    proof = dict(status='CPU_PREPARED_PENDING_MAIN_REVIEW_AND_GO', observed_unix=time.time(),
                 plan=ref(CONTROL / 'PLAN.json'), config=ref(CONTROL / 'GUARD.json'),
                 manifest=ref(CONTROL / 'SOURCE_PINS.json'), operator=ref(CONTROL / 'admitted_probe.py'),
                 required_GO_schema='R163_NODE3_NUMERICAL_GO_V1', required_GO_binding=expected,
                 import_origins=origins, source_origin=ref(ROOT / 'source/STAGED_SOURCE.json'),
                 selected_additions=additions,
                 guard_replacement=dict(origin='/localhome/local-rohing/orch_r145_combined_targets_20260916t1645z_2/physical5/source/gpu/orch_r125_continual_guard.py',
                                        sha256=GUARD_SHA, reason='standalone native plan, not R150 matched cohort'),
                 other_candidate5_files_unchanged=True, guard_validate_actual='PASS',
                 containment_command_CPU_constructed_not_executed=command,
                 source_files_pinned=len(manifest['files']), native_seed=plan['seed'],
                 checkpoint_loaded=False, model_loaded=False, cuda_initialized=torch.cuda.is_initialized(),
                 root_exists=Path(plan['root']).exists(), attempt_exists=(ROOT / 'attempt1').exists(),
                 proposed_runtime_seconds=1800, remaining_lease_hardwall_seconds=1789668000-time.time(),
                 six_hour_margin_preserved=plan['hard_end_unix']+21600 <= 1789668000,
                 physical5_gpu_metadata=subprocess.check_output(['nvidia-smi', '-i', plan['gpu_uuid'],
                    '--query-gpu=index,uuid,memory.used,memory.total,utilization.gpu', '--format=csv,noheader'], text=True),
                 not_R163_science_training_admission=True)
    write(CONTROL / 'PREPARED_EXECUTION.json', proof)
    print(json.dumps(proof, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
