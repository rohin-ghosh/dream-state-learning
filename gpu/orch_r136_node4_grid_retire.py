"""Preserve a40r7's exact frozen BASE grid boundary; never launch or fit a model."""

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import struct
import time

from gpu import orch_r136_node4_launch as node4


ROOT = node4.BASE/'orch_r118_node3_6_grid_20260915_attempt1'
SOURCE = node4.BASE/'orch_r119_grid_lease_source_20260915_v1'
OLD = node4.BASE/'orch_r118_node3_6_grid_recovery_source_20260915_v2'
ERA = 'lease_budget_r119_base'
BOUNDARY_EVENTS = 0x8 | 0x80 | 0x100
MAX_WAIT_SECONDS = 3600
PINS = {
    str(SOURCE/'gpu/orch_r119_grid_lease_resume.py'): '449d0208a47bc14cf84d70410ebf2950c2fcc40285c6ada3f1b4fa4ac9c3f403',
    str(SOURCE/'gpu/orch_r119_grid_a40r7_continue.py'): '46c7f7ddbe5fa29892d221adf42798f5a523a0f1af718b141e7d8aef193611ac',
    str(SOURCE/'gpu/orch_r119_grid_continuation.py'): '9de64111bc02c2db61050e36aa244bc8c558440b7682ac8699f4590515d9439b',
    str(OLD/'gpu/orch_r115_grid_native.py'): 'd282ce52b352e93db5345777c8d28af5a9577813d9d3642a7d33b1806bf1a2f3',
}
require, read, write, sha, ref = node4.require, node4.read, node4.write, node4.sha, node4.ref


def boundary_markers(payload):
    offset, markers = 0, set()
    while offset + 16 <= len(payload):
        _, mask, _, length = struct.unpack_from('iIII', payload, offset)
        name = payload[offset+16:offset+16+length].rstrip(b'\0').decode()
        if mask & BOUNDARY_EVENTS and re.fullmatch(r'C[0-9]{4}_CONTINUED.json', name):
            markers.add(name)
        offset += 16 + length
    return sorted(markers)


def check_wait(wait_seconds, lease, now):
    require(type(wait_seconds) is int and 1 <= wait_seconds <= MAX_WAIT_SECONDS
            and now + wait_seconds + 300 < lease['hard_end_unix']
            <= lease['lease_end_unix'] - 21600, 'bounded_existing_lease')


def check_chain(request):
    require(type(request.get('physical')) is int and request['physical'] == 7, 'physical7_only')
    actor, timer, guard = (request[key] for key in ('actor', 'timer', 'supervisor'))
    arguments = [str(node4.BASE/'v2/venv/bin/python'), '-B', str(SOURCE/'gpu/orch_r119_grid_lease_resume.py'),
                 'native', '--physical', '6', '--old-source', str(OLD)]
    require(actor['argv'] == arguments, 'exact_migrated_GRID_actor')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
            and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
            and timer['argv'][4:] == arguments, 'exact_own_timeout')
    require(guard['argv'] == ['python3', '-B', arguments[2], 'guard', '--physical', '6', '--old-source', str(OLD)],
            'exact_migrated_GRID_guard')
    require(actor['parent'] == timer['pid'] and timer['parent'] == guard['pid'], 'exact_three_process_chain')
    require(actor['uid'] == timer['uid'] == guard['uid'] == os.getuid(), 'same_owned_uid')
    require(actor['cvd'] == timer['cvd'] == [node4.allocation(7)] and guard['cvd'] == [''], 'physical7_UUID_only')


def frontier(root, marker, actor):
    root = Path(root)
    require(re.fullmatch(r'C[0-9]{4}_CONTINUED.json', marker), 'exact_boundary_name')
    saved = read(root/ERA/marker)
    cycle = int(marker[1:5])
    require(saved['cycle'] == cycle and saved['optimizer_steps'] == 0, 'frozen_saved_cycle')
    require(saved['carry'] == ref(root/'CARRY.json') and saved['ledger'] == ref(root/'LEDGER.jsonl'),
            'no_work_after_exact_saved_carry_ledger')
    loaded = read(root/ERA/'LOADED.json')
    require(loaded['pid'] == actor['pid'] and loaded['optimizer_steps'] == 0
            and loaded['no_adapter']['adapter_parameter_count'] == 0
            and loaded['no_adapter']['trainable_parameter_count'] == 0, 'frozen_BASE_not_active_optimizer')
    complete_path = root/'cycles'/f'{cycle:04d}'/'TRAIN_COMPLETE.json'
    complete = read(complete_path)
    require(complete['optimizer_steps'] == 0 and len(complete['outcomes']) == 2
            and complete['carry'] == read(root/'CARRY.json')
            and complete['finished_unix'] <= saved['observed_unix'], 'two_episode_complete_saved_carry')
    rows = [json.loads(line) for line in (root/'LEDGER.jsonl').read_text().splitlines() if line]
    require(max(row.get('cycle', 0) for row in rows) == cycle, 'no_later_grid_cycle')
    require(all(row['reserved_unix'] <= saved['observed_unix'] for row in rows), 'no_later_grid_charge')
    for row in rows:
        if row.get('cycle') != cycle:
            continue
        if row['kind'] == 'NATIVE':
            call = read(root/'calls'/f'N{row["number"]:05d}.json')
            require(row['split'] == 'TRAIN' and not row.get('attached_readout')
                    and call['cycle'] == cycle and call['number'] == row['number']
                    and call['status'] == 'COMPLETE' and call['finished_unix'] <= saved['observed_unix'],
                    'no_inflight_or_later_GRID_native')
        elif row['kind'] == 'PARENT':
            received = read(root/'parent_received'/f'P{row["number"]:04d}.json')
            require(received['observed_unix'] <= saved['observed_unix'], 'parent_disposition_before_saved_boundary')
        else:
            raise ValueError('unknown_grid_charge_kind')
    return dict(checkpoint=ref(root/ERA/marker), carry=saved['carry'], ledger=saved['ledger'],
                train_complete=ref(complete_path), cycle=cycle, optimizer='ABSENT_FROZEN_BASE',
                live_generation_rng='NOT_EXPORTED_NO_BITWISE_GENERATION_RESUME_CLAIM')


