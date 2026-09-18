"""Node4 exact saved-boundary retirement and new-life staging; never GPUs0/2."""

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import subprocess
import sys
import tarfile
import time
from types import SimpleNamespace

from gpu import orch_r133_retire_old_lanes as custody


BASE = Path('/localhome/local-rohing')
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
DEVICES = {
    1: 'GPU-4b071167-a06a-773c-f947-60cb8c2f7512',
    3: 'GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14',
    4: 'GPU-f83fb491-34ce-4176-5852-c94652151a9f',
    5: 'GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30',
    6: 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397',
    7: 'GPU-6eac3b9d-551a-d786-f598-04ef6d701c98',
}
ROUTE_SOURCES = {
    'orch_r120_route_life_source_20260915_v3/gpu/orch_r120_route_life.py':
        'c480e667e990cf6e8990922e5f008721b10dc60a3b0534b4dbd4268dca810d1d',
    'orch_r118_node1_route_source/gpu/orch_r111_route_recovery.py':
        '2b96471dbb7dbfde4ca749250a21828b04643257eae217a9aa9a49b5649102c4',
    'orch_r118_node1_route_source/gpu/orch_r109_route_run.py':
        '95b7be9f76e5a31549264b11c16ff84561e237d6d30ddf94d10138fe34341496',
}
CODE_SOURCES = {
    'orch_r126_code_capacity_20260915_v3/source/gpu/orch_r126_code_capacity.py':
        'd32303b47954f9fda5093f284e7bc2441d6b93e3955c8f929e4e6649d0b54149',
    'orch_r119_code_old_forks_20260915_v3/source/gpu/orch_r108_code_parent_r109_run.py':
        '0aeec5ba67ae703fc2ad7c8f0fdfc9a0db75051c1175ba61f1a879f58b8bac65',
    'orch_r119_code_old_forks_20260915_v3/source/gpu/orch_r119_code_old_fork.py':
        'f5891b07fa11de7706c6970369f9c8f22f0e7defa20c44752f1d4c801fcaf889',
}
COUNTERS = ('native_completed', 'parent_completed', 'parent_missing', 'train_segments',
            'train_episodes', 'held_episodes', 'sleeps', 'optimizer_updates', 'triples')
