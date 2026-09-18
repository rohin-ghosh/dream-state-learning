"""One-shot receiving assembly/CPU gate, then separately logged strict dispatch."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
sys.path.insert(0, str(SOURCE))
from research_loop.workers.rohin183_repo_learning_20260917.r186_copy import (
    ARMS, BASE_ROOT, BASE_PLAN_SHA, BASE_SOURCE_SHA, GATE_ROOT, GATE_SHA,
    PACKET_SHA, REMOTE_ROOT, TEST_MODULES, make_plan,
)
from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import require


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, sort_keys=True)


def pins():
    actual = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    declared = json.loads((ROOT / 'SOURCE.json').read_bytes())
    require(actual == declared['source_pins'], 'exact_assembled_source')
    require(all(actual[name] == expected for name, expected in declared['protected_pins'].items()),
        'frozen_noncanonical_runtime_closure')
    return actual


def prepare(label):
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from gpu.orch_r125_continual_native import validate_plan
    require(ROOT == Path(REMOTE_ROOT) / (label + '3'), 'exact_new_copy_root')
    write(ROOT / 'PREPARE_ATTEMPT.json', dict(label=label, started_unix=time.time(), no_retry=True))
    source_pins = pins()
    baseline = Path(BASE_ROOT)
    require(sha(baseline / 'SOURCE.json') == BASE_SOURCE_SHA, 'actual_frozen_baseline_source')
    require(sha(baseline / 'control/PLAN.json') == BASE_PLAN_SHA, 'actual_frozen_baseline_plan')
    base_plan = json.loads((baseline / 'control/PLAN.json').read_bytes())
    stage = Path('/localhome/local-rohing/orch_r153_r184_staging_20260917')
    packet = stage / 'orch_r184_C2_sleep41_1789684294308387719'
    require(sha(packet / 'PRESERVATION_RECEIPT.json') == PACKET_SHA, 'exact_saved41_packet')
    require(shutil.disk_usage(ROOT).free >= 8 * 1024**3, 'receiving_copy_and_three_checkpoints_disk_budget')
    receipt = json.loads((packet / 'PRESERVATION_RECEIPT.json').read_bytes())
    raw = ROOT / 'raw'
    from gpu.orch_r153_community_transport import remote_root
    require(remote_root(str(raw)) == raw, 'actual_bridge_root_accepted_before_copy')
    shutil.copytree(packet, raw)
    (raw / 'stream/inbox').mkdir()
    (raw / 'stream/WRITER.lock').touch(exist_ok=False)
    for path in (stage / 'registered_inbox').iterdir():
        require(path.is_file() and not path.is_symlink(), 'regular_registered_inbox')
        shutil.copy2(path, raw / 'stream/inbox' / path.name)
    for name, expected in receipt['checkpoint_files'].items():
        require(sha(raw / 'checkpoints/sleep_000041' / name) == expected, 'exact_saved41:' + name)
    saved = json.loads((raw / 'SAVED_STATE.json').read_bytes())
    require(saved['sha256'] == receipt['saved_state_sha256'] and saved['state']['pending'] is None,
        'completed_saved41_no_pending')
    require(saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'saved41_full_frontier')
    require(len(list((raw / 'stream/records').glob('[0-9]' * 20 + '.json'))) == 5129, 'exact_prefix_record_count')
    terminal = json.loads((raw / 'stream/records/00000000000000005128.json').read_bytes())
    require(terminal['kind'] == 'SLEEP_COMPLETE'
        and terminal['sha256'] == 'adcbefb57e9598fe75dfadd294dec0ef6aa1530faefbc4574b8b47c7cd834cc9',
        'source41_terminal_not_unsaved42')
    (SOURCE / 'context').mkdir(exist_ok=True)
    shutil.copy2(baseline / 'source/context/R153_STARTUP.md', SOURCE / 'context/R153_STARTUP.md')
    plan = make_plan(base_plan, SOURCE, label)
    require(plan['hard_end_unix'] == saved['state']['deadline_unix'], 'unchanged_saved_deadline')
    validate_plan(plan)
    require(digest(verify_gate(GATE_ROOT)) == GATE_SHA, 'frozen_actual_receiving_CPU_gate')
    command = [sys.executable, '-B', '-m', 'unittest', *TEST_MODULES, '-q']
    result = subprocess.run(command, cwd=SOURCE, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', TMPDIR='/tmp', PYTHONPATH=str(SOURCE),
            PYTHONDONTWRITEBYTECODE='1'), timeout=90)
    (ROOT / 'CPU.log').write_text(result.stdout)
    require(result.returncode == 0, 'receiving_focused_CPU_failed:' + result.stdout[-1800:])
    counts = re.findall(r'Ran (\d+) tests?', result.stdout)
    require(len(counts) == 1, 'actual_test_count_available')
    source_pins = pins()
    cpu = dict(schema='R186_RECEIVING_CPU_V1', passed=True, tests_run=int(counts[0]),
        source_pins=source_pins, observed_unix=time.time(), log_sha256=sha(ROOT / 'CPU.log'),
        packet_receipt_sha256=PACKET_SHA, gate_sha256=GATE_SHA, baseline_plan_sha256=BASE_PLAN_SHA,
        source_manifest_sha256=sha(ROOT / 'SOURCE.json'), receive_source_sha256=sha(__file__),
        startup_sha256=sha(SOURCE / 'context/R153_STARTUP.md'), no_suffix42=True,
        complete_episode_encoder_integrated=False)
    write(ROOT / 'CPU.json', cpu)
    control = ROOT / 'control'
    control.mkdir()
    write(control / 'RECEIVING_CPU.json', cpu)
    write(control / 'PLAN.json', plan)
    original = Path('/localhome/local-rohing/orch_r119_l1_generation_20260915_attempt2/FORKS.json')
    require(sha(original) == '621e1391285bcad9ee075106b4afab28970616b663876dc4ebeba7834e7b81e3',
        'existing_node2_lease_receipt')
    require(plan['hard_end_unix'] <= json.loads(original.read_bytes())['hard_deadline_unix'],
        'copy_wall_inside_existing_machine_wall')
    write(ROOT / 'LEASE.json', dict(hard_end_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'],
        existing_node2_original=str(original), existing_node2_original_sha256=sha(original), machine_lease_changed=False))
    ready = dict(status='CPU_READY_NOT_DISPATCHED', label=label, physical=plan['physical'],
        gpu_uuid=plan['gpu_uuid'], tests_run=cpu['tests_run'], cpu_sha256=sha(ROOT / 'CPU.json'),
        plan_sha256=sha(control / 'PLAN.json'), source_manifest_sha256=sha(ROOT / 'SOURCE.json'),
        source_file_count=len(source_pins), prepared_unix=time.time())
    write(ROOT / 'READY.json', ready)
    print(json.dumps(ready, sort_keys=True))


def launch(label):
    from gpu import orch_r125_continual_guard as guard
    require(ROOT == Path(REMOTE_ROOT) / (label + '3'), 'exact_new_copy_root')
    ready = json.loads((ROOT / 'READY.json').read_bytes())
    builder = json.loads((ROOT / 'BUILDER_ENTRY.json').read_bytes())
    require(builder['cpu_sha256'] == sha(ROOT / 'CPU.json') == ready['cpu_sha256']
        and builder['plan_sha256'] == sha(ROOT / 'control/PLAN.json') == ready['plan_sha256']
        and builder['label'] == label and builder['logged_unix'] <= time.time()
        and builder['coordination_entry_sha256'], 'actual_logged_Builder_CPU_provenance')
    source_pins = pins()
    write(ROOT / 'LAUNCH_ATTEMPT.json', dict(started_unix=time.time(), label=label,
        builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json'), no_retry=True))
    control = ROOT / 'control'
    plan = json.loads((control / 'PLAN.json').read_bytes())
    require(plan['max_sleeps'] == 44 and plan['physical'] == ARMS[label][0], 'fixed_launch_treatment')
    write(control / 'ALLOCATION.json', dict(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'], physical=plan['physical'], builder_entry_logged=True,
        builder_entry_path=str(ROOT / 'BUILDER_ENTRY.json'), builder_entry_sha256=sha(ROOT / 'BUILDER_ENTRY.json'),
        cpu_receipt_path=str(ROOT / 'CPU.json'), cpu_receipt_sha256=sha(ROOT / 'CPU.json'), declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', source_pins=source_pins, resume=True,
        copy_raw=str(ROOT / 'raw'), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        attempt_dir=str(control), host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        hard_end_unix=plan['hard_end_unix'], lease_path=str(ROOT / 'LEASE.json'), lease_sha256=sha(ROOT / 'LEASE.json'),
        next_reserved_unix=plan['lease_end_unix'], allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    write(control / 'GUARD.json', config)
    guard.validate(control / 'GUARD.json')
    journal = json.loads((ROOT / 'raw/stream/JOURNAL.json').read_bytes())
    bridge = dict(raw_root=str(ROOT / 'raw'), journal_id=journal['journal_id'],
        socket='/tmp/r186_c2_' + label + '_3.sock', gate_root=GATE_ROOT, gate_sha256=GATE_SHA,
        stop_unix=min(time.time() + 7200, plan['hard_end_unix']))
    write(ROOT / 'BRIDGE.json', bridge)
    processes = {}
    for name, argv in (
        ('cpu_bridge', [sys.executable, '-B', '-m', 'gpu.r184_cpu_bridge', '--config', str(ROOT / 'BRIDGE.json')]),
        ('supervisor', [sys.executable, '-B', '-m', 'gpu.r184_node2_confinement', 'dispatch', '--config', str(control / 'GUARD.json')]),
    ):
        with (ROOT / (name + '.log')).open('x') as log:
            process = subprocess.Popen(argv, cwd=SOURCE,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(SOURCE), PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        ticks = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19]
        processes[name] = dict(pid=process.pid, startticks=ticks)
    started = dict(status='WRAPPERS_STARTED_NOT_LOADED_PROOF', started_unix=time.time(), label=label,
        physical=plan['physical'], gpu_uuid=plan['gpu_uuid'], source_root=str(SOURCE),
        raw_root=str(ROOT / 'raw'), logical_root=plan['root'], guard_sha256=sha(control / 'GUARD.json'),
        processes=processes, complete_episode_encoder_integrated=False)
    write(ROOT / 'STARTED.json', started)
    print(json.dumps(started, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'launch'))
    parser.add_argument('label', choices=tuple(ARMS))
    arguments = parser.parse_args()
    try:
        (prepare if arguments.mode == 'prepare' else launch)(arguments.label)
    except BaseException as error:
        failure = ROOT / (arguments.mode.upper() + '_FAILED_' + str(time.time_ns()) + '.json')
        write(failure, dict(error_type=type(error).__name__, error=str(error), observed_unix=time.time(), no_retry=True))
        raise
