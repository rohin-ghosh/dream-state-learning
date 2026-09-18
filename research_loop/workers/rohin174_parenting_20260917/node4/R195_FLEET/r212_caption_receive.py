"""Non-material exact historical-proof compatibility in the own P3 receiver."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from math_c import HOME, PYTHON, WALL, host, read, require, sha, write
from r206_handoff import records, root_for


CLIENT_SHA = '4ab66ec154cead349b8693747067e033978da1325f5455f0daf16c5e37c02c6f'
LEGACY_SHA = 'd9cc89488fa38a4c478b24ecaad7ae1228d37e6a505de530a25dd74e362bb5be'


def prepare():
    host()
    root = root_for(3)
    old, target = root / 'r210', root / 'r212'
    guard = read(old / 'control/GUARD.json')
    plan = read(guard['plan_path'])
    old_source = Path(plan['source_root'])
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'exact_failed_plan')
    require(all(sha(old_source / name) == digest for name, digest in guard['source_pins'].items()),
        'failed_receiver_source_unchanged')
    preserved = read(old / 'PRESERVED.json')
    history = records(root)
    require(history[-1]['sha256'] == preserved['last_record_sha256']
        and history[-1]['index'] == 368, 'fresh_exact_complete57_no_later_generation')
    require(sha(preserved['saved']['checkpoint_path']) == preserved['saved']['checkpoint_sha256']
        and read(preserved['saved']['record_path'])['sha256'] == preserved['saved']['record_sha256'],
        'same_preserved_checkpoint_and_record')
    require(read(old / 'control/EXIT.json')['exit_code'] == 1 and plan['physical'] == 3
        and plan['root'] == str(root / 'life') and guard['resume'] is True
        and plan['hard_end_unix'] == WALL and plan['max_sleeps'] is None, 'same_life_no_hold_or_recipe_reset')
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            command = (process / 'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        require(not (str(old / 'control/GUARD.json').encode() in command and b'native' in command),
            'failed_native_not_running')
    packet = HOME.parent / 'caption_r212_client'
    environment_path = Path('/localhome/local-rohing/orch_r212_caption_service_20260918/session1/CHILD_ENVIRONMENT.json')
    require(sha(packet / 'gpu/ny_caption_life.py') == CLIENT_SHA
        and sha(packet / 'organism_v6/r212_legacy_prose.py') == LEGACY_SHA, 'exact_client_and_historical_builder')
    require(sha(environment_path) == sha(packet / 'CHILD_ENVIRONMENT.json'), 'actual_public_environment_only')
    listening = read(environment_path.parent / 'LISTENING.json')
    require(listening['socket'] == '/tmp/r212_caption_n4.sock'
        and Path(listening['socket']).is_socket() and Path('/proc', str(listening['pid'])).exists(),
        'actual_Main_service_live')
    environment = read(environment_path)
    require(set(environment) == {'policy', 'scenes', 'help', 'scoring'}
        and 'rank <= 50 of 65' in environment['scoring'] and 'humour' in environment['help'], 'authorized_top50_humour')
    target.mkdir()
    source, control = target / 'source', target / 'control'
    shutil.copytree(old_source, source)
    control.mkdir()
    for path in packet.rglob('*.py'):
        shutil.copyfile(path, source / path.relative_to(packet))
        compile(path.read_text(), str(path), 'exec')
    for name in ('gpu/orch_r132_kernel_bridge.py', 'gpu/r184_cpu_bridge.py',
            'gpu/orch_r125_stream_journal.py', 'organism_v6/orch_r194_code_target_filter.py'):
        require(sha(source / name) == sha(old_source / name), 'bridges_and_strict_validators_unchanged')
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(old_source))
    scenes = ['Scene ' + str(scene['number']) + ': ' + '. '.join(scene['scene'].split('. ')[:2]) + '.'
        for scene in environment['scenes']]
    facts = environment['help'] + '\nSupplied image-only scene descriptions:\n' + '\n'.join(scenes) + '\n' + environment['scoring']
    require(len(facts.encode()) <= 2048, 'existing_environment_facts_bound')
    plan['think_act_learn']['environment_facts'] = facts
    replay = subprocess.run([str(PYTHON), '-B', '-c',
        'import json,sys; from gpu.r212_prose_replay import activate; activate(); '
        'from gpu.orch_r125_stream_journal import StreamJournal; '
        'journal=StreamJournal(sys.argv[1],create=False); print(json.dumps(journal.audit())); journal.close()',
        str(root / 'life/stream')], cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'), check=True, capture_output=True, text=True, timeout=60)
    audit = json.loads(replay.stdout)
    require(audit == dict(record_count=369, head_sha256=preserved['last_record_sha256']), 'strict_actual_replay_same_head')
    pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
    write(target / 'PRESERVED.json', dict(preserved, observed_unix=time.time(),
        inbox_hashes={path.name: sha(path) for path in (root / 'life/stream/inbox').glob('*.json')}))
    write(target / 'CAPTION_ENVIRONMENT.json', environment)
    cpu = target / 'RECEIVING_CPU.json'
    write(cpu, dict(passed=True, strict_actual_replay=audit, source_pins=pins, observed_unix=time.time(),
        saved=preserved['saved'], original_R203_builder_sha256=LEGACY_SHA, Main_client_sha256=CLIENT_SHA,
        local_regressions_passed=5, Main_tests_passed=14, generic_zero_reason='no_eligible_child_rows',
        validator_bypass=False, records_modified=False, broad_tests_run=0, socket=listening['socket']))
    write(control / 'PLAN.json', plan)
    allocation = read(guard['allocation_path'])
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_receipt_path=str(cpu), cpu_receipt_sha256=sha(cpu),
        declared_unix=time.time(), builder_entry='Main R212 explicit P3 launch; own scoped historical-proof compatibility; 5 focused regressions and strict actual replay')
    write(control / 'ALLOCATION.json', allocation)
    guard.update(plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'),
        source_pins=pins, attempt_dir=str(control))
    guard['device_containment']['unit'] = 'orch-r136-native-' + uuid.uuid4().hex
    write(control / 'GUARD.json', guard)
    bridge = read(old / 'BRIDGE.json')
    bridge.update(native_source=str(source), guard_path=str(control / 'GUARD.json'),
        guard_sha256=sha(control / 'GUARD.json'), socket=str(target / 'cpu.sock'), first_new_record=369)
    write(target / 'BRIDGE.json', bridge)
    subprocess.run([str(PYTHON), '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=dict(os.environ, CUDA_VISIBLE_DEVICES='',
        PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'), check=True, timeout=45)
    write(target / 'RECEIVING_READY.json', dict(status='CPU_TESTED_NOT_LIVE', guard_sha256=sha(control / 'GUARD.json'),
        physical=3, prepared_unix=time.time(), new_phase='R212_CAPTION_HUMOUR', socket=listening['socket']))
    print('P3_R212_RECEIVING_READY', json.dumps(audit), flush=True)


if __name__ == '__main__':
    prepare()
