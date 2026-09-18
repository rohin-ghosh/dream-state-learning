"""One-shot REPO-C launch through the existing strict node2 admission path."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from prepare_repo_c import ROOT, SOURCE, SNAPSHOT, DEVICE, PYTHON, read, write, sha, require


INTRODUCTION = (
    'I am Astra, the new parent for this REPO-C copy. You inherited the same fixed C2 checkpoint and masked '
    'conversation cut as the other new copies, not the continuing original conversation. Your present environment '
    'has an actual read-only repository snapshot and a private note/proposal workspace. In ACT you can request '
    'repo_list . or repo_read relative/path.py 0, or use the documented repo_action commands. Choose one action. '
    'There is no code/test execution, shell, network, merge, or live learner modification here. A proposed patch '
    'is not applied, and a claim about a test is not a test result. Inspect the actual tool content and receipt. '
    'I have the clean human/C2 reference as parent background; I will not paste its later conversation or creative '
    'test into your context. You will receive sparse guidance for three completed cycles, then no parent guidance '
    'for three cycles. What do you want to understand about this repository, and what small real inspection could '
    'change your next action? Treat my suggestions as context, not evidence. A later explicitly labeled peer '
    'connection with a mathematical copy is a different-environment treatment, not a matched comparison; it is '
    'not active just because I mention it.'
)


def environment():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')


def main():
    require(ROOT.name == 'repo_c1', 'owned_REPO_C_only')
    sys.path.insert(0, str(SOURCE))
    from gpu import orch_r125_continual_guard as guard
    from gpu import orch_r127_pilot_console as console
    part_one = ROOT / 'R202_PART_ONE.txt'
    expected = '48921afaf6c1a7dec7fbe7cbb79c3be8c52bd9612cbcdad3ff6da64fc7469e30'
    require(sha(part_one) == expected, 'exact_authorized_Rohin_PART_ONE')
    plan = read(ROOT / 'control/PLAN.json')
    cpu = read(ROOT / 'CPU.json')
    restore = read(ROOT / 'RESTORE_CPU.json')
    builder = read(ROOT / 'BUILDER_ENTRY.json')
    parent = read(ROOT / 'PARENT_CONFIG.json')
    require(sha(parent['reference_path']) == parent['reference_sha256'], 'full_clean_parent_reference')
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    require(cpu['passed'] and cpu['tests_run'] == 471 and cpu['source_pins'] == pins, 'tested_repo_tool_render_source')
    require(read(ROOT / 'TOOL_RENDER_RECEIVING.json')['actual_tool_content_and_receipt_visible'], 'repository_result_rendering_repaired')
    require(restore['status'] == 'PASS' and restore['optimizer_restored_exact'] and restore['console_masking_preserved'], 'exact_CPU_restore')
    require(builder['cpu_sha256'] == sha(ROOT / 'CPU.json') and builder['restore_sha256'] == sha(ROOT / 'RESTORE_CPU.json'), 'dated_Builder_evidence')
    require(plan['physical'] == 3 and plan['gpu_uuid'] == DEVICE and plan['max_sleeps'] == 57, 'assigned_free_slot_and_six_cycles')
    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 0
        and plan['anchor_lambda'] == 0.25 and plan.get('plasticity') is None, 'unchanged_fixed_recipe')
    require(not (ROOT / 'STARTED.json').exists() and not (ROOT / 'FIRST_INPUTS.json').exists(), 'once_only_unconsumed_clone')
    write(ROOT / 'LAUNCH_ATTEMPT.json', dict(started_unix=time.time(), no_implicit_retry=True,
        part_one_sha256=expected, builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json')))
    control = ROOT / 'control'
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=DEVICE, physical=3, builder_entry_logged=True, builder_entry_path=str(ROOT / 'BUILDER_ENTRY.json'),
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
        socket='/tmp/r202_node2_repo_c1.sock', native_source=str(SOURCE), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), repo_config=str(ROOT / 'TOOLS.json'),
        repo_config_sha256=sha(ROOT / 'TOOLS.json'), stop_unix=min(time.time() + 7200, plan['hard_end_unix']))
    write(ROOT / 'BRIDGE.json', bridge)
    write(ROOT / 'READY.json', dict(status='RECEIVING_CPU_READY_NOT_LOADED_PROOF', cpu_sha256=sha(ROOT / 'CPU.json'),
        restore_sha256=sha(ROOT / 'RESTORE_CPU.json'), plan_sha256=sha(control / 'PLAN.json'),
        guard_sha256=sha(control / 'GUARD.json'), source_manifest_sha256=sha(ROOT / 'SOURCE.json'),
        checkpoint_cycle=51, optimizer_steps=4908, console_record=5846, part_one_sha256=expected,
        parent_reference_sha256=parent['reference_sha256'], guided_cycles=[52, 53, 54], withdrawn_cycles=[55, 56, 57],
        peer_exchange_active=False, think_style='open', child_code_execution=False))
    processes = {}
    def start(name, arguments):
        with (ROOT / (name + '.log')).open('x') as output:
            process = subprocess.Popen(arguments, cwd=SOURCE, env=environment(), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        processes[name] = dict(pid=process.pid, start_ticks=ticks, started_unix=time.time())
    start('repo_bridge', [PYTHON, '-B', str(ROOT / 'repo_c_bridge.py'), '--config', str(ROOT / 'BRIDGE.json')])
    until = time.time() + 15
    while time.time() < until and not list((ROOT / 'bridge_receipts').glob('READY_*.json')):
        time.sleep(0.1)
    require(list((ROOT / 'bridge_receipts').glob('READY_*.json')), 'actual_repo_bridge_READY')
    publications = []
    with console._open_stream_directory(ROOT / 'raw', 'inbox') as (directory, path):
        for identifier, speaker, content in [('r202_000_rohin_part_one', 'Rohin', part_one.read_text()),
            ('r202_001_astra_repo_c_introduction', 'Astra', INTRODUCTION)]:
            document = dict(schema=console.SCHEMA, id=identifier, text=content, split='TRAIN', actor='parent',
                speaker=speaker, source_receipt=None)
            publications.append(dict(console._publish(directory, path, document), speaker=speaker,
                text_sha256=hashlib.sha256(content.encode()).hexdigest(), published_unix=time.time()))
    write(ROOT / 'FIRST_INPUTS.json', dict(published_unix=time.time(), publications=publications,
        ordering='Rohin PART ONE before new Astra REPO-C introduction', exact_part_one_sha256=expected,
        creative_test_passage_copied=False, full_parent_reference_pasted=False, original_C2_writes=0))
    start('parent', [PYTHON, '-B', str(ROOT / 'clone_parent.py')])
    start('supervisor', [PYTHON, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')])
    started = dict(status='WRAPPERS_STARTED_NOT_LOADED_PROOF', observed_unix=time.time(), physical=3,
        gpu_uuid=DEVICE, processes=processes, guard_sha256=sha(control / 'GUARD.json'),
        source_manifest_sha256=sha(SNAPSHOT / 'MANIFEST.json'), input_publications=publications,
        original_C2_signals=0, retirements=0)
    write(ROOT / 'STARTED.json', started)
    print(json.dumps(started))


if __name__ == '__main__':
    main()
