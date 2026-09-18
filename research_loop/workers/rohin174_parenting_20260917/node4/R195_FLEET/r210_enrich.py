"""Resume stopped node4 clone screens as a separate, explicitly authorized phase."""

import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from math_c import HELPER_BUNDLE, HOME, PYTHON, WALL, host, read, require, sha, write
from r206_handoff import ARCHIVE_SHA, bind_driver, records, root_for
from retire_brain_guided6 import module


FILES = {
    'gpu/orch_r184_think_act_learn.py': '0575afc35273c2cffc90f45be3635d562ab5d6eef7d7d22e3dcf36c365be9673',
    'organism_v6/orch_r203_prose_target_filter.py': '4bceeff13176f61b8ee32f4ae4f995ce8cce5d2aba7b2286bd13b6e48281d9ed',
}
POLICY = 'R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1'


def prepare(physical):
    host()
    require(physical in (2, 3, 5, 6, 7), 'Main_zero_vision_one_kernel_four_untouched')
    root = root_for(physical)
    target = root / 'r210'
    target.mkdir()
    old = root / 'reload_r206'
    guard_path = old / 'control/GUARD.json'
    guard = read(guard_path)
    plan = read(guard['plan_path'])
    old_source = Path(plan['source_root'])
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'exact_R206_plan')
    require(all(sha(old_source / name) == digest for name, digest in guard['source_pins'].items()), 'unchanged_R206_source')
    require(plan['physical'] == physical and plan['root'] == str(root / 'life')
        and plan['hard_end_unix'] == WALL and guard['resume'] is True, 'same_life_resume_wall')
    history = records(root)
    last_loaded = [entry for entry in history if entry['kind'] == 'LOADED'][-1]
    require(not Path('/proc', str(last_loaded['document']['pid'])).exists(), 'screen_native_already_exited_no_signals')
    complete = [entry for entry in history if entry['kind'] == 'SLEEP_COMPLETE'][-1]
    cycle = complete['document']['cycle']
    require(cycle == 57, 'completed_guided_and_withdrawn_screen')
    tail = history[complete['index'] + 1:]
    require(tail and tail[-1]['kind'] == 'TERMINAL'
        and tail[-1]['document'] == dict(completed_sleeps=cycle, status='R184_SCREEN_STOP'), 'exact_terminal_screen_boundary')
    require(all(entry['kind'] == 'R184_LEARN_COMPLETE'
        and entry['document']['cycle'] == cycle
        and entry['document']['checkpoint'] == complete['document']['checkpoint'] for entry in tail[:-1]), 'metadata_only_tail_no_later_generation')
    rollout = module('r210_existing_rollout', HELPER_BUNDLE / 'node4_rollout.py')
    helpers = rollout.helper_module(HELPER_BUNDLE)
    unused_guard, unused_plan, original = helpers.originals(guard_path)
    original_records = helpers.records
    helpers.records = lambda unused: original_records(root / 'life')[:complete['index'] + 1]
    try:
        saved = helpers.sleep_boundary(root / 'life')
    finally:
        helpers.records = original_records
    evidence = helpers.saved_evidence(plan, saved, original)
    write(target / 'PRESERVED.json', dict(saved=evidence, last_record_index=history[-1]['index'],
        last_record_sha256=history[-1]['sha256'], observed_unix=time.time(), no_signals=True,
        root=str(root / 'life'), backing_root=str((root / 'life').resolve()),
        previous_screen='GUIDED_52_54_WITHDRAWN_55_57_UNCHANGED', new_phase='R210_ENRICHMENT',
        inbox_hashes={path.name: sha(path) for path in (root / 'life/stream/inbox').glob('*.json')}))
    packet = HOME.parent / 'r209_prose_ready'
    ready = read(packet / 'READY.json')
    require(ready['status'] == 'CPU_TESTED_NOT_LIVE' and ready['base_archive_sha256'] == ARCHIVE_SHA
        and ready['files'] == FILES and ready['prose_target_filter'] == POLICY, 'approved_exact_R209_repair')
    source, control = target / 'source', target / 'control'
    shutil.copytree(old_source, source)
    control.mkdir()
    for name, digest in FILES.items():
        require(sha(packet / name) == digest, 'incoming_R209_file_hash')
        shutil.copyfile(packet / name, source / name)
    bind_driver(source, plan['think_act_learn']['trial_id'], physical == 5)
    plan['source_root'] = str(source)
    plan['max_sleeps'] = None
    plan['think_act_learn']['prose_target_filter'] = POLICY
    require(plan['think_act_learn']['console_reply_policy'] == 'R205_CONSOLE_REPLY_ACT_V1'
        and plan['think_act_learn']['pinned_messages_policy'] == 'R206_VERBATIM_ROHIN_MESSAGES_V1', 'genuine_R205_console_and_R206_pins')
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(old_source))
    if physical == 3:
        from r210_caption_bind import bind
        bind(source, plan, target)
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    for name in ('gpu/orch_r132_kernel_bridge.py', 'gpu/r184_cpu_bridge.py'):
        require(sha(source / name) == sha(old_source / name), 'existing_bridges_preserved')
    for name in FILES:
        compile((source / name).read_text(), str(source / name), 'exec')
    cpu = target / 'RECEIVING_CPU.json'
    write(cpu, dict(passed=True, source_pins=pins, Main_R206_archive=ARCHIVE_SHA,
        R209_READY_sha256=sha(packet / 'READY.json'), R209_tests=ready['tests'], broad_tests_run=0,
        preserved=evidence, observed_unix=time.time(), parent_phase='R210_NOT_OLD_CONTROL'))
    write(control / 'PLAN.json', plan)
    allocation = read(guard['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_receipt_path=str(cpu), cpu_receipt_sha256=sha(cpu),
        declared_unix=time.time(), builder_entry='Main R210 enrichment authorization; exact saved57; approved R209 repair over R206')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        source_pins=pins, attempt_dir=str(control))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    bridge = read(old / 'BRIDGE.json')
    bridge.update(native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), socket=str(target / 'cpu.sock'), first_new_record=len(history))
    require(len(bridge['socket'].encode()) < 108 and bridge['journal_id'] == history[-1]['journal_id'], 'same_journal_and_bounded_socket')
    write(target / 'BRIDGE.json', bridge)
    subprocess.run([str(PYTHON), '-B', '-c',
        'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])', str(control / 'GUARD.json')],
        cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
        check=True, timeout=45)
    write(target / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE', guard_sha256=sha(control / 'GUARD.json'),
        physical=physical, prepared_unix=time.time(), new_phase='R210_ENRICHMENT'))
    if physical == 3:
        from r210_caption_bind import publish_opening
        publish_opening(root, target)
    print('R210_RECEIVING_READY', physical, flush=True)


