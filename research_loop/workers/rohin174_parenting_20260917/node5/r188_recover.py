"""Preserve the whole stopped old life, restore complete41, replay only inputs."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    root = Path(__file__).resolve().parent
    source = root / 'source'
    sys.path.insert(0, str(source))
    from gpu.orch_r125_cpu_experiment import digest, verify_gate
    from gpu import orch_r125_continual_guard as guard
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == 2524, 'NODE5_only')
    stop = read(root / 'STOPPED.json')
    for identity in stop['pair'].values():
        process = Path('/proc') / str(identity['pid'])
        require(not process.exists(), 'original_native_pair_must_be_dead')
    logical = Path(stop['old_root'])
    packet = Path('/localhome/local-rohing/orch_r184_C2_sleep41_1789684294308387719')
    require(sha(packet/'PRESERVATION_RECEIPT.json') == 'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e', 'fixed41_packet')
    packet_receipt = read(packet/'PRESERVATION_RECEIPT.json')
    saved = read(packet/'SAVED_STATE.json')
    require(saved['state']['pending'] is None and saved['state']['sleep_frontier'] == len(saved['state']['rows']), 'complete41_no_pending_sleep')
    old_config = read('/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/GUARD.json')
    plan = read(old_config['plan_path'])
    gate_root = '/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate'
    gate_sha = '8b4579d9c99c2f4d54fbd738ff965bc9472ed9f08ff6fae5f4dbfeadceaf1150'
    require(digest(verify_gate(gate_root)) == gate_sha, 'actual_NODE5_same_source_CPU_gate')
    require(shutil.disk_usage(root).free > 3 * 1024**3, 'recovery_disk_headroom')
    archive = root / 'archived_full_original_life'
    require(logical.is_dir() and not archive.exists() and not (root/'ARCHIVE_INTENT.json').exists(), 'one_archive_not_replayed')
    prefix_ids = set()
    suffix_ids = set()
    for path in sorted((logical/'stream/records').glob('[0-9]'*20+'.json')):
        with path.open('rb') as stream:
            stream.seek(max(0,path.stat().st_size-4096))
            tail = stream.read()
        metadata = json.loads(b'{'+tail[tail.rfind(b',"index":')+1:])
        if metadata['kind'] == 'INBOX':
            record = read(path)
            (prefix_ids if record['index'] <= 5128 else suffix_ids).add(record['document']['message']['id'])
    inventory = []
    for path in sorted((logical/'stream/inbox').glob('*.json')):
        message = read(path)
        require(message['id'] == path.stem, 'exact_inbox_filename')
        retained = message['id'] in prefix_ids
        speaker = message.get('speaker', message.get('actor', 'UNATTRIBUTED'))
        include = retained or speaker != 'Tool'
        kind = 'PREFIX_REGISTERED_NO_REDELIVERY' if retained else ('DISCARDED_SUFFIX_INPUT_REDELIVERY' if message['id'] in suffix_ids else 'PENDING_INPUT_FIRST_DELIVERY')
        inventory.append(dict(name=path.name,id=message['id'],speaker=speaker,sha256=sha(path),
            include=include,classification=kind if include else 'ARCHIVED_TOOL_FEEDBACK_NOT_NEW_EXECUTION'))
    expected_rohin = '3078c29c7f70428da03ba284e247206c'
    require(any(item['id'] == expected_rohin and item['include'] for item in inventory), 'Rohin20_08_input_preserved')
    write(root/'ARCHIVE_INTENT.json', dict(original=str(logical),archive=str(archive),inode=logical.stat().st_ino,
        cutoff=5128,stopped_receipt_sha256=sha(root/'STOPPED.json'),inputs=inventory,observed_unix=time.time()))
    original_inode = logical.stat().st_ino
    logical.rename(archive)
    require(archive.stat().st_ino == original_inode, 'atomic_full_root_preserved')
    shutil.copytree(packet, logical)
    for name, expected in packet_receipt['checkpoint_files'].items():
        require(sha(logical/'checkpoints/sleep_000041'/name) == expected, 'same_complete41_checkpoint')
    (logical/'stream/inbox').mkdir(mode=0o700)
    (logical/'stream/WRITER.lock').touch(exist_ok=False)
    for item in inventory:
        if not item['include']:
            continue
        origin = archive/'stream/inbox'/item['name']
        target = logical/'stream/inbox'/item['name']
        shutil.copyfile(origin,target)
        require(sha(target) == item['sha256'], 'byte_identical_inbox')
        target.chmod(0o444)
    for path in archive.rglob('*'):
        require(not path.is_symlink(), 'archive_no_symlink')
        if path.name == 'WRITER.lock':
            continue
        path.chmod(0o555 if path.is_dir() else 0o444)
    archive.chmod(0o555)
    write(root/'RESTORED.json', dict(archive=str(archive),root=str(logical),source_cutoff=5128,
        source_sleep=41,restored_optimizer_steps=4428,discarded_recorded_updates=stop['discarded_recorded_updates'],
        possible_unlogged_inflight=stop['possible_unlogged_inflight_update'],inputs=inventory,
        retrospective_tool_execution=False,label='R188_LOSS_LABELLED_SAME_LIFE_NOT_UNBROKEN',observed_unix=time.time()))
    finish_runtime(root, source, logical, plan, gate_root, gate_sha, old_config, guard)


def finish_runtime(root, source, logical, plan, gate_root, gate_sha, old_config, guard):
    (source/'context').mkdir(exist_ok=True)
    shutil.copyfile(plan['startup_context']['path'], source/'context/R153_STARTUP.md')
    plan.update(source_root=str(source),rehearsal_presentations=0)
    plan['startup_context']['path'] = str(source/'context/R153_STARTUP.md')
    plan['think_act_learn'] = dict(schema='R184_THINK_ACT_LEARN_V1',trial_id='C2_R188_same_life_recovery',
        reflection_policy='explicit',think_segments=1,cpu_gate_root=gate_root,cpu_gate_sha256=gate_sha)
    pins = {str(path.relative_to(source)):sha(path) for path in source.rglob('*.py')}
    require(pins == read(root/'SOURCE.json')['source_pins'], 'frozen_actual_source_closure')
    test = subprocess.run([sys.executable,'-B','-m','unittest','tests.test_orch_r184_think_act_learn','-q'],
        cwd=source,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),TMPDIR='/tmp'),
        capture_output=True,text=True,timeout=40)
    (root/'CPU.log').write_text(test.stdout + test.stderr)
    require(test.returncode == 0, 'receiving_scaffold_CPU')
    cpu = dict(passed=True,source_pins=pins,observed_unix=time.time(),log_sha256=sha(root/'CPU.log'),
        loss_labelled_recovery=True,restored_optimizer_steps=4428,old_root_archived=True)
    write(root/'CPU.json',cpu)
    control = root/'control'
    control.mkdir()
    write(control/'RECEIVING_CPU.json',cpu)
    write(control/'PLAN.json',plan)
    lease = read(old_config['lease_path'])
    require(sha(old_config['lease_path']) == old_config['lease_sha256'], 'original_lease_unchanged')
    write(root/'LEASE.json',lease)
    write(control/'ALLOCATION.json',dict(plan_sha256=sha(control/'PLAN.json'),cpu_tests_passed=True,
        gpu_uuid=plan['gpu_uuid'],physical=plan['physical'],builder_entry_logged=True,
        cpu_receipt_path=str(root/'CPU.json'),cpu_receipt_sha256=sha(root/'CPU.json'),declared_unix=time.time()))
    config = dict(schema='R125_CONTINUAL_GUARD_V1',source_pins=pins,resume=True,copy_raw=str(logical),
        plan_path=str(control/'PLAN.json'),plan_sha256=sha(control/'PLAN.json'),attempt_dir=str(control),
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),hard_end_unix=plan['hard_end_unix'],
        lease_path=str(root/'LEASE.json'),lease_sha256=sha(root/'LEASE.json'),next_reserved_unix=old_config['next_reserved_unix'],
        allocation_path=str(control/'ALLOCATION.json'),allocation_sha256=sha(control/'ALLOCATION.json'))
    write(control/'GUARD.json',config)
    guard.validate(control/'GUARD.json')
    journal = read(logical/'stream/JOURNAL.json')
    bridge = dict(raw_root=str(logical),journal_id=journal['journal_id'],socket='/tmp/r188_node5_c2_recovery1.sock',
        gate_root=gate_root,gate_sha256=gate_sha,stop_unix=plan['hard_end_unix'])
    write(root/'BRIDGE.json',bridge)
    processes = {}
    for name, argv in (('cpu_bridge',[sys.executable,'-B','-m','gpu.r184_cpu_bridge','--config',str(root/'BRIDGE.json')]),
        ('supervisor',[sys.executable,'-B','-m','gpu.r188_node5_confinement','dispatch','--config',str(control/'GUARD.json')])):
        with (root/(name+'.log')).open('x') as log:
            process = subprocess.Popen(argv,cwd=source,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(source),PYTHONDONTWRITEBYTECODE='1'),
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        ticks = Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
        processes[name] = dict(pid=process.pid,start_ticks=ticks)
    write(root/'STARTED.json',dict(processes=processes,source=str(source),root=str(logical),
        guard_sha256=sha(control/'GUARD.json'),label='R188_LOSS_LABELLED_SAME_LIFE',observed_unix=time.time()))
    print(json.dumps(read(root/'STARTED.json')))


if __name__ == '__main__':
    main()