def verify_release(directory, output):
    directory, output = Path(directory), Path(output)
    request = read(directory/'REQUEST.json')
    check_chain(request)
    require(all(not node4.custody.alive(request[key]) for key in ('actor','timer','supervisor')), 'all_old_actors_exited')
    boundary = read(directory/'BOUNDARY.json')
    require(boundary['checkpoint'] == ref(boundary['checkpoint']['path']), 'saved_checkpoint_unchanged')
    archive = read(directory/'ARCHIVE_MANIFEST.json')['archive']
    require(archive == ref(archive['path']), 'immutable_archive_bytes')
    if output != directory:
        output.mkdir(parents=True, exist_ok=False)
    node4.release(7, output)
    result = dict(schema='R136_NODE4_RELEASE_V1', physical=7, gpu_uuid=node4.allocation(7), retired=True,
                  boundary=ref(directory/'BOUNDARY.json'), archive=ref(directory/'ARCHIVE_MANIFEST.json'),
                  scan=ref(output/'FINAL_SCAN.json'), finished_unix=time.time())
    write(output/'RELEASED.json', result)
    return result


def retire(request, output):
    check_chain(request)
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == node4.HOST_SHA, 'exact_node4_host')
    require(request['tested_source_sha256'] == sha(__file__)
            and request['helper_sha256'] == sha(node4.__file__)
            and request['custody_sha256'] == sha(node4.custody.__file__), 'tested_source_closure')
    require(node4.checked(request['cpu_receipt'])['passed'] is True, 'CPU_provenance_required')
    for path, expected in PINS.items():
        require(sha(path) == expected, 'reviewed_GRID_source')
    lease = read(ROOT/ERA/'LEASE_BUDGET.json')
    check_wait(request['wait_seconds'], lease, time.time())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', request)
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK)
    require(watch >= 0 and library.inotify_add_watch(watch, os.fsencode(ROOT/ERA), BOUNDARY_EVENTS) >= 0, 'inotify_required')
    descriptors, paused, handlers = {}, [], {}

    def interrupted(signum, frame):
        raise InterruptedError('operator_signal:'+str(signum))

    started, attempt = time.time(), 0
    try:
        for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            handlers[signum] = signal.signal(signum, interrupted)
        for label in ('supervisor','timer','actor'):
            node4.custody.same(request[label])
            descriptors[label] = os.pidfd_open(request[label]['pid'])
            node4.custody.same(request[label])
        deadline = time.monotonic()+request['wait_seconds']
        while time.monotonic() < deadline:
            readable, _, _ = select.select([watch], [], [], max(0, min(1, deadline-time.monotonic())))
            if not readable:
                for label in descriptors:
                    node4.custody.same(request[label])
                continue
            markers = boundary_markers(os.read(watch, 65536))
            if not markers:
                continue
            marker = max(markers)
            attempt += 1
            try:
                for label in ('supervisor','timer','actor'):
                    paused.append(label)
                    node4.custody.pause(request[label],descriptors[label])
                require(read(ROOT/ERA/marker)['observed_unix'] >= started, 'fresh_boundary_not_old_carry')
                boundary = frontier(ROOT,marker,request['actor'])
                archive = node4.snapshot([ROOT,SOURCE,OLD],output/f'ARCHIVE_{attempt:03d}.tar')
                require(frontier(ROOT,marker,request['actor']) == boundary, 'boundary_stable_after_archive')
            except (ValueError,FileNotFoundError,json.JSONDecodeError) as error:
                write(output/f'REJECTED_{attempt:03d}.json',dict(reason=str(error),observed_unix=time.time()))
                for label in reversed(paused):
                    signal.pidfd_send_signal(descriptors[label],signal.SIGCONT)
                paused.clear()
                continue
            write(output/'BOUNDARY.json',boundary)
            write(output/'ARCHIVE_MANIFEST.json',archive)
            for label in ('actor','timer','supervisor'):
                node4.custody.same(request[label])
                if label != 'timer':
                    signal.pidfd_send_signal(descriptors[label],signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[label],signal.SIGCONT)
                readable,_,_ = select.select([descriptors[label]],[],[],30)
                require(bool(readable),'exact_GRID_process_exit_no_forced_kill')
            paused.clear()
            return verify_release(output,output)
        return dict(retired=False,reason='no_exact_next_boundary_captured',attempts=attempt)
    finally:
        for label in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[label],signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(watch)
        for signum,handler in handlers.items():
            signal.signal(signum,handler)
        if not (output/'RELEASED.json').exists():
            write(output/'NO_RELEASE_CLAIM.json',dict(retired=False,observed_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('retire','verify-release'))
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    options = parser.parse_args()
    result = retire(read(options.request),options.output) if options.operation=='retire' else verify_release(options.request,options.output)
    print(json.dumps(result,sort_keys=True))
