"""Read-only Main allocation check; no process or GPU mutation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time


def reservations(device_index, device_uuid, proc=Path('/proc')):
    matches, unresolved, excluded = [], [], []
    scanned = 0
    for entry in proc.glob('[0-9]*/environ'):
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            try:
                fields = entry.read_bytes().split(b'\0')
            except PermissionError:
                process = entry.parent
                status = (process / 'stat').read_text().rsplit(')', 1)[1].split()
                identity = dict(pid=int(process.name), comm=(process / 'comm').read_text().strip(),
                                ppid=int(status[1]), start_ticks=int(status[19]))
                if identity == dict(pid=3245, comm='systemd', ppid=1, start_ticks=2469):
                    excluded.append(identity)
                else:
                    unresolved.append(identity)
                continue
            scanned += 1
            devices = next((field.split(b'=', 1)[1].decode() for field in fields
                            if field.startswith(b'CUDA_VISIBLE_DEVICES=')), '')
            if set(value.strip() for value in devices.split(',')) & {str(device_index), device_uuid}:
                matches.append(int(entry.parent.name))
        except FileNotFoundError:
            continue
    return dict(same_user_environments_scanned=scanned, matching_reservations=matches,
                unresolved_same_user=unresolved, verified_nonlearner_exclusions=excluded,
                reservation_scope='same-user readable environments; explicit manager identity exception')


def check(device_index, device_uuid):
    inventory = subprocess.run(['nvidia-smi', '-i', str(device_index), '--query-gpu=index,uuid', '--format=csv,noheader,nounits'],
                               text=True, capture_output=True, check=True, timeout=25).stdout
    pairs = [tuple(value.strip() for value in line.split(',')) for line in inventory.splitlines()]
    if (str(device_index), device_uuid) not in pairs:
        raise ValueError('GPU index/UUID mismatch')
    output = subprocess.run(['nvidia-smi', '-i', str(device_index), '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'],
                            text=True, capture_output=True, check=True, timeout=25).stdout
    compute = []
    for line in output.splitlines():
        gpu, process = (value.strip() for value in line.split(','))
        if gpu == device_uuid:
            compute.append(int(process))
    result = dict(checked_unix=time.time(), gpu_index=device_index, gpu_uuid=device_uuid,
                  compute_processes=compute, **reservations(device_index, device_uuid))
    print(json.dumps(result, sort_keys=True), flush=True)
    if compute or result['matching_reservations'] or result['unresolved_same_user']:
        raise ValueError('GPU occupied or reservation unresolved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu-index', type=int, required=True)
    parser.add_argument('--gpu-uuid', required=True)
    options = parser.parse_args()
    check(options.gpu_index, options.gpu_uuid)