def launch(physical, phase='r210'):
    host()
    require(physical in (2, 3, 5, 6, 7), 'only_assigned_enrichment_slots')
    root = root_for(physical)
    require(phase == 'r210' or phase == 'r212' and physical == 3, 'exact_authorized_receiving_phase')
    target = root / phase
    with (target / 'OPERATOR.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (target / 'DISPATCHED.json').exists(), 'no_duplicate_launch')
        preserved = read(target / 'PRESERVED.json')
        history = records(root)
        require(history[-1]['sha256'] == preserved['last_record_sha256'], 'fresh_same_complete_no_rollback')
        guard_path = target / 'control/GUARD.json'
        require(sha(guard_path) == read(target / 'RECEIVING_READY.json')['guard_sha256'], 'receiving_source_unchanged')
        plan = read(target / 'control/PLAN.json')
        processes = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'], text=True)
        require(plan['gpu_uuid'] not in processes, 'physical_GPU_unoccupied')
        with (target / 'BRIDGE.log').open('x') as output:
            bridge = subprocess.Popen([str(PYTHON), '-B', str(root / 'math_c_bridge.py'), '--config', str(target / 'BRIDGE.json')],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 15
        while not list((target / 'bridge_receipts').glob('READY_*.json')):
            require(time.monotonic() < deadline and bridge.poll() is None, 'actual_bridge_ready')
            time.sleep(.1)
        name = 'gpu.orch_r188_node4_rehome_containment' if physical == 6 else 'gpu.r203_node4_containment'
        source = target / 'source'
        with (target / 'control/SUPERVISOR.log').open('x') as output:
            native = subprocess.Popen([str(PYTHON), '-B', '-m', name, 'contained-supervise', '--config', str(guard_path)],
                cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        write(target / 'DISPATCHED.json', dict(physical=physical, supervisor_pid=native.pid, bridge_pid=bridge.pid,
            started_unix=time.time(), preserved_cycle=57, root=str(root / 'life'), hard_end_unix=WALL,
            status='DISPATCHED_NOT_YET_LOADED', new_phase='R212_CAPTION_HUMOUR' if phase == 'r212' else 'R210_ENRICHMENT'))
        print('R210_DISPATCHED', physical, native.pid, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'launch'))
    parser.add_argument('--physical', type=int, required=True)
    options = parser.parse_args()
    globals()[options.action](options.physical)
