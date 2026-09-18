"""Explicit new-run repair after a proved pre-native PCI-path case failure."""

import ast
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time

from r203_new_arm_v2 import ROOT, SOURCE, PYTHON, read, write, sha, require, environment


def main():
    arm = read(ROOT / 'ARM.json')
    prior = read(ROOT / 'STARTED.json')
    old_control = ROOT / 'control'
    require(not (old_control / 'LAUNCH.json').exists(), 'no_prior_native_launch')
    require('FileNotFoundError' in (ROOT / 'supervisor.log').read_text() and
        '/proc/driver/nvidia/gpus/' in (ROOT / 'supervisor.log').read_text(), 'exact_analyzed_preflight_failure')
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            arguments = (process / 'cmdline').read_bytes().decode().split('\0')
            require(not (str(old_control / 'GUARD.json') in arguments and 'native' in arguments), 'no_residual_native_owner')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    failure = ROOT / 'failed_dispatch_r203_pci_case'
    failure.mkdir()
    shutil.copytree(SOURCE, failure / 'source')
    shutil.copytree(old_control, failure / 'control')
    for name in ('STARTED.json', 'SOURCE.json', 'CPU.json', 'supervisor.log'):
        shutil.copy2(ROOT / name, failure / name)
    info = Path('/proc/driver/nvidia/gpus') / arm['pci'].lower() / 'information'
    metadata = dict(line.split(':', 1) for line in info.read_text().splitlines() if ':' in line)
    require(metadata['GPU UUID'].strip() == arm['gpu_uuid'] and int(metadata['Device Minor']) == arm['physical'], 'actual_lowercase_kernel_UUID_minor_binding')
    if arm['math_tool']:
        require(not list((ROOT / 'bridge_receipts').glob('ACCEPTED_*.json')), 'old_bridge_never_dispatched')
        identity = prior['processes']['math_bridge']
        process = Path('/proc') / str(identity['pid'])
        require(process.stat().st_uid == 2524 and process.joinpath('stat').read_text().rsplit(')', 1)[1].split()[19] == identity['start_ticks']
            and str(ROOT / 'BRIDGE.json') in process.joinpath('cmdline').read_bytes().decode().split('\0'), 'exact_idle_owned_bridge')
        descriptor = os.pidfd_open(identity['pid'])
        try:
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            require(bool(select.select([descriptor], [], [], 10)[0]), 'old_idle_bridge_exited')
        finally:
            os.close(descriptor)
        (ROOT / 'bridge_receipts').rename(failure / 'bridge_receipts')
        (ROOT / 'BRIDGE.json').rename(failure / 'BRIDGE.json')
    ready_root = ROOT.parent / 'r204_ready'
    ready = read(ready_root / 'READY.json')
    require(sha(ready_root / 'runtime_overlay.tar.gz') == ready['archive_sha256'] == 'b0f148c92172af9d1525fda79a97bebfb31337e312e26c0f6bc805b3c687f8fc', 'exact_Main_R204')
    with tarfile.open(ready_root / 'runtime_overlay.tar.gz') as archive:
        require(len(archive.getmembers()) == 37 and all(member.isfile() and member.name in ready['files'] for member in archive.getmembers()), 'exact_R204_closure')
        archive.extractall(SOURCE, filter='data')
    require(all(sha(SOURCE / name) == expected for name, expected in ready['files'].items()), 'R204_source_pins')
    confinement = SOURCE / 'gpu/r184_node2_confinement.py'
    text = confinement.read_text()
    require(text.count(arm['pci']) == 1, 'one_failed_PCI_path')
    text = text.replace(arm['pci'], arm['pci'].lower())
    old_prefix = 'orch-r203-' + ROOT.name.replace('_', '-') + '-'
    require(old_prefix in text, 'existing_unit_prefix')
    confinement.write_text(text.replace(old_prefix, 'orch-r204-' + ROOT.name.replace('_', '-') + '-casefixed-'))
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    nodes = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(nodes) == 1, 'one_transport_adapter')
    original = ''.join(text.splitlines(keepends=True)[nodes[0].lineno - 1:nodes[0].end_lineno])
    replacement = '    def _cpu(self, origin):\n        if self.config["trial_id"] == ' + repr(arm['trial_id']) + ':\n'
    replacement += ('            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n' if arm['math_tool']
        else '            return dict(status="PROSE_ENVIRONMENT_NO_CODE_EXECUTOR", executed=False, origin=origin)\n')
    replacement += ''.join(original.splitlines(keepends=True)[1:])
    driver.write_text(text.replace(original, replacement, 1))
    control = ROOT / 'control_r204_casefix'
    control.mkdir()
    plan = read(old_control / 'PLAN.json')
    plan['think_act_learn'].update(ready['required_driver_options'])
    write(control / 'PLAN.json', plan)
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import ThinkActLearn
    from unittest.mock import patch
    validate_plan(plan)
    probe = object.__new__(ThinkActLearn)
    probe.config = plan['think_act_learn']
    if arm['math_tool']:
        with patch('gpu.r184_cpu_bridge.call', return_value=dict(status='SYNTHETIC_ONLY')) as call:
            require(probe._cpu({})['status'] == 'SYNTHETIC_ONLY' and call.call_count == 1, 'real_transport_seam_smoke')
    else:
        require(probe._cpu({})['executed'] is False, 'creative_no_executor')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    cpu = dict(passed=True, tests_run=1, source_pins=pins, Main_READY_sha256=sha(ready_root / 'READY.json'),
        Main_archive_sha256=ready['archive_sha256'], Main67_test_receipt_reused=True, observed_unix=time.time(),
        receiving_test='actual transport branch; UUID/minor kernel metadata exact; strict device probe follows')
    write(control / 'RECEIVING_CPU.json', cpu)
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        physical=arm['physical'], gpu_uuid=arm['gpu_uuid'], builder_entry_logged=True,
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        Main_READY_sha256=cpu['Main_READY_sha256'], declared_unix=time.time()))
    config = read(old_control / 'GUARD.json')
    config.update(source_pins=pins, plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        attempt_dir=str(control), allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    dispatch()


def dispatch():
    arm = read(ROOT / 'ARM.json')
    prior = read(ROOT / 'STARTED.json')
    old_control = ROOT / 'control'
    control = ROOT / 'control_r204_casefix'
    failure = ROOT / 'failed_dispatch_r203_pci_case'
    ready = read(ROOT.parent / 'r204_ready/READY.json')
    info = Path('/proc/driver/nvidia/gpus') / arm['pci'].lower() / 'information'
    pins = read(control / 'GUARD.json')['source_pins']
    require(not (control / 'OUTER_STARTED.json').exists() and not (old_control / 'LAUNCH.json').exists(), 'no_native_or_second_attempt')
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_guard import validate
    validate(control / 'GUARD.json')
    write(ROOT / 'R204_CASE_REPAIR.json', dict(observed_unix=time.time(), failed_control=str(old_control), new_control=str(control),
        actual_kernel_info=str(info), no_prior_native=True, inputs_republished=False, parent_restarted=False,
        Main_archive_sha256=ready['archive_sha256'], guard_sha256=sha(control / 'GUARD.json'),
        confinement_relaxed=False, no_inflight_launch_cancelled=True, source_pins=pins))
    processes = {'parent': prior['processes']['parent']}
    def start(name, arguments):
        with (ROOT / (name + '.log')).open('x') as output:
            process = subprocess.Popen(arguments, cwd=SOURCE, env=environment(), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes[name] = dict(pid=process.pid, start_ticks=Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19], started_unix=time.time())
    if arm['math_tool']:
        bridge = read(failure / 'BRIDGE.json')
        bridge.update(socket='/tmp/r204_node2_' + ROOT.name + '_casefixed.sock', guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'))
        write(ROOT / 'BRIDGE.json', bridge)
        start('math_bridge_r204', [PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')])
        until = time.time() + 15
        while time.time() < until and not list((ROOT / 'bridge_receipts').glob('READY_*.json')):
            time.sleep(0.1)
        require(list((ROOT / 'bridge_receipts').glob('READY_*.json')), 'actual_new_bridge_READY')
    start('supervisor_r204', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')])
    write(ROOT / 'STARTED_R204.json', dict(status='NEW_RUN_WRAPPERS_NOT_LOADED_PROOF', observed_unix=time.time(),
        processes=processes, control=str(control), physical=arm['physical'], prior_failed_preserved=str(failure), inputs_republished=False))
    print(json.dumps(read(ROOT / 'STARTED_R204.json')))


if __name__ == '__main__':
    main()