LIVES = {
    1: dict(programme='raw', cadence='hands-off', cadence_responses=None, replay='free_distillation', style='no-parent', seed=0),
    3: dict(programme='raw', cadence='sparse3', cadence_responses=3, replay='free_distillation', style='Socratic', seed=1),
    4: dict(programme='kernel', cadence='sparse2', cadence_responses=2, replay='parent_guided_distillation', style='experimental-coach', seed=0),
    5: dict(programme='kernel', cadence='hands-off', cadence_responses=None, replay='free_distillation', style='no-parent', seed=0),
    6: dict(programme='raw', cadence='hands-off', cadence_responses=None, replay='reread_select', style='no-parent', seed=0),
    7: dict(programme='raw', cadence='hands-off', cadence_responses=None, replay='no_distillation', style='no-parent', seed=0),
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def allocation(physical):
    require(type(physical) is int and physical in DEVICES, 'protected_or_unassigned_device')
    return DEVICES[physical]


def life_spec(physical, variants_ready=False):
    allocation(physical)
    result = dict(LIVES[physical], physical=physical, gpu_uuid=DEVICES[physical],
                  parent_enabled=LIVES[physical]['cadence_responses'] is not None)
    if not variants_ready:
        require(physical not in (3, 6, 7), 'tested_seed_or_replay_runtime_required')
        if physical == 4:
            result.update(replay='free_distillation', requested_replay='parent_guided_distillation',
                          fallback_disclosed='R137 explicit free replay allowance until patched source ready')
    return result


def startup_text(original, spec):
    require(isinstance(original, str) and original.count('### Kernel environment') == 1,
            'exact_existing_kernel_startup_template')
    text = original if spec['programme'] == 'kernel' else original.split('### Kernel environment')[0]
    bound = 'The current allocation ends no later than'
    if spec['programme'] != 'kernel' and bound in original:
        text += '\n' + bound + original.split(bound, 1)[1]
    if spec['parent_enabled']:
        paragraph = ('This branch has the ' + spec['programme'] + ' programme. Planned parenting is '
                     + spec['style'] + ', approximately every ' + str(spec['cadence_responses'])
                     + ' child responses. A planned parent is not a delivered message: rely only on actual attributed inputs.')
    else:
        paragraph = ('This branch is an unparented ' + spec['programme'] + ' comparison. '
                     'No scheduled parent will send guidance. Continue your own inquiry; '
                     'operator safety notices or actual tool receipts, if delivered, are not parenting.')
    return text.rstrip() + '\n\n### This branch\n\n' + paragraph + '\n'


def bind_startup(original, spec, branch, source):
    original_base = str(BASE/'orch_r132_kernel_child_20260916_attempt1')
    text = startup_text(original, spec)
    changes = {original_base+'/workspace': str(Path(branch)/'workspace'),
               original_base+'/source1': str(source),
               'physical 0 through the a40r wrapper': 'physical '+str(spec['physical'])+' through the a40r wrapper'}
    for before, after in changes.items():
        require(text.count(before) == 1, 'exact_original_startup_resource_binding')
        text = text.replace(before, after, 1)
    require(original_base not in text, 'no_original_child_workspace_or_source_alias')
    return text


def route_root(physical):
    allocation(physical)
    require(physical in (1, 3), 'only_reviewed_route_retirement')
    return BASE / f'orch_r109_route_20260915_r120_C39_fork_a40r{physical}_attempt1'


def sha(path):
    return custody.sha(path)


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    custody.immutable(Path(path), value)


def ref(path):
    return dict(path=str(path), sha256=sha(path))


def checked(reference):
    require(sha(reference['path']) == reference['sha256'], 'reference_hash_binding')
    return read(reference['path'])


def code_root(physical):
    allocation(physical)
    require(physical in (4, 5, 6), 'only_reviewed_code_retirement')
    return BASE / f'orch_r126_code_capacity_20260915_v3/a40r_{physical}'


def code_frontier(root, marker, actor):
    root = Path(root)
    lane = root / 'campaign_code_parent'
    saved = read(lane / marker)
    cycle = int(marker.split('_')[1])
    plan = read(root / 'PLAN.json')
    require(plan['adapter'] is None and plan['optimizer_updates'] == 0
            and plan['parent_cadence'] == 'EPISODE' and plan['parent_wait_seconds'] == 0,
            'reviewed_frozen_nonblocking_CODE_only')
    require(saved['cycle'] == cycle and saved['status'] == 'COMPLETE' and saved['updates'] == 0
            and saved['no_adapter']['optimizer_updates'] == 0, 'complete_readonly_cycle_required')
    context_path = lane / f'CONTEXT_DISTILLATION_C{cycle:03d}.json'
    context = read(context_path)
    require(context['status'] == 'COMPLETE' and context['weight_updates'] == 0
            and context['parent_rounds'] == context['child_rounds'] == 3
            and context['finished_unix'] <= saved['finished_unix'], 'complete_context_before_boundary')
    cohorts = checked(plan['cohorts'])
    expected = {}
    completed_chunks = []
    for chunk in cohorts['chunks']:
        if chunk['first_cycle'] > cycle:
            break
        for row in checked(chunk['reservations']):
            if row['cycle'] <= cycle:
                require(row['cell_id'] not in expected, 'unique_CODE_schedule')
                expected[row['cell_id']] = row
        if chunk['last_cycle'] < cycle:
            completed_chunks.append(chunk)
    paths = list((lane / 'cells').glob('*.json'))
    require({path.stem for path in paths} == set(expected), 'no_missing_or_later_CODE_reservation')
    pending = []
    counts = dict(NATIVE=0, PARENT=0)
    for path in paths:
        row = read(path)
        require(all(row.get(key) == value for key, value in expected[path.stem].items()), 'exact_CODE_reserved_cell')
        require(row['started_unix'] <= saved['finished_unix'], 'no_CODE_charge_after_boundary')
        counts[row['kind']] += 1
        if row['kind'] == 'NATIVE':
            require(row['status'] == 'COMPLETE' and row['finished_unix'] <= saved['finished_unix'],
                    'no_inflight_or_later_CODE_native')
        else:
            require(row['status'] in ('PENDING', 'COMPLETE', 'SILENT', 'MISSING') and row['lesson'] == '',
                    'immutable_initial_empty_parent_lesson')
            if row['status'] == 'PENDING':
                request_path = root / 'parent_queue' / (path.stem + '.request.json')
                pending.append(dict(record=ref(path), request=ref(request_path)))
    if completed_chunks:
        prior = completed_chunks[-1]
        prior_marker = root / f'CHUNK_{prior["chunk"]:03d}_COMPLETE.json'
        require(read(prior_marker)['optimizer_updates'] == 0, 'frozen_prior_chunk')
        carry_path = root / f'CHUNK_{prior["chunk"]:03d}_CARRY_PRIVATE.json'
        carry = read(carry_path)
        prior_cycle = prior['last_cycle']
    else:
        carry_path = Path(plan['inputs']['context']['path'])
        carry = checked(plan['inputs']['context'])
        prior_cycle = cohorts['chunks'][0]['first_cycle'] - 1
    restored = dict(own_context=context['own_context'],
                    lessons=list(carry['lessons']) + [''] * (5 * (cycle-prior_cycle)))
    return dict(checkpoint=ref(lane / marker), context=ref(context_path), prior_carry=ref(carry_path),
                cycle=cycle, reconstructed_carry=restored, reconstruction='PINNED_SOURCE_TWO_EMPTY_EPISODE_LESSONS_PLUS_THREE_UNSCHEDULED_META_LESSONS_PER_CYCLE',
                counts=counts, pending_parents=pending, optimizer='ABSENT_FROZEN_BASE',
                adapter='ABSENT_FROZEN_BASE', live_generation_rng='NOT_EXPORTED_NO_BITWISE_GENERATION_RESUME_CLAIM')


def route_frontier(root, marker, actor):
    root = Path(root)
    lane = root / 'lease_r120_v2/campaign_node1_7'
    saved = read(lane / marker)
    cycle = int(Path(marker).stem.split('C')[-1])
    require(saved['resident_pid'] == actor['pid'] and saved['adapter'] is None
            and saved['optimizer_updates'] == 0 and isinstance(saved['own_memory'], str),
            'saved_BASE_context_not_active_optimizer')
    ready = read(lane / 'READY.json')
    require(ready['learned'] is False, 'BASE_only_no_training_interrupt')
    rows = [json.loads(line) for line in (root / 'RESERVATIONS.jsonl').read_text().splitlines()]
    require(bool(rows) and max(row['cycle'] for row in rows) == cycle, 'no_later_cycle_charge')
    require(all(row['reserved_unix'] <= saved['finished_unix'] for row in rows), 'no_charge_after_saved_boundary')
    calls = list((lane / 'native').glob('CALL_*.json'))
    require(bool(calls), 'actual_native_calls_required')
    completed = []
    for path in calls:
        row = read(path)
        require(row.get('status') == 'COMPLETE' and row['cycle'] <= cycle
                and row['finished_unix'] <= saved['finished_unix'], 'later_or_incomplete_native_call')
        completed.append(row['number'])
    current_numbers = {row['number'] for row in rows if row['kind'] == 'NATIVE'
                       and row['cycle'] >= read(lane / 'RECOVERY.json')['first_cycle']}
    require(set(completed) == current_numbers and len(completed) == len(current_numbers),
            'all_current_native_reservations_completed')
    require(max(row['number'] for row in rows if row['kind'] == 'NATIVE') == saved['native_completed'],
            'native_counter_saved_cursor')
    parent_numbers = set()
    for path in lane.glob('PARENT_*.json'):
        parent = read(path)
        require(parent.get('status') in ('COMPLETE', 'MISSING')
                and parent['observed_unix'] <= saved['finished_unix'], 'parent_terminal_receipt_required')
        parent_numbers.add(parent['number'])
    require(parent_numbers == {row['number'] for row in rows if row['kind'] == 'PARENT'
            and row['cycle'] >= read(lane / 'RECOVERY.json')['first_cycle']}, 'all_parent_reservations_completed')
    sleep_path = lane / 'sleeps' / f'{cycle:04d}.json'
    require(read(sleep_path)['context_only'] is True and read(sleep_path)['weight_updates'] == 0,
            'context_only_saved_sleep')
    return dict(checkpoint=ref(lane / marker), reservations=ref(root / 'RESERVATIONS.jsonl'),
                sleep=ref(sleep_path), cycle=cycle, saved=saved, native_files=len(calls),
                optimizer='ABSENT_FROZEN_BASE', adapter='ABSENT_FROZEN_BASE',
                live_generation_rng='NOT_EXPORTED_NO_BITWISE_GENERATION_RESUME_CLAIM',
                raw_history_preserved=True)


def check_pair(physical, actor, supervisor):
    python = str(BASE / 'v2/venv/bin/python')
    if physical in (1, 3):
        root = route_root(physical)
        require(actor['argv'] == [python, '-B', '-m', 'gpu.orch_r120_route_life', 'native',
                             '--root', str(root), '--lane', 'node1_7'], 'exact_route_actor_argv')
        require(supervisor['argv'] == [python, '-B', str(BASE / next(iter(ROUTE_SOURCES))),
                                  'guard', '--root', str(root), '--lane', 'node1_7'], 'exact_route_guard_argv')
    else:
        root = code_root(physical)
        prefix = ("import sys,runpy;sys.path.insert(0," + repr(str(BASE/'orch_r119_code_old_forks_20260915_v3/source'))
                  + ");import gpu;gpu.__path__.insert(0," + repr(str(BASE/'orch_r126_code_capacity_20260915_v3/source/gpu'))
                  + ");sys.argv=")
        suffix = ';runpy.run_module(\'gpu.orch_r126_code_capacity\',run_name="__main__")'
        for record, phase in ((actor, 'native'), (supervisor, 'watch')):
            code = prefix + repr(['gpu.orch_r126_code_capacity', phase, '--root', str(root)]) + suffix
            require(record['argv'] == [python, '-B', '-c', code], 'exact_CODE_actor_or_guard_argv')
    require(actor['uid'] == supervisor['uid'] == os.getuid()
            and actor['parent'] == supervisor['pid'], 'owned_direct_parent_child')
    require(actor['cvd'] == [allocation(physical)] and supervisor['cvd'] in ([], ['']),
            'exact_assigned_GPU_and_CPU_guard')


def snapshot(paths, destination):
    entries = {}
    for root in map(Path, paths):
        for path in ([root] if root.is_file() else sorted(root.rglob('*'))):
            if path.is_symlink():
                entries[str(path)] = dict(kind='symlink', target=os.readlink(path))
            elif path.is_file():
                entries[str(path)] = dict(kind='file', sha256=sha(path), size=path.stat().st_size)
    required = sum(entry.get('size', 0) for entry in entries.values())
    space = os.statvfs(Path(destination).parent)
    require(space.f_bavail * space.f_frsize > 2 * required + 1024**3, 'archive_disk_headroom')
    with tarfile.open(destination, 'x') as archive:
        for name in entries:
            archive.add(name, arcname=name.lstrip('/'), recursive=False)
    with tarfile.open(destination, 'r') as archive:
        require(len(archive.getmembers()) == len(entries), 'exact_archive_members')
        for member in archive:
            record = entries['/' + member.name]
            if record['kind'] == 'symlink':
                require(member.issym() and member.linkname == record['target'], 'exact_symlink_record')
            else:
                require(member.isfile(), 'regular_archive_member')
                digest = hashlib.sha256()
                with archive.extractfile(member) as stream:
                    for block in iter(lambda: stream.read(1048576), b''):
                        digest.update(block)
                require(digest.hexdigest() == record['sha256'], 'archive_content_verified')
    for name, record in entries.items():
        require(os.readlink(name) == record['target'] if record['kind'] == 'symlink'
                else sha(name) == record['sha256'], 'source_stable_during_snapshot')
    with Path(destination).open('rb') as stream:
        os.fsync(stream.fileno())
    Path(destination).chmod(0o444)
    return dict(archive=ref(destination), files=entries)


def scan(physical, output):
    allocation(physical)
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_scan_only')
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission
    minor.pinned.policy = SimpleNamespace(HOST_SHA=HOST_SHA, DEVICES=DEVICES,
                                         require=require, allocation=allocation)
    service = Path(output) / 'SERVICE_IDENTITY.json'
    if not service.exists():
        minor.pinned.service(service)
    return admission.scan(physical, service)


def release(physical, output):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
               'PYTHONPATH=' + os.environ['PYTHONPATH'], sys.executable, '-B', '-m',
               'gpu.orch_r136_node4_launch', 'scan', '--physical', str(physical), '--output', str(output)]
    report = json.loads(subprocess.check_output(command, text=True, timeout=100))
    report.pop('host', None)
    write(output / 'FINAL_SCAN.json', report)
    require(report['clear'] is True and report['scanner_euid'] == 0
            and report['gpu']['uuid'] == allocation(physical) and not report['blocking_reasons'],
            'actual_privileged_release_required')
    return report


