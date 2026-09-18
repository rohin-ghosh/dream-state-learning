"""Adapt the tested R186 receiver to the exact R201 MATH-D snapshot."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
SNAPSHOT = ROOT.parent / 'snapshot'
MAIN = ROOT.parent / 'main_ready'
BASE_PACKET = Path('/localhome/local-rohing/orch_r153_r184_staging_20260917/orch_r184_C2_sleep41_1789684294308387719')
DEVICE = 'GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MATH_ROOT = Path('/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0234z')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, document):
    with Path(path).open('x') as output:
        json.dump(document, output, sort_keys=True, indent=2)


def environment(source=SOURCE):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')


def prepare():
    require(str(ROOT) == '/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1/math_d1', 'new_clone_only')
    write(ROOT / 'PREPARE_ATTEMPT.json', dict(started_unix=time.time(), no_implicit_retry=True))
    require(sha(SNAPSHOT / 'MANIFEST.json') == '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84', 'exact_manifest')
    require(sha(MAIN / 'runtime_overlay.tar.gz') == '599f44f1a39bc0a312a180963feef8affc62748cec20721a79112bfc5a0540b1', 'Main_READY_archive')
    manifest = read(SNAPSHOT / 'MANIFEST.json')
    require(sha(BASE_PACKET / 'PRESERVATION_RECEIPT.json') == 'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e', 'retained_prefix_provenance')
    require(read(BASE_PACKET / 'stream/records/00000000000000005128.json')['sha256'] == 'adcbefb57e9598fe75dfadd294dec0ef6aa1530faefbc4574b8b47c7cd834cc9', 'prefix_terminal')
    require(shutil.disk_usage(ROOT).free > 12 * 1024**3, 'copy_disk_budget')
    raw = ROOT / 'raw'
    raw.mkdir(mode=0o700)
    (raw / 'stream').mkdir(mode=0o700)
    shutil.copy2(BASE_PACKET / 'stream/JOURNAL.json', raw / 'stream/JOURNAL.json')
    shutil.copytree(BASE_PACKET / 'stream/records', raw / 'stream/records')
    require(len(list((raw / 'stream/records').glob('*.json'))) == 2 * 5129, 'complete_prior_prefix_only')
    require(sha(ROOT / 'FIXED_PREFIX_SUFFIX.tar.gz') == '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0', 'exact_suffix')
    with tarfile.open(ROOT / 'FIXED_PREFIX_SUFFIX.tar.gz') as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            require(member.isfile() and len(path.parts) == 2 and path.parts[0] in ('records', 'inbox'), 'safe_suffix_member')
            require(not (raw / 'stream' / path).exists(), 'no_prefix_overwrite')
        archive.extractall(raw / 'stream', filter='data')
    (raw / 'stream/WRITER.lock').touch(exist_ok=False)
    registrations = {}
    previous = hashlib.sha256(json.dumps(read(raw / 'stream/JOURNAL.json'), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for index in range(5847):
        record = read(raw / 'stream/records' / f'{index:020d}.json')
        expected = hashlib.sha256(json.dumps({key: value for key, value in record.items() if key != 'sha256'}, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        require(record['previous_sha256'] == previous and record['sha256'] == expected, 'full_immutable_prefix_hash_chain')
        previous = record['sha256']
        if record['kind'] == 'INBOX':
            item = record['document']
            registrations[Path(item['source_id']).name] = item['source_sha256']
    require(previous == manifest['console_record']['sha256'], 'exact_shared_console_cut')
    extra = ROOT / 'captured_unregistered_inbox_not_replayed'
    extra.mkdir(mode=0o700)
    for path in (raw / 'stream/inbox').iterdir():
        if path.name not in registrations:
            path.rename(extra / path.name)
    require({path.name: sha(path) for path in (raw / 'stream/inbox').iterdir()} == registrations, 'registered_history_only_no_future_messages')
    checkpoint = raw / 'checkpoints/sleep_000051'
    shutil.copytree(SNAPSHOT / 'complete', checkpoint)
    source_plan = read(SNAPSHOT / 'source_binding/PLAN.json')
    (SOURCE / 'context').mkdir(exist_ok=True)
    startup = source_plan['birth_prompt'].encode()
    require(hashlib.sha256(startup).hexdigest() == source_plan['startup_context']['sha256'], 'source_exact_startup_bytes')
    (SOURCE / 'context/R153_STARTUP.md').write_bytes(startup)
    confinement = SOURCE / 'gpu/r184_node2_confinement.py'
    text = confinement.read_text()
    substitutions = {'GPU-c9450d3d-0455-f034-b9bf-7f8956e44733': DEVICE,
        'MINOR=3': 'MINOR=1', '/dev/nvidia3': '/dev/nvidia1', '0000:57:00.0': '0000:52:00.0',
        '[0, 1, 2, 4, 5, 6, 7]': '[0, 2, 3, 4, 5, 6, 7]',
        "'orch-r184-c2-explicit-'": "'orch-r201-math-d1-'"}
    for before, after in substitutions.items():
        require(before in text, 'tested_confinement_token:' + before)
        text = text.replace(before, after)
    confinement.write_text(text)
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    nodes = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(nodes) == 1, 'one_Main_transport_adapter')
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    original = ''.join(lines[node.lineno - 1:node.end_lineno])
    require('EXISTING_LIFE_CPU_POLICY' in original and 'code_policy' in original, 'Main_NFKC_adapter')
    replacement = "    def _cpu(self, origin):\n        if self.config['trial_id'] == 'R201_MATH_D_node2_clone1':\n            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n"
    replacement += ''.join(original.splitlines(keepends=True)[1:])
    text = text.replace(original, replacement, 1)
    driver.write_text(text)
    shutil.copy2(ROOT / 'math_d_bridge.py', SOURCE / 'gpu/r184_cpu_bridge.py')
    write(ROOT / 'ASSEMBLY.json', dict(terminal_sha256=previous, registered_inbox=len(registrations),
        unused_inbox_not_replayed=len(list(extra.iterdir())), baseline_records=5129, total_records=5847,
        console_record=5846, complete_cycle=51, optimizer_steps=4908,
        Main_adapter_only_delta=dict(original_cpu_method=original, driver_sha256=sha(driver)),
        protected_original_source_writes=0, launches=0))
    print(json.dumps(dict(status='ASSEMBLED_EXACT_PREFIX_NOT_LAUNCHED', records=5847, registrations=len(registrations))))


def math_prepare():
    specification = importlib.util.spec_from_file_location('math_environment', ROOT / 'c2_math_environment.py')
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    helper.ORIGINAL_SOURCE = SOURCE
    helper.prepare(MATH_ROOT)


def math_test():
    specification = importlib.util.spec_from_file_location('math_environment', ROOT / 'c2_math_environment.py')
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    helper.ORIGINAL_SOURCE = SOURCE
    helper.test_candidate(MATH_ROOT)


def configure():
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan
    ready = read(MAIN / 'READY.json')
    math = read(MATH_ROOT / 'RESULT.json')
    require(math['status'] == 'PASS_NOT_DEPLOYED', 'tested_actual_math_environment')
    source_plan = read(SNAPSHOT / 'source_binding/PLAN.json')
    plan = deepcopy(source_plan)
    plan.update(source_root=str(SOURCE), physical=1, gpu_uuid=DEVICE, max_sleeps=57)
    plan.update(ready['required_native_options'])
    plan['startup_context']['path'] = str(SOURCE / 'context/R153_STARTUP.md')
    plan['think_act_learn'] = dict(ready['required_driver_options'], trial_id='R201_MATH_D_node2_clone1',
        cpu_gate_root=math['gate_root'], cpu_gate_sha256=math['gate_sha256'],
        environment_facts=source_plan['think_act_learn']['environment_facts'])
    require('console_reflection' not in plan['think_act_learn'] and plan.get('plasticity') is None, 'new_clone_no_hold_no_LR_change')
    validate_plan(plan)
    require(Path(plan['model_dir']).is_dir() and Path(plan['anchors']).is_dir(), 'local_base_and_unchanged_anchors_exist')
    control = ROOT / 'control'
    control.mkdir()
    write(control / 'PLAN.json', plan)
    original = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
    require(sha(original) == '621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3', 'existing_node2_lease')
    require(plan['hard_end_unix'] <= read(original)['hard_deadline_unix'], 'unchanged_wall_within_lease')
    write(ROOT / 'LEASE.json', dict(hard_end_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'],
        existing_node2_original=str(original), existing_node2_original_sha256=sha(original), machine_lease_changed=False))
    modules = ['tests.' + Path(name).stem for name in ready['files'] if name.startswith('tests/')]
    with (ROOT / 'CPU.log').open('x') as log:
        result = subprocess.run([PYTHON, '-B', '-m', 'unittest', *modules, '-q'], cwd=SOURCE,
            env=environment(), stdout=log, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_CPU_tests_see_CPU.log')
    text = (ROOT / 'CPU.log').read_text()
    count = re.findall(r'Ran (\d+) tests?', text)
    require(len(count) == 1 and 'skipped' not in text, 'all_receiving_tests_no_skips')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    write(ROOT / 'SOURCE.json', dict(source_root=str(SOURCE), source_pins=pins,
        Main_READY_sha256=sha(MAIN / 'READY.json'), capture_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json')))
    cpu = dict(passed=True, tests_run=int(count[0]), source_pins=pins, log_sha256=sha(ROOT / 'CPU.log'),
        math_result_sha256=sha(MATH_ROOT / 'RESULT.json'), observed_unix=time.time())
    write(ROOT / 'CPU.json', cpu)
    write(control / 'RECEIVING_CPU.json', cpu)
    print(json.dumps(dict(status='CONFIGURED_TESTS_PASS_NOT_LAUNCHED', tests_run=int(count[0]), gate_root=math['gate_root'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'math_prepare', 'math_test', 'configure'))
    arguments = parser.parse_args()
    globals()[arguments.mode]()
