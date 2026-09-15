"""Checkpoint immutable inference evidence and release only assigned prefill PIDs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time

from gpu import orch_rich_intensity_guard as ownership
from gpu.orch_rich_hot_node3_run import bind_host
from gpu.orch_math_rich_screen import write


def identity(pid, root, index):
    if index not in (0, 1, 2):
        raise ValueError('release_only_prefill_0_1_2')
    directory = Path('/proc') / str(pid)
    arguments = (directory / 'cmdline').read_bytes().split(b'\0')
    environment = (directory / 'environ').read_bytes().split(b'\0')
    expected = [b'-m', b'gpu.orch_rich_hot_node3_run', b'screen', b'--root',
                str(root).encode(), b'--index', str(index).encode()]
    if not any(arguments[position:position + len(expected)] == expected
               for position in range(len(arguments))):
        raise ValueError('owned_exact_argv_mismatch')
    if ('CUDA_VISIBLE_DEVICES=' + ownership.DEVICES[index]).encode() not in environment:
        raise ValueError('owned_uuid_environment_mismatch')
    if directory.stat().st_uid != os.getuid() or os.getpgid(pid) != pid or os.getsid(pid) != pid:
        raise ValueError('owned_uid_session_processgroup_mismatch')
    return dict(pid=pid, physical_index=index, uuid=ownership.DEVICES[index],
        uid=directory.stat().st_uid, pgid=os.getpgid(pid), sid=os.getsid(pid),
        start_ticks=(directory / 'stat').read_text().rsplit(')', 1)[1].split()[19],
        command_sha256=hashlib.sha256((directory / 'cmdline').read_bytes()).hexdigest())


def release(root, output):
    bind_host()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for index in (0, 1, 2):
        launch = json.loads((root / 'run' / f'LAUNCH_{index}.json').read_text())
        records.append(identity(launch['pid'], root, index))
    write(output / 'IDENTITIES.json', records)
    for record in records:
        pid, index = record['pid'], record['physical_index']
        assert identity(pid, root, index) == record
        os.killpg(pid, signal.SIGSTOP)
    time.sleep(0.2)
    for record in records:
        pid, index = record['pid'], record['physical_index']
        assert identity(pid, root, index) == record
        shard = root / 'run' / f'shard{index}'
        destination = output / f'shard{index}'
        destination.mkdir()
        inventory, parsed, incomplete = {}, {}, []
        for path in sorted(shard.glob('*.json')):
            content = path.read_bytes()
            (destination / path.name).write_bytes(content)
            inventory[path.name] = hashlib.sha256(content).hexdigest()
            try:
                parsed[path.name] = json.loads(content)
            except json.JSONDecodeError:
                incomplete.append(path.name)
        unfinished = []
        for name, intent in parsed.items():
            if name.startswith('INTENT_') and 'CALL_' + name[7:] not in parsed:
                unfinished.append(dict(global_call=intent['global_call'], task_id=intent['task_id'],
                    kind=intent['kind'], status='INTERRUPTED_FOR_REQUESTED_REALLOCATION',
                    partial_native_tokens_unavailable=True, retried=False))
        write(destination / 'CHECKPOINT.json', dict(identity=record, files=inventory,
            incomplete_json_preserved=incomplete, unfinished_calls=unfinished,
            training_updates=0, checkpoint_kind='completed_raw_outputs_plus_inflight_intents',
            finished_utc=datetime.now(timezone.utc).isoformat()))
    for record in records:
        pid, index = record['pid'], record['physical_index']
        assert identity(pid, root, index) == record
        os.killpg(pid, signal.SIGTERM)
        os.killpg(pid, signal.SIGCONT)
    deadline = time.monotonic() + 30
    while any((Path('/proc') / str(record['pid'])).exists() for record in records):
        if time.monotonic() >= deadline:
            raise RuntimeError('owned_exit_not_confirmed_no_blind_escalation')
        time.sleep(0.5)
    clear = {}
    for index in (0, 1, 2):
        snapshot = ownership.scan(index, root / 'SERVICE_IDENTITY.json')
        write(output / f'RELEASE_{index}.json', snapshot)
        clear[index] = snapshot['clear']
    receipt = dict(status='RELEASED' if all(clear.values()) else 'NOT_CLEAR',
        finished_utc=datetime.now(timezone.utc).isoformat(), indices=[0, 1, 2],
        stopped_identities=records, release_clear=clear, touched_other_gpus=False,
        recipient='Pasteur route parenting and Main', main_ack_required=False,
        evidence_root=str(output))
    write(output / 'RECEIPT.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    release(options.root, options.output)
