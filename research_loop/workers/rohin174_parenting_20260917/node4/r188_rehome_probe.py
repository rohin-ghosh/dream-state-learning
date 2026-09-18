"""Model-free NODE4 receiving ACL evidence; never a learner launch or admission."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import uuid


ROOT = Path('/localhome/local-rohing/orch_r188_node4_rehome_20260917t2341z')
BASE = Path('/localhome/local-rohing')
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
R137_SHA = '74cca3f1061f848da049b19e98797c5925e7646002c82147399b0c1131c4dcd2'
PROBE_SHA = 'd32658950a078c837eeecc9096b03ae4d3098456ab4ac68e8ea7721b4a9a4192'
LEASE = BASE / 'orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json'
LEASE_SHA = 'ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2'
DEVICES = {
    5: ('GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30', 6),
    6: ('GPU-06b31c8f-7a96-d812-23f3-df3444d95397', 5),
    7: ('GPU-6eac3b9d-551a-d786-f598-04ef6d701c98', 4),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(physical, reference, unit):
    require(type(physical) is int and physical in DEVICES, 'only_reserved_receiving_5_6_7')
    require(hashlib.sha256(reference.encode()).hexdigest() == R137_SHA, 'unchanged_R137_command_reference')
    nodes = [node for node in ast.parse(reference).body if isinstance(node, ast.FunctionDef)
        and node.name == 'device_containment_command']
    require(len(nodes) == 1, 'one_existing_device_command')
    namespace = dict(require=require, re=re, Path=Path, BASE=BASE,
        DEVICES={physical: binding[0] for physical, binding in DEVICES.items()})
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<unchanged_R137_device_command>', 'exec'), namespace)
    gpu_uuid, minor = DEVICES[physical]
    policy = dict(uid=2524, gid=2524, minor=minor, unit=unit)
    invocation = ['/usr/bin/python3', '-B', str(ROOT / 'device_probe.py'),
        '--policy', json.dumps(policy, sort_keys=True), '--uuid', gpu_uuid]
    return namespace['device_containment_command'](physical, minor, 2524, 2524, unit, ROOT, invocation, 45), policy


def run(physical):
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_NODE4_host')
    require(Path(__file__).resolve().parent == ROOT and os.getuid() == os.getgid() == 2524,
        'exact_owned_receiving_root_and_identity')
    require(sha(ROOT / 'device_probe.py') == PROBE_SHA and sha(LEASE) == LEASE_SHA, 'existing_probe_and_lease')
    lease = json.loads(LEASE.read_text())
    require(lease['hard_end_unix'] == 1789754400 and time.time() + 60 < lease['hard_end_unix'], 'unchanged_actual_wall')
    gpu_uuid, minor = DEVICES[physical]
    inventory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu',
        '--format=csv,noheader,nounits'], text=True, timeout=20)
    rows = [[value.strip() for value in row.split(',')] for row in inventory.splitlines()]
    row = next(row for row in rows if row[0] == str(physical))
    require(row[1] == gpu_uuid and row[2:] == ['0', '0'], 'reserved_slot_still_idle')
    holders = subprocess.run(['sudo', '-n', 'fuser', '-v', '/dev/nvidia' + str(minor)],
        capture_output=True, text=True, timeout=20)
    require(holders.returncode == 1 and not (holders.stdout + holders.stderr).strip(), 'no_target_FD_holder')
    invocation, policy = command(physical, (ROOT / 'reference_r137.py').read_text(), 'orch-r136-nvml-' + uuid.uuid4().hex)
    intent = ROOT / f'RECEIVING_DEVICE_{physical}_INTENT.json'
    with intent.open('x') as stream:
        json.dump(dict(command=invocation, physical=physical, policy=policy,
            observed_unix=time.time(), native_launch=False), stream, indent=2)
    result = subprocess.run(invocation, capture_output=True, text=True, timeout=60)
    with (ROOT / f'RECEIVING_DEVICE_{physical}.log').open('x') as stream:
        stream.write(result.stdout + result.stderr)
    require(result.returncode == 0, 'actual_strict_service_probe_failed')
    proof = json.loads(result.stdout)
    require(proof['status'] == 'PASS' and proof['policy'] == policy and proof['gpu_uuid'] == gpu_uuid
        and proof['denied_foreign_minors'] == [value for value in range(8) if value != minor]
        and proof['target_open_close'] and not proof['CUDA_context_created'], 'actual_seven_foreign_denials')
    receipt = dict(status='RECEIVING_DEVICE_PROOF_NOT_LEARNER_ADMISSION', physical=physical, proof=proof,
        observed_unix=time.time(), hard_end_unix=lease['hard_end_unix'], boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        source_sha256=sha(__file__), device_command_reference_sha256=R137_SHA,
        probe_sha256=PROBE_SHA, lease_sha256=LEASE_SHA, model_calls=0, native_signals=0)
    with (ROOT / f'RECEIVING_DEVICE_{physical}.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--physical', type=int, choices=tuple(DEVICES), required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.physical), sort_keys=True))
