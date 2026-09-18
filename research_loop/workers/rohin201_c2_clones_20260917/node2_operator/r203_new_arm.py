"""Receive Main R203 and launch one assigned, unconsumed node2 clone."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tarfile
import time


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MATH_ROOT = Path('/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0234z')
ARCHIVE_SHA = 'ca6c1b006260c677bdbb003baf52333e354d7a9e0ec266ebdacac08992f89544'


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, sort_keys=True, indent=2)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')


def prepare():
    arm = read(ROOT / 'ARM.json')
    require(ROOT.name in ('creative_d1', 'math_transfer_c1') and not (ROOT / 'STARTED.json').exists(), 'only_new_assigned_clones')
    ready_root = ROOT.parent / 'r203_ready'
    ready = read(ready_root / 'READY.json')
    require(sha(ready_root / 'runtime_overlay.tar.gz') == ready['archive_sha256'] == ARCHIVE_SHA, 'Main_exact_released_R203')
    shutil.copytree(SOURCE, ROOT / 'source_pre_r203')
    with tarfile.open(ready_root / 'runtime_overlay.tar.gz') as archive:
        members = archive.getmembers()
        require(len(members) == len(ready['files']) == 37 and all(member.isfile() and member.name in ready['files'] for member in members), 'exact37_overlay_files')
        archive.extractall(SOURCE, filter='data')
    require(all(sha(SOURCE / name) == expected for name, expected in ready['files'].items()), 'exact_receiving_overlay_bytes')
    driver = SOURCE / 'gpu/orch_r184_think_act_learn.py'
    text = driver.read_text()
    functions = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef) and node.name == '_cpu']
    require(len(functions) == 1, 'single_Main_transport_seam')
    function = functions[0]
    original = ''.join(text.splitlines(keepends=True)[function.lineno - 1:function.end_lineno])
    replacement = '    def _cpu(self, origin):\n        if self.config["trial_id"] == ' + repr(arm['trial_id']) + ':\n'
    if arm['math_tool']:
        replacement += '            from gpu.r184_cpu_bridge import call\n            return call(self.config, origin)\n'
    else:
        replacement += '            return dict(status="PROSE_ENVIRONMENT_NO_CODE_EXECUTOR", executed=False, origin=origin)\n'
    replacement += ''.join(original.splitlines(keepends=True)[1:])
    driver.write_text(text.replace(original, replacement, 1))
    plan = read(ROOT / 'control/PLAN_PRE_R203.json')
    plan.update(ready['required_native_options'])
    plan['think_act_learn'].update(ready['required_driver_options'])
    require('console_reflection' not in plan['think_act_learn'] and 'structured_think_policy' not in plan['think_act_learn'], 'new_open_THINK_no_original_hold')
    write(ROOT / 'control/PLAN.json', plan)
    check()


def check():
    arm = read(ROOT / 'ARM.json')
    plan = read(ROOT / 'control/PLAN.json')
    ready_root = ROOT.parent / 'r203_ready'
    sys.path.insert(0, str(SOURCE))
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import ThinkActLearn
    from unittest.mock import patch
    validate_plan(plan)
    probe = object.__new__(ThinkActLearn)
    probe.config = plan['think_act_learn']
    if arm['math_tool']:
        with patch('gpu.r184_cpu_bridge.call', return_value=dict(status='SYNTHETIC_TRANSPORT_TEST', executed=False)) as call:
            require(probe._cpu(dict(synthetic=True))['status'] == 'SYNTHETIC_TRANSPORT_TEST', 'actual_math_transport_branch')
            require(call.call_count == 1, 'single_math_dispatch')
    else:
        require(probe._cpu(dict(synthetic=True))['status'] == 'PROSE_ENVIRONMENT_NO_CODE_EXECUTOR', 'honest_creative_no_execution')
    tests = ['tests/test_orch_r184_think_act_learn.py::ThinkActLearnTests::test_unknown_tool_outcome_is_kept_and_never_retried',
        'tests/test_orch_r125_continual_stream.py::StreamTests::test_threshold_compaction_precedes_generation_and_preserves_raw_input']
    test_environment = dict(environment(), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTHONPATH=os.pathsep.join((str(SOURCE), str(SOURCE / 'tests'), str(ROOT / 'test_support'))))
    with (ROOT / 'CPU_R203_checked.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests],
            cwd=SOURCE, env=test_environment, stdout=output, stderr=subprocess.STDOUT, timeout=90)
    require(result.returncode == 0, 'two_targeted_receiving_regressions')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    cpu = dict(passed=True, tests_run=3, source_pins=pins, observed_unix=time.time(),
        scope='one exact transport smoke plus two targeted regressions; Main broad suite reused, not rerun',
        Main_READY_sha256=sha(ready_root / 'READY.json'), Main_archive_sha256=ARCHIVE_SHA,
        log_sha256=sha(ROOT / 'CPU_R203_checked.log'), no_GPU_calls=True)
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    write(ROOT / 'SOURCE.json', dict(source_root=str(SOURCE), source_pins=pins, Main_READY_sha256=sha(ready_root / 'READY.json'),
        Main_archive_sha256=ARCHIVE_SHA, only_additional_driver_delta='Assigned true transport/no-executor branch', physical=arm['physical']))
    reference = ROOT.parent / 'parent_reference/ROHIN_C2_CONVERSATION_2026-09-17.md'
    require(sha(reference) == '3d0d9dc7fbdefc7ccc24c2625b56b05a6a8c07baea41e3753038813f86da541d', 'full_clean_parent_reference')
    if arm['math_tool']:
        followups = {'52': 'What do your actual modular or divisibility calculations support, and what remains a conjecture? Which small counterexample could change your mind?',
            '53': 'Which question would best test whether your pattern transfers beyond the examples? What will you check without further parent guidance during the next three cycles?'}
    else:
        followups = {'52': 'Which concrete choice in your draft changed the scene, voice or relationship? What small revision would make that change more legible without explaining everything?',
            '53': 'Which part of the draft now earns its effect through a concrete detail, and which still relies on a stock phrase? What will you try while parent guidance is withdrawn for the next three cycles?'}
    write(ROOT / 'PARENT_CONFIG.json', dict(reference_path=str(reference), reference_sha256=sha(reference),
        followups=followups, peer_active=False, qualitative_parent_receipt_requires_actual_read_not_fabricated=True))
    print(json.dumps(dict(status='R203_TARGETED_CPU_READY_NOT_LIVE', arm=arm['name'], cpu_sha256=sha(ROOT / 'CPU.json'),
        source_sha256=sha(ROOT / 'SOURCE.json'), plan_sha256=sha(ROOT / 'control/PLAN.json'))))


def launch():
    arm = read(ROOT / 'ARM.json')
    plan = read(ROOT / 'control/PLAN.json')
    cpu = read(ROOT / 'CPU.json')
    restore = read(ROOT / 'RESTORE_CPU.json')
    require(not (ROOT / 'STARTED.json').exists() and not (ROOT / 'FIRST_INPUTS.json').exists(), 'one_unconsumed_launch_only')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    require(cpu['passed'] and pins == cpu['source_pins'] and restore['optimizer_restored_exact']
        and restore['console_masking_preserved'] and not restore['cuda_initialized'], 'tested_exact_source_and_restore')
    require(plan['physical'] == arm['physical'] and plan['gpu_uuid'] == arm['gpu_uuid'], 'assigned_slot')
    require(plan['max_sleeps'] == 57 and plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and plan['anchor_lambda'] == 0.25, 'unchanged_six_cycle_recipe')
    control = ROOT / 'control'
    write(ROOT / 'BUILDER_ENTRY.json', dict(recorded_unix=time.time(), Main_logged_CPU_provenance=True,
        Main_READY_sha256=cpu['Main_READY_sha256'], receiving_cpu_sha256=sha(ROOT / 'CPU.json'), restore_sha256=sha(ROOT / 'RESTORE_CPU.json')))
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=arm['gpu_uuid'], physical=arm['physical'], builder_entry_logged=True,
        builder_entry_path=str(ROOT / 'BUILDER_ENTRY.json'), builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json'),
        cpu_receipt_path=str(ROOT / 'CPU.json'), cpu_receipt_sha256=sha(ROOT / 'CPU.json'), declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=True, copy_raw=str(ROOT / 'raw'),
        plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'), attempt_dir=str(control),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(), hard_end_unix=plan['hard_end_unix'],
        lease_path=str(ROOT / 'LEASE.json'), lease_sha256=sha(ROOT / 'LEASE.json'), next_reserved_unix=plan['lease_end_unix'],
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_guard as guard
    from gpu import orch_r127_pilot_console as console
    guard.validate(control / 'GUARD.json')
    processes = {}
    def start(name, command):
        with (ROOT / (name + '.log')).open('x') as output:
            process = subprocess.Popen(command, cwd=SOURCE, env=environment(), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        processes[name] = dict(pid=process.pid, start_ticks=Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19], started_unix=time.time())
    if arm['math_tool']:
        driver = plan['think_act_learn']
        write(ROOT / 'BRIDGE.json', dict(raw_root=str(ROOT / 'raw'), journal_id=read(ROOT / 'raw/stream/JOURNAL.json')['journal_id'],
            socket='/tmp/r203_node2_' + ROOT.name + '.sock', cpu_source=str(MATH_ROOT / 'source'), native_source=str(SOURCE),
            guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'), gate_root=driver['cpu_gate_root'],
            gate_sha256=driver['cpu_gate_sha256'], code_policy=driver['code_policy'], stop_unix=min(time.time() + 7200, plan['hard_end_unix'])))
        start('math_bridge', [PYTHON, '-B', str(ROOT / 'math_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')])
        until = time.time() + 15
        while time.time() < until and not list((ROOT / 'bridge_receipts').glob('READY_*.json')):
            time.sleep(0.1)
        require(list((ROOT / 'bridge_receipts').glob('READY_*.json')), 'actual_math_bridge_READY')
    first = ROOT / 'R202_PART_ONE.txt'
    require(sha(first) == '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30', 'exact_first_Rohin_input')
    introduction = ('I am Astra, the new parent for this ' + arm['name'] + ' copy. You inherit a fixed checkpoint and masked conversation cut, not later original-C2 conversation. '
        + arm['environment_facts'] + ' I have the full clean human/C2 reference as parent background; I will not paste later exchanges or the creative-test passage to you. '
        'This initial screen has three guided completed cycles followed by three cycles with no further parent input. There is no peer exchange in this screen. ')
    introduction += ('Which modular or divisibility question would you like to investigate, what small cases could challenge a conjecture, and what actual sandbox output would you expect?' if arm['math_tool']
        else 'What scene, voice or relationship would you like to make concrete? Choose your own subject and make an actual draft; I will offer light questions and qualitative feedback rather than a supplied story or a score.')
    publications = []
    with console._open_stream_directory(ROOT / 'raw', 'inbox') as (directory, path):
        for identifier, speaker, text in [('r202_000_rohin_part_one', 'Rohin', first.read_text()), ('r202_001_astra_' + ROOT.name, 'Astra', introduction)]:
            publication = console._publish(directory, path, dict(schema=console.SCHEMA, id=identifier, text=text,
                split='TRAIN', actor='parent', speaker=speaker, source_receipt=None))
            publications.append(dict(publication, speaker=speaker, text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    write(ROOT / 'FIRST_INPUTS.json', dict(published_unix=time.time(), publications=publications,
        creative_test_passage_copied=False, full_parent_reference_pasted=False, peer_exchange_active=False))
    start('parent', [PYTHON, '-B', str(ROOT / 'clone_parent.py')])
    start('supervisor', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')])
    started = dict(status='WRAPPERS_STARTED_NOT_LOADED_PROOF', observed_unix=time.time(), physical=arm['physical'],
        gpu_uuid=arm['gpu_uuid'], processes=processes, guard_sha256=sha(control / 'GUARD.json'),
        Main_archive_sha256=ARCHIVE_SHA, original_C2_signals=0, retirements=0, peer_active=False)
    write(ROOT / 'STARTED.json', started)
    print(json.dumps(started))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'check', 'launch'))
    globals()[parser.parse_args().mode]()
