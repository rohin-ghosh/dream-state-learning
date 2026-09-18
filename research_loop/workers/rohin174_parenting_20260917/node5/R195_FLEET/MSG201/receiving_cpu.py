"""Receiving tests and exact-state proof using the existing clone namespace."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
sys.path.insert(0, str(SOURCE))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def tests():
    ready = read(ROOT / 'main_ready/READY.json')
    assembly = read(ROOT / 'ASSEMBLY.json')
    require(ready['status'] == 'CPU_TESTED_NOT_LIVE'
        and ready['schema'] == 'R201_MAIN_TESTED_SOURCE_OVERLAY_V1', 'actual_Main_schema')
    for name, expected in ready['files'].items():
        if name == 'gpu/orch_r184_think_act_learn.py':
            expected = assembly['Main_adapter_only_delta']['driver_sha256']
        require(sha(SOURCE / name) == expected, 'frozen_Main_with_declared_transport_adapter:' + name)
    paths = [str(SOURCE / name) for name in ready['files'] if name.startswith('tests/')]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=os.pathsep.join(map(str, (ROOT / 'cpu_test_deps', SOURCE, SOURCE / 'tests'))),
        OMP_NUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    log_path = ROOT / ('CPU_PYTEST_' + str(time.time_ns()) + '.log')
    with log_path.open('x') as log:
        outcome = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'pytest_subtests',
            '-o', 'cache_dir=' + str(ROOT / 'pytest_cache'), *paths], cwd=SOURCE,
            env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    text = log_path.read_text()
    require(outcome.returncode == 0 and ' skipped' not in text, 'actual_receiving_tests_see_CPU_PYTEST.log')
    counts = re.findall(r'(\d+) passed', text)
    require(counts, 'actual_pytest_count')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    cpu = dict(passed=True, tests_run=int(counts[-1]), source_pins=pins, log_sha256=sha(log_path),
        observed_unix=time.time(), prior_failed_test_log_preserved=sha(ROOT / 'CPU.log'))
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    write(ROOT / 'SOURCE.json', dict(source_root=str(SOURCE), source_pins=pins,
        Main_READY_sha256=sha(ROOT / 'main_ready/READY.json'),
        capture_manifest_sha256=sha(ROOT / 'snapshot/MANIFEST.json')))
    print(json.dumps(dict(status='RECEIVING_TESTS_PASS_NOT_LAUNCHED', tests_run=cpu['tests_run'],
        observed_unix=cpu['observed_unix'], cpu_sha256=sha(ROOT / 'CPU.json'))))


def state():
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only')
    from gpu import orch_r125_continual_native as native
    from gpu.orch_r125_stream_journal import StreamJournal
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest
    import torch
    plan = read(ROOT / 'control/PLAN.json')
    logical = Path(plan['root'])
    physical = ROOT / 'life'
    require(logical != physical and os.path.samefile(logical, physical), 'private_clone_mount_required')
    original = read(ROOT / 'ORIGINAL_MOUNT_IDENTITY.json')
    metadata = logical.stat()
    require([metadata.st_dev, metadata.st_ino] != original['original_device_inode'], 'original_C2_not_mounted')
    complete = read(ROOT / 'snapshot/complete/SLEEP_COMPLETE.json')['document']
    context = read(ROOT / 'snapshot/console/CONTEXT_COMMITTED.json')['document']['state']
    require(context['state']['rows'] == complete['resume_state']['state']['rows'], 'no_console_training_rows')
    require(context['state']['history']['events'][:504] == complete['resume_state']['state']['history']['events'],
        'exact_history_prefix')
    with StreamJournal(logical / 'stream') as journal:
        checkpoint = journal.latest_checkpoint()
        require(checkpoint['document'] == context, 'exact_common_committed_context5846')
        before = len(list((physical / 'stream/records').glob('[0-9]' * 20 + '.json')))
        require(len(journal.read_inbox()) == 130, 'only_captured_registered_inbox')
        require(before == 5847 == len(list((physical / 'stream/records').glob('[0-9]' * 20 + '.json'))),
            'no_new_history_or_inbox_registration')
    restored = ContinualStream.restore(context, expected_sha256=context['sha256'])
    require(restored.checkpoint() == context and restored.pending is None, 'exact_console_state_roundtrip')
    model = read(logical / 'checkpoints/sleep_000051/COMMIT.json')
    native.NativeChild.verify_checkpoint(model)
    require(digest(model['checkpoint_sha256']) == restored.model_state_sha256, 'model_history_binding')
    payload = torch.load(model['optimizer_rng_path'], map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == model['optimizer_steps'] == 4908, 'optimizer4908_not_reset')
    parameters = [torch.nn.Parameter(torch.zeros_like(payload['optimizer']['state'][index]['exp_avg']))
        for index in range(len(payload['parameter_names']))]
    optimizer = torch.optim.AdamW(parameters)
    optimizer.load_state_dict(payload['optimizer'])
    current = optimizer.state_dict()
    require(current['param_groups'] == payload['optimizer']['param_groups'], 'exact_AdamW_groups')
    require(all(group['lr'] == 3e-5 for group in current['param_groups']), 'fixed_LR3e-5')
    for index, values in payload['optimizer']['state'].items():
        for name, expected in values.items():
            actual = current['state'][index][name]
            require(torch.equal(actual, expected) if torch.is_tensor(expected) else actual == expected,
                'exact_AdamW_tensor_or_step')
    random.setstate(payload['python_rng'])
    torch.set_rng_state(payload['cpu_rng'])
    require(random.getstate() == payload['python_rng'] and torch.equal(torch.get_rng_state(), payload['cpu_rng']),
        'exact_Python_and_CPU_RNG')
    require(len(payload['cuda_rng']) == 1 and payload['cuda_rng'][0].device.type == 'cpu'
        and payload['cuda_rng'][0].numel() > 0 and not torch.cuda.is_initialized(), 'saved_CUDA_RNG_no_GPU_context')
    receipt = dict(status='PASS', observed_unix=time.time(), optimizer_steps=4908,
        optimizer_restored_exact=True, console_masking_preserved=True, cuda_initialized=False,
        source_cycle=51, console_record=5846, full_context_sha256=context['sha256'],
        original_C2_not_mounted=True, private_storage_root=str(physical), inherited_logical_root=str(logical),
        original_device_inode=original['original_device_inode'], clone_device_inode=[metadata.st_dev, metadata.st_ino],
        learning_rate=3e-5, guided_cycles=3, withdrawn_cycles=3, success_required=False)
    write(ROOT / 'STATE_CPU.json', receipt)
    print(json.dumps(receipt))


def smoke():
    from gpu.orch_r125_cpu_experiment import digest, verify_gate, run_request
    from organism_v6.orch_r125_experiment_request import make_request
    config = read(ROOT / 'control/PLAN.json')['think_act_learn']
    require(digest(verify_gate(config['cpu_gate_root'])) == config['cpu_gate_sha256'], 'actual_same_boot_gate')
    code = 'import sympy\nprint(sympy.factor(sympy.Symbol("z")**2 - 1))\n'
    request = make_request(code, dict(kind='BUILDER_TEST', record_index=0,
        record_sha256=hashlib.sha256(b'R201_MATH_B_RECEIVING_SMOKE_NOT_CHILD_DATA').hexdigest()))
    result = run_request(json.dumps(request).encode(), ROOT / 'builder_smoke', config['cpu_gate_root'])
    require(result['status'] == 'COMPLETE' and result['returncode'] == 0
        and result['stdout'].strip() == '(z - 1)*(z + 1)' and result['cgroup_removed_after_stop'], 'actual_math_roundtrip')
    receipt = dict(status='PASS', observed_unix=time.time(), gate_root=config['cpu_gate_root'],
        gate_sha256=config['cpu_gate_sha256'], result=result, child_data=False, parent_data=False, publications=0)
    write(ROOT / 'TOOL_SMOKE.json', receipt)
    print(json.dumps(dict(status='REAL_BUILDER_TOOL_SMOKE_PASS', gate_sha256=config['cpu_gate_sha256'],
        publications=0, observed_unix=receipt['observed_unix'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('tests', 'state', 'smoke'))
    globals()[parser.parse_args().mode]()
