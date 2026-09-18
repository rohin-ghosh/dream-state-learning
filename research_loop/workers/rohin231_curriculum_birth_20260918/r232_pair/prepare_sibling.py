"""One-shot exact-initial sibling preparation; no learner control or GPU calls."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
ORIGINAL = Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')
DEVICE = 'GPU-02917283-de83-a2c7-db03-272dca482162'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)
        output.write('\n')


def main():
    os.umask(0o077)
    assert ROOT == Path('/localhome/local-rohing/orch_r232_curriculum_frozen_20260918')
    assert not (ROOT / 'control').exists() and not (ROOT / 'raw').exists()
    device_inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used',
        '--format=csv,noheader,nounits'], text=True)
    assert '1, ' + DEVICE + ', 0' in device_inventory.splitlines()
    assert DEVICE not in subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
        '--format=csv,noheader,nounits'], text=True)
    old_guard = json.loads((ORIGINAL / 'control/GUARD.json').read_bytes())
    old_plan = json.loads((ORIGINAL / 'control/PLAN.json').read_bytes())
    assert all(sha(ORIGINAL / 'source' / name) == expected for name, expected in old_guard['source_pins'].items())
    assert not any(path.is_symlink() for path in (ORIGINAL / 'source').rglob('*'))
    shutil.copytree(ORIGINAL / 'source', ROOT / 'source', copy_function=shutil.copy2)
    shutil.copy2(ROOT / 'r232_runtime.py', ROOT / 'source/gpu/r232_runtime.py')
    (ROOT / 'control').mkdir()
    (ROOT / 'raw').mkdir()
    (ROOT / 'raw/checkpoints').mkdir()
    source_initial = ORIGINAL / 'raw/checkpoints/initial'
    assert not any(path.is_symlink() for path in source_initial.rglob('*'))
    shutil.copytree(source_initial, ROOT / 'raw/checkpoints/initial', copy_function=shutil.copy2)
    initial_files = {str(path.relative_to(source_initial)): sha(path) for path in source_initial.rglob('*') if path.is_file()}
    assert all(sha(ROOT / 'raw/checkpoints/initial' / name) == expected for name, expected in initial_files.items())
    for name in ('BIRTH_PROMPT.txt', 'BIRTH_SPEC_SOURCE.md', 'BIRTH_MANIFEST.json', 'NO_EXECUTOR.json', 'LEASE.json'):
        shutil.copy2(ORIGINAL / name, ROOT / name)
    shutil.copy2(source_initial / 'COMMIT.json', ROOT / 'INITIAL_ORIGINAL_COMMIT.json')
    source_record = ORIGINAL / 'raw/stream/records/00000000000000000000.json'
    shutil.copy2(source_record, ROOT / 'INITIAL_ORIGINAL_RECORD.json')
    old_commit = json.loads((source_initial / 'COMMIT.json').read_bytes())
    new_commit = deepcopy(old_commit)
    for name in ('adapter_path', 'optimizer_rng_path'):
        new_commit[name] = str(ROOT / Path(old_commit[name]).relative_to(ORIGINAL))
    commit_path = ROOT / 'raw/checkpoints/initial/COMMIT.json'
    commit_path.write_text(json.dumps(new_commit, sort_keys=True, indent=2) + '\n')
    assert all(sha(ROOT / 'raw/checkpoints/initial' / name) == expected
        for name, expected in initial_files.items() if name != 'COMMIT.json')
    sys.path.insert(0, str(ROOT / 'source'))
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_stream_journal import StreamJournal, _digest
    from organism_v6.orch_r124_train_history import TrainHistory
    record = json.loads(source_record.read_bytes())
    assert record['kind'] == 'COMMITTED' and record['document']['kind'] == 'BIRTH'
    assert record['sha256'] == _digest({key: value for key, value in record.items() if key != 'sha256'})
    state = record['document']['state']
    assert state['sha256'] == _digest(state['state'])
    assert not state['state']['rows'] and not state['state']['sleep_receipts'] and state['state']['pending'] is None
    assert TrainHistory.restore(state['state']['history']).working_state['entries'] == []
    with StreamJournal(ROOT / 'raw/stream', create=True) as journal:
        birth_receipt = journal.record('COMMITTED', deepcopy(record['document']))
    plan = deepcopy(old_plan)
    plan.update(root=str(ROOT / 'raw'), source_root=str(ROOT / 'source'), physical=1, gpu_uuid=DEVICE)
    plan['startup_context']['path'] = str(ROOT / 'source/context/BIRTH_R231.txt')
    plan['think_act_learn']['cpu_gate_root'] = str(ROOT)
    native.validate_plan(plan)
    normalized = deepcopy(plan)
    for name in ('root', 'source_root', 'physical', 'gpu_uuid'):
        normalized[name] = old_plan[name]
    normalized['startup_context']['path'] = old_plan['startup_context']['path']
    normalized['think_act_learn']['cpu_gate_root'] = old_plan['think_act_learn']['cpu_gate_root']
    assert normalized == old_plan
    import torch
    payload = torch.load(new_commit['optimizer_rng_path'], map_location='cpu', weights_only=False)
    assert payload['optimizer_steps'] == old_commit['optimizer_steps'] == 0 and payload['optimizer']['state'] == {}
    assert not torch.cuda.is_initialized()
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=os.pathsep.join((str(ROOT), str(ROOT / 'source'))))
    with (ROOT / 'control/CPU.log').open('x') as output:
        tested = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_frozen'],
            cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=60)
    assert tested.returncode == 0
    pins = {str(path.relative_to(ROOT / 'source')): sha(path) for path in (ROOT / 'source').rglob('*.py')}
    binding = dict(schema='R232_EXACT_INITIAL_SIBLING_BINDING_V1', original_initial_file_sha256=initial_files,
        copied_initial_file_sha256={name: sha(ROOT / 'raw/checkpoints/initial' / name) for name in initial_files},
        checkpoint_path_fields_only_relocated=True, original_birth_record_sha256=record['sha256'],
        original_birth_state_sha256=state['sha256'], copied_birth_receipt=birth_receipt,
        original_source_pins=old_guard['source_pins'], extra_source_module_sha256=sha(ROOT / 'source/gpu/r232_runtime.py'),
        original_plan_sha256=sha(ORIGINAL / 'control/PLAN.json'), original_guard_sha256=sha(ORIGINAL / 'control/GUARD.json'),
        seed=old_plan['seed'], birth_sha256=sha(ROOT / 'BIRTH_PROMPT.txt'), same_prompt_decoder_context_recipe=True,
        only_treatment='weight_updates_disabled_in_frozen_sibling', initial_optimizer_steps=0,
        initial_optimizer_state_entries=0, original_learner_never_signaled=True, observed_unix=time.time())
    write(ROOT / 'control/INITIAL_BINDING.json', binding)
    write(ROOT / 'control/PLAN.json', plan)
    builder = json.loads((ROOT / 'BUILDER_LOG_RECEIPT.json').read_bytes())
    assert builder['logged'] is True
    write(ROOT / 'control/RECEIVING_CPU.json', dict(passed=True, tests=4, subtests=7, source_pins=pins,
        log_sha256=sha(ROOT / 'control/CPU.log'), binding_sha256=sha(ROOT / 'control/INITIAL_BINDING.json'),
        builder_log=builder, no_GPU_model_calls=True, exact_initial_not_current=True))
    write(ROOT / 'control/ALLOCATION.json', dict(physical=1, gpu_uuid=DEVICE, declared_unix=time.time(),
        builder_entry_logged=True, cpu_tests_passed=True, plan_sha256=sha(ROOT / 'control/PLAN.json'),
        cpu_receipt_path=str(ROOT / 'control/RECEIVING_CPU.json'), cpu_receipt_sha256=sha(ROOT / 'control/RECEIVING_CPU.json')))
    guard = dict(schema='R125_CONTINUAL_GUARD_V1', host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        attempt_dir=str(ROOT / 'control'), copy_raw=str(ROOT / 'raw'), resume=True,
        plan_path=str(ROOT / 'control/PLAN.json'), plan_sha256=sha(ROOT / 'control/PLAN.json'),
        lease_path=str(ROOT / 'LEASE.json'), lease_sha256=sha(ROOT / 'LEASE.json'),
        hard_end_unix=plan['hard_end_unix'], next_reserved_unix=old_guard['next_reserved_unix'], source_pins=pins,
        allocation_path=str(ROOT / 'control/ALLOCATION.json'), allocation_sha256=sha(ROOT / 'control/ALLOCATION.json'))
    write(ROOT / 'control/GUARD.json', guard)
    from gpu.orch_r125_continual_guard import validate
    validate(ROOT / 'control/GUARD.json')
    print(json.dumps(dict(status='EXACT_INITIAL_CPU_READY_NOT_LOADED', binding_sha256=sha(ROOT / 'control/INITIAL_BINDING.json'),
        plan_sha256=sha(ROOT / 'control/PLAN.json'), physical=1, initial_optimizer_steps=0)))


if __name__ == '__main__':
    main()
