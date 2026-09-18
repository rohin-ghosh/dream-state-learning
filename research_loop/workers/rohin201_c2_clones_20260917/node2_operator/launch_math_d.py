"""Use the tested R186 once-only strict launcher for the prepared MATH-D clone."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from receive_math_d import ROOT, SOURCE, SNAPSHOT, MAIN, MATH_ROOT, DEVICE, PYTHON, read, write, sha, require, environment


INTRODUCTION = (
    'I am Astra, the new parent for this MATH-D copy. You inherited the fixed C2 checkpoint and a masked conversation cut, '
    'not the continuing original C2 conversation. Your present environment supports your own mathematical investigation, '
    'worked prose, and a confined Python tool with read-only SymPy 1.14.0 and mpmath 1.3.0; it has no network, GPU, home '
    'access, or Torch. A package being installed is not a successful calculation: use the actual receipt. '
    'I will offer sparse questions for your first three completed cycles, then withdraw guidance for the next three. '
    'What question is worth pursuing now, and what observation would tell you whether to persist or change direction? '
    'You choose the attempt; my suggestions are context, not evidence or learning targets.'
)


def main(part_one, expected_sha):
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_guard as guard
    from gpu import orch_r127_pilot_console as console
    require(sha(part_one) == expected_sha, 'exact_Main_Rohin_PART_ONE_file')
    text = part_one.read_text()
    require(text and len(text.encode()) < 16384, 'bounded_exact_first_input')
    plan = read(ROOT / 'control/PLAN.json')
    cpu = read(ROOT / 'CPU.json')
    restore = read(ROOT / 'RESTORE_CPU.json')
    builder = read(ROOT / 'BUILDER_ENTRY.json')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    require(cpu['passed'] and cpu['tests_run'] == 400 and pins == cpu['source_pins'], 'tested_receiving_source')
    require(restore['status'] == 'PASS' and restore['optimizer_restored_exact'] and restore['console_masking_preserved'], 'actual_restore_receipt')
    require(builder['cpu_sha256'] == sha(ROOT / 'CPU.json') and builder['restore_sha256'] == sha(ROOT / 'RESTORE_CPU.json'), 'dated_Builder_evidence')
    require(plan['physical'] == 1 and plan['gpu_uuid'] == DEVICE and plan['max_sleeps'] == 57,
        'fixed_slot_and_six_cycles')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and plan['anchor_lambda'] == 0.25 and plan.get('plasticity') is None, 'fixed_recipe')
    require(not (ROOT / 'STARTED.json').exists(), 'one_new_clone_only')
    write(ROOT / 'LAUNCH_ATTEMPT.json', dict(started_unix=time.time(), no_implicit_retry=True,
        part_one_sha256=expected_sha, builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json')))
    control = ROOT / 'control'
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=DEVICE, physical=1, builder_entry_logged=True, builder_entry_path=str(ROOT / 'BUILDER_ENTRY.json'),
        builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json'), cpu_receipt_path=str(ROOT / 'CPU.json'),
        cpu_receipt_sha256=sha(ROOT / 'CPU.json'), declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=pins, resume=True,
        copy_raw=str(ROOT / 'raw'), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        attempt_dir=str(control), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        hard_end_unix=plan['hard_end_unix'], lease_path=str(ROOT / 'LEASE.json'), lease_sha256=sha(ROOT / 'LEASE.json'),
        next_reserved_unix=plan['lease_end_unix'], allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    guard.validate(control / 'GUARD.json')
    bridge = dict(raw_root=str(ROOT / 'raw'), journal_id=read(ROOT / 'raw/stream/JOURNAL.json')['journal_id'],
        socket='/tmp/r201_node2_math_d1.sock', cpu_source=str(MATH_ROOT / 'source'),
        native_source=str(SOURCE), guard_path=str(control / 'GUARD.json'), guard_sha256=sha(control / 'GUARD.json'),
        gate_root=plan['think_act_learn']['cpu_gate_root'], gate_sha256=plan['think_act_learn']['cpu_gate_sha256'],
        code_policy=plan['think_act_learn']['code_policy'], stop_unix=min(time.time() + 7200, plan['hard_end_unix']))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'READY.json', dict(status='RECEIVING_CPU_READY_NOT_YET_LIVE', cpu_sha256=sha(ROOT / 'CPU.json'),
        restore_sha256=sha(ROOT / 'RESTORE_CPU.json'), plan_sha256=sha(control / 'PLAN.json'),
        guard_sha256=sha(control / 'GUARD.json'), source_manifest_sha256=sha(ROOT / 'SOURCE.json'),
        checkpoint_cycle=51, optimizer_steps=4908, console_record=5846, new_input='Rohin PART ONE only, then Astra introduction',
        parent_sha256=sha(ROOT / 'parent_math_d.py'), part_one_sha256=expected_sha,
        guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57], peer_exchange_active=False,
        comparison='R202-updated birth; proposed MATH-D/REPO-C peer treatment is not the original matched contrast'))
    dispatch(text, expected_sha)


def dispatch(text, expected_sha, bridge_name='cpu_bridge', existing_bridge=None):
    from gpu import orch_r127_pilot_console as console
    control = ROOT / 'control'
    processes = {}
    def start(name, arguments):
        with (ROOT / (name + '.log')).open('x') as output:
            process = subprocess.Popen(arguments, cwd=SOURCE, env=environment(), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        processes[name] = dict(pid=process.pid, start_ticks=ticks, started_unix=time.time())
        return process
    if existing_bridge is None:
        start(bridge_name, [PYTHON, '-B', str(ROOT / 'math_d_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')])
    else:
        processes[bridge_name] = existing_bridge
    until = time.time() + 15
    while time.time() < until and not list((ROOT / 'bridge_receipts').glob('READY_*.json')):
        time.sleep(0.1)
    require(list((ROOT / 'bridge_receipts').glob('READY_*.json')), 'actual_bridge_READY_before_native')
    publications = []
    with console._open_stream_directory(ROOT / 'raw', 'inbox') as (directory, path):
        for identifier, speaker, content in [('r202_000_rohin_part_one', 'Rohin', text),
                                             ('r202_001_astra_math_d_introduction', 'Astra', INTRODUCTION)]:
            document = dict(schema=console.SCHEMA, id=identifier, text=content, split='TRAIN', actor='parent',
                speaker=speaker, source_receipt=None)
            publications.append(dict(console._publish(directory, path, document), speaker=speaker,
                text_sha256=hashlib.sha256(content.encode()).hexdigest(), published_unix=time.time()))
    write(ROOT / 'FIRST_INPUTS.json', dict(published_unix=time.time(), publications=publications,
        ordering='Explicit new IDs sort Rohin PART ONE before Astra introduction',
        exact_part_one_sha256=expected_sha, creative_test_passage_copied=False, original_C2_writes=0))
    start('parent', [PYTHON, '-B', str(ROOT / 'parent_math_d.py')])
    start('supervisor', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')])
    started = dict(status='WRAPPERS_STARTED_NOT_LOADED_PROOF', observed_unix=time.time(), physical=1,
        gpu_uuid=DEVICE, processes=processes, guard_sha256=sha(control / 'GUARD.json'),
        snapshot_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json'), main_READY_sha256=sha(MAIN / 'READY.json'),
        input_publications=publications, original_C2_signals=0, retirements=0)
    write(ROOT / 'STARTED.json', started)
    print(json.dumps(started))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--part-one', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    arguments = parser.parse_args()
    main(arguments.part_one, arguments.sha256)