def verify_retired(directory, output):
    directory, output = Path(directory), Path(output)
    request = read(directory/'REQUEST.json')
    physical = request['physical']
    allocation(physical)
    check_pair(physical, request['actor'], request['supervisor'])
    require(not custody.alive(request['actor']) and not custody.alive(request['supervisor']),
            'both_exact_old_actors_must_have_exited')
    boundary = read(directory/'BOUNDARY.json')
    require(sha(boundary['checkpoint']['path']) == boundary['checkpoint']['sha256'], 'saved_checkpoint_still_exact')
    manifest = read(directory/'ARCHIVE_MANIFEST.json')
    require(sha(manifest['archive']['path']) == manifest['archive']['sha256'], 'preserved_raw_archive_hash')
    output.mkdir(parents=True, exist_ok=False)
    release(physical, output)
    result = dict(schema='R136_NODE4_RELEASE_V1', physical=physical, gpu_uuid=allocation(physical),
                  retired=True, boundary=ref(directory/'BOUNDARY.json'), archive=ref(directory/'ARCHIVE_MANIFEST.json'),
                  scan=ref(output/'FINAL_SCAN.json'), original_retirement=str(directory),
                  finished_unix=time.time(), rechecked_readonly_no_signals=True)
    write(output/'RELEASED.json', result)
    return result


def retire(request, output):
    physical = request['physical']
    is_route = physical in (1, 3)
    root = route_root(physical) if is_route else code_root(physical)
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA, 'exact_node4_host')
    actor, supervisor = request['actor'], request['supervisor']
    check_pair(physical, actor, supervisor)
    require(request['tested_source_sha256'] == sha(__file__) and request['cpu_passed'] is True,
            'tested_operator_required')
    require(request['custody_sha256'] == sha(custody.__file__)
            and sha(request['cpu_receipt']['path']) == request['cpu_receipt']['sha256'],
            'frozen_tested_dependency_and_CPU_receipt')
    require(1 <= request['wait_seconds'] <= 1200, 'bounded_boundary_wait')
    source_pins = ROUTE_SOURCES if is_route else CODE_SOURCES
    for name, expected in source_pins.items():
        require(sha(BASE / name) == expected, 'reviewed_route_source')
    lane = root / ('lease_r120_v2/campaign_node1_7' if is_route else 'campaign_code_parent')
    frontier = route_frontier if is_route else code_frontier
    if is_route:
        ready = read(lane / 'READY.json')
        require(ready['learned'] is False, 'BASE_only')
        hard_end = ready['hard_deadline_unix']
        sources = [(root/'source').resolve()]
    else:
        ready = read(root / 'PLAN.json')
        require(ready['adapter'] is None and ready['optimizer_updates'] == 0, 'BASE_only')
        require(ready['physical'] == physical and ready['gpu_uuid'] == allocation(physical), 'exact_CODE_plan_slot')
        hard_end = ready['hard_end_unix']
        sources = [BASE/'orch_r119_code_old_forks_20260915_v3/source', BASE/'orch_r126_code_capacity_20260915_v3/source']
        for name, expected in ready['source_files'].items():
            require(sha(name) == expected, 'full_CODE_source_closure')
    require(time.time() + request['wait_seconds'] + 300 < hard_end, 'lease_headroom')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'REQUEST.json', request)
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK)
    require(watch >= 0, 'inotify_required')
    require(library.inotify_add_watch(watch, os.fsencode(lane), 0x8 | 0x80) >= 0, 'boundary_watch_required')
    descriptors, paused, retired = {}, [], False
    handlers = {}

    def interrupted(signum, frame):
        raise InterruptedError('operator_signal:' + str(signum))

    started = time.time()
    try:
        for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            handlers[signum] = signal.signal(signum, interrupted)
        for label, record in (('actor', actor), ('supervisor', supervisor)):
            custody.same(record)
            descriptors[label] = os.pidfd_open(record['pid'])
            custody.same(record)
        deadline = time.monotonic() + request['wait_seconds']
        attempt = 0
        while time.monotonic() < deadline:
            readable, _, _ = select.select([watch], [], [], min(1, deadline-time.monotonic()))
            if not readable:
                custody.same(actor)
                custody.same(supervisor)
                continue
            events, cursor, markers = os.read(watch, 65536), 0, []
            while cursor + 16 <= len(events):
                _, mask, _, length = struct.unpack_from('iIII', events, cursor)
                name = events[cursor+16:cursor+16+length].rstrip(b'\0').decode()
                match = name.startswith('CHECKPOINT_C') and name.endswith('.json') if is_route else name.startswith('CYCLE_') and name.endswith('_COMPLETE.json')
                if match and mask & (0x8 | 0x80):
                    markers.append(name)
                cursor += 16 + length
            if not markers:
                continue
            marker = max(markers, key=lambda name: int(Path(name).stem.split('C')[-1]) if is_route else int(name.split('_')[1]))
            attempt += 1
            try:
                for label, record in (('supervisor', supervisor), ('actor', actor)):
                    paused.append((label, record))
                    custody.pause(record, descriptors[label])
                require(read(lane / marker)['finished_unix'] >= started, 'fresh_boundary_only')
                boundary = frontier(root, marker, actor)
                archive = snapshot([root, *sources, *[BASE/name for name in source_pins]],
                                   output / f'ARCHIVE_{attempt:03d}.tar')
                require(frontier(root, marker, actor) == boundary, 'boundary_unchanged_after_archive')
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
                write(output / f'REJECTED_{attempt:03d}.json', dict(reason=str(error), observed_unix=time.time()))
                for label, record in reversed(paused):
                    signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                paused.clear()
                continue
            write(output / 'BOUNDARY.json', boundary)
            write(output / 'ARCHIVE_MANIFEST.json', archive)
            for label, record in (('actor', actor), ('supervisor', supervisor)):
                custody.same(record)
                signal.pidfd_send_signal(descriptors[label], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                exited, _, _ = select.select([descriptors[label]], [], [], 30)
                require(bool(exited), 'owned_actor_exit_required_no_SIGKILL')
            paused.clear()
            report = release(physical, output)
            result = dict(schema='R136_NODE4_RELEASE_V1', physical=physical, gpu_uuid=allocation(physical),
                          retired=True, boundary=ref(output/'BOUNDARY.json'), archive=ref(output/'ARCHIVE_MANIFEST.json'),
                          scan=ref(output/'FINAL_SCAN.json'), finished_unix=time.time(), no_live_rng_claim=True)
            write(output / 'RELEASED.json', result)
            retired = True
            return result
        return dict(retired=False, reason='next_exact_saved_boundary_not_captured', attempts=attempt)
    finally:
        for label, record in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(watch)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
        if not retired:
            write(output/'NO_RELEASE_CLAIM.json', dict(observed_unix=time.time(), retired=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('scan', 'retire', 'verify-release'))
    parser.add_argument('--physical', type=int)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    if options.operation == 'scan':
        result = scan(options.physical, options.output)
    elif options.operation == 'verify-release':
        result = verify_retired(options.request, options.output)
    else:
        result = retire(read(options.request), options.output)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
